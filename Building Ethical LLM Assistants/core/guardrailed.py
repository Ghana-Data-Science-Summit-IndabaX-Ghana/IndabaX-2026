"""
Guardrailed assistant runner.

Composes all five layers in sequence. Each layer is called by name
so participants can see the pipeline structure clearly.

Pipeline:
  1. validate_input       — block injection/out-of-scope pre-LLM [LLM01]
  2. retrieve             — RAG retrieval via the Retriever seam
  3. model call           — via generate_answer (separated from retrieval)
  4. filter_output        — scan reply for prohibited patterns [LLM09]
  5. compute_trust_score  — seeded by shared groundedness_signal [LLM09]
  6. should_escalate      — route to human on high-stakes signals [LLM06]
  7. make_log_entry       — structured audit trail [LLM02]
"""

from core.config import MOCK_MODE, DEFAULT_PROVIDER
from core.prompts import GUARDRAILED_SYSTEM_PROMPT, ESCALATION_RESPONSE, FALLBACK_RESPONSE
from core.guardrails import validate_input, filter_output, compute_trust_score, should_escalate
from core.logging import make_log_entry


def run_guardrailed(
    message: str,
    provider_name: str | None = None,
    history: list[dict] | None = None,
    system_prompt: str | None = None,
    retriever=None,
    validate_input_fn=None,
    filter_output_fn=None,
    should_escalate_fn=None,
    extra_output_rules_fn=None,
) -> dict:
    """
    Run the guardrailed assistant (all five layers wrapping RAG).

    Returns:
        {reply, provider, model, mock, history, retrieval_log,
         guardrail_report, log_entry}
    """
    from core.eval import groundedness_signal
    from core.retrieval import get_default_retriever
    from core.rag import generate_answer

    provider_name = (provider_name or DEFAULT_PROVIDER).lower()
    system = system_prompt if system_prompt is not None else GUARDRAILED_SYSTEM_PROMPT
    retriever = retriever if retriever is not None else get_default_retriever()
    _validate = validate_input_fn or validate_input
    _filter = filter_output_fn or filter_output
    _escalate = should_escalate_fn or should_escalate
    history = list(history) if history else []

    # ── Layer 1: Input Validation ─────────────────────────────────────────
    v = _validate(message)

    if v["blocked"]:
        if "out_of_scope_medical" in v["flags"]:
            blocked_reply = (
                "I can only help with agricultural credit questions in Ghana. "
                "For medical concerns, please consult a qualified health professional. "
                "[LLM01: Out-of-scope topic blocked]"
            )
        else:
            blocked_reply = (
                "I cannot process this request — it appears to contain instructions "
                "that attempt to override my guidelines. [LLM01: Prompt Injection blocked]"
            )
        log_entry = make_log_entry(
            query=message, provider=provider_name, model="blocked",
            mock=MOCK_MODE, stage="guardrails",
            input_flags=v["flags"], blocked_pre_llm=True,
            tokens_saved_estimated=v["tokens_saved_estimated"],
            response=blocked_reply,
        )
        guardrail_report = {
            "input_flags": v["flags"], "output_flags": [], "trust_score": 0.0,
            "trust_band": "blocked", "escalated": False, "groundedness": {},
            "blocked_pre_llm": True, "tokens_saved_estimated": v["tokens_saved_estimated"],
        }
        return {
            "reply": blocked_reply, "provider": provider_name, "model": "blocked",
            "mock": MOCK_MODE, "history": history,
            "retrieval_log": None, "guardrail_report": guardrail_report, "log_entry": log_entry,
        }

    # ── Layer 2: Retrieval (always runs) ──────────────────────────────────
    chunks = retriever.retrieve(message, k=5)
    doc_ids, seen = [], set()
    for c in chunks:
        if c["doc_id"] not in seen:
            seen.add(c["doc_id"])
            doc_ids.append(c["doc_id"])

    # ── Layer 3: Model Call (separated from retrieval) ────────────────────
    answer = generate_answer(message, chunks, system, provider_name, history, stage="guardrails")
    reply = answer["reply"]

    # ── Layer 4: Output Filtering ─────────────────────────────────────────
    fout = _filter(reply, chunks)
    output_flags = list(fout["flags"])
    if extra_output_rules_fn:
        output_flags += extra_output_rules_fn(reply)

    # ── Layer 5: Trust Score via shared groundedness signal ───────────────
    gsig = groundedness_signal(reply, chunks)
    trust = compute_trust_score(output_flags, gsig)
    band = "pass" if trust >= 0.7 else ("fallback" if trust >= 0.4 else "escalate")

    # ── Layer 6: Human Escalation ─────────────────────────────────────────
    escalated = _escalate(message, trust)
    if escalated or band == "escalate":
        final_reply = ESCALATION_RESPONSE
        escalated = True
        band = "escalate"
    elif band == "fallback":
        final_reply = FALLBACK_RESPONSE
    else:
        final_reply = reply

    answer["history"].append({"role": "assistant", "content": final_reply})

    retrieval_log = {
        "query": message,
        "retrieved_doc_ids": doc_ids,
        "retrieved_chunk_ids": [c["id"] for c in chunks],
        "retrieved_doc_titles": [c["title"] for c in chunks],
        "response": final_reply,
    }
    log_entry = make_log_entry(
        query=message, provider=provider_name, model=answer["model"],
        mock=answer["mock"], stage="guardrails",
        retrieved_ids=doc_ids, retrieved_titles=retrieval_log["retrieved_doc_titles"],
        input_flags=v["flags"], output_flags=output_flags,
        trust_score=trust, trust_band=band, escalated=escalated,
        blocked_pre_llm=False, tokens_saved_estimated=0, response=final_reply,
    )
    guardrail_report = {
        "input_flags": v["flags"], "output_flags": output_flags,
        "trust_score": trust, "trust_band": band, "escalated": escalated,
        "groundedness": gsig, "blocked_pre_llm": False, "tokens_saved_estimated": 0,
        "log_entry": log_entry,
    }
    return {
        "reply": final_reply, "provider": provider_name, "model": answer["model"],
        "mock": answer["mock"], "history": answer["history"],
        "retrieval_log": retrieval_log, "guardrail_report": guardrail_report, "log_entry": log_entry,
    }


def participant_guardrail_rule(reply: str) -> list[str]:
    """
    TYPE-ONE-GUARDRAIL EXERCISE — fill this in yourself.

    Add one rule to catch a prohibited phrase in the model's reply.

    Example:
        if "you will definitely be approved" in reply.lower():
            return ["guarantee"]
        return []

    Pass this function into run_guardrailed() as extra_output_rules_fn.
    """
    return []
