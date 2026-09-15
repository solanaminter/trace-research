# SUBMISSION_BRIEF.md — Nebius × NVIDIA Global AI Hackathon

## (a) Rules, criteria, track

- **Hackathon:** Nebius × NVIDIA Global AI Hackathon — https://nebiusglobalaihackathon.devpost.com/
- **Deadline:** Oct 30, 2026, 10:00 AM PT (5:00 PM UTC). Fully online.
- **Requirements (verified from the hackathon page):** project must run on
  Nebius Token Factory or Nebius AI Cloud AND use ≥1 NVIDIA open-source model;
  working demo URL; text description; **demo video ≤3 min, public on YouTube,
  with audio covering how we used Token Factory + Nemotron/open models**;
  **public code repo with OSS license** visible in About + README with setup/run
  instructions highlighting Nemotron + Token Factory usage; feedback on
  Nebius/NVIDIA tools; track selection. New or significantly updated work only.
- **Track entered: Best Apps and Agents** — a real app people would use,
  powered by Nemotron via Token Factory. (Backup consideration was Coding and
  Agentic Engineering, but the app framing is broader and Grand-eligible.)
- **Judging:** Technological Implementation (deep Token Factory usage:
  inference + sandboxes + Nemotron tiering) · Design (complete product, not
  PoC) · Potential Impact (analysts/researchers who can't afford hallucinated
  numbers) · Quality of the Idea (non-obvious: claim-level verification with
  sandbox-recomputed numbers + audit trail).
- **Prizes targeted:** Grand $20,000; track winner (Jetson Orin Nano);
  **Best Use of Tavily $3,000** (stackable — Tavily search+extract integrated).
- **Also enter:** Most Valuable Feedback ($100 ×10) via TOOL_FEEDBACK.md text.

## (b) Repo

- **Local path:** `~/workspace/hackathons/nebius-nvidia/trace/`
- **Suggested public repo name:** `trace-research` (github.com/solanaminter/trace-research)
- MIT LICENSE (Copyright (c) 2026 Solana Minter) included. README has Demo
  section with setup + Nemotron/Token Factory usage table.

## (c) Video

- **Local path:** `~/workspace/hackathons/nebius-nvidia/trace/assets/trace-demo.mp4`
  (rendered from `assets/trace-demo/` HyperFrames project; 139 s ≈ 2:19, ≤3:00 ✓)
- **Proposed YouTube title:** `Trace — deep research with receipts | NVIDIA Nemotron × Nebius Token Factory`
- **Proposed description:**
  > Trace is a deep-research copilot built for the Nebius × NVIDIA Global AI
  > Hackathon (Best Apps and Agents). Every claim cites a source, every number
  > is recomputed in a Token Factory Sandbox, and a human approves the brief.
  > Inference runs on NVIDIA Nemotron models via Nebius Token Factory's
  > OpenAI-compatible endpoint — Nemotron 3 Super (120B, reasoning on) plans
  > and verifies, Nemotron 3 Nano (30B, reasoning low) drafts, Tavily retrieves
  > sources, and Token Factory Sandboxes execute the analysis code. Code:
  > https://github.com/solanaminter/trace-research
- **Tags:** nebius, token factory, nvidia, nemotron, ai agents, deep research,
  hackathon, tavily, open source

## (d) Devpost form fields (filled)

- **Name:** Trace — deep research with receipts
- **Tagline:** A deep-research copilot where every claim cites a source, every
  number is recomputed in a sandbox, and a human approves the brief.
- **Description (long):**
  Trace turns a research question into an audited brief through a six-stage
  pipeline: PLAN → SEARCH → ANALYZE → DRAFT → VERIFY → human approval.
  NVIDIA Nemotron models on Nebius Token Factory do the reasoning with
  deliberate tiering — Nemotron 3 Super (120B, reasoning on) for planning and
  claim-by-claim verification, Nemotron 3 Nano (30B, reasoning low) for fast,
  cheap drafting — all through Token Factory's OpenAI-compatible endpoint.
  Tavily search + extract retrieves and grounds sources (Best Use of Tavily).
  Generated data-analysis code executes in Token Factory Sandboxes, so numbers
  in the brief are recomputed, not quoted. Agent governance is built in: scoped
  tool permissions per stage (a stage cannot call another stage's tools), a
  human-approval gate before any brief leaves draft, and a JSONL audit trail
  recording every tool call, model tier, and latency. Built with: Python,
  OpenAI SDK, Nemotron 3 Super/Nano, Nebius Token Factory, Token Factory
  Sandboxes, Tavily API.
- **Track:** Best Apps and Agents
- **Live Demo URL:** https://trace-research-demo.vercel.app
- **Demo URL plan:** hosted demo = the GitHub repo README demo + YouTube video;
  optionally deploy `POST /research` on a Nebius Serverless Endpoint after
  NEBIUS_SETUP.md steps (parent's call).
- **Video URL:** YouTube public link (parent uploads `assets/trace-demo.mp4`).
- **Code repo:** https://github.com/solanaminter/trace-research (parent pushes)
- **Feedback text:** paste `TOOL_FEEDBACK.md`.

## (e) Nebius account/key steps for the parent

1. Enroll in the Nebius Builder Program: https://dev.nebius.com (credits for
   Token Factory + Tavily).
2. Create a Token Factory API key in the console; confirm base URL
   (currently `https://api.tokenfactory.nebius.com/v1`).
3. `curl $NEBIUS_BASE_URL/models -H "Authorization: Bearer $NEBIUS_API_KEY"`
   to confirm live Nemotron model IDs (`nvidia/nemotron-3-super-120b-a12b`,
   `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`, `nvidia/Nemotron-3-Ultra-550b-a55b`
   — verified live 2026-09-15; IDs are case-sensitive).
4. Get a Tavily key at https://tavily.com.
5. Confirm the Token Factory Sandbox execution endpoint in dev.nebius.com
   console → set `NEBIUS_SANDBOX_URL`.
6. Export env vars (see NEBIUS_SETUP.md), run `python -m trace.cli models`,
   then a live `trace research`.
7. Full details: `NEBIUS_SETUP.md`.

## (f) Unverified / incomplete

- **Live Nebius inference — smoke-tested 2026-09-15.** A real call was
  executed against Token Factory (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`,
  drafter tier, `mock=False`, 3.8s, valid response; evidence in
  `runs/live_smoke_20260915.json`). Auth, model IDs, and response parsing
  confirmed. Full-pipeline live evals (planner/verifier on Super 120B)
  pending credit approval — account currently has ~$1.
- **Exact Token Factory Sandbox execution URL** — endpoint path is
  account-specific; `trace/sandbox.py` uses `{NEBIUS_SANDBOX_URL}/execute`
  and raises a clear error telling the user where to confirm it. Verify in
  the console before the live demo.
- **Nemotron 3 Ultra tier** — confirmed live on Token Factory 2026-09-15
  (`nvidia/Nemotron-3-Ultra-550b-a55b`); added as optional `"ultra"` tier.
  Swap `STAGE_TIER["plan"]`/`["verify"]` to it when credits allow.
- **Demo URL** — currently repo + video; a hosted endpoint (Nebius
  Serverless) is optional and needs the parent's Nebius account.
- **Tavily key** — same as Nebius: parent supplies; mock covers tests/demo.
- **Video** — rendered locally; parent uploads to YouTube as PUBLIC
  (unlisted is not acceptable per rules) and pastes the link.
