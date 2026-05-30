#!/usr/bin/env python3
import os
import sys
import argparse
import pickle
import json
import math
import re
from pathlib import Path
from collections import Counter

os.environ["CUDA_VISIBLE_DEVICES"] = ""

def build_vocab(items):
    words = set()
    for item in items:
        name = item.get("name", "")
        cat = item.get("category", "")
        for token in re.findall(r'\w+', name.lower() + " " + cat.lower()):
            words.add(token)
    return {w: i for i, w in enumerate(sorted(words))}

def vectorize(text, vocab):
    vec = [0.0] * len(vocab)
    tokens = re.findall(r'\w+', text.lower())
    counts = Counter(tokens)
    for word, count in counts.items():
        if word in vocab:
            vec[vocab[word]] = count
    n = math.sqrt(sum(v * v for v in vec))
    if n > 0:
        vec = [v / n for v in vec]
    return vec

def cosine_sim(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    return dot

def main():
    parser = argparse.ArgumentParser(description="Query the Divi Plus semantic catalog locally.")
    parser.add_argument("--query", required=True, help="Search query (e.g., 'bento features grid')")
    parser.add_argument("--category", help="Constrain search to a specific category (e.g., 'about', 'hero', 'contact')")
    parser.add_argument("--limit", type=int, default=5, help="Number of results to return (default: 5)")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format (default: json)")

    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    pkl_path = script_dir.parent / "catalog" / "embeddings.pkl"

    if not pkl_path.exists():
        print(f"Error: Embeddings file not found.", file=sys.stderr)
        return 1

    with open(pkl_path, "rb") as f:
        data = pickle.load(f)

    catalog_items = data["items"]

    indices = list(range(len(catalog_items)))
    if args.category:
        target_cat = args.category.lower().strip()
        if target_cat == 'hero-centered':
            target_cat = 'hero'
        elif target_cat == 'content' or target_cat == 'content-list':
            target_cat = 'features'
        filtered = []
        for idx, item in enumerate(catalog_items):
            if item.get("category", "generic").lower().strip() == target_cat:
                filtered.append(idx)
        if filtered:
            indices = filtered
        else:
            print(f"Warning: No catalog items in '{target_cat}'. Searching all.", file=sys.stderr)

    vocab = build_vocab(catalog_items)
    query_vec = vectorize(args.query, vocab)

    scored = []
    for idx in indices:
        item = catalog_items[idx]
        name = item.get("name", "")
        cat = item.get("category", "")
        text = f"{name} {cat}"
        item_vec = vectorize(text, vocab)
        score = cosine_sim(query_vec, item_vec)
        scored.append((score, idx))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:args.limit]

    results = []
    for score, idx in top:
        item = catalog_items[idx]
        results.append({
            "name": item["name"],
            "path": item["path"],
            "category": item.get("category", "generic"),
            "score": round(score, 4)
        })

    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(f"\nSearch results for: '{args.query}'" + (f" in category: '{args.category}'" if args.category else ""))
        print("-" * 60)
        for i, res in enumerate(results, 1):
            print(f"{i}. {res['name']} [{res['category']}] (Score: {res['score']:.4f})")
            print(f"   Path: {res['path']}\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
