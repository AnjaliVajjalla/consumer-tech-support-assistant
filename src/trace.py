"""
Pipeline tracing for the Consumer Technology Support Assistant.

What this does (Sprint 4):
  Times each stage of answer() (retrieve, rerank, generate) so latency
  is visible per question instead of just "the answer came back
  eventually." This is the "observability" goal named in
  PROJECT_BRIEF.md, extending the token-usage tracking from Sprint 3.
"""
import json
import time
from contextlib import contextmanager
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRACES_PATH = PROJECT_ROOT / "data" / "traces" / "traces.jsonl"


@contextmanager
def time_stage(trace: dict, stage: str):
    """Record how long a `with` block took, in milliseconds, as trace[f"{stage}_ms"]."""
    start = time.perf_counter()
    yield
    trace[f"{stage}_ms"] = round((time.perf_counter() - start) * 1000, 1)


def save_trace(trace: dict) -> None:
    """Append one trace record as a line of JSON, for later inspection."""
    TRACES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(trace) + "\n")
