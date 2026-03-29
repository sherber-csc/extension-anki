from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

from backend.schemas import GeneratedNoteContent, PreflightCheckResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You generate structured vocabulary card content for a single English word.
Return only one strict JSON object with these keys:
- word: string
- ipa: string
- emoji: string
- image_prompt: string
- meanings: array of strings
- pairs: array of strings
- examples: array of strings

Rules:
- meanings must be English-only and concise.
- pairs must be concise useful collocations.
- examples must contain exactly 3 generated example sentences.
- Do not wrap the JSON in markdown fences.
- Do not include any keys beyond the required keys.
"""


class LLMClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        request_timeout_seconds: int | None = None,
    ) -> None:
        env_file_values = _load_project_env_file()
        self.api_key = api_key if api_key is not None else (os.getenv("LLM_API_KEY") or env_file_values.get("LLM_API_KEY"))
        self.base_url = base_url if base_url is not None else (os.getenv("LLM_BASE_URL") or env_file_values.get("LLM_BASE_URL"))
        self.model = model if model is not None else (os.getenv("LLM_MODEL") or env_file_values.get("LLM_MODEL") or "MiniMax-M2.1")
        self.request_timeout_seconds = _resolve_request_timeout_seconds(
            request_timeout_seconds=request_timeout_seconds,
            env_value=os.getenv("LLM_REQUEST_TIMEOUT_SECONDS") or env_file_values.get("LLM_REQUEST_TIMEOUT_SECONDS"),
        )

    def preflight_check(self) -> PreflightCheckResult:
        missing_fields: list[str] = []
        if not str(self.api_key or "").strip():
            missing_fields.append("LLM_API_KEY")
        if not str(self.base_url or "").strip():
            missing_fields.append("LLM_BASE_URL")

        if missing_fields:
            return PreflightCheckResult(
                ok=False,
                message=f"Missing required LLM config: {', '.join(missing_fields)}.",
            )

        return PreflightCheckResult(
            ok=True,
            message="Required LLM config is available.",
        )

    def generate_note_content(self, *, word: str, source_sentence: str | None = None) -> GeneratedNoteContent:
        self._ensure_runtime_config()

        request_body = self._build_request_body(word=word, source_sentence=source_sentence)

        request = urllib.request.Request(
            self._chat_completion_url(),
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.request_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"llm request failed after timeout={self.request_timeout_seconds}s: "
                f"HTTP {exc.code} {detail}".strip()
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise RuntimeError(
                f"llm request failed after timeout={self.request_timeout_seconds}s: {exc}"
            ) from exc

        content_text = self._extract_content_text(payload)
        data = self._parse_response_json(content_text)
        return self._validate_generated_content(data)

    def _ensure_runtime_config(self) -> None:
        missing_fields: list[str] = []
        if not str(self.api_key or "").strip():
            missing_fields.append("LLM_API_KEY")
        if not str(self.base_url or "").strip():
            missing_fields.append("LLM_BASE_URL")
        if missing_fields:
            raise RuntimeError(f"llm config missing: {', '.join(missing_fields)}")

    def _chat_completion_url(self) -> str:
        base = str(self.base_url).rstrip("/")
        if "chatcompletion_v2" in base:
            return base
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/chat/completions"

    def _build_request_body(self, *, word: str, source_sentence: str | None) -> dict:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": self._build_user_prompt(word=word, source_sentence=source_sentence),
            },
        ]
        if "chatcompletion_v2" in self._chat_completion_url():
            return {
                "model": self.model,
                "messages": [
                    {"role": "system", "name": "MiniMax AI", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "name": "用户",
                        "content": self._build_user_prompt(word=word, source_sentence=source_sentence),
                    },
                ],
                "reasoning_split": True,
            }
        return {
            "model": self.model,
            "messages": messages,
            "temperature": 0.4,
            "reasoning_split": True,
        }

    @staticmethod
    def _build_user_prompt(*, word: str, source_sentence: str | None) -> str:
        source_line = source_sentence.strip() if source_sentence else ""
        return "\n".join(
            (
                f"word: {word}",
                f"source_sentence: {source_line or '(none)'}",
                "Use the source sentence only as context for sense disambiguation.",
                "Do not copy the source sentence into the examples array.",
            )
        )

    @staticmethod
    def _extract_content_text(payload: dict) -> str:
        try:
            choices = payload["choices"]
            message = choices[0]["message"]
            content = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("llm response invalid: missing choices[0].message.content") from exc

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(str(item.get("text", "")))
            merged = "".join(text_parts).strip()
            if merged:
                return merged

        raise RuntimeError("llm response invalid: unsupported content format")

    @staticmethod
    def _parse_response_json(content_text: str) -> dict:
        text = _strip_think_blocks(content_text).strip()
        text = _strip_fenced_code_blocks(text).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            try:
                extracted = _extract_first_json_object(text)
            except ValueError:
                logger.error("LLM raw message.content that failed JSON parse:\n%s", content_text)
                raise RuntimeError(f"llm response invalid: JSON parse failed: {exc}") from exc

            try:
                return json.loads(extracted)
            except json.JSONDecodeError as nested_exc:
                logger.error("LLM raw message.content that failed JSON parse:\n%s", content_text)
                raise RuntimeError(
                    f"llm response invalid: JSON parse failed: {nested_exc}"
                ) from nested_exc

    @staticmethod
    def _validate_generated_content(data: dict) -> GeneratedNoteContent:
        required_string_fields = ("word", "ipa", "emoji", "image_prompt")
        required_list_fields = ("meanings", "pairs", "examples")

        for field_name in required_string_fields:
            value = data.get(field_name)
            if not isinstance(value, str) or not value.strip():
                raise RuntimeError(f"llm response invalid: missing or empty string field '{field_name}'")

        for field_name in required_list_fields:
            value = data.get(field_name)
            if not isinstance(value, list) or not value:
                raise RuntimeError(f"llm response invalid: missing or empty list field '{field_name}'")

        meanings = [str(item).strip() for item in data["meanings"] if str(item).strip()]
        pairs = [str(item).strip() for item in data["pairs"] if str(item).strip()]
        examples = [str(item).strip() for item in data["examples"] if str(item).strip()]

        if len(examples) < 3:
            raise RuntimeError("llm response invalid: examples must contain at least 3 items")

        return GeneratedNoteContent(
            word=str(data["word"]).strip(),
            ipa=str(data["ipa"]).strip(),
            emoji=str(data["emoji"]).strip(),
            image_prompt=str(data["image_prompt"]).strip(),
            meanings=meanings,
            pairs=pairs,
            examples=examples,
        )


def _load_project_env_file() -> dict[str, str]:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _resolve_request_timeout_seconds(
    *,
    request_timeout_seconds: int | None,
    env_value: str | None,
) -> int:
    default_timeout_seconds = 180
    if request_timeout_seconds is not None and request_timeout_seconds > 0:
        return request_timeout_seconds

    if env_value is None:
        return default_timeout_seconds

    try:
        parsed_timeout_seconds = int(str(env_value).strip())
    except (TypeError, ValueError):
        return default_timeout_seconds

    if parsed_timeout_seconds <= 0:
        return default_timeout_seconds

    return parsed_timeout_seconds


def _strip_think_blocks(text: str) -> str:
    return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL)


def _strip_fenced_code_blocks(text: str) -> str:
    if "```" not in text:
        return text

    cleaned_lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _extract_first_json_object(text: str) -> str:
    candidate_start = text.find("{")
    if candidate_start == -1:
        raise ValueError("no JSON object found")

    depth = 0
    in_string = False
    escape = False
    candidate_end: int | None = None

    for index in range(candidate_start, len(text)):
        char = text[index]

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            depth += 1
            continue

        if char == "}":
            depth -= 1
            if depth < 0:
                raise ValueError("invalid JSON object structure")
            if depth == 0:
                candidate_end = index + 1
                break

    if candidate_end is None or depth != 0:
        raise ValueError("no complete top-level JSON object found")

    candidate = text[candidate_start:candidate_end]
    if not candidate.startswith("{") or not candidate.endswith("}"):
        raise ValueError("invalid top-level JSON object")

    trailing_text = text[candidate_end:].lstrip()
    if trailing_text.startswith(("{", "[", '"', "-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "true", "false", "null")):
        raise ValueError("multiple JSON values detected")

    return candidate
