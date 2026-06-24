# RAG Deepening — Status Handoff (post-implementation)

> Updated after PR #1 was merged to `dev`, 22 June 2026.
> All 19 tasks from the implementation plan are **COMPLETE**.
> The next chat should pick up from here.

---

## What this project is

A 3-hour hands-on tutorial (Ghana, 25 June 2026) — "Building Ethical LLM Assistants." A shared
`core` Python package powers both a participant Colab notebook and a facilitator demo
(FastAPI backend in `backend/` + a separate Next.js frontend at `/Users/jessemurah/SWE/assist-demo`).
The assistant is shown at three stages: **Base → RAG → Guardrailed**.

---

## What was built (this session)

All 19 tasks from `docs/superpowers/plans/2026-06-22-rag-deepening-agric-credit.md` are done.

### New files
| File | Purpose |
|---|---|
| `data/agric/*.md` | 6 Markdown fact-sheets (the knowledge base corpus) |
| `data/golden.jsonl` | 24 golden queries — 17 dev / 7 test, 5 Pidgin-tagged |
| `core/ingest.py` | `load_documents()`, `chunk_documents()`, `build_chroma()` |
| `core/retrieval.py` | `Retriever` protocol, `KeywordRetriever`, `ChromaRetriever`, `get_default_retriever()` |
| `core/eval.py` | `load_golden()`, `evaluate()`, `groundedness_signal()`, `evaluate_answer()` |
| `core/experiments.py` | `run_experiment()` — single-variable sweep (retriever or k) |
| `tests/test_config.py` | Config defaults test |
| `tests/test_ingest.py` | Corpus validation + load + chunk |
| `tests/test_retrieval.py` | KeywordRetriever + Pidgin miss teaching point |
| `tests/test_eval.py` | Golden loader, evaluate(), groundedness, answer-eval |
| `tests/test_experiments.py` | k-sweep delta test |
| `tests/test_prompts.py` | Agric scope assertions |
| `tests/test_notebook_smoke.py` | Offline RAG flow smoke test |

### Modified files
| File | What changed |
|---|---|
| `core/rag.py` | `generate_answer()` split out; `run_rag()` uses retriever seam; `retrieval_log` gains `retrieved_chunk_ids` |
| `core/guardrailed.py` | Rewired onto retriever + `generate_answer` + `groundedness_signal`; five layers stay separate |
| `core/guardrails.py` | Two-tier input validation (medical blocks → `out_of_scope_medical`; agronomy non-blocking → `out_of_scope_agronomy`); farmer distress escalation triggers; `compute_trust_score` now takes grounding dict |
| `core/prompts.py` | Full agric reframe; agronomy-redirect line; new ESCALATION/FALLBACK responses cite MoFA/GIRSAL/cooperative |
| `core/mocks.py` | Re-keyed to agric scenarios (eligibility, GIRSAL, warehouse receipt, interest terms, outgrower, distress, Pidgin); `get_judge_mock()` added |
| `core/observability.py` | `summarize_logs()` extended with `retrieval_metrics` + `answer_failure_taxonomy` optional args |
| `core/knowledge_base.py` | Stripped to `format_retrieved_context()` only — inline docs and `retrieve_relevant_documents` removed |
| `core/config.py` | `DEFAULT_RETRIEVER`, `CHROMA_DIR`, `EMBEDDING_MODEL` added |
| `pyproject.toml` | `chromadb>=0.5.0`, `sentence-transformers>=3.0.0` added |
| `.gitignore` | `.chroma/` added |
| `.env.example` | Three new retrieval env vars |
| `tests/test_rag.py` | Replaced with T8 shape tests + agric mock tests |
| `tests/test_guardrails.py` | Updated for new guardrail shapes; agronomy/medical/distress tests added |
| `tests/test_observability.py` | Optional metrics test added |
| `notebooks/ethical_llm_workshop.ipynb` | Fixed broken imports; agric TEST_SCENARIOS (8); gendered land-tenure BIAS_PROBES; assessment title updated |
| `notebooks/ethical_llm_workshop_instructor.ipynb` | RAG section restructured — 7 AMA-style tiered cells, 2 coding moments |

### Deleted
- `notebooks/generate_participant_notebook.sh` — removed; notebooks are now two independent files

---

## Resolved design decisions (finalized this session)

### Notebook structure
**Decision:** Option C — two independent notebooks, no generation script.
- `notebooks/ethical_llm_workshop.ipynb` — participant artifact, edit directly
- `notebooks/ethical_llm_workshop_instructor.ipynb` — facilitator practice copy

The generate script was removed because only 4 of 47 cells differed, and it required nbformat/nbconvert (not in dev deps).

### Signature changes (breaking, external callers must update)
- `run_rag()` no longer accepts `knowledge_base` or `retrieve_fn` kwargs → takes `retriever` instead
- `compute_trust_score(output_flags, grounding_dict)` — second arg is now a grounding dict, not a list of docs
- `run_guardrailed()` no longer accepts `knowledge_base` or `retrieve_fn` kwargs → takes `retriever` instead

### trust_band tokens
`pass` (≥0.7) / `fallback` (0.4–0.7) / `escalate` (<0.4) / `blocked` (pre-LLM block). **Do NOT rename to "deliver"** — frontend colors on these tokens.

---

## Current state

- Branch `rag-deepening-agric-credit` merged to `dev`
- **108 tests passing** (MOCK_MODE=true, no API key, no network)
- FastAPI backend (`backend/main.py`) **unchanged** — `/chat` and `/observability` work as before
- Chroma store is gitignored and rebuilt on first use
- Frontend (`/Users/jessemurah/SWE/assist-demo`) updated: `components/ai-01.tsx` has agric copy + new `FLAG_OWASP` entries

---

## What is NOT done yet

- **Chroma embedding model not downloaded** — first run with `DEFAULT_RETRIEVER=chroma` will download `paraphrase-multilingual-MiniLM-L12-v2` (~500 MB). This is expected; it's offline after that.
- **Notebook not tested end-to-end in Colab** — the smoke test covers the Python logic but not the Colab cell execution flow.
- **Frontend (assist-demo) not committed** — `components/ai-01.tsx` changes are in the working tree of `/Users/jessemurah/SWE/assist-demo` but not committed to that repo.
- **`my-corrections.md` not committed** — intentionally left out of PR #1.

---

## Next actions (suggested)

1. Test `ethical_llm_workshop.ipynb` end-to-end in Colab with `MOCK_MODE=true`
2. Commit the frontend changes in `assist-demo` repo
3. Run a full demo curl: `python backend/run.py` then hit `/chat` with an agric query in RAG mode
4. When satisfied, open a PR from `dev` → `main`

---

## CRITICAL constraints (still apply)

- **MOCK_MODE must run with no API key and no network.** Embeddings are local only. Retrieval always runs even in MOCK.
- **Chroma store gitignored + rebuilt**, never committed.
- **Five guardrail layers stay visibly separate** in code, log, and demo.
- **Chunk score normalised to [0,1] for BOTH retrievers** (keyword: overlap/len(query_terms); chroma: 1 − cosine distance).
- **trust_band emitted token = `pass`** for ≥0.7 — do NOT rename.
- Python ≥3.12.
