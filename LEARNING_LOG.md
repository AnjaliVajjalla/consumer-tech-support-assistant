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

## Sprint 2 — Chunking (done, tested, reviewed)
**What it is:** `src/chunk.py` splits each ingested document into ~100-word
chunks with 20-word overlap (`chunk_text`), then attaches the parent
document's metadata (product, title, url, category) to every chunk
(`chunk_corpus`). Output: `data/processed/chunks.json`.

**Lesson:** Semantic search retrieves chunks, not whole documents, so every
chunk needs its own stable `chunk_id` plus a trace back to its source
document (`doc_id`) to keep citations correct. Overlap between chunks
matters because it stops an answer's key sentence from being split across
two chunks with neither one containing the full thought.

**Tests:** `tests/test_chunk.py` (7 tests) — chunks get produced, every
chunk has all 7 required fields, no blank text, unique chunk ids, every
chunk traces back to a real document, short text stays one chunk, long
text splits into overlapping chunks (verified the actual 20-word overlap).

**Interview answer:** "I split documents into overlapping word-based
chunks so retrieval works on passages small enough to be relevant, while
each chunk still carries its source document's metadata for citations."

**Status:** Done. 7/7 tests pass.

## Sprint 2 — Embeddings (done, tested, reviewed)
**What it is:** `src/embed.py` turns text into vectors using
`sentence-transformers` (`all-MiniLM-L6-v2`, a small free local model, no
API key needed). `embed_texts()` embeds a list of strings.
`embed_chunks()` embeds every chunk from `chunks.json` and returns
`{chunk_id, embedding}` records, keeping the link back to the full chunk
(text + metadata) by id instead of duplicating it. `main()` writes the
results to `data/processed/embeddings.json`.

**Lesson:** An embedding is text turned into a list of numbers such that
similar meaning ends up numerically close. That's the mechanism behind
semantic search: compare a question's vector to every chunk's vector
instead of matching exact keywords. Keeping embeddings in a separate file
from chunk text (linked by `chunk_id`) means the embedding model can be
swapped later without touching the chunk data.

**Tests:** `tests/test_embed.py` (4 tests) — one vector per input text,
all vectors the same length, semantically similar sentences produce
vectors with higher cosine similarity than unrelated ones (the real proof
the model captures meaning, not just word overlap), and `embed_chunks`
preserves one embedding per chunk with the matching `chunk_id`. Also ran
`python3 -m src.chunk` then `python3 -m src.embed` end-to-end on the real
corpus: 9 chunks -> 9 embeddings, 384 numbers each.

**Interview answer:** "I used a small local embedding model to turn each
chunk into a vector, so a user's question can later be compared by
meaning against every chunk instead of relying on exact keyword matches.
I tested it by confirming semantically similar sentences actually end up
closer together than unrelated ones, not just that the code runs."

**Status:** Done. 16/16 tests pass across the whole project.

## Not started yet
- Sprint 2: semantic retrieval (`src/retrieve.py`, not built yet)
- Sprint 3: source-grounded answer generation + citations
- Sprint 4-10: evaluation, BM25/hybrid search, reranking, tracing, Docker, README

## Repo status
Git initialized locally, one commit made ("Sprint 0-1: project brief, raw doc
corpus, ingestion script + tests"). No GitHub remote yet — create the repo and
push from Claude Code or your own Terminal, since that has real network access
(this cloud session's local shell doesn't).
