# Consumer Technology Support Assistant — Project Write-Up

A case study, for anyone evaluating this as a portfolio project rather
than reading the code directly. For setup/usage, see `README.md`.

## The problem

Support documentation for consumer electronics is scattered across long
manuals and support pages. I wanted hands-on practice with the technique
most production AI support tools actually use to solve this — retrieval-
augmented generation (RAG) — and to build every stage of it myself,
end to end, rather than calling one API and stopping there.

## What I built

An assistant that answers setup, troubleshooting, and spec questions
about two real products (Sony WH-1000XM5, AirPods Pro 2 USB-C), grounded
only in their official documentation, with inline citations back to the
exact source. If a question falls outside what the sources cover — a
warranty question, or a different brand entirely — it says so instead of
guessing.

Under the hood: documents are split into overlapping chunks, turned into
vectors (embeddings), and searched two ways at once — by meaning
(semantic search) and by exact keyword overlap (BM25) — then the top
candidates are re-ranked by a second, more precise model before being
handed to Claude to write a cited answer. Every stage is independently
tested, and retrieval quality is measured against a hand-labeled set of
real questions, not just eyeballed.

## Decisions I'd defend in an interview

**Why hybrid search instead of just embeddings.** Embeddings are great at
matching meaning but can underweight short, literal terms — a user
reading exact on-screen text ("AirPlay button, Control Center") types
something closer to a keyword search than a natural-language question.
I found two real cases in my own small corpus where pure semantic search
ranked the correct document 2nd or 3rd instead of 1st for exactly this
reason. Adding BM25 keyword search alongside embeddings, blended by a
tunable weight, fixed both.

**Why I measure hit-rate *and* mean reciprocal rank, not just one.**
Hit-rate answers "is the right document somewhere in the top 3?" — a
forgiving question. Mean reciprocal rank (MRR) answers "how close to #1
is it?" On this project, two methods tied on hit-rate while one
consistently ranked the right answer first and the other third — a real
quality difference hit-rate alone would have hidden.

**Why the eval set grew from 10 to 28 questions.** My first golden set
scored a perfect 1.00 on every metric, which meant it had nothing left to
show. I deliberately added harder, more ambiguous questions — and they
surfaced a genuine weakness: two of my four source documents share
overlapping language, which confused retrieval on a handful of
questions. I diagnosed it, tested a fix (retuning a retrieval weight)
against real data rather than guessing, and it worked — measurably.

**Why I reported a finding I didn't like.** After that fix, my reranking
step — a whole extra model, more latency, more complexity — stopped
adding any measurable benefit on this evaluation set. I could have left
that quietly out of the write-up. Instead: the honest reason is that my
corpus is small enough (9 chunks) that a well-tuned simpler method
already reaches the same ceiling reranking used to raise. That's a
real, defensible engineering judgment, not a failure to hide.

## Two real bugs I found by testing, not by reading code

1. **A relevance filter that would have silently broken.** One of my
   retrieval scores is normalized relative to each individual question,
   which means it always looks "confident" even for a totally unrelated
   question. Reusing that score to decide whether a question was
   off-topic would have quietly broken my system's ability to correctly
   refuse a warranty question or a competitor's product — a real safety
   behavior I'd already built and tested in an earlier stage. I caught
   it while integrating a new feature, before it ever shipped.
2. **A 9.82GB Docker image for a project with a 9-chunk corpus.** My
   embedding library defaulted to installing full GPU support even though
   the container never touches a GPU. Installing the CPU-only build
   instead cut the image size by almost 80%, to 2.1GB — the kind of
   easy-to-miss inefficiency that's genuinely worth knowing to check for.

## Results

Retrieval quality (28-question hand-labeled golden set):

| method | hit_rate@3 | mrr@3 |
|---|---|---|
| semantic search only | 1.00 | 0.9048 |
| + BM25 hybrid search | 1.00 | 0.9643 |
| + cross-encoder reranking | 1.00 | 0.9643 |

Generation quality (real API calls, no mocking): correctly cites the
right product for on-topic questions; correctly declines and cites
nothing for a product outside the corpus and for a warranty question no
source covers.

Docker image size: 9.82GB → 2.1GB after fixing an unnecessary GPU
dependency.

## What I'd do next

- Swap the hand-built latency/token logging for a real observability
  tool (Langfuse), so traces are queryable rather than a flat log file.
- Grow the source corpus meaningfully — the current 4-document corpus is
  intentionally small for a portfolio project, but a bigger, more varied
  corpus would be a fairer test of hybrid search and reranking, and would
  very likely show reranking earning its cost back.

## Stack

Python, `sentence-transformers` (embeddings + cross-encoder reranking),
`rank-bm25` (keyword search), the Anthropic API (Claude, for answer
generation only), `pytest`, Docker.

Full source, tests, and commit history: see the repository this file
lives in.
