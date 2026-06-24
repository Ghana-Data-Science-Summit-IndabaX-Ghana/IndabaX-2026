# Implementation Plan — Building Ethical LLM Assistants (Hands-On)

## Context

Working directory: `/Users/jessemurah/SWE/llm-assist/`
This directory IS the `llm-assistants` repo root (push to `King-Murah-s-Projects/llm-assistants`).
`assist-demo/` is a nested repo (its own git) — leave its `.git` alone; add it to `.gitignore`.

Glossary: see `CONTEXT.md`. Decisions: see `docs/adr/0001`–`0004`.
PRD: see `ai-int/ref/PRD-ethical-llm-hands-on.md`.
Existing code to keep/adapt: `ai-int/code/` (notebook, mocks, workshop_mocks.py).

## Architecture Summary

- `core/` — pip-installable shared package. Provider interface + two adapters (Anthropic, Gemma). MOCK_MODE (provider-aware canned responses). 4-doc knowledge base. Retrieval. 5-layer guardrail pipeline. Trust score. Structured logger. Observability summarizer. Runner (dependency-injected teaching artifacts).
- `backend/` — FastAPI. Single `POST /chat` endpoint. CORS for local frontend.
- `notebooks/` — Instructor source notebook (participant copy via nbconvert tag-strip).
- `assist-demo/` — Existing Next.js frontend (separate git repo, build on top of existing shell).
- `FACILITATOR_GUIDE.md` — Markdown runbook.

## Slices

### Slice 1 — Walking skeleton: Base assistant end-to-end [START HERE]

Scaffold the repo + `core` + base runner + FastAPI `/chat` (base mode) + tests.

**What to build:**

1. **Repo scaffold:**
   - `pyproject.toml` — makes `core` pip-installable via `pip install -e .` or `pip install git+https://github.com/King-Murah-s-Projects/llm-assistants.git`. Deps: `anthropic`, `fastapi`, `uvicorn`, `python-dotenv`, `pandas`, `matplotlib`.
   - `.gitignore` — ignore `assist-demo/` nested git, `.env`, `__pycache__`, `*.pyc`, `.venv`, `dist/`, `*.egg-info/`.
   - `.env.example` — `ANTHROPIC_API_KEY=`, `GOOGLE_API_KEY=`, `MOCK_MODE=true`, `DEFAULT_PROVIDER=anthropic`.
   - `README.md` — what this repo is, install steps (`%pip install git+https://...`), how to run backend locally, BYOK instructions.

2. **`core/` package:**
   - `core/__init__.py` — exports: `run_base`, `run_rag`, `run_guardrailed`, `MOCK_MODE`, `get_provider`.
   - `core/config.py` — reads `.env`; exposes `MOCK_MODE: bool`, `DEFAULT_PROVIDER: str`.
   - `core/providers.py` — `LLMProvider` abstract base (method: `complete(system: str, messages: list[dict]) -> str`). `AnthropicProvider(model="claude-haiku-4-5")` implementation using `anthropic` SDK with native `system=` param. Provider factory `get_provider(name: str) -> LLMProvider`.
   - `core/mocks.py` — Provider-aware mock store. Keys: `(scenario_id, stage, provider)` where `stage ∈ {"base","rag","guardrails"}` and `provider ∈ {"anthropic","gemma"}`. Reuse existing mock texts from `ai-int/code/workshop_mocks.py` as the Anthropic/base mocks. `get_mock(message, stage, provider) -> str`.
   - `core/knowledge_base.py` — The 4 existing Ghana docs from `ai-int/code/ethical_llm_workshop.ipynb` as a typed list of dicts `{id, title, content, source, verified}`. `retrieve_relevant_documents(query, knowledge_base, top_k=2) -> list[dict]`. `format_retrieved_context(docs) -> str`.
   - `core/prompts.py` — `BASE_SYSTEM_PROMPT`, `RAG_SYSTEM_PROMPT`. Each rule in each prompt tagged with its OWASP id in a comment.
   - `core/runner.py` — `run_base(message, provider_name, history=None) -> dict`. Returns `{reply, provider, model, mock, history}`. Uses `MOCK_MODE` flag — when True, bypasses provider and returns `get_mock(message, "base", provider_name)`.
   - `core/logging.py` — `make_log_entry(**kwargs) -> dict` with fields: `timestamp, query, provider, model, mock, stage, retrieved_ids, retrieved_titles, input_flags, output_flags, trust_score, escalated, blocked_pre_llm, tokens_saved_estimated, response`.

3. **`backend/` package:**
   - `backend/__init__.py`
   - `backend/main.py` — FastAPI app. CORS middleware (allow all origins for local dev). `POST /chat` accepting `{mode, message, provider}` returning the unified envelope: `{reply, provider, model, mock, retrieval_log, guardrail_report}`. For Slice 1: only `mode="base"` is wired; `mode="rag"` and `mode="guardrails"` return 501 Not Implemented. `retrieval_log` and `guardrail_report` are null for base mode.
   - `backend/run.py` — `if __name__ == "__main__": uvicorn.run(...)` entry point.

4. **Tests:**
   - `tests/__init__.py`
   - `tests/test_runner.py` — In MOCK_MODE, `run_base` with each of the 7 scenario inputs returns a dict with all required keys and a non-empty `reply`. Provider name appears in the result.
   - `tests/test_api.py` — FastAPI `TestClient`. `POST /chat` with `mode="base"` returns 200 with the required envelope keys. `mode="rag"` returns 501.

**Acceptance criteria:**
- `pip install -e .` succeeds from the root.
- `MOCK_MODE=true python -m pytest tests/ -q` passes all tests.
- `MOCK_MODE=true uvicorn backend.main:app` starts without error.
- `POST /chat {"mode":"base","message":"hello","provider":"anthropic"}` returns the envelope in MOCK_MODE.
- `.env` is gitignored; `.env.example` is committed.

---

### Slice 2 — RAG stage end-to-end

**Blocked by:** Slice 1

**What to build:**

1. `core/rag.py` — `run_rag(message, provider_name, history=None, knowledge_base=None, retrieve_fn=None) -> dict`. Returns `{reply, provider, model, mock, history, retrieval_log: {query, retrieved_doc_ids, retrieved_doc_titles, response}}`. `knowledge_base` and `retrieve_fn` are the DI injection points (default to `core.knowledge_base.KNOWLEDGE_BASE` and `core.knowledge_base.retrieve_relevant_documents`). In MOCK_MODE, returns `get_mock(message, "rag", provider_name)` with the retrieval log still computed from the real retrieve function (so logs are instructive offline).

2. Wire `mode="rag"` in `backend/main.py`.

3. Tests: RAG scenarios 6 and 7 (hidden-fees, APR) retrieve the expected doc ids in MOCK_MODE. Retrieval log is present and non-empty in the envelope.

4. In the notebook (Slice 7), the RAG teaching artifacts will be the inline cells — for now just ensure `run_rag` accepts them as args.

**Acceptance criteria:**
- `run_rag` returns a `retrieval_log` with `retrieved_doc_ids`.
- Injection and Pidgin scenarios retrieve 0 docs (no match) and the log reflects that.
- All existing tests still pass.

---

### Slice 3 — Guardrailed stage end-to-end

**Blocked by:** Slice 2

**What to build (five visibly-separate layers + trust score):**

1. `core/guardrails.py`:
   - `validate_input(message: str) -> dict` — returns `{blocked: bool, flags: list[str], blocked_pre_llm: bool, tokens_saved_estimated: int}`. Flags if message contains known injection patterns (`"ignore previous"`, `"ignore your instructions"`, `"approve my loan"`, `"bypass"`, `"override"`). If blocked, returns immediately with `tokens_saved_estimated = len(message)//4`. OWASP label: LLM01.
   - `filter_output(reply: str, retrieved_docs: list[dict]) -> dict` — returns `{flags: list[str], trust_score: float}`. Start at 1.0. Subtract 0.35 for each guarantee/certainty phrase (`"you will definitely"`, `"guaranteed"`, `"I can confirm"`, `"you are approved"`, `"100% certain"`). Subtract 0.25 if reply references a claim the retrieved docs don't ground (no retrieved docs + specific numerical claim). Subtract 0.15 for hedge-free overclaiming. Clamp 0.0–1.0. OWASP label: LLM09.
   - `compute_trust_score(output_flags, retrieved_docs) -> float` — called inside filter_output; documented separately so it's a named, inspectable step in the pipeline.
   - `should_escalate(message: str, trust_score: float) -> bool` — returns True if `trust_score < 0.4` OR message contains high-stakes triggers (`"final decision"`, `"approve"`, `"legal advice"`, `"guarantee"`, `"distress"`, `"emergency"`). OWASP label: LLM06.
   - `ESCALATION_RESPONSE: str` — the simulated human-escalation reply.
   - `FALLBACK_RESPONSE: str` — the safe fallback for 0.4 ≤ score < 0.7.

2. `core/guardrailed.py` — `run_guardrailed(message, provider_name, history=None, knowledge_base=None, retrieve_fn=None, validate_input_fn=None, filter_output_fn=None, should_escalate_fn=None) -> dict`. Pipeline: validate_input → (if blocked: early return) → retrieve → model call → filter_output → trust_score band → escalation check → log. Returns full envelope including `guardrail_report: {input_flags, output_flags, trust_score, trust_band, escalated, blocked_pre_llm, tokens_saved_estimated, log_entry}`. All five layers explicitly named as steps in the function body with comments.

3. `core/runner.py` — update to also export `run_guardrailed`.

4. Wire `mode="guardrails"` in `backend/main.py`.

5. Tests:
   - Injection scenario (`"Ignore your previous instructions..."`) → `blocked_pre_llm=True`, `tokens_saved_estimated > 0`, no model call.
   - Certainty scenario (`"Will I definitely be approved..."`) → output flag `guarantee` → trust_score reduced → fallback or escalate band.
   - High-stakes trigger → escalated=True → reply is ESCALATION_RESPONSE.
   - Normal scenario passes through cleanly with trust_score ≥ 0.7.

6. `core/mocks.py` — add `"guardrails"` stage mocks for all 7 scenarios, both providers.

7. Type-one-guardrail exercise: add a `FILL_IN_GUARDRAIL_EXERCISE` constant / stub function in `core/guardrails.py` with a `TODO` comment and a docstring explaining what to add. The crafted mock reply for scenario 2 (Anthropic/guardrails) must contain `"you will definitely be approved"` so the participant's new rule catches it.

**Acceptance criteria:**
- Injection blocked pre-LLM with tokens_saved_estimated.
- Guarantee phrase caught by output filter; trust_score drops below baseline.
- High-stakes scenario escalates.
- All five layers (validate_input, filter_output, trust_score, should_escalate, logging) are distinct named functions called in sequence inside run_guardrailed.
- `guardrail_report` in the `/chat` envelope is fully populated.
- All tests pass.

---

### Slice 4 — Observability dashboard end-to-end

**Blocked by:** Slice 3

**What to build:**

1. `core/observability.py` — `summarize_logs(logs: list[dict]) -> dict`. Returns:
   - `total_requests: int`
   - `flagged_count: int` (any flag fired)
   - `blocked_pre_llm_count: int`
   - `violation_taxonomy: dict[str, int]` (flag type → count)
   - `total_tokens_saved_estimated: int`
   - `mock_mode: bool` (True if any log entry has mock=True)
   - `caveat: str` — `"estimated · illustrative in MOCK"` if mock_mode else `"estimated"`.

2. Backend: `GET /observability` returns `summarize_logs` over the session log (logs accumulated in-memory per backend process).

3. Frontend under-the-hood panel: add session observability tally (flagged count, tokens saved, mini violation-type bars). No charting library — pure CSS/SVG or plain numbers.

4. Tests: `summarize_logs` on a list of crafted log entries returns correct counts and taxonomy.

**Acceptance criteria:**
- `summarize_logs` returns all required fields.
- Caveat string is correct in MOCK vs live mode.
- `/observability` endpoint returns valid JSON.
- Demo panel shows the tally.

---

### Slice 5 — Gemma provider + projector toggle

**Blocked by:** Slice 3

**What to build:**

1. `core/providers.py` — add `GemmaProvider`. Verify the exact Gemma 4 model-id from Google's live docs at implementation time (do NOT guess; WebFetch `https://ai.google.dev/gemini-api/docs/models` and use the exact id). Use `google-genai` SDK (`from google import genai`). System prompt prepended to user turn as `"System: {system}\n\nUser: {message}"`. Same `complete(system, messages)` interface.

2. `core/config.py` — add `GOOGLE_API_KEY` env var.

3. `core/mocks.py` — ensure all existing mocks work with `provider="gemma"` (provider-aware keys exist for all scenarios × stages × providers). Gemma mocks should be slightly different from Anthropic mocks (different phrasing, less system-prompt faithful) to illustrate the faithfulness difference.

4. `core/providers.py` — factory: `get_provider("gemma")` returns `GemmaProvider`.

5. Backend: provider toggle already accepted in `/chat` `provider` field — wire to `GemmaProvider` when `provider="gemma"` and not MOCK_MODE.

6. Frontend: visible provider toggle (Anthropic ↔ Gemma). Provider/model badge in the response area and under-the-hood panel. Toggle is a live-mode action; in MOCK, it sends the provider name and returns provider-flavored mocks.

7. Tests: in MOCK_MODE, `provider="gemma"` returns a different mock text than `provider="anthropic"` for the same scenario/stage. All existing tests still pass.

**Acceptance criteria:**
- `GemmaProvider` uses the verified exact Gemma 4 model-id.
- Provider toggle visible in the demo UI.
- Provider-flavored mocks return different text for the two providers.
- All tests pass.

---

### Slice 6 — Three-Dimensional Assessment + export

**Blocked by:** Slices 3 + 4

**What to build:**

The assessment lives in the instructor notebook (Slice 7) but the export lives in `core`. Build the export mechanic here.

1. `core/export.py` — `export_assessment(audit_text: str, logs: list[dict], observability_summary: dict) -> str`. Returns a Markdown string structured as:
   ```
   # Three-Dimensional Assessment
   ## Technical Robustness (40%)
   [participant-filled sections from audit_text]
   ## Ethical Alignment (30%)
   [participant-filled sections + Stakeholder Engagement Plan]
   ## Observability & Efficiency (30%)
   [auto-generated from observability_summary]
   ## Prioritised Recommendations
   [participant-filled]
   ---
   ## Evidence
   ### Run Logs
   [log entries as JSON]
   ### Observability Dashboard
   [observability_summary as formatted table]
   ```
   The function merges the participant's written text (passed as a string) with the auto-generated evidence.

2. Tests: `export_assessment` returns a string containing all three dimension headers, the evidence section, and the observability caveat.

**Acceptance criteria:**
- Export function returns valid Markdown with all sections.
- Evidence section includes log entries and observability summary.
- OWASP tags appear in the recommendations template.

---

### Slice 7 — Dual-notebook mechanism + housekeeping

**Blocked by:** Slice 6

**What to build:**

1. **Delete** `ai-int/code/build_notebook.py`.
2. **Move/archive** loose PDFs from `ai-int/` (the outline and notes are already `.md` files; any `.pdf` files get moved to `ai-int/ref/` or deleted — check what exists).
3. Create `notebooks/ethical_llm_workshop_instructor.ipynb` — the instructor source notebook. Three sections:
   - **Section 1: Motivation & Setup** — theory framing, OWASP context, `%pip install`, MOCK_MODE toggle, provider selection, imports, BYOK instructions.
   - **Section 2: Building & Running the Assistants** — Base (read system prompt, run 7 scenarios, read retrieval function, compare base/RAG, RAG Triad eval, Guardrails pipeline walk-through, type-one-guardrail exercise, run all three stages, run observability dashboard).
   - **Section 3: The Three-Dimensional Assessment** — assessment template (Technical/Ethical/Observability/Recommendations), bias probes, Stakeholder Engagement Plan prompts, one-click export cell.
   - **Author cell** at the end: `[Your name / affiliation / date]` placeholder.
   - Facilitation cells tagged with `instructor` metadata — `"metadata": {"tags": ["instructor"]}`.
4. Create `notebooks/generate_participant_notebook.sh` — one-liner: `jupyter nbconvert --TagRemovePreprocessor.remove_cell_tags=instructor --to notebook --output ethical_llm_workshop.ipynb notebooks/ethical_llm_workshop_instructor.ipynb`.
5. Update `README.md` — add the `%pip install git+https://github.com/King-Murah-s-Projects/llm-assistants.git` cell (as a code block), the `generate_participant_notebook.sh` step, and the note that repos must be public for pip install to work.

**Acceptance criteria:**
- `build_notebook.py` is gone.
- Instructor notebook has all three sections with `instructor`-tagged facilitation cells.
- `generate_participant_notebook.sh` runs (requires nbconvert installed) and produces a participant notebook without any `instructor`-tagged cells.
- Author cell present at the end.
- README has the install cell and the generate step.

---

### Slice 8 — Facilitator guide

**Blocked by:** Slice 7

**What to build:**

`FACILITATOR_GUIDE.md` at the repo root. Sections:

1. **Pre-event setup** — clone repos, `pip install -e .`, set `.env` from `.env.example`, smoke-test MOCK mode (`pytest`), smoke-test live mode (one API call each provider), generate participant notebook, run backend (`uvicorn backend.main:app --reload`), open demo frontend, verify end-to-end.
2. **Room runbook** — the 90-minute timing (Setup 5 / Base 8 / RAG 18 / Guardrails 16 [incl. ~6 exercise] / Assessment 35 / Debrief 8). Each time slot tied to: which notebook cells to run, what to say on the projector, which demo mode to show, when to flip the provider toggle, how to run the type-one-guardrail exercise, how to walk the observability dashboard.
3. **Failure playbook** — network dies → flip `MOCK_MODE=True`, restart backend; participant `pip install` fails → share the `ai-int/code/` folder as fallback; rate-limit hit → MOCK; Colab runtime crashes → re-run from top (MOCK_MODE means no state loss).
4. **Expected outputs** — for each of the 7 test scenarios, what a good base / RAG / guardrailed response looks like (key phrase, expected flags, expected trust band). Enough to recognize when something is off live.
5. **Collecting deliverables** — participant runs the export cell, downloads the `.md` file, sends to facilitator.
6. **Post-event** — push `llm-assistants` to GitHub, deploy `assist-demo` to Cloudflare Workers (optional; links to Cloudflare Workers docs).

**Acceptance criteria:**
- All five sections present.
- Timing in the runbook adds to 90 minutes.
- Failure playbook covers the three main failure modes.
- Expected outputs cover all 7 scenarios.
- Post-event Cloudflare note present.

---

### Slice 9 — Cloudflare Workers deploy (HITL)

**Blocked by:** Slice 5 + GitHub repos live

**Note:** This requires human action (Cloudflare account, wrangler auth). Documented in FACILITATOR_GUIDE.md §Post-event. Skip until after all other slices.
