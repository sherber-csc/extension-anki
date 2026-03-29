from __future__ import annotations

from html import escape
import re

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
            "meanings": _serialize_meanings(generated_content.meanings),
            "forms": _serialize_forms(forms),
            "pairs": _serialize_list_items(
                generated_content.pairs,
                item_class="pair-item",
                limit=3,
            ),
            "examples": _serialize_list_items(
                _normalize_examples(
                    examples,
                    fallback_pos=_extract_primary_pos(generated_content.meanings),
                ),
                item_class="example-item",
                limit=3,
            ),
            "record_id": str(record.record_id),
            "word_key": record.word_key,
            "lemma": record.lemma,
            "surface_form": record.surface_form,
            "source_url": record.source_url or "",
            "source_type": record.source_type,
            "source_timestamp": record.source_timestamp or "",
            "generator_version": record.generator_version,
        }


def _serialize_meanings(values: list[str]) -> str:
    cleaned_values = _clean_values(values)
    return "".join(
        _serialize_meaning_item(value)
        for value in cleaned_values
    )


def _serialize_forms(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ""
    return (
        '<span class="forms-label">forms:</span> '
        f'<span class="forms-value">{_escape_text(text)}</span>'
    )


def _serialize_list_items(
    values: list[str],
    *,
    item_class: str,
    limit: int | None = None,
) -> str:
    cleaned_values = _clean_values(values)
    if limit is not None:
        cleaned_values = cleaned_values[:limit]
    return "".join(
        _serialize_list_item(value, item_class=item_class)
        for value in cleaned_values
    )


def _clean_values(values: list[str]) -> list[str]:
    return [str(value).strip() for value in values if str(value).strip()]


def _escape_text(value: str) -> str:
    return escape(str(value).strip(), quote=False)


def _serialize_meaning_item(value: str) -> str:
    text = str(value).strip()
    match = re.match(r"^\(([^()]+)\)\s*(.+)$", text)
    if not match:
        return (
            '<div class="meaning-item">'
            f'<span class="meaning-text">{_escape_text(text)}</span>'
            "</div>"
        )

    pos, meaning = match.groups()
    return (
        '<div class="meaning-item">'
        f'<span class="meaning-pos">({_escape_text(pos)})</span> '
        f'<span class="meaning-text">{_escape_text(meaning)}</span>'
        "</div>"
    )


def _serialize_list_item(value: str, *, item_class: str) -> str:
    text = str(value).strip()
    if item_class == "pair-item":
        return _serialize_pair_item(text)
    if item_class == "example-item":
        return _serialize_example_item(text)

    return f'<li class="{item_class}">{_escape_text(text)}</li>'


def _serialize_pair_item(text: str) -> str:
    pair_parts = _split_pair_text(text)
    if pair_parts is None:
        return f'<li class="pair-item">{_escape_text(text)}</li>'

    english_text, translated_text = pair_parts
    return (
        '<li class="pair-item">'
        f'<span class="pair-en">{_escape_text(english_text)}</span> '
        f'<span class="pair-zh">({_escape_text(translated_text)})</span>'
        "</li>"
    )


def _serialize_example_item(text: str) -> str:
    sentence_text, meta_values = _split_example_text(text)
    if not meta_values:
        return (
            '<li class="example-item">'
            f'<span class="example-sentence">{_escape_text(text)}</span>'
            "</li>"
        )

    ordered_meta_values = _ordered_example_meta_values(meta_values)
    meta_html = " ".join(
        f'<span class="example-meta">({_escape_text(meta_value)})</span>'
        for meta_value in ordered_meta_values
    )
    return (
        '<li class="example-item">'
        f'<span class="example-sentence">{_escape_text(sentence_text)}</span> '
        f"{meta_html}"
        "</li>"
    )


def _split_pair_text(text: str) -> tuple[str, str] | None:
    full_width_open = text.rfind("（")
    full_width_close = text.endswith("）")
    if full_width_open != -1 and full_width_close:
        english_text = text[:full_width_open].strip()
        translated_text = text[full_width_open + 1 : -1].strip()
        if english_text and translated_text:
            return english_text, translated_text

    ascii_open = text.rfind("(")
    ascii_close = text.endswith(")")
    if ascii_open != -1 and ascii_close:
        english_text = text[:ascii_open].strip()
        translated_text = text[ascii_open + 1 : -1].strip()
        if english_text and translated_text:
            return english_text, translated_text

    bracket_open = text.rfind("[")
    bracket_close = text.endswith("]")
    if bracket_open != -1 and bracket_close:
        english_text = text[:bracket_open].strip()
        translated_text = text[bracket_open + 1 : -1].strip()
        if english_text and translated_text:
            return english_text, translated_text

    return None


def _split_example_text(text: str) -> tuple[str, list[str]]:
    remaining_text = str(text).strip()
    meta_values: list[str] = []

    while True:
        match = re.search(r"\s*\(([^()]+)\)\s*$", remaining_text)
        if match is None:
            break
        meta_value = match.group(1).strip()
        if not meta_value:
            break
        meta_values.insert(0, meta_value)
        remaining_text = remaining_text[: match.start()].rstrip()

    return remaining_text, meta_values


def _normalize_examples(examples: list[str], *, fallback_pos: str | None) -> list[str]:
    normalized_examples: list[str] = []
    for text in examples:
        sentence_text, meta_values = _split_example_text(text)
        if not sentence_text:
            continue

        normalized_meta_values = list(meta_values)
        if fallback_pos is not None and not _has_pos_meta(normalized_meta_values):
            normalized_meta_values.append(fallback_pos)

        if normalized_meta_values:
            normalized_examples.append(
                sentence_text
                + " "
                + " ".join(f"({meta_value})" for meta_value in normalized_meta_values)
            )
        else:
            normalized_examples.append(sentence_text)

    return normalized_examples


def _has_pos_meta(meta_values: list[str]) -> bool:
    return any(meta_value.strip().lower() != "source sentence" for meta_value in meta_values)


def _ordered_example_meta_values(meta_values: list[str]) -> list[str]:
    source_meta_values: list[str] = []
    other_meta_values: list[str] = []
    for meta_value in meta_values:
        if meta_value.strip().lower() == "source sentence":
            source_meta_values.append(meta_value)
        else:
            other_meta_values.append(meta_value)
    return other_meta_values + source_meta_values


def _extract_primary_pos(meanings: list[str]) -> str | None:
    for meaning in meanings:
        match = re.match(r"^\(([^()]+)\)\s*(.+)$", str(meaning).strip())
        if match is not None:
            return match.group(1).strip()
    return None
