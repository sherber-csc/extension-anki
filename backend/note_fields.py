from __future__ import annotations

from typing import Final

DISPLAY_FIELDS: Final[tuple[str, ...]] = (
    "word",
    "ipa",
    "emoji",
    "audio",
    "image_prompt",
    "meanings",
    "pairs",
    "examples",
)

WEAK_DISPLAY_FIELDS: Final[tuple[str, ...]] = ("forms",)

NON_DISPLAY_NOTE_FIELDS: Final[tuple[str, ...]] = (
    "record_id",
    "word_key",
    "lemma",
    "surface_form",
    "source_url",
    "source_type",
    "source_timestamp",
    "generator_version",
)

INTERMEDIATE_FIELDS: Final[tuple[str, ...]] = ("source_sentence",)
