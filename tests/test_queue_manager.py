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
        created = self._create_pending("retry", captured_at="2026-03-29T00:00:00+00:00")
        loaded = self.queue_manager.get_pending_by_word_key("retry")

        self.assertIsNotNone(loaded)
        self.assertEqual(created.record_id, loaded.record_id)
        self.assertEqual("retry", loaded.word_key)

    def test_delete_pending_removes_only_target_record(self) -> None:
        first = self._create_pending("retry", captured_at="2026-03-29T00:00:00+00:00")
        second = self._create_pending("grammar", captured_at="2026-03-29T00:01:00+00:00")

        status = self.queue_manager.delete_pending(first.record_id)
        items = self.queue_manager.list_recent(limit=50)
        remaining_ids = {item.record_id for item in items}

        self.assertEqual("deleted_pending_item", status)
        self.assertNotIn(first.record_id, remaining_ids)
        self.assertIn(second.record_id, remaining_ids)

    def test_delete_pending_returns_not_found_for_missing_record_id(self) -> None:
        status = self.queue_manager.delete_pending(9999)

        self.assertEqual("pending_record_not_found", status)

    def test_delete_pending_rejects_non_pending_records(self) -> None:
        record = self._create_pending("retry", captured_at="2026-03-29T00:00:00+00:00")
        self.queue_manager.update_status(record_id=record.record_id, status="success", error_message="")

        status = self.queue_manager.delete_pending(record.record_id)
        loaded = self.queue_manager.list_recent(limit=50)

        self.assertEqual("delete_not_allowed", status)
        self.assertEqual(record.record_id, loaded[0].record_id)
        self.assertEqual("success", loaded[0].status)

    def _create_pending(self, surface_form: str, *, captured_at: str):
        request = CaptureRequest(
            surface_form=surface_form,
            source_type="web",
            source_sentence=None,
            source_title="Title",
            source_url="https://example.com",
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
