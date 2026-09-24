from pydantic import BaseModel
from typing import Any


class AskRequest(BaseModel):
    query: str
    language: str = "auto"
    conversation_id: str | None = None


class SourceCard(BaseModel):
    title: str
    url: str | None = None
    page: int | str | None = None
    snippet: str


class AskResponse(BaseModel):
    answer: str
    language: str
    verified: bool
    sources: list[SourceCard]
    conversation_id: str
    pii_detected: bool = False
    pii_types: list[str] = []
    clean_query: str = ""
    partner_data: dict[str, Any] | None = None


class SpeakRequest(BaseModel):
    text: str
    language: str = "en-US"
