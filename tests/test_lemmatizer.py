from __future__ import annotations

import unittest

from backend.lemmatizer import lemmatize_word


class LemmatizerTestCase(unittest.TestCase):
    def test_retry_family_maps_to_same_word_key(self) -> None:
        for surface_form in ("retry", "retried", "retrying", "retries"):
            result = lemmatize_word(surface_form)
            self.assertEqual("retry", result.lemma)
            self.assertEqual("retry", result.word_key)


if __name__ == "__main__":
    unittest.main()
