# Consumer Technology Support Assistant — Project Brief

## Why
Practical experience with retrieval-augmented generation (RAG): document ingestion, chunking, embeddings, semantic search, source-grounded answers, evaluation, testing, and observability. Supports entry-level AI analyst / AI solutions / AI operations job targets.

## Product idea
An assistant that answers setup, troubleshooting, compatibility, and spec questions about a small set of wireless headphones/earbuds, grounded in official manuals and support pages, with citations.

## Sprint 0 decisions

**Device scope (2 products):**
- Sony WH-1000XM5 (over-ear headphones)
- Apple AirPods Pro 2, USB-C (earbuds)

**Sources (official only):**
- Sony Help Guide (helpguide.sony.net) — pairing, troubleshooting
- Apple Support (support.apple.com) — tech specs, connection troubleshooting

4 documents ingested so far, stored in `data/raw/<product>/` with a `_meta.json` sidecar per product recording title, source URL, and category (setup / troubleshooting / specs) for citation traceability.

**Boundaries:**
- Answers only from the ingested document collection — no invented specs or compatibility claims
- No warranty decisions, no repair instructions not present in sources, no account/purchase actions
- When the docs don't support an answer, say so and point to official support

**Success criteria (core version):**
- Ingestion produces a structured, traceable corpus (done — see `data/raw/`)
- Chunking + embeddings + semantic search retrieve relevant passages
- Answers cite the specific source document/URL they're grounded in
- Pytest coverage for retrieval and answer-grounding logic

## Status
- Sprint 0: done (this doc)
- Sprint 1: in progress — corpus ingested, ingestion script next
- Sprint 2+: not started
