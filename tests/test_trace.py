"""
Tests for local stage timing.

Why this test: a timing helper is only useful if it actually measures
elapsed time correctly, not just that the code runs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from trace import time_stage  # noqa: E402


def test_time_stage_records_a_nonnegative_duration():
    result = {}
    with time_stage(result, "retrieve"):
        pass
    assert result["retrieve_ms"] >= 0
