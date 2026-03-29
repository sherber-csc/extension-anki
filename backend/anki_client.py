from __future__ import annotations

import base64
import json
from pathlib import Path
import urllib.error
import urllib.request


class AnkiConnectClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def invoke(self, action: str, params: dict | None = None) -> dict:
        payload = {
            "action": action,
            "version": 6,
            "params": params or {},
        }
        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))

    def is_available(self) -> bool:
        try:
            response = self.invoke("version")
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return False
        return response.get("error") is None

    def find_notes(self, query: str) -> list[int]:
        response = self.invoke("findNotes", {"query": query})
        self._raise_if_error(response, action="findNotes")
        return [int(note_id) for note_id in response.get("result", [])]

    def store_media_file(self, *, filename: str, file_path: str) -> str:
        encoded = base64.b64encode(Path(file_path).read_bytes()).decode("ascii")
        response = self.invoke(
            "storeMediaFile",
            {
                "filename": filename,
                "data": encoded,
            },
        )
        self._raise_if_error(response, action="storeMediaFile")
        return str(response.get("result") or filename)

    def add_note(self, *, note: dict) -> int:
        response = self.invoke("addNote", {"note": note})
        self._raise_if_error(response, action="addNote")
        return int(response.get("result"))

    @staticmethod
    def _raise_if_error(response: dict, *, action: str) -> None:
        error = response.get("error")
        if error:
            raise RuntimeError(f"AnkiConnect {action} failed: {error}")
