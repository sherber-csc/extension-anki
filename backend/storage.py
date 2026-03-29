from __future__ import annotations

import sqlite3
from pathlib import Path


class SQLiteStorage:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS queue_records (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    surface_form TEXT NOT NULL,
                    normalized_form TEXT NOT NULL,
                    lemma TEXT NOT NULL,
                    word_key TEXT NOT NULL,
                    source_sentence TEXT,
                    source_title TEXT,
                    source_url TEXT,
                    source_type TEXT NOT NULL,
                    source_timestamp TEXT,
                    captured_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT NOT NULL DEFAULT '',
                    generator_version TEXT NOT NULL
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_queue_pending_word_key
                ON queue_records(word_key)
                WHERE status = 'pending';

                CREATE INDEX IF NOT EXISTS idx_queue_status
                ON queue_records(status);
                """
            )
