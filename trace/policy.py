"""Scoped tool permissions: each pipeline stage may call only its tools.

Enforced in code by the orchestrator — a stage cannot reach for tools outside
its scope, so a compromised/creative model output cannot exfiltrate data or
run code where it shouldn't.
"""
from __future__ import annotations

STAGE_TOOLS: dict[str, frozenset[str]] = {
    "plan": frozenset({"llm:planner"}),
    "search": frozenset({"tavily:search"}),
    "extract": frozenset({"tavily:extract"}),
    "analyze": frozenset({"sandbox:execute"}),
    "draft": frozenset({"llm:drafter"}),
    "verify": frozenset({"llm:verifier", "tavily:extract"}),
    "approve": frozenset({"human:approve"}),
    "assemble": frozenset(),  # pure local code, no tools
}


class PermissionError(RuntimeError):
    pass


def check(stage: str, tool: str) -> None:
    allowed = STAGE_TOOLS.get(stage)
    if allowed is None:
        raise PermissionError(f"unknown stage: {stage}")
    if tool not in allowed:
        raise PermissionError(
            f"stage '{stage}' may not call tool '{tool}' "
            f"(allowed: {sorted(allowed) or 'none'})"
        )


def allowed_tools(stage: str) -> list[str]:
    return sorted(STAGE_TOOLS[stage])
