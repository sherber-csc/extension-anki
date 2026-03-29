from __future__ import annotations

import unittest

from backend.llm_client import LLMClient


class LLMClientValidationTestCase(unittest.TestCase):
    def test_accepts_strict_format_when_source_sentence_present(self) -> None:
        result = LLMClient._validate_generated_content(
            {
                "word": "retry",
                "ipa": "/riːˈtraɪ/",
                "emoji": "retry-emoji",
                "image_prompt": "retry prompt",
                "meanings": [
                    "(verb) to attempt something again after failing",
                    "(noun) an act of trying something again",
                ],
                "pairs": [
                    "retry the password (重新输入密码)",
                    "retry the operation (重试操作)",
                    "max retry attempts (最大重试次数)",
                ],
                "examples": [
                    "(source sentence) (verb)",
                    "The system allows three retry attempts before locking the account. (noun)",
                    "Please retry the download if it doesn't start automatically. (verb)",
                ],
            },
            has_source_sentence=True,
        )

        self.assertEqual("(source sentence) (verb)", result.examples[0])

    def test_rejects_invalid_meaning_with_indexed_error(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            r"meanings\[1\] must match '\(<pos>\) <meaning>'",
        ):
            LLMClient._validate_generated_content(
                {
                    "word": "retry",
                    "ipa": "/riːˈtraɪ/",
                    "emoji": "retry-emoji",
                    "image_prompt": "retry prompt",
                    "meanings": [
                        "(verb) to attempt something again after failing",
                        "an act of trying something again",
                    ],
                    "pairs": [
                        "retry the password (重新输入密码)",
                        "retry the operation (重试操作)",
                        "max retry attempts (最大重试次数)",
                    ],
                    "examples": [
                        "(source sentence) (verb)",
                        "The system allows three retry attempts before locking the account. (noun)",
                        "Please retry the download if it doesn't start automatically. (verb)",
                    ],
                },
                has_source_sentence=True,
            )

    def test_rejects_invalid_pair_with_indexed_error(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            r"pairs\[2\] must match '<english> \(<zh>\)'",
        ):
            LLMClient._validate_generated_content(
                {
                    "word": "retry",
                    "ipa": "/riːˈtraɪ/",
                    "emoji": "retry-emoji",
                    "image_prompt": "retry prompt",
                    "meanings": [
                        "(verb) to attempt something again after failing",
                        "(noun) an act of trying something again",
                    ],
                    "pairs": [
                        "retry the password (重新输入密码)",
                        "retry the operation (重试操作)",
                        "max retry attempts",
                    ],
                    "examples": [
                        "(source sentence) (verb)",
                        "The system allows three retry attempts before locking the account. (noun)",
                        "Please retry the download if it doesn't start automatically. (verb)",
                    ],
                },
                has_source_sentence=True,
            )

    def test_rejects_invalid_examples_zero_when_source_sentence_present(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            r"examples\[0\] must match '\(source sentence\) \(<pos>\)'",
        ):
            LLMClient._validate_generated_content(
                {
                    "word": "retry",
                    "ipa": "/riːˈtraɪ/",
                    "emoji": "retry-emoji",
                    "image_prompt": "retry prompt",
                    "meanings": [
                        "(verb) to attempt something again after failing",
                        "(noun) an act of trying something again",
                    ],
                    "pairs": [
                        "retry the password (重新输入密码)",
                        "retry the operation (重试操作)",
                        "max retry attempts (最大重试次数)",
                    ],
                    "examples": [
                        "Please retry the download if it doesn't start automatically. (verb)",
                        "The system allows three retry attempts before locking the account. (noun)",
                        "Please retry the download if it doesn't start automatically. (verb)",
                    ],
                },
                has_source_sentence=True,
            )

    def test_rejects_meta_only_example_when_source_sentence_missing(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            r"examples\[0\] must match '<sentence> \(<pos>\)'",
        ):
            LLMClient._validate_generated_content(
                {
                    "word": "retry",
                    "ipa": "/riːˈtraɪ/",
                    "emoji": "retry-emoji",
                    "image_prompt": "retry prompt",
                    "meanings": [
                        "(verb) to attempt something again after failing",
                        "(noun) an act of trying something again",
                    ],
                    "pairs": [
                        "retry the password (重新输入密码)",
                        "retry the operation (重试操作)",
                        "max retry attempts (最大重试次数)",
                    ],
                    "examples": [
                        "(source sentence) (verb)",
                        "The system allows three retry attempts before locking the account. (noun)",
                        "Please retry the download if it doesn't start automatically. (verb)",
                    ],
                },
                has_source_sentence=False,
            )


if __name__ == "__main__":
    unittest.main()
