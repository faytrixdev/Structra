import pytest
from app.dedup.fingerprint import (
    canonical_fingerprint,
    group_by_fingerprint,
)


class TestCanonicalFingerprint:
    def test_identical_texts_same_fingerprint(self):
        a = canonical_fingerprint("Le remboursement sous 7 jours.")
        b = canonical_fingerprint("Le remboursement sous 7 jours.")
        assert a == b

    def test_case_insensitive_same_fingerprint(self):
        a = canonical_fingerprint("CREER")
        b = canonical_fingerprint("créer")
        assert a == b

    def test_different_texts_different_fingerprint(self):
        a = canonical_fingerprint("Le manager valide les demandes.")
        b = canonical_fingerprint("Le service financier rembourse.")
        assert a != b

    def test_punctuation_ignored_same_fingerprint(self):
        a = canonical_fingerprint("Transport, Hebergement, Repas")
        b = canonical_fingerprint("Transport Hebergement Repas")
        assert a == b

    def test_empty_text_safe(self):
        assert canonical_fingerprint("") == canonical_fingerprint("")
        assert canonical_fingerprint(None) == canonical_fingerprint(None)


class TestGroupByFingerprint:
    def test_groups_exact_duplicates(self):
        items = [
            {"id": "a", "text": "remboursement 7 jours"},
            {"id": "b", "text": "remboursement 7 jours"},
            {"id": "c", "text": "validation manager"},
        ]
        groups = group_by_fingerprint(items, key=lambda x: x["text"])
        assert len(groups) == 2
        group_ids = [sorted(g["id"] for g in grp) for grp in groups]
        assert ["a", "b"] in group_ids
        assert ["c"] in group_ids

    def test_groups_by_canonical_form(self):
        items = [
            {"id": "a", "text": "Creer un compte"},
            {"id": "b", "text": "créer un compte!!"},
            {"id": "c", "text": "Valider les demandes"},
        ]
        groups = group_by_fingerprint(items, key=lambda x: x["text"])
        assert len(groups) == 2

    def test_no_duplicates_single_groups(self):
        items = [
            {"id": "a", "text": "manager"},
            {"id": "b", "text": "remboursement"},
            {"id": "c", "text": "validation"},
        ]
        groups = group_by_fingerprint(items, key=lambda x: x["text"])
        assert len(groups) == 3

    def test_empty_items_returns_empty(self):
        assert group_by_fingerprint([], key=lambda x: x["text"]) == []
