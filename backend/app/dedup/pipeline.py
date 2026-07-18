from app.dedup.fingerprint import canonical_fingerprint, group_by_fingerprint
from app.dedup.similarity import are_quasi_identical, are_semantically_equivalent
from app.dedup.merger import merge_group


def deduplicate(items: list[dict]) -> list[dict]:
    if not items:
        return []

    # Level 2: Exact duplicates via canonical fingerprint
    groups = group_by_fingerprint(items, key=lambda x: x.get("statement", ""))
    level2_result: list[dict] = []
    for group in groups:
        level2_result.append(merge_group(group))

    # Level 3 + 4: Near-duplicate and semantic equivalence
    final: list[dict] = []
    merged_indices: set[int] = set()

    for i, item_a in enumerate(level2_result):
        if i in merged_indices:
            continue
        group = [item_a]
        for j, item_b in enumerate(level2_result):
            if j <= i or j in merged_indices:
                continue
            text_a = item_a.get("statement", "")
            text_b = item_b.get("statement", "")
            if are_quasi_identical(text_a, text_b):
                group.append(item_b)
                merged_indices.add(j)
            elif are_semantically_equivalent(text_a, text_b):
                group.append(item_b)
                merged_indices.add(j)

        if len(group) > 1:
            final.append(merge_group(group))
        else:
            final.append(item_a)

    return final
