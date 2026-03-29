from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.capture_service import CaptureService
from backend.lemmatizer import lemmatize_word
from backend.normalization import normalize_surface_form
from backend.queue_manager import QueueManager
from backend.queue_repository import QueueRepository
from backend.storage import SQLiteStorage


class FakeAnkiService:
    def __init__(self, *, available: bool, contains_word_key: bool) -> None:
        self.available = available
        self.contains_word_key_value = contains_word_key

    def is_available(self) -> bool:
        return self.available

    def contains_word_key(self, word_key: str) -> bool:
        _ = word_key
        return self.contains_word_key_value


class CaptureServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "queue.db"
        storage = SQLiteStorage(database_path)
        storage.initialize()
        self.queue_manager = QueueManager(
            QueueRepository(storage),
            generator_version="v1",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_capture_still_adds_to_queue_when_anki_is_unavailable(self) -> None:
        service = CaptureService(
            queue_manager=self.queue_manager,
            anki_service=FakeAnkiService(available=False, contains_word_key=False),
            normalize_surface_form=normalize_surface_form,
            lemmatize_word=lemmatize_word,
        )

        response = service.capture(
            {
                "surface_form": "retry",
                "source_type": "web",
            }
        )

        self.assertEqual("added_to_queue", response.status)
        self.assertEqual("retry", response.word_key)

    def test_already_in_anki_only_when_anki_is_available(self) -> None:
        service = CaptureService(
            queue_manager=self.queue_manager,
            anki_service=FakeAnkiService(available=True, contains_word_key=True),
            normalize_surface_form=normalize_surface_form,
            lemmatize_word=lemmatize_word,
        )

        response = service.capture(
            {
                "surface_form": "retry",
                "source_type": "web",
            }
        )

        self.assertEqual("already_in_anki", response.status)

    def test_already_in_queue_wins_before_anki_check(self) -> None:
        priming_service = CaptureService(
            queue_manager=self.queue_manager,
            anki_service=FakeAnkiService(available=False, contains_word_key=False),
            normalize_surface_form=normalize_surface_form,
            lemmatize_word=lemmatize_word,
        )
        priming_service.capture(
            {
                "surface_form": "retry",
                "source_type": "web",
            }
        )

        service = CaptureService(
            queue_manager=self.queue_manager,
            anki_service=FakeAnkiService(available=True, contains_word_key=True),
            normalize_surface_form=normalize_surface_form,
            lemmatize_word=lemmatize_word,
        )
        response = service.capture(
            {
                "surface_form": "retries",
                "source_type": "web",
            }
        )

        self.assertEqual("already_in_queue", response.status)


if __name__ == "__main__":
    unittest.main()
