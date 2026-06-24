"""RAG stage: retrieval (seam) + answer generation (separable), composed."""
from core.config import MOCK_MODE, DEFAULT_PROVIDER
from core.mocks import get_mock
from core.prompts import RAG_SYSTEM_PROMPT
from core.knowledge_base import format_retrieved_context
from core.retrieval import get_default_retriever
from core.logging import make_log_entry

_DEFAULT_K = 5


def generate_answer(query, chunks, system_prompt, provider_name, history=None, stage="rag"):
    """Turn retrieved chunks into a grounded reply. Separate from retrieval."""
    history = list(history) if history else []
    if MOCK_MODE:
        return {"reply": get_mock(query, stage, provider_name),
                "model": f"mock/{provider_name}", "mock": True, "history": history}
    augmented = (
        f"USER QUESTION: {query}\n\n"
        f"RETRIEVED DOCUMENTS:\n{format_retrieved_context(chunks)}\n\n"
        "Answer the question based on the retrieved documents above.\n"
        "If they do not contain the information needed, say so clearly.\n"
    )
    from core.providers import get_provider
    provider = get_provider(provider_name)
    history.append({"role": "user", "content": augmented})
    reply = provider.complete(system_prompt, history)
    return {"reply": reply, "model": provider.model, "mock": False, "history": history}


def run_rag(message, provider_name=None, history=None, system_prompt=None, retriever=None):
    """Compose retrieval + answer. Retrieval always runs (log is real even in MOCK)."""
    provider_name = (provider_name or DEFAULT_PROVIDER).lower()
    system = system_prompt if system_prompt is not None else RAG_SYSTEM_PROMPT
    retriever = retriever if retriever is not None else get_default_retriever()

    chunks = retriever.retrieve(message, k=_DEFAULT_K)
    doc_ids, seen = [], set()
    for c in chunks:
        if c["doc_id"] not in seen:
            seen.add(c["doc_id"])
            doc_ids.append(c["doc_id"])

    answer = generate_answer(message, chunks, system, provider_name, history)
    answer["history"].append({"role": "assistant", "content": answer["reply"]})

    retrieval_log = {
        "query": message,
        "retrieved_doc_ids": doc_ids,
        "retrieved_chunk_ids": [c["id"] for c in chunks],
        "retrieved_doc_titles": [c["title"] for c in chunks],
        "response": answer["reply"],
    }
    log_entry = make_log_entry(
        query=message, provider=provider_name, model=answer["model"],
        mock=answer["mock"], stage="rag",
        retrieved_ids=doc_ids, retrieved_titles=retrieval_log["retrieved_doc_titles"],
        response=answer["reply"],
    )
    return {
        "reply": answer["reply"], "provider": provider_name, "model": answer["model"],
        "mock": answer["mock"], "history": answer["history"],
        "retrieval_log": retrieval_log, "log_entry": log_entry,
    }
