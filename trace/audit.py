"""Structured observability: every run writes a JSONL audit trail.

Each record carries: timestamp, stage, tool, inputs hash, output summary,
model tier + id, latency, sandbox backend, and human decisions. This is the
"receipts" — a judge (or user) can replay exactly what the agent did.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field


def _h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


@dataclass
class Audit:
    run_id: str
    query: str
    path: str
    events: list[dict] = field(default_factory=list)

    def log(self, stage: str, tool: str, *, detail: str = "", meta: dict | None = None) -> dict:
        ev = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "run_id": self.run_id,
            "stage": stage,
            "tool": tool,
            "detail": detail,
            "meta": meta or {},
        }
        self.events.append(ev)
        with open(self.path, "a") as f:
            f.write(json.dumps(ev) + "\n")
        return ev

    def tool_call(self, stage: str, tool: str, input_summary: str, output_summary: str,
                  *, tier: str = "", model_id: str = "", latency_ms: int = 0,
                  backend: str = "", mock: bool = False) -> dict:
        return self.log(stage, tool, detail=f"{input_summary} -> {output_summary}", meta={
            "input_hash": _h(input_summary),
            "tier": tier, "model_id": model_id, "latency_ms": latency_ms,
            "backend": backend, "mock": mock,
        })

    def summary(self) -> dict:
        stages = sorted({e["stage"] for e in self.events})
        return {
            "run_id": self.run_id,
            "query": self.query,
            "events": len(self.events),
            "stages": stages,
            "mock": any(e["meta"].get("mock") for e in self.events),
        }


def new_audit(query: str, audit_dir: str) -> Audit:
    run_id = f"run-{time.strftime('%Y%m%d-%H%M%S')}-{_h(query)[:6]}"
    os.makedirs(audit_dir, exist_ok=True)
    path = os.path.join(audit_dir, f"{run_id}.jsonl")
    a = Audit(run_id=run_id, query=query, path=path)
    a.log("start", "trace", detail=f"query: {query}")
    return a
