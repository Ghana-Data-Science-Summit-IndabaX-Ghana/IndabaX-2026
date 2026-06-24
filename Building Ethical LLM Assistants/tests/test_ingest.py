from pathlib import Path
import re

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "agric"
EXPECTED_IDS = {
    "eligibility-basics", "girsal", "warehouse-receipt",
    "rcb-terms", "outgrower-aggregator", "borrowers-lenders-apr",
}


def _parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, "missing frontmatter"
    fm = {}
    for line in m.group(1).splitlines():
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip()
    return fm


from core.ingest import load_documents, chunk_documents


def test_load_documents():
    docs = load_documents()
    assert len(docs) == 6
    d = {x["id"]: x for x in docs}["girsal"]
    assert d["title"] and d["source"]
    assert "## " in d["body"]


def test_chunk_documents():
    chunks = chunk_documents(load_documents())
    assert len(chunks) >= 30
    for c in chunks:
        assert set(c) == {"id", "doc_id", "title", "source", "content"}
        assert c["id"].startswith(c["doc_id"] + "#")
        assert 1 <= len(c["content"].split()) <= 400
    # parent doc ids are exactly the six corpus ids
    assert {c["doc_id"] for c in chunks} == {
        "eligibility-basics", "girsal", "warehouse-receipt",
        "rcb-terms", "outgrower-aggregator", "borrowers-lenders-apr",
    }


def test_corpus_present_and_well_formed():
    files = list(DATA_DIR.glob("*.md"))
    ids = {f.stem for f in files}
    assert ids == EXPECTED_IDS
    for f in files:
        text = f.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        assert fm["id"] == f.stem
        assert fm["title"] and fm["source"]
        body = text.split("---", 2)[2]
        assert body.count("\n## ") >= 3, f"{f.stem} needs >=4 sections"
        word_count = len(body.split())
        assert 350 <= word_count <= 1200, f"{f.stem} has {word_count} words"
