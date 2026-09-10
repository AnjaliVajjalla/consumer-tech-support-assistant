"""
Chunking script for the Consumer Technology Support Assistant.

What this does (Sprint 2):
  1. Loads the document corpus (via ingest.build_corpus)
  2. Splits each document's text into overlapping word-based chunks
  3. Builds one chunk record per chunk, carrying the parent document's
     metadata (product, title, url, category) forward
  4. Writes all chunk records to data/processed/chunks.json

Why this matters for RAG: semantic search retrieves chunks, not whole
documents. Every chunk still needs to trace back to its source doc so
answers can cite exactly where they came from.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ingest import build_corpus  # noqa: E402

OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "chunks.json"

CHUNK_SIZE = 100
CHUNK_OVERLAP = 20


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    step = chunk_size - overlap
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start += step

    return chunks


def chunk_corpus(corpus: list[dict]) -> list[dict]:
    """Chunk every document in the corpus into chunk records."""
    all_chunks = []

    for record in corpus:
        pieces = chunk_text(record["text"])
        for i, piece in enumerate(pieces):
            chunk_record = {
                "chunk_id": f"{record['id']}__c{i}",
                "doc_id": record["id"],
                "product": record["product"],
                "title": record["title"],
                "url": record["url"],
                "category": record["category"],
                "text": piece,
            }
            all_chunks.append(chunk_record)

    return all_chunks


def main() -> None:
    corpus = build_corpus()
    chunks = chunk_corpus(corpus)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    print(f"Chunked {len(corpus)} documents into {len(chunks)} chunks")
    print(f"Wrote chunks to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
