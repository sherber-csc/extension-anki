from __future__ import annotations

from backend.schemas import GenerationPreflightResponse, PreflightCheckResult


class GenerationPreflightService:
    def __init__(self, *, anki_service, llm_client, audio_service) -> None:
        self.anki_service = anki_service
        self.llm_client = llm_client
        self.audio_service = audio_service

    def check(self) -> GenerationPreflightResponse:
        checks = {
            "anki": self._anki_check(),
            "llm": self.llm_client.preflight_check(),
            "audio": self.audio_service.preflight_check(),
        }
        passed_count = sum(1 for result in checks.values() if result.ok)
        total_count = len(checks)
        status = "ready" if passed_count == total_count else "not_ready"
        return GenerationPreflightResponse(
            status=status,
            summary=f"{passed_count} of {total_count} checks passed.",
            checks=checks,
        )

    def _anki_check(self) -> PreflightCheckResult:
        if self.anki_service.is_available():
            return PreflightCheckResult(
                ok=True,
                message="AnkiConnect is available.",
            )
        return PreflightCheckResult(
            ok=False,
            message="AnkiConnect is not available.",
        )
