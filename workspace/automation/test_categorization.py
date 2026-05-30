#!/usr/bin/env python3
import os
import sys
import json
import re
from pathlib import Path

# Setup paths
script_dir = Path(__file__).parent.resolve()
daw_root = script_dir.parent.parent
jsons_dir = script_dir.parent / "catalog" / "jsons"

sys.path.append(str(daw_root / "workspace"))
from extract_patterns import extract_divi_info, categorize_section

def clean_text_from_shortcodes(content_str: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', content_str)
    text = re.sub(r'\[[^\]]+\]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_metadata_from_json(json_path: Path) -> tuple[str, str]:
    try:
        data = json.loads(json_path.read_text(encoding='utf-8', errors='ignore'))
        raw_shortcode = ""
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], dict):
                for val in data["data"].values():
                    if isinstance(val, str):
                        raw_shortcode += " " + val
            elif "context" in data and isinstance(data.get("data"), str):
                raw_shortcode = data["data"]
        return "", raw_shortcode
    except:
        return "", ""

def main():
    if not jsons_dir.exists():
        print(f"Error: Directory not found: {jsons_dir}")
        return 1

    subdirs = sorted([d for d in jsons_dir.iterdir() if d.is_dir()])
    
    # Track classifications for verification
    category_counts = {}
    mismatches = []
    
    print("Running light-weight dry-run categorization check...")
    print("-" * 50)
    
    for subdir in subdirs:
        json_files = list(subdir.glob("*.json"))
        if not json_files:
            continue
        
        json_path = json_files[0]
        folder_name = subdir.name
        
        _, raw_shortcode = extract_metadata_from_json(json_path)
        
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
        
        category_counts[category] = category_counts.get(category, 0) + 1
        
        # Check for obvious mismatches between folder name and category
        name_lower = folder_name.lower()
        if "about" in name_lower and category != "about":
            # Avoid false positives: if folder has contact or testimonials or shop, it might be categorized as such
            if not ("contact" in name_lower and category == "contact") and not ("testimonial" in name_lower and category == "testimonials") and not ("shop" in name_lower and category == "product"):
                mismatches.append(f"Folder: '{folder_name}' | Categorized as: '{category}' (expected 'about')")
        elif "hero" in name_lower and category != "hero":
            mismatches.append(f"Folder: '{folder_name}' | Categorized as: '{category}' (expected 'hero')")
        elif "testimonial" in name_lower and category != "testimonials":
            mismatches.append(f"Folder: '{folder_name}' | Categorized as: '{category}' (expected 'testimonials')")
        elif "contact" in name_lower and category != "contact":
            mismatches.append(f"Folder: '{folder_name}' | Categorized as: '{category}' (expected 'contact')")
        elif "pricing" in name_lower and category != "pricing":
            mismatches.append(f"Folder: '{folder_name}' | Categorized as: '{category}' (expected 'pricing')")
        elif "stats" in name_lower and category != "stats":
            mismatches.append(f"Folder: '{folder_name}' | Categorized as: '{category}' (expected 'stats')")
            
        # Log specific templates mentioned in the user's issue to verify them
        if any(x in folder_name for x in ["Fashion Influencer", "Healthcare", "Kindergarten"]):
            print(f"[VERIFY] Folder: {folder_name:30s} -> Category: {category}")
            
    print("\n" + "=" * 50)
    print("CATEGORIZATION DISTRIBUTION SUMMARY:")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:15s}: {count}")
    print("=" * 50)
    
    if mismatches:
        print(f"\n[ALERT] Found {len(mismatches)} potential folder-to-category mismatches:")
        for m in mismatches[:15]:
            print(f"  - {m}")
        if len(mismatches) > 15:
            print(f"  ... and {len(mismatches)-15} more.")
    else:
        print("\n[SUCCESS] No obvious folder-to-category mismatches found!")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
