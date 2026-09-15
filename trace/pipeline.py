"""Research pipeline orchestrator: plan -> search -> analyze -> draft -> verify
-> human approval -> brief. Every claim must trace to a source (Tavily) or a
sandbox-computed number (Token Factory Sandbox); every stage runs behind
scoped tool permissions and writes to the audit trail.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from . import audit as audit_mod
from . import config, policy
from .llm import NebiusClient
from .sandbox import Sandbox, SandboxJob
from .tavily_client import Source, TavilyClient

SYSTEM_PLAN = "You are a research planner. Output JSON only: {questions: [...], analysis_tasks: [{id, title, code, description}]}."
SYSTEM_DRAFT = ("You are a technical writer. Write section drafts as JSON: "
                "[{heading, body, citations: [n], sandbox_ref?}]. Cite every factual claim with [n].")
SYSTEM_VERIFY = ("You are a skeptical fact-checker. Given claims + source texts, output JSON: "
                 "[{claim, confidence: 0-1, supported_by}]. Confidence < 0.6 must be flagged.")


@dataclass
class Brief:
    query: str
    sections: list[dict]
    sources: list[Source]
    verifications: list[dict]
    sandbox_results: dict[str, str]
    approved: bool
    approval_note: str = ""

    def markdown(self) -> str:
        lines = [f"# Research brief: {self.query}\n"]
        for i, s in enumerate(self.sections, 1):
            lines.append(f"## {i}. {s['heading']}\n\n{s['body']}\n")
        lines.append("## Verification\n")
        for v in self.verifications:
            flag = " ✅" if v["confidence"] >= 0.6 else " ⚠️ LOW CONFIDENCE"
            lines.append(f"- {v['claim']} — confidence {v['confidence']:.2f}{flag}")
        if self.sandbox_results:
            lines.append("\n## Sandbox computations\n")
            for jid, out in self.sandbox_results.items():
                lines.append(f"### `{jid}`\n```\n{out.strip()}\n```\n")
        lines.append("## Sources\n")
        for i, s in enumerate(self.sources, 1):
            lines.append(f"[{i}] {s.title} — {s.url}")
        lines.append(f"\n_Approved by human: {'yes' if self.approved else 'NO — DRAFT ONLY'}"
                     + (f" ({self.approval_note})" if self.approval_note else "") + "_")
        return "\n".join(lines)


@dataclass
class Orchestrator:
    settings: config.Settings = field(default_factory=config.Settings)
    llm: NebiusClient = field(init=False)
    tavily: TavilyClient = field(init=False)
    sandbox: Sandbox = field(init=False)

    def __post_init__(self) -> None:
        self.llm = NebiusClient(self.settings)
        self.tavily = TavilyClient(self.settings)
        self.sandbox = Sandbox(self.settings)

    def run(self, query: str, *, auto_approve: bool = False,
            approval_note: str = "") -> tuple[Brief, audit_mod.Audit]:
        a = audit_mod.new_audit(query, self.settings.audit_dir)

        # 1. PLAN (Nemotron 3 Super, reasoning on)
        policy.check("plan", "llm:planner")
        call = self.llm.chat("plan", SYSTEM_PLAN, f"Research plan for: {query}", json_mode=True)
        a.tool_call("plan", "llm:planner", f"query: {query}", f"plan {call.prompt_hash}",
                    tier=call.tier, model_id=call.model_id, latency_ms=call.latency_ms, mock=call.mock)
        plan = json.loads(call.response)
        questions: list[str] = plan["questions"]
        tasks: list[dict] = plan.get("analysis_tasks", [])

        # 2. SEARCH (Tavily)
        policy.check("search", "tavily:search")
        sources: list[Source] = []
        seen: set[str] = set()
        for q in questions[:3]:
            for s in self.tavily.search(q, max_results=3):
                if s.url not in seen:
                    seen.add(s.url)
                    sources.append(s)
        a.tool_call("search", "tavily:search", f"{len(questions)} questions",
                    f"{len(sources)} unique sources", backend="tavily")

        # 3. ANALYZE (Token Factory Sandbox / local)
        policy.check("analyze", "sandbox:execute")
        sandbox_results: dict[str, str] = {}
        for t in tasks[:3]:
            res = self.sandbox.execute(SandboxJob(id=t["id"], code=t["code"],
                                                  description=t.get("description", "")))
            sandbox_results[t["id"]] = res.stdout or res.stderr
            a.tool_call("analyze", "sandbox:execute", f"job {t['id']}: {t['title']}",
                        f"exit={res.exit_code} {res.duration_ms}ms",
                        backend=res.backend, latency_ms=res.duration_ms, mock=self.settings.mock)

        # 4. DRAFT (Nemotron 3 Nano, reasoning low — high volume, cheap)
        policy.check("draft", "llm:drafter")
        draft_ctx = (f"Query: {query}\nSources:\n"
                     + "\n".join(f"[{i+1}] {s.title} ({s.url}): {s.snippet}" for i, s in enumerate(sources))
                     + "\nSandbox results:\n"
                     + "\n".join(f"[{jid}]\n{out}" for jid, out in sandbox_results.items()))
        call = self.llm.chat("draft", SYSTEM_DRAFT, draft_ctx, json_mode=True, max_tokens=4096)
        a.tool_call("draft", "llm:drafter", f"{len(sources)} sources, {len(sandbox_results)} sandbox runs",
                    f"{call.prompt_hash}", tier=call.tier, model_id=call.model_id,
                    latency_ms=call.latency_ms, mock=call.mock)
        sections = json.loads(call.response)

        # 5. VERIFY (Nemotron 3 Super, reasoning on — claim-by-claim)
        policy.check("verify", "llm:verifier")
        policy.check("verify", "tavily:extract")
        texts = self.tavily.extract([s.url for s in sources[:5]])
        verify_ctx = (f"Claims/sections: {json.dumps(sections)}\nSource texts:\n"
                      + "\n".join(f"[{u}]\n{t[:2000]}" for u, t in texts.items()))
        call = self.llm.chat("verify", SYSTEM_VERIFY, verify_ctx, json_mode=True, max_tokens=4096)
        a.tool_call("verify", "llm:verifier", f"{len(sections)} sections",
                    f"verifications {call.prompt_hash}", tier=call.tier,
                    model_id=call.model_id, latency_ms=call.latency_ms, mock=call.mock)
        verifications = json.loads(call.response)

        # 6. HUMAN APPROVAL GATE — brief is DRAFT ONLY until a human approves
        policy.check("approve", "human:approve")
        approved = auto_approve
        if not approved:
            a.log("approve", "human:approve", detail="approval pending (non-interactive run)")
        else:
            a.log("approve", "human:approve",
                  detail=f"approved{': ' + approval_note if approval_note else ''}")

        brief = Brief(query=query, sections=sections, sources=sources,
                      verifications=verifications, sandbox_results=sandbox_results,
                      approved=approved, approval_note=approval_note)
        a.log("assemble", "trace", detail=f"brief assembled: {len(sections)} sections")
        return brief, a
