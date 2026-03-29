from __future__ import annotations

import gc
import json
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from backend.app import AppContext, create_handler
from backend.config import DEFAULT_CONFIG
from backend.schemas import GeneratePendingResponse
from backend.storage import SQLiteStorage


class FakeGenerationService:
    def __init__(self, response: GeneratePendingResponse) -> None:
        self.response = response
        self.calls = 0

    def generate_all_pending(self) -> GeneratePendingResponse:
        self.calls += 1
        return self.response


class AppGenerateAllPendingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        storage = SQLiteStorage(Path(self.temp_dir.name) / "queue.db")
        storage.initialize()
        self.generation_service = FakeGenerationService(
            GeneratePendingResponse(
                status="processed_all_with_failures",
                message="Processed all pending records with failures.",
                processed_count=3,
                success_count=2,
                failed_count=1,
            )
        )
        self.context = AppContext(
            config=DEFAULT_CONFIG,
            capture_service=object(),
            queue_manager=object(),
            generation_service=self.generation_service,
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
        self.generation_service = None
        gc.collect()
        self.temp_dir.cleanup()

    def test_generate_all_pending_endpoint_returns_summary_payload(self) -> None:
        request = urllib.request.Request(
            f"{self.base_url}/generate-all-pending",
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(200, response.status)
        self.assertEqual(1, self.generation_service.calls)
        self.assertEqual("processed_all_with_failures", payload["status"])
        self.assertEqual(3, payload["processed_count"])
        self.assertEqual(2, payload["success_count"])
        self.assertEqual(1, payload["failed_count"])


if __name__ == "__main__":
    unittest.main()
