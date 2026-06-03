"""Premium Pipeline E2E Test — validates CSS flows from VIE → build_page.php → Layout Engine → WP.

Run: python -m pytest DAW_bundle/tests/test_premium_pipeline.py -v
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from vie.factory import create_vie

DS_PATH = Path("DAW_bundle/site/nomade/design-system/divitheme.json")
PLAN_DIR = Path("DAW_bundle/site/nomade/plans")
PAGE_DIR = Path("DAW_bundle/site/nomade/pages")


def _generate_plan(mood="warm_minimal"):
    ds = json.loads(DS_PATH.read_text(encoding="utf-8"))
    vie = create_vie(ds)
    brief = {
        "title": f"Premium Test {mood}",
        "slug": f"premium-test-{mood}",
        "design_direction": {"mood": mood},
        "sections": [
            {"section_type": "hero", "eyebrow": "TEST", "title": "Premium Page", "text": "Body."},
            {"section_type": "features", "items": [{"title": "A", "text": "B"}, {"title": "C", "text": "D"}]},
            {"section_type": "stats", "stats": [{"number": "1", "label": "X"}, {"number": "2", "label": "Y"}]},
            {"section_type": "cta", "title": "CTA", "btn_primary_text": "Go", "btn_primary_url": "/go"},
        ],
    }
    return vie.translate_brief(brief)


class TestVIEPremiumOutput:
    """Test 1: VIE generates CSS in plan.json."""

    def test_hero_section_has_css(self):
        plan = _generate_plan()
        hero = plan["sections"][0]
        assert "css" in hero, "Hero section missing 'css' field"

    def test_hero_css_has_freeform(self):
        plan = _generate_plan()
        hero = plan["sections"][0]
        css = hero["css"]
        assert "desktop" in css
        desktop_css = css["desktop"]
        if isinstance(desktop_css, dict):
            ff = desktop_css.get("value", {}).get("freeForm", "")
        else:
            ff = desktop_css
        assert len(ff) > 50, f"Hero freeForm CSS too short ({len(ff)} chars)"

    def test_hero_css_has_orb_glow(self):
        plan = _generate_plan()
        hero = plan["sections"][0]
        ff = hero["css"]["desktop"]["value"]["freeForm"]
        assert "radial-gradient" in ff, "Orb glow missing from hero CSS"

    def test_hero_css_has_grain(self):
        plan = _generate_plan("warm_minimal")
        hero = plan["sections"][0]
        ff = hero["css"]["desktop"]["value"]["freeForm"]
        assert "feTurbulence" in ff or "svg" in ff.lower(), "Grain texture missing"

    def test_hero_css_has_blur_reveal_keyframes(self):
        plan = _generate_plan()
        hero = plan["sections"][0]
        ff = hero["css"]["desktop"]["value"]["freeForm"]
        assert "revealUp" in ff or "@keyframes" in ff, "Blur-reveal keyframes missing"

    def test_cta_section_has_css(self):
        plan = _generate_plan()
        cta = plan["sections"][3]
        assert "css" in cta, "CTA section missing 'css' field"

    def test_stats_css_has_column_dividers(self):
        plan = _generate_plan()
        stats = plan["sections"][2]
        ff = stats["css"]["desktop"]["value"]["freeForm"]
        assert "divider" in ff or "column" in ff or "after" in ff, "Column dividers missing from stats CSS"

    def test_hero_modules_have_css(self):
        plan = _generate_plan()
        hero = plan["sections"][0]
        mods = hero["rows"][0]["columns"][0]["modules"]
        css_mods = [m for m in mods if "css" in m]
        assert len(css_mods) > 0, "No hero modules have 'css' field"

    def test_stagger_delays_progress(self):
        plan = _generate_plan()
        hero = plan["sections"][0]
        mods = hero["rows"][0]["columns"][0]["modules"]
        delays = []
        for m in mods:
            ff = m.get("css", {}).get("desktop", {}).get("value", {}).get("freeForm", "")
            if "animation" in ff:
                import re
                match = re.search(r"(\d+)ms both", ff)
                if match:
                    delays.append(int(match.group(1)))
        if len(delays) >= 2:
            assert delays[-1] > delays[0], f"Stagger delays not progressive: {delays}"

    def test_hero_radial_gradient_decoration(self):
        plan = _generate_plan()
        hero = plan["sections"][0]
        bg = hero.get("decoration", {}).get("background", {})
        bg_str = json.dumps(bg)
        assert "radial" in bg_str, "Hero decoration uses overlay, not radial gradient"

    def test_stats_dark_background(self):
        plan = _generate_plan("warm_minimal")
        stats = plan["sections"][2]
        bg_color = stats.get("decoration", {}).get("background", {}).get("desktop", {}).get("value", {}).get("color", "")
        assert bg_color == "#1A110A", f"Stats bg should be dark, got: {bg_color}"

    def test_responsive_spacing_hero(self):
        plan = _generate_plan()
        hero = plan["sections"][0]
        spacing = hero.get("decoration", {}).get("spacing", {})
        assert "tablet" in spacing, "Hero lacks responsive tablet spacing"

    def test_all_moods_generate_css(self):
        for mood in ["academic_night", "cool_luxury", "warm_minimal", "tech_glass", "organic_modern"]:
            plan = _generate_plan(mood)
            hero = plan["sections"][0]
            assert "css" in hero, f"Mood '{mood}' hero missing 'css' field"


class TestBuildPagePreservesCSS:
    """Test 2: build_page.php preserves CSS in the built schema."""

    @classmethod
    def setup_class(cls):
        plan = _generate_plan()
        slug = "premium-pipeline-test"
        plan_path = PLAN_DIR / f"{slug}.json"
        out_path = PAGE_DIR / f"{slug}.json"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
        php_bat = str(Path("php.bat").resolve())
        result = subprocess.run(
            [php_bat, str(Path("DAW_bundle/divi-agentic-core/bin/build_page.php").resolve()),
             f"--def={plan_path}", f"--out={out_path}"],
            capture_output=True, text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"build_page.php failed: {result.stderr}"
        cls.schema = json.loads(out_path.read_text(encoding="utf-8"))

    def test_schema_hero_has_css(self):
        hero = self.schema["sections"][0]
        assert "css" in hero, "Hero section CSS lost in build_page.php"

    def test_schema_hero_freeform_nonempty(self):
        hero = self.schema["sections"][0]
        ff = hero["css"]["desktop"]["value"]["freeForm"]
        assert len(ff) > 50, f"Hero freeForm too short after build: got {len(ff)} chars"

    def test_schema_hero_modules_have_css(self):
        hero = self.schema["sections"][0]
        mods = hero["rows"][0]["columns"][0]["modules"]
        css_mods = [m for m in mods if "css" in m]
        assert len(css_mods) > 0, "Hero modules lost CSS in build_page.php"

    def test_schema_cta_has_css(self):
        cta = self.schema["sections"][3]
        assert "css" in cta, "CTA CSS lost in build_page.php"


class TestVolcadoBugs:
    """Tests that catch bugs found by auditing deployed post_content.

    These verify the VIE output before it reaches the Layout Engine.
    The previous version had: decoration:[] on blurbs, 'subtlems' delays,
    overlay overwriting radial gradients, stats with wrong background.
    """

    def test_features_blurbs_have_card_decoration(self):
        plan = _generate_plan()
        features = plan["sections"][1]
        blurbs = []
        for row in features.get("rows", []):
            for col in row.get("columns", []):
                for mod in col.get("modules", []):
                    if mod.get("type") == "divi/blurb":
                        blurbs.append(mod)
        assert len(blurbs) > 0, "No blurbs found in features section"
        for b in blurbs:
            deco = b.get("decoration", {})
            assert deco != {} and deco != [], f"Blurb has empty decoration: {deco}"
            assert "background" in deco or "border" in deco, f"Blurb missing card styling: {list(deco.keys())}"

    def test_features_blurbs_have_backdrop_saturate(self):
        plan = _generate_plan("warm_minimal")
        features = plan["sections"][1]
        for row in features.get("rows", []):
            for col in row.get("columns", []):
                for mod in col.get("modules", []):
                    if mod.get("type") != "divi/blurb":
                        continue
                    deco = mod.get("decoration", {})
                    bf = deco.get("filter", {}).get("desktop", {}).get("value", {}).get("backdropFilter", "")
                    assert "saturate" in bf, f"backdropFilter missing saturate: '{bf}'"

    def test_no_subtlems_delays(self):
        plan = _generate_plan()
        plan_str = json.dumps(plan)
        assert "subtlems" not in plan_str, "Found 'subtlems' — stagger_delay kwargs bug"
        assert "subtlesubtle" not in plan_str, "Found 'subtlesubtle' — stagger_delay kwargs bug"

    def test_animation_delays_are_numeric(self):
        plan = _generate_plan()
        plan_str = json.dumps(plan)
        import re
        delays = re.findall(r'"delay":"([^"]*)"', plan_str)
        for d in delays:
            assert d.replace("ms", "").replace("-", "").isdigit(), f"Non-numeric delay: '{d}'"

    def test_compose_background_does_not_overwrite_hero_gradient(self):
        plan = _generate_plan()
        hero = plan["sections"][0]
        bg = hero.get("decoration", {}).get("background", {})
        bg_str = json.dumps(bg)
        assert "overlay" not in bg_str or "gradient" in bg_str, "compose_background overwrote hero radial gradient with overlay"

    def test_stats_bg_is_dark(self):
        plan = _generate_plan("warm_minimal")
        stats = plan["sections"][2]
        bg_color = stats.get("decoration", {}).get("background", {}).get("desktop", {}).get("value", {}).get("color", "")
        assert bg_color != "#FFFFFF" and bg_color != "#FCF5F1", f"Stats has light bg: {bg_color}"

    def test_all_sections_responsive_spacing(self):
        plan = _generate_plan()
        for i, section in enumerate(plan["sections"]):
            spacing = section.get("decoration", {}).get("spacing", {})
            assert "tablet" in spacing, f"Section {i} lacks responsive tablet spacing"