# LLM Assistants — Building Ethical LLM Assistants (Hands-On)

This repo contains the code for the hands-on portion of *Building Ethical LLM Assistants* — a mastery-level tutorial on ethical AI deployment in the Ghanaian context. It covers a credit-access assistant in three stages: Base → RAG → Guardrailed, with a from-scratch observability dashboard and a Three-Dimensional Assessment (Technical 40% / Ethical 30% / Observability 30%).

**Repos:**
- This repo (`llm-assistants`) — shared `core` package + FastAPI backend + Colab notebooks
- [`assist-demo`](https://github.com/King-Murah-s-Projects/assist-demo) — Next.js facilitator demo (projector UI)

---

## For participants (Google Colab)

Open the participant notebook and run the first cell:

```python
%pip install git+https://github.com/King-Murah-s-Projects/llm-assistants.git -q
```

> **Note:** The repo must be public for this to work. If you can't access it, ask the facilitator for the local fallback.

The notebook defaults to `MOCK_MODE = True` — no API key needed. You can complete the entire session and the Three-Dimensional Assessment offline.

**To use a live API (optional):**
Set `MOCK_MODE = False` and add your key to Colab Secrets:
- `ANTHROPIC_API_KEY` — from [console.anthropic.com](https://console.anthropic.com)
- `GOOGLE_API_KEY` — from [aistudio.google.com](https://aistudio.google.com) (for Gemma, free tier)

---

## For the facilitator (local setup)

### 1. Clone and install

```bash
git clone https://github.com/King-Murah-s-Projects/llm-assistants.git
cd llm-assistants
pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — fill in your API keys, or leave MOCK_MODE=true
```

### 3. Run the backend (demo server)

```bash
MOCK_MODE=true uvicorn backend.main:app --reload
# Open http://localhost:8000/docs to verify
```

### 4. Run tests

```bash
MOCK_MODE=true python3.12 -m pytest tests/ -q
```

### 5. Generate the participant notebook

```bash
bash notebooks/generate_participant_notebook.sh
# Produces notebooks/ethical_llm_workshop.ipynb (no instructor cells)
```

---

## Project structure

```
llm-assistants/
├── core/                   # Shared pip-installable package
│   ├── config.py           # MOCK_MODE, DEFAULT_PROVIDER env vars
│   ├── providers.py        # LLMProvider ABC + Anthropic/Gemma adapters
│   ├── mocks.py            # Provider-aware canned responses (MOCK_MODE)
│   ├── knowledge_base.py   # 4 verified Ghana financial docs + retrieval
│   ├── prompts.py          # System prompts (OWASP-tagged)
│   ├── runner.py           # run_base / run_rag / run_guardrailed
│   ├── guardrails.py       # 5 guardrail layers + trust score
│   ├── observability.py    # summarize_logs (Grafana stand-in)
│   ├── export.py           # export_assessment (one-click export)
│   └── logging.py          # make_log_entry
├── backend/
│   └── main.py             # FastAPI POST /chat + GET /observability
├── notebooks/
│   ├── ethical_llm_workshop_instructor.ipynb
│   ├── ethical_llm_workshop.ipynb          # generated — do not edit directly
│   └── generate_participant_notebook.sh
├── ai-int/                 # Session design, notes, reference material
├── docs/adr/               # Architecture Decision Records
├── CONTEXT.md              # Domain glossary
├── FACILITATOR_GUIDE.md    # Room runbook
└── pyproject.toml
```

---

## Key design decisions

- **MOCK_MODE** (default: on) — canned responses keyed by (scenario, stage, provider). The entire session including the audit runs offline.
- **Dual provider** — Anthropic Claude Haiku 4.5 (native `system=`) and Google Gemma 4 (free tier, system prompt prepended). The provider toggle is pedagogically deliberate: Gemma's "free tier trains on your data" is a live consent/privacy teaching moment.
- **Shared `core` + dependency injection** — the FastAPI backend and the notebook both call the same runner; the notebook passes its own inline, editable teaching artifacts into it.
- **Five guardrail layers** — input validation, output filtering, trust score, human escalation, logging. From-scratch, inspectable code that maps to the NeMo/Grafana/Cleanlab enterprise stack conceptually.
