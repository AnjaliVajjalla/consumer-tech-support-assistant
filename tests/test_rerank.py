"""
Tests for cross-encoder reranking.

Why this test: reranking only earns its keep if it can actually fix a
bad initial order, scoring the query and each chunk together instead of
comparing separately-embedded vectors.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rerank import rerank  # noqa: E402


def test_rerank_moves_the_more_relevant_chunk_to_the_top():
    query = "How do I put my Sony headphones into pairing mode?"
    candidates = [
        {"chunk_id": "c_off_topic", "text": "What is the return policy for online orders?"},
        {"chunk_id": "c_relevant", "text": "Press and hold the power button for about 5 seconds to enter pairing mode."},
    ]

    results = rerank(query, candidates, top_k=2)

    assert results[0]["chunk_id"] == "c_relevant"


def test_rerank_respects_top_k():
    query = "How do I pair my headphones?"
    candidates = [
        {"chunk_id": "c1", "text": "Pairing mode instructions."},
        {"chunk_id": "c2", "text": "Battery life details."},
        {"chunk_id": "c3", "text": "Return policy details."},
    ]

    results = rerank(query, candidates, top_k=1)

    assert len(results) == 1
