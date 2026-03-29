from __future__ import annotations

import unittest

from backend.forms_builder import build_forms


class FormsBuilderTestCase(unittest.TestCase):
    def test_builds_verb_forms_in_fixed_order(self) -> None:
        self.assertEqual(build_forms("retry", is_verb=True), "retries / retried / retrying")

    def test_returns_empty_for_non_verbs(self) -> None:
        self.assertEqual(build_forms("quick", is_verb=False), "")


if __name__ == "__main__":
    unittest.main()
