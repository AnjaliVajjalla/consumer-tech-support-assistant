"""
Retrieval evaluation for the Consumer Technology Support Assistant.

What this does (Sprint 4):
  Measures retrieval quality against a small hand-labeled golden set.
  A test checks code behavior on a known input; an eval checks whether
  real output quality clears a bar, using examples a human judged correct.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from retrieve import load_chunks_with_embeddings, retrieve, hybrid_retrieve  # noqa: E402

GOLDEN_SET = [
    {"question": "How do I pair my Sony WH-1000XM5 headphones with a new Bluetooth device?",
     "expected_doc_id": "sony_wh1000xm5__pairing"},
    {"question": "My Sony headphones won't go into pairing mode, what should I check?",
     "expected_doc_id": "sony_wh1000xm5__pairing_troubleshooting"},
    {"question": "My AirPods Pro 2 won't connect to my iPhone, how do I fix it?",
     "expected_doc_id": "airpods_pro2__connection_troubleshooting"},
    {"question": "What are the technical specs of the AirPods Pro 2 with USB-C?",
     "expected_doc_id": "airpods_pro2__tech_specs"},
    {"question": "How many minutes of inactivity before Sony pairing mode cancels automatically?",
     "expected_doc_id": "sony_wh1000xm5__pairing"},
    {"question": "How do I manually put my AirPods into pairing mode?",
     "expected_doc_id": "airpods_pro2__connection_troubleshooting"},
    {"question": "What touch controls does the AirPods Pro 2 charging case support?",
     "expected_doc_id": "airpods_pro2__tech_specs"},
    {"question": "What is the first troubleshooting step if Sony headphones fail to pair?",
     "expected_doc_id": "sony_wh1000xm5__pairing_troubleshooting"},
    # Keyword-heavy cases (Sprint 4): phrased the way a user reading exact
    # on-screen text would type it. Plain semantic search ranks the correct
    # doc 2nd-3rd here instead of 1st, since "AirPlay"/"status light" are
    # short, generic-sounding tokens; BM25's exact term match fixes it.
    {"question": "AirPlay button Control Center",
     "expected_doc_id": "airpods_pro2__connection_troubleshooting"},
    {"question": "status light flashes white",
     "expected_doc_id": "airpods_pro2__connection_troubleshooting"},
]


def hit_rate_at_k(retrieve_fn, chunks, golden_set=GOLDEN_SET, k=3) -> float:
    """Fraction of questions where the correct document appears in the top k results."""
    hits = 0
    for case in golden_set:
        results = retrieve_fn(case["question"], chunks, top_k=k)
        if any(r["doc_id"] == case["expected_doc_id"] for r in results):
            hits += 1
    return hits / len(golden_set)


def mean_reciprocal_rank(retrieve_fn, chunks, golden_set=GOLDEN_SET, k=3) -> float:
    """Average of 1/rank of the first correct document, 0 if it's not in the top k."""
    reciprocal_ranks = []
    for case in golden_set:
        results = retrieve_fn(case["question"], chunks, top_k=k)
        rank = next(
            (i for i, r in enumerate(results, start=1) if r["doc_id"] == case["expected_doc_id"]),
            None,
        )
        reciprocal_ranks.append(1 / rank if rank else 0.0)
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


METHODS = {
    "semantic": retrieve,
    "hybrid": hybrid_retrieve,
}


def main() -> None:
    chunks = load_chunks_with_embeddings()
    print(f"Golden set: {len(GOLDEN_SET)} questions\n")
    print(f"{'method':<12}{'hit_rate@3':<12}{'mrr@3':<12}")
    for name, retrieve_fn in METHODS.items():
        hit_rate = hit_rate_at_k(retrieve_fn, chunks)
        mrr = mean_reciprocal_rank(retrieve_fn, chunks)
        print(f"{name:<12}{hit_rate:<12.2f}{mrr:<12.2f}")


if __name__ == "__main__":
    main()
