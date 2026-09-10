# Consumer Technology Support Assistant

A retrieval-augmented generation (RAG) assistant that answers setup,
troubleshooting, and spec questions about two wireless headphone products,
grounded in official manuals and support pages, with citations.

## Why this project exists

Built for hands-on practice with the full RAG pipeline: document ingestion,
chunking, embeddings, semantic + keyword search, reranking, source-grounded
generation, evaluation, testing, and observability. See `PROJECT_BRIEF.md`
for the original scope and boundaries.

## Products covered

- Sony WH-1000XM5 (over-ear headphones)
- Apple AirPods Pro 2, USB-C (earbuds)

Sourced only from official documentation (Sony Help Guide, Apple Support).
The assistant never invents specs, warranty policy, or repair steps not
present in its sources — when its sources don't cover something, it says so.

## Architecture

```
data/raw/*.txt  →  ingest.py  →  corpus.json
                →  chunk.py   →  chunks.json
                →  embed.py   →  embeddings.json
                                      │
question ──────────────────────────► │
                                      ▼
                    hybrid_retrieve() (retrieve.py)
                    semantic (embeddings) + BM25 (keyword) blend
                                      │
                                      ▼
                         rerank() (cross-encoder)
                                      │
                                      ▼
                    generate_answer() (Claude API, cited)
                                      │
                                      ▼
                          answer + sources + trace
```

Each stage is its own module in `src/`, independently tested in `tests/`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-...
```

## Running the pipeline

```bash
python -m src.ingest   # data/raw/ -> data/processed/corpus.json
python -m src.chunk    # -> data/processed/chunks.json
python -m src.embed    # -> data/processed/embeddings.json
```
(`data/processed/` is gitignored — generated output, rebuild anytime from `data/raw/`.)

## Asking questions

```bash
python -m src.cli
```
Prints a grounded, cited answer, plus token usage and per-stage latency
(retrieve/rerank/generate) for every question. Traces append to
`data/traces/traces.jsonl` (gitignored).

## Testing vs. evaluation

- `pytest tests/` — unit tests (35 tests, free, no API calls). Checks the
  *code* behaves correctly: does chunking overlap correctly, does BM25 rank
  an exact keyword match first, does the citation filter drop uncited
  sources.
- `pytest evals/` — quality evaluation against hand-labeled golden sets (6
  tests: 2 free retrieval-quality regression checks, 4 real-API citation
  checks that cost a small amount). Checks the *system* behaves well: does
  retrieval find the right document, does generation cite the right
  product, does it correctly refuse off-topic/warranty questions.
- `python -m evals.eval_retrieval` — prints a full retrieval-quality report
  comparing methods (see results below).

## Evaluation results

Retrieval quality on a 28-question hand-labeled golden set (`evals/eval_retrieval.py`),
measuring hit_rate@3 (is the right document in the top 3?) and mrr@3
(is it ranked near the top, not just present?):

| method | hit_rate@3 | mrr@3 |
|---|---|---|
| semantic (embeddings only) | 1.00 | 0.9048 |
| + BM25 hybrid search (alpha=0.6) | 1.00 | 0.9643 |
| + cross-encoder reranking | 1.00 | 0.9643 |

Hit-rate looks identical across all three because the corpus is small
enough that the correct document nearly always lands somewhere in the top
3 regardless of method. MRR is what reveals the real story: hybrid search
measurably improves *where* the correct answer ranks, most visibly on
keyword-heavy queries (e.g. "AirPlay button Control Center") that plain
semantic search ranks 2nd–3rd instead of 1st.

`alpha` (the semantic/BM25 blend weight) was tuned from 0.5 to 0.6 after
expanding the golden set from 10 to 28 questions surfaced real ranking
misses (Sprint 7) — mostly between the two Sony documents (`pairing` vs.
`pairing_troubleshooting`), which genuinely share overlapping language
(both mention the 1-meter proximity requirement and the "press and hold
power button for 5 seconds" step almost verbatim). Lower alpha (more BM25
weight) made this worse, since BM25 gets more confused by shared
vocabulary than embeddings do.

Honest note: with only 9 chunks total and a candidate shortlist of 10,
reranking always sees the entire corpus regardless of hybrid's ordering,
so once alpha was tuned well, reranking's ranking is identical to
hybrid's alone on this golden set (both 0.9643) — its marginal benefit
here is currently zero. It measurably helped *before* alpha was tuned
(0.9286 → 0.9643 with the untuned alpha=0.5), so it's not dead weight,
but on a corpus this small and homogeneous, a well-tuned hybrid blend can
already reach reranking's ceiling on its own. A larger, more diverse
corpus would likely show reranking pulling ahead of hybrid again.

Generation quality (`evals/test_citations.py`, real API calls): answers
correctly cite the right product for on-topic questions, and correctly
cite nothing (refuse) for a product not in the corpus (Bose) and for a
warranty question no source covers.

## Docker

```bash
docker build -t consumer-tech-support-assistant .
docker run --env-file .env -it consumer-tech-support-assistant
```
The image builds the corpus (ingest → chunk → embed) at build time, so it
starts ready to answer questions. The API key is injected at `docker run`
time from your `.env` file — never baked into the image. Image size: 2.1GB
(uses CPU-only PyTorch; the default GPU build would add ~7.7GB of unused
CUDA libraries).

## Known limitations

- Corpus is intentionally tiny (4 documents, 9 chunks) — a portfolio-scale
  demonstration of the pipeline, not a production-scale search index.
- `retrieve()` and `rerank()` reload their models on every call rather than
  caching them across questions in a single session, so most of the
  latency shown in `cli.py` is model-loading overhead, not the actual
  retrieval/ranking computation.
- No account/purchase actions, no warranty decisions, no repair guidance
  beyond what official sources describe (see `PROJECT_BRIEF.md`).

## Tech stack

Python, `sentence-transformers` (embeddings + cross-encoder reranking,
local, free), `rank-bm25` (keyword search), Anthropic API (Claude, for
generation only), `pytest`, Docker.
