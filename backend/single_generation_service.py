from __future__ import annotations

from backend.schemas import QueueRecord, SingleGenerationResult


class SingleGenerationService:
    """Runs the real formal-generation chain for one queued record."""

    def __init__(
        self,
        *,
        llm_client,
        audio_service,
        note_mapper,
        anki_service,
        build_examples,
        build_forms,
    ) -> None:
        self.llm_client = llm_client
        self.audio_service = audio_service
        self.note_mapper = note_mapper
        self.anki_service = anki_service
        self.build_examples = build_examples
        self.build_forms = build_forms

    def generate(self, record: QueueRecord) -> SingleGenerationResult:
        try:
            self.anki_service.ensure_generation_ready()
            if self.anki_service.contains_word_key(record.word_key):
                raise RuntimeError(
                    f"word already exists in Anki for word_key={record.word_key}"
                )

            generated_content = self.llm_client.generate_note_content(
                word=record.lemma,
                source_sentence=record.source_sentence,
            )
            generated_audio = self.audio_service.generate_audio(record.lemma)
            examples = self.build_examples(record.source_sentence, generated_content.examples)
            forms = self.build_forms(record.lemma, is_verb=False)
            note_fields = self.note_mapper.map_note_fields(
                record=record,
                generated_content=generated_content,
                audio_filename=generated_audio.filename,
                examples=examples,
                forms=forms,
            )
            note_id = self.anki_service.write_note(
                word_key=record.word_key,
                note_fields=note_fields,
                audio_file_path=generated_audio.file_path,
            )
        except Exception as exc:  # pragma: no cover - defensive guard around external services
            return SingleGenerationResult.failed(
                record_id=record.record_id,
                word_key=record.word_key,
                error_message=str(exc),
            )

        return SingleGenerationResult.success(
            record_id=record.record_id,
            word_key=record.word_key,
            note_id=note_id,
            audio_filename=generated_audio.filename,
        )
