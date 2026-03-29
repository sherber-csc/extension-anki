from __future__ import annotations

import unittest

from backend.example_builder import build_examples


class ExampleBuilderTestCase(unittest.TestCase):
    def test_places_source_sentence_at_examples_zero(self) -> None:
        examples = build_examples(
            "Please retry the download if it doesn't start automatically.",
            [
                "(source sentence) (verb)",
                "I retried the task after fixing the error. (verb)",
                "You can retry the operation later. (verb)",
                "She will retry the process tomorrow. (verb)",
            ],
        )

        self.assertEqual(
            [
                "Please retry the download if it doesn't start automatically. (source sentence) (verb)",
                "I retried the task after fixing the error. (verb)",
                "You can retry the operation later. (verb)",
            ],
            examples,
        )

    def test_uses_only_generated_examples_when_source_sentence_missing(self) -> None:
        examples = build_examples(
            None,
            [
                "I retried the task after fixing the error. (verb)",
                "You can retry the operation later. (verb)",
                "She will retry the process tomorrow. (verb)",
                "This extra example should be ignored. (verb)",
            ],
        )

        self.assertEqual(
            [
                "I retried the task after fixing the error. (verb)",
                "You can retry the operation later. (verb)",
                "She will retry the process tomorrow. (verb)",
            ],
            examples,
        )

    def test_requires_three_generated_examples_without_source_sentence(self) -> None:
        with self.assertRaises(ValueError):
            build_examples(None, ["Only one example."])

    def test_requires_source_sentence_meta_when_source_sentence_present(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"generated_examples\[0\] must match '\(source sentence\) \(<pos>\)'",
        ):
            build_examples(
                "Please retry the download if it doesn't start automatically.",
                [
                    "Please retry the download if it doesn't start automatically. (verb)",
                    "I retried the task after fixing the error. (verb)",
                    "You can retry the operation later. (verb)",
                ],
            )

    def test_requires_pos_suffix_without_source_sentence(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"generated_examples\[1\] must match '<sentence> \(<pos>\)'",
        ):
            build_examples(
                None,
                [
                    "I retried the task after fixing the error. (verb)",
                    "You can retry the operation later.",
                    "She will retry the process tomorrow. (verb)",
                ],
            )


if __name__ == "__main__":
    unittest.main()
