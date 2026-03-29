from __future__ import annotations

import unittest

from backend.anki_service import AnkiService
from backend.note_type_templates import CARD_TEMPLATES, NOTE_TYPE_CSS
from backend.schemas import PreflightCheckResult


class FakeAnkiConnectClient:
    def __init__(
        self,
        *,
        available: bool = True,
        decks: list[str] | None = None,
        models: list[str] | None = None,
        model_fields: dict[str, list[str]] | None = None,
    ) -> None:
        self.available = available
        self.decks = list(decks or [])
        self.models = list(models or [])
        self.model_fields = dict(model_fields or {})
        self.created_decks: list[str] = []
        self.created_models: list[dict[str, object]] = []

    def is_available(self) -> bool:
        return self.available

    def deck_names(self) -> list[str]:
        return list(self.decks)

    def create_deck(self, *, deck: str) -> None:
        if deck not in self.decks:
            self.decks.append(deck)
        self.created_decks.append(deck)

    def model_names(self) -> list[str]:
        return list(self.models)

    def model_field_names(self, *, model_name: str) -> list[str]:
        return list(self.model_fields[model_name])

    def create_model(
        self,
        *,
        model_name: str,
        in_order_fields: list[str],
        css: str,
        card_templates: list[dict[str, str]],
        is_cloze: bool = False,
    ) -> None:
        if model_name not in self.models:
            self.models.append(model_name)
        self.model_fields[model_name] = list(in_order_fields)
        self.created_models.append(
            {
                "model_name": model_name,
                "in_order_fields": list(in_order_fields),
                "css": css,
                "card_templates": list(card_templates),
                "is_cloze": is_cloze,
            }
        )


class AnkiServiceSetupTestCase(unittest.TestCase):
    def test_note_type_templates_match_display_structure_contract(self) -> None:
        front_template = CARD_TEMPLATES[0]["Front"]
        back_template = CARD_TEMPLATES[0]["Back"]

        self.assertIn('<div class="word">{{word}}</div>', front_template)
        self.assertIn('<div class="image-prompt">💡 Imagine: {{image_prompt}}</div>', front_template)
        self.assertNotIn("{{FrontSide}}", back_template)
        self.assertIn('<div class="meanings">{{meanings}}</div>', back_template)
        self.assertNotIn("forms-inline", back_template)
        self.assertNotIn("{{{", back_template)
        self.assertIn('<ul class="pair-list">{{pairs}}</ul>', back_template)
        self.assertIn('<ul class="example-list">{{examples}}</ul>', back_template)
        self.assertIn('.meaning-pos', NOTE_TYPE_CSS)
        self.assertIn('.meaning-text', NOTE_TYPE_CSS)
        self.assertIn('.forms-label', NOTE_TYPE_CSS)
        self.assertIn('.forms-value', NOTE_TYPE_CSS)
        self.assertIn('.pair-zh', NOTE_TYPE_CSS)
        self.assertIn('.example-meta', NOTE_TYPE_CSS)

    def test_check_collection_setup_reports_missing_note_type(self) -> None:
        client = FakeAnkiConnectClient(
            decks=["sherber"],
            models=[],
        )
        service = AnkiService(client)

        result = service.check_collection_setup()

        self.assertFalse(result.ok)
        self.assertEqual("Missing required note type: SherberVocabNote.", result.message)

    def test_check_collection_setup_reports_field_mismatch(self) -> None:
        client = FakeAnkiConnectClient(
            decks=["sherber"],
            models=["SherberVocabNote"],
            model_fields={"SherberVocabNote": ["word", "ipa", "emoji"]},
        )
        service = AnkiService(client)

        result = service.check_collection_setup()

        self.assertFalse(result.ok)
        self.assertIn("fields mismatch", result.message)
        self.assertIn("missing fields", result.message)

    def test_ensure_collection_setup_creates_missing_deck_and_model(self) -> None:
        client = FakeAnkiConnectClient()
        service = AnkiService(client)

        service.ensure_collection_setup()

        self.assertEqual(["sherber"], client.created_decks)
        self.assertEqual(1, len(client.created_models))
        self.assertEqual("SherberVocabNote", client.created_models[0]["model_name"])
        self.assertEqual(NOTE_TYPE_CSS, client.created_models[0]["css"])
        self.assertEqual(CARD_TEMPLATES, client.created_models[0]["card_templates"])

    def test_ensure_collection_setup_is_idempotent_when_setup_matches(self) -> None:
        client = FakeAnkiConnectClient(
            decks=["sherber"],
            models=["SherberVocabNote"],
            model_fields={
                "SherberVocabNote": [
                    "word",
                    "ipa",
                    "emoji",
                    "audio",
                    "image_prompt",
                    "meanings",
                    "pairs",
                    "examples",
                    "forms",
                    "record_id",
                    "word_key",
                    "lemma",
                    "surface_form",
                    "source_url",
                    "source_type",
                    "source_timestamp",
                    "generator_version",
                ]
            },
        )
        service = AnkiService(client)

        service.ensure_collection_setup()

        self.assertEqual([], client.created_decks)
        self.assertEqual([], client.created_models)

    def test_ensure_collection_setup_fails_when_existing_model_fields_mismatch(self) -> None:
        client = FakeAnkiConnectClient(
            decks=["sherber"],
            models=["SherberVocabNote"],
            model_fields={"SherberVocabNote": ["word", "ipa", "emoji"]},
        )
        service = AnkiService(client)

        with self.assertRaises(RuntimeError) as context:
            service.ensure_collection_setup()

        self.assertIn("fields mismatch", str(context.exception))

    def test_ensure_collection_setup_does_not_recreate_existing_matching_model(self) -> None:
        client = FakeAnkiConnectClient(
            decks=["sherber"],
            models=["SherberVocabNote"],
            model_fields={
                "SherberVocabNote": [
                    "word",
                    "ipa",
                    "emoji",
                    "audio",
                    "image_prompt",
                    "meanings",
                    "pairs",
                    "examples",
                    "forms",
                    "record_id",
                    "word_key",
                    "lemma",
                    "surface_form",
                    "source_url",
                    "source_type",
                    "source_timestamp",
                    "generator_version",
                ]
            },
        )
        service = AnkiService(client)

        service.ensure_collection_setup()

        self.assertEqual([], client.created_models)


if __name__ == "__main__":
    unittest.main()
