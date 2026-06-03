#!/usr/bin/env python3
"""Validate augmented dataset integrity and slot coverage"""
import json
from collections import Counter

with open("DAW_bundle/ml-dataset/dataset.jsonl", encoding="utf-8") as f:
    records = [json.loads(line) for line in f]

print("=== DATASET STATS ===")
print("Total records:", len(records))

sources = Counter(r["source"] for r in records)
print("=== SOURCE BREAKDOWN ===")
print("Unique sources:", len(sources))
print("Original (single):", sum(1 for v in sources.values() if v == 1))
print("Augmented (multi):", sum(1 for v in sources.values() if v > 1))
for s, c in sources.most_common(10):
    print("  %-50s %d" % (s[:50], c))

contents = [json.dumps(r, sort_keys=True) for r in records]
unique = set(contents)
print("Unique records: %d/%d (%d dups)" % (len(unique), len(records), len(records)-len(unique)))
if len(records) != len(unique):
    dup_counts = Counter(contents)
    for c, n in dup_counts.most_common(5):
        if n > 1:
            print("  Exact dup count=%d for: %s" % (n, c[:120]))

# Section type distribution from source names
print("=== SECTION TYPE INFERENCE (from source name keywords) ===")
type_keywords = {
    "hero": ["hero", "banner", "header", "cover", "slider"],
    "features": ["feature", "service", "offer", "capability", "solution"],
    "testimonials": ["testimonial", "review", "quote", "feedback"],
    "pricing": ["pricing", "price", "plan", "membership"],
    "cta": ["cta", "callout", "banner-cta", "subscribe", "newsletter"],
    "gallery": ["gallery", "portfolio", "showcase", "masonry"],
    "team": ["team", "people", "staff", "member", "about-us"],
    "about": ["about", "story", "mission", "value", "company"],
    "contact": ["contact", "location", "map", "address"],
    "blog": ["blog", "post", "article", "news", "journal"],
    "faq": ["faq", "question", "accordion", "toggle"],
    "countdown": ["countdown", "timer", "coming-soon", "event"],
    "stats": ["stat", "counter", "number", "achievement", "fact"],
    "footer": ["footer", "bottom", "foot"],
    "logos": ["logo", "client", "partner", "sponsor"],
    "product": ["product", "shop", "item", "card", "listing"],
    "timeline": ["timeline", "history", "process", "step"],
    "generic": [],
}
section_counts = Counter()
for r in records:
    name = r["source"].lower()
    found = "generic"
    for st, kws in type_keywords.items():
        if any(kw in name for kw in kws):
            found = st
            break
    section_counts[found] += 1
for st, c in section_counts.most_common():
    print("  %-15s: %4d (%5.1f%%)" % (st, c, c/len(records)*100))

# Slot coverage
slot_fields = ["items", "testimonials", "features", "stats", "logos", "buttons", "images", "titles", "paragraphs"]
print("=== SLOT COVERAGE ===")
for sf in slot_fields:
    c = sum(1 for r in records if r.get("slots_offered", {}).get(sf))
    print("  %-15s: %4d/%d (%5.1f%%)" % (sf, c, len(records), c/len(records)*100))

# Slot depth stats
print("=== SLOT DEPTH (avg per record with slot) ===")
for sf in slot_fields:
    vals = []
    for r in records:
        v = r.get("slots_offered", {}).get(sf)
        if v:
            vals.append(len(v) if isinstance(v, (list, tuple)) else int(v))
    if vals:
        print("  %-15s: avg=%.1f max=%d" % (sf, sum(vals)/len(vals), max(vals)))

# Content quality
print("=== CONTENT QUALITY ===")
lorem_cnt = 0
placeholder_cnt = 0
for r in records:
    text = json.dumps(r)
    if "lorem" in text.lower():
        lorem_cnt += 1
    if "placeholder" in text.lower():
        placeholder_cnt += 1
print("Records with lorem:", lorem_cnt)
print("Records with placeholder:", placeholder_cnt)
empty_cnt = sum(1 for r in records if not r.get("content_texts", []))
print("Empty content_texts:", empty_cnt)
no_mt = sum(1 for r in records if not r.get("module_types"))
print("Missing module_types:", no_mt)
no_shortcode = sum(1 for r in records if not r.get("raw_shortcode"))
print("Missing raw_shortcode:", no_shortcode)

# Check max content_texts length
text_lens = [len(r.get("content_texts", [])) for r in records]
if text_lens:
    print("Content texts lengths: min=%d max=%d avg=%.1f" % (min(text_lens), max(text_lens), sum(text_lens)/len(text_lens)))
