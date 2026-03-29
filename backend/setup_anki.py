from __future__ import annotations

from backend.anki_client import AnkiConnectClient
from backend.anki_service import AnkiService
from backend.config import DEFAULT_CONFIG


def main() -> None:
    service = AnkiService(
        AnkiConnectClient(DEFAULT_CONFIG.anki_connect_url),
        config=DEFAULT_CONFIG,
    )
    service.ensure_collection_setup()
    print(
        (
            f"Anki setup is ready: deck '{DEFAULT_CONFIG.default_deck_name}' and "
            f"note type '{DEFAULT_CONFIG.default_note_type_name}' are available."
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
