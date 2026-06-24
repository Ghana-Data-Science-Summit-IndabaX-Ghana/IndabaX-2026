"""Tests for the RAG runner. All run in MOCK_MODE."""
import os
os.environ["MOCK_MODE"] = "true"

from core.rag import run_rag, generate_answer
from core.retrieval import get_default_retriever


def test_run_rag_shape_and_doc_level_log():
    out = run_rag("What interest rate will I pay on a farm loan?")
    assert set(out) >= {"reply", "provider", "model", "mock", "history", "retrieval_log", "log_entry"}
    rl = out["retrieval_log"]
    assert "retrieved_doc_ids" in rl and "retrieved_chunk_ids" in rl
    assert len(rl["retrieved_doc_ids"]) == len(set(rl["retrieved_doc_ids"]))


def test_generate_answer_is_callable_without_retrieval():
    chunks = get_default_retriever("keyword").retrieve("repay at harvest", k=3)
    ans = generate_answer("When do I repay?", chunks, system_prompt="Test.", provider_name="anthropic")
    assert set(ans) == {"reply", "model", "mock", "history"}
    assert isinstance(ans["reply"], str) and ans["reply"]


def test_mock_rag_reply_is_agric_and_provider_aware():
    from core.mocks import get_mock
    a = get_mock("What interest rate will I pay on a farm loan?", "rag", "anthropic")
    g = get_mock("What interest rate will I pay on a farm loan?", "rag", "gemma")
    assert a and g
    assert "loan" in a.lower() or "interest" in a.lower() or "apr" in a.lower()
    assert a != g  # provider-flavored


def test_mock_guarantee_scenario_contains_catchable_phrase():
    from core.mocks import get_mock
    r = get_mock("Will I definitely be approved for the fertiliser loan?", "guardrails", "anthropic")
    assert "definitely be approved" in r.lower()
