import json
from pathlib import Path
import statistics

DATASET_JSONL = Path(__file__).parent.parent / "dataset.jsonl"
OUTPUT        = Path(__file__).parent / "slot_stats.json"

# Known mapping: brief slot type → Divi module tags (from e_page_mapper)
SLOT_TO_TAGS = {
    "title":    ["dipl_double_color_heading", "dipl_image_card", "et_pb_blurb", "et_pb_pricing_table"],
    "eyebrow":  ["et_pb_text"],
    "body":     ["et_pb_text"],
    "btn_primary_text":   ["dipl_button"],
    "btn_secondary_text": ["dipl_button"],
}

def main():
    lengths_by_tag = {}

    with open(DATASET_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            for ct in rec.get("content_texts", []):
                tag = ct["tag"]
                text = ct["text"]
                lengths_by_tag.setdefault(tag, []).append(len(text))

    stats = {}
    for tag, lengths in sorted(lengths_by_tag.items()):
        stats[tag] = {
            "mean": round(sum(lengths) / len(lengths), 1) if lengths else 0,
            "std": round(statistics.stdev(lengths), 1) if len(lengths) > 1 else 0,
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "count": len(lengths),
            "p10": sorted(lengths)[len(lengths)//10] if lengths else 0,
            "p90": sorted(lengths)[len(lengths)*9//10] if lengths else 0,
        }

    slot_stats = {}
    for slot, tags in SLOT_TO_TAGS.items():
        all_lengths = []
        for tag in tags:
            all_lengths.extend(lengths_by_tag.get(tag, []))
        if all_lengths:
            slot_stats[slot] = {
                "mean": round(sum(all_lengths) / len(all_lengths), 1),
                "std": round(statistics.stdev(all_lengths), 1) if len(all_lengths) > 1 else 0,
                "min": min(all_lengths),
                "max": max(all_lengths),
                "count": len(all_lengths),
                "p10": sorted(all_lengths)[len(all_lengths)//10],
                "p90": sorted(all_lengths)[len(all_lengths)*9//10],
                "source_tags": tags,
            }
        else:
            slot_stats[slot] = {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0, "p10": 0, "p90": 0, "source_tags": tags}

    slot_stats["_meta"] = {
        "source": "dataset.jsonl (877 templates, content_texts field)",
        "note": "All text values were truncated at 500 chars during extraction; max_observed=500 is an under-estimate for longer texts.",
        "slot_to_tags": SLOT_TO_TAGS,
    }

    OUTPUT.write_text(json.dumps(slot_stats, indent=2), encoding="utf-8")
    print(f"[OK] slot_stats.json written ({OUTPUT.stat().st_size} bytes)")
    for slot, s in sorted(slot_stats.items()):
        if slot == "_meta": continue
        print(f"  {slot:20s}: mean={s['mean']:>6.1f}  std={s['std']:>5.1f}  p10={s['p10']:>4d}  p90={s['p90']:>4d}  count={s['count']}")

if __name__ == "__main__":
    main()
