# PRD — Building Ethical LLM Assistants (Hands-On Portion)

Status: ready-for-agent
Date: 2026-06-15
Glossary: see `/CONTEXT.md`. Decisions: see `/docs/adr/0001`–`0004`.

## Problem Statement

A facilitator is delivering the 90-minute hands-on portion of a 3-hour mastery tutorial, *Building Ethical LLM Assistants* (Ghana, 25 June 2026), to a mixed-but-technical room. Today the facilitator has: an outline and detailed notes, committee feedback flagging gaps, and an incomplete Colab notebook plus a frontend shell. The notebook has no guardrails implementation, no observability, no provider choice, and only an informal audit; the frontend has no backend and shows none of the teaching internals; and the course syllabi demand concepts (OWASP, RAG Triad, active guardrails, observability/economics, a three-dimensional assessment, stakeholder engagement) that the current materials don't deliver. The facilitator needs (1) a complete, working code implementation covering base assistant, RAG, and guardrails, and (2) a clear facilitator guide for running it in the room — runnable with no connectivity, on a tight timer, in front of beginners and practitioners at once.

## Solution

A single credit-access assistant for Ghana, shown at three capability stages — **Base → RAG → Guardrailed** — implemented once in a shared, pip-installable `core` package and surfaced two ways: a **participant Colab notebook** (read, run, edit, assess) and a **facilitator demo** (Next.js projector UI + local FastAPI) that mirrors the same stages via a mode switcher. Guardrails are five visibly-separate, rule-based, inspectable layers wrapping RAG, with a rule-based trust score, a from-scratch observability dashboard, and OWASP labels — the from-scratch teaching versions of the syllabi's enterprise stack (NeMo/Grafana/Cleanlab), which are referenced but not deployed. Two LLM providers (Anthropic Claude Haiku 4.5, Google Gemma 4) sit behind one interface, switchable by a projector-visible toggle. `MOCK_MODE` (provider-aware canned responses) lets the entire flow — including the deliverable — run with no key and no network. The deliverable is a **Three-Dimensional Assessment** (Technical 40% / Ethical 30% / Observability 30%) exported as a single audit-plus-evidence Markdown scorecard per participant.

## User Stories

1. As a participant, I want to open one Colab notebook and run it top to bottom, so that I can follow the session without local setup.
2. As a participant, I want the notebook to install the shared `core` package via a single `%pip install git+…` cell, so that the demo and my notebook run identical plumbing.
3. As a participant with no API key, I want `MOCK_MODE = True` by default, so that I can complete the entire session and the deliverable offline.
4. As a participant who brought my own key, I want to flip to live mode, so that I can see real model behavior.
5. As a participant, I want to read the base assistant's system prompt line by line, so that I can map each rule to an ethical concern.
6. As a participant, I want to run the base assistant on the test scenarios, so that I can capture verbatim outputs as audit evidence.
7. As a participant, I want to read the retrieval function, so that I understand how RAG selects documents.
8. As a participant, I want to inspect the small knowledge base of Ghanaian financial documents, so that I can reason about what retrieval can and cannot ground.
9. As a participant, I want the RAG assistant to cite its source document, so that I can verify claims (Groundedness).
10. As a participant, I want to compare base vs RAG answers on the same query, so that I can see exactly what retrieval changed and what it did not.
11. As a participant, I want to evaluate RAG with the RAG Triad (Context Relevance, Groundedness, Q/A Relevance), so that my technical assessment uses a named framework.
12. As a participant, I want to see a retrieval log (which document ids were retrieved), so that I have an exhibit for the audit.
13. As a participant, I want the guardrailed assistant to run input validation before the model, so that obvious injection and out-of-scope inputs are blocked early.
14. As a participant, I want blocked-before-the-LLM inputs to record token savings, so that I can see the Denial-of-Wallet (LLM10) mitigation.
15. As a participant, I want output filtering to scan replies for prohibited patterns (guarantees, final decisions, fabricated specifics), so that confidently-wrong outputs are caught.
16. As a participant, I want a rule-based trust score on each response, so that I can see the pass/fallback/escalate decision the way the Cleanlab TLM workflow describes it.
17. As a participant, I want responses scoring 0.4–0.7 replaced with a safe fallback message, so that low-confidence answers are not delivered as fact.
18. As a participant, I want responses scoring below 0.4, or matching a high-stakes intent trigger, routed to a simulated human escalation, so that the assistant never makes high-stakes calls itself.
19. As a participant, I want each guardrail layer to remain visibly separate in code, log, and demo, so that I can learn them individually.
20. As a participant, I want each concern and guardrail labeled with its OWASP LLM Top-10 id, so that my work ties to the standard framework.
21. As a participant, I want to add one prohibited-phrase rule to the output filter myself, so that I get one genuine hands-on coding moment.
22. As a participant, I want a crafted mock reply that contains that phrase, so that my new rule visibly catches something even offline.
23. As a participant, I want a structured per-request log (timestamp, query, provider, model, retrieved ids, input/output flags, trust score, escalation, response), so that accountability can be reconstructed.
24. As a participant, I want an observability dashboard summarizing flagged-interaction volume, violation taxonomy, and token savings, so that I can complete the Observability dimension.
25. As a participant, I want the dashboard labeled "estimated · illustrative in MOCK," so that I am not misled about offline economics.
26. As a participant, I want to run the bias probes (Kwame / Fatima / Pidgin), so that I can assess differential treatment.
27. As a participant, I want to handle a Pidgin input ("Me I no sabi plenty English"), so that I can assess language/register equity.
28. As a participant, I want a Stakeholder Engagement Plan with ~3 guided prompts, so that I can address Indigenous Data Sovereignty for Twi/Ga/Ewe/Hausa/Dagbani and Northern-region communities.
29. As a participant, I want the deliverable organized as a Three-Dimensional Assessment (Technical 40 / Ethical 30 / Observability 30), so that it matches the course grading standard.
30. As a participant, I want each prioritized recommendation tagged with its OWASP id, so that fixes map to named risks.
31. As a participant, I want a one-click export cell, so that I produce a single Markdown file bundling my assessment with its evidence (logs + dashboard).
32. As a participant, I want my assessment to require quoted model text and document ids, so that claims are defensible rather than vague.
33. As a participant, I want to switch the provider between Anthropic and Gemma, so that I can observe how the same prompt is followed differently.
34. As a participant, I want provider-aware mocks, so that the Anthropic-vs-Gemma difference still shows when the network is down.
35. As a facilitator, I want the demo to expose Base / RAG / Guardrails modes via a switcher, so that the projector mirrors each step participants reach.
36. As a facilitator, I want an "under the hood" panel showing retrieval log, guardrail flags, escalation banner, trust score, and provider/model badge, so that I can make the invisible visible on screen.
37. As a facilitator, I want a provider toggle visible on the projector, so that I can flip Anthropic→Gemma live and stage the "free tier trains on your data" privacy discussion.
38. As a facilitator, I want the backend to run locally on my laptop, so that the demo has no connectivity dependency in the room.
39. As a facilitator, I want the demo to run fully in `MOCK_MODE`, so that a dead network does not kill the session.
40. As a facilitator, I want an instructor notebook with facilitation guidance interleaved in tagged cells, so that I know what to say at each step.
41. As a facilitator, I want the participant notebook generated from the instructor notebook by an `nbconvert` tag-strip, so that there is a single source of truth and no drift.
42. As a facilitator, I want a markdown facilitator guide in the repo (pre-event setup, room runbook, failure playbook, expected outputs, deliverable collection), so that I can run the code confidently.
43. As a facilitator, I want the re-budgeted 90-minute timing tied to specific cells and demo actions, so that I stay on schedule.
44. As a facilitator, I want a failure playbook (network → MOCK, install fails → fallback, rate-limit → MOCK), so that I can recover live.
45. As a facilitator, I want expected good outputs per scenario per stage, so that I can recognize when something is off live.
46. As a facilitator, I want to collect one export file per participant, so that grading the assessment is straightforward.
47. As a facilitator, I want to deploy the Next.js demo to Cloudflare Workers after the event, so that I can share it.
48. As a maintainer, I want no API keys in either repo and `.env.example` committed, so that the public repos are safe.
49. As a maintainer, I want `build_notebook.py` deleted and loose PDFs removed, so that the committee's housekeeping feedback is addressed.
50. As a maintainer, I want an author/attribution cell at the end of the participant notebook, so that the committee's "complete your details" note is addressed.
51. As a maintainer, I want enterprise tools (NeMo/OpenShift/vLLM/Colang/Grafana/Cleanlab) referenced as "the production tool this maps to," so that the spec's concepts are honored without infeasible deployment.
52. As a maintainer, I want training-time/research topics (DPO, ACL, steganography, watermarking) as optional appendix content only, so that they never block the 90-minute critical path.

## Implementation Decisions

**Repositories (ADR-0003).** Two public repos. `llm-assistants` holds `core/`, `backend/`, `notebooks/`, `ai-int/`, `docs/adr/`, `FACILITATOR_GUIDE.md`, `README.md`, `pyproject.toml`. `assist-demo` (existing) holds the Next.js frontend, deployed to Cloudflare Workers post-event. No secrets in either tree; `.env` gitignored, `.env.example` committed.

**`core` package + dependency injection (ADR-0002).** `core` is the single source of truth for plumbing: provider adapters, `MOCK_MODE`, knowledge base, structured logger, observability summarizer, and a **runner** that accepts the teaching artifacts (system prompts, retrieve function, guardrail functions) as arguments. FastAPI calls the runner with `core`'s defaults; the notebook installs `core` from GitHub and passes its own inline, editable artifacts into the same runner. `core` ships byte-identical defaults.

**Providers (ADR-0001).** One `LLMProvider` interface, two adapters: Anthropic (Claude Haiku 4.5, native `system=`) and Gemma (Google Gemma 4, `google-genai`, system prompt prepended to the user turn). The exact Gemma model-id string is verified against Google's live docs at build time. Provider selected by config/toggle; live-only (MOCK serves provider-flavored canned responses).

**Assistant stages.** `run_base`, `run_rag`, `run_guardrailed` runner entrypoints. Base = system prompt + provider. RAG = keyword-overlap retrieval over the existing 4-document knowledge base + citation-forcing system prompt + retrieval log. Guardrailed wraps RAG with the five-layer pipeline.

**Guardrails (ADR-0004), five visibly-separate layers:** (1) system prompt; (2) `validate_input` — rule-based pre-model injection/out-of-scope checks that early-return without calling the model and record `blocked_pre_llm` + estimated `tokens_saved`; (3) `filter_output` — rule-based post-model scan for prohibited patterns emitting flags; (4) trust score — rule-based 0.0–1.0 computed from output flags + retrieval groundedness, three bands (≥0.7 deliver / 0.4–0.7 safe fallback / <0.4 escalate); (5) `should_escalate` — fires on `score < 0.4` or a high-stakes intent trigger, returning a simulated human-escalation response; plus structured logging. The trust score flows from the (distinct) output-filter layer into the (distinct) escalation layer; the two are not merged.

**Observability.** `core.summarize_logs(logs)` returns flagged-interaction volume, violation taxonomy (counts by flag type), and token savings (`len(text)//4` estimate, labeled estimated/illustrative-in-MOCK). Rendered in-notebook (pandas table + matplotlib bar) and in the demo panel (numeric counters + SVG/CSS bars, no charting dependency).

**Backend API contract.** `POST /chat` with `{ mode: "base"|"rag"|"guardrails", message, provider }` → unified non-streaming envelope `{ reply, provider, model, mock, retrieval_log | null, guardrail_report | null }` where `guardrail_report` carries input/output flags, trust score, escalation, and the log entry. CORS enabled for the local frontend.

**Frontend.** Build on the existing shadcn shell: mode switcher (Base/RAG/Guardrails), response area, under-the-hood panel (retrieval log, flags, escalation banner, trust score, provider/model badge, session observability tally), and a visible provider toggle. Read-only for participants; projector use.

**Notebook.** Three sections — (1) Motivation & Setup, (2) Building & Running the Assistants (Base→RAG→Guardrailed incl. the type-one-guardrail exercise), (3) The Three-Dimensional Assessment. Instructor notebook is source with facilitation cells tagged `instructor`; participant notebook produced by `jupyter nbconvert --TagRemovePreprocessor.remove_cell_tags=instructor`. `build_notebook.py` deleted; loose PDFs removed; author cell added.

**Assessment.** Reorganized under three dimensions (Technical 40 / Ethical 30 / Observability 30) with a cross-cutting prioritized-recommendations close; absorbs the prior 9 sections; includes the RAG Triad, the Stakeholder Engagement Plan (~3 prompts; Twi/Ga/Ewe/Hausa/Dagbani + Northern regions), and OWASP-tagged recommendations. Exported by a final cell to one audit-plus-evidence Markdown file.

**Test scenarios.** Keep the existing 7 (5 original + 2 RAG).

## Testing Decisions

Good tests assert **external behavior**, not implementation details: given a scenario input in `MOCK_MODE`, assert the structured result — which flags fired, which document ids were retrieved, the trust-score band, whether escalation triggered, the envelope shape — never internal call counts or private helpers. `MOCK_MODE` + provider-aware mocks make every test deterministic and offline.

- **Highest seam — the `core` runner.** Test `run_base` / `run_rag` / `run_guardrailed` against the 7 scenarios: e.g. the injection scenario sets an input flag and `blocked_pre_llm`; the certainty scenario trips an output guarantee flag and lowers the trust score; a thin-retrieval query lands in the fallback band; a high-stakes intent escalates; the RAG scenarios return the expected document ids. Prefer this seam.
- **Pure-function unit seams.** `validate_input`, `filter_output`, the trust-score function, `should_escalate`, `retrieve_relevant_documents`, and `summarize_logs` are pure (input → flags/score/ids/metrics) and tested directly, including the participant exercise rule.
- **Integration seam — FastAPI `/chat`.** Via `TestClient` in `MOCK_MODE`, assert the unified envelope per mode (base has null retrieval_log and guardrail_report; rag has retrieval_log; guardrails has guardrail_report with flags/score/escalation).
- **Prior art.** The existing `workshop_mocks.py` scenario-matching pattern is the model for deterministic mock selection; tests reuse the canonical scenario inputs.

Frontend automated testing is light/out of scope (it is a read-only demo shell); verification is manual via the room runbook.

## Out of Scope

- Deploying any enterprise tooling: NeMo Guardrails, OpenShift/RHOAI, vLLM, Colang config maps, real Grafana, real Cleanlab TLM. These are referenced as the production mapping only (ADR-0004).
- Training-time / research topics: DPO/LibraAlign, ACL staged release, CoT-steganography monitoring, watermarking — optional appendix/stretch content only, never in the 90-minute critical path.
- A publicly-hosted FastAPI backend during the session (local laptop only; Fly/Render documented as post-event). FastAPI on Cloudflare Workers is explicitly excluded (ADR-0003).
- The theory/slide portion of the tutorial (owned by others).
- Real per-token economics in MOCK (token savings are estimated/illustrative).
- Expanding the knowledge base beyond the existing 4 documents.
- Participants actively building the observability dashboard or stakeholder plan in-room (run-and-read only; the single build moment is the type-one-guardrail exercise).

## Further Notes

- Timing (90 min): Setup 5 / Base 8 / RAG 18 / Guardrails 16 (incl. ~6 exercise) / Three-Dimensional Assessment 35 / Debrief 8. The session is full; any new "build it live" request trades against something already planned.
- Staging the live Gemma data-privacy moment requires both an Anthropic key and a Google key on the laptop; the provider-flavored mock preserves the teaching point offline.
- Build sequence: `core` first (everything imports it) → `backend` → instructor notebook → participant notebook (via nbconvert) → frontend → facilitator guide.
- Build-time inputs needed from the facilitator: the two GitHub repos created at the agreed URLs (so `%pip install git+…` resolves) and local Anthropic + Google keys for live smoke-testing (never committed).
