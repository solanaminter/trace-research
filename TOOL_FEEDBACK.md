# TOOL_FEEDBACK.md — feedback on Nebius Token Factory + NVIDIA tooling

(Paste into the hackathon's "feedback on Nebius/NVIDIA tools" field.)

## What we built

**Trace** — a deep-research copilot where every claim cites a source and every
number is recomputed in a sandbox. Inference runs on NVIDIA Nemotron models
via Nebius Token Factory's OpenAI-compatible endpoint, with deliberate model
tiering (Super 120B for planning/verification, Nano 30B for drafting) and
data-analysis jobs executed in Token Factory Sandboxes.

## What worked well

- **Token Factory's OpenAI-compatible API made integration trivial.** Pointing
  the `openai` SDK at `https://api.tokenfactory.nebius.com/v1` with a Bearer
  key and swapping the `model` string to `nvidia/nemotron-3-*` was the entire
  integration surface. Tiering (Nano vs Super) became a one-line config change.
- **Nemotron reasoning effort control is genuinely useful for agents.**
  Reasoning-off Nano for high-volume drafting and reasoning-on Super for
  planning/verification gave us a clean cost/latency/quality tradeoff per
  pipeline stage — this kind of knob is exactly what agentic pipelines need.
- **Native function calling on Nemotron 3 Super worked for our plan stage**,
  and 1M context meant we could feed full extracted source texts to the
  verifier without chunking gymnastics.

## Friction / requests

1. **Sandbox execution endpoint discovery was the hardest part.** The
   inference side is beautifully documented; the Token Factory Sandboxes API
   (exact execution URL, auth scope, job lifecycle) was not discoverable from
   public docs. We architected a pluggable client (`local` vs `tokenfactory`
   backend, env-configured endpoint) so the code path is real and testable,
   but we could not verify the live sandbox URL without console access. A
   public "Sandboxes quickstart" with a curl-able `/execute` example — like
   the inference quickstart — would unlock the Coding/Agentic Engineering track.
2. **Model availability clarity.** The ~500B Nemotron 3 Ultra tier discussed in
   hackathon materials was not confirmed live on Token Factory (community
   sources, June 2026); we built on Nano + Super, which are live and excellent.
   A public model-availability matrix (live / coming soon per tier) in the
   Token Factory console would save every team this research.
3. **Tavily credit via the Builder Program** — great that it's bundled; the
   signup-to-first-key path worked, but a single "hackathon starter" page
   linking Token Factory key + Tavily key + sandbox endpoint in one place
   would reduce drop-off.

## Most valuable

If we could only keep one thing: the **OpenAI-compatible endpoint + per-tier
reasoning control on Nemotron**. It turned "which model for which agent stage"
from a research project into a config file, and that is the whole reason Trace
could be built in days rather than weeks.
