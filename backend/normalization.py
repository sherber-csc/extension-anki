from __future__ import annotations

import re
import string

from backend.schemas import NormalizationResult

_LEADING_TRAILING_PUNCTUATION = string.punctuation + "“”‘’"
_SURFACE_FORM_PATTERN = re.compile(r"^[a-z]+$")


def normalize_surface_form(surface_form: str) -> NormalizationResult:
    if surface_form is None:
        raise ValueError("Only single English words are supported.")

    text = str(surface_form).strip().strip(_LEADING_TRAILING_PUNCTUATION).strip().lower()
    if not text or not _SURFACE_FORM_PATTERN.fullmatch(text):
        raise ValueError("Only single English words are supported.")

    return NormalizationResult(surface_form=str(surface_form), normalized_form=text)
