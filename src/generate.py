"""
Answer generation for the Consumer Technology Support Assistant.

What this does (Sprint 3):
  Turns retrieved chunks + a user's question into a source-grounded
  answer by calling the Claude API, constrained to only use the
  provided chunks.
"""

import os
import re
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from retrieve import load_chunks_with_embeddings, hybrid_retrieve  # noqa: E402
from rerank import rerank  # noqa: E402
from trace import time_stage  # noqa: E402

MODEL_NAME = "claude-haiku-4-5-20251001"

# Below this cosine similarity, a question is treated as unrelated to the
# corpus (e.g. "what's the capital of France?") rather than sent to the
# API. Picked from real scores: on-topic questions scored 0.42-0.67,
# unrelated ones scored ~0.04 or below, so 0.15 sits safely in the gap.
MIN_RELEVANCE_SCORE = 0.15

NO_RELEVANT_INFO_ANSWER = (
    "I don't have any information relevant to that question in these "
    "sources. Please check official support instead."
)

ZERO_USAGE = {"input_tokens": 0, "output_tokens": 0}

_client = None


def get_client() -> Anthropic:
    """Create the Anthropic client once and reuse it."""
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def build_context(chunks: list[dict]) -> str:
    """Number each chunk as a labeled source block for the prompt."""
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        blocks.append(f"[{i}] {chunk['product']} — {chunk['title']}\n{chunk['text']}")
    return "\n\n".join(blocks)


SYSTEM_PROMPT = (
    "You are a support assistant for wireless headphones. Answer the "
    "user's question using ONLY the numbered sources below. Cite the "
    "source number(s) you used in brackets, like [1], right after each "
    "claim. If the sources don't contain the answer, say so plainly and "
    "recommend checking official support instead of guessing. Write in "
    "plain text: short paragraphs or a simple numbered list are fine, "
    "but don't use markdown headers or bold text."
)


def generate_answer(question: str, chunks: list[dict]) -> dict:
    """Generate a source-grounded answer with citations for a question."""
    context = build_context(chunks)
    client = get_client()

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Sources:\n{context}\n\nQuestion: {question}"}
        ],
    )

    answer_text = response.content[0].text
    cited_numbers = {int(n) for n in re.findall(r"\[(\d+)\]", answer_text)}

    all_sources = [
        {"n": i, "product": c["product"], "title": c["title"], "url": c["url"]}
        for i, c in enumerate(chunks, start=1)
    ]
    sources = [s for s in all_sources if s["n"] in cited_numbers]

    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return {"answer": answer_text, "sources": sources, "usage": usage}


def answer(question: str, top_k: int = 3, candidate_k: int = 10) -> dict:
    """Answer a question end-to-end: hybrid-retrieve a candidate shortlist,
    drop individually irrelevant ones, rerank with a cross-encoder, then
    generate a grounded, cited answer. Returns a trace of stage timing
    and usage alongside the result."""
    trace = {"question": question, "model": MODEL_NAME}
    chunks = load_chunks_with_embeddings()

    with time_stage(trace, "retrieve"):
        candidates = hybrid_retrieve(question, chunks, top_k=candidate_k)

    relevant_candidates = [c for c in candidates if c["semantic_score"] >= MIN_RELEVANCE_SCORE]
    if not relevant_candidates:
        trace.update(rerank_ms=0.0, generate_ms=0.0, chunk_scores=[], usage=ZERO_USAGE)
        return {"answer": NO_RELEVANT_INFO_ANSWER, "sources": [], "usage": ZERO_USAGE, "trace": trace}

    with time_stage(trace, "rerank"):
        top_chunks = rerank(question, relevant_candidates, top_k=top_k)
    trace["chunk_scores"] = [round(c["score"], 3) for c in top_chunks]

    with time_stage(trace, "generate"):
        result = generate_answer(question, top_chunks)

    trace["usage"] = result["usage"]
    result["trace"] = trace
    return result


def main() -> None:
    question = "How do I pair my headphones?"
    result = answer(question)

    print(f"Question: {question}\n")
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  [{s['n']}] {s['product']} - {s['title']}")
        print(f"      {s['url']}")
    print(f"\nTokens used: {result['usage']['input_tokens']} in / {result['usage']['output_tokens']} out")


if __name__ == "__main__":
    main()
