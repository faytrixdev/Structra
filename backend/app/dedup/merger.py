from copy import deepcopy
from typing import Any

from app.domain.types import KnowledgeType


TYPE_PRIORITY: dict[KnowledgeType, int] = {
    KnowledgeType.PROCEDURE: 100,
    KnowledgeType.POLICY: 95,
    KnowledgeType.RULE: 90,
    KnowledgeType.WORKFLOW: 85,
    KnowledgeType.CONSTRAINT: 80,
    KnowledgeType.OBLIGATION: 75,
    KnowledgeType.PROHIBITION: 70,
    KnowledgeType.RESPONSIBILITY: 65,
    KnowledgeType.REQUIREMENT: 60,
    KnowledgeType.DECISION: 55,
    KnowledgeType.METRIC: 50,
    KnowledgeType.KPI: 50,
    KnowledgeType.DEFINITION: 45,
    KnowledgeType.EXCEPTION: 40,
    KnowledgeType.RISK: 35,
    KnowledgeType.EVENT: 30,
    KnowledgeType.CONCEPT: 25,
}


def _coerce_type(value: Any) -> KnowledgeType | None:
    if isinstance(value, KnowledgeType):
        return value
    if isinstance(value, str):
        try:
            return KnowledgeType(value)
        except ValueError:
            return None
    return None


def resolve_type_conflict(type_a: Any, type_b: Any) -> Any:
    enum_a = _coerce_type(type_a)
    enum_b = _coerce_type(type_b)
    priority_a = TYPE_PRIORITY.get(enum_a, 0) if enum_a is not None else 0
    priority_b = TYPE_PRIORITY.get(enum_b, 0) if enum_b is not None else 0
    if priority_a >= priority_b:
        return type_a
    return type_b


def merge_entities(entities_a: list[dict], entities_b: list[dict]) -> list[dict]:
    seen: dict[tuple[str, str], dict] = {}
    for ent in entities_a + entities_b:
        key = (ent.get("entity_type", ""), ent.get("value", ""))
        if key not in seen:
            seen[key] = ent
        else:
            existing_role = seen[key].get("role") or ""
            new_role = ent.get("role") or ""
            if len(new_role) > len(existing_role):
                seen[key]["role"] = new_role
    return list(seen.values())


def merge_conditions(conds_a: list[dict], conds_b: list[dict]) -> list[dict]:
    seen: dict[tuple[str, str], dict] = {}
    for cond in conds_a + conds_b:
        key = (cond.get("condition_type", ""), cond.get("description", ""))
        seen[key] = cond
    return list(seen.values())


def merge_group(group: list[dict]) -> dict:
    if len(group) == 1:
        return deepcopy(group[0])

    winner = max(group, key=lambda x: (x.get("confidence", 0), len(x.get("statement", ""))))

    merged = deepcopy(winner)

    all_entities: list[dict] = []
    for item in group:
        all_entities.extend(item.get("entities", []))
    merged["entities"] = merge_entities(merged.get("entities", []), all_entities)

    all_conditions: list[dict] = []
    for item in group:
        all_conditions.extend(item.get("conditions", []))
    merged["conditions"] = merge_conditions(merged.get("conditions", []), all_conditions)

    best_type = merged.get("type")
    for item in group:
        item_type = item.get("type")
        if item_type and best_type and item_type != best_type:
            best_type = resolve_type_conflict(best_type, item_type)
    merged["type"] = best_type

    merged["metadata"] = merged.get("metadata", {})
    merged["metadata"]["merged_from"] = [
        {"id": item.get("id"), "statement": item.get("statement", ""), "confidence": item.get("confidence", 0)}
        for item in group if item.get("id") != winner.get("id")
    ]

    return merged
