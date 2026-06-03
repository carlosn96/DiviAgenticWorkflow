from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from workspace.automation.ux_pro_brief_generator import generate_brief_for_page


def test_landing_brief_is_page_type_aware():
    brief = generate_brief_for_page("Landing page for a premium agency", brand="Aurea")

    assert brief["page_type"] == "landing"
    assert brief["tone"] == "premium"
    assert brief["design_direction"]["hero_layout"] == "asymmetric"
    assert len(brief["sections"]) >= 6
    assert [section["section_type"] for section in brief["sections"]] == [
        "hero",
        "trust-bar",
        "features",
        "stats",
        "testimonials",
        "cta",
    ]