# evals/

Brief-quality evals live in `../tests/test_trace.py` and run offline against
the deterministic mock shim (`TRACE_MOCK=1`):

| Eval | What it asserts |
|---|---|
| `test_full_pipeline_produces_cited_brief` | every section carries citations; every verification has a 0–1 confidence + supporting evidence; sandbox numbers appear in the brief; ≥3 sources |
| `test_audit_trail_covers_all_stages` | audit JSONL covers all 7 stages and is valid JSONL |
| `test_unapproved_brief_is_marked_draft` | the human-approval gate marks unapproved briefs DRAFT ONLY |
| `test_tier_routing_per_stage` | plan→Super/reasoning-on, draft→Nano/reasoning-low, verify→Super/reasoning-on; NVIDIA Nemotron models only |
| `test_sandbox_*` | local sandbox executes, blocks unsafe imports, enforces timeouts |

Run: `python -m pytest tests/ -q` (11 passed, Sep 2026).
