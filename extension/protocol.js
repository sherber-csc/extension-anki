// Generated from backend/contracts.py. Do not edit by hand.
const PROTOCOL = Object.freeze({
  "captureEndpoint": "/api/captures",
  "generatePendingEndpoint": "/generate-pending",
  "generatePendingResponseFields": [
    "status",
    "message",
    "processed_count",
    "success_count",
    "failed_count",
    "record_id",
    "word_key",
    "error_message"
  ],
  "generatePendingResponseStatuses": [
    "no_pending_items",
    "processed_one_success",
    "processed_one_failed"
  ],
  "generationPreflightEndpoint": "/generation-preflight",
  "generationPreflightFields": [
    "status",
    "summary",
    "checks"
  ],
  "generationPreflightStatuses": [
    "ready",
    "not_ready"
  ],
  "optionalFields": [
    "source_sentence",
    "source_title",
    "source_url",
    "source_timestamp",
    "captured_at"
  ],
  "queueEndpoint": "/queue",
  "queueStatuses": [
    "pending",
    "success",
    "failed"
  ],
  "requestFields": [
    "surface_form",
    "source_sentence",
    "source_title",
    "source_url",
    "source_type",
    "source_timestamp",
    "captured_at"
  ],
  "requiredFields": [
    "surface_form",
    "source_type"
  ],
  "responseFields": [
    "status",
    "message",
    "record_id",
    "word_key",
    "lemma"
  ],
  "responseStatusTexts": {
    "added_to_queue": "已加入待处理",
    "already_in_anki": "该单词已存在于 Anki",
    "already_in_queue": "已在待处理队列中",
    "backend_unavailable": "本地后端不可用",
    "invalid_input": "当前仅支持单词",
    "processing_failed": "采集失败"
  },
  "responseStatuses": [
    "added_to_queue",
    "already_in_queue",
    "already_in_anki",
    "invalid_input",
    "backend_unavailable",
    "processing_failed"
  ],
  "sourceTypes": [
    "web",
    "youtube"
  ]
});

export const CAPTURE_ENDPOINT = PROTOCOL.captureEndpoint;
export const QUEUE_ENDPOINT = PROTOCOL.queueEndpoint;
export const GENERATE_PENDING_ENDPOINT = PROTOCOL.generatePendingEndpoint;
export const GENERATION_PREFLIGHT_ENDPOINT = PROTOCOL.generationPreflightEndpoint;
export const GENERATE_PENDING_RESPONSE_FIELDS = Object.freeze(PROTOCOL.generatePendingResponseFields);
export const GENERATE_PENDING_RESPONSE_STATUSES = Object.freeze(PROTOCOL.generatePendingResponseStatuses);
export const GENERATION_PREFLIGHT_FIELDS = Object.freeze(PROTOCOL.generationPreflightFields);
export const GENERATION_PREFLIGHT_STATUSES = Object.freeze(PROTOCOL.generationPreflightStatuses);
export const REQUEST_FIELDS = Object.freeze(PROTOCOL.requestFields);
export const REQUIRED_FIELDS = Object.freeze(PROTOCOL.requiredFields);
export const OPTIONAL_FIELDS = Object.freeze(PROTOCOL.optionalFields);
export const RESPONSE_FIELDS = Object.freeze(PROTOCOL.responseFields);
export const RESPONSE_STATUSES = Object.freeze(PROTOCOL.responseStatuses);
export const RESPONSE_STATUS_TEXTS = Object.freeze(PROTOCOL.responseStatusTexts);
export const SOURCE_TYPES = Object.freeze(PROTOCOL.sourceTypes);
export const QUEUE_STATUSES = Object.freeze(PROTOCOL.queueStatuses);

export default PROTOCOL;
