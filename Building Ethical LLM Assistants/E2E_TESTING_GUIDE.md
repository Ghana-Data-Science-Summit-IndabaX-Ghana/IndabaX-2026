# End-to-End Testing Guide — LLM Assistants (Agricultural Credit)

> Workshop: "Building Ethical LLM Assistants" — Ghana, 25 June 2026  
> This guide walks from zero (no keys, no deps) to a fully live demo.

---

## Prerequisites

- Python ≥ 3.12 (`python3 --version`)
- Node.js ≥ 18 (for the frontend — optional for backend-only testing)
- ~1 GB disk free (Chroma embedding model download)
- Git working tree: branch `rag-deepening-agric-credit`

---

## Phase 0 — Get API Keys

You need keys for both LLM providers. Chroma is fully local — no key required.

### Anthropic (Claude)

1. Go to [https://console.anthropic.com](https://console.anthropic.com) → **API Keys**
2. Click **Create Key** → name it `llm-workshop-test`
3. Copy the key (shown once) — starts with `sk-ant-...`

### Google Gemini

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **Create API Key** → select a project (or create one)
3. Copy the key — starts with `AIza...`

### Chroma

No key needed. Chroma runs as an embedded local store. The embedding model
(`paraphrase-multilingual-MiniLM-L12-v2`, ~500 MB) downloads automatically from
Hugging Face on first use. This download happens once; after that everything is
offline.

---

## Phase 1 — Environment Setup

```bash
cd /Users/jessemurah/SWE/llm-assist

# 1. Activate the virtual environment
source .venv/bin/activate

# 2. Install / sync dependencies
pip install -e ".[dev]"

# 3. Verify Python version
python --version   # must be 3.12+
```

### Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```dotenv
ANTHROPIC_API_KEY=sk-ant-...          # your Anthropic key
GOOGLE_API_KEY=AIza...                # your Google key
MOCK_MODE=true                        # start in mock; switch to false for live
DEFAULT_PROVIDER=anthropic
DEFAULT_RETRIEVER=keyword             # start here; switch to chroma later
CHROMA_DIR=.chroma
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
```

---

## Phase 2 — Offline Tests (MOCK_MODE=true, no network)

These 108 tests run with no API key and no internet connection.

```bash
MOCK_MODE=true pytest -v
```

**Expected:** 108 passed, 0 failed.

If any test fails, check:
- `pip install -e ".[dev]"` was run
- You are on branch `rag-deepening-agric-credit`
- No `.env` overrides are breaking mock detection

Key test files and what they cover:

| File | Covers |
|---|---|
| `tests/test_config.py` | Config defaults |
| `tests/test_ingest.py` | Corpus load, chunk splitting, frontmatter validation |
| `tests/test_retrieval.py` | KeywordRetriever, Pidgin miss teaching point |
| `tests/test_eval.py` | Golden loader, `evaluate()`, groundedness, answer-eval |
| `tests/test_experiments.py` | k-sweep delta |
| `tests/test_rag.py` | RAG shape + agric mock scenarios |
| `tests/test_guardrails.py` | Medical block, agronomy redirect, distress escalation |
| `tests/test_observability.py` | Log summary, optional retrieval metrics |
| `tests/test_notebook_smoke.py` | Offline RAG flow: ingest → retrieve → generate |
| `tests/test_prompts.py` | Agric scope assertions |

---

## Phase 3 — Corpus & Retrieval Smoke Test

### 3a. Keyword retriever (no download required)

```bash
python - <<'EOF'
from core.ingest import load_documents, chunk_documents
from core.retrieval import KeywordRetriever

docs   = load_documents()
chunks = chunk_documents(docs)
print(f"Loaded {len(docs)} docs → {len(chunks)} chunks")

r      = KeywordRetriever(chunks)
hits   = r.retrieve("GIRSAL credit guarantee", k=3)
for h in hits:
    print(f"  [{h['score']:.2f}] {h['id']}")
EOF
```

**Expected:** 6 docs, ~30 chunks, top hit contains `girsal`.

### 3b. Chroma retriever (triggers ~500 MB model download on first run)

```bash
DEFAULT_RETRIEVER=chroma python - <<'EOF'
from core.ingest import load_documents, chunk_documents
from core.retrieval import ChromaRetriever

docs   = load_documents()
chunks = chunk_documents(docs)

# ChromaRetriever builds + persists the collection internally
r    = ChromaRetriever(chunks)
hits = r.retrieve("warehouse receipt financing", k=3)
for h in hits:
    print(f"  [{h['score']:.2f}] {h['id']}")
EOF
```

**Expected on first run:** model downloads to `~/.cache/huggingface/`. Subsequent
runs are instant. Top hit contains `warehouse-receipt`.

---

## Phase 4 — Live API Tests (MOCK_MODE=false)

Switch off mock mode and run the provider smoke tests:

```bash
MOCK_MODE=false pytest tests/test_providers.py -v
```

**Expected:** both Anthropic and Google providers return a non-empty string reply.

If Anthropic fails: verify `ANTHROPIC_API_KEY` in `.env` and that the key has
quota.  
If Google fails: verify `GOOGLE_API_KEY` and that the Gemini API is enabled in
your GCP project.

---

## Phase 5 — Backend API (FastAPI)

### 5a. Start the server

```bash
python backend/run.py
```

Server starts at `http://localhost:8000`. Keep this terminal open.

### 5b. Health check

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

### 5c. Base mode (MOCK_MODE=true)

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mode":"base","message":"How do I apply for an agric loan?","provider":"anthropic"}' \
  | python -m json.tool
```

**Expected:** `reply` contains a response, `mock: true`, no `retrieval_log`.

### 5d. RAG mode

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mode":"rag","message":"What is the GIRSAL guarantee?","provider":"anthropic"}' \
  | python -m json.tool
```

**Expected:** `retrieval_log` present with `retrieved_chunks`, `scores`, and
`retrieved_chunk_ids`.

### 5e. Guardrails mode — normal query

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mode":"guardrails","message":"What collateral does RCB accept?","provider":"anthropic"}' \
  | python -m json.tool
```

**Expected:** `guardrail_report` present, `trust_band` = `"pass"`.

### 5f. Guardrails mode — medical block

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mode":"guardrails","message":"What medication should I take for malaria?","provider":"anthropic"}' \
  | python -m json.tool
```

**Expected:** `trust_band` = `"blocked"`, reply cites referral language.

### 5g. Guardrails mode — distress escalation

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mode":"guardrails","message":"I cannot pay my loan and I feel like giving up everything","provider":"anthropic"}' \
  | python -m json.tool
```

**Expected:** `trust_band` = `"escalate"`, reply mentions MoFA / cooperative /
GIRSAL relief channel.

### 5h. Observability endpoint

After running several `/chat` requests above:

```bash
curl -s http://localhost:8000/observability | python -m json.tool
```

**Expected:** summary with `total_requests`, `mock_ratio`, and
`retrieval_metrics` populated.

### 5i. Live mode end-to-end (MOCK_MODE=false)

Stop the server, set `MOCK_MODE=false` in `.env`, restart, then repeat steps
5c–5h. Replies will be longer and non-deterministic, but shape should be
identical.

---

## Phase 6 — Evaluation Harness

```bash
MOCK_MODE=false python - <<'EOF'
from core.eval import load_golden, evaluate
from core.retrieval import get_default_retriever

retriever = get_default_retriever()
golden    = load_golden()          # loads data/golden.jsonl
dev_set   = [q for q in golden if q.get("split") == "dev"]

results = evaluate(dev_set, retriever, k=3)
print(f"Recall@3:    {results['recall_at_k']:.2f}")
print(f"Precision@3: {results['precision_at_k']:.2f}")
print(f"MRR:         {results['mrr']:.2f}")
EOF
```

**Expected baseline (keyword retriever, k=3):** Recall ≥ 0.55, MRR ≥ 0.50.

---

## Phase 7 — Experiment Sweep

```bash
MOCK_MODE=false python - <<'EOF'
from core.experiments import run_experiment
from core.eval import load_golden

golden  = load_golden()
dev_set = [q for q in golden if q.get("split") == "dev"]

# Sweep k from 1 to 5
results = run_experiment(dev_set, variable="k", values=[1, 2, 3, 4, 5])
for r in results:
    print(f"k={r['k']}  recall={r['recall_at_k']:.2f}  mrr={r['mrr']:.2f}")
EOF
```

---

## Phase 8 — Notebook Smoke Test (Colab-local)

```bash
MOCK_MODE=true pytest tests/test_notebook_smoke.py -v -s
```

This covers the full offline RAG pipeline as it runs in the participant notebook
without Colab's cell runner.

For a real Colab test:
1. Upload `notebooks/ethical_llm_workshop.ipynb` to Google Colab.
2. In the first code cell add:
   ```python
   import os; os.environ["MOCK_MODE"] = "true"
   ```
3. Run all cells (`Runtime → Run all`).
4. Verify all assertion cells pass without errors.

---

## Phase 9 — Frontend (assist-demo)

The Next.js frontend lives at `/Users/jessemurah/SWE/assist-demo`.

> **Note:** frontend changes (`components/ai-01.tsx`) are currently uncommitted
> in that repo's working tree. Commit them before testing.

```bash
cd /Users/jessemurah/SWE/assist-demo

# Commit outstanding frontend changes first
git add components/ai-01.tsx
git commit -m "feat: agric copy + FLAG_OWASP entries"

# Install deps
npm install

# Point at the running backend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start the dev server (keep backend running too)
npm run dev
```

Open `http://localhost:3000` in a browser and verify:
- Mode switcher: Base → RAG → Guardrails
- Agric-domain copy renders (no generic placeholder text)
- Guardrail badges appear in Guardrails mode
- `FLAG_OWASP` entries surface in the observability panel

---

## Phase 10 — Pre-PR Checklist

Before opening the PR from `dev` → `main`:

```bash
# 1. Full test suite
MOCK_MODE=true pytest -v

# 2. Live provider check
MOCK_MODE=false pytest tests/test_providers.py -v

# 3. Backend curl smoke (steps 5b–5h above)

# 4. Notebook smoke
MOCK_MODE=true pytest tests/test_notebook_smoke.py -v

# 5. No stray files
git status   # only expected changes staged
```

Then open the PR:
```bash
git push origin rag-deepening-agric-credit
gh pr create --base main --title "RAG deepening: agric-credit domain"
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: core` | Run `pip install -e ".[dev]"` from repo root |
| Chroma collection not found | Run Phase 3b to build it |
| `MOCK_MODE=false` but still mocking | Check `.env` — `MOCK_MODE` must be `false` not `"false"` |
| Embedding model slow / timeout | First run downloads ~500 MB; wait or set `TRANSFORMERS_OFFLINE=1` after first download |
| `trust_band` key missing | Guardrails mode only; base/rag modes return `null` for `guardrail_report` |
| Google 403 error | Gemini API not enabled in GCP — visit [https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com](https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com) |
| Port 8000 already in use | `lsof -ti:8000 \| xargs kill` |

---

## Critical Constraints (do not change during testing)

- `trust_band` tokens are `pass` / `fallback` / `escalate` / `blocked` — frontend colours depend on these exact strings.
- Five guardrail layers must remain **visibly separate** in logs and `guardrail_report`.
- Chroma store (`.chroma/`) is gitignored — never commit it.
- `MOCK_MODE=true` must work with **zero network** and **no API key**.
