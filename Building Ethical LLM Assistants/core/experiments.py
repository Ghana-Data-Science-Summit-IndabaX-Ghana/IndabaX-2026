"""Single-variable experiment harness: change one knob, measure delta vs baseline."""
from core.eval import load_golden, evaluate
from core.ingest import load_documents, chunk_documents
from core.retrieval import KeywordRetriever, ChromaRetriever


def _build_retriever(name: str, chunks):
    return ChromaRetriever(chunks) if name == "chroma" else KeywordRetriever(chunks)


def run_experiment(variable: str, values: list, golden_split: str = "dev", k: int = 5) -> list[dict]:
    """Run a single-variable experiment over the golden dev split.

    variable: 'retriever' (values like ['keyword', 'chroma']) or 'k' (values like [3, 5, 8])
    Returns list of {value, recall_at_5, mrr, delta_recall, delta_mrr} vs first value as baseline.
    """
    golden = load_golden(split=golden_split)
    chunks = chunk_documents(load_documents())
    results = []
    base_recall = base_mrr = None
    for v in values:
        if variable == "retriever":
            retr, ks = _build_retriever(v, chunks), (3, k)
        elif variable == "k":
            retr, ks = KeywordRetriever(chunks), (3, v)
        else:
            raise ValueError(f"Unsupported experiment variable: {variable!r}")
        m = evaluate(retr, golden, ks=ks)
        recall = m["recall_at"][max(ks)]
        if base_recall is None:
            base_recall, base_mrr = recall, m["mrr"]
        results.append({
            "value": v,
            "recall_at_5": recall,
            "mrr": m["mrr"],
            "delta_recall": round(recall - base_recall, 4),
            "delta_mrr": round(m["mrr"] - base_mrr, 4),
        })
    return results
