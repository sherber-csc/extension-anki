from __future__ import annotations

from backend.schemas import CaptureRequest, LemmaResult, NormalizationResult, QueueRecord
from backend.storage import SQLiteStorage


class QueueRepository:
    def __init__(self, storage: SQLiteStorage) -> None:
        self.storage = storage

    def get_pending_by_word_key(self, word_key: str) -> QueueRecord | None:
        with self.storage.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    record_id,
                    surface_form,
                    normalized_form,
                    lemma,
                    word_key,
                    source_sentence,
                    source_title,
                    source_url,
                    source_type,
                    source_timestamp,
                    captured_at,
                    status,
                    error_message,
                    generator_version
                FROM queue_records
                WHERE word_key = ? AND status = 'pending'
                ORDER BY record_id ASC
                LIMIT 1
                """,
                (word_key,),
            ).fetchone()

        if row is None:
            return None

        return QueueRecord.from_row(tuple(row))

    def create_pending(
        self,
        request: CaptureRequest,
        normalized: NormalizationResult,
        lemma_result: LemmaResult,
        *,
        generator_version: str,
    ) -> QueueRecord:
        with self.storage.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO queue_records (
                    surface_form,
                    normalized_form,
                    lemma,
                    word_key,
                    source_sentence,
                    source_title,
                    source_url,
                    source_type,
                    source_timestamp,
                    captured_at,
                    status,
                    error_message,
                    generator_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', '', ?)
                """,
                (
                    request.surface_form,
                    normalized.normalized_form,
                    lemma_result.lemma,
                    lemma_result.word_key,
                    request.source_sentence,
                    request.source_title,
                    request.source_url,
                    request.source_type,
                    request.source_timestamp,
                    request.captured_at,
                    generator_version,
                ),
            )
            record_id = int(cursor.lastrowid)

        return QueueRecord(
            record_id=record_id,
            surface_form=request.surface_form,
            normalized_form=normalized.normalized_form,
            lemma=lemma_result.lemma,
            word_key=lemma_result.word_key,
            source_sentence=request.source_sentence,
            source_title=request.source_title,
            source_url=request.source_url,
            source_type=request.source_type,
            source_timestamp=request.source_timestamp,
            captured_at=request.captured_at or "",
            status="pending",
            error_message="",
            generator_version=generator_version,
        )

    def list_recent(self, *, limit: int) -> list[QueueRecord]:
        with self.storage.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    record_id,
                    surface_form,
                    normalized_form,
                    lemma,
                    word_key,
                    source_sentence,
                    source_title,
                    source_url,
                    source_type,
                    source_timestamp,
                    captured_at,
                    status,
                    error_message,
                    generator_version
                FROM queue_records
                ORDER BY captured_at DESC, record_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [QueueRecord.from_row(tuple(row)) for row in rows]
