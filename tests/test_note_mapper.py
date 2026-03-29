from __future__ import annotations

import unittest

from backend.note_mapper import NoteMapper
from backend.schemas import GeneratedNoteContent, QueueRecord


class NoteMapperTestCase(unittest.TestCase):
    def test_serializes_display_fields_as_html_fragments_with_escaping(self) -> None:
        mapper = NoteMapper()
        record = QueueRecord(
            record_id=101,
            surface_form="retry",
            normalized_form="retry",
            lemma="retry",
            word_key="retry",
            source_sentence="Please retry the download if it doesn't start automatically.",
            source_title="How to Fix Download Problems",
            source_url="https://example.com",
            source_type="web",
            source_timestamp="00:12:35",
            captured_at="2026-03-29T00:00:00+00:00",
            status="pending",
            error_message="",
            generator_version="v1",
        )
        generated_content = GeneratedNoteContent(
            word="retry",
            ipa="/riːˈtraɪ/",
            emoji="retry-emoji",
            image_prompt="retry prompt",
            meanings=["(verb) to try again", "(noun) another <attempt>"],
            pairs=[
                "retry the request（重新请求）",
                "retry later（稍后重试）",
                "retry & recover（重试并恢复）",
                "retry forever（一直重试）",
            ],
            examples=[
                "Generated example one.",
                "Generated example two.",
                "Generated example three.",
            ],
        )

        result = mapper.map_note_fields(
            record=record,
            generated_content=generated_content,
            audio_filename="retry.wav",
            examples=[
                "Please retry the download if it doesn't start automatically. (source sentence)",
                "Generated example two. (verb)",
                "Generated example three <again>. (noun)",
                "Generated example four. (verb)",
            ],
            forms="retries / retried & retrying",
        )

        self.assertEqual(
            (
                '<div class="meaning-item"><span class="meaning-pos">(verb)</span> '
                '<span class="meaning-text">to try again</span></div>'
                '<div class="meaning-item"><span class="meaning-pos">(noun)</span> '
                '<span class="meaning-text">another &lt;attempt&gt;</span></div>'
            ),
            result["meanings"],
        )
        self.assertEqual(
            (
                '<li class="pair-item"><span class="pair-en">retry the request</span> '
                '<span class="pair-zh">(重新请求)</span></li>'
                '<li class="pair-item"><span class="pair-en">retry later</span> '
                '<span class="pair-zh">(稍后重试)</span></li>'
                '<li class="pair-item"><span class="pair-en">retry &amp; recover</span> '
                '<span class="pair-zh">(重试并恢复)</span></li>'
            ),
            result["pairs"],
        )
        self.assertEqual(
            (
                '<li class="example-item"><span class="example-sentence">'
                "Please retry the download if it doesn't start automatically."
                '</span> <span class="example-meta">(verb)</span> '
                '<span class="example-meta">(source sentence)</span></li>'
                '<li class="example-item"><span class="example-sentence">Generated example two.</span> '
                '<span class="example-meta">(verb)</span></li>'
                '<li class="example-item"><span class="example-sentence">Generated example three &lt;again&gt;.</span> '
                '<span class="example-meta">(noun)</span></li>'
            ),
            result["examples"],
        )
        self.assertEqual(
            (
                '<span class="forms-label">forms:</span> '
                '<span class="forms-value">retries / retried &amp; retrying</span>'
            ),
            result["forms"],
        )


if __name__ == "__main__":
    unittest.main()
