#!/usr/bin/env python3
import os
import re
import json
import pickle
import sys
from pathlib import Path

# Force CPU execution to keep it simple and consistent on CPU-only local environments
os.environ["CUDA_VISIBLE_DEVICES"] = ""

def clean_text_from_shortcodes(content_str: str) -> str:
    """Strip shortcodes and HTML tags to extract clean readable text."""
    # Remove HTML tags: <p>Success</p> -> Success
    text = re.sub(r'<[^>]+>', ' ', content_str)
    # Remove shortcodes brackets: [et_pb_text ...] -> space
    text = re.sub(r'\[[^\]]+\]', ' ', text)
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_metadata_from_json(json_path: Path) -> tuple[str, str]:
    """Reads a Divi JSON and extracts content for embedding enrichment and raw shortcode text."""
    try:
        data = json.loads(json_path.read_text(encoding='utf-8', errors='ignore'))
        
        # Extract shortcode strings from the data payload
        raw_shortcode = ""
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], dict):
                for val in data["data"].values():
                    if isinstance(val, str):
                        raw_shortcode += " " + val
            elif "context" in data and isinstance(data.get("data"), str):
                raw_shortcode = data["data"]

        if not raw_shortcode:
            return "", ""

        # Extract attributes of interest: title="...", admin_label="..."
        attributes = []
        for match in re.finditer(r'(?:title|admin_label)="([^"]+)"', raw_shortcode):
            attributes.append(match.group(1))

        # Extract clean plain text content
        plain_text = clean_text_from_shortcodes(raw_shortcode)
        
        # Combine folder name, special attributes and first 400 chars of body text
        combined = " ".join(attributes) + " " + plain_text
        return combined[:400], raw_shortcode
    except Exception as e:
        print(f"Warning: Failed to parse text from {json_path}: {e}", file=sys.stderr)
        return "", ""

def main():
    # Setup paths relative to the script location (which is in workspace/automation)
    script_dir = Path(__file__).parent.resolve()
    daw_root = script_dir.parent.parent
    
    # jsons folder is in workspace/catalog/jsons
    jsons_dir = script_dir.parent / "catalog" / "jsons"
    output_pkl = script_dir.parent / "catalog" / "embeddings.pkl"

    if not jsons_dir.exists():
        print(f"Error: Directory not found: {jsons_dir}", file=sys.stderr)
        return 1

    # Import extract_patterns for categorization
    sys.path.append(str(daw_root / "workspace"))
    try:
        from extract_patterns import extract_divi_info, categorize_section
    except ImportError as e:
        print(f"Error: Cannot import extract_patterns: {e}", file=sys.stderr)
        return 1

    # Suppress HF Hub stderr noise during model loading
    import contextlib
    print("Loading SentenceTransformer model ('all-MiniLM-L6-v2')...")
    with open(os.devnull, "w", encoding="utf-8") as devnull, contextlib.redirect_stderr(devnull):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')

    print(f"Scanning folder: {jsons_dir}")
    catalog_items = []
    
    # Sort subdirectories to maintain deterministic order
    subdirs = sorted([d for d in jsons_dir.iterdir() if d.is_dir()])
    
    for subdir in subdirs:
        # Look for the first JSON file inside the subdirectory
        json_files = list(subdir.glob("*.json"))
        if not json_files:
            continue
        
        json_path = json_files[0]
        folder_name = subdir.name
        
        # Extract additional text metadata to make vector representation more precise
        enriched_text, raw_shortcode = extract_metadata_from_json(json_path)
        
        # Categorize
        category = 'generic'
        try:
            if raw_shortcode:
                info = extract_divi_info(raw_shortcode, folder_name, str(json_path))
            else:
                info = {'modules': [], 'section_count': 0, 'row_count': 0, 'module_count': 0}
            category = categorize_section(folder_name, info)
        except Exception as e:
            try:
                category = categorize_section(folder_name, {'modules': [], 'section_count': 0, 'row_count': 0, 'module_count': 0})
            except:
                category = 'generic'
        
        # Final text to embed: Folder name (strong weight) + internal metadata
        text_to_embed = f"{folder_name} | {enriched_text}".strip()
        
        catalog_items.append({
            "name": folder_name,
            "path": str(json_path.resolve()),
            "text_to_embed": text_to_embed,
            "category": category
        })

    if not catalog_items:
        print("No JSON files found to index.", file=sys.stderr)
        return 1

    print(f"Indexing {len(catalog_items)} layout templates...")
    texts = [item["text_to_embed"] for item in catalog_items]
    
    # Generate embeddings (shape: [num_items, 384])
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    # Save to pickle file
    print(f"Saving embeddings and metadata to: {output_pkl}")
    # Ensure catalog folder exists
    output_pkl.parent.mkdir(parents=True, exist_ok=True)
    with open(output_pkl, "wb") as f:
        pickle.dump({
            "items": catalog_items,
            "embeddings": embeddings
        }, f)

    print("Success! Catalog successfully indexed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
