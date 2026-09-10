"""
Embedding script for the Consumer Technology Support Assistant.

What this does (Sprint 2):
  Turns chunk text into embedding vectors so semantic search can compare
  a user's question against chunks by meaning, not just keywords.
"""

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "chunks.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "embeddings.json"

MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Turn a list of texts into a list of embedding vectors."""
    model = get_model()
    vectors = model.encode(texts)
    return vectors.tolist()


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Embed each chunk's text, keeping the chunk_id link for citations."""
    texts = [chunk["text"] for chunk in chunks]
    vectors = embed_texts(texts)
    return [
        {"chunk_id": chunk["chunk_id"], "embedding": vector}
        for chunk, vector in zip(chunks, vectors)
    ]


def main() -> None:
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)

    embeddings = embed_chunks(chunks)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(embeddings, f)

    print(f"Embedded {len(embeddings)} chunks")
    print(f"Wrote embeddings to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
