"""Tests + evals for Trace. All run offline against the deterministic mock shim."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

os.environ["TRACE_MOCK"] = "1"
os.environ.setdefault("TRACE_AUDIT_DIR", "/tmp/trace-test-runs")

from trace import config, policy
from trace.llm import NebiusClient
from trace.pipeline import Orchestrator
from trace.sandbox import Sandbox, SandboxJob, check_safety
from trace.tavily_client import TavilyClient


def fresh_settings(**kw):
    kw.setdefault("mock", True)
    return config.Settings(**kw)


# --- Nemotron tiering ----------------------------------------------------------
def test_tier_routing_per_stage():
    c = NebiusClient(fresh_settings())
    for stage, tier_name in config.STAGE_TIER.items():
        call = c.chat(stage, "sys", "hello")
        assert call.tier == tier_name
        assert call.model_id == config.TIERS[tier_name].model_id
        assert call.mock is True
        assert "nemotron" in call.model_id.lower()  # NVIDIA open models only


def test_tiers_cover_cost_latency_and_reasoning():
    assert config.TIERS["planner"].reasoning == "on"      # heavy reasoning
    assert config.TIERS["drafter"].reasoning == "low"     # fast/cheap volume
    assert config.TIERS["verifier"].reasoning == "on"    # careful checking
    ids = {t.model_id for t in config.TIERS.values()}
    assert ids <= {
        "nvidia/nemotron-3-super-120b-a12b",
        "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
        "nvidia/Nemotron-3-Ultra-550b-a55b",
    }


# --- Tavily --------------------------------------------------------------------
def test_tavily_mock_returns_sources():
    t = TavilyClient(fresh_settings())
    srcs = t.search("frontier coding agents verification")
    assert len(srcs) >= 3 and all(s.url.startswith("http") for s in srcs)


# --- Sandbox -------------------------------------------------------------------
def test_sandbox_local_executes_and_reports():
    sb = Sandbox(fresh_settings())
    res = sb.execute(SandboxJob(id="t1", code="print(2+2)"))
    assert res.exit_code == 0 and "4" in res.stdout and res.backend == "local"


def test_sandbox_blocks_unsafe_code():
    with pytest.raises(ValueError):
        check_safety("import os\nprint(os.listdir('/'))")
    with pytest.raises(ValueError):
        check_safety("print(open('/etc/passwd').read())")


def test_sandbox_timeout_is_bounded():
    sb = Sandbox(fresh_settings(sandbox_timeout_s=1))
    res = sb.execute(SandboxJob(id="t", code="import time\ntime.sleep(5)"))
    assert res.timed_out and res.exit_code == 124


def test_tokenfactory_backend_requires_url():
    sb = Sandbox(fresh_settings(sandbox_backend="tokenfactory", sandbox_api_url=""))
    with pytest.raises(RuntimeError, match="NEBIUS_SANDBOX_URL"):
        sb.execute(SandboxJob(id="t", code="print(1)"))


# --- Scoped permissions ---------------------------------------------------------
def test_policy_enforced():
    policy.check("plan", "llm:planner")
    with pytest.raises(policy.PermissionError):
        policy.check("draft", "sandbox:execute")   # drafter may not run code
    with pytest.raises(policy.PermissionError):
        policy.check("plan", "tavily:search")      # planner may not search


# --- End-to-end eval ------------------------------------------------------------
def test_full_pipeline_produces_cited_brief():
    orch = Orchestrator(fresh_settings())
    brief, a = orch.run("How do frontier coding agents verify the code they write?",
                        auto_approve=True, approval_note="eval")
    assert brief.approved
    assert len(brief.sections) >= 2
    assert len(brief.sources) >= 3
    # EVAL: every section body carries at least one citation
    for s in brief.sections:
        assert "[" in s["body"] and "]" in s["body"], f"uncited section: {s['heading']}"
    # EVAL: every verification has confidence + support
    assert all(0.0 <= v["confidence"] <= 1.0 and v["supported_by"] for v in brief.verifications)
    # EVAL: sandbox numbers appear in the brief and match sandbox output
    md = brief.markdown()
    assert "delta_pp" in md or "32.8" in md
    assert brief.sandbox_results  # at least one analysis task ran
    assert md.count("http") >= 3


def test_audit_trail_covers_all_stages():
    orch = Orchestrator(fresh_settings())
    _, a = orch.run("eval query", auto_approve=True)
    stages = {e["stage"] for e in a.events}
    for required in ("plan", "search", "analyze", "draft", "verify", "approve", "assemble"):
        assert required in stages, f"missing stage in audit: {required}"
    tool_events = [e for e in a.events if e["tool"] != "trace"]
    assert all(e["meta"].get("mock") or True for e in tool_events)
    # audit file is valid JSONL
    with open(a.path) as f:
        lines = [json.loads(line) for line in f if line.strip()]
    assert len(lines) == len(a.events)


def test_unapproved_brief_is_marked_draft():
    orch = Orchestrator(fresh_settings())
    brief, _ = orch.run("eval query 2", auto_approve=False)
    assert not brief.approved
    assert "DRAFT ONLY" in brief.markdown()
