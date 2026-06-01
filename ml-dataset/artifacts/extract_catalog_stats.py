import json, re, pickle, statistics
from pathlib import Path

DATASET_JSONL = Path(__file__).parent.parent / "dataset.jsonl"
CLUSTER_PKL   = Path(__file__).parent / "decoration-clusters.pkl"
OUTPUT        = Path(__file__).parent / "catalog_stats.json"

PADDING_RE = re.compile(r'custom_padding="([^"]*)"')

def parse_padding(val: str):
    parts = val.split("|")
    def to_px(s):
        s = s.strip()
        if not s or s == "false":
            return None
        if s.endswith("px"):
            return float(s[:-2])
        if s.endswith("%"):
            return float(s[:-1]) * 0.16  # rough: 1% ≈ 1.6px at 1000px container
        try:
            return float(s)
        except:
            return None
    top = to_px(parts[0]) if len(parts) > 0 else None
    bot = to_px(parts[2]) if len(parts) > 2 else None
    return top, bot

def main():
    with open(CLUSTER_PKL, "rb") as f:
        data = pickle.load(f)
    km = data["kmeans"]
    labels = km.labels_.tolist()
    n_clusters = km.n_clusters

    tops = {i: [] for i in range(n_clusters)}
    bots = {i: [] for i in range(n_clusters)}

    with open(DATASET_JSONL, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                rec = json.loads(line)
            except:
                continue
            src = rec.get("raw_shortcode", "")
            matches = PADDING_RE.findall(src)
            if not matches:
                continue
            cluster = labels[idx] if idx < len(labels) else None
            if cluster is None:
                continue
            for val in matches:
                top, bot = parse_padding(val)
                if top is not None:
                    tops[cluster].append(top)
                if bot is not None:
                    bots[cluster].append(bot)

    stats = {}
    for c in range(n_clusters):
        t = tops[c]
        b = bots[c]
        stats[f"cluster_{c}"] = {}
        for name, values in [("padding_top", t), ("padding_bottom", b)]:
            if values:
                stats[f"cluster_{c}"][name] = {
                    "mean": round(statistics.mean(values), 1),
                    "std": round(statistics.stdev(values), 1) if len(values) > 1 else 0.0,
                    "min": round(min(values), 1),
                    "max": round(max(values), 1),
                    "count": len(values),
                    "p10": round(sorted(values)[len(values)//10], 1),
                    "p90": round(sorted(values)[len(values)*9//10], 1),
                }
            else:
                stats[f"cluster_{c}"][name] = {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0, "p10": 0, "p90": 0}

    stats["_meta"] = {
        "source": "dataset.jsonl (877 templates, custom_padding from raw_shortcode)",
        "clusters": n_clusters,
        "cluster_labels_kmeans": "kmeans.labels_ aligned by dataset index",
    }

    OUTPUT.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"[OK] catalog_stats.json written ({OUTPUT.stat().st_size} bytes)")
    for c in range(n_clusters):
        t = stats[f"cluster_{c}"]["padding_top"]
        b = stats[f"cluster_{c}"]["padding_bottom"]
        print(f"  cluster_{c}: top={t['mean']}±{t['std']} bot={b['mean']}±{b['std']} (n_top={t['count']} n_bot={b['count']})")

if __name__ == "__main__":
    main()
