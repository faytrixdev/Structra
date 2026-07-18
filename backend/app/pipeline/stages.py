from __future__ import annotations

import asyncio
import json
import time
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.provider.nim_client import nim_client, NIMClient, NIMClientError
from app.pipeline.prompts import (
    SYSTEM_EXTRACT_IDEAS,
    SYSTEM_CLASSIFY,
    SYSTEM_EXTRACT_ENTITIES,
    SYSTEM_CLASSIFY_AND_EXTRACT,
    SYSTEM_BUILD_RELATIONS,
    SYSTEM_VALIDATE,
)
from app.domain.models import PipelineLog
from app.domain.types import KnowledgeType, RelationType, EntityType, ConditionType
from app.config import settings

logger = logging.getLogger(__name__)

_ALL_KNOWLEDGE_TYPES: set[str] = {kt.value for kt in KnowledgeType}
_ALL_RELATION_TYPES: set[str] = {rt.value for rt in RelationType}
_ALL_ENTITY_TYPES: set[str] = {et.value for et in EntityType}
_ALL_CONDITION_TYPES: set[str] = {ct.value for ct in ConditionType}


# ── Deterministic validation (no LLM) ────────────────────────────────────

def validate_knowledge_obj(ko: dict[str, Any]) -> dict[str, Any]:
    """Validate a knowledge object entirely in code.

    Returns {"valid": bool, "issues": list[str], "confidence": float}.
    """
    issues: list[str] = []

    stmt = ko.get("statement", "") or ko.get("title", "")
    if not stmt or len(stmt.strip()) < 5:
        issues.append("Statement is too short or empty")
    if len(stmt) > 500:
        issues.append(f"Statement too long ({len(stmt)} chars); consider splitting")

    raw_type = ko.get("type", "")
    if isinstance(raw_type, str):
        if raw_type not in _ALL_KNOWLEDGE_TYPES:
            issues.append(f"Unknown type '{raw_type}'; expected one of {sorted(_ALL_KNOWLEDGE_TYPES)}")
    else:
        issues.append(f"Type must be a string, got {type(raw_type).__name__}")

    confidence = ko.get("confidence", 0.5)
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        issues.append(f"Confidence must be a float in [0, 1], got {confidence!r}")
        confidence = 0.5

    entities = ko.get("entities", [])
    if not isinstance(entities, list):
        issues.append("Entities must be a list")
    else:
        seen_ent: set[tuple[str, str]] = set()
        for ent in entities:
            et = ent.get("type", "")
            if et not in _ALL_ENTITY_TYPES:
                issues.append(f"Unknown entity type '{et}'")
            key = (et, ent.get("value", ""))
            if key in seen_ent:
                issues.append(f"Duplicate entity {key}")
            seen_ent.add(key)

    conditions = ko.get("conditions", [])
    if not isinstance(conditions, list):
        issues.append("Conditions must be a list")
    else:
        for cond in conditions:
            ct = cond.get("type", "")
            if ct not in _ALL_CONDITION_TYPES:
                issues.append(f"Unknown condition type '{ct}'")
            if not cond.get("description"):
                issues.append("Condition missing description")

    valid = len(issues) == 0
    return {
        "valid": valid,
        "issues": issues,
        "confidence": confidence,
    }


# ── LLM pipeline stages ──────────────────────────────────────────────────

async def extract_ideas_batch(
    document_id: str,
    segments: list[str],
    max_concurrency: int = 8,
) -> list[dict[str, Any]]:
    """Extract ideas from multiple segments in parallel.

    Each segment is an independent LLM call; we run up to max_concurrency
    concurrently via a semaphore. Default lowered (was 12) to stay under the
    NIM 429 rate-limit when batching many segments simultaneously.
    """
    sem = asyncio.Semaphore(max_concurrency)
    all_ideas: list[dict[str, Any]] = []

    async def _extract_one(segment: str) -> list[dict[str, Any]]:
        async with sem:
            try:
                content = await nim_client.chat_completion(
                    SYSTEM_EXTRACT_IDEAS,
                    segment,
                    response_format={"type": "json_object"},
                )
                parsed = NIMClient._parse_json_object(content)
                if isinstance(parsed, dict) and "ideas" in parsed:
                    parsed = parsed["ideas"]
                if isinstance(parsed, list):
                    return parsed
                return []
            except Exception as e:
                logger.warning("extract_ideas failed: %s", e)
                return []

    results = await asyncio.gather(*[_extract_one(seg) for seg in segments])
    for ideas in results:
        all_ideas.extend(ideas)
    return all_ideas


async def classify_and_extract_entities_batch(
    ideas: list[dict[str, Any]],
    max_concurrency: int = 6,
    classify_concurrency: int | None = None,
    entity_concurrency: int | None = None,
    combined: bool | None = None,
) -> list[dict[str, Any]]:
    """For each idea, classify and extract entities in parallel.

    Returns a list of candidate dicts with keys:
    id, type, title, statement, original_text, confidence, entities, conditions.

    `classify_concurrency` and `entity_concurrency` independently throttle
    each call type. Default when omitted: `classify=4`, `entity=8`. This
    avoids hitting the NIM 429 rate limit when many ideas fan out in parallel.

    When `combined=True`, both tasks run in a SINGLE LLM call per idea
    (using SYSTEM_CLASSIFY_AND_EXTRACT). This halves the total request count
    — useful on rate-limited providers (NVIDIA NIM free tier, etc.).
    `combined` defaults to `settings.pipeline_combined_default`.
    """
    if combined is None:
        combined = getattr(settings, "pipeline_combined_default", True)

    if combined:
        # Single LLM call per idea; only one semaphore is needed.
        if classify_concurrency is None and entity_concurrency is None:
            sem_limit = max_concurrency
        else:
            sem_limit = min(
                filter(
                    None,
                    [
                        classify_concurrency,
                        entity_concurrency,
                        max_concurrency,
                    ],
                )
            )
        sem = asyncio.Semaphore(sem_limit)

        async def _process_one_combined(idx: int, idea: dict[str, Any]) -> dict[str, Any]:
            statement = idea.get("statement", "")
            idea_id = idea.get("id", str(idx))
            async with sem:
                try:
                    result = await nim_client.chat_completion_json(
                        SYSTEM_CLASSIFY_AND_EXTRACT,
                        statement,
                    )
                except Exception as exc:
                    logger.warning("combined classify+entities failed for idea %s: %s", idea_id, exc)
                    result = {}

            raw_type = result.get("type", idea.get("type", "Concept"))
            if raw_type not in _ALL_KNOWLEDGE_TYPES:
                raw_type = "Concept"

            return {
                "id": idea_id,
                "type": raw_type,
                "title": statement[:100],
                "statement": statement,
                "original_text": statement,
                "confidence": result.get("confidence", 0.5),
                "entities": result.get("entities", []) or [],
                "conditions": result.get("conditions", []) or [],
            }

        results = await asyncio.gather(
            *[_process_one_combined(i, idea) for i, idea in enumerate(ideas)]
        )
        return list(results)

    # ── Legacy two-call path (used when combined=False is explicitly set) ──
    if classify_concurrency is None:
        classify_concurrency = getattr(settings, "pipeline_classify_concurrency", 4)
    if entity_concurrency is None:
        entity_concurrency = getattr(settings, "pipeline_entity_concurrency", max_concurrency * 2)
    classify_sem = asyncio.Semaphore(classify_concurrency)
    entity_sem = asyncio.Semaphore(entity_concurrency)

    async def _process_one(idx: int, idea: dict[str, Any]) -> dict[str, Any]:
        statement = idea.get("statement", "")
        idea_id = idea.get("id", str(idx))

        async def _classify() -> dict[str, Any]:
            async with classify_sem:
                return await nim_client.chat_completion_json(
                    SYSTEM_CLASSIFY,
                    f"Statement: {statement}\n\nClassify this statement.",
                )

        async def _entities() -> dict[str, Any]:
            async with entity_sem:
                return await nim_client.chat_completion_json(
                    SYSTEM_EXTRACT_ENTITIES,
                    statement,
                )

        classify_result, entities_result = await asyncio.gather(
            _classify(), _entities(), return_exceptions=True
        )

        classification: dict[str, Any] = {}
        if isinstance(classify_result, dict):
            classification = classify_result
        elif isinstance(classify_result, Exception):
            logger.warning("classify failed for idea %s: %s", idea_id, classify_result)
            classification = {"type": "Concept", "confidence": 0.5}

        entities_data: dict[str, Any] = {}
        if isinstance(entities_result, dict):
            entities_data = entities_result
        elif isinstance(entities_result, Exception):
            logger.warning("entity extraction failed for idea %s: %s", idea_id, entities_result)
            entities_data = {"entities": [], "conditions": []}

        raw_type = classification.get("type", idea.get("type", "Concept"))
        if raw_type not in _ALL_KNOWLEDGE_TYPES:
            raw_type = "Concept"
        confidence = classification.get("confidence", 0.5)

        return {
            "id": idea_id,
            "type": raw_type,
            "title": statement[:100],
            "statement": statement,
            "original_text": statement,
            "confidence": confidence,
            "entities": entities_data.get("entities", []),
            "conditions": entities_data.get("conditions", []),
        }

    results = await asyncio.gather(
        *[_process_one(i, idea) for i, idea in enumerate(ideas)]
    )
    return list(results)


async def extract_relations_batch(
    knowledge_objects: list[dict[str, Any]],
    max_concurrency: int = 1,
) -> list[dict[str, Any]]:
    """Extract relations between knowledge objects in a single LLM call.

    Returns a list of relation dicts with keys:
    source_index, target_index, type, confidence.
    """
    if len(knowledge_objects) < 2:
        return []

    statements_block = "\n".join(
        f"[{i}] {ko.get('statement', '')}" for i, ko in enumerate(knowledge_objects)
    )
    user_prompt = (
        f"Knowledge objects:\n{statements_block}\n\n"
        "Identify relationships between the listed knowledge objects."
    )

    try:
        result = await nim_client.chat_completion_json(
            SYSTEM_BUILD_RELATIONS,
            user_prompt,
        )
        relations = result.get("relations", [])
        validated: list[dict[str, Any]] = []
        for rel in relations:
            src = rel.get("source_index", -1)
            tgt = rel.get("target_index", -1)
            rtype = rel.get("type", "references")
            conf = rel.get("confidence", 0.5)
            if (
                isinstance(src, int) and isinstance(tgt, int)
                and 0 <= src < len(knowledge_objects)
                and 0 <= tgt < len(knowledge_objects)
                and src != tgt
                and rtype in _ALL_RELATION_TYPES
                and 0 <= conf <= 1
            ):
                validated.append({
                    "source_index": src,
                    "target_index": tgt,
                    "type": rtype,
                    "confidence": conf,
                })
        return validated
    except Exception as e:
        logger.warning("relation extraction failed: %s", e)
        return []


def build_relations_heuristic(
    knowledge_objects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Deterministic relation builder (no LLM).

    Creates a 'references' edge between every pair of same-type knowledge
    objects. Used in Balanced mode where LLM relation extraction is skipped
    to save latency. This is strictly less accurate than the LLM pass but
    preserves a baseline relational graph.
    """
    relations: list[dict[str, Any]] = []
    n = len(knowledge_objects)
    for i in range(n):
        for j in range(i + 1, n):
            if knowledge_objects[i].get("type") == knowledge_objects[j].get("type"):
                relations.append({
                    "source_index": i,
                    "target_index": j,
                    "type": RelationType.REFERENCES.value,
                    "confidence": 0.5,
                })
    return relations
