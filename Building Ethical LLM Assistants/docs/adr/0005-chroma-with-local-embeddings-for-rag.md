# 5. Chroma vector store with local embeddings, alongside the keyword retriever

Date: 2026-06-22

## Status

Accepted

## Context

The RAG stage needs to teach real retrieval against the 5-step RAG framework (scope → golden dataset → retrieval + metrics → answer system → experiments). The original retriever was keyword token-overlap over four documents hardcoded inline in `core/knowledge_base.py` — transparent, but too shallow to teach embeddings, chunking, or retrieval metrics, and with no dataset behind it.

Two constraints pull against adding a vector store:

1. **MOCK_MODE must run with no API key and no connectivity** (the room's cost/reliability control), and retrieval always runs — even mocked — so the retrieval log is real. Any embedding model reached over the network would break this. Anthropic has no embeddings API; Gemma's needs network.
2. **The knowledge base must stay hand-inspectable** (ADR-0002, CONTEXT.md). A vector store is opaque; participants must still be able to read the retriever line-by-line and read the documents as files.

## Decision

Add a Chroma retriever **alongside** the keyword retriever, behind one `Retriever.retrieve(query, k) → [chunk]` interface (dependency-injected, as the runner already supports).

- **Local embeddings.** The Chroma adapter embeds with a local sentence-transformer (`paraphrase-multilingual-MiniLM-L12-v2` by default — multilingual so English-lexified Pidgin queries retrieve correctly). No network at query time after a one-time model download (the same network moment as `pip install`). This preserves offline MOCK_MODE.
- **Keep the keyword retriever as the inspectable baseline.** Two adapters make the seam real; the keyword path is what participants read first, the Chroma path is "the production tool this maps to." Both index the *same* chunks so metrics compare fairly.
- **Documents move to `data/agric/*.md`** (Markdown + frontmatter), chunked by `##` section. An ingestion step (`core/ingest.py`) parses → chunks → embeds → writes an on-disk Chroma collection.
- **The Chroma store is gitignored and rebuilt from the Markdown**, never committed. Rebuilding is the ingestion lesson and takes seconds for ~50 chunks.

## Consequences

- New dependencies: `chromadb` and `sentence-transformers` (pulls in torch). Heavier install, but Colab-friendly, and the only runtime cost is a one-time model download.
- Offline MOCK_MODE survives: query embedding is local, so retrieval (keyword *and* Chroma) runs with no connectivity and the retrieval log stays real.
- The default embedding model is load-bearing for the language-equity lesson — it must pass the Pidgin golden queries. Swapping it (e.g. to English-only MiniLM) becomes a Step-5 experiment, not a silent default.
- The retriever interface changes from a stateless `retrieve(message, kb)` to a stateful retriever object holding its own index. The runner's DI contract is unchanged (callers still pass a retriever); inline notebook retrievers and `core` defaults stay interchangeable.
- The hand-inspectable property is preserved through the keyword baseline + Markdown documents, not the Chroma store itself. Accepting an opaque index for the semantic path is the residual trade-off.
