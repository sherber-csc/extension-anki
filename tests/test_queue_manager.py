from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.queue_repository import QueueRepository
from backend.queue_manager import QueueManager
from backend.schemas import CaptureRequest, LemmaResult, NormalizationResult
from backend.storage import SQLiteStorage


class QueueManagerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "queue.db"
        self.storage = SQLiteStorage(database_path)
        self.storage.initialize()
        self.queue_manager = QueueManager(
            QueueRepository(self.storage),
            generator_version="v1",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_lookup_pending_record(self) -> None:
        request = CaptureRequest(
            surface_form="retry",
            source_type="web",
            source_sentence=None,
            source_title="Title",
            source_url="https://example.com",
            source_timestamp=None,
            captured_at="2026-03-29T00:00:00+00:00",
        )
        normalized = NormalizationResult(surface_form="retry", normalized_form="retry")
        lemma_result = LemmaResult(normalized_form="retry", lemma="retry", word_key="retry")

        created = self.queue_manager.create_pending(request, normalized, lemma_result)
        loaded = self.queue_manager.get_pending_by_word_key("retry")

        self.assertIsNotNone(loaded)
        self.assertEqual(created.record_id, loaded.record_id)
        self.assertEqual("retry", loaded.word_key)


if __name__ == "__main__":
    unittest.main()
