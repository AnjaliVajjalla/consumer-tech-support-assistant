"""
Retrieval script for the Consumer Technology Support Assistant.

What this does (Sprint 2):
  Given a user's question, finds the chunks whose meaning is closest to
  it, so an answer can be grounded in and cite the right source passages.
"""

import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from embed import embed_texts  # noqa: E402

CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "chunks.json"
EMBEDDINGS_PATH = PROJECT_ROOT / "data" / "processed" / "embeddings.json"


def cosine_similarity(a, b) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def load_chunks_with_embeddings() -> list[dict]:
    """Join chunk records with their embeddings by chunk_id."""
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)
    with open(EMBEDDINGS_PATH, encoding="utf-8") as f:
        embeddings = json.load(f)

    embedding_by_id = {e["chunk_id"]: e["embedding"] for e in embeddings}
    for chunk in chunks:
        chunk["embedding"] = embedding_by_id[chunk["chunk_id"]]
    return chunks


def retrieve(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    """Return the top_k chunks most semantically similar to the query."""
    query_vector = embed_texts([query])[0]

    scored = [
        {**chunk, "score": cosine_similarity(query_vector, chunk["embedding"])}
        for chunk in chunks
    ]
    scored.sort(key=lambda c: c["score"], reverse=True)
    return scored[:top_k]


def main() -> None:
    chunks = load_chunks_with_embeddings()
    query = "How do I pair my headphones?"
    results = retrieve(query, chunks)

    print(f"Query: {query}\n")
    for r in results:
        print(f"[{r['score']:.3f}] {r['product']} - {r['title']}")
        print(f"  {r['text'][:150]}...")
        print()


if __name__ == "__main__":
    main()
