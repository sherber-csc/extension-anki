from __future__ import annotations

from backend.queue_repository import QueueRepository
from backend.schemas import CaptureRequest, LemmaResult, NormalizationResult, QueueRecord


class QueueManager:
    def __init__(self, repository: QueueRepository, *, generator_version: str) -> None:
        self.repository = repository
        self.generator_version = generator_version

    def get_pending_by_word_key(self, word_key: str) -> QueueRecord | None:
        return self.repository.get_pending_by_word_key(word_key)

    def create_pending(
        self,
        request: CaptureRequest,
        normalized: NormalizationResult,
        lemma_result: LemmaResult,
    ) -> QueueRecord:
        return self.repository.create_pending(
            request,
            normalized,
            lemma_result,
            generator_version=self.generator_version,
        )

    def list_recent(self, *, limit: int) -> list[QueueRecord]:
        return self.repository.list_recent(limit=limit)

    def list_by_status(self, *, status: str, limit: int | None = None) -> list[QueueRecord]:
        return self.repository.list_by_status(status=status, limit=limit)

    def update_status(self, *, record_id: int, status: str, error_message: str) -> None:
        self.repository.update_status(record_id=record_id, status=status, error_message=error_message)
