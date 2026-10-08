"""Unit tests for the browser-facing FastAPI contract."""

from unittest.mock import Mock

from fastapi.testclient import TestClient

from api.errors import (
    CONFIGURATION_ERROR,
    CORPUS_UNAVAILABLE,
    TIMEOUT_ERROR,
    UPSTREAM_ERROR,
)
from api.main import app


client = TestClient(app, raise_server_exceptions=False)


def rag_result(*, sources: list[dict] | None = None) -> dict:
    return {
        "answer": "Hold the power button for five seconds [1].",
        "sources": sources
        if sources is not None
        else [
            {
                "n": 1,
                "product": "Sony WH-1000XM5",
                "title": "Pairing",
                "url": "https://helpguide.sony.net/example",
            }
        ],
        "usage": {"input_tokens": 100, "output_tokens": 25},
        "trace": {"retrieve_ms": 10.0, "rerank_ms": 20.0, "generate_ms": 30.0},
    }


def test_ask_returns_structured_answer(monkeypatch) -> None:
    mocked = Mock(return_value=rag_result())
    monkeypatch.setattr("api.main.run_answer", mocked)

    response = client.post("/api/ask", json={"question": "  How do I pair them?  "})

    assert response.status_code == 200
    body = response.json()
    mocked.assert_called_once_with("How do I pair them?")
    assert body["sources"][0] == {
        "number": 1,
        "product": "Sony WH-1000XM5",
        "title": "Pairing",
        "url": "https://helpguide.sony.net/example",
    }
    assert body["latency"]["retrieve_ms"] == 10.0
    assert body["latency"]["rerank_ms"] == 20.0
    assert body["latency"]["generate_ms"] == 30.0
    assert body["latency"]["total_ms"] >= 0
    assert body["usage"] == {"input_tokens": 100, "output_tokens": 25}


def test_empty_question_is_rejected() -> None:
    assert client.post("/api/ask", json={"question": ""}).status_code == 422


def test_whitespace_question_is_rejected() -> None:
    assert client.post("/api/ask", json={"question": "   "}).status_code == 422


def test_overlong_question_is_rejected() -> None:
    assert client.post("/api/ask", json={"question": "x" * 1001}).status_code == 422


def test_unsupported_answer_has_no_sources(monkeypatch) -> None:
    result = rag_result(sources=[])
    result["answer"] = "I don't have that information in these sources."
    result["usage"] = {"input_tokens": 0, "output_tokens": 0}
    monkeypatch.setattr("api.main.run_answer", Mock(return_value=result))

    response = client.post("/api/ask", json={"question": "What about Bose?"})

    assert response.status_code == 200
    assert response.json()["sources"] == []


def test_internal_error_returns_safe_message(monkeypatch) -> None:
    monkeypatch.setattr("api.main.run_answer", Mock(side_effect=RuntimeError("secret path")))

    response = client.post("/api/ask", json={"question": "How do I pair them?"})

    assert response.status_code == 500
    assert response.json() == {"detail": UPSTREAM_ERROR}
    assert "secret path" not in response.text


def test_missing_corpus_returns_safe_service_error(monkeypatch) -> None:
    monkeypatch.setattr("api.main.run_answer", Mock(side_effect=FileNotFoundError("private path")))

    response = client.post("/api/ask", json={"question": "How do I pair them?"})

    assert response.status_code == 503
    assert response.json() == {"detail": CORPUS_UNAVAILABLE}
    assert "private path" not in response.text


def test_missing_api_key_returns_safe_configuration_error(monkeypatch) -> None:
    monkeypatch.setattr("api.main.run_answer", Mock(side_effect=KeyError("ANTHROPIC_API_KEY")))

    response = client.post("/api/ask", json={"question": "How do I pair them?"})

    assert response.status_code == 503
    assert response.json() == {"detail": CONFIGURATION_ERROR}


def test_upstream_timeout_returns_retryable_error(monkeypatch) -> None:
    class SimulatedTimeout(Exception):
        pass

    monkeypatch.setattr("api.main.APITimeoutError", SimulatedTimeout)
    monkeypatch.setattr("api.main.run_answer", Mock(side_effect=SimulatedTimeout("timed out")))

    response = client.post("/api/ask", json={"question": "How do I pair them?"})

    assert response.status_code == 504
    assert response.json() == {"detail": TIMEOUT_ERROR}
    assert "timed out" not in response.text


def test_cors_allows_only_local_frontend() -> None:
    allowed = client.options(
        "/api/ask",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    blocked = client.options(
        "/api/ask",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in blocked.headers
