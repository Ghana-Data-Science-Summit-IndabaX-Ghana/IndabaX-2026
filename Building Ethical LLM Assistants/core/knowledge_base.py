"""Formatting helper for retrieved chunks. The corpus now lives in data/agric/."""


def format_retrieved_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant documents were retrieved for this query."
    parts = []
    for c in chunks:
        parts.append(
            f"SOURCE: {c['source']}\n"
            f"TITLE: {c['title']}\n"
            f"CONTENT: {c['content'].strip()}\n"
        )
    return "\n\n".join(parts)
