def test_rag_section_flow_runs_offline():
    """Mirrors the notebook RAG cells: ingest -> eval baseline -> swap -> experiment."""
    from core.eval import load_golden, evaluate
    from core.retrieval import get_default_retriever
    from core.experiments import run_experiment

    base = evaluate(get_default_retriever("keyword"), load_golden(split="dev"))
    assert 0.0 <= base["recall_at"][5] <= 1.0
    results = run_experiment("k", [3, 5], golden_split="dev")
    assert len(results) == 2
