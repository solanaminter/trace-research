"""Nebius Token Factory inference client (OpenAI-compatible) + mock shim.

Real path: OpenAI SDK pointed at https://api.tokenfactory.nebius.com/v1 with a
Nebius Token Factory API key, calling NVIDIA Nemotron models with per-tier
reasoning effort (chat_template_kwargs.enable_thinking / effort control).

Mock path (TRACE_MOCK=1): deterministic, offline responses recorded in
trace/mock_data.py so tests, evals and the demo run with no key and no network.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field

from . import config
from . import mock_data


@dataclass
class LLMCall:
    tier: str
    model_id: str
    reasoning: str
    prompt: str
    response: str
    latency_ms: int
    prompt_hash: str = ""
    mock: bool = False


@dataclass
class NebiusClient:
    settings: config.Settings = field(default_factory=config.Settings)

    def __post_init__(self) -> None:
        self._real = None  # lazily created openai.OpenAI

    # -- internal -----------------------------------------------------------
    def _live_client(self):
        self.settings.require_live_nebius()
        if self._real is None:
            from openai import OpenAI

            self._real = OpenAI(
                base_url=self.settings.nebius_base_url,
                api_key=self.settings.nebius_api_key,
            )
        return self._real

    # -- public --------------------------------------------------------------
    def chat(self, stage: str, system: str, user: str, *, max_tokens: int = 2048,
             json_mode: bool = False) -> LLMCall:
        """Run one tiered inference call for a pipeline stage."""
        tier_name = config.STAGE_TIER[stage]
        tier = self.settings.tiers[tier_name]
        t0 = time.time()

        if self.settings.mock:
            response = mock_data.mock_response(stage, user)
            mock = True
        else:
            client = self._live_client()
            extra: dict = {}
            # Nemotron reasoning effort control (NVIDIA NIM-style chat template kwargs)
            if tier.reasoning == "off":
                extra["chat_template_kwargs"] = {"enable_thinking": False}
            elif tier.reasoning == "low":
                extra["chat_template_kwargs"] = {"enable_thinking": True, "thinking_budget": 512}
            resp = client.chat.completions.create(
                model=tier.model_id,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=max_tokens,
                response_format={"type": "json_object"} if json_mode else None,
                extra_body=extra or None,
            )
            response = resp.choices[0].message.content or ""
            mock = False

        latency_ms = int((time.time() - t0) * 1000)
        return LLMCall(
            tier=tier_name,
            model_id=tier.model_id,
            reasoning=tier.reasoning,
            prompt=user,
            response=response,
            latency_ms=latency_ms,
            prompt_hash=hashlib.sha256(user.encode()).hexdigest()[:12],
            mock=mock,
        )

    def models(self) -> list[str]:
        """List models available on the account (live) or tier models (mock)."""
        if self.settings.mock:
            return [t.model_id for t in self.settings.tiers.values()]
        client = self._live_client()
        return [m.id for m in client.models.list().data]
