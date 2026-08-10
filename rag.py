"""Local RAG index over personal documents for the digital twin.

Documents live in the ``knowledge/`` folder as ``.md``/``.txt`` files. Running
this module (``uv run rag.py``) chunks and embeds them into a local index made
of two files: ``data/rag_index.npy`` (embeddings) and ``data/rag_index.json``
(chunk text + source). No database is used.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(override=True)

KNOWLEDGE_DIR = Path(os.getenv("TWIN_KNOWLEDGE_DIR", "knowledge"))
INDEX_DIR = Path(os.getenv("TWIN_INDEX_DIR", "data"))
EMBEDDINGS_PATH = INDEX_DIR / "rag_index.npy"
METADATA_PATH = INDEX_DIR / "rag_index.json"

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 4

_client: OpenAI | None = None


def _openai() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _chunk(text: str) -> list[str]:
    """Split text into overlapping, word-bounded chunks."""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + CHUNK_SIZE]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def _embed(texts: list[str]) -> np.ndarray:
    """Return L2-normalized embeddings so a dot product equals cosine similarity."""
    response = _openai().embeddings.create(model=EMBEDDING_MODEL, input=texts)
    vectors = np.array([item.embedding for item in response.data], dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.clip(norms, 1e-8, None)


def _iter_sources() -> list[Path]:
    """Collect every knowledge document that should be indexed."""
    if not KNOWLEDGE_DIR.is_dir():
        return []
    sources = sorted(KNOWLEDGE_DIR.glob("**/*.md")) + sorted(
        KNOWLEDGE_DIR.glob("**/*.txt")
    )
    return [path for path in sources if path.name != "README.md"]


def ingest() -> dict[str, int]:
    """(Re)build the RAG index from all knowledge documents."""
    documents: list[dict[str, str]] = []
    for path in _iter_sources():
        for chunk in _chunk(path.read_text(encoding="utf-8")):
            documents.append({"source": str(path), "content": chunk})

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    if documents:
        embeddings = _embed([doc["content"] for doc in documents])
    else:
        embeddings = np.empty((0, 0), dtype=np.float32)

    np.save(EMBEDDINGS_PATH, embeddings)
    METADATA_PATH.write_text(json.dumps(documents, indent=2), encoding="utf-8")
    return {"chunks": len(documents), "sources": len(_iter_sources())}


def _load_index() -> tuple[np.ndarray, list[dict[str, str]]]:
    """Load the embeddings matrix and chunk metadata from disk."""
    if not EMBEDDINGS_PATH.exists() or not METADATA_PATH.exists():
        return np.empty((0, 0), dtype=np.float32), []
    embeddings = np.load(EMBEDDINGS_PATH)
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return embeddings, metadata


def search_profile(query: str, top_k: int = TOP_K) -> list[dict[str, str]]:
    """Return the most relevant document chunks for a query."""
    clean_query = query.strip()
    if not clean_query:
        return []

    embeddings, metadata = _load_index()
    if embeddings.size == 0 or not metadata:
        return []

    query_vector = _embed([clean_query])[0]
    scores = embeddings @ query_vector
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [
        {
            "source": metadata[i]["source"],
            "content": metadata[i]["content"],
            "score": round(float(scores[i]), 4),
        }
        for i in top_indices
    ]


if __name__ == "__main__":
    print(ingest())
