"""
Tests for pipeline tracing.

Why this test: a trace is only useful if timing is actually captured
and writes don't crash the pipeline, not just that the code runs.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import trace  # noqa: E402
from trace import time_stage, save_trace  # noqa: E402


def test_time_stage_records_a_nonnegative_duration():
    result = {}
    with time_stage(result, "retrieve"):
        pass
    assert result["retrieve_ms"] >= 0


def test_save_trace_appends_json_lines(tmp_path, monkeypatch):
    monkeypatch.setattr(trace, "TRACES_PATH", tmp_path / "traces.jsonl")

    save_trace({"question": "test1"})
    save_trace({"question": "test2"})

    lines = trace.TRACES_PATH.read_text().strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["question"] == "test1"
