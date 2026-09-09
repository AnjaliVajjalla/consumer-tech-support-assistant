"""
Embedding script for the Consumer Technology Support Assistant.

What this does (Sprint 2):
  Turns chunk text into embedding vectors so semantic search can compare
  a user's question against chunks by meaning, not just keywords.
"""

from sentence_transformers import SentenceTransformer

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
