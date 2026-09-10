"""
Tests for BM25 keyword search.

Why this test: BM25's whole job is exact term overlap, not meaning. This
proves a chunk sharing the query's literal words outranks one that's
topically similar but doesn't share those words.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bm25 import bm25_search  # noqa: E402


def test_bm25_ranks_exact_keyword_match_first():
    chunks = [
        {"chunk_id": "c_keyword", "text": "Press the AirPlay button in Control Center to select your headphones."},
        {"chunk_id": "c_other", "text": "Battery life varies depending on volume and noise cancellation settings."},
    ]

    results = bm25_search("AirPlay button Control Center", chunks, top_k=1)

    assert results[0]["chunk_id"] == "c_keyword"


def test_bm25_respects_top_k():
    chunks = [
        {"chunk_id": "c1", "text": "How do I put my headphones into pairing mode?"},
        {"chunk_id": "c2", "text": "What is the battery life of the headphones?"},
        {"chunk_id": "c3", "text": "What is the return policy for online orders?"},
    ]

    results = bm25_search("pairing mode", chunks, top_k=2)

    assert len(results) == 2
