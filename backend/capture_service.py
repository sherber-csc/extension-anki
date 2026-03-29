from __future__ import annotations

from backend.anki_service import AnkiService
from backend.queue_manager import QueueManager
from backend.schemas import CaptureRequest, CaptureResponse


class CaptureService:
    def __init__(
        self,
        *,
        queue_manager: QueueManager,
        anki_service: AnkiService,
        normalize_surface_form,
        lemmatize_word,
    ) -> None:
        self.queue_manager = queue_manager
        self.anki_service = anki_service
        self.normalize_surface_form = normalize_surface_form
        self.lemmatize_word = lemmatize_word

    def capture(self, payload: dict) -> CaptureResponse:
        try:
            request = CaptureRequest.from_dict(payload)
            normalized = self.normalize_surface_form(request.surface_form)
            lemma_result = self.lemmatize_word(normalized.normalized_form)
        except ValueError as exc:
            return CaptureResponse(
                status="invalid_input",
                message=str(exc),
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            return CaptureResponse(
                status="processing_failed",
                message=str(exc),
            )

        existing_pending = self.queue_manager.get_pending_by_word_key(lemma_result.word_key)
        if existing_pending is not None:
            return CaptureResponse(
                status="already_in_queue",
                message="Word already exists in pending queue.",
                record_id=existing_pending.record_id,
                word_key=existing_pending.word_key,
                lemma=existing_pending.lemma,
            )

        if self.anki_service.is_available() and self.anki_service.contains_word_key(lemma_result.word_key):
            return CaptureResponse(
                status="already_in_anki",
                message="Word already exists in Anki.",
                word_key=lemma_result.word_key,
                lemma=lemma_result.lemma,
            )

        record = self.queue_manager.create_pending(request, normalized, lemma_result)
        return CaptureResponse(
            status="added_to_queue",
            message="Word added to pending queue.",
            record_id=record.record_id,
            word_key=record.word_key,
            lemma=record.lemma,
        )

    @staticmethod
    def is_backend_error(response: CaptureResponse) -> bool:
        return response.status in {
            "backend_unavailable",
            "processing_failed",
        }
