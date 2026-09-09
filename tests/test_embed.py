"""
Tests for the embedding script.

Why these tests: embeddings are only useful for semantic search if
similar text actually ends up with similar (close) vectors, and every
text produces a vector of the same length. If either of those breaks,
retrieval in a later sprint would silently return bad matches.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from embed import embed_texts  # noqa: E402


def cosine_similarity(a, b) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def test_embed_texts_returns_one_vector_per_text():
    texts = ["How do I pair my headphones?", "What is the battery life?"]
    vectors = embed_texts(texts)
    assert len(vectors) == len(texts)


def test_all_vectors_have_the_same_length():
    texts = ["Short text.", "A different, somewhat longer piece of text."]
    vectors = embed_texts(texts)
    assert len(vectors[0]) == len(vectors[1])


def test_similar_sentences_are_closer_than_unrelated_ones():
    anchor = "How do I put my headphones into pairing mode?"
    similar = "How do I pair my headphones with a new device?"
    unrelated = "What is the return policy for online orders?"

    vectors = embed_texts([anchor, similar, unrelated])
    anchor_vec, similar_vec, unrelated_vec = vectors

    sim_to_similar = cosine_similarity(anchor_vec, similar_vec)
    sim_to_unrelated = cosine_similarity(anchor_vec, unrelated_vec)

    assert sim_to_similar > sim_to_unrelated, (
        "Embeddings should place semantically similar sentences closer "
        "together than unrelated ones"
    )
