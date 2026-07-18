"""Orchestrator-level integration: verify dedup works in the actual pipeline.

These tests exercise the merged deduplicate() entry point against all the
specification examples to guarantee no regressions in the 4-level pipeline.
"""

import pytest
from app.dedup import deduplicate


class TestDedupIntegration:
    def test_in_memory_dedup_before_persist(self):
        candidates = [
            {"id": "1", "type": "Procedure", "statement": "Remboursement sous 7 jours.", "confidence": 0.50, "entities": [], "conditions": []},
            {"id": "2", "type": "Procedure", "statement": "Remboursement sous 7 jours.", "confidence": 0.90, "entities": [], "conditions": []},
            {"id": "3", "type": "Definition", "statement": "Le manager valide les demandes.", "confidence": 0.80, "entities": [], "conditions": []},
        ]
        deduped = deduplicate(candidates)
        assert len(deduped) < len(candidates)
        assert len(deduped) == 2

    def test_entity_merge_preserved_in_dedup(self):
        candidates = [
            {
                "id": "1", "type": "Responsibility", "confidence": 0.80,
                "statement": "Le manager valide les demandes de remboursement.",
                "entities": [{"entity_type": "actor", "value": "Manager", "role": "validator"}],
                "conditions": [],
            },
            {
                "id": "2", "type": "Responsibility", "confidence": 0.90,
                "statement": "Le manager valide les demandes de remboursement.",
                "entities": [{"entity_type": "actor", "value": "Service financier", "role": "processor"}],
                "conditions": [],
            },
        ]
        deduped = deduplicate(candidates)
        assert len(deduped) == 1
        assert len(deduped[0]["entities"]) == 2

    def test_best_confidence_kept(self):
        candidates = [
            {"id": "1", "type": "Procedure", "confidence": 0.50, "statement": "X", "entities": [], "conditions": []},
            {"id": "2", "type": "Procedure", "confidence": 0.90, "statement": "X", "entities": [], "conditions": []},
        ]
        deduped = deduplicate(candidates)
        assert len(deduped) == 1
        assert deduped[0]["confidence"] == 0.90

    def test_all_french_spec_examples(self):
        # Example 1: exact duplicate
        r1 = deduplicate([
            {"id": "1", "type": "Procedure", "confidence": 0.9,
             "statement": "Le remboursement est effectue sous 7 jours ouvres apres validation financiere.",
             "entities": [], "conditions": []},
            {"id": "2", "type": "Procedure", "confidence": 0.9,
             "statement": "Le remboursement est effectue sous 7 jours ouvres apres validation financiere.",
             "entities": [], "conditions": []},
        ])
        assert len(r1) == 1

        # Example 2: near-duplicate (comma vs no comma in lists)
        r2 = deduplicate([
            {"id": "1", "type": "Procedure", "confidence": 0.9,
             "statement": "Les categories suivantes sont remboursables : Transport professionnel Hebergement professionnel Repas professionnels",
             "entities": [], "conditions": []},
            {"id": "2", "type": "Procedure", "confidence": 0.9,
             "statement": "Les categories suivantes sont remboursables : Transport professionnel, Hebergement professionnel, Repas professionnels",
             "entities": [], "conditions": []},
        ])
        assert len(r2) == 1

        # Example 3: conjugation
        r3 = deduplicate([
            {"id": "1", "type": "Action", "confidence": 0.9, "statement": "creer", "entities": [], "conditions": []},
            {"id": "2", "type": "Action", "confidence": 0.9, "statement": "cree", "entities": [], "conditions": []},
        ])
        assert len(r3) == 1

        # Example 4: semantic (flagship)
        r4 = deduplicate([
            {"id": "1", "type": "Constraint", "confidence": 0.9,
             "statement": "Les depenses sans justificatif valide ne peuvent pas etre remboursees.",
             "entities": [], "conditions": []},
            {"id": "2", "type": "Constraint", "confidence": 0.9,
             "statement": "Les depenses depourvues d un justificatif valide ne sont pas remboursables.",
             "entities": [], "conditions": []},
        ])
        assert len(r4) == 1

        # Example 5: same text, conflicting classification
        r5 = deduplicate([
            {"id": "1", "type": "Policy", "confidence": 0.9,
             "statement": "Cette politique definit les regles de remboursement.",
             "entities": [], "conditions": []},
            {"id": "2", "type": "Definition", "confidence": 0.9,
             "statement": "Cette politique definit les regles de remboursement.",
             "entities": [], "conditions": []},
        ])
        assert len(r5) == 1
        assert r5[0]["type"] == "Policy"

    def test_distinct_rules_not_merged(self):
        candidates = [
            {"id": "1", "type": "Constraint", "confidence": 0.9,
             "statement": "Les depenses de transport sont remboursees a 100 %.",
             "entities": [], "conditions": []},
            {"id": "2", "type": "Constraint", "confidence": 0.9,
             "statement": "Les depenses de repas sont remboursees a 50 % de la limite legale.",
             "entities": [], "conditions": []},
        ]
        deduped = deduplicate(candidates)
        assert len(deduped) == 2

    def test_no_duplicates_in_final_output(self):
        """The result must contain exactly one representation of each knowledge unit."""
        candidates = [
            {"id": "1", "type": "Workflow", "confidence": 0.9, "statement": "Workflow A", "entities": [], "conditions": []},
            {"id": "2", "type": "Workflow", "confidence": 0.9, "statement": "Workflow A", "entities": [], "conditions": []},
            {"id": "3", "type": "Workflow", "confidence": 0.9, "statement": "Workflow A", "entities": [], "conditions": []},
            {"id": "4", "type": "Procedure", "confidence": 0.9, "statement": "Procedure B", "entities": [], "conditions": []},
            {"id": "5", "type": "Procedure", "confidence": 0.9, "statement": "Procedure B", "entities": [], "conditions": []},
            {"id": "6", "type": "Metric", "confidence": 0.9, "statement": "Metric C", "entities": [], "conditions": []},
            {"id": "7", "type": "Metric", "confidence": 0.9, "statement": "Metric C", "entities": [], "conditions": []},
        ]
        deduped = deduplicate(candidates)
        assert len(deduped) == 3
        types = sorted(item["type"] for item in deduped)
        assert types == ["Metric", "Procedure", "Workflow"]
