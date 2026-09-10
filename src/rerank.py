"""
Cross-encoder reranking for the Consumer Technology Support Assistant.

What this does (Sprint 4):
  Re-scores a shortlist of candidate chunks together with the query,
  for a more accurate final ranking than embedding similarity alone.

  Bi-encoders (used everywhere else here) embed the query and each
  chunk separately, then compare vectors - fast enough to search the
  whole corpus, but approximate. A cross-encoder feeds the query and
  one chunk into the model together so it can judge the match directly
  - more accurate, but too slow to run over every chunk, so it only
  reranks a small shortlist retrieval already narrowed down.
"""
from sentence_transformers import CrossEncoder

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_model = None


def get_model() -> CrossEncoder:
    """Create the cross-encoder once and reuse it."""
    global _model
    if _model is None:
        _model = CrossEncoder(MODEL_NAME)
    return _model


def rerank(query: str, candidates: list[dict], top_k: int = 3) -> list[dict]:
    """Re-sort candidate chunks by a cross-encoder's relevance score for the query."""
    model = get_model()
    pairs = [(query, c["text"]) for c in candidates]
    scores = model.predict(pairs)

    scored = [{**c, "score": float(s)} for c, s in zip(candidates, scores)]
    scored.sort(key=lambda c: c["score"], reverse=True)
    return scored[:top_k]
