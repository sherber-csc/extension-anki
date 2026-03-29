from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from backend.anki_client import AnkiConnectClient
from backend.anki_service import AnkiService
from backend.capture_service import CaptureService
from backend.config import AppConfig, DEFAULT_CONFIG
from backend.contracts import RESPONSE_STATUS_TEXTS
from backend.lemmatizer import lemmatize_word
from backend.normalization import normalize_surface_form
from backend.queue_manager import QueueManager
from backend.queue_repository import QueueRepository
from backend.storage import SQLiteStorage


@dataclass
class AppContext:
    config: AppConfig
    capture_service: CaptureService


def build_app_context(config: AppConfig = DEFAULT_CONFIG) -> AppContext:
    storage = SQLiteStorage(Path(config.database_path))
    storage.initialize()

    queue_manager = QueueManager(
        QueueRepository(storage),
        generator_version=config.default_generator_version,
    )
    anki_service = AnkiService(AnkiConnectClient(config.anki_connect_url))
    capture_service = CaptureService(
        queue_manager=queue_manager,
        anki_service=anki_service,
        normalize_surface_form=normalize_surface_form,
        lemmatize_word=lemmatize_word,
    )
    return AppContext(config=config, capture_service=capture_service)


def create_handler(context: AppContext):
    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path != context.config.health_endpoint:
                self._send_json(HTTPStatus.NOT_FOUND, {"status": "not_found"})
                return
            self._send_json(HTTPStatus.OK, {"status": "ok"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path != context.config.capture_endpoint:
                self._send_json(HTTPStatus.NOT_FOUND, {"status": "not_found"})
                return

            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "status": "invalid_input",
                        "message": "Only single English words are supported.",
                    },
                )
                return

            response = context.capture_service.capture(payload)
            status_code = HTTPStatus.OK
            if response.status == "invalid_input":
                status_code = HTTPStatus.BAD_REQUEST

            response_payload = response.to_dict()
            if response_payload.get("message") is None:
                response_payload["message"] = RESPONSE_STATUS_TEXTS.get(response.status)
            self._send_json(status_code, response_payload)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _send_json(self, status_code: HTTPStatus, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return RequestHandler


def run_server(config: AppConfig = DEFAULT_CONFIG) -> None:
    context = build_app_context(config)
    server = ThreadingHTTPServer((config.backend_host, config.backend_port), create_handler(context))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
