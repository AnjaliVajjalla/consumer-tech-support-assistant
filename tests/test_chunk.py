"""
Tests for the chunking script.

Why these tests: chunking is where documents lose their original shape.
If a chunk drops its source metadata or the text gets mangled, retrieval
can still "work" while citations become wrong or chunks become
untraceable. These tests catch that early.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ingest import build_corpus  # noqa: E402
from chunk import chunk_corpus, chunk_text  # noqa: E402


def test_chunks_are_produced():
    corpus = build_corpus()
    chunks = chunk_corpus(corpus)
    assert len(chunks) > 0, "Chunking should produce at least one chunk"


def test_every_chunk_has_required_fields():
    corpus = build_corpus()
    chunks = chunk_corpus(corpus)
    required_fields = {"chunk_id", "doc_id", "product", "title", "url", "category", "text"}

    for chunk in chunks:
        missing = required_fields - chunk.keys()
        assert not missing, f"Chunk {chunk.get('chunk_id')} missing fields: {missing}"


def test_every_chunk_has_nonempty_text():
    corpus = build_corpus()
    chunks = chunk_corpus(corpus)
    for chunk in chunks:
        assert chunk["text"].strip() != "", f"Chunk {chunk['chunk_id']} has empty text"


def test_chunk_ids_are_unique():
    corpus = build_corpus()
    chunks = chunk_corpus(corpus)
    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids)), "Chunk IDs must be unique for citations to work"


def test_every_chunk_traces_back_to_a_real_document():
    corpus = build_corpus()
    doc_ids = {r["id"] for r in corpus}
    chunks = chunk_corpus(corpus)
    for chunk in chunks:
        assert chunk["doc_id"] in doc_ids, f"Chunk {chunk['chunk_id']} points to unknown doc {chunk['doc_id']}"


def test_short_text_returns_single_chunk():
    text = "This is a short document with very few words."
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert chunks == [text]


def test_long_text_splits_into_overlapping_chunks():
    words = [f"word{i}" for i in range(250)]
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=100, overlap=20)

    assert len(chunks) == 3

    first_chunk_words = chunks[0].split()
    second_chunk_words = chunks[1].split()
    assert first_chunk_words[-20:] == second_chunk_words[:20], "Consecutive chunks should overlap by 20 words"
