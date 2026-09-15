"""Tavily web-search integration (Best Use of Tavily prize track).

Real path: https://api.tavily.com/search + /extract with TAVILY_API_KEY.
Mock path (TRACE_MOCK=1): deterministic sources from mock_data.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import requests

from . import config, mock_data


@dataclass
class Source:
    title: str
    url: str
    snippet: str
    score: float = 0.0


@dataclass
class TavilyClient:
    settings: config.Settings = field(default_factory=config.Settings)

    def _headers(self) -> dict:
        if not self.settings.tavily_api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not set. Get one at https://tavily.com "
                "or run with TRACE_MOCK=1."
            )
        return {"x-api-key": self.settings.tavily_api_key, "Content-Type": "application/json"}

    def search(self, query: str, *, max_results: int = 5, search_depth: str = "advanced") -> list[Source]:
        if self.settings.mock:
            return [Source(**s, score=0.9 - i * 0.05) for i, s in enumerate(mock_data.MOCK_SOURCES)]
        t0 = time.time()
        r = requests.post(
            f"{self.settings.tavily_base_url}/search",
            headers=self._headers(),
            json={
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": False,
            },
            timeout=30,
        )
        r.raise_for_status()
        out = []
        for i, item in enumerate(r.json().get("results", [])):
            out.append(Source(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", "")[:600],
                score=item.get("score", 1.0 - i * 0.05),
            ))
        return out

    def extract(self, urls: list[str]) -> dict[str, str]:
        """Pull full text for the top sources (used by the verifier stage)."""
        if self.settings.mock:
            return {s["url"]: s["snippet"] * 4 for s in mock_data.MOCK_SOURCES}
        r = requests.post(
            f"{self.settings.tavily_base_url}/extract",
            headers=self._headers(),
            json={"urls": urls, "extract_depth": "advanced"},
            timeout=60,
        )
        r.raise_for_status()
        return {it["url"]: it.get("raw_content", "")[:8000] for it in r.json().get("results", [])}
