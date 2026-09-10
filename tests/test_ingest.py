"""
Tests for the ingestion script.

Why these tests: RAG systems fail silently if ingestion drops or
mislabels a document (wrong URL, missing category), because everything
downstream trusts this data. These tests catch that early.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ingest import build_corpus, RAW_DIR  # noqa: E402


def test_corpus_has_records():
    corpus = build_corpus()
    assert len(corpus) > 0, "Ingestion should find at least one document"


def test_every_record_has_required_fields():
    corpus = build_corpus()
    required_fields = {"id", "product", "title", "url", "category", "text"}

    for record in corpus:
        missing = required_fields - record.keys()
        assert not missing, f"Record {record.get('id')} missing fields: {missing}"


def test_every_record_has_nonempty_text():
    corpus = build_corpus()
    for record in corpus:
        assert record["text"].strip() != "", f"Record {record['id']} has empty text"


def test_ids_are_unique():
    corpus = build_corpus()
    ids = [r["id"] for r in corpus]
    assert len(ids) == len(set(ids)), "Document IDs must be unique for citations to work"


def test_expected_products_present():
    corpus = build_corpus()
    products = {r["product"] for r in corpus}
    assert "Sony WH-1000XM5" in products
    assert "AirPods Pro 2 (USB-C)" in products
