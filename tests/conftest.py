"""
Disables Langfuse tracing for unit tests in this directory.

Why: tests/ mocks the Anthropic client so no real API calls happen, but
without this, importing src.generate still creates a real Langfuse
client and sends real trace data for mocked calls (e.g. the literal
"How do I pair?" / "Press the power button." test fixtures would show
up as real traces). evals/ intentionally keeps tracing enabled, since
its real API calls should produce real traces, same as they cost real
tokens.
"""
import os

os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
