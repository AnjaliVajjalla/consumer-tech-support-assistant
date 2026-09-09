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
from retrieve import retrieve  # noqa: E402


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
