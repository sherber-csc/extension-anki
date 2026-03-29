from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from backend.anki_client import AnkiConnectClient
from backend.config import AppConfig, DEFAULT_CONFIG
from backend.note_fields import NOTE_TYPE_FIELDS
from backend.schemas import PreflightCheckResult

_NOTE_TYPE_CSS = """
.card {
  font-family: Arial, sans-serif;
  font-size: 18px;
  text-align: left;
  color: #222;
  background: white;
}

.front {
  text-align: center;
}

.front .emoji {
  font-size: 48px;
  margin-bottom: 12px;
}

.front .word {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 12px;
}

.front .ipa {
  font-size: 22px;
  color: #666;
  margin-bottom: 12px;
}

.front .image-prompt {
  font-size: 16px;
  color: #555;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  font-weight: bold;
  margin-bottom: 8px;
}

.forms {
  color: #666;
}
""".strip()

_CARD_TEMPLATES = [
    {
        "Name": "Card 1",
        "Front": """
<div class="front">
  <div class="emoji">{{emoji}}</div>
  <div class="word">{{word}}</div>
  {{#audio}}<div>[sound:{{audio}}]</div>{{/audio}}
  <div class="ipa">{{ipa}}</div>
  <div class="image-prompt">{{image_prompt}}</div>
</div>
""".strip(),
        "Back": """
{{FrontSide}}
<hr id=answer>
<div class="section">
  <div class="section-title">Meaning</div>
  <div>{{meanings}}</div>
</div>
{{#forms}}
<div class="section forms">Forms: {{forms}}</div>
{{/forms}}
<div class="section">
  <div class="section-title">Pair</div>
  <div>{{pairs}}</div>
</div>
<div class="section">
  <div class="section-title">Example</div>
  <div>{{examples}}</div>
</div>
""".strip(),
    }
]


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

    def check_collection_setup(self) -> PreflightCheckResult:
        if not self.is_available():
            return PreflightCheckResult(
                ok=False,
                message="AnkiConnect is not available.",
            )

        try:
            deck_names = self.client.deck_names()
            model_names = self.client.model_names()
        except RuntimeError as exc:
            return PreflightCheckResult(
                ok=False,
                message=f"Failed to inspect Anki collection setup: {exc}",
            )

        if self.config.default_deck_name not in deck_names:
            return PreflightCheckResult(
                ok=False,
                message=f"Missing required deck: {self.config.default_deck_name}.",
            )

        if self.config.default_note_type_name not in model_names:
            return PreflightCheckResult(
                ok=False,
                message=f"Missing required note type: {self.config.default_note_type_name}.",
            )

        try:
            actual_fields = self.client.model_field_names(
                model_name=self.config.default_note_type_name
            )
        except RuntimeError as exc:
            return PreflightCheckResult(
                ok=False,
                message=f"Failed to inspect note type fields: {exc}",
            )

        mismatch_message = self._note_type_field_mismatch_message(actual_fields)
        if mismatch_message is not None:
            return PreflightCheckResult(
                ok=False,
                message=mismatch_message,
            )

        return PreflightCheckResult(
            ok=True,
            message=(
                f"Anki collection setup is ready: deck '{self.config.default_deck_name}' "
                f"and note type '{self.config.default_note_type_name}' are available."
            ),
        )

    def ensure_collection_setup(self) -> None:
        self.ensure_generation_ready()

        deck_names = self.client.deck_names()
        if self.config.default_deck_name not in deck_names:
            self.client.create_deck(deck=self.config.default_deck_name)

        model_names = self.client.model_names()
        if self.config.default_note_type_name not in model_names:
            self.client.create_model(
                model_name=self.config.default_note_type_name,
                in_order_fields=list(NOTE_TYPE_FIELDS),
                css=_NOTE_TYPE_CSS,
                card_templates=_CARD_TEMPLATES,
            )
            return

        actual_fields = self.client.model_field_names(
            model_name=self.config.default_note_type_name
        )
        mismatch_message = self._note_type_field_mismatch_message(actual_fields)
        if mismatch_message is not None:
            raise RuntimeError(mismatch_message)

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

    def _note_type_field_mismatch_message(self, actual_fields: list[str]) -> str | None:
        expected_fields = list(NOTE_TYPE_FIELDS)
        missing_fields = [field for field in expected_fields if field not in actual_fields]
        extra_fields = [field for field in actual_fields if field not in expected_fields]
        if not missing_fields and not extra_fields:
            return None

        differences: list[str] = []
        if missing_fields:
            differences.append(f"missing fields: {', '.join(missing_fields)}")
        if extra_fields:
            differences.append(f"extra fields: {', '.join(extra_fields)}")

        joined_differences = "; ".join(differences)
        return (
            f"Note type '{self.config.default_note_type_name}' fields mismatch: "
            f"{joined_differences}."
        )
