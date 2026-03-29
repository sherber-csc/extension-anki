from __future__ import annotations

from backend.schemas import GeneratedNoteContent, QueueRecord


class NoteMapper:
    def map_note_fields(
        self,
        *,
        record: QueueRecord,
        generated_content: GeneratedNoteContent,
        audio_filename: str,
        examples: list[str],
        forms: str,
    ) -> dict[str, str]:
        return {
            "word": generated_content.word,
            "ipa": generated_content.ipa,
            "emoji": generated_content.emoji,
            "audio": audio_filename,
            "image_prompt": generated_content.image_prompt,
            "meanings": _serialize_list(generated_content.meanings),
            "forms": forms,
            "pairs": _serialize_list(generated_content.pairs),
            "examples": _serialize_list(examples),
            "record_id": str(record.record_id),
            "word_key": record.word_key,
            "lemma": record.lemma,
            "surface_form": record.surface_form,
            "source_url": record.source_url or "",
            "source_type": record.source_type,
            "source_timestamp": record.source_timestamp or "",
            "generator_version": record.generator_version,
        }


def _serialize_list(values: list[str]) -> str:
    cleaned_values = [str(value).strip() for value in values if str(value).strip()]
    return f"[{', '.join(cleaned_values)}]"
