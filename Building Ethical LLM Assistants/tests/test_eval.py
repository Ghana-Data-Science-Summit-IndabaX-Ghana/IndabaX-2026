from core.eval import load_golden, evaluate, groundedness_signal
from core.retrieval import get_default_retriever

VALID_DOC_IDS = {
    "eligibility-basics", "girsal", "warehouse-receipt",
    "rcb-terms", "outgrower-aggregator", "borrowers-lenders-apr",
}


def test_golden_loads_and_is_well_formed():
    rows = load_golden()
    assert len(rows) == 24
    for r in rows:
        assert r["id"] and r["query"]
        assert r["split"] in ("dev", "test")
        assert r["expected_doc_ids"], f"{r['id']} has no expected docs"
        assert set(r["expected_doc_ids"]) <= VALID_DOC_IDS


def test_evaluate_returns_metrics():
    r = get_default_retriever("keyword")
    m = evaluate(r, load_golden(split="dev"), ks=(3, 5))
    assert 0.0 <= m["recall_at"][5] <= 1.0
    assert 0.0 <= m["mrr"] <= 1.0
    assert 0.0 <= m["precision_at"][5] <= 1.0
    assert len(m["per_query"]) == len(load_golden(split="dev"))
    assert m["recall_at"][5] >= m["recall_at"][3]  # larger window never worse


def test_evaluate_answer_flags_missing_citation():
    from core.eval import evaluate_answer
    chunks = [{"id": "rcb#x", "doc_id": "rcb-terms", "title": "Rural and Community Bank Farm Loan Terms",
               "source": "ARB Apex Bank", "content": "Interest is quoted as APR.", "score": 0.5}]
    res = evaluate_answer("What interest will I pay?", "Some interest applies.", chunks)
    assert res["citation_ok"] is False
    assert "missing_citation" in res["tags"]
    assert 0.0 <= res["judge_groundedness"] <= 1.0


def test_groundedness_signal():
    chunks = [{"id": "girsal#x", "doc_id": "girsal", "title": "GIRSAL Credit Guarantee",
               "source": "GIRSAL 2024", "content": "...", "score": 0.6}]
    grounded = groundedness_signal("According to the GIRSAL Credit Guarantee, ...", chunks)
    assert grounded["has_valid_citation"] is True
    assert grounded["grounded"] is True

    ungrounded = groundedness_signal("You will definitely be approved.", chunks=[])
    assert ungrounded["grounded"] is False
    assert ungrounded["top_score"] == 0.0


def test_golden_split_ratio_and_pidgin_seed():
    rows = load_golden()
    dev = load_golden(split="dev")
    test = load_golden(split="test")
    assert len(dev) + len(test) == 24
    assert 15 <= len(dev) <= 18  # ~70%
    # at least 5 deliberately colloquial/Pidgin queries, tagged in id with 'pidgin'
    pidgin = [r for r in rows if "pidgin" in r["id"]]
    assert len(pidgin) >= 5
