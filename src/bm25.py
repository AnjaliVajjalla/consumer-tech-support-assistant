"""
BM25 keyword search for the Consumer Technology Support Assistant.

What this does (Sprint 4):
  Scores chunks by exact keyword overlap with a query, using BM25
  (classic term-frequency ranking, weighted so rare words count more
  than common ones). This pairs with the embedding-based semantic
  search from Sprint 2: embeddings catch meaning, BM25 catches exact
  terms embeddings can underweight (model numbers, UI element names,
  exact button/menu labels).
"""
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return text.lower().split()


def build_bm25_index(chunks: list[dict]) -> BM25Okapi:
    """Build a BM25 index over chunk text. Rebuild whenever chunks change."""
    return BM25Okapi([tokenize(chunk["text"]) for chunk in chunks])


def bm25_search(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    """Return the top_k chunks ranked by BM25 keyword overlap with the query."""
    index = build_bm25_index(chunks)
    scores = index.get_scores(tokenize(query))
    scored = [{**chunk, "score": score} for chunk, score in zip(chunks, scores)]
    scored.sort(key=lambda c: c["score"], reverse=True)
    return scored[:top_k]
