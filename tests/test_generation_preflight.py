from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.audio_service import AudioService
from backend.generation_preflight import GenerationPreflightService
from backend.llm_client import LLMClient
from backend.schemas import PreflightCheckResult


class DummyAnkiService:
    def __init__(self, result: PreflightCheckResult) -> None:
        self.result = result

    def check_collection_setup(self) -> PreflightCheckResult:
        return self.result


class GenerationPreflightServiceTestCase(unittest.TestCase):
    def test_returns_ready_when_all_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = GenerationPreflightService(
                anki_service=DummyAnkiService(
                    PreflightCheckResult(
                        ok=True,
                        message="Anki collection setup is ready.",
                    )
                ),
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
                anki_service=DummyAnkiService(
                    PreflightCheckResult(
                        ok=False,
                        message="Missing required note type: SherberVocabNote.",
                    )
                ),
                llm_client=LLMClient(api_key=None, base_url=None),
                audio_service=AudioService(output_dir=Path(temp_dir) / "audio"),
            )

            response = service.check()

        self.assertEqual("not_ready", response.status)
        self.assertEqual("1 of 3 checks passed.", response.summary)
        self.assertFalse(response.checks["anki"].ok)
        self.assertFalse(response.checks["llm"].ok)
        self.assertTrue(response.checks["audio"].ok)


if __name__ == "__main__":
    unittest.main()
