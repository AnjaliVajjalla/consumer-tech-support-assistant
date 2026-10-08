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
from rerank import rerank  # noqa: E402

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
    # Sprint 7 additions: harder phrasing, model-specific details, and a
    # few deliberately ambiguous cases. sony_wh1000xm5__pairing and
    # sony_wh1000xm5__pairing_troubleshooting genuinely share overlapping
    # language (both mention the 1-meter proximity requirement and the
    # "press and hold power button for 5 seconds" step), so some of these
    # are honestly hard - a real, documented limitation, not a bug.
    {"question": "How many Bluetooth devices can the Sony WH-1000XM5 remember at once?",
     "expected_doc_id": "sony_wh1000xm5__pairing"},
    {"question": "Do I need to re-pair my Sony headphones every time I turn them on?",
     "expected_doc_id": "sony_wh1000xm5__pairing"},
    {"question": "What passkey do I need if my computer asks for one while pairing Sony headphones?",
     "expected_doc_id": "sony_wh1000xm5__pairing"},
    {"question": "What happens if I leave my Sony headphones in pairing mode without connecting anything?",
     "expected_doc_id": "sony_wh1000xm5__pairing"},
    {"question": "My Sony headphones won't reconnect to a phone I've paired with before, what should I try?",
     "expected_doc_id": "sony_wh1000xm5__pairing_troubleshooting"},
    {"question": "How do I completely reset my Sony WH-1000XM5 back to factory settings?",
     "expected_doc_id": "sony_wh1000xm5__pairing_troubleshooting"},
    {"question": "If restarting my phone doesn't fix Sony pairing issues, what else can I try?",
     "expected_doc_id": "sony_wh1000xm5__pairing_troubleshooting"},
    {"question": "What Bluetooth version do the AirPods Pro 2 use?",
     "expected_doc_id": "airpods_pro2__tech_specs"},
    {"question": "Are the AirPods Pro 2 water or sweat resistant?",
     "expected_doc_id": "airpods_pro2__tech_specs"},
    {"question": "What chip is inside the AirPods Pro 2 charging case?",
     "expected_doc_id": "airpods_pro2__tech_specs"},
    {"question": "Can the AirPods Pro 2 be used for a hearing test?",
     "expected_doc_id": "airpods_pro2__tech_specs"},
    {"question": "How much does a single AirPods Pro 2 earbud weigh?",
     "expected_doc_id": "airpods_pro2__tech_specs"},
    {"question": "What are the dimensions of the AirPods Pro 2 charging case?",
     "expected_doc_id": "airpods_pro2__tech_specs"},
    {"question": "What's the very first thing to check if my AirPods won't connect to my iPhone?",
     "expected_doc_id": "airpods_pro2__connection_troubleshooting"},
    {"question": "How do I reset the AirPods Pro 2 charging case?",
     "expected_doc_id": "airpods_pro2__connection_troubleshooting"},
    {"question": "If the status light on my AirPods case is flashing white, what does that mean?",
     "expected_doc_id": "airpods_pro2__connection_troubleshooting"},
    {"question": "Do I tap or press and hold to put AirPods 4 into pairing mode?",
     "expected_doc_id": "airpods_pro2__connection_troubleshooting"},
    {"question": "How close does my phone need to be to my Sony headphones to start pairing?",
     "expected_doc_id": "sony_wh1000xm5__pairing"},
    {"question": "How long does a full Sony WH-1000XM5 charge take?", "expected_doc_id": "sony_wh1000xm5__charging"},
    {"question": "What does the orange Sony light mean when the battery is low?", "expected_doc_id": "sony_wh1000xm5__battery_status"},
    {"question": "Can I reboot my WH-1000XM5 without deleting its pairings?", "expected_doc_id": "sony_wh1000xm5__reset"},
    {"question": "Which Sony button switches between ambient sound and noise canceling?", "expected_doc_id": "sony_wh1000xm5__noise_canceling"},
    {"question": "What swipe gesture raises the volume on WH-1000XM5?", "expected_doc_id": "sony_wh1000xm5__controls"},
    {"question": "Which Bluetooth codecs does the Sony WH-1000XM5 support?", "expected_doc_id": "sony_wh1000xm5__specifications"},
    {"question": "How do I manually pair AirPods Pro 2 with a Mac?", "expected_doc_id": "airpods_pro2__pairing"},
    {"question": "Can the AirPods Pro 2 USB-C case charge on an Apple Watch charger?", "expected_doc_id": "airpods_pro2__charging"},
    {"question": "Can Find My locate the AirPods Pro 2 charging case separately?", "expected_doc_id": "airpods_pro2__find_my"},
    {"question": "What is the difference between Transparency and Adaptive Audio?", "expected_doc_id": "airpods_pro2__noise_control"},
    {"question": "How do I lower AirPods Pro 2 volume from the stem?", "expected_doc_id": "airpods_pro2__controls"},
    {"question": "How do I put Pixel Buds Pro 2 into pairing mode?", "expected_doc_id": "pixel_buds_pro2__setup"},
    {"question": "What Bluetooth version do Pixel Buds Pro 2 use?", "expected_doc_id": "pixel_buds_pro2__specifications"},
    {"question": "Are the Pixel Buds Pro 2 case and earbuds water resistant?", "expected_doc_id": "pixel_buds_pro2__specifications"},
    {"question": "What does a triple tap do on Pixel Buds Pro 2?", "expected_doc_id": "pixel_buds_pro2__controls"},
    {"question": "Can I answer a call by nodding with Pixel Buds Pro 2?", "expected_doc_id": "pixel_buds_pro2__controls"},
    {"question": "What does Adaptive mode do on Pixel Buds Pro 2?", "expected_doc_id": "pixel_buds_pro2__noise_control"},
    {"question": "How do I factory reset Pixel Buds Pro 2 for a new owner?", "expected_doc_id": "pixel_buds_pro2__reset"},
    {"question": "The Pixel Buds audio keeps cutting out. What should I try?", "expected_doc_id": "pixel_buds_pro2__audio_troubleshooting"},
    {"question": "Why is bass weak on my Pixel Buds Pro 2?", "expected_doc_id": "pixel_buds_pro2__audio_troubleshooting"},
    {"question": "How do I make Bose QuietComfort Ultra discoverable?", "expected_doc_id": "bose_qc_ultra__pairing"},
    {"question": "Why does Windows show an LE Bose device and a headphone device?", "expected_doc_id": "bose_qc_ultra__pairing"},
    {"question": "How much listening time does a 15-minute Bose charge provide?", "expected_doc_id": "bose_qc_ultra__charging"},
    {"question": "What is the difference between Bose Quiet, Aware, and Immersion modes?", "expected_doc_id": "bose_qc_ultra__modes"},
    {"question": "How do I enable Wind Block on Bose QuietComfort Ultra?", "expected_doc_id": "bose_qc_ultra__modes"},
    {"question": "My Bose headphones disconnect outside. What should I check?", "expected_doc_id": "bose_qc_ultra__connection_troubleshooting"},
    {"question": "Why does Bluetooth stop working while my Bose headphones charge?", "expected_doc_id": "bose_qc_ultra__no_audio"},
    {"question": "Can QuietComfort Ultra play audio directly over USB?", "expected_doc_id": "bose_qc_ultra__no_audio"},
]

REFUSAL_SET = [
    {"question": "How do I pair Samsung Galaxy Buds?", "expected": "unsupported_product"},
    {"question": "Will Sony replace my headphones under warranty?", "expected": "unsupported_policy"},
    {"question": "How do I solder a broken AirPods battery?", "expected": "unsupported_repair"},
    {"question": "Which headphones should I buy for under $100?", "expected": "unsupported_recommendation"},
    {"question": "Can you access my Apple account and find my AirPods?", "expected": "unsupported_account_action"},
    {"question": "Does Bose guarantee these headphones are safe for driving?", "expected": "unsupported_safety_claim"},
    {"question": "My earbuds caused ear pain. Diagnose the medical problem.", "expected": "unsupported_medical"},
    {"question": "What is the return policy at the store where I bought them?", "expected": "unsupported_policy"},
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


def hybrid_then_rerank(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    """Retrieve a wider hybrid candidate shortlist, then rerank it down to top_k."""
    candidates = hybrid_retrieve(query, chunks, top_k=10)
    return rerank(query, candidates, top_k=top_k)


METHODS = {
    "semantic": retrieve,
    "hybrid": hybrid_retrieve,
    "hybrid+rerank": hybrid_then_rerank,
}


def main() -> None:
    chunks = load_chunks_with_embeddings()
    print(f"Golden set: {len(GOLDEN_SET)} questions\n")
    print(f"{'method':<16}{'hit_rate@3':<12}{'mrr@3':<12}")
    for name, retrieve_fn in METHODS.items():
        hit_rate = hit_rate_at_k(retrieve_fn, chunks)
        mrr = mean_reciprocal_rank(retrieve_fn, chunks)
        print(f"{name:<16}{hit_rate:<12.2f}{mrr:<12.2f}")


if __name__ == "__main__":
    main()
