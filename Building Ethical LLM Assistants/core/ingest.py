"""Ingestion: Markdown fact-sheets -> chunks -> persisted Chroma collection."""
import re
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "agric"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_documents(data_dir: str | None = None) -> list[dict]:
    """Parse each Markdown fact-sheet into {id, title, source, body}."""
    base = Path(data_dir) if data_dir else _DATA_DIR
    docs = []
    for f in sorted(base.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
        if not m:
            raise ValueError(f"{f.name}: missing frontmatter")
        fm = {}
        for line in m.group(1).splitlines():
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
        docs.append({
            "id": fm["id"], "title": fm["title"],
            "source": fm["source"], "body": m.group(2).strip(),
        })
    return docs


def chunk_documents(docs: list[dict]) -> list[dict]:
    """Split each document body on '## ' headings into chunks."""
    chunks = []
    for doc in docs:
        parts = re.split(r"\n(?=## )", doc["body"])
        for part in parts:
            part = part.strip()
            if not part:
                continue
            heading = part.splitlines()[0].lstrip("# ").strip()
            chunks.append({
                "id": f"{doc['id']}#{_slug(heading)}",
                "doc_id": doc["id"],
                "title": doc["title"],
                "source": doc["source"],
                "content": part,
            })
    return chunks


def build_chroma(chunks: list[dict], persist_dir: str, embedding_fn) -> "object":
    """Embed chunks and persist a Chroma collection. Returns the collection."""
    import chromadb
    client = chromadb.PersistentClient(path=persist_dir)
    try:
        client.delete_collection("agric")
    except Exception:
        pass
    coll = client.create_collection("agric", configuration={"hnsw": {"space": "cosine"}})
    coll.add(
        ids=[c["id"] for c in chunks],
        documents=[c["content"] for c in chunks],
        embeddings=embedding_fn([c["content"] for c in chunks]),
        metadatas=[{"doc_id": c["doc_id"], "title": c["title"], "source": c["source"]} for c in chunks],
    )
    return coll
