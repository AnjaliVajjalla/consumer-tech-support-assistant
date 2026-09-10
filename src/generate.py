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

from retrieve import load_chunks_with_embeddings, retrieve  # noqa: E402

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
    "recommend checking official support instead of guessing."
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

    return {"answer": answer_text, "sources": sources}


def answer(question: str, top_k: int = 3) -> dict:
    """Answer a question end-to-end: retrieve relevant chunks, then generate a grounded, cited answer."""
    chunks = load_chunks_with_embeddings()
    top_chunks = retrieve(question, chunks, top_k=top_k)

    relevant_chunks = [c for c in top_chunks if c["score"] >= MIN_RELEVANCE_SCORE]
    if not relevant_chunks:
        return {"answer": NO_RELEVANT_INFO_ANSWER, "sources": []}

    return generate_answer(question, relevant_chunks)


def main() -> None:
    question = "How do I pair my headphones?"
    result = answer(question)

    print(f"Question: {question}\n")
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  [{s['n']}] {s['product']} - {s['title']}")
        print(f"      {s['url']}")


if __name__ == "__main__":
    main()
