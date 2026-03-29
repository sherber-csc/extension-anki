from __future__ import annotations

from backend.anki_client import AnkiConnectClient


class AnkiService:
    def __init__(self, client: AnkiConnectClient) -> None:
        self.client = client

    def is_available(self) -> bool:
        return self.client.is_available()

    def contains_word_key(self, word_key: str) -> bool:
        # Batch generation and full Anki duplicate logic are implemented later.
        # During the first phase, the capture flow only queries Anki when this
        # service reports availability, and defaults to "not found".
        _ = word_key
        return False
