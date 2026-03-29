from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from backend import contracts
from backend.config import DEFAULT_CONFIG


def _clean_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@dataclass(frozen=True)
class CaptureRequest:
    surface_form: str
    source_type: str
    source_sentence: str | None = None
    source_title: str | None = None
    source_url: str | None = None
    source_timestamp: str | None = None
    captured_at: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CaptureRequest":
        missing = [field for field in contracts.CAPTURE_REQUIRED_FIELDS if not payload.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        source_type = str(payload["source_type"]).strip()
        if source_type not in contracts.SOURCE_TYPES:
            raise ValueError(f"Unsupported source_type: {source_type}")

        captured_at = _clean_optional_text(payload.get("captured_at"))
        if captured_at is None:
            captured_at = datetime.now(timezone.utc).astimezone().isoformat()

        return cls(
            surface_form=str(payload["surface_form"]),
            source_type=source_type,
            source_sentence=_clean_optional_text(payload.get("source_sentence")),
            source_title=_clean_optional_text(payload.get("source_title")),
            source_url=_clean_optional_text(payload.get("source_url")),
            source_timestamp=_clean_optional_text(payload.get("source_timestamp")),
            captured_at=captured_at,
        )


@dataclass(frozen=True)
class NormalizationResult:
    surface_form: str
    normalized_form: str


@dataclass(frozen=True)
class LemmaResult:
    normalized_form: str
    lemma: str
    word_key: str


@dataclass(frozen=True)
class QueueRecord:
    record_id: int
    surface_form: str
    normalized_form: str
    lemma: str
    word_key: str
    source_sentence: str | None
    source_title: str | None
    source_url: str | None
    source_type: str
    source_timestamp: str | None
    captured_at: str
    status: str
    error_message: str
    generator_version: str = DEFAULT_CONFIG.default_generator_version

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> "QueueRecord":
        return cls(*row)


@dataclass(frozen=True)
class CaptureResponse:
    status: str
    message: str | None = None
    record_id: int | None = None
    word_key: str | None = None
    lemma: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True)
class GeneratePendingResponse:
    status: str
    message: str
    processed_count: int
    success_count: int
    failed_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
