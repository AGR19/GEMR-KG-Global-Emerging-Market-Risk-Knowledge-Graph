"""
Deterministic dev / held-out-test split for the GEMR-KG benchmark.

Rationale
---------
Prompt tuning against questions whose failures we've already inspected biases the
reported numbers. We freeze a stratified-random split (seed=42) up front: the
pipeline prompt may only be adjusted in response to DEV failures, and the final
headline numbers are reported on TEST, which the prompt never sees during tuning.

Ratio is ~60/40 (dev / test) stratified by tier so each tier contributes to both
splits. For 27 questions: 10 dev, 17 test.
"""

import random
from evaluation.questions import TEST_QUESTIONS

SEED = 42
DEV_RATIO = 0.37  # → 10/27 dev, 17/27 test


def _split_by_tier(qs, ratio: float, seed: int):
    tiers: dict[str, list] = {}
    for q in qs:
        tiers.setdefault(q.tier, []).append(q)

    rng = random.Random(seed)
    dev_ids, test_ids = [], []
    for tier in sorted(tiers):
        pool = sorted(tiers[tier], key=lambda q: q.id)
        rng.shuffle(pool)
        n_dev = max(1, round(len(pool) * ratio))
        dev_ids.extend(q.id for q in pool[:n_dev])
        test_ids.extend(q.id for q in pool[n_dev:])
    return sorted(dev_ids), sorted(test_ids)


DEV_IDS, TEST_IDS = _split_by_tier(TEST_QUESTIONS, DEV_RATIO, SEED)


def filter_questions(questions, split: str):
    """Filter a question list by split name ('dev', 'test', 'all')."""
    if split == "all":
        return questions
    if split == "dev":
        keep = set(DEV_IDS)
    elif split == "test":
        keep = set(TEST_IDS)
    else:
        raise ValueError(f"split must be 'dev', 'test', or 'all' (got {split!r})")
    return [q for q in questions if q.id in keep]


if __name__ == "__main__":
    print(f"DEV  ({len(DEV_IDS):2d}): {', '.join(DEV_IDS)}")
    print(f"TEST ({len(TEST_IDS):2d}): {', '.join(TEST_IDS)}")
