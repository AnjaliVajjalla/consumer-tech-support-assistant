"""FastAPI entry point for the Consumer Technology Support Assistant."""

import logging
import time
from typing import Any

from anthropic import APIConnectionError, APIStatusError, APITimeoutError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.errors import (
    CONFIGURATION_ERROR,
    CORPUS_UNAVAILABLE,
    TIMEOUT_ERROR,
    UPSTREAM_ERROR,
)
from api.models import AskRequest, AskResponse, Latency, Source, TokenUsage


app = FastAPI(title="Consumer Technology Support Assistant API")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def run_answer(question: str) -> dict[str, Any]:
    """Import lazily so the health endpoint remains independent of the RAG stack."""
    from src.generate import answer

    return answer(question)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Confirm the API process is available without loading the RAG pipeline."""
    return {"status": "ok"}


@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """Validate one question and return the existing RAG pipeline's result."""
    started = time.perf_counter()
    try:
        result = run_answer(request.question)
    except FileNotFoundError:
        logger.exception("Processed corpus files are missing")
        raise HTTPException(status_code=503, detail=CORPUS_UNAVAILABLE) from None
    except KeyError as exc:
        if exc.args == ("ANTHROPIC_API_KEY",):
            logger.exception("ANTHROPIC_API_KEY is missing")
            raise HTTPException(status_code=503, detail=CONFIGURATION_ERROR) from None
        logger.exception("Unexpected missing key while answering")
        raise HTTPException(status_code=500, detail=UPSTREAM_ERROR) from None
    except APITimeoutError:
        logger.exception("Anthropic request timed out")
        raise HTTPException(status_code=504, detail=TIMEOUT_ERROR) from None
    except (APIConnectionError, APIStatusError):
        logger.exception("Anthropic request failed")
        raise HTTPException(status_code=502, detail=UPSTREAM_ERROR) from None
    except Exception:
        logger.exception("Unexpected error while answering")
        raise HTTPException(status_code=500, detail=UPSTREAM_ERROR) from None

    trace = result["trace"]
    sources = [
        Source(
            number=source["n"],
            product=source["product"],
            title=source["title"],
            url=source["url"],
        )
        for source in result["sources"]
    ]
    return AskResponse(
        answer=result["answer"],
        sources=sources,
        latency=Latency(
            retrieve_ms=trace["retrieve_ms"],
            rerank_ms=trace["rerank_ms"],
            generate_ms=trace["generate_ms"],
            total_ms=round((time.perf_counter() - started) * 1000, 1),
        ),
        usage=TokenUsage(**result["usage"]),
    )
