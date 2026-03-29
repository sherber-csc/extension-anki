from __future__ import annotations

import json
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
