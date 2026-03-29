from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from backend.anki_client import AnkiConnectClient
from backend.anki_service import AnkiService
from backend.audio_service import AudioService
from backend.capture_service import CaptureService
from backend.config import AppConfig, DEFAULT_CONFIG
from backend.contracts import (
    GENERATE_PENDING_ENDPOINT,
    GENERATION_PREFLIGHT_ENDPOINT,
    QUEUE_ENDPOINT,
    RESPONSE_STATUS_TEXTS,
)
from backend.generation_preflight import GenerationPreflightService
from backend.generation_service import GenerationService
from backend.lemmatizer import lemmatize_word
from backend.llm_client import LLMClient
from backend.note_mapper import NoteMapper
from backend.normalization import normalize_surface_form
from backend.queue_manager import QueueManager
from backend.queue_repository import QueueRepository
from backend.single_generation_service import SingleGenerationService
from backend.storage import SQLiteStorage
from backend.example_builder import build_examples
from backend.forms_builder import build_forms


@dataclass
class AppContext:
    config: AppConfig
    capture_service: CaptureService
    queue_manager: QueueManager
    generation_service: GenerationService
    generation_preflight_service: GenerationPreflightService


def build_app_context(config: AppConfig = DEFAULT_CONFIG) -> AppContext:
    storage = SQLiteStorage(Path(config.database_path))
    storage.initialize()

    queue_manager = QueueManager(
        QueueRepository(storage),
        generator_version=config.default_generator_version,
    )
    anki_service = AnkiService(AnkiConnectClient(config.anki_connect_url))
    llm_client = LLMClient()
    audio_service = AudioService(output_dir=config.audio_output_dir)
    note_mapper = NoteMapper()
    capture_service = CaptureService(
        queue_manager=queue_manager,
        anki_service=anki_service,
        normalize_surface_form=normalize_surface_form,
        lemmatize_word=lemmatize_word,
    )
    single_generation_service = SingleGenerationService(
        llm_client=llm_client,
        audio_service=audio_service,
        note_mapper=note_mapper,
        anki_service=anki_service,
        build_examples=build_examples,
        build_forms=build_forms,
    )
    generation_service = GenerationService(
        queue_manager=queue_manager,
        single_generation_service=single_generation_service,
    )
    generation_preflight_service = GenerationPreflightService(
        anki_service=anki_service,
        llm_client=llm_client,
        audio_service=audio_service,
    )
    return AppContext(
        config=config,
        capture_service=capture_service,
        queue_manager=queue_manager,
        generation_service=generation_service,
        generation_preflight_service=generation_preflight_service,
    )


def create_handler(context: AppContext):
    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == context.config.health_endpoint:
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return

            if self.path == QUEUE_ENDPOINT:
                items = [
                    {
                        "record_id": record.record_id,
                        "surface_form": record.surface_form,
                        "lemma": record.lemma,
                        "word_key": record.word_key,
                        "status": record.status,
                        "captured_at": record.captured_at,
                    }
                    for record in context.queue_manager.list_recent(limit=50)
                ]
                self._send_json(HTTPStatus.OK, {"items": items})
                return

            if self.path == GENERATION_PREFLIGHT_ENDPOINT:
                payload = context.generation_preflight_service.check().to_dict()
                self._send_json(HTTPStatus.OK, payload)
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"status": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path == GENERATE_PENDING_ENDPOINT:
                response_payload = context.generation_service.generate_pending().to_dict()
                self._send_json(HTTPStatus.OK, response_payload)
                return

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
    print(f"Backend listening on http://{config.backend_host}:{config.backend_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
