"""
Regression tests for retrieval quality against the golden set.

Why this is in evals/, not tests/: tests/test_retrieve.py already checks
"does the code run correctly" with made-up chunks. This checks "is
real-world retrieval quality still good enough," using judgment calls
about which document should answer which question, captured once in the
golden set instead of re-litigated by eye every time.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from retrieve import load_chunks_with_embeddings, retrieve  # noqa: E402
from eval_retrieval import GOLDEN_SET, hit_rate_at_k, mean_reciprocal_rank  # noqa: E402

MIN_HIT_RATE = 0.75
MIN_MRR = 0.6


def test_semantic_retrieval_hit_rate_stays_above_threshold():
    chunks = load_chunks_with_embeddings()
    rate = hit_rate_at_k(retrieve, chunks, GOLDEN_SET, k=3)
    assert rate >= MIN_HIT_RATE, f"hit_rate@3 dropped to {rate:.2f}"


def test_semantic_retrieval_mrr_stays_above_threshold():
    chunks = load_chunks_with_embeddings()
    mrr = mean_reciprocal_rank(retrieve, chunks, GOLDEN_SET, k=3)
    assert mrr >= MIN_MRR, f"mrr@3 dropped to {mrr:.2f}"
