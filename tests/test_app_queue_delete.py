from __future__ import annotations

import gc
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from backend.app import AppContext, create_handler
from backend.config import DEFAULT_CONFIG
from backend.queue_manager import QueueManager
from backend.queue_repository import QueueRepository
from backend.schemas import CaptureRequest, LemmaResult, NormalizationResult
from backend.storage import SQLiteStorage


class AppQueueDeleteTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "queue.db"
        storage = SQLiteStorage(database_path)
        storage.initialize()
        self.queue_manager = QueueManager(
            QueueRepository(storage),
            generator_version="v1",
        )
        self.context = AppContext(
            config=DEFAULT_CONFIG,
            capture_service=object(),
            queue_manager=self.queue_manager,
            generation_service=object(),
            generation_preflight_service=object(),
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(self.context))
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=5)
        self.context = None
        self.queue_manager = None
        gc.collect()
        self.temp_dir.cleanup()

    def test_delete_pending_endpoint_removes_only_target_record(self) -> None:
        target = self._create_pending("retry", captured_at="2026-03-29T00:00:00+00:00")
        survivor = self._create_pending("grammar", captured_at="2026-03-29T00:01:00+00:00")

        status_code, payload = self._delete_record(target.record_id)
        items = self.queue_manager.list_recent(limit=50)
        remaining_ids = {item.record_id for item in items}

        self.assertEqual(200, status_code)
        self.assertEqual("deleted_pending_item", payload["status"])
        self.assertEqual(target.record_id, payload["record_id"])
        self.assertNotIn(target.record_id, remaining_ids)
        self.assertIn(survivor.record_id, remaining_ids)

    def test_delete_pending_endpoint_returns_not_found_for_missing_record_id(self) -> None:
        status_code, payload = self._delete_record(9999)

        self.assertEqual(404, status_code)
        self.assertEqual("pending_record_not_found", payload["status"])
        self.assertEqual(9999, payload["record_id"])

    def test_delete_pending_endpoint_rejects_non_pending_record(self) -> None:
        record = self._create_pending("retry", captured_at="2026-03-29T00:00:00+00:00")
        self.queue_manager.update_status(record_id=record.record_id, status="failed", error_message="x")

        status_code, payload = self._delete_record(record.record_id)
        loaded = self.queue_manager.list_recent(limit=50)

        self.assertEqual(409, status_code)
        self.assertEqual("delete_not_allowed", payload["status"])
        self.assertEqual(record.record_id, payload["record_id"])
        self.assertEqual(record.record_id, loaded[0].record_id)
        self.assertEqual("failed", loaded[0].status)

    def _delete_record(self, record_id: int) -> tuple[int, dict]:
        request = urllib.request.Request(
            f"{self.base_url}/queue/{record_id}",
            method="DELETE",
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))

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
