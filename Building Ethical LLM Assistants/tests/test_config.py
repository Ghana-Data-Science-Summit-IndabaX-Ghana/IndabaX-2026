import importlib


def test_new_config_defaults(monkeypatch):
    for var in ("DEFAULT_RETRIEVER", "CHROMA_DIR", "EMBEDDING_MODEL"):
        monkeypatch.delenv(var, raising=False)
    import core.config as config
    importlib.reload(config)
    assert config.DEFAULT_RETRIEVER == "keyword"
    assert config.CHROMA_DIR.endswith(".chroma")
    assert "MiniLM" in config.EMBEDDING_MODEL
