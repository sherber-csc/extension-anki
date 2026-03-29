from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.audio_service import AudioService
from backend.generation_preflight import GenerationPreflightService
from backend.llm_client import LLMClient


class DummyAnkiService:
    def __init__(self, available: bool) -> None:
        self.available = available

    def is_available(self) -> bool:
        return self.available


class GenerationPreflightServiceTestCase(unittest.TestCase):
    def test_returns_ready_when_all_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = GenerationPreflightService(
                anki_service=DummyAnkiService(True),
                llm_client=LLMClient(api_key="test-key", base_url="https://example.com"),
                audio_service=AudioService(output_dir=Path(temp_dir) / "audio"),
            )

            response = service.check()

        self.assertEqual("ready", response.status)
        self.assertEqual("3 of 3 checks passed.", response.summary)
        self.assertTrue(response.checks["anki"].ok)
        self.assertTrue(response.checks["llm"].ok)
        self.assertTrue(response.checks["audio"].ok)

    def test_returns_not_ready_when_any_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = GenerationPreflightService(
                anki_service=DummyAnkiService(True),
                llm_client=LLMClient(api_key=None, base_url=None),
                audio_service=AudioService(output_dir=Path(temp_dir) / "audio"),
            )

            response = service.check()

        self.assertEqual("not_ready", response.status)
        self.assertEqual("2 of 3 checks passed.", response.summary)
        self.assertTrue(response.checks["anki"].ok)
        self.assertFalse(response.checks["llm"].ok)
        self.assertTrue(response.checks["audio"].ok)


if __name__ == "__main__":
    unittest.main()
