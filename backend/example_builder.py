from __future__ import annotations

import re


_SOURCE_SENTENCE_META_PATTERN = re.compile(r"^\(source sentence\)\s+\([a-z][a-z_-]*\)$")
_EXAMPLE_WITH_POS_PATTERN = re.compile(r"^.+\s+\([a-z][a-z_-]*\)$")


def build_examples(source_sentence: str | None, generated_examples: list[str]) -> list[str]:
    cleaned_generated = [example.strip() for example in generated_examples if str(example).strip()]

    if source_sentence is not None:
        source_text = str(source_sentence).strip()
        if len(cleaned_generated) < 3:
            raise ValueError("generated_examples must contain at least 3 items")
        if _SOURCE_SENTENCE_META_PATTERN.match(cleaned_generated[0]) is None:
            raise ValueError("generated_examples[0] must match '(source sentence) (<pos>)'")
        if _EXAMPLE_WITH_POS_PATTERN.match(cleaned_generated[1]) is None:
            raise ValueError("generated_examples[1] must match '<sentence> (<pos>)'")
        if _EXAMPLE_WITH_POS_PATTERN.match(cleaned_generated[2]) is None:
            raise ValueError("generated_examples[2] must match '<sentence> (<pos>)'")

        examples: list[str] = []
        if source_text:
            examples.append(f"{source_text} {cleaned_generated[0]}")
        else:
            examples.append(cleaned_generated[0])
        examples.extend(cleaned_generated[1:3])
        return examples

    if len(cleaned_generated) < 3:
        raise ValueError("generated_examples must contain at least 3 items")
    for index in range(3):
        if _EXAMPLE_WITH_POS_PATTERN.match(cleaned_generated[index]) is None:
            raise ValueError(f"generated_examples[{index}] must match '<sentence> (<pos>)'")
    return cleaned_generated[:3]
