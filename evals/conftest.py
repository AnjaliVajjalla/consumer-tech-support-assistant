"""
Ensures Langfuse traces from real API calls in this directory are
actually sent before the test process exits.

Why: Langfuse batches trace data and only sends it over the network on
flush() (or an unreliable best-effort flush at process exit). Direct
calls to answer() from evals/test_citations.py never go through
cli.py or generate.py's main(), the only two places that call
flush() today - without this, most eval traces would silently never
reach the dashboard.
"""
import pytest

from src.generate import langfuse


@pytest.fixture(scope="session", autouse=True)
def flush_langfuse_traces():
    yield
    langfuse.flush()
