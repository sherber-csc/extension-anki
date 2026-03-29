from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from backend.anki_client import AnkiConnectClient
from backend.config import AppConfig, DEFAULT_CONFIG


class AnkiService:
    def __init__(self, client: AnkiConnectClient, config: AppConfig = DEFAULT_CONFIG) -> None:
        self.client = client
        self.config = config

    def is_available(self) -> bool:
        return self.client.is_available()

    def ensure_generation_ready(self) -> None:
        if self.is_available():
            return

        if not self._attempt_start_anki():
            raise RuntimeError(
                "anki unavailable: AnkiConnect is not available and Anki could not be started."
            )

        deadline = time.time() + 15
        while time.time() < deadline:
            if self.is_available():
                return
            time.sleep(1)

        raise RuntimeError(
            "anki unavailable: Anki was started, but AnkiConnect did not become available in time."
        )

    def contains_word_key(self, word_key: str) -> bool:
        query = f'note:"{self.config.default_note_type_name}" word_key:{word_key}'
        try:
            note_ids = self.client.find_notes(query)
        except RuntimeError as exc:
            raise RuntimeError(f"anki write failed: {exc}") from exc
        return bool(note_ids)

    def write_note(self, *, word_key: str, note_fields: dict[str, str], audio_file_path: str | None = None) -> int:
        if self.contains_word_key(word_key):
            raise RuntimeError(f"anki write failed: word_key '{word_key}' already exists in Anki.")

        if audio_file_path:
            audio_filename = note_fields.get("audio", "").strip()
            if not audio_filename:
                raise RuntimeError("anki write failed: audio filename is missing from note fields.")
            try:
                self.client.store_media_file(filename=audio_filename, file_path=audio_file_path)
            except RuntimeError as exc:
                raise RuntimeError(f"anki write failed: {exc}") from exc

        note = {
            "deckName": self.config.default_deck_name,
            "modelName": self.config.default_note_type_name,
            "fields": note_fields,
        }
        try:
            return self.client.add_note(note=note)
        except RuntimeError as exc:
            raise RuntimeError(f"anki write failed: {exc}") from exc

    def _attempt_start_anki(self) -> bool:
        for candidate in self._anki_launch_candidates():
            try:
                subprocess.Popen([candidate], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except OSError:
                continue
        return False

    @staticmethod
    def _anki_launch_candidates() -> list[str]:
        candidates: list[str] = []
        env_path = str(os.getenv("ANKI_EXE_PATH") or "").strip()
        if env_path:
            candidates.append(env_path)

        which_path = shutil.which("anki")
        if which_path:
            candidates.append(which_path)

        common_paths = (
            Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "Anki" / "anki.exe",
            Path("C:/Program Files/Anki/anki.exe"),
            Path("C:/Program Files (x86)/Anki/anki.exe"),
        )
        for path in common_paths:
            if str(path) and path.exists():
                candidates.append(str(path))

        seen: set[str] = set()
        deduped: list[str] = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                deduped.append(candidate)
        return deduped
