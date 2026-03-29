from __future__ import annotations


class LLMClient:
    def generate_note_content(self, word: str) -> dict:
        raise NotImplementedError("LLM generation is implemented in a later phase.")
