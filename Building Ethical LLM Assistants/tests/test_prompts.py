from core import prompts


def test_prompts_are_agric_scoped():
    assert "input" in prompts.BASE_SYSTEM_PROMPT.lower()
    assert "farmer" in prompts.BASE_SYSTEM_PROMPT.lower()
    assert "extension" in prompts.BASE_SYSTEM_PROMPT.lower()  # agronomy redirect line
    assert "credit decision" in prompts.RAG_SYSTEM_PROMPT.lower()  # still no decisions
    assert "source" in prompts.RAG_SYSTEM_PROMPT.lower()  # citation rule kept
    assert "loan options" not in prompts.BASE_SYSTEM_PROMPT.lower()  # old framing gone
