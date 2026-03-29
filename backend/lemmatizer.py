from __future__ import annotations

from backend.schemas import LemmaResult

_IRREGULAR_FORMS: dict[str, str] = {
    "retries": "retry",
    "retried": "retry",
    "retrying": "retry",
}


def lemmatize_word(normalized_form: str) -> LemmaResult:
    text = str(normalized_form).strip().lower()
    if not text:
        raise ValueError("normalized_form must not be empty.")

    lemma = _infer_lemma(text)
    word_key = lemma.strip().lower() or text
    return LemmaResult(normalized_form=text, lemma=lemma, word_key=word_key)


def _infer_lemma(normalized_form: str) -> str:
    irregular = _IRREGULAR_FORMS.get(normalized_form)
    if irregular is not None:
        return irregular

    if normalized_form.endswith("ies") and len(normalized_form) > 3:
        return f"{normalized_form[:-3]}y"

    if normalized_form.endswith("ied") and len(normalized_form) > 3:
        return f"{normalized_form[:-3]}y"

    if normalized_form.endswith("ing") and len(normalized_form) > 4:
        stem = normalized_form[:-3]
        if stem.endswith("y"):
            return stem
        if stem.endswith("e"):
            return stem
        return stem

    if normalized_form.endswith("ed") and len(normalized_form) > 3:
        stem = normalized_form[:-2]
        if stem.endswith("i"):
            return f"{stem[:-1]}y"
        return stem

    return normalized_form
