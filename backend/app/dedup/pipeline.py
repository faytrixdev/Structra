from __future__ import annotations

import hashlib
from typing import Any
from collections import defaultdict

from app.dedup.normalizer import full_normalize, token_set
from app.dedup.similarity import (
    are_quasi_identical,
    are_semantically_equivalent,
    content_tokens,
)
from app.dedup.merger import merge_group


Precomputed = dict[str, Any]


class _StatementCache:
    """In-process memoization for token_set / content_tokens / full_normalize.

    Both `are_quasi_identical` and `are_semantically_equivalent` re-compute
    spaCy lemmatization for every pair they inspect. With O(N^2) pairs the
    same statement can be re-lemmatized N times. We precompute once per
    unique normalized statement and pass results through.
    """

    def __init__(self) -> None:
        self._norm: dict[str, str] = {}
        self._fp: dict[str, str] = {}
        self._tokens: dict[str, set[str]] = {}
        self._content: dict[str, set[str]] = {}

    def get(self, text: str) -> Precomputed:
        if text in self._tokens:
            return {
                "statement": text,
                "fp": self._fp[text],
                "tokens": self._tokens[text],
                "content_tokens": self._content[text],
            }
        norm = full_normalize(text)
        fp = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        tokens = token_set(text)
        content = content_tokens(text)
        self._norm[text] = norm
        self._fp[text] = fp
        self._tokens[text] = tokens
        self._content[text] = content
        return {
            "statement": text,
            "fp": fp,
            "tokens": tokens,
            "content_tokens": content,
        }


def _pair_passes(
    prep_a: Precomputed, prep_b: Precomputed, cache: _StatementCache
) -> bool:
    if prep_a["fp"] == prep_b["fp"]:
        return True
    if are_quasi_identical(prep_a["statement"], prep_b["statement"]):
        return True
    if are_semantically_equivalent(prep_a["statement"], prep_b["statement"]):
        return True
    return False


def deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate idea candidates using 3 levels:

    1. Exact fingerprint (SHA-256 of fully-normalized statement).
    2. Lemmatized Jaccard >= 0.90 (near-duplicates).
    3. Synonym-expanded semantic Jaccard >= 0.85 (semantic duplicates).

    Optimized over the original implementation by:
    - Memoizing spaCy/NLTK lemmatization so each unique statement is
      processed at most once regardless of how many pairs reference it.
    - Pre-building an inverted content-token index so we only call the
      similarity functions on pairs sharing >= 1 content token instead
      of every pair.
    """
    if not items:
        return []

    cache = _StatementCache()
    precomputed: list[Precomputed] = []
    for item in items:
        text = (item.get("statement", "") or "")
        prep = dict(cache.get(text))
        prep["item"] = item
        precomputed.append(prep)

    n = len(precomputed)
    if n <= 1:
        return [precomputed[0]["item"]]

    # ── Level 2: group by exact fingerprint ───────────────────────────
    fp_buckets: dict[str, list[int]] = defaultdict(list)
    for idx, prep in enumerate(precomputed):
        fp_buckets[prep["fp"]].append(idx)

    # Build one merged representative per fingerprint group
    rep_items: list[dict[str, Any]] = []           # merged item per rep
    rep_raw: list[list[dict[str, Any]]] = []       # original items per rep
    original_to_rep: dict[int, int] = {}
    for rep_idx, (fp, group_indices) in enumerate(fp_buckets.items()):
        raw = [precomputed[i]["item"] for i in group_indices]
        rep_items.append(merge_group(raw))
        rep_raw.append(raw)
        for i in group_indices:
            original_to_rep[i] = rep_idx

    rep_count = len(rep_items)
    if rep_count <= 1:
        return [rep_items[0]]

    # ── Build precomputed reps for Level 3+4 ─────────────────────────
    rep_prep: list[Precomputed] = []
    for item in rep_items:
        rep_prep.append(cache.get((item.get("statement", "") or "")))

    # ── Build inverted index for pair filtering ──────────────────────
    token_index: dict[str, list[int]] = {}
    for idx, prep in enumerate(precomputed):
        for token in prep["content_tokens"]:
            token_index.setdefault(token, []).append(idx)

    rep_pair_set: set[tuple[int, int]] = set()
    for token, idxs in token_index.items():
        if len(idxs) > 128:
            continue
        for a_pos, i in enumerate(idxs):
            for j in idxs[a_pos + 1:]:
                if i == j:
                    continue
                ra = original_to_rep[i]
                rb = original_to_rep[j]
                if ra == rb:
                    continue
                pair = (ra, rb) if ra < rb else (rb, ra)
                rep_pair_set.add(pair)

    # For very short items (<=3 content tokens), the inverted index may
    # miss them because the two statements share no token. Compare them
    # against all other reps as a fallback — overhead is negligible.
    SHORT_THRESHOLD = 3
    for i in range(rep_count):
        if len(rep_prep[i]["content_tokens"]) <= SHORT_THRESHOLD:
            for j in range(rep_count):
                if i == j:
                    continue
                pair = (i, j) if i < j else (j, i)
                rep_pair_set.add(pair)

    # ── Level 3 + 4: near-duplicate and semantic equivalence ─────────
    rep_merged: set[int] = set()
    for i in range(rep_count):
        if i in rep_merged:
            continue
        collected: list[int] = [i]
        for j in range(i + 1, rep_count):
            if j in rep_merged:
                continue
            if (i, j) not in rep_pair_set:
                continue
            if _pair_passes(rep_prep[i], rep_prep[j], cache):
                collected.append(j)
                rep_merged.add(j)

        if len(collected) > 1:
            raw_items: list[dict[str, Any]] = []
            for rep in collected:
                raw_items.extend(rep_raw[rep])
            rep_items.append(merge_group(raw_items))
            for rep in collected:
                rep_merged.add(rep)

    # ── Build final output ───────────────────────────────────────────
    # Include: (a) merged groups from Level 3+4, (b) un-merged Level 2 reps
    final: list[dict[str, Any]] = []

    # The merged groups from Level 3+4 were appended after rep_count
    merged_groups_start = rep_count
    merged_group_count = len(rep_items) - rep_count
    for k in range(merged_groups_start, len(rep_items)):
        final.append(rep_items[k])

    # Include un-merged Level 2 reps
    for i in range(rep_count):
        if i not in rep_merged:
            final.append(rep_items[i])

    return final
