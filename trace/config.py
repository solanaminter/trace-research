"""Configuration: Nebius Token Factory + NVIDIA Nemotron tiers, Tavily, sandboxes.

Everything sensitive comes from env vars. Model IDs below are the Nemotron
models served live on Nebius Token Factory (OpenAI-compatible endpoint);
the full list for an account is always:
    curl $NEBIUS_BASE_URL/models -H "Authorization: Bearer $NEBIUS_API_KEY"
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


# --- Nebius Token Factory -----------------------------------------------------
NEBIUS_BASE_URL = os.environ.get(
    "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"
)
NEBIUS_API_KEY = os.environ.get("NEBIUS_API_KEY", "")

# --- NVIDIA Nemotron model tiering --------------------------------------------
# reasoning:  "on"  -> full chain-of-thought (slow, best quality)
#             "low"  -> minimal thinking (fast, cheap)
#             "off"  -> direct answer
#
# NOTE (verified 2026-09-15 via live /models call): Nemotron 3 Ultra 550B IS live
# on Token Factory as nvidia/Nemotron-3-Ultra-550b-a55b (added as "ultra" tier
# below). Model IDs are case-sensitive — always confirm against /models.
@dataclass
class Tier:
    model_id: str
    reasoning: str
    use: str


TIERS: dict[str, Tier] = {
    "planner": Tier(
        model_id="nvidia/nemotron-3-super-120b-a12b",  # verified live 2026-09-15 via /models
        reasoning="on",
        use="Research-plan generation, multi-step decomposition, heavy reasoning",
    ),
    "drafter": Tier(
        model_id="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",  # verified live 2026-09-15; IDs are case-sensitive
        reasoning="low",
        use="High-volume section drafting, summarization, extractive QA",
    ),
    "verifier": Tier(
        model_id="nvidia/nemotron-3-super-120b-a12b",
        reasoning="on",
        use="Claim-by-claim verification against cited sources, confidence scoring",
    ),
    # Optional: Nemotron 3 Ultra 550B is live on Token Factory (verified 2026-09-15).
    # Point STAGE_TIER["plan"]/["verify"] at "ultra" when credits allow — best quality, highest cost.
    "ultra": Tier(
        model_id="nvidia/Nemotron-3-Ultra-550b-a55b",
        reasoning="on",
        use="Flagship reasoning tier (550B); swap in for planner/verifier when funded",
    ),
}

STAGE_TIER = {
    "plan": "planner",
    "draft": "drafter",
    "verify": "verifier",
}

# --- Tavily (Best Use of Tavily $3k prize integration) -------------------------
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
TAVILY_BASE_URL = os.environ.get("TAVILY_BASE_URL", "https://api.tavily.com")

# --- Token Factory Sandboxes ---------------------------------------------------
# Sandboxes run generated data-analysis code in an isolated Nebius cloud
# environment (Firecracker microVMs). Endpoint is account-specific; confirm in
# dev.nebius.com console. `sandbox execute --backend tokenfactory` uses it,
# `local` runs the same jobs in a restricted local subprocess (mock/dev).
SANDBOX_BACKEND = os.environ.get("TRACE_SANDBOX_BACKEND", "local")
SANDBOX_API_URL = os.environ.get("NEBIUS_SANDBOX_URL", "")
SANDBOX_TIMEOUT_S = int(os.environ.get("TRACE_SANDBOX_TIMEOUT", "60"))

# --- Trace behavior ------------------------------------------------------------
MOCK = os.environ.get("TRACE_MOCK", "") not in ("", "0", "false")  # deterministic mock shim
AUDIT_DIR = os.environ.get("TRACE_AUDIT_DIR", "runs")
MAX_TOOL_CALLS_PER_STAGE = 12


@dataclass
class Settings:
    nebius_base_url: str = NEBIUS_BASE_URL
    nebius_api_key: str = NEBIUS_API_KEY
    tiers: dict[str, Tier] = field(default_factory=lambda: TIERS)
    tavily_api_key: str = TAVILY_API_KEY
    tavily_base_url: str = TAVILY_BASE_URL
    sandbox_backend: str = SANDBOX_BACKEND
    sandbox_api_url: str = SANDBOX_API_URL
    sandbox_timeout_s: int = SANDBOX_TIMEOUT_S
    mock: bool = MOCK
    audit_dir: str = AUDIT_DIR

    def require_live_nebius(self) -> None:
        if not self.nebius_api_key:
            raise RuntimeError(
                "NEBIUS_API_KEY is not set. See NEBIUS_SETUP.md for key creation. "
                "Or run with TRACE_MOCK=1 for the deterministic offline shim."
            )
