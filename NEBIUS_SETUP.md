# NEBIUS_SETUP.md — going live on Nebius Token Factory

Everything Trace needs is env-config; no code changes. Do NOT commit keys.

## 1. Get credits (recommended)

Enroll in the **Nebius Builder Program** at **https://dev.nebius.com** —
it grants credits usable on Token Factory inference and Tavily. This is the
fastest path to a funded key.

## 2. Create a Token Factory API key

1. Sign in at https://dev.nebius.com (or tokenfactory.nebius.com console).
2. Create an API key for Token Factory inference.
3. Confirm the inference base URL in the dashboard; the current
   OpenAI-compatible endpoint is:

```
https://api.tokenfactory.nebius.com/v1
```

## 3. Confirm model IDs on your account

Model IDs are namespaced and case-sensitive. List exactly what's live for you:

```bash
curl -s "$NEBIUS_BASE_URL/models" -H "Authorization: Bearer $NEBIUS_API_KEY"
```

Trace's defaults (live on Token Factory as of Sep 2026):

| Tier | Model ID | Notes |
|---|---|---|
| planner / verifier | `nvidia/nemotron-3-super-120b-a12b` | 120B/12B active MoE, 1M context, native function calling, reasoning toggle |
| drafter | `nvidia/nemotron-3-nano-30b-a3b` | 30B/3B active, ~$0.06/$0.24 per M tokens, fast, JSON mode |

Note: a ~500B "Nemotron 3 Ultra" tier was not confirmed live on Token Factory
as of Sep 2026. If it ships, add it to `TIERS` in `trace/config.py` and point
`STAGE_TIER["plan"]` / `["verify"]` at it — one-line change.

## 4. Environment

```bash
export NEBIUS_API_KEY="tf-..."                                  # Token Factory key
export NEBIUS_BASE_URL="https://api.tokenfactory.nebius.com/v1"  # confirm in console
export TAVILY_API_KEY="tvly-..."                                 # https://tavily.com
# Sandbox backend: Token Factory Sandboxes (isolated cloud microVMs)
export TRACE_SANDBOX_BACKEND=tokenfactory
export NEBIUS_SANDBOX_URL="https://<your-sandbox-endpoint>"       # confirm in dev.nebius.com console
export TRACE_SANDBOX_TIMEOUT=60
export TRACE_AUDIT_DIR=runs
```

Keep `TRACE_SANDBOX_BACKEND=local` (default) for offline dev — the same jobs
run in a restricted local subprocess.

## 5. Verify the live path

```bash
python -m trace.cli models          # must list nvidia/nemotron-3-* models
python -m trace.cli sandbox-demo    # backend=tokenfactory
python -m trace.cli research "How do frontier coding agents verify the code they write?"
# -> brief is DRAFT ONLY until you re-run with --auto-approve
```

## 6. Deploying on Nebius AI Cloud (optional)

Trace is a plain Python app with no exotic deps, so it ports directly:

- **Serverless Jobs**: package the repo (`python:3.12-slim` + `pip install openai requests`),
  entrypoint `python -m trace.cli research "$QUERY" --auto-approve`, inject the env
  vars above as secrets. Good for scheduled/queued research runs.
- **Serverless Endpoints**: wrap `Orchestrator.run` in a FastAPI app exposing
  `POST /research` (returns brief markdown + audit run_id). Deploy as a
  Token Factory-compatible endpoint for a hosted demo URL.
- **DevPods**: interactive dev against live Token Factory from the cloud.

## Troubleshooting

- `401` from the inference endpoint → key is for the wrong product (AI Cloud
  vs Token Factory) or missing the `tf-` prefix; regenerate in the Token
  Factory section of the console.
- `404` on a model ID → copy exact casing from `/models`; Nemotron IDs are
  `nvidia/...` namespaced.
- Sandbox `execute` 404 → the sandbox path is account-specific; confirm the
  exact execution URL in the console (see `trace/sandbox.py::_execute_tokenfactory`).
