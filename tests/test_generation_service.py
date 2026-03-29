from __future__ import annotations

import gc
import tempfile
import unittest
from pathlib import Path

from backend.generation_service import GenerationService
from backend.queue_manager import QueueManager
from backend.queue_repository import QueueRepository
from backend.schemas import CaptureRequest, LemmaResult, NormalizationResult
from backend.storage import SQLiteStorage


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
        self.service = GenerationService(queue_manager=self.queue_manager)

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

    def test_generate_pending_keeps_current_pending_records_unchanged_when_formal_generation_is_missing(self) -> None:
        request = CaptureRequest(
            surface_form="grammar",
            source_type="web",
            source_sentence=None,
            source_title=None,
            source_url=None,
            source_timestamp=None,
            captured_at="2026-03-29T00:00:00+00:00",
        )
        normalized = NormalizationResult(surface_form="grammar", normalized_form="grammar")
        lemma_result = LemmaResult(normalized_form="grammar", lemma="grammar", word_key="grammar")
        created = self.queue_manager.create_pending(request, normalized, lemma_result)

        response = self.service.generate_pending()
        queue_items = self.queue_manager.list_recent(limit=50)

        self.assertEqual("partial_failure", response.status)
        self.assertEqual(
            "Generate entry is wired, but formal card generation is not implemented yet. "
            "Left 1 pending record(s) unchanged.",
            response.message,
        )
        self.assertEqual(0, response.processed_count)
        self.assertEqual(0, response.success_count)
        self.assertEqual(0, response.failed_count)
        self.assertEqual(1, len(queue_items))
        self.assertEqual(created.record_id, queue_items[0].record_id)
        self.assertEqual("pending", queue_items[0].status)
        self.assertEqual("", queue_items[0].error_message)


if __name__ == "__main__":
    unittest.main()
