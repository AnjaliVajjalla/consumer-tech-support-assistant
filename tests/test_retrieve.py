"""
Tests for the retrieval script.

Why these tests: retrieval is the whole point of building embeddings.
If it doesn't actually return the most relevant chunk for a question,
every later sprint (grounded answers, citations) is built on a broken
foundation. This test proves the ranking works, not just that it runs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from embed import embed_texts  # noqa: E402
from retrieve import retrieve, hybrid_retrieve  # noqa: E402
from bm25 import bm25_search  # noqa: E402


def make_chunk(chunk_id: str, text: str) -> dict:
    return {
        "chunk_id": chunk_id,
        "doc_id": "doc1",
        "product": "test_product",
        "title": "Test Doc",
        "url": "https://example.com",
        "category": "setup",
        "text": text,
        "embedding": embed_texts([text])[0],
    }


def test_retrieve_returns_the_most_relevant_chunk_first():
    chunks = [
        make_chunk("c_pairing", "How do I put my headphones into pairing mode?"),
        make_chunk("c_battery", "What is the battery life of the headphones?"),
        make_chunk("c_returns", "What is the return policy for online orders?"),
    ]

    results = retrieve("How do I pair my headphones with a new device?", chunks, top_k=1)

    assert results[0]["chunk_id"] == "c_pairing"


def test_retrieve_respects_top_k():
    chunks = [
        make_chunk("c1", "How do I put my headphones into pairing mode?"),
        make_chunk("c2", "What is the battery life of the headphones?"),
        make_chunk("c3", "What is the return policy for online orders?"),
    ]

    results = retrieve("How do I pair my headphones?", chunks, top_k=2)

    assert len(results) == 2


def test_hybrid_retrieve_at_alpha_1_matches_pure_semantic_ranking():
    """alpha=1.0 should weight semantic score only, so ranking should match retrieve()."""
    chunks = [
        make_chunk("c_pairing", "How do I put my headphones into pairing mode?"),
        make_chunk("c_keyword", "Press the AirPlay button in Control Center to select your headphones."),
        make_chunk("c_other", "What is the return policy for online orders?"),
    ]
    query = "AirPlay button Control Center"

    semantic_order = [r["chunk_id"] for r in retrieve(query, chunks, top_k=3)]
    hybrid_order = [r["chunk_id"] for r in hybrid_retrieve(query, chunks, top_k=3, alpha=1.0)]

    assert hybrid_order == semantic_order


def test_hybrid_retrieve_at_alpha_0_matches_pure_bm25_ranking():
    """alpha=0.0 should weight BM25 score only, so ranking should match bm25_search()."""
    chunks = [
        make_chunk("c_pairing", "How do I put my headphones into pairing mode?"),
        make_chunk("c_keyword", "Press the AirPlay button in Control Center to select your headphones."),
        make_chunk("c_other", "What is the return policy for online orders?"),
    ]
    query = "AirPlay button Control Center"

    bm25_order = [r["chunk_id"] for r in bm25_search(query, chunks, top_k=3)]
    hybrid_order = [r["chunk_id"] for r in hybrid_retrieve(query, chunks, top_k=3, alpha=0.0)]

    assert hybrid_order == bm25_order


def test_hybrid_retrieve_respects_top_k():
    chunks = [
        make_chunk("c1", "How do I put my headphones into pairing mode?"),
        make_chunk("c2", "What is the battery life of the headphones?"),
        make_chunk("c3", "What is the return policy for online orders?"),
    ]

    results = hybrid_retrieve("How do I pair my headphones?", chunks, top_k=2)

    assert len(results) == 2
