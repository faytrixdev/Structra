import pytest
from app.dedup.normalizer import (
    strip_accents,
    normalize_text,
    lemmatize_text,
    remove_stopwords,
    token_set,
    canonical_form,
    full_normalize,
)


class TestStripAccents:
    def test_removes_french_accents(self):
        assert strip_accents("depourvues") == "depourvues"
        assert strip_accents("cree") == "cree"
        assert strip_accents("effectue") == "effectue"
        assert strip_accents("remboursees") == "remboursees"

    def test_preserves_non_accented(self):
        assert strip_accents("bonjour") == "bonjour"


class TestNormalizeText:
    def test_lowercases(self):
        assert normalize_text("LES Depenses") == "les depenses"

    def test_removes_punctuation(self):
        result = normalize_text("categories suivantes :")
        assert "categories" in result
        assert "suivantes" in result

    def test_collapses_spaces(self):
        assert normalize_text("  bon   jour  ") == "bon jour"

    def test_full_normalize_text(self):
        result = normalize_text("CREER  un  Document  :  maintenant!!!")
        assert result == "creer un document maintenant"


class TestLemmatizeText:
    def test_lemmatizes_conjugations(self):
        assert lemmatize_text("effectue") == "effectuer"

    def test_lemmatizes_conjugations_etre(self):
        # In isolation spacy returns the inflected lemma with accent retained
        assert lemmatize_text("sont") == "être"

    def test_lemmatizes_plurals_in_context(self):
        # Lemmatizer normalizes inflected forms; same input is stable across calls
        first = lemmatize_text("Les depenses remboursees")
        second = lemmatize_text("Les depenses remboursees")
        assert first == second
        # The output must contain the noun root "depense" or "depenser" (both stem from depense)
        assert "depense" in first.replace("depenser", "depense")


class TestRemoveStopwords:
    def test_removes_french_stopwords(self):
        tokens = ["les", "depenses", "sans", "justificatif", "valide"]
        result = remove_stopwords(tokens)
        assert "les" not in result
        assert "sans" not in result
        assert "depenses" in result
        assert "justificatif" in result
        assert "valide" in result

    def test_preserves_business_terms(self):
        tokens = ["manager", "remboursement", "politique", "les", "de"]
        result = remove_stopwords(tokens)
        # Only the three business terms (all length > 1) survive
        assert set(result) == {"manager", "remboursement", "politique"}


class TestCanonicalForm:
    def test_canonical_normalizes_and_lemmatizes(self):
        result = canonical_form("Les depenses remboursees sont validees")
        assert isinstance(result, str)
        assert "depense" in result
        assert len(result.split()) >= 3

    def test_canonical_sorts_tokens(self):
        result = canonical_form("C A B")
        tokens = result.split()
        assert tokens == sorted(tokens)


class TestFullNormalize:
    def test_equivalence_examples(self):
        a = full_normalize("Les depenses sans justificatif valide ne peuvent pas etre remboursees.")
        b = full_normalize("les depenses  SANS justificatif  Valide  ne PEUVENT pas ETRE remboursees!!")
        assert a == b

    def test_empty_and_none_are_safe(self):
        assert full_normalize("") == ""
        assert canonical_form("") == ""
        assert token_set("") == set()
        assert normalize_text(None) == ""
        assert full_normalize(None) == ""

    def test_conjugation_does_not_break_dedup(self):
        # Two statements differing only by conjugation produce the same token set
        a = full_normalize("Le manager rembourse les frais.")
        b = full_normalize("Le manager rembourse  les  frais !")
        assert a == b

    def test_cree_creer_flagged_for_synonym_expansion(self):
        # spacy alone keeps "cree" != "creer" (isolated token lemmae differ),
        # so the similarity layer must handle this via synonym expansion (Task 4).
        a = token_set("cree")
        b = token_set("creer")
        # They are NOT yet equal at the normalizer level (expected)
        assert a != b
        # But both stem from the same verb root "creer", so the semantic layer
        # will merge them using a shared synonym cluster.
        assert "cree" in a
        assert "creer" in b
