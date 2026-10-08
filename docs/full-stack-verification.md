# Full-stack expansion verification

Branch: `full-stack-expansion`. The changes are local; this report does not claim a deployment, push, or merged pull request.

## Scope and baseline

The original RAG baseline passed 34 unit tests and 4 live citation/refusal checks. Its 4 documents produced 9 chunks. On the original 28 questions, semantic hit/MRR was 1.0000/0.9048; hybrid and reranking both measured 1.0000/0.9643. The CLI was exercised successfully before expansion.

The expansion adds a React/TypeScript frontend, a FastAPI boundary calling the existing `answer()` function, source/latency display, controlled errors and retry, and official-documentation coverage for four products. Ingestion now validates metadata and file consistency, nonempty text/URLs, and unique IDs. The final corpus contains 26 documents and 53 chunks. All 26 source URLs returned successful responses when checked, and no identical raw text files were found.

## Final automated checks

| Check | Observed result |
| --- | --- |
| Python unit/API/ingestion tests and retrieval regression tests | 56 passed |
| Real generation evaluation, run separately | 15 passed |
| Frontend component and API-client tests | 12 passed |
| TypeScript and Vite production build | Passed |
| Frontend lint | Passed |
| Git whitespace check | Passed |

The 15 live checks comprise four supported-product citation checks, two original unsupported-product/policy checks, eight expanded refusal scenarios, and one product-clarification check. They cost real API tokens. Passing them is not a guarantee that all possible questions or paraphrases work. No tests were deleted or relaxed to obtain these results.

Two intermediate live failures helped refine the prompt: the ambiguity instruction initially asked for a model even when a supported family was named; account-action refusals sometimes appended cited procedures. The final prompt distinguishes missing product families from named families and requests a plain refusal for account/device actions.

## Browser acceptance checks

Checks used the real React UI and FastAPI backend. Provider-failure and timeout checks used a temporary local failure simulator, not a real provider outage. That simulator was stopped and the real backend restored afterward.

| Case | Observed behavior |
| --- | --- |
| Sony pairing | Cited setup steps, official Sony links, real latency/token values |
| Sony connection troubleshooting | Cited proximity, pairing-mode, old-pairing-data, and restart advice |
| Pixel Buds Bluetooth specification | Answered Bluetooth 5.4 with its official source |
| Sony reset paraphrase | Explained reset without deleting pairings, with a citation |
| Broad AirPods troubleshooting wording | Refused despite relevant material elsewhere in the corpus; recorded retrieval/answer-quality limitation |
| Exact phrase `AirPlay button Control Center` | Refused after retrieval missed the expected document; recorded failure, not counted as a correct support answer |
| Product omitted | Initial model guess exposed ambiguity; prompt revised and live clarification regression added |
| Unsupported Samsung product | Refused without sources |
| Unsupported Sony warranty policy | Refused without sources |
| Empty input | Visible validation message before any request |
| Backend unavailable | Clear network message and Retry control |
| Simulated provider connection failure | Safe server-error message and Retry control |
| Simulated request exceeding 30 seconds | Timeout message and Retry control |
| Retry after backend recovery | Returned a real response for the last submitted question |

Loading state visibly preserved the question and disabled repeat submission. Subsequent submissions cleared earlier answers. Source links and citation numbers were inspected in successful responses. No API credentials or backend stack traces appeared in the interface. Timings varied by request and include cold-start overhead; no speed guarantee is claimed.

## Retrieval evidence and tradeoffs

The [per-question report](evaluation-results.json) stores the 56-query evaluation. Semantic hit/MRR is 0.9107/0.7649; hybrid at alpha 0.95 is 0.9107/0.7708; hybrid plus reranking is 0.9286/0.7738. Reranking adds one hit and a small MRR gain, at additional latency. Alpha was selected from a 0.3 to 1.0 development-set sweep. There is no separate held-out test set.

Inspected misses include short AirPlay/status-light queries, repeated connection vocabulary, and alternate relevant documents for reset questions. Single-document labels and multiple chunks per document can penalize reasonable alternatives or crowd out coverage. The 0.15 relevance cutoff was retained after supported/off-topic spot checks; it cannot by itself detect unsupported warranties or products.

## Boundaries

- Implementation phases are complete locally, with the above retrieval-quality limitations explicitly retained.
- The original Dockerfile still runs the CLI. A Docker image rebuild and full-stack deployment were outside this verification.
- Learning quizzes and personal modification checkpoints were skipped at the owner's request. Independent explanation/mastery was not assessed, and no resume claim was updated.
- The backend is a local prototype without authentication, rate limiting, or cancellation of an already-running generation when the browser times out.
- Historical project brief and portfolio writeup describe the original version. The root README and these notes document the expansion.
