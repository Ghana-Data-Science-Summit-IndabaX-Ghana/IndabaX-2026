# 3. FastAPI backend stays off Cloudflare Workers; two-repo split; local for the room

Date: 2026-06-15

## Status

Accepted

## Context

The facilitator demo is a Next.js frontend the facilitator wants to deploy to **Cloudflare Workers**, backed by a **FastAPI** service (the mandated "Python + FastAPI for all backend work"). Cloudflare Workers is a V8/edge runtime; its Python Workers are Pyodide-based (beta), do not run the `uvicorn`/ASGI server model, and choke on packages with native deps — which includes the HTTP stack the Anthropic and Google SDKs sit on. FastAPI and Cloudflare Workers cannot both be true for the same service.

The demo is projector-only and read-only for participants; it never needs to be publicly reachable during the session.

## Decision

- **Two repos.** `assist-demo` (Next.js → Cloudflare Workers) stays its own repo because it has its own deploy target and config. `llm-assistants` holds `core`, `backend/` (FastAPI), `notebooks/`, and `ai-int/`.
- The **FastAPI backend runs locally on the facilitator's laptop** during the session (it can even run fully in `MOCK_MODE`). A container host (Fly/Render) is documented as a post-event option — **never Cloudflare Workers**.
- No keys in either tree; `.env` gitignored, `.env.example` committed (the repos are public).

## Consequences

- Honors both "Python + FastAPI backend" and "demo on Cloudflare" by splitting where each runs.
- Most reliable room setup: no tunnel, no public backend, no connectivity dependency for the demo.
- A Cloudflare-hosted frontend cannot reach a laptop backend without a tunnel — so for the live room, the frontend also runs locally; the Cloudflare deploy is for sharing the demo after the event.
- Two repos means two clone/install paths; the README in each must be self-sufficient.
