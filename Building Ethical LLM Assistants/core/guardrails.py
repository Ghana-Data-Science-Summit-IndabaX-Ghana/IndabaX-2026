"""
The five guardrail layers for the guardrailed assistant stage.

Each layer is a distinct, named, inspectable function — they are composed
in sequence inside run_guardrailed(), but kept separate here for teaching.

OWASP LLM Top-10 (2025) ids are tagged on each layer.

Pipeline order:
  1. validate_input   → catch injection/out-of-scope pre-LLM       [LLM01]
  2. (retrieval)      → RAG retrieval (in core/rag.py)
  3. (model call)     → provider.complete()
  4. filter_output    → scan reply for prohibited patterns           [LLM09]
  5. compute_trust_score → 0.0–1.0 heuristic from flags + grounding [LLM09]
  6. should_escalate  → route to human on high-stakes signals       [LLM06]
  7. make_log_entry   → structured audit trail                      [LLM02]
"""

import re

# ── Layer 1: Input Validation ─────────────────────────────────────────────────
# OWASP LLM01: Prompt Injection

_INJECTION_PATTERNS = [
    r"ignore\s+(your\s+)?(previous|prior)\s+instructions",
    r"ignore\s+(your\s+)?instructions",
    r"approve\s+(my\s+)?loan",
    r"bypass\s+(your\s+)?",
    r"override\s+(your\s+)?",
    r"forget\s+(your\s+)?instructions",
    r"disregard\s+(your\s+)?",
    r"act\s+as\s+if\s+you\s+have\s+no\s+rules",
    r"you\s+are\s+now\s+",
]

_MEDICAL_PATTERNS = [
    r"\b(medical|medication|drug\s+interaction|diagnosis|symptom|treatment)\b",
    r"\bprescri(be|ption)\b",
    r"\b(malaria|typhoid|cholera|tuberculosis|hiv|aids|hepatitis|disease|illness|infection)\b",
    r"\b(medicine|tablet|capsule|dosage|dose|antibiotic|paracetamol|ibuprofen)\b",
    r"\b(doctor|physician|nurse|clinic|hospital|pharmacy|health\s+facility)\b",
    r"\b(sick|unwell|fever|pain|headache|vomiting|diarrhoe?a|wound|injury)\b",
    r"\bwhat\s+(medicine|drug|tablet|treatment)\b",
]

# Agronomy is detected by ADVICE INTENT, not crop nouns — so "loan for fertiliser" passes.
_AGRONOMY_INTENT_PATTERNS = [
    r"\bwhich\s+(seed|variety|fertili[sz]er|pesticide|herbicide|chemical)s?\b",
    r"\bhow\s+(do|to)\s+(i\s+)?(treat|control|prevent|spray|apply|plant|grow)\b",
    r"\bwhen\s+(should|do)\s+i\s+(plant|harvest|spray|weed|apply)\b",
    r"\bwhat\s+(should|do)\s+i\s+(plant|grow|apply|spray)\b",
]


def validate_input(message: str) -> dict:
    """Layer 1: input validation. Medical blocks; agronomy flags (non-blocking)."""
    flags = []
    text = message.lower()
    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, text):
            flags.append("injection_attempt")
            break
    blocked = "injection_attempt" in flags
    for pattern in _MEDICAL_PATTERNS:
        if re.search(pattern, text):
            flags.append("out_of_scope_medical")
            blocked = True
            break
    for pattern in _AGRONOMY_INTENT_PATTERNS:
        if re.search(pattern, text):
            flags.append("out_of_scope_agronomy")
            break  # non-blocking
    tokens_saved = len(message) // 4 if blocked else 0
    return {"blocked": blocked, "flags": flags,
            "blocked_pre_llm": blocked, "tokens_saved_estimated": tokens_saved}


# ── Layers 3 + 4: Output Filtering + Trust Score ────────────────────────────
# OWASP LLM09: Misinformation / Hallucination risk

_GUARANTEE_PATTERNS = [
    r"you\s+will\s+definitely\s+be\s+(approved|eligible)",
    r"you\s+will\s+definitely",
    r"you\s+are\s+(guaranteed|approved)",
    r"\bguaranteed\b",
    r"i\s+can\s+confirm\s+(that\s+)?you",
    r"100\s*%\s*(certain|sure|guaranteed)",
    r"without\s+(a\s+)?doubt\s+you",
]

_FINAL_DECISION_PATTERNS = [
    r"i\s+(hereby\s+)?(approve|grant|authorise|authorize)",
    r"your\s+loan\s+is\s+(approved|granted)",
    r"you\s+qualify\s+for\s+a\s+loan",
]

_FABRICATION_SIGNALS = [
    # Overly specific numbers the assistant can't know
    r"exactly\s+\d+(\.\d+)?\s*(percent|%|ghs|cedis)",
    r"your\s+(credit\s+)?score\s+is\s+\d+",
]


def filter_output(reply: str, retrieved_docs: list[dict] | None = None) -> dict:
    """
    Layer 3: Post-model output filtering.  [LLM09: Misinformation]

    Scans the reply for prohibited patterns and computes a trust score.
    Does NOT modify the reply — only flags and scores it.

    Returns:
        {flags, trust_score, grounding}
    """
    flags = []
    text = reply.lower()

    for pattern in _GUARANTEE_PATTERNS:
        if re.search(pattern, text):
            flags.append("guarantee")
            break

    for pattern in _FINAL_DECISION_PATTERNS:
        if re.search(pattern, text):
            flags.append("final_decision")
            break

    for pattern in _FABRICATION_SIGNALS:
        if re.search(pattern, text):
            flags.append("fabrication_signal")
            break

    from core.eval import groundedness_signal
    grounding = groundedness_signal(reply, retrieved_docs or [])
    trust_score = compute_trust_score(flags, grounding)

    return {"flags": flags, "trust_score": trust_score, "grounding": grounding}


def compute_trust_score(output_flags: list[str], grounding: dict) -> float:
    """0.0–1.0 trust. Subtract for flags; subtract more when not grounded.
    Bands (emitted token preserved for the frontend contract): >=0.7 'pass',
    0.4–0.7 'fallback', <0.4 'escalate' (pre-LLM block emits 'blocked')."""
    score = 1.0

    if "guarantee" in output_flags:
        score -= 0.35
    if "final_decision" in output_flags:
        score -= 0.35
    if "fabrication_signal" in output_flags:
        score -= 0.25
    if not grounding.get("grounded", False):
        score -= 0.25 if not grounding.get("has_valid_citation") else 0.10

    return max(0.0, min(1.0, score))


# ── Layer 5: Human Escalation ────────────────────────────────────────────────
# OWASP LLM06: Excessive Agency

_ESCALATION_TRIGGER_PATTERNS = [
    r"final\s+(credit\s+)?decision",
    r"legal\s+advice",
    r"(i|am)\s+desperate",
    r"emergency",
    r"suicid",
    r"guarantee\s+(me|my)",
    r"must\s+(approve|give\s+me)",
    # farmer debt / livelihood distress
    r"can('?t| ?not)\s+(re)?pay",
    r"lose\s+(my\s+)?(farm|land)",
    r"bank\s+will\s+take",
    r"crops?\s+(failed|died).*(owe|debt|loan)",
]

_HIGH_STAKES_INTENT = [
    "approve", "guarantee", "legal", "emergency", "desperate",
    "certain", "definitely",
]


def should_escalate(message: str, trust_score: float) -> bool:
    """
    Layer 5: Human escalation check.  [LLM06: Excessive Agency]

    Returns True if the trust score is critically low OR the message
    contains explicit high-stakes intent triggers.

    Fires on trust_score < 0.4 OR pattern match — whichever comes first.
    Note: This layer fires AFTER output filtering — it has both the
    message content and the trust score available.
    """
    if trust_score < 0.4:
        return True

    text = message.lower()
    for pattern in _ESCALATION_TRIGGER_PATTERNS:
        if re.search(pattern, text):
            return True

    return False


# ── Exercise stub ─────────────────────────────────────────────────────────────

def participant_guardrail_rule(reply: str) -> list[str]:
    """
    TYPE-ONE-GUARDRAIL EXERCISE — fill this in yourself.

    Add one rule to catch a prohibited phrase in the model's reply.

    Example to get you started:
        >>> if "you will definitely be approved" in reply.lower():
        ...     return ["guarantee"]
        >>> return []

    Tip: Run scenario 2 ("Will I definitely be approved...") in guardrails
    mode — the mock reply contains the phrase "you will definitely be approved".
    Your rule should catch it and add "guarantee" to the flags.

    When you're done, pass this function into run_guardrailed() as the
    `extra_output_rules_fn` argument to see it fire in the pipeline.
    """
    # TODO: Add your rule here
    return []
