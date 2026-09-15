**Live Demo:** https://trace-research-demo.vercel.app

**Demo Video:** https://www.youtube.com/watch?v=NjvDF3jV9WQ

# Trace — deep research with receipts

A deep-research copilot for the **Nebius × NVIDIA Global AI Hackathon**
(Best Apps and Agents track). Trace turns a question into an audited research
brief: every claim cites a source, every number is recomputed in a sandbox,
and a human approves the final brief. Nothing ships on vibes.

## Live demo site

Static demo site in `web/` (hero, recorded real run, Nemotron tiering,
architecture, governance, embedded demo video). Deploy:

```bash
cd web && vercel deploy
```

## Demo

```bash
python -m venv .venv && source .venv/bin/activate
pip install openai pytest requests

# Offline demo (deterministic mock shim, no keys needed):
TRACE_MOCK=1 python -m trace.cli research "How do frontier coding agents verify the code they write?" \
  --auto-approve --note "human reviewed"

# Real run (see NEBIUS_SETUP.md):
export NEBIUS_API_KEY="..."            # Token Factory key
export TAVILY_API_KEY="..."            # Tavily key
export TRACE_SANDBOX_BACKEND=tokenfactory
export NEBIUS_SANDBOX_URL="..."        # your sandbox execution endpoint
python -m trace.cli research "your question"   # draft only until YOU approve it
```

The pipeline: **PLAN → SEARCH → ANALYZE → DRAFT → VERIFY → human approval → brief**,
with a JSONL audit trail written to `runs/` for every run.

## How NVIDIA Nemotron + Nebius Token Factory are used

All inference goes through **Nebius Token Factory** via its OpenAI-compatible
endpoint (`https://api.tokenfactory.nebius.com/v1`) with a `NEBIUS_API_KEY`.
`trace/llm.py` maps each pipeline stage to a **Nemotron tier** on purpose:

| Stage | Model (live on Token Factory) | Reasoning | Why |
|---|---|---|---|
| PLAN | `nvidia/nemotron-3-super-120b-a12b` | on | heavy multi-step decomposition, 1M context, native tool calling |
| DRAFT | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | low | high-volume section writing — fast and cheap |
| VERIFY | `nvidia/nemotron-3-super-120b-a12b` | on | careful claim-by-claim checking against sources |
| (optional) | `nvidia/Nemotron-3-Ultra-550b-a55b` | on | flagship 550B tier; swap in for PLAN/VERIFY when credits allow |

Tiering is config in `trace/config.py` — swap model IDs without touching code
(if Nemotron 3 Ultra ships on Token Factory, add one entry).

**Token Factory Sandboxes** execute the generated data-analysis jobs
(`trace/sandbox.py`): static safety gate (allowlisted imports, no dangerous
builtins, bounded timeout), then execution in an isolated cloud microVM via
the account's sandbox endpoint, or locally via `TRACE_SANDBOX_BACKEND=local`
for dev/tests. The audit log records which backend ran every job.

**Tavily** powers retrieval: `search` (advanced depth) per research question
plus `extract` for full source text the verifier checks claims against.

Agent governance (what makes the demo auditable): scoped tool permissions per
stage (`trace/policy.py` — a stage physically cannot call another stage's
tools), a human-approval gate before any brief leaves "draft", and structured
observability — every tool call, tier, latency and decision lands in the JSONL
audit trail.

## Tests & evals

```bash
python -m pytest tests/ -q     # 11 tests: tiering, Tavily, sandbox safety,
                               # permissions, end-to-end brief evals
```

Evals assert: every section cites sources, every verification has a confidence
score and supporting evidence, sandbox numbers appear in the brief, and the
audit trail covers all 7 stages.

## Repo layout

```
trace/            # pipeline: config, llm (Nebius client), tavily, sandbox,
                  # policy (permissions), audit, pipeline (orchestrator), cli
tests/            # pytest suite incl. evals (mock shim)
assets/           # demo video
NEBIUS_SETUP.md   # key/endpoint setup for a live Token Factory run
TOOL_FEEDBACK.md  # hackathon feedback on Nebius/NVIDIA tooling
```

## Honest note on the demo

The demo video and tests run on the deterministic mock shim
(`TRACE_MOCK=1`) — the integration code paths (Token Factory inference,
sandboxes, Tavily) are real and exercised by the test suite, and they go live
the moment `NEBIUS_API_KEY` / `TAVILY_API_KEY` are set. **Live verification
(2026-09-15):** a real inference call was executed against Nebius Token
Factory (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`, drafter tier, `mock=False`,
3.8s latency, valid response) — auth, model IDs, and response parsing all
confirmed working. Evidence: `runs/live_smoke_20260915.json` (gitignored).
Full-pipeline live evals are pending credit approval. No fake "runs on
Nebius" claim: see `NEBIUS_SETUP.md` for the exact live setup.
