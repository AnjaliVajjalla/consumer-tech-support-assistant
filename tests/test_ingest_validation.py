import json

import pytest

import src.ingest as ingest
from src.ingest import build_corpus, load_product_folder


VALID = {"file": "setup.txt", "product": "Example Buds", "title": "Setup", "url": "https://example.com/setup", "category": "setup"}


def make_folder(tmp_path, entries=None, text="Useful official support text."):
    folder = tmp_path / "example"
    folder.mkdir()
    (folder / "_meta.json").write_text(json.dumps(entries or [VALID]))
    (folder / "setup.txt").write_text(text)
    return folder


def test_missing_metadata(tmp_path):
    folder = tmp_path / "example"; folder.mkdir()
    with pytest.raises(FileNotFoundError): load_product_folder(folder)


def test_missing_source_file(tmp_path):
    folder = tmp_path / "example"; folder.mkdir(); (folder / "_meta.json").write_text(json.dumps([VALID]))
    with pytest.raises(FileNotFoundError): load_product_folder(folder)


def test_orphan_text_file(tmp_path):
    folder = make_folder(tmp_path); (folder / "orphan.txt").write_text("orphan")
    with pytest.raises(ValueError, match="missing metadata"): load_product_folder(folder)


def test_empty_text(tmp_path):
    with pytest.raises(ValueError, match="Empty source"): load_product_folder(make_folder(tmp_path, text=""))


def test_blank_url(tmp_path):
    entry = {**VALID, "url": ""}
    with pytest.raises(ValueError, match="blank"): load_product_folder(make_folder(tmp_path, [entry]))


def test_invalid_metadata_fields(tmp_path):
    entry = {key: value for key, value in VALID.items() if key != "category"}
    with pytest.raises(ValueError, match="fields"): load_product_folder(make_folder(tmp_path, [entry]))


def test_inconsistent_product_names(tmp_path):
    second = {**VALID, "file": "other.txt", "product": "Other Buds"}
    folder = make_folder(tmp_path, [VALID, second]); (folder / "other.txt").write_text("Other official text")
    with pytest.raises(ValueError, match="Inconsistent"): load_product_folder(folder)


def test_duplicate_document_ids_across_corpus(tmp_path, monkeypatch):
    (tmp_path / "first").mkdir()
    (tmp_path / "second").mkdir()
    duplicate = {
        "id": "same-id",
        "product": "Example Buds",
        "title": "Setup",
        "url": "https://example.com/setup",
        "category": "setup",
        "text": "Useful official support text.",
    }
    monkeypatch.setattr(ingest, "load_product_folder", lambda folder: [duplicate.copy()])

    with pytest.raises(ValueError, match="Duplicate document IDs"):
        build_corpus(tmp_path)


def test_all_real_folders_ingest_successfully():
    corpus = build_corpus()
    assert len(corpus) >= 20
    assert len({record["id"] for record in corpus}) == len(corpus)
