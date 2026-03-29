from __future__ import annotations


def build_forms(lemma: str, *, is_verb: bool) -> str:
    if not is_verb:
        return ""

    lemma = lemma.strip().lower()
    if not lemma:
        return ""

    third_person = _to_third_person_singular(lemma)
    past = _to_past_tense(lemma)
    present_participle = _to_present_participle(lemma)
    return " / ".join((third_person, past, present_participle))


def _to_third_person_singular(lemma: str) -> str:
    if lemma.endswith("y") and len(lemma) > 1 and lemma[-2] not in "aeiou":
        return f"{lemma[:-1]}ies"
    if lemma.endswith(("s", "sh", "ch", "x", "z", "o")):
        return f"{lemma}es"
    return f"{lemma}s"


def _to_past_tense(lemma: str) -> str:
    if lemma.endswith("e"):
        return f"{lemma}d"
    if lemma.endswith("y") and len(lemma) > 1 and lemma[-2] not in "aeiou":
        return f"{lemma[:-1]}ied"
    return f"{lemma}ed"


def _to_present_participle(lemma: str) -> str:
    if lemma.endswith("ie"):
        return f"{lemma[:-2]}ying"
    if lemma.endswith("e") and not lemma.endswith("ee"):
        return f"{lemma[:-1]}ing"
    return f"{lemma}ing"
