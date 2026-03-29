from __future__ import annotations

import gc
import tempfile
import unittest
from pathlib import Path

from backend.generation_service import GenerationService
from backend.queue_manager import QueueManager
from backend.queue_repository import QueueRepository
from backend.schemas import CaptureRequest, LemmaResult, NormalizationResult, SingleGenerationResult
from backend.storage import SQLiteStorage


class FakeSingleGenerationService:
    def __init__(self) -> None:
        self.results_by_record_id: dict[int, SingleGenerationResult] = {}
        self.calls: list[int] = []

    def generate(self, record) -> SingleGenerationResult:
        self.calls.append(record.record_id)
        return self.results_by_record_id[record.record_id]


class GenerationServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "queue.db"
        storage = SQLiteStorage(database_path)
        storage.initialize()
        self.queue_manager = QueueManager(
            QueueRepository(storage),
            generator_version="v1",
        )
        self.single_generation_service = FakeSingleGenerationService()
        self.service = GenerationService(
            queue_manager=self.queue_manager,
            single_generation_service=self.single_generation_service,
        )

    def tearDown(self) -> None:
        self.service = None
        self.queue_manager = None
        gc.collect()
        self.temp_dir.cleanup()

    def test_generate_pending_returns_no_pending_items_for_empty_queue(self) -> None:
        response = self.service.generate_pending()

        self.assertEqual("no_pending_items", response.status)
        self.assertEqual(0, response.processed_count)
        self.assertEqual(0, response.success_count)
        self.assertEqual(0, response.failed_count)
        self.assertEqual([], self.single_generation_service.calls)

    def test_generate_pending_marks_oldest_pending_as_success(self) -> None:
        oldest = self._create_pending("grammar", captured_at="2026-03-29T00:00:00+00:00")
        newer = self._create_pending("simple", captured_at="2026-03-29T01:00:00+00:00")
        self.single_generation_service.results_by_record_id[oldest.record_id] = (
            SingleGenerationResult.success(
                record_id=oldest.record_id,
                word_key=oldest.word_key,
                note_id=123,
                audio_filename="grammar.wav",
            )
        )

        response = self.service.generate_pending()
        queue_items = self.queue_manager.list_recent(limit=50)

        self.assertEqual("processed_one_success", response.status)
        self.assertEqual(1, response.processed_count)
        self.assertEqual(1, response.success_count)
        self.assertEqual(0, response.failed_count)
        self.assertEqual(oldest.record_id, response.record_id)
        self.assertEqual("grammar", response.word_key)
        self.assertEqual([oldest.record_id], self.single_generation_service.calls)
        loaded_oldest = next(item for item in queue_items if item.record_id == oldest.record_id)
        loaded_newer = next(item for item in queue_items if item.record_id == newer.record_id)
        self.assertEqual("success", loaded_oldest.status)
        self.assertEqual("", loaded_oldest.error_message)
        self.assertEqual("pending", loaded_newer.status)

    def test_generate_pending_marks_duplicate_in_anki_as_failed_with_real_error(self) -> None:
        record = self._create_pending("retry", captured_at="2026-03-29T00:00:00+00:00")
        self.single_generation_service.results_by_record_id[record.record_id] = (
            SingleGenerationResult.failed(
                record_id=record.record_id,
                word_key=record.word_key,
                error_message="word already exists in Anki for word_key=retry",
            )
        )

        response = self.service.generate_pending()
        loaded = self.queue_manager.list_recent(limit=50)[0]

        self.assertEqual("processed_one_failed", response.status)
        self.assertEqual(1, response.processed_count)
        self.assertEqual(0, response.success_count)
        self.assertEqual(1, response.failed_count)
        self.assertEqual(
            "word already exists in Anki for word_key=retry",
            response.error_message,
        )
        self.assertEqual("failed", loaded.status)
        self.assertEqual(
            "word already exists in Anki for word_key=retry",
            loaded.error_message,
        )

    def test_generate_pending_marks_leaf_failure_as_failed_with_real_error(self) -> None:
        record = self._create_pending("attempt", captured_at="2026-03-29T00:00:00+00:00")
        self.single_generation_service.results_by_record_id[record.record_id] = (
            SingleGenerationResult.failed(
                record_id=record.record_id,
                word_key=record.word_key,
                error_message="audio generation failed: PowerShell is not available.",
            )
        )

        response = self.service.generate_pending()
        loaded = self.queue_manager.list_recent(limit=50)[0]

        self.assertEqual("processed_one_failed", response.status)
        self.assertEqual(
            "audio generation failed: PowerShell is not available.",
            response.error_message,
        )
        self.assertEqual("failed", loaded.status)
        self.assertEqual(
            "audio generation failed: PowerShell is not available.",
            loaded.error_message,
        )

    def _create_pending(self, surface_form: str, *, captured_at: str):
        request = CaptureRequest(
            surface_form=surface_form,
            source_type="web",
            source_sentence=None,
            source_title=None,
            source_url=None,
            source_timestamp=None,
            captured_at=captured_at,
        )
        normalized = NormalizationResult(surface_form=surface_form, normalized_form=surface_form)
        lemma_result = LemmaResult(
            normalized_form=surface_form,
            lemma=surface_form,
            word_key=surface_form,
        )
        return self.queue_manager.create_pending(request, normalized, lemma_result)


if __name__ == "__main__":
    unittest.main()
