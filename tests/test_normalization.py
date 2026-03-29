from __future__ import annotations

import unittest

from backend.normalization import normalize_surface_form


class NormalizationTestCase(unittest.TestCase):
    def test_normalizes_case_and_edge_punctuation(self) -> None:
        result = normalize_surface_form(" Retry! ")
        self.assertEqual("retry", result.normalized_form)
        self.assertEqual(" Retry! ", result.surface_form)

    def test_rejects_non_word_input(self) -> None:
        with self.assertRaises(ValueError):
            normalize_surface_form("two words")


if __name__ == "__main__":
    unittest.main()
