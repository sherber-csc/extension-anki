from __future__ import annotations

import unittest

from backend.note_mapper import NoteMapper
from backend.schemas import GeneratedAudio, GeneratedNoteContent, QueueRecord
from backend.single_generation_service import SingleGenerationService


class FakeLLMClient:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error

    def generate_note_content(self, *, word: str, source_sentence: str | None = None) -> GeneratedNoteContent:
        _ = (word, source_sentence)
        if self.error is not None:
            raise self.error
        return GeneratedNoteContent(
            word="retry",
            ipa="/riːˈtraɪ/",
            emoji="retry-emoji",
            image_prompt="retry prompt",
            meanings=["to try again"],
            pairs=["retry the request"],
            examples=[
                "Generated example one.",
                "Generated example two.",
                "Generated example three.",
            ],
        )


class FakeAudioService:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error

    def generate_audio(self, word: str) -> GeneratedAudio:
        _ = word
        if self.error is not None:
            raise self.error
        return GeneratedAudio(
            filename="retry_anki_audio.wav",
            file_path="D:/tmp/retry_anki_audio.wav",
        )


class FakeAnkiService:
    def __init__(
        self,
        *,
        duplicate_exists: bool = False,
        write_error: Exception | None = None,
    ) -> None:
        self.duplicate_exists = duplicate_exists
        self.write_error = write_error
        self.write_calls: list[dict] = []

    def ensure_generation_ready(self) -> None:
        return

    def contains_word_key(self, word_key: str) -> bool:
        _ = word_key
        return self.duplicate_exists

    def write_note(
        self,
        *,
        word_key: str,
        note_fields: dict[str, str],
        audio_file_path: str | None = None,
    ) -> int:
        if self.write_error is not None:
            raise self.write_error
        self.write_calls.append(
            {
                "word_key": word_key,
                "note_fields": note_fields,
                "audio_file_path": audio_file_path,
            }
        )
        return 123


def fake_build_forms(lemma: str, *, is_verb: bool) -> str:
    _ = (lemma, is_verb)
    return ""


class SingleGenerationServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.record = QueueRecord(
            record_id=7,
            surface_form="retried",
            normalized_form="retried",
            lemma="retry",
            word_key="retry",
            source_sentence="Please retry the download if it doesn't start automatically.",
            source_title="Example title",
            source_url="https://example.com",
            source_type="web",
            source_timestamp=None,
            captured_at="2026-03-29T00:00:00+00:00",
            status="pending",
            error_message="",
            generator_version="v1",
        )

    def test_generate_returns_success_with_note_id_and_audio_filename(self) -> None:
        service = SingleGenerationService(
            llm_client=FakeLLMClient(),
            audio_service=FakeAudioService(),
            note_mapper=NoteMapper(),
            anki_service=FakeAnkiService(),
            build_examples=lambda source_sentence, examples: examples[:3],
            build_forms=fake_build_forms,
        )

        result = service.generate(self.record)

        self.assertEqual("success", result.status)
        self.assertEqual(7, result.record_id)
        self.assertEqual("retry", result.word_key)
        self.assertEqual("", result.error_message)
        self.assertEqual(123, result.note_id)
        self.assertEqual("retry_anki_audio.wav", result.audio_filename)

    def test_generate_returns_failed_when_word_already_exists_in_anki(self) -> None:
        service = SingleGenerationService(
            llm_client=FakeLLMClient(),
            audio_service=FakeAudioService(),
            note_mapper=NoteMapper(),
            anki_service=FakeAnkiService(duplicate_exists=True),
            build_examples=lambda source_sentence, examples: examples[:3],
            build_forms=fake_build_forms,
        )

        result = service.generate(self.record)

        self.assertEqual("failed", result.status)
        self.assertEqual("retry", result.word_key)
        self.assertIn("word already exists in Anki", result.error_message)
        self.assertIsNone(result.note_id)
        self.assertIsNone(result.audio_filename)

    def test_generate_returns_failed_with_real_leaf_error_message(self) -> None:
        service = SingleGenerationService(
            llm_client=FakeLLMClient(error=RuntimeError("llm response invalid: missing field")),
            audio_service=FakeAudioService(),
            note_mapper=NoteMapper(),
            anki_service=FakeAnkiService(),
            build_examples=lambda source_sentence, examples: examples[:3],
            build_forms=fake_build_forms,
        )

        result = service.generate(self.record)

        self.assertEqual("failed", result.status)
        self.assertEqual("llm response invalid: missing field", result.error_message)


if __name__ == "__main__":
    unittest.main()
