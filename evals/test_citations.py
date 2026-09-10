"""
Citation evaluation for the Consumer Technology Support Assistant.

What this does:
  Calls the real API to check that generated answers cite the
  correct source product, not just that a source was retrieved.
  Kept separate from tests/ because it costs real API calls, unlike
  the mocked unit tests.
"""

import re

import pytest

from src.generate import answer

EVAL_CASES = [
    {
        "question": "How do I put my Sony headphones into pairing mode?",
        "expected_product": "Sony WH-1000XM5",
    },
    {
        "question": "What do I do if my AirPods won't connect?",
        "expected_product": "AirPods Pro 2 (USB-C)",
    },
]


def _cited_products(result: dict) -> set[str]:
    """Which sources the answer text actually cites (its [n] markers), mapped to products."""
    cited_numbers = {int(n) for n in re.findall(r"\[(\d+)\]", result["answer"])}
    sources_by_number = {s["n"]: s for s in result["sources"]}
    return {sources_by_number[n]["product"] for n in cited_numbers if n in sources_by_number}


@pytest.mark.parametrize("case", EVAL_CASES)
def test_answer_cites_the_correct_product(case):
    """The answer's own [n] citations point to the right product, not just that it was retrieved."""
    result = answer(case["question"])
    assert case["expected_product"] in _cited_products(result)


def test_answer_cites_nothing_for_a_product_not_in_the_corpus():
    """Bose isn't in the corpus, so the answer must not cite our real products as if they covered it."""
    result = answer("What is the battery life on my Bose QuietComfort headphones?")
    assert result["sources"] == []


def test_answer_cites_nothing_for_a_warranty_question():
    """No source document covers warranty policy, so the answer must not fabricate a citation for it."""
    result = answer("My Sony headphones broke, can I get a free replacement under warranty?")
    assert result["sources"] == []
