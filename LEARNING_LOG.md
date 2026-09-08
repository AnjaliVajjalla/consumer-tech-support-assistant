# Learning Log — Consumer Technology Support Assistant

Running notes on what's been built, what each sprint taught, and how to talk
about it in an interview. Read this before opening a new Claude Code session
on this project so you don't lose context.

## How we work on this project
1. Teach the lesson for the sprint
2. Show the code
3. Explain it
4. Explain the takeaway + how to describe it to an interviewer
5. Confirm you understand it
6. Commit, then move to the next sprint

## Sprint 0 — Define scope (done)
**What it is:** `PROJECT_BRIEF.md` — chosen products (Sony WH-1000XM5, AirPods Pro 2
USB-C), official sources only, boundaries (no invented specs, no warranty/repair
answers), success criteria.

**Lesson:** Define scope and failure boundaries before writing code. An AI feature
with no defined "what it won't do" is a liability, not a product.

**Interview answer:** "Before building, I wrote a one-page brief defining what the
assistant would and wouldn't do, so failure modes were designed for up front
instead of discovered later."

## Sprint 1 — Ingestion (code written, needs your review/commit)
**What it is:** `src/ingest.py` reads raw docs + `_meta.json` sidecars from
`data/raw/<product>/` and builds a structured corpus (`data/processed/corpus.json`).
Each record: id, product, title, url, category, text.

**Lesson:** Ingestion is a separate, offline step from retrieval. It only needs to
re-run when source docs change. Retrieval (Sprint 2) needs to be fast and runs on
every question. Also: every record gets a stable `id` + `url` now, because that's
the only way to cite sources later — you can't retrofit citations after the fact.

**Tests:** `tests/test_ingest.py` — corpus not empty, every record has all 6
required fields, no blank text, ids are unique, both products present. This is
"testing the data contract," not just "does the code run."

**Interview answer:** "Ingestion is a separate offline step that turns raw docs
into structured records with source metadata attached. That's what lets retrieval
later cite exactly where an answer came from." For testing: "I tested the data
contract — every document has the fields retrieval depends on, and ids are unique
since those become the citation keys."

**Status:** Done. Formally verified with real pytest on the local machine (the
cloud sandbox that wrote this code couldn't install pytest due to network
restrictions) — all 5 tests pass. `data/processed/corpus.json` is generated
output from `ingest.py`, not source, so it's gitignored rather than committed —
re-run `python3 -m src.ingest` anytime to rebuild it from `data/raw/`.

## Not started yet
- Sprint 2: chunking, embeddings, semantic retrieval
- Sprint 3: source-grounded answer generation + citations
- Sprint 4-10: evaluation, BM25/hybrid search, reranking, tracing, Docker, README

## Repo status
Git initialized locally, one commit made ("Sprint 0-1: project brief, raw doc
corpus, ingestion script + tests"). No GitHub remote yet — create the repo and
push from Claude Code or your own Terminal, since that has real network access
(this cloud session's local shell doesn't).
