from core.ingest import load_documents, chunk_documents
from core.retrieval import KeywordRetriever

CHUNKS = chunk_documents(load_documents())


def test_keyword_retriever_returns_scored_chunks():
    r = KeywordRetriever(CHUNKS)
    hits = r.retrieve("interest rate on a farm loan", k=3)
    assert 1 <= len(hits) <= 3
    assert all(0.0 <= h["score"] <= 1.0 for h in hits)
    assert hits == sorted(hits, key=lambda h: h["score"], reverse=True)
    assert {"id", "doc_id", "title", "source", "content", "score"} <= set(hits[0])


def test_keyword_retriever_misses_pidgin():
    # The teaching point: formal-token overlap fails on Pidgin phrasing.
    r = KeywordRetriever(CHUNKS)
    hits = r.retrieve("Wetin I go need before dem fit give me loan for fertilizer?", k=5)
    # Either nothing, or nothing from the correct doc near the top.
    assert all(h["doc_id"] != "eligibility-basics" for h in hits[:1]) or hits == []
