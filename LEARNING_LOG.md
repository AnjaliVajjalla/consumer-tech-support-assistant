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

**Status:** Done. 7/7 tests pass. Merged into `main` via PR #11
(squash-merged as commit `a6e09dd`).

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

## Sprint 2 — Semantic retrieval (done, tested, reviewed)
**What it is:** `src/retrieve.py` completes the RAG pipeline. It joins
`chunks.json` (text + metadata) and `embeddings.json` (vectors) back
together by `chunk_id` (`load_chunks_with_embeddings`), then `retrieve()`
embeds a question with the same model used on the chunks, scores every
chunk by cosine similarity to that question, sorts best-first, and
returns the top `top_k` matches.

**Lesson:** Retrieval is the step that makes semantic search real: a
question and a chunk both become vectors, and "most relevant" just means
"highest cosine similarity." Everything built in Sprints 1-2 (ingest ->
chunk -> embed) exists to feed this one comparison.

**Tests:** `tests/test_retrieve.py` (2 tests) — given a pairing chunk, a
battery chunk, and a returns chunk, a pairing-style question retrieves
the pairing chunk first (proves the ranking is actually correct, not
just that the code runs), and `top_k` is respected. Also ran
`python3 -m src.retrieve` end-to-end on the real corpus: asking "How do
I pair my headphones?" correctly ranked the Sony pairing document (score
0.534) above AirPods connection-troubleshooting content (0.458).

**Interview answer:** "Retrieval turns a user's question into the same
kind of vector used for the document chunks, then ranks every chunk by
cosine similarity to find the closest matches. I verified it end-to-end
with a real question and confirmed the correct document actually came
back ranked first, not just that the script ran without errors."

**Status:** Done. 18/18 tests pass across the whole project. Sprint 2 is
now fully code-complete: ingest -> chunk -> embed -> retrieve, each step
tested. Merged into `main` via PR #13.

## Sprint 3 — Source-grounded answers with citations (done, tested, reviewed)
**What it is:** `src/generate.py` completes the RAG pipeline. `build_context`
numbers retrieved chunks (`[1]`, `[2]`...) for the prompt. `generate_answer`
sends those numbered sources + the question to Claude (via the Anthropic
API), with a system prompt that forces it to answer only from the given
sources, cite them inline, and say so plainly when the sources don't cover
something. `answer(question)` chains the whole pipeline in one call:
retrieve (Sprint 2) -> generate (Sprint 3). `src/cli.py` adds an interactive
terminal loop to ask arbitrary questions.

**Lesson: local vs. API, and why RAG's "G" needs a real LLM.** Sprints 1-2
(ingest, chunk, embed, retrieve) all run locally and are free, a small
model turns text into vectors for comparison. Sprint 3 is different:
turning a question + passages into a coherent, correctly-cited written
answer needs a real large language model, too big to run on a laptop, so
that one step calls Anthropic's API over the network and costs a small
amount per call. Retrieval finds the facts; generation is what makes it
"retrieval-*augmented generation*."

**Lesson: citations are built in code, not written by the model.** The
model only ever sees/cites `[1]`, `[2]`, `[3]` in the prompt, it never
writes out a URL itself. The `sources` list mapping numbers to real
titles/URLs is built by our own code from the same trusted chunk data.
That means a citation can be "pointing at the wrong source" (a retrieval
or model error) but never a fabricated URL.

**Bug found and fixed via live testing, not code review:** an early
version returned every retrieved chunk as "sources," even when the model
cited none of them (e.g. asking an off-topic question like "what's the
capital of France?" still showed 3 headphone sources under a "sources
cited" list, despite the answer correctly saying it couldn't help). Fixed
by scanning the model's own answer text for `[n]` markers and filtering
`sources` down to only what was actually cited. Caught by manually testing
edge cases in the live CLI, not by a pre-written test, then confirmed with
a new test (`test_generate_answer_returns_no_sources_when_none_are_cited`).

**Extension: a relevance threshold, not just the prompt, blocks off-topic
questions.** Before this, `retrieve()` always returned its top 3 chunks no
matter how irrelevant the question was, "what's the capital of France?"
still got 3 headphone chunks handed to the model, and only the system
prompt's instructions kept it from making something up. Checked real
cosine similarity scores across several questions: on-topic ones scored
0.42-0.67, totally unrelated ones scored ~0.04 or below, wrong-product-but-
still-headphones ones (like Bose) stayed around 0.42. `MIN_RELEVANCE_SCORE
= 0.15` in `generate.py` sits in that gap, so a genuinely unrelated
question now short-circuits before any API call is made (free, instant),
while a wrong-product question still reaches the model, which correctly
says it doesn't cover that product. This is defense in depth: retrieval
filters obvious nonsense, the prompt handles subtler judgment calls.

**Tests:** `tests/test_generate.py` (7 tests, mocked API, no cost) — chunk
numbering, empty-input edge case, sources correctly match what's cited,
the real question/context gets sent to the API, citing nothing returns no
sources, a low-relevance question skips the API entirely, and a relevant
one still reaches it. `evals/test_citations.py` (2 tests, real API calls,
kept separate from `tests/` since it costs money and tests actual model
behavior, not just our code) — checks the model's own `[n]` citations in
a generated answer point to the correct product, not just that the right
chunk was retrieved nearby.

**Manually verified live, beyond the automated tests:** correct grounded
pairing steps with citations; correctly declined to answer about a
product not in the corpus (Bose); correctly refused to invent a warranty
policy (boundary from `PROJECT_BRIEF.md`); correctly admitted a source
mentions a Sony reset exists but doesn't include the steps, rather than
guessing them.

**Interview answer:** "I built the generation step of a RAG pipeline:
retrieved passages get numbered and passed to Claude with a system prompt
that restricts it to only those sources and requires inline citations.
The citation mapping to real URLs is built in my own code, not by the
model, so URLs can't be hallucinated. While testing it live I found a real
bug, the code was reporting sources the model never actually used, fixed
it by checking which citation markers actually appear in the generated
text, and added a test for that exact case."

**Status:** Done. 25/25 mocked tests pass, 2/2 real citation evals pass.
Built on branch `sprint-3-source-grounded-answers`, committed and pushed,
open as PR #14, not yet merged.

## Not started yet
- Sprint 4-10: evaluation, BM25/hybrid search, reranking, tracing, Docker, README

## Repo status
GitHub remote is set up (`AnjaliVajjalla/consumer-tech-support-assistant`,
private). Workflow per sprint: branch off `main`, build + test locally,
commit, push, open a PR, merge only after explicit confirmation, then pull
`main` locally. Sprint 2's chunking work followed this via PR #11. Sprint 3
followed the same pattern on branch `sprint-3-source-grounded-answers`.
