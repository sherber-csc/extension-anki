from __future__ import annotations

import unittest
from unittest.mock import patch

from backend import lemmatizer
from backend.lemmatizer import lemmatize_word


class LemmatizerTestCase(unittest.TestCase):
    def assert_lemma(self, surface_form: str, expected_lemma: str) -> None:
        result = lemmatize_word(surface_form)
        self.assertEqual(expected_lemma, result.lemma)
        self.assertEqual(expected_lemma, result.word_key)

    def test_override_families_do_not_call_wordnet(self) -> None:
        cases = {
            "organised": "organise",
            "organising": "organise",
            "organises": "organise",
            "practised": "practise",
            "practising": "practise",
            "practises": "practise",
            "retried": "retry",
            "retrying": "retry",
            "retries": "retry",
            "revises": "revise",
        }

        with patch("backend.lemmatizer._infer_with_wordnet") as mock_wordnet:
            for surface_form, expected_lemma in cases.items():
                with self.subTest(surface_form=surface_form):
                    self.assert_lemma(surface_form, expected_lemma)
            mock_wordnet.assert_not_called()

    def test_wordnet_main_path_handles_supported_inflections(self) -> None:
        responses = {
            "improving": "improve",
            "revised": "revise",
            "revising": "revise",
        }

        def fake_wordnet(word: str) -> str | None:
            return responses.get(word)

        with patch("backend.lemmatizer._infer_with_wordnet", side_effect=fake_wordnet) as mock_wordnet:
            self.assert_lemma("improving", "improve")
            self.assert_lemma("revised", "revise")
            self.assert_lemma("revising", "revise")
            self.assertEqual(3, mock_wordnet.call_count)

    def test_non_inflected_words_fall_back_without_wordnet(self) -> None:
        with patch("backend.lemmatizer._infer_with_wordnet") as mock_wordnet:
            self.assert_lemma("interactive", "interactive")
            self.assert_lemma("materials", "materials")
            mock_wordnet.assert_not_called()

    def test_wordnet_unavailable_does_not_crash(self) -> None:
        with patch("backend.lemmatizer._infer_with_wordnet", return_value=None):
            self.assert_lemma("improving", "improving")
            self.assert_lemma("revised", "revised")

    def test_missing_nltk_dependency_does_not_crash(self) -> None:
        with patch.object(lemmatizer, "NLTKWordNetLemmatizer", None), patch.object(
            lemmatizer,
            "_wordnet_lemmatizer",
            None,
        ):
            self.assert_lemma("improving", "improving")

    def test_wordnet_result_acceptance_is_minimal_and_explicit(self) -> None:
        self.assertTrue(lemmatizer._is_acceptable_wordnet_result("improving", "improve"))
        self.assertTrue(lemmatizer._is_acceptable_wordnet_result("interactive", "interactive"))
        self.assertFalse(lemmatizer._is_acceptable_wordnet_result("improving", ""))
        self.assertFalse(lemmatizer._is_acceptable_wordnet_result("improving", "x"))
        self.assertFalse(lemmatizer._is_acceptable_wordnet_result("improving", "rev1se"))
        self.assertFalse(lemmatizer._is_acceptable_wordnet_result("improving", None))

    def test_wordnet_result_longer_than_input_is_rejected(self) -> None:
        self.assertFalse(lemmatizer._is_acceptable_wordnet_result("revised", "reviseds"))


if __name__ == "__main__":
    unittest.main()
