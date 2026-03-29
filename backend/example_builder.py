from __future__ import annotations


def build_examples(source_sentence: str | None, generated_examples: list[str]) -> list[str]:
    cleaned_generated = [example.strip() for example in generated_examples if str(example).strip()]

    if source_sentence is not None:
        source_text = str(source_sentence).strip()
        if source_text:
            if len(cleaned_generated) < 2:
                raise ValueError("At least two generated examples are required when source_sentence is present.")
            return [
                f"{source_text} (source sentence)",
                cleaned_generated[0],
                cleaned_generated[1],
            ]

    if len(cleaned_generated) < 3:
        raise ValueError("At least three generated examples are required when source_sentence is absent.")

    return cleaned_generated[:3]
