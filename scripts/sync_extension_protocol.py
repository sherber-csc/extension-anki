from __future__ import annotations

from pathlib import Path

from backend.contracts import render_extension_protocol_js


def sync_protocol(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_extension_protocol_js(), encoding="utf-8")


if __name__ == "__main__":
    sync_protocol(Path("extension/protocol.js"))
