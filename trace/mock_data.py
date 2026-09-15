"""Deterministic mock shim (TRACE_MOCK=1).

Used by tests, evals, and the demo video so the full pipeline runs offline
with zero keys. Responses are realistic in shape (JSON plans, cited sections,
verification scores) so the audit trail, approvals and briefs are identical
in structure to live runs.
"""
from __future__ import annotations

import json

DEMO_QUERY = "How do frontier coding agents verify the code they write?"

MOCK_PLAN = {
    "questions": [
        "What verification strategies do frontier coding agents use (tests, sandbox execution, self-critique)?",
        "Which agentic coding systems publish verifiable evaluation harnesses?",
        "What are the failure modes of LLM self-verification?",
    ],
    "analysis_tasks": [
        {
            "id": "t1",
            "title": "Compare reported pass rates",
            "code": (
                "data = {'SWE-bench Verified': 0.747, 'SWE-bench Multimodal': 0.419}\n"
                "for k, v in data.items():\n"
                "    print(f'{k}: {v:.1%}')\n"
                "print('delta_pp:', round((0.747-0.419)*100, 1))\n"
            ),
            "description": "Recompute the gap between reported pass rates in a sandbox.",
        }
    ],
}

MOCK_SOURCES = [
    {
        "title": "SWE-bench Verified: Can Language Models Resolve Real-World GitHub Issues?",
        "url": "https://openai.com/index/introducing-swe-bench-verified/",
        "snippet": "SWE-bench Verified is a human-validated subset of 500 tasks ... agent pass rates rose from 2% to 74.7% on the verified split.",
    },
    {
        "title": "SWE-bench Multimodal: Do AI Agents Generalize to Visual Software Tasks?",
        "url": "https://www.swebench.com/multimodal.html",
        "snippet": "Frontier agents score 41.9% on multimodal software tasks, far below text-only splits.",
    },
    {
        "title": "Why LLM self-verification fails: a survey of failure modes",
        "url": "https://arxiv.org/abs/2409.12345",
        "snippet": "Self-critique without external execution degrades calibration; independent test execution restores it.",
    },
]

MOCK_DRAFT_SECTIONS = [
    {
        "heading": "Tests first, trust later",
        "body": ("Frontier coding agents verify code primarily by executing it: "
                 "reproducing failing tests, applying a patch, and re-running the "
                 "suite until green [1][3]. Self-critique alone is unreliable."),
        "citations": [1, 3],
    },
    {
        "heading": "Published harnesses set the bar",
        "body": ("SWE-bench Verified reports top agent pass rates of 74.7%, while "
                 "SWE-bench Multimodal drops to 41.9% — a 32.8 percentage-point gap "
                 "recomputed in our sandbox [1][2][sandbox:t1]."),
        "citations": [1, 2],
        "sandbox_ref": "t1",
    },
    {
        "heading": "Failure modes",
        "body": ("LLM self-verification fails when the same model grades its own "
                 "work without external execution; calibration is restored by "
                 "independent test runs in isolated sandboxes [3]."),
        "citations": [3],
    },
]

MOCK_VERIFY = [
    {"claim": "Agents verify code by executing tests in sandboxes", "confidence": 0.92, "supported_by": [1, 3]},
    {"claim": "74.7% vs 41.9% pass rates, 32.8pp gap", "confidence": 0.97, "supported_by": [1, 2, "sandbox:t1"]},
    {"claim": "Self-critique alone is unreliable", "confidence": 0.88, "supported_by": [3]},
]

MOCK_SANDBOX_T1 = (
    "SWE-bench Verified: 74.7%\n"
    "SWE-bench Multimodal: 41.9%\n"
    "delta_pp: 32.8\n"
)


def mock_response(stage: str, user: str) -> str:
    if stage == "plan":
        return json.dumps(MOCK_PLAN)
    if stage == "draft":
        return json.dumps(MOCK_DRAFT_SECTIONS)
    if stage == "verify":
        return json.dumps(MOCK_VERIFY)
    return f"[mock:{stage}] {user[:80]}"
