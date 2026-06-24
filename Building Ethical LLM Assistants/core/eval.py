"""Evaluation: golden dataset loader, retrieval metrics, groundedness, answer-eval."""
import json
from pathlib import Path

_GOLDEN_PATH = Path(__file__).resolve().parent.parent / "data" / "golden.jsonl"


def groundedness_signal(reply: str, chunks: list[dict], threshold: float = 0.15) -> dict:
    """One deterministic grounding check, shared by runtime trust score and offline answer-eval."""
    top_score = max((c.get("score", 0.0) for c in chunks), default=0.0)
    text = reply.lower()
    has_citation = any(
        (c.get("title", "").lower() in text) or (c.get("source", "").lower() in text)
        for c in chunks
    )
    return {
        "top_score": top_score,
        "has_valid_citation": has_citation,
        "grounded": top_score >= threshold and has_citation,
    }


_TAXONOMY = ("ungrounded_claim", "missing_citation", "register_mismatch", "over_hedge")


def evaluate_answer(query: str, reply: str, chunks: list[dict], judge_fn=None) -> dict:
    """Offline answer-quality eval: deterministic code checks + LLM-judge."""
    from core.config import MOCK_MODE
    grounding = groundedness_signal(reply, chunks)
    if judge_fn is None:
        from core.mocks import get_judge_mock
        judge = get_judge_mock(query, reply) if MOCK_MODE else _live_judge(query, reply, chunks)
    else:
        judge = judge_fn(query, reply, chunks)

    tags = []
    if not grounding["has_valid_citation"]:
        tags.append("missing_citation")
    if not grounding["grounded"] or judge["groundedness"] < 0.5:
        tags.append("ungrounded_claim")
    if judge["answer_relevance"] < 0.5:
        tags.append("register_mismatch")
    if reply.lower().count("i'm not confident") or reply.lower().count("cannot answer"):
        tags.append("over_hedge")

    return {
        "citation_ok": grounding["has_valid_citation"],
        "grounded": grounding["grounded"],
        "judge_groundedness": judge["groundedness"],
        "judge_relevance": judge["answer_relevance"],
        "tags": [t for t in tags if t in _TAXONOMY],
    }


def _live_judge(query: str, reply: str, chunks: list[dict]) -> dict:
    """Live LLM-as-judge (non-MOCK). Same model family via get_provider."""
    from core.providers import get_provider
    from core.config import DEFAULT_PROVIDER
    from core.knowledge_base import format_retrieved_context
    import re
    prompt = (
        "Score the ASSISTANT REPLY for Groundedness (claims supported by the SOURCES, 0-1) "
        "and Answer Relevance (addresses the QUESTION, 0-1). Reply as 'groundedness=<x> relevance=<y>'.\n\n"
        f"QUESTION: {query}\n\nSOURCES:\n{format_retrieved_context(chunks)}\n\nASSISTANT REPLY: {reply}"
    )
    raw = get_provider(DEFAULT_PROVIDER).complete("You are a strict evaluator.", [{"role": "user", "content": prompt}])
    g = float((re.search(r"groundedness\s*=\s*([01](?:\.\d+)?)", raw) or [0, "0.5"])[1])
    r = float((re.search(r"relevance\s*=\s*([01](?:\.\d+)?)", raw) or [0, "0.5"])[1])
    return {"groundedness": g, "answer_relevance": r, "rationale": raw[:200]}


def evaluate(retriever, golden: list[dict], ks: tuple = (3, 5)) -> dict:
    """Document-level retrieval metrics over a golden split."""
    maxk = max(ks)
    recall_hits = {k: 0.0 for k in ks}
    precision_sum = {k: 0.0 for k in ks}
    rr_sum = 0.0
    per_query = []
    for row in golden:
        expected = set(row["expected_doc_ids"])
        hits = retriever.retrieve(row["query"], k=maxk)
        ranked_docs = [h["doc_id"] for h in hits]
        first_rank = next((i + 1 for i, d in enumerate(ranked_docs) if d in expected), 0)
        rr = 1.0 / first_rank if first_rank else 0.0
        rr_sum += rr
        q = {"id": row["id"], "expected": sorted(expected), "retrieved": ranked_docs, "rr": rr}
        for k in ks:
            topk = ranked_docs[:k]
            found = expected & set(topk)
            recall_hits[k] += len(found) / len(expected)
            precision_sum[k] += (len(found) / k) if k else 0.0
            q[f"recall_at_{k}"] = len(found) / len(expected)
        per_query.append(q)
    n = max(1, len(golden))
    return {
        "recall_at": {k: recall_hits[k] / n for k in ks},
        "precision_at": {k: precision_sum[k] / n for k in ks},
        "mrr": rr_sum / n,
        "per_query": per_query,
    }


def load_golden(path: str | None = None, split: str | None = None) -> list[dict]:
    """Load the golden dataset. Optionally filter to 'dev' or 'test'."""
    p = Path(path) if path else _GOLDEN_PATH
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    if split is not None:
        rows = [r for r in rows if r["split"] == split]
    return rows
