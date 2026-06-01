#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import argparse
import random
from pathlib import Path

# Fix paths to import ui-ux-pro-max
SCRIPT_DIR = Path(__file__).resolve().parent
DAW_ROOT = SCRIPT_DIR.parent.parent
UI_UX_DIR = DAW_ROOT / "ui-ux-pro-max" / "scripts"

sys.path.append(str(UI_UX_DIR))
try:
    from design_system import DesignSystemGenerator
except ImportError:
    print(f"Error: Could not import DesignSystemGenerator from {UI_UX_DIR}")
    sys.exit(1)

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
        {"title": "Global Reach", "text": "Operating in over 50 countries worldwide."},
        {"title": "Advanced Analytics", "text": "Gain actionable insights with our deep data reporting."}
    ],
    "pricing_tiers": [
        {"tier": "Basic", "price": "$99/mo", "features": "1 User, Basic Support, 10GB Storage"},
        {"tier": "Pro", "price": "$199/mo", "features": "5 Users, Priority Support, 50GB Storage"},
        {"tier": "Enterprise", "price": "Custom", "features": "Unlimited Users, 24/7 Support, Unlimited Storage"}
    ],
    "testimonials": [
        {"name": "Sarah Jenkins", "role": "CEO at TechCorp", "text": "Absolutely transformative for our business. The ROI was immediate."},
        {"name": "Mike Ross", "role": "Director of Operations", "text": "The best decision we made this year. Streamlined everything."},
        {"name": "Elena Smith", "role": "Founder, StartupX", "text": "Incredible quality and attention to detail. Highly recommended."}
    ],
    "portfolio": [
        {"title": "Project Alpha", "category": "Web Design"},
        {"title": "Project Beta", "category": "App Development"},
        {"title": "Project Gamma", "category": "Branding"}
    ],
    "timeline": [
        {"title": "Phase 1: Discovery", "text": "We map out your needs and requirements."},
        {"title": "Phase 2: Execution", "text": "Our team starts building the solution."},
        {"title": "Phase 3: Delivery", "text": "Final review and deployment to production."}
    ]
}

def translate_section(section_name):
    """Translates a UX-Pro semantic section name into a brief schema section."""
    section_name = section_name.lower().strip()
    
    if "hero" in section_name:
        return {
            "section_type": "hero",
            "eyebrow": "WELCOME",
            "title": "Welcome to the Future",
            "text": random.choice(CONTENT_BANK["paragraphs"]),
            "btn_primary_text": "Explore More",
            "btn_primary_url": "/",
            "image": ""
        }
    elif "feature" in section_name or "content" in section_name or "service" in section_name:
        return {
            "section_type": "features",
            "eyebrow": "WHAT WE DO",
            "title": random.choice(CONTENT_BANK["titles"]),
            "items": [{
                "title": f["title"],
                "icon": random.choice(["\u0026#xe03a;", "\u0026#xe065;", "\u0026#xe0bf;", "\u0026#xe050;", "\u0026#xe052;"]),
                "text": f["text"]
            } for f in random.sample(CONTENT_BANK["features"], 3)]
        }
    elif "faq" in section_name or "question" in section_name:
        return {
            "section_type": "faq",
            "eyebrow": "FAQ",
            "title": "Frequently Asked Questions",
            "faqs": [{"question": f["title"], "answer": f["text"]} for f in random.sample(CONTENT_BANK["features"], 3)]
        }
    elif "pricing" in section_name or "cost" in section_name:
        return {
            "section_type": "pricing",
            "eyebrow": "PLANS",
            "title": "Pricing Plans",
            "features": [{"title": t["tier"], "subtitle": t["price"], "price": t["price"], "text": t["features"]} for t in CONTENT_BANK["pricing_tiers"]]
        }
    elif "contact" in section_name:
        return {
            "section_type": "contact",
            "eyebrow": "CONTACT",
            "title": "Get In Touch",
            "text": "We would love to hear from you. Fill out the form below.",
            "btn_primary_text": "Send Message",
            "btn_primary_url": "/contact"
        }
    elif "cta" in section_name or "booking" in section_name or "action" in section_name:
        return {
            "section_type": "cta",
            "eyebrow": "TAKE ACTION",
            "title": "Ready to Begin?",
            "text": "Start your journey today with a free consultation.",
            "btn_primary_text": "Book Now",
            "btn_primary_url": "/book"
        }
    elif "testimonial" in section_name or "social proof" in section_name or "review" in section_name or "trust" in section_name:
        return {
            "section_type": "testimonials",
            "eyebrow": "TESTIMONIALS",
            "title": "Client Success Stories",
            "testimonials": random.sample(CONTENT_BANK["testimonials"], 3)
        }
    elif "gallery" in section_name or "image" in section_name or "grid" in section_name:
        # Gallery real con portfolio items ricos
        return {
            "section_type": "gallery",
            "eyebrow": "GALLERY",
            "title": "Our Portfolio",
            "subtitle": "A glimpse of our latest work",
            "items": [{"image": "", "alt": p["title"], "title": p["title"]} for p in random.sample(CONTENT_BANK["portfolio"], 3)]
        }
    elif "timeline" in section_name or "process" in section_name or "how it works" in section_name:
        return {
            "section_type": "process",
            "eyebrow": "PROCESS",
            "title": "Our Process",
            "phases": CONTENT_BANK["timeline"]
        }
    elif "stats" in section_name or "number" in section_name or "metrics" in section_name or "counter" in section_name:
        return {
            "section_type": "stats",
            "stats": [
                {"number": "150+", "label": "Projects Delivered"},
                {"number": "98%", "label": "Client Satisfaction"},
                {"number": "24/7", "label": "Support Available"},
                {"number": "50+", "label": "Countries"}
            ]
        }
    elif "team" in section_name or "people" in section_name or "staff" in section_name:
        return {
            "section_type": "team",
            "eyebrow": "OUR TEAM",
            "title": "Meet the Experts",
            "members": [
                {"name": "Sarah Jenkins", "role": "CEO", "text": "Visionary leader with 15+ years of experience."},
                {"name": "Mike Ross", "role": "CTO", "text": "Technical genius driving innovation."},
                {"name": "Elena Smith", "role": "Design Lead", "text": "Award-winning creative director."}
            ]
        }
    elif "icon-list" in section_name or "list" in section_name or "bullet" in section_name:
        return {
            "section_type": "icon-list",
            "eyebrow": "HIGHLIGHTS",
            "title": "Key Points",
            "items": [{
                "title": f["title"],
                "icon": random.choice(["\u0026#xe03a;", "\u0026#xe065;", "\u0026#xe0bf;"]),
                "text": f["text"]
            } for f in random.sample(CONTENT_BANK["features"], 4)]
        }
    else:
        # Fallback: content split con body/text fallback
        return {
            "section_type": "content",
            "eyebrow": "ABOUT",
            "title": section_name.title(),
            "text": random.choice(CONTENT_BANK["paragraphs"]),
            "image": ""
        }

def generate_brief(query):
    # 1. Use UX-Pro BM25 engine to extract deterministic design system
    generator = DesignSystemGenerator()
    ds = generator.generate(query)
    
    # 2. Extract sections, handling both ',' from landing.csv and '>' from fallback
    # To truly harness UX-Pro, if sections is the fallback, we search landing.csv using the Pattern Name!
    pattern_name = ds.get("pattern", {}).get("name", "")
    sections_str = ds.get("pattern", {}).get("sections", "Hero > Features > CTA")
    
    if sections_str == "Hero > Features > CTA" and pattern_name:
        from core import search
        res = search(pattern_name, "landing", 1)
        results_list = res.get("results", [])
        if results_list:
            sections_str = results_list[0].get("Section Order", sections_str)
            
    # Clean out numbers like "1. ", "2. " from strings
    import re
    sections_str = re.sub(r'\d+\.\s*', '', sections_str)
    
    if "," in sections_str:
        section_names = [s.strip() for s in sections_str.split(",") if s.strip()]
    else:
        section_names = [s.strip() for s in sections_str.split(">") if s.strip()]
    
    brief = {
        "title": query,
        "slug": query.lower().replace(" ", "-"),
        "tone": "premium",
        "description": f"Generated via UX-Pro Deterministic Engine. Category: {ds.get('category')} | Pattern: {ds.get('pattern', {}).get('name')}",
        "sections": []
    }
    
    # 3. Translate to Divi Schema
    for sec_name in section_names:
        brief["sections"].append(translate_section(sec_name))
        
    return brief

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default="Landing Page", help="Page Title / Category")
    parser.add_argument("--out", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    brief = generate_brief(args.query)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(brief, f, indent=2, ensure_ascii=False)
        print(f"UX-Pro Deterministic Brief generated at {args.out}")
    else:
        print(json.dumps(brief, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
