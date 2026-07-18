from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.domain.models import (
    Document,
    DocumentChunk,
    KnowledgeObject,
    KnowledgeEntity,
    KnowledgeCondition,
    KnowledgeRelation,
    PipelineLog,
)
from app.domain.types import (
    DocumentStatus,
    KnowledgeType,
    RelationType,
)
from app.pipeline.stages import (
    extract_ideas_batch,
    classify_and_extract_entities_batch,
    extract_relations_batch,
    build_relations_heuristic,
    validate_knowledge_obj,
)
from app.service.extraction_service import extract_text, detect_sections
from app.dedup import deduplicate

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────

def _content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_log(db: Session, document_id: str, step: str, status: str, duration_ms: int, error: str | None = None) -> None:
    db.add(PipelineLog(
        document_id=document_id,
        step=step,
        status=status,
        duration_ms=duration_ms,
        model=settings.nvidia_model,
        error_message=error,
    ))


def _segment_text(text: str, max_chars: int = 2000, overlap: int = 200) -> list[str]:
    """Sliding-window segmenter. Keeps context while limiting prompt size."""
    text = text.strip()
    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    segments: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))

        if end < len(text):
            last_period = text.rfind(".", start, end)
            last_newline = text.rfind("\n", start, end)
            split_at = max(last_period, last_newline)
            if split_at > start + max_chars // 2:
                end = split_at + 1

        seg = text[start:end].strip()
        if seg:
            segments.append(seg)

        if end >= len(text):
            break
        start = end - overlap

    return segments


def _persist_results(
    db: Session,
    doc: Document,
    deduped: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    pipeline_mode: str,
) -> list[str]:
    """Persist all knowledge objects, entities, conditions in a single transaction."""
    knowledge_ids: list[str] = []

    for item in deduped:
        raw_type = item.get("type", "Concept")
        try:
            kt = KnowledgeType(raw_type)
        except ValueError:
            kt = KnowledgeType.CONCEPT

        ko = KnowledgeObject(
            organization_id=doc.organization_id,
            document_id=doc.id,
            type=kt,
            title=item.get("statement", "")[:100],
            statement=item.get("statement", ""),
            original_text=item.get("original_text", ""),
            confidence=item.get("confidence", 0.5),
            extra_data=item.get("metadata", {}),
        )
        db.add(ko)
        db.flush()

        for ent in item.get("entities", []):
            db.add(KnowledgeEntity(
                knowledge_id=ko.id,
                entity_type=ent.get("type", "object"),
                value=(ent.get("value", "") or "")[:240],
                role=(ent.get("role") or None) and ent.get("role")[:240],
            ))

        for cond in item.get("conditions", []):
            db.add(KnowledgeCondition(
                knowledge_id=ko.id,
                condition_type=cond.get("type", "condition"),
                description=cond.get("description", ""),
            ))

        knowledge_ids.append(str(ko.id))

    if relations and len(deduped) >= 2:
        for rel in relations:
            src_idx = rel.get("source_index", -1)
            tgt_idx = rel.get("target_index", -1)
            rtype = rel.get("type", "references")
            conf = rel.get("confidence", 0.5)
            if 0 <= src_idx < len(knowledge_ids) and 0 <= tgt_idx < len(knowledge_ids) and src_idx != tgt_idx:
                try:
                    rt = RelationType(rtype)
                except ValueError:
                    rt = RelationType.REFERENCES
                db.add(KnowledgeRelation(
                    source_id=knowledge_ids[src_idx],
                    target_id=knowledge_ids[tgt_idx],
                    relation_type=rt,
                    confidence=conf,
                ))

    return knowledge_ids


def _persist_chunks(
    db: Session,
    doc: Document,
    sections: list[tuple[str, str]],
) -> None:
    """Persist document chunks (for future reference/reprocessing)."""
    for position, (title, body) in enumerate(sections):
        # Truncate section title to fit VARCHAR(255) safely.
        safe_title = (title or "")[:240] if title else None
        db.add(DocumentChunk(
            document_id=doc.id,
            content=body,
            section=safe_title,
            position=position,
        ))


# ── Main pipeline ─────────────────────────────────────────────────────────

async def run_pipeline(
    document_id: str,
    pipeline_mode: str | None = None,
) -> None:
    """Run the full extraction pipeline for a document.

    Pipeline modes:
    - high_accuracy (default): LLM relation extraction, full entity+classify, validation.
    - balanced: heuristic relations, parallel classify+entities.
    - high_speed: no relations, combined classify+entities prompt.
    """
    if pipeline_mode is None:
        pipeline_mode = settings.pipeline_mode

    max_concurrency = settings.pipeline_max_concurrency
    db = SessionLocal()
    doc: Document | None = None
    pipeline_start = time.time()
    logs: list[PipelineLog] = []

    def _log(step: str, status: str, duration_ms: int, error: str | None = None) -> None:
        logs.append(PipelineLog(
            document_id=document_id,
            step=step,
            status=status,
            duration_ms=duration_ms,
            model=settings.nvidia_model,
            error_message=error,
        ))
        # Persist incrementally so partial failures leave an audit trail.
        db.add(logs[-1])
        try:
            db.commit()
        except Exception:
            db.rollback()

    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        # ── Read file (async) ─────────────────────────────────────────
        t0 = time.time()
        doc.status = DocumentStatus.EXTRACTING
        db.commit()

        import aiofiles
        async with aiofiles.open(doc.file_path, "rb") as f:
            file_content = await f.read()
        file_hash = _content_hash(file_content)

        # Only skip reprocessing if the document has already been COMPLETED
        # with the same content. A first-time upload always runs the pipeline,
        # even if content_hash was set on upload.
        if (
            doc.content_hash == file_hash
            and doc.status == DocumentStatus.COMPLETED
        ):
            logger.info("Document %s unchanged (hash=%s); skipping reprocessing", document_id, file_hash[:12])
            doc.status = DocumentStatus.COMPLETED
            db.commit()
            return

        text, page_count = await extract_text(doc.file_path, doc.file_type, file_content)
        doc.page_count = page_count
        doc.content_hash = file_hash
        db.commit()
        _log("extract_text", "completed", int((time.time() - t0) * 1000))

        # ── Clean + segment ───────────────────────────────────────────
        t1 = time.time()
        doc.status = DocumentStatus.CLEANING
        db.commit()
        cleaned_text = text.strip()

        doc.status = DocumentStatus.SEGMENTING
        db.commit()
        sections = detect_sections(cleaned_text, doc.file_type)
        if not sections:
            sections = [("", cleaned_text)]

        segment_texts = [body.strip() for _, body in sections if body.strip()]
        if not segment_texts:
            segment_texts = _segment_text(cleaned_text)

        _persist_chunks(db, doc, sections)
        db.commit()
        _log("segment", "completed", int((time.time() - t1) * 1000))

        # ── Extract ideas (parallel) ──────────────────────────────────
        t2 = time.time()
        doc.status = DocumentStatus.EXTRACTING_IDEAS
        db.commit()

        all_ideas = await extract_ideas_batch(
            str(doc.id),
            segment_texts,
            max_concurrency=max_concurrency,
        )

        if not all_ideas:
            doc.status = DocumentStatus.FAILED
            doc.error_message = "No ideas extracted from document"
            db.commit()
            _log("extract_ideas", "failed", int((time.time() - t2) * 1000), "No ideas extracted")
            return
        _log("extract_ideas", "completed", int((time.time() - t2) * 1000))

        # ── Classify + extract entities (parallel) ────────────────────
        t3 = time.time()
        doc.status = DocumentStatus.EXTRACTING_ENTITIES
        db.commit()

        candidate_pairs = await classify_and_extract_entities_batch(
            all_ideas,
            max_concurrency=max_concurrency,
        )
        _log("classify_and_entities", "completed", int((time.time() - t3) * 1000))

        # ── Deterministic validation (in-code) ────────────────────────
        t4 = time.time()
        doc.status = DocumentStatus.VALIDATING
        db.commit()

        validated: list[dict[str, Any]] = []
        validation_issues = 0
        for kp in candidate_pairs:
            result = validate_knowledge_obj(kp)
            kp["confidence"] = result.get("confidence", kp.get("confidence", 0.5))
            if result["valid"]:
                validated.append(kp)
            else:
                validation_issues += 1
                logger.debug("Validation issues for %s: %s", kp.get("id"), result["issues"])
                validated.append(kp)

        _log("validate", "completed", int((time.time() - t4) * 1000))

        # ── Deduplicate ───────────────────────────────────────────────
        t5 = time.time()
        deduped = deduplicate(validated)
        _log("deduplicate", "completed", int((time.time() - t5) * 1000))

        # ── Build relations ───────────────────────────────────────────
        t6 = time.time()
        doc.status = DocumentStatus.BUILDING_RELATIONS
        db.commit()

        if pipeline_mode == "high_accuracy":
            relations = await extract_relations_batch(deduped, max_concurrency=1)
        elif pipeline_mode == "balanced":
            relations = build_relations_heuristic(deduped)
        else:
            relations = []
        _log("build_relations", "completed", int((time.time() - t6) * 1000))

        # ── Persist all results in one transaction ────────────────────
        t7 = time.time()
        _persist_results(db, doc, deduped, relations, pipeline_mode)
        db.commit()
        _log("persist", "completed", int((time.time() - t7) * 1000))

        # ── Done ──────────────────────────────────────────────────────
        doc.status = DocumentStatus.COMPLETED
        db.commit()

        total_ms = int((time.time() - pipeline_start) * 1000)
        logger.info(
            "Pipeline completed for %s: %d ideas → %d deduped, %d relations, %d validation issues, total=%dms, mode=%s",
            document_id, len(all_ideas), len(deduped), len(relations), validation_issues, total_ms, pipeline_mode,
        )

    except Exception as e:
        logger.exception("Pipeline failed for %s", document_id)
        if doc is not None:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            try:
                db.commit()
            except Exception:
                db.rollback()
    finally:
        try:
            db.commit()
        except Exception:
            db.rollback()
        db.close()
        # NOTE: do NOT close the shared NIM client here — it is a long-lived
        # singleton with a connection pool. The rate limiter state must persist
        # across pipeline runs. The client closes on interpreter shutdown.
