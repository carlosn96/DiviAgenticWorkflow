#!/usr/bin/env python3
"""
augment_dataset.py — Cross-record structural mutation augmentation.

NO LLM. NO hardcoded domains. NO invented colors/texts.
Strategy: For each source record, find donors with similar slot profile
but different module composition, then swap colors + texts + re-label.

Algorithm:
  1. Load dataset.jsonl
  2. For each record, compute (slot_profile, module_signature, text_fingerprint)
  3. For each source, find top-N donors with:
     - slot_profile_distance < 0.20 (similar content shape)
     - module_signature != source (different template, ensures variety)
     - text content different enough (avoids self-augmentation)
  4. Mutate: source structure + donor colors + donor text labels → new record
  5. Deduplication via structural fingerprint
  6. Write dataset_augmented.jsonl
"""

import json, sys, math, warnings
from pathlib import Path
from collections import defaultdict
from hashlib import md5
from random import Random

import numpy as np

warnings.filterwarnings("ignore")

ARTIFACTS_DIR = Path(__file__).resolve().parent
DATASET_PATH = ARTIFACTS_DIR / "dataset.jsonl"
OUT_PATH = ARTIFACTS_DIR / "dataset_augmented.jsonl"

SEED = 42
MAX_DONORS_PER_SOURCE = 2
MAX_VARIANTS_PER_SOURCE = 3
SLOT_DISTANCE_THRESHOLD = 0.20
MIN_TEXT_DIFFERENCE = 0.30   # min fraction of different text tags for donor


def extract_slot_profile(record):
    so = record.get("slots_offered", {})
    keys = ["titles", "paragraphs", "buttons", "images",
            "features", "testimonials", "stats", "logos", "items"]
    return {k: so.get(k, 0) for k in keys}


def slot_profile_distance(a, b):
    keys = ["titles", "paragraphs", "buttons", "images",
            "features", "testimonials", "stats", "logos", "items"]
    ta = max(sum(a.get(k, 0) for k in keys), 1)
    tb = max(sum(b.get(k, 0) for k in keys), 1)
    diff = 0.0
    for k in keys:
        diff += abs(a.get(k, 0) / ta - b.get(k, 0) / tb)
    return diff / len(keys)


def module_signature(record):
    return tuple(sorted(set(t for t in record.get("module_types", [])
                            if not t.startswith("et_pb_section") and
                            not t.startswith("et_pb_row") and
                            not t.startswith("et_pb_column"))))


def text_tag_set(record):
    texts = record.get("content_texts", [])
    return {t.get("tag", "") if isinstance(t, dict) else "" for t in texts}


def tag_difference(a_tags, b_tags):
    """Fraction of tags in A not present in B (higher = more different)."""
    if not a_tags:
        return 1.0
    diff = a_tags - b_tags
    return len(diff) / len(a_tags)


def fingerprint(record):
    so = record.get("slots_offered", {})
    return (
        record.get("columns_count", 0),
        module_signature(record),
        so.get("titles", 0), so.get("paragraphs", 0),
        so.get("buttons", 0), so.get("images", 0),
        so.get("features", 0), so.get("testimonials", 0),
        so.get("stats", 0), so.get("logos", 0), so.get("items", 0),
    )


def color_pool(record):
    pool = defaultdict(list)
    for c in record.get("colors", []):
        val = c.get("value", "")
        if val.startswith("#") and 4 <= len(val) <= 9:
            pool[c.get("attribute", "color")].append(val)
    flat = []
    for vals in pool.values():
        flat.extend(vals)
    return flat


def mutate_colors(src_colors, donor_hex_pool):
    if not donor_hex_pool:
        return list(src_colors)
    rng = Random(SEED)
    result = []
    for c in src_colors:
        result.append({
            "attribute": c.get("attribute", "color"),
            "value": rng.choice(donor_hex_pool)
        })
    return result


def validate_slot_coverage(original, variant):
    orig_slots = extract_slot_profile(original)
    var_slots = extract_slot_profile(variant)
    keys = ["titles", "paragraphs", "buttons", "images",
            "features", "testimonials", "stats", "logos", "items"]
    for k in keys:
        if orig_slots[k] > 0 and var_slots[k] == 0:
            return False
    to = sum(orig_slots.values())
    tv = sum(var_slots.values())
    if to > 0 and tv / to < 0.70:
        return False
    return True


def augment(records):
    rng = Random(SEED)
    n = len(records)

    # Pre-compute indexes
    print(f"[AUG] Indexing {n} records...", file=sys.stderr)
    slots = [extract_slot_profile(r) for r in records]
    mod_sigs = [module_signature(r) for r in records]
    tags = [text_tag_set(r) for r in records]
    hex_pools = [color_pool(r) for r in records]

    existing_fps = {fingerprint(r) for r in records}

    # For each source, find compatible donors
    augmented = []
    sources_processed = 0
    variants_total = 0

    print(f"[AUG] Finding cross-record donors...", file=sys.stderr)
    for src_idx in range(n):
        if variants_total >= n * 2:  # Cap total augmentation at 2x
            break

        src_slots = slots[src_idx]
        src_mods = mod_sigs[src_idx]
        src_tags = tags[src_idx]
        src_record = records[src_idx]

        # Find donors: similar slots, different modules, different text content
        candidates = []
        for dst_idx in range(n):
            if dst_idx == src_idx:
                continue
            dst_slots = slots[dst_idx]
            dist = slot_profile_distance(src_slots, dst_slots)
            if dist > SLOT_DISTANCE_THRESHOLD:
                continue
            mod_diff = 1.0 if mod_sigs[dst_idx] != src_mods else 0.0
            tag_diff = tag_difference(src_tags, tags[dst_idx])
            if tag_diff < MIN_TEXT_DIFFERENCE:
                continue
            score = (1.0 - dist) * 0.4 + mod_diff * 0.3 + tag_diff * 0.3
            candidates.append((score, dst_idx))

        if not candidates:
            continue

        candidates.sort(key=lambda x: -x[0])
        variants_this_source = 0

        for _, donor_idx in candidates[:MAX_DONORS_PER_SOURCE]:
            if variants_this_source >= MAX_VARIANTS_PER_SOURCE:
                break
            donor = records[donor_idx]

            variant = dict(src_record)
            variant["source"] = f"{src_record.get('source','x')}|{donor.get('source','y')}"

            # Mutate colors from donor
            variant["colors"] = mutate_colors(variant.get("colors", []),
                                              hex_pools[donor_idx])[:80]

            # Use donor's content texts for re-labeling
            variant["content_texts"] = donor.get("content_texts", [])[:50]

            if not validate_slot_coverage(src_record, variant):
                continue

            fp = fingerprint(variant)
            donor_fp = fp + (donor_idx,)
            if donor_fp in existing_fps:
                continue

            existing_fps.add(donor_fp)
            augmented.append(variant)
            variants_this_source += 1
            variants_total += 1

        sources_processed += 1
        if sources_processed % 200 == 0:
            print(f"[AUG]   {sources_processed}/{n} sources, {variants_total} variants",
                  file=sys.stderr)

    print(f"[AUG] Generated {variants_total} augmented records from {sources_processed} sources",
          file=sys.stderr)

    # Domain stats  
    slot_summary = defaultdict(int)
    for rec in augmented:
        so = rec.get("slots_offered", {})
        for k, v in so.items():
            if v > 0:
                slot_summary[k] += 1
    for k in sorted(slot_summary):
        print(f"[AUG]   {k}: {slot_summary[k]} variants have this slot", file=sys.stderr)

    return augmented


def main():
    print("[AUG] Loading dataset...", file=sys.stderr)
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    print(f"[AUG] {len(records)} records", file=sys.stderr)

    augmented = augment(records)
    total = records + augmented

    print(f"[AUG] Total: {len(records)} orig + {len(augmented)} aug = {len(total)}",
          file=sys.stderr)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for rec in total:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[AUG] Written: {OUT_PATH}", file=sys.stderr)

    # Show before/after slot stats
    orig_so = defaultdict(int)
    for r in records:
        so = r.get("slots_offered", {})
        for k in so:
            if so[k] > 0:
                orig_so[k] += 1
    aug_so = defaultdict(int)
    for r in augmented:
        so = r.get("slots_offered", {})
        for k in so:
            if so[k] > 0:
                aug_so[k] += 1

    print(f"[AUG] Slot coverage before → after:", file=sys.stderr)
    for k in sorted(set(list(orig_so) + list(aug_so))):
        print(f"[AUG]   {k:15s}: {orig_so.get(k,0):4d} → {aug_so.get(k,0):4d}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
