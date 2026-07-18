import pytest
from app.dedup.pipeline import deduplicate


def make_item(id: str, statement: str, type: str = "Procedure") -> dict:
    return {
        "id": id,
        "statement": statement,
        "type": type,
        "entities": [],
        "conditions": [],
        "confidence": 0.80,
    }


class TestDeduplicate:
    def test_exact_duplicates_merged(self):
        items = [
            make_item("a", "Le remboursement est effectue sous 7 jours ouvres."),
            make_item("b", "Le remboursement est effectue sous 7 jours ouvres."),
        ]
        result = deduplicate(items)
        assert len(result) == 1

    def test_quasi_duplicates_merged(self):
        items = [
            make_item("a", "Les categories suivantes sont remboursables : Transport Hebergement Repas"),
            make_item("b", "Les categories suivantes sont remboursables : Transport, Hebergement, Repas"),
        ]
        result = deduplicate(items)
        assert len(result) == 1

    def test_semantic_equivalent_merged(self):
        items = [
            make_item("a", "Les depenses sans justificatif valide ne peuvent pas etre remboursees."),
            make_item("b", "Les depenses depourvues d'un justificatif valide ne sont pas remboursables."),
        ]
        result = deduplicate(items)
        assert len(result) == 1

    def test_distinct_items_preserved(self):
        items = [
            make_item("a", "Le manager valide les demandes de remboursement."),
            make_item("b", "Le service financier traite les paiements."),
            make_item("c", "Les notes de frais doivent etre soumises avant le 5 du mois."),
        ]
        result = deduplicate(items)
        assert len(result) == 3

    def test_mixed_scenario(self):
        items = [
            make_item("a", "remboursement 7 jours"),
            make_item("b", "remboursement 7 jours"),
            make_item("c", "remboursement  7 jours"),
            make_item("d", "validation manager"),
            make_item("e", "politique de conformite"),
        ]
        result = deduplicate(items)
        assert len(result) == 3

    def test_best_score_kept(self):
        items = [
            {"id": "a", "statement": "X", "type": "Procedure", "confidence": 0.50, "entities": [], "conditions": []},
            {"id": "b", "statement": "X", "type": "Procedure", "confidence": 0.90, "entities": [], "conditions": []},
        ]
        result = deduplicate(items)
        assert len(result) == 1
        assert result[0]["confidence"] == 0.90

    def test_type_conflict_resolved(self):
        items = [
            make_item("a", "Cette politique definit les regles de remboursement.", "Policy"),
            make_item("b", "Cette politique definit les regles de remboursement.", "Definition"),
        ]
        result = deduplicate(items)
        assert len(result) == 1
        assert result[0]["type"] == "Policy"

    def test_entity_union_preserved(self):
        items = [
            {"id": "a", "statement": "Le manager valide.", "type": "Responsibility", "confidence": 0.80,
             "entities": [{"entity_type": "actor", "value": "Manager", "role": "validator"}], "conditions": []},
            {"id": "b", "statement": "Le manager valide.", "type": "Responsibility", "confidence": 0.90,
             "entities": [{"entity_type": "actor", "value": "Service financier", "role": "processor"}], "conditions": []},
        ]
        result = deduplicate(items)
        assert len(result) == 1
        values = {e["value"] for e in result[0]["entities"]}
        assert "Manager" in values
        assert "Service financier" in values

    def test_no_false_positives_on_distinct_short_items(self):
        items = [
            make_item("a", "manager"),
            make_item("b", "Service financier"),
            make_item("c", "Audit"),
        ]
        result = deduplicate(items)
        assert len(result) == 3

    def test_empty_input(self):
        assert deduplicate([]) == []

    def test_creer_cree_merged_via_semantic(self):
        items = [
            make_item("a", "Le collaborateur doit creer la demande."),
            make_item("b", "Le collaborateur doit cree la demande."),
        ]
        result = deduplicate(items)
        assert len(result) == 1
