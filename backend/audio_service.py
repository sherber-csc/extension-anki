from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from backend.schemas import GeneratedAudio, PreflightCheckResult


class AudioService:
    def __init__(self, *, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)

    def preflight_check(self) -> PreflightCheckResult:
        shell = self._resolve_shell()
        if shell is None:
            return PreflightCheckResult(
                ok=False,
                message="Missing required audio dependency: PowerShell.",
            )

        if not str(self.output_dir).strip():
            return PreflightCheckResult(
                ok=False,
                message="Missing required audio config: output directory.",
            )

        target_dir = self.output_dir
        writable_target = target_dir if target_dir.exists() else target_dir.parent

        if not writable_target.exists():
            return PreflightCheckResult(
                ok=False,
                message=f"Audio output parent directory does not exist: {writable_target}.",
            )

        if not writable_target.is_dir():
            return PreflightCheckResult(
                ok=False,
                message=f"Audio output path is not a directory: {writable_target}.",
            )

        if not self._is_writable(writable_target):
            return PreflightCheckResult(
                ok=False,
                message=f"Audio output directory is not writable: {writable_target}.",
            )

        return PreflightCheckResult(
            ok=True,
            message=f"Audio dependency is available via {shell} and output directory is writable: {target_dir}.",
        )

    def generate_audio(self, word: str) -> GeneratedAudio:
        shell = self._resolve_shell()
        if shell is None:
            raise RuntimeError("audio generation failed: PowerShell is not available.")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self._slugify(word)}_anki_audio.wav"
        file_path = self.output_dir / filename
        script = self._build_powershell_script(text=word, output_path=file_path)

        try:
            completed = subprocess.run(
                [shell, "-NoProfile", "-Command", script],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            raise RuntimeError(f"audio generation failed: {exc}") from exc

        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown PowerShell error"
            raise RuntimeError(f"audio generation failed: {stderr}")

        if not file_path.exists():
            raise RuntimeError("audio generation failed: output file was not created.")

        return GeneratedAudio(filename=filename, file_path=str(file_path))

    @staticmethod
    def _resolve_shell() -> str | None:
        return shutil.which("powershell") or shutil.which("pwsh")

    @staticmethod
    def _is_writable(path: Path) -> bool:
        return os.access(path, os.W_OK)

    @staticmethod
    def _slugify(word: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", word.strip().lower()).strip("_")
        return cleaned or "audio"

    @staticmethod
    def _build_powershell_script(*, text: str, output_path: Path) -> str:
        escaped_text = text.replace("'", "''")
        escaped_path = str(output_path).replace("'", "''")
        return (
            "Add-Type -AssemblyName System.Speech; "
            "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.SetOutputToWaveFile('{escaped_path}'); "
            f"$synth.Speak('{escaped_text}'); "
            "$synth.Dispose();"
        )
