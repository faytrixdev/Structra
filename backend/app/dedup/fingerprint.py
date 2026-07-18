import hashlib
from collections import defaultdict
from typing import Callable, TypeVar

from app.dedup.normalizer import full_normalize

T = TypeVar("T")


def canonical_fingerprint(text: str) -> str:
    normalized = full_normalize(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def group_by_fingerprint(
    items: list[T],
    key: Callable[[T], str],
    fingerprint_fn: Callable[[str], str] = canonical_fingerprint,
) -> list[list[T]]:
    buckets: dict[str, list[T]] = defaultdict(list)
    for item in items:
        fp = fingerprint_fn(key(item))
        buckets[fp].append(item)
    return list(buckets.values())
