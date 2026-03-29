from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.contracts import render_extension_protocol_js


def sync_protocol(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_extension_protocol_js(), encoding="utf-8")


if __name__ == "__main__":
    sync_protocol(Path("extension/protocol.js"))
