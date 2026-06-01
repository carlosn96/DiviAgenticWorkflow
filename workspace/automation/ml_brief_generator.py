#!/usr/bin/env python3
import json
import sys
import random
import argparse
import os
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
DAW_ROOT = SCRIPT_DIR.parent.parent
WEIGHTS_PATH = DAW_ROOT / "ml-dataset" / "module_weights.json"

# Content filler dictionaries to avoid LLM token costs
CONTENT_BANK = {
    "titles": [
        "Elevating Your Experience", "Discover The Difference", "Premium Services",
        "Our Core Values", "What We Do", "Innovating The Future", "Unmatched Quality"
    ],
    "paragraphs": [
        "We are dedicated to providing the highest quality of service. Our team of experts works tirelessly to ensure your satisfaction.",
        "Experience the next generation of solutions designed specifically for your needs. We blend technology with craftsmanship.",
        "Our approach is simple: we put our clients first. By understanding your goals, we create strategies that deliver measurable results.",
        "Join thousands of satisfied customers who have transformed their workflow with our premium suite of tools."
    ],
    "features": [
        {"title": "Fast Execution", "text": "Lightning fast delivery of all services."},
        {"title": "Premium Support", "text": "24/7 dedicated assistance for our clients."},
        {"title": "Secure Infrastructure", "text": "Enterprise-grade security protocols."},
        {"title": "Global Reach", "text": "Operating in over 50 countries worldwide."}
    ],
    "pricing_tiers": [
        {"tier": "Basic", "price": "$99", "features": "1 User, Basic Support, 10GB Storage"},
        {"tier": "Pro", "price": "$199", "features": "5 Users, Priority Support, 50GB Storage"},
        {"tier": "Enterprise", "price": "Custom", "features": "Unlimited Users, 24/7 Support, Unlimited Storage"}
    ],
    "testimonials": [
        {"name": "Sarah Jenkins", "role": "CEO", "text": "Absolutely transformative for our business."},
        {"name": "Mike Ross", "role": "Director", "text": "The best decision we made this year."},
        {"name": "Elena Smith", "role": "Founder", "text": "Incredible quality and attention to detail."}
    ]
}

def load_model():
    if not WEIGHTS_PATH.exists():
        print(f"Error: {WEIGHTS_PATH} not found. Run train_module_graph.py first.")
        sys.exit(1)
    with open(WEIGHTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def sample_next(transitions):
    if not transitions:
        return "END"
    choices = list(transitions.keys())
    weights = list(transitions.values())
    return random.choices(choices, weights=weights, k=1)[0]

def generate_module_sequence(model, length=6):
    """Generates a semantic sequence of Divi modules based on Markov probabilities."""
    sequence = []
    
    # Start with a high-probability start node (usually a heading or hero text)
    starts = model.get("start_probabilities", {})
    if starts:
        current = random.choices(list(starts.keys()), weights=list(starts.values()), k=1)[0]
    else:
        current = "dipl_double_color_heading"
        
    sequence.append(current)
    
    for _ in range(length - 1):
        transitions = model.get("transitions", {}).get(current, {})
        next_mod = sample_next(transitions)
        if next_mod == "END":
            break
        sequence.append(next_mod)
        current = next_mod
        
    return sequence

def translate_sequence_to_brief(sequence, title="ML Generated Page"):
    """
    Translates a sequence of raw Divi tags into a semantic brief.json compatible with Visual Impact Engine.
    """
    brief = {
        "title": title,
        "slug": title.lower().replace(" ", "-"),
        "tone": "premium",
        "description": "Generated via Markov Chain Module Graph",
        "sections": []
    }
    
    current_section = {}
    
    for mod in sequence:
        if mod in ("dipl_double_color_heading", "et_pb_text", "et_pb_heading", "dipl_advanced_heading"):
            if current_section and current_section.get("section_type") not in ("hero", "content"):
                brief["sections"].append(current_section)
                current_section = {}
            if not current_section:
                current_section = {
                    "section_type": "content",
                    "title": random.choice(CONTENT_BANK["titles"]),
                    "body": random.choice(CONTENT_BANK["paragraphs"])
                }
        
        elif mod in ("et_pb_accordion", "dipl_faq"):
            if current_section: brief["sections"].append(current_section)
            current_section = {
                "section_type": "faq",
                "title": "Frequently Asked Questions",
                "faqs": [
                    {"question": f["title"], "answer": f["text"]} for f in random.sample(CONTENT_BANK["features"], 3)
                ]
            }
            
        elif mod in ("et_pb_pricing_table", "dipl_price_list"):
            if current_section: brief["sections"].append(current_section)
            current_section = {
                "section_type": "pricing",
                "title": "Pricing Plans",
                "features": [{"title": t["tier"], "text": f"{t['price']} - {t['features']}"} for t in CONTENT_BANK["pricing_tiers"]]
            }
            
        elif mod in ("et_pb_contact_form",):
            if current_section: brief["sections"].append(current_section)
            current_section = {
                "section_type": "contact",
                "title": "Get In Touch",
                "text": "We would love to hear from you."
            }
            
        elif mod in ("et_pb_gallery", "dipl_masonry_gallery"):
            if current_section: brief["sections"].append(current_section)
            current_section = {
                "section_type": "gallery",
                "title": "Our Portfolio"
            }
            
        elif mod in ("et_pb_blurb", "dipl_image_card", "dipl_list", "dipl_list_item", "et_pb_icon"):
            if current_section and current_section.get("section_type") != "features":
                brief["sections"].append(current_section)
                current_section = {}
            if not current_section:
                current_section = {
                    "section_type": "features",
                    "title": "Our Expertise",
                    "features": random.sample(CONTENT_BANK["features"], 3)
                }
            
        elif mod in ("et_pb_testimonial", "dipl_testimonial_slider"):
            if current_section: brief["sections"].append(current_section)
            current_section = {
                "section_type": "testimonials",
                "title": "Client Success",
                "testimonials": random.sample(CONTENT_BANK["testimonials"], 2)
            }
            
        elif mod in ("dipl_timeline",):
            if current_section: brief["sections"].append(current_section)
            current_section = {
                "section_type": "process",
                "title": "Our Process",
                "features": random.sample(CONTENT_BANK["features"], 3)
            }
        else:
            # Fallback genérico para cualquier módulo desconocido
            if not current_section:
                current_section = {
                    "section_type": "features",
                    "title": "Additional Details",
                    "features": random.sample(CONTENT_BANK["features"], 2)
                }

    if current_section and current_section not in brief["sections"]:
        brief["sections"].append(current_section)
        
    # Ensure at least a hero section exists if the page is empty
    if not brief["sections"]:
        brief["sections"].append({
            "section_type": "hero",
            "title": title,
            "text": random.choice(CONTENT_BANK["paragraphs"])
        })

    return brief

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default="ML Landing Page", help="Page Title")
    parser.add_argument("--out", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    model = load_model()
    # Generate a rich sequence of 6-10 modules
    seq = generate_module_sequence(model, length=random.randint(6, 10))
    
    # Steering basado en query
    q_low = args.query.lower()
    if "contact" in q_low and "et_pb_contact_form" not in seq:
        seq.insert(random.randint(1, max(1, len(seq)-1)), "et_pb_contact_form")
    if ("precio" in q_low or "pricing" in q_low) and "et_pb_pricing_table" not in seq:
        seq.insert(random.randint(1, max(1, len(seq)-1)), "et_pb_pricing_table")
    if ("galeria" in q_low or "gallery" in q_low) and "et_pb_gallery" not in seq:
        seq.insert(random.randint(1, max(1, len(seq)-1)), "et_pb_gallery")

    print(f"[ML-BRIEF] Predicted module sequence: {' -> '.join(seq)}")
    
    brief = translate_sequence_to_brief(seq, title=args.query)
    
    out_path = args.out
    if not out_path:
        site_name = os.environ.get("DAW_SITE", "bibliotheca")
        out_dir = DAW_ROOT / "site" / site_name / "briefs"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{brief['slug']}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(brief, f, indent=2)

    print(f"[ML-BRIEF] Successfully exported ML Brief to: {out_path}")

if __name__ == "__main__":
    main()
