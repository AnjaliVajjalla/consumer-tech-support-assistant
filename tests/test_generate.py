from unittest.mock import MagicMock, patch

from src.generate import (
    NO_RELEVANT_INFO_ANSWER,
    ZERO_USAGE,
    answer,
    build_context,
    generate_answer,
)

SAMPLE_CHUNKS = [
    {
        "chunk_id": "sony__c0",
        "product": "Sony WH-1000XM5",
        "title": "Pairing",
        "url": "https://example.com/sony-pairing",
        "text": "Press and hold the power button for 5 seconds.",
    },
    {
        "chunk_id": "airpods__c0",
        "product": "AirPods Pro 2",
        "title": "Connection troubleshooting",
        "url": "https://example.com/airpods-troubleshooting",
        "text": "Place the AirPods in the case and hold the setup button.",
    },
]


def test_build_context_numbers_each_chunk():
    context = build_context(SAMPLE_CHUNKS)
    assert "[1]" in context
    assert "[2]" in context
    assert "Sony WH-1000XM5" in context
    assert "Press and hold the power button" in context


def test_build_context_empty_chunks_returns_empty_string():
    assert build_context([]) == ""


def _fake_response(text: str, input_tokens: int = 42, output_tokens: int = 17):
    fake = MagicMock()
    fake.content = [MagicMock(text=text)]
    fake.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return fake


@patch("src.generate.get_client")
def test_generate_answer_returns_answer_and_sources(mock_get_client):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response("Press the power button. [1]")
    mock_get_client.return_value = mock_client

    result = generate_answer("How do I pair?", SAMPLE_CHUNKS)

    assert result["answer"] == "Press the power button. [1]"
    assert len(result["sources"]) == 1
    assert result["sources"][0] == {
        "n": 1,
        "product": "Sony WH-1000XM5",
        "title": "Pairing",
        "url": "https://example.com/sony-pairing",
    }
    assert result["usage"] == {"input_tokens": 42, "output_tokens": 17}


@patch("src.generate.get_client")
def test_generate_answer_sends_the_context_to_the_api(mock_get_client):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response("answer")
    mock_get_client.return_value = mock_client

    generate_answer("How do I pair?", SAMPLE_CHUNKS)

    sent_content = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Press and hold the power button" in sent_content
    assert "How do I pair?" in sent_content


@patch("src.generate.get_client")
def test_generate_answer_returns_no_sources_when_none_are_cited(mock_get_client):
    """If the model doesn't cite anything (e.g. it declined to answer), sources should be empty, not every retrieved chunk."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response(
        "I can't answer that from the sources provided."
    )
    mock_get_client.return_value = mock_client

    result = generate_answer("What's the capital of France?", SAMPLE_CHUNKS)

    assert result["sources"] == []


@patch("src.generate.retrieve")
@patch("src.generate.load_chunks_with_embeddings")
@patch("src.generate.get_client")
def test_answer_skips_the_api_when_nothing_is_relevant(
    mock_get_client, mock_load_chunks, mock_retrieve
):
    """A low-relevance question shouldn't reach the API at all, not just get a good refusal from it."""
    mock_load_chunks.return_value = SAMPLE_CHUNKS
    mock_retrieve.return_value = [{**c, "score": 0.02} for c in SAMPLE_CHUNKS]

    result = answer("What is the capital of France?")

    assert result["answer"] == NO_RELEVANT_INFO_ANSWER
    assert result["sources"] == []
    assert result["usage"] == ZERO_USAGE
    mock_get_client.assert_not_called()


@patch("src.generate.retrieve")
@patch("src.generate.load_chunks_with_embeddings")
@patch("src.generate.get_client")
def test_answer_calls_the_api_when_chunks_are_relevant(
    mock_get_client, mock_load_chunks, mock_retrieve
):
    mock_load_chunks.return_value = SAMPLE_CHUNKS
    mock_retrieve.return_value = [{**c, "score": 0.6} for c in SAMPLE_CHUNKS]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response("Press the power button. [1]")
    mock_get_client.return_value = mock_client

    result = answer("How do I pair?")

    assert result["answer"] == "Press the power button. [1]"
    mock_get_client.assert_called_once()
