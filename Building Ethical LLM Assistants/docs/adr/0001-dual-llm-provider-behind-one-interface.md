# 1. Support two LLM providers (Anthropic + Gemma) behind one interface

Date: 2026-06-15

## Status

Accepted

## Context

The hands-on needs an LLM backend for the credit-access assistant. Two candidates were on the table:

- **Anthropic Claude Haiku 4.5** — $1 / $5 per 1M tokens; native `system=` parameter.
- **Google Gemma 4** — free tier (input/output/caching free), via the `google-genai` SDK; no system role; free tier states "content used to improve our products."

For a 90-minute workshop, the dominant cost control is `MOCK_MODE` (canned responses, zero API calls), so live cost is marginal either way. Supporting both doubles the surface to test before standing in front of the room.

## Decision

Build a thin `LLMProvider` interface in `core` with two adapters — Anthropic and Gemma — selectable by config and by a toggle visible on the facilitator demo. Both work day one. The Gemma adapter normalizes the missing system role by prepending the system prompt to the user turn.

## Consequences

- "Switch if needed" is a one-line config flip, and the demo can flip providers live.
- Gemma's "free tier trains on your data" becomes a deliberate, live teaching moment for the consent/privacy module — the contradiction is the lesson.
- `MOCK_MODE` mocks become **provider-aware** (keyed by scenario × stage × provider) so the Anthropic-vs-Gemma difference still shows with no network.
- The same system prompt may be adhered to differently across providers (native system vs prepend) — itself a representation/faithfulness teaching point, but it means demo outputs are not identical across providers.
- Cost: negligible. Complexity: a second SDK, a second auth path, and provider-aware mock data to author.
