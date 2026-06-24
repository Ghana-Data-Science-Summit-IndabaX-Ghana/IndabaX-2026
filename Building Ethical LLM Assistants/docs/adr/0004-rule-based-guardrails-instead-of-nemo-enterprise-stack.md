# 4. Rule-based, from-scratch guardrails instead of the NeMo/enterprise stack

Date: 2026-06-15

## Status

Accepted

## Context

The course syllabi (a spec this hands-on must satisfy) name an enterprise stack: **NVIDIA NeMo Guardrails on Red Hat OpenShift AI, vLLM, Kubernetes ConfigMaps, Colang, a live Grafana deployment, and Cleanlab TLM** trustworthiness scoring. They also cover training-time and research topics (DPO/LibraAlign, ACL staged release, CoT-steganography monitoring, watermarking).

None of that runs in a 90-minute Google Colab + FastAPI + Cloudflare workshop using **API providers** (NeMo wraps self-hosted vLLM models, not API providers; Grafana needs a metrics backend; OpenShift is a cluster). It also conflicts with already-accepted decisions (rule-based guardrails, run-and-audit, Anthropic/Gemma providers) and with keeping the notebook runnable by a beginner.

## Decision

Satisfy the syllabi's **objectives and concepts** by building the **from-scratch teaching version** of each mechanism in our stack, and reference (not deploy) the enterprise tools:

- Five rule-based, inspectable guardrail functions instead of NeMo/Colang.
- An in-notebook + in-demo **observability dashboard** computed from our logs instead of Grafana.
- A rule-based **trust score** (three-band pass/fallback/escalate) instead of Cleanlab TLM.
- **OWASP LLM Top-10 labels**, the **RAG Triad**, and the **Three-Dimensional Assessment** (Technical 40 / Ethical 30 / Observability 30) as framing.
- Enterprise tools named as "the production tool this maps to" (optional read-only Colang snippet for awareness).
- Training-time/research items (DPO, ACL, steganography, watermarking) left to the theory portion; available only as optional appendix/stretch content if time allows.

## Consequences

- The hands-on is feasible in 90 minutes, on the chosen stack, and stays readable by a mixed-but-technical room.
- Every concept the room learns is implemented from scratch and fully inspectable — arguably better pedagogy than configuring a black-box enterprise tool.
- The deliverable will *not* contain a real NeMo/OpenShift/Grafana deployment; if a stakeholder expects the literal enterprise stack, that is a different, multi-day, cluster-based project and this ADR is the record of why we did not build it here.
