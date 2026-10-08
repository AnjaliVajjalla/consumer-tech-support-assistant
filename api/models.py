"""Validated request and response models for the support API."""

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question", mode="before")
    @classmethod
    def strip_question(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class Source(BaseModel):
    number: int
    product: str
    title: str
    url: str


class Latency(BaseModel):
    retrieve_ms: float
    rerank_ms: float
    generate_ms: float
    total_ms: float


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    latency: Latency
    usage: TokenUsage
