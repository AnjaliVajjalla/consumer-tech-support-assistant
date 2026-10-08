"""
Ingestion script for the Consumer Technology Support Assistant.

What this does (Sprint 1):
  1. Walks data/raw/<product>/ folders
  2. Reads each product's _meta.json (title, source URL, category per file)
  3. Loads the matching .txt file's content
  4. Builds one structured "document record" per file
  5. Writes all records to data/processed/corpus.json

Why this matters for RAG: every downstream step (chunking, embeddings,
retrieval, citations) depends on documents having consistent structure
and a traceable source. This script is where that structure gets created.
"""

import json
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "corpus.json"
REQUIRED_FIELDS = {"file", "product", "title", "url", "category"}


def load_product_folder(folder: Path) -> list[dict]:
    """Load all documents for one product folder into record dicts."""
    meta_path = folder / "_meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing _meta.json in {folder}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_entries = json.load(f)

    if not isinstance(meta_entries, list) or not meta_entries:
        raise ValueError(f"Metadata must be a non-empty list in {meta_path}")

    metadata_files = set()
    products = set()
    for entry in meta_entries:
        if not isinstance(entry, dict) or set(entry) != REQUIRED_FIELDS:
            raise ValueError(f"Invalid metadata fields in {meta_path}")
        if not all(isinstance(entry[field], str) and entry[field].strip() for field in REQUIRED_FIELDS):
            raise ValueError(f"Metadata values cannot be blank in {meta_path}")
        parsed = urlparse(entry["url"])
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"Invalid official source URL in {meta_path}: {entry['url']}")
        if entry["file"] in metadata_files:
            raise ValueError(f"Duplicate metadata file in {meta_path}: {entry['file']}")
        metadata_files.add(entry["file"])
        products.add(entry["product"])

    if len(products) != 1:
        raise ValueError(f"Inconsistent product names in {meta_path}")

    text_files = {path.name for path in folder.glob("*.txt")}
    orphaned = text_files - metadata_files
    if orphaned:
        raise ValueError(f"Text files missing metadata in {folder}: {sorted(orphaned)}")

    records = []
    for entry in meta_entries:
        text_path = folder / entry["file"]
        if not text_path.exists():
            raise FileNotFoundError(f"Missing text file: {text_path}")

        text = text_path.read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"Empty source text: {text_path}")

        record = {
            "id": f"{folder.name}__{text_path.stem}",
            "product": entry["product"],
            "title": entry["title"],
            "url": entry["url"],
            "category": entry["category"],
            "text": text,
        }
        records.append(record)

    return records


def build_corpus(raw_dir: Path = RAW_DIR) -> list[dict]:
    """Build the full corpus across every product folder."""
    all_records = []
    product_folders = sorted(p for p in raw_dir.iterdir() if p.is_dir())

    for folder in product_folders:
        all_records.extend(load_product_folder(folder))

    ids = [record["id"] for record in all_records]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate document IDs found across corpus")

    return all_records


def main() -> None:
    corpus = build_corpus()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2)

    print(f"Ingested {len(corpus)} documents from {RAW_DIR}")
    print(f"Wrote corpus to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
