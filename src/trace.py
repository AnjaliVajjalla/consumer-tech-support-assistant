"""
Local stage timing for the Consumer Technology Support Assistant.

What this does (Sprint 4, refined Sprint 8):
  Times each stage of answer() (retrieve, rerank, generate) so latency
  is printed per question in the CLI immediately. Persisted, queryable
  tracing (full input/output, cost, history across questions) is handled
  by Langfuse (see generate.py) rather than a local log file - this
  module now only covers the immediate-feedback half of observability.
"""
import time
from contextlib import contextmanager


@contextmanager
def time_stage(trace: dict, stage: str):
    """Record how long a `with` block took, in milliseconds, as trace[f"{stage}_ms"]."""
    start = time.perf_counter()
    yield
    trace[f"{stage}_ms"] = round((time.perf_counter() - start) * 1000, 1)
