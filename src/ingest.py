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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "corpus.json"


def load_product_folder(folder: Path) -> list[dict]:
    """Load all documents for one product folder into record dicts."""
    meta_path = folder / "_meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing _meta.json in {folder}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_entries = json.load(f)

    records = []
    for entry in meta_entries:
        text_path = folder / entry["file"]
        if not text_path.exists():
            raise FileNotFoundError(f"Missing text file: {text_path}")

        text = text_path.read_text(encoding="utf-8").strip()

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
