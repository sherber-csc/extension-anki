from __future__ import annotations

LEMMA_OVERRIDES: dict[str, str] = {
    "organised": "organise",
    "organising": "organise",
    "organises": "organise",
    "practised": "practise",
    "practising": "practise",
    "practises": "practise",
    "revises": "revise",
    "retried": "retry",
    "retrying": "retry",
    "retries": "retry",
}


def get_lemma_override(normalized_form: str) -> str | None:
    return LEMMA_OVERRIDES.get(str(normalized_form).strip().lower())
