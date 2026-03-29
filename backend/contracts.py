from __future__ import annotations

import json
from typing import Final

CAPTURE_REQUEST_FIELDS: Final[tuple[str, ...]] = (
    "surface_form",
    "source_sentence",
    "source_title",
    "source_url",
    "source_type",
    "source_timestamp",
    "captured_at",
)

CAPTURE_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "surface_form",
    "source_type",
)

CAPTURE_OPTIONAL_FIELDS: Final[tuple[str, ...]] = (
    "source_sentence",
    "source_title",
    "source_url",
    "source_timestamp",
    "captured_at",
)

CAPTURE_RESPONSE_FIELDS: Final[tuple[str, ...]] = (
    "status",
    "message",
    "record_id",
    "word_key",
    "lemma",
)

SOURCE_TYPES: Final[tuple[str, ...]] = (
    "web",
    "youtube",
)

RESPONSE_STATUSES: Final[tuple[str, ...]] = (
    "added_to_queue",
    "already_in_queue",
    "already_in_anki",
    "invalid_input",
    "backend_unavailable",
    "processing_failed",
)

QUEUE_STATUSES: Final[tuple[str, ...]] = (
    "pending",
    "success",
    "failed",
)

CAPTURE_ENDPOINT: Final[str] = "/api/captures"

RESPONSE_STATUS_TEXTS: Final[dict[str, str]] = {
    "added_to_queue": "已加入待处理",
    "already_in_queue": "已在待处理队列中",
    "already_in_anki": "该单词已存在于 Anki",
    "invalid_input": "当前仅支持单词",
    "backend_unavailable": "本地后端不可用",
    "processing_failed": "采集失败",
}

EXTENSION_PROTOCOL_SNAPSHOT: Final[dict[str, object]] = {
    "captureEndpoint": CAPTURE_ENDPOINT,
    "requestFields": list(CAPTURE_REQUEST_FIELDS),
    "requiredFields": list(CAPTURE_REQUIRED_FIELDS),
    "optionalFields": list(CAPTURE_OPTIONAL_FIELDS),
    "responseFields": list(CAPTURE_RESPONSE_FIELDS),
    "responseStatuses": list(RESPONSE_STATUSES),
    "responseStatusTexts": dict(RESPONSE_STATUS_TEXTS),
    "sourceTypes": list(SOURCE_TYPES),
    "queueStatuses": list(QUEUE_STATUSES),
}


def render_extension_protocol_js() -> str:
    snapshot = json.dumps(
        EXTENSION_PROTOCOL_SNAPSHOT,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return "\n".join(
        (
            "// Generated from backend/contracts.py. Do not edit by hand.",
            f"const PROTOCOL = Object.freeze({snapshot});",
            "",
            "export const CAPTURE_ENDPOINT = PROTOCOL.captureEndpoint;",
            "export const REQUEST_FIELDS = Object.freeze(PROTOCOL.requestFields);",
            "export const REQUIRED_FIELDS = Object.freeze(PROTOCOL.requiredFields);",
            "export const OPTIONAL_FIELDS = Object.freeze(PROTOCOL.optionalFields);",
            "export const RESPONSE_FIELDS = Object.freeze(PROTOCOL.responseFields);",
            "export const RESPONSE_STATUSES = Object.freeze(PROTOCOL.responseStatuses);",
            "export const RESPONSE_STATUS_TEXTS = Object.freeze(PROTOCOL.responseStatusTexts);",
            "export const SOURCE_TYPES = Object.freeze(PROTOCOL.sourceTypes);",
            "export const QUEUE_STATUSES = Object.freeze(PROTOCOL.queueStatuses);",
            "",
            "export default PROTOCOL;",
            "",
        )
    )
