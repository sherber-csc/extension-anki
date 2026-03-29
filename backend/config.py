from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    default_deck_name: str = "sherber"
    default_note_type_name: str = "SherberVocabNote"
    default_generator_version: str = "v1"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8766
    capture_endpoint: str = "/api/captures"
    health_endpoint: str = "/health"
    database_path: Path = Path("data/queue.db")
    anki_connect_url: str = "http://127.0.0.1:8765"
    audio_output_dir: Path = Path("data/audio")


DEFAULT_CONFIG = AppConfig()
