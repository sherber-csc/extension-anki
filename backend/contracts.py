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
QUEUE_ENDPOINT: Final[str] = "/queue"
GENERATE_PENDING_ENDPOINT: Final[str] = "/generate-pending"
GENERATION_PREFLIGHT_ENDPOINT: Final[str] = "/generation-preflight"

GENERATE_PENDING_RESPONSE_STATUSES: Final[tuple[str, ...]] = (
    "no_pending_items",
    "processed_one_success",
    "processed_one_failed",
)

GENERATE_PENDING_RESPONSE_FIELDS: Final[tuple[str, ...]] = (
    "status",
    "message",
    "processed_count",
    "success_count",
    "failed_count",
    "record_id",
    "word_key",
    "error_message",
)

DELETE_PENDING_RESPONSE_STATUSES: Final[tuple[str, ...]] = (
    "deleted_pending_item",
    "pending_record_not_found",
    "delete_not_allowed",
)

DELETE_PENDING_RESPONSE_FIELDS: Final[tuple[str, ...]] = (
    "status",
    "message",
    "record_id",
)

GENERATION_PREFLIGHT_STATUSES: Final[tuple[str, ...]] = (
    "ready",
    "not_ready",
)

GENERATION_PREFLIGHT_FIELDS: Final[tuple[str, ...]] = (
    "status",
    "summary",
    "checks",
)

RESPONSE_STATUS_TEXTS: Final[dict[str, str]] = {
    "added_to_queue": "已加入待处理",
    "already_in_queue": "已在待处理队列中",
    "already_in_anki": "该单词已存在于 Anki",
    "invalid_input": "当前仅支持单词",
    "backend_unavailable": "本地后端不可用",
    "processing_failed": "采集失败",
    "deleted_pending_item": "Deleted one pending record.",
    "pending_record_not_found": "Pending record not found.",
    "delete_not_allowed": "Delete is only allowed for pending records.",
}

EXTENSION_PROTOCOL_SNAPSHOT: Final[dict[str, object]] = {
    "captureEndpoint": CAPTURE_ENDPOINT,
    "queueEndpoint": QUEUE_ENDPOINT,
    "generatePendingEndpoint": GENERATE_PENDING_ENDPOINT,
    "generationPreflightEndpoint": GENERATION_PREFLIGHT_ENDPOINT,
    "deletePendingResponseFields": list(DELETE_PENDING_RESPONSE_FIELDS),
    "deletePendingResponseStatuses": list(DELETE_PENDING_RESPONSE_STATUSES),
    "generatePendingResponseFields": list(GENERATE_PENDING_RESPONSE_FIELDS),
    "generatePendingResponseStatuses": list(GENERATE_PENDING_RESPONSE_STATUSES),
    "generationPreflightFields": list(GENERATION_PREFLIGHT_FIELDS),
    "generationPreflightStatuses": list(GENERATION_PREFLIGHT_STATUSES),
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
            "export const QUEUE_ENDPOINT = PROTOCOL.queueEndpoint;",
            "export const GENERATE_PENDING_ENDPOINT = PROTOCOL.generatePendingEndpoint;",
            "export const GENERATION_PREFLIGHT_ENDPOINT = PROTOCOL.generationPreflightEndpoint;",
            "export const DELETE_PENDING_RESPONSE_FIELDS = Object.freeze(PROTOCOL.deletePendingResponseFields);",
            "export const DELETE_PENDING_RESPONSE_STATUSES = Object.freeze(PROTOCOL.deletePendingResponseStatuses);",
            "export const GENERATE_PENDING_RESPONSE_FIELDS = Object.freeze(PROTOCOL.generatePendingResponseFields);",
            "export const GENERATE_PENDING_RESPONSE_STATUSES = Object.freeze(PROTOCOL.generatePendingResponseStatuses);",
            "export const GENERATION_PREFLIGHT_FIELDS = Object.freeze(PROTOCOL.generationPreflightFields);",
            "export const GENERATION_PREFLIGHT_STATUSES = Object.freeze(PROTOCOL.generationPreflightStatuses);",
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
