"""The retriever seam: one interface, two adapters (keyword baseline + Chroma)."""
import re
from typing import Protocol

_STOP_WORDS = {
    "i", "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "my", "your", "is", "it", "can",
    "get", "be", "do", "if", "me", "am", "are", "was", "not", "no", "so",
}


def _tokenize(text: str) -> set[str]:
    tokens = re.sub(r"[^\w\s]", "", text.lower()).split()
    return {t for t in tokens if t and t not in _STOP_WORDS}


class Retriever(Protocol):
    def retrieve(self, query: str, k: int = 5) -> list[dict]: ...


class KeywordRetriever:
    """Transparent token-overlap baseline over chunks. Score normalised to [0,1]."""

    def __init__(self, chunks: list[dict]):
        self.chunks = chunks

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        query_terms = _tokenize(query)
        denom = max(1, len(query_terms))
        scored = []
        for c in self.chunks:
            overlap = len(query_terms & _tokenize(c["title"] + " " + c["content"]))
            if overlap > 0:
                scored.append({**c, "score": overlap / denom})
        scored.sort(key=lambda h: h["score"], reverse=True)
        return scored[:k]


def default_embedding_fn():
    """Local sentence-transformer embedding callable. Lazily imported (heavy)."""
    from sentence_transformers import SentenceTransformer
    from core.config import EMBEDDING_MODEL
    model = SentenceTransformer(EMBEDDING_MODEL)

    def embed(texts: list[str]) -> list[list[float]]:
        return model.encode(list(texts), normalize_embeddings=True).tolist()

    return embed


class ChromaRetriever:
    """Semantic retrieval over a local Chroma collection. Score = cosine similarity in [0,1]."""

    def __init__(self, chunks: list[dict], persist_dir: str | None = None, embedding_fn=None):
        from core.config import CHROMA_DIR
        from core.ingest import build_chroma
        self._by_id = {c["id"]: c for c in chunks}
        self._embed = embedding_fn or default_embedding_fn()
        self._coll = build_chroma(chunks, persist_dir or CHROMA_DIR, self._embed)

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        res = self._coll.query(query_embeddings=self._embed([query]), n_results=k)
        hits = []
        for cid, dist in zip(res["ids"][0], res["distances"][0]):
            chunk = self._by_id[cid]
            hits.append({**chunk, "score": max(0.0, 1.0 - float(dist))})
        return hits


_RETRIEVER_CACHE: dict[str, "Retriever"] = {}


def get_default_retriever(name: str | None = None) -> "Retriever":
    """Build (and cache) the configured retriever over the ingested corpus."""
    from core.config import DEFAULT_RETRIEVER
    from core.ingest import load_documents, chunk_documents
    name = (name or DEFAULT_RETRIEVER).lower()
    if name not in _RETRIEVER_CACHE:
        chunks = chunk_documents(load_documents())
        if name == "chroma":
            _RETRIEVER_CACHE[name] = ChromaRetriever(chunks)
        else:
            _RETRIEVER_CACHE[name] = KeywordRetriever(chunks)
    return _RETRIEVER_CACHE[name]
