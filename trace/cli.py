"""Trace CLI: deep research with receipts.

Usage:
  trace research "your question" [--auto-approve] [--note "..."]
  trace models                      # list Nebius models on your account
  trace sandbox-demo                 # run a sandbox job directly
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import config, mock_data
from .pipeline import Orchestrator
from .sandbox import Sandbox, SandboxJob


def cmd_research(args) -> int:
    settings = config.Settings()
    orch = Orchestrator(settings)
    brief, a = orch.run(args.query, auto_approve=args.auto_approve, approval_note=args.note or "")
    out = brief.markdown()
    print(out)
    brief_path = os.path.join(settings.audit_dir, f"{a.run_id}-brief.md")
    with open(brief_path, "w") as f:
        f.write(out)
    print(f"\n---\naudit trail: {a.path}\nbrief: {brief_path}")
    print(f"tiers used: planner={settings.tiers['planner'].model_id} "
          f"drafter={settings.tiers['drafter'].model_id} verifier={settings.tiers['verifier'].model_id}")
    print(f"sandbox backend: {orch.sandbox.backend} | mock: {settings.mock}")
    if not args.auto_approve:
        print("NOTE: brief is DRAFT ONLY — approve it with --auto-approve after human review.")
    return 0


def cmd_models(args) -> int:
    from .llm import NebiusClient
    client = NebiusClient()
    for m in client.models():
        print(m)
    return 0


def cmd_sandbox_demo(args) -> int:
    settings = config.Settings()
    sb = Sandbox(settings)
    job = SandboxJob(id="demo", code=mock_data.MOCK_PLAN["analysis_tasks"][0]["code"],
                     description="Recompute reported pass-rate gap")
    res = sb.execute(job)
    print(f"backend={res.backend} exit={res.exit_code} {res.duration_ms}ms\n{res.stdout}{res.stderr}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="trace", description="Deep research with receipts.")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("research", help="Run the full research pipeline")
    r.add_argument("query")
    r.add_argument("--auto-approve", action="store_true", help="Human approves the brief (HITL gate)")
    r.add_argument("--note", default="", help="Approval note recorded in the audit trail")
    r.set_defaults(fn=cmd_research)

    m = sub.add_parser("models", help="List models on your Nebius account")
    m.set_defaults(fn=cmd_models)

    s = sub.add_parser("sandbox-demo", help="Run a sandbox data-analysis job")
    s.set_defaults(fn=cmd_sandbox_demo)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
