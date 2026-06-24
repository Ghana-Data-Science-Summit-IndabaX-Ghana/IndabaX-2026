# 2. Shared `core` package with dependency-injected teaching artifacts

Date: 2026-06-15

## Status

Accepted

## Context

The same Base → RAG → Guardrails logic must run in two places: the participant **Colab notebook** and the **FastAPI demo backend**. If they drift, the projected demo stops matching what participants build — which defeats the progressive demo.

But the session is pedagogically built on participants **reading and editing** the teaching code (walk the system prompt line by line, open the retrieval function, edit a query, add a guardrail rule). If that code is hidden inside an imported package, the audit-the-code pedagogy collapses.

So: single source of truth (no drift) vs. editable inline code (pedagogy). A naive choice sacrifices one.

## Decision

A shared, pip-installable `core` package owns all **plumbing**: provider adapters, `MOCK_MODE`, the knowledge base, the logger, the observability summarizer, and a **runner** that takes the teaching artifacts (system prompts, retrieve function, guardrail functions) as **arguments** (dependency injection).

- FastAPI calls the runner with `core`'s default artifacts.
- The notebook installs `core` from GitHub (`%pip install git+https://…`) for plumbing, but **defines the teaching artifacts inline as editable cells** and passes them into the same runner. `core` ships byte-identical defaults.

## Consequences

- Plumbing has one source → no drift. The demo executes the *same runner* as the notebook → parity holds for everything except what a participant deliberately edits (which is the exercise).
- The teaching surface stays inline and editable.
- The notebook depends on a public GitHub repo and network at install time; `!git clone` is the documented fallback.
- The teaching artifacts exist in two places (inline cells + package defaults). They are short and reviewed; the runner contract keeps them interchangeable. This is the accepted residual duplication.
