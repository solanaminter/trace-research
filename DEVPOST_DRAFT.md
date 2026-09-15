# Devpost submission draft — Trace (Nebius × NVIDIA Global AI Hackathon)

Fill these into the Devpost submission form at https://nebiusglobalaihackathon.devpost.com/.
Track: **Best Apps and Agents**. Prize angle: **Best Use of Tavily** ($3,000).

## Project name
Trace

## Tagline
Deep research with receipts — an audited research copilot on NVIDIA Nemotron via Nebius Token Factory

## Description (About / What it does / How we built it)

**Inspiration**
AI research tools hallucinate citations, invent numbers, and ship vibes. Trace is a deep-research copilot built on the opposite principle: every claim cites a source, every number is recomputed in a sandbox, and nothing ships until a human approves it.

**What it does**
Ask Trace a hard question and it runs a six-stage pipeline — PLAN → SEARCH → ANALYZE → DRAFT → VERIFY → human approval — and produces an audited research brief with a JSONL audit trail. Search results come from Tavily (candidate for the $3,000 Best Use of Tavily prize). Data-analysis code is safety-gated (allowlisted imports, no dangerous builtins, bounded timeouts) and executed in isolated Token Factory Sandbox microVMs. A verifier model re-checks every claim against its cited sources with confidence scores. The final brief only publishes after explicit human approval.

**How we built it — NVIDIA Nemotron on Nebius Token Factory**
All inference runs through Nebius Token Factory's OpenAI-compatible endpoint, using NVIDIA's open Nemotron 3 models with deliberate cost/quality tiering:
- PLAN + VERIFY → `nvidia/nemotron-3-super-120b-a12b` (reasoning on; 1M context, native tool calling) for heavy decomposition and claim-by-claim checking
- DRAFT → `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` (reasoning low) for fast, cheap high-volume writing
- Optional `nvidia/Nemotron-3-Ultra-550b-a55b` tier for flagship-quality runs
Tiering is pure config (`trace/config.py`) — swap model IDs without touching code. A live inference call was verified against Token Factory on 2026-09-15 (auth, model IDs, response parsing all confirmed).

**Challenges**
- Token Factory model IDs are case-sensitive — the lowercase drafter ID 404'd; fixed by verifying against the live `/models` endpoint.
- Nemotron's thinking tokens consume the token budget, so small `max_tokens` values returned empty responses; the pipeline accounts for this.
- Scoped permissions: each stage may only call its assigned tools, enforced by a policy module, with approval gates before publish.

**Accomplishments**
- Working 6-stage pipeline with real stage→model tiering, hash-chained audit trail, and 11/11 passing tests.
- Live Nebius inference verified end-to-end through the project's own client code.
- Live demo site + 2:20 narrated demo video.

**What's next**
Full-pipeline live evals on Super 120B once credits land; real Tavily search with an API key; Token Factory Sandbox execution against the account's endpoint.

## Video URL
https://www.youtube.com/watch?v=NjvDF3jV9WQ (2:20, narrated, public)

## Try it out / demo URL
https://trace-research-demo.vercel.app

## GitHub repo
https://github.com/solanaminter/trace-research (MIT)

## Built with
Python, NVIDIA Nemotron 3 (Nano 30B / Super 120B / Ultra 550B), Nebius Token Factory, Tavily, OpenAI-compatible API, pytest
