from __future__ import annotations


class NoteMapper:
    def map_note_fields(self, payload: dict) -> dict:
        raise NotImplementedError("Note mapping is implemented in a later phase.")
