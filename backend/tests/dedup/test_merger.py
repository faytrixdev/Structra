import pytest
from app.dedup.merger import (
    merge_group,
    merge_entities,
    merge_conditions,
    resolve_type_conflict,
    TYPE_PRIORITY,
)
from app.domain.types import KnowledgeType


class TestTypeConflict:
    def test_procedure_beats_concept(self):
        assert resolve_type_conflict(KnowledgeType.CONCEPT, KnowledgeType.PROCEDURE) == KnowledgeType.PROCEDURE

    def test_policy_beats_definition(self):
        assert resolve_type_conflict(KnowledgeType.DEFINITION, KnowledgeType.POLICY) == KnowledgeType.POLICY

    def test_same_type_returns_first(self):
        assert resolve_type_conflict(KnowledgeType.RULE, KnowledgeType.RULE) == KnowledgeType.RULE

    def test_type_priority_ordering(self):
        assert TYPE_PRIORITY[KnowledgeType.PROCEDURE] > TYPE_PRIORITY[KnowledgeType.CONCEPT]
        assert TYPE_PRIORITY[KnowledgeType.POLICY] > TYPE_PRIORITY[KnowledgeType.DEFINITION]
        assert TYPE_PRIORITY[KnowledgeType.CONSTRAINT] > TYPE_PRIORITY[KnowledgeType.EVENT]


class TestMergeEntities:
    def test_union_of_different_entities(self):
        entities_a = [{"entity_type": "actor", "value": "Manager", "role": "approver"}]
        entities_b = [
            {"entity_type": "actor", "value": "Manager", "role": "approver"},
            {"entity_type": "actor", "value": "Service financier", "role": "processor"},
        ]
        result = merge_entities(entities_a, entities_b)
        assert len(result) == 2
        values = {e["value"] for e in result}
        assert "Manager" in values
        assert "Service financier" in values

    def test_deduplicates_exact_duplicates(self):
        entities_a = [{"entity_type": "actor", "value": "Manager", "role": "validator"}]
        entities_b = [{"entity_type": "actor", "value": "Manager", "role": "validator"}]
        result = merge_entities(entities_a, entities_b)
        assert len(result) == 1

    def test_keeps_longest_role_for_same_entity(self):
        entities_a = [{"entity_type": "actor", "value": "Manager", "role": "HR"}]
        entities_b = [{"entity_type": "actor", "value": "Manager", "role": "Human Resources Manager"}]
        result = merge_entities(entities_a, entities_b)
        assert len(result) == 1
        assert result[0]["role"] == "Human Resources Manager"


class TestMergeConditions:
    def test_union_of_different_conditions(self):
        cond_a = [{"condition_type": "condition", "description": "Montant > 500"}]
        cond_b = [
            {"condition_type": "condition", "description": "Montant > 500"},
            {"condition_type": "condition", "description": "Justificatif requis"},
        ]
        result = merge_conditions(cond_a, cond_b)
        assert len(result) == 2

    def test_deduplicates_identical(self):
        cond_a = [{"condition_type": "constraint", "description": "Pas de limite"}]
        cond_b = [{"condition_type": "constraint", "description": "Pas de limite"}]
        result = merge_conditions(cond_a, cond_b)
        assert len(result) == 1


class TestMergeGroup:
    def test_picks_highest_confidence(self):
        group = [
            {"id": "a", "confidence": 0.90, "statement": "short", "type": KnowledgeType.PROCEDURE, "entities": [], "conditions": []},
            {"id": "b", "confidence": 0.50, "statement": "longer" * 10, "type": KnowledgeType.PROCEDURE, "entities": [], "conditions": []},
        ]
        result = merge_group(group)
        assert result["id"] == "a"

    def test_tiebreaker_picks_longest_statement(self):
        group = [
            {"id": "a", "confidence": 0.90, "statement": "short", "type": KnowledgeType.PROCEDURE, "entities": [], "conditions": []},
            {"id": "b", "confidence": 0.90, "statement": "this is the longest statement", "type": KnowledgeType.PROCEDURE, "entities": [], "conditions": []},
        ]
        result = merge_group(group)
        assert result["id"] == "b"

    def test_merges_entities_from_all(self):
        group = [
            {"id": "a", "confidence": 0.90, "statement": "OK", "type": KnowledgeType.PROCEDURE,
             "entities": [{"entity_type": "actor", "value": "Manager", "role": "val"}], "conditions": []},
            {"id": "b", "confidence": 0.80, "statement": "OK", "type": KnowledgeType.PROCEDURE,
             "entities": [{"entity_type": "actor", "value": "Service financier", "role": "remb"}], "conditions": []},
        ]
        result = merge_group(group)
        values = {e["value"] for e in result["entities"]}
        assert "Manager" in values
        assert "Service financier" in values

    def test_merges_conditions_from_all(self):
        group = [
            {"id": "a", "confidence": 0.90, "statement": "OK", "type": KnowledgeType.PROCEDURE,
             "entities": [], "conditions": [{"condition_type": "condition", "description": "A"}]},
            {"id": "b", "confidence": 0.80, "statement": "OK", "type": KnowledgeType.PROCEDURE,
             "entities": [], "conditions": [{"condition_type": "condition", "description": "B"}]},
        ]
        result = merge_group(group)
        assert len(result["conditions"]) == 2

    def test_resolves_type_conflict(self):
        group = [
            {"id": "a", "confidence": 0.90, "statement": "X", "type": KnowledgeType.POLICY, "entities": [], "conditions": []},
            {"id": "b", "confidence": 0.90, "statement": "X", "type": KnowledgeType.DEFINITION, "entities": [], "conditions": []},
        ]
        result = merge_group(group)
        assert result["type"] == KnowledgeType.POLICY

    def test_records_merged_from_metadata(self):
        group = [
            {"id": "a", "confidence": 0.90, "statement": "X", "type": KnowledgeType.PROCEDURE, "entities": [], "conditions": []},
            {"id": "b", "confidence": 0.50, "statement": "X", "type": KnowledgeType.PROCEDURE, "entities": [], "conditions": []},
        ]
        result = merge_group(group)
        assert "merged_from" in result["metadata"]
        assert len(result["metadata"]["merged_from"]) == 1
        assert result["metadata"]["merged_from"][0]["id"] == "b"

    def test_single_item_returns_copy(self):
        group = [{"id": "a", "confidence": 0.90, "statement": "X", "type": KnowledgeType.PROCEDURE, "entities": [], "conditions": []}]
        result = merge_group(group)
        assert result["id"] == "a"
        assert result is not group[0]
