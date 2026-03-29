from __future__ import annotations


def build_examples(source_sentence: str | None, generated_examples: list[str]) -> list[str]:
    cleaned_generated = [example.strip() for example in generated_examples if str(example).strip()]

    if source_sentence is not None:
        source_text = str(source_sentence).strip()
        examples: list[str] = []
        if source_text:
            examples.append(f"{source_text} (source sentence)")
        examples.extend(cleaned_generated[: 3 - len(examples)])
        return examples[:3]

    return cleaned_generated[:3]
