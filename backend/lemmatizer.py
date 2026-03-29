from __future__ import annotations

import logging

from backend.lemma_overrides import get_lemma_override
from backend.schemas import LemmaResult

try:  # pragma: no cover - import availability depends on local env
    from nltk.stem import WordNetLemmatizer as NLTKWordNetLemmatizer
except ImportError:  # pragma: no cover - import availability depends on local env
    NLTKWordNetLemmatizer = None

logger = logging.getLogger(__name__)

_wordnet_lemmatizer = None


def lemmatize_word(normalized_form: str) -> LemmaResult:
    text = str(normalized_form).strip().lower()
    if not text:
        raise ValueError("normalized_form must not be empty.")

    lemma = _infer_lemma(text)
    word_key = lemma.strip().lower() or text
    return LemmaResult(normalized_form=text, lemma=lemma, word_key=word_key)


def _infer_lemma(normalized_form: str) -> str:
    override = get_lemma_override(normalized_form)
    if override is not None:
        return override

    if _looks_like_inflected_verb_form(normalized_form):
        candidate = _infer_with_wordnet(normalized_form, pos="v")
        if _is_acceptable_verb_wordnet_result(normalized_form, candidate):
            return candidate

    if _looks_like_plural_noun_candidate(normalized_form):
        candidate = _infer_with_wordnet(normalized_form, pos="n")
        if _is_acceptable_noun_wordnet_result(normalized_form, candidate):
            return candidate

    return normalized_form


def _looks_like_inflected_verb_form(normalized_form: str) -> bool:
    text = str(normalized_form).strip().lower()
    if text.endswith("ied") and len(text) > 3:
        return True
    if text.endswith("ies") and len(text) > 3:
        return True
    if text.endswith("ing") and len(text) > 4:
        return True
    if text.endswith("ed") and len(text) > 3:
        return True
    return False


def _looks_like_plural_noun_candidate(normalized_form: str) -> bool:
    text = str(normalized_form).strip().lower()
    if len(text) < 4:
        return False
    if not text.endswith("s"):
        return False
    if _looks_like_inflected_verb_form(text):
        return False
    return True


def _infer_with_wordnet(normalized_form: str, *, pos: str) -> str | None:
    lemmatizer = _get_wordnet_lemmatizer()
    if lemmatizer is None:
        return None

    try:
        candidate = str(lemmatizer.lemmatize(normalized_form, pos=pos)).strip().lower()
    except LookupError as exc:  # pragma: no cover - depends on local nltk data
        logger.warning("wordnet corpus unavailable for lemmatizer: %s", exc)
        return None

    return candidate or None


def _get_wordnet_lemmatizer():
    global _wordnet_lemmatizer
    if NLTKWordNetLemmatizer is None:
        return None
    if _wordnet_lemmatizer is None:
        _wordnet_lemmatizer = NLTKWordNetLemmatizer()
    return _wordnet_lemmatizer


def _is_acceptable_verb_wordnet_result(original_word: str, candidate: str | None) -> bool:
    if candidate is None:
        return False
    text = str(candidate).strip().lower()
    if not text:
        return False
    if not text.isalpha():
        return False
    if len(text) < 3:
        return False
    if text == original_word:
        return True
    return len(text) <= len(original_word)


def _is_acceptable_noun_wordnet_result(original_word: str, candidate: str | None) -> bool:
    if candidate is None:
        return False

    text = str(candidate).strip().lower()
    if not text:
        return False
    if not text.isalpha():
        return False
    if len(text) < 3:
        return False
    return original_word == f"{text}s"
