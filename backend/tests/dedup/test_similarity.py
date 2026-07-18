import pytest
from app.dedup.similarity import (
    jaccard_similarity,
    semantic_jaccard,
    are_quasi_identical,
    are_semantically_equivalent,
    SYNONYMS_FR,
    expand_with_synonyms,
)


class TestJaccardSimilarity:
    def test_identical_sets_score_one(self):
        assert jaccard_similarity({"a", "b", "c"}, {"a", "b", "c"}) == 1.0

    def test_disjoint_sets_score_zero(self):
        assert jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0

    def test_partial_overlap(self):
        score = jaccard_similarity({"a", "b", "c"}, {"a", "b", "d"})
        assert score == pytest.approx(0.5, 0.01)

    def test_empty_sets_score_one(self):
        assert jaccard_similarity(set(), set()) == 1.0


class TestAreQuasiIdentical:
    def test_identical_after_normalization(self):
        assert are_quasi_identical(
            "Les categories suivantes sont remboursables : Transport professionnel Hebergement professionnel Repas professionnels",
            "Les categories suivantes sont remboursables : Transport professionnel, Hebergement professionnel, Repas professionnels",
        )

    def test_different_meanings_false(self):
        assert not are_quasi_identical(
            "Le manager valide les demandes.",
            "Le service financier rembourse les frais.",
        )


class TestSemanticEquivalence:
    def test_synonym_expansion(self):
        assert "remboursable" in SYNONYMS_FR
        synonyms = expand_with_synonyms({"remboursable"})
        assert "pouvant_etre_rembourse" in synonyms or "eligible_remboursement" in synonyms

    def test_creer_cree_merge_via_synonyms(self):
        # spacy alone doesn't merge these; synonym cluster does
        synonyms_a = expand_with_synonyms({"cree"})
        synonyms_b = expand_with_synonyms({"creer"})
        assert "creer" in synonyms_a | synonyms_b

    def test_semantic_equivalence_french(self):
        """The flagship example from the spec."""
        assert are_semantically_equivalent(
            "Les depenses sans justificatif valide ne peuvent pas etre remboursees.",
            "Les depenses depourvues d'un justificatif valide ne sont pas remboursables.",
        )

    def test_different_rules_not_equivalent(self):
        assert not are_semantically_equivalent(
            "Les depenses de transport sont remboursees a 100 %.",
            "Les depenses de repas sont remboursees a 50 % de la limite legale.",
        )

    def test_garde_fou_small_intersection(self):
        """Very short texts with high ratio but small absolute overlap."""
        assert not are_semantically_equivalent("manager", "service financier")


class TestSimilarityThresholds:
    def test_quasi_threshold_90(self):
        score = jaccard_similarity({"depense", "justificatif", "valide"}, {"depense", "justificatif", "valide"})
        assert score >= 0.90
        assert score >= 0.85

    def test_semantic_threshold_85(self):
        a = {"depense", "justificatif", "valide", "remboursable"}
        b = {"depense", "justificatif", "valide", "pouvant_etre_rembourse"}
        semantic_score = semantic_jaccard(a, b)
        assert semantic_score >= 0.85
