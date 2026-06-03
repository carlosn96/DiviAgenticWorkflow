"""SectionBuilder — assembles complete sections from blocks + rules.

Phase 3: Añade soporte para design_direction. Si el brief contiene
`design_direction`, el builder genera secciones con decisiones de diseño
explícitas (color, tipo, spacing, layout) en vez de usar presets genéricos.
"""
from typing import Dict, List, Optional

from vie.building import DecorationBuilder, RowBuilder
from vie.director import ImpactDirector
from vie.module import ModuleBuilder


class SectionBuilder:
    """Builds complete sections using the dataset blocks and catalog props."""

    def __init__(self, director: ImpactDirector, module_builder: ModuleBuilder,
                 decorator: DecorationBuilder,
                 design_direction: Optional[Dict] = None,
                 all_sections: Optional[List[Dict]] = None):
        self.director = director
        self.mb = module_builder
        self.decorator = decorator
        self.resolver = director.resolver
        self.design_direction = design_direction
        self.all_sections = all_sections or []
        self._profile = None

    def _get_profile(self):
        if self._profile is None and self.design_direction:
            from vie.design_director import get_profile, apply_effects_tags
            resolver = getattr(self, 'resolver', None)
            self._profile = get_profile(self.design_direction, resolver=resolver)
            effects_tags = self.design_direction.get("effects_tags", [])
            if effects_tags:
                self._profile = apply_effects_tags(self._profile, effects_tags)
        return self._profile

    def build(self, sec_def: Dict, index: int) -> Dict:
        """Build a rich section from brief definition."""
        st = sec_def.get("section_type", "generic")
        self._current_index = index

        # PATH A: design_direction presente → diseño calculado
        profile = self._get_profile()
        if profile:
            return self._build_designer_section(sec_def, st, index, profile)

        # PATH B: sin design_direction → comportamiento original (blocks + presets)
        block = self.director.select_block(st, index)
        if not block:
            return self._build_fallback_section(sec_def)
        block_id = block.get("id", "unknown")

        props = self.director.adapt_block_props(block)
        props = self.director.apply_combination_rules(props)

        section_presets = self._resolve_section_presets(st, block)
        section_deco = self._build_section_decoration(props.get("section", {}), st)
        rows = self._build_rows(sec_def, st, block, props)

        return {
            "type": "regular",
            "module": "divi/section",
            "module_class": f"{st}-section",
            "presets": section_presets,
            "decoration": section_deco,
            "rows": rows,
            "_block_id": block_id,
        }

    # ── PATH A: Diseño calculado (design_direction) ───────────────────────

    def _build_designer_section(self, sec_def: Dict, section_type: str, index: int,
                                 profile) -> Dict:
        """Build section using SemanticModuleMapper + LayoutComposer + PremiumEffects.

        Reemplaza el enfoque monolitico (13 metodos _build_designer_*) por composicion
        generica: mapear semantica -> seleccionar layout -> aplicar efectos premium.
        """
        from vie.design_director import (
            get_hero_decoration, get_features_decoration, get_cta_decoration,
            get_content_decoration, get_stats_decoration,
            get_gallery_decoration, get_process_decoration,
            get_eyebrow_font, get_heading_font, get_body_font,
        )
        from vie.patterns import (
            get_zone, compose_background, card_system, eyebrow_pill,
            heading_decoration, body_decoration,
            get_zone_divider, is_dark_zone,
        )
        from vie.semantic_module_mapper import SemanticModuleMapper
        from vie.layout_composer import LayoutComposer

        zone_info = get_zone(profile, section_type, index)
        zone = zone_info["zone"]
        is_dark = is_dark_zone(zone)

        # 1. Mapear campos semanticos del brief a modulos Divi nativos
        modules = SemanticModuleMapper.map_section(sec_def)

        # 2. Detectar page_type del brief (si no esta, usar "home" por defecto)
        page_type = getattr(self, '_page_type', 'home')

        # 3. Seleccionar layout asimetrico por page_type + section_type
        layout_composer = LayoutComposer()
        variant_hint = getattr(profile, '_variant_hint', '')
        rows = layout_composer.compose_rows(section_type, page_type, modules, variant_hint, profile)

        # 4. Seleccionar decoration de seccion segun tipo
        if section_type in ("hero", "hero-centered", "hero-split"):
            decoration = get_hero_decoration(profile)
        elif section_type == "features":
            decoration = get_features_decoration(profile)
        elif section_type == "cta":
            decoration = get_cta_decoration(profile)
        elif section_type == "content":
            decoration = get_content_decoration(profile, is_light=not is_dark)
        elif section_type == "stats":
            decoration = get_stats_decoration(profile)
        elif section_type in ("gallery", "slider"):
            decoration = get_gallery_decoration(profile)
        elif section_type == "process":
            decoration = get_process_decoration(profile)
        else:
            decoration = get_content_decoration(profile, is_light=not is_dark)

        # 5. Aplicar zone background (si no hay gradiente custom ya)
        zone_deco = compose_background(profile, zone)
        if zone_deco:
            existing_bg = decoration.get("background", {})
            existing_has_custom_bg = False
            if existing_bg:
                ev = existing_bg.get("desktop", {}).get("value", {})
                if "gradient" in ev:
                    existing_has_custom_bg = True
                if "color" in ev and zone_deco.get("background", {}).get("desktop", {}).get("value", {}).get("color") != ev.get("color"):
                    existing_has_custom_bg = True
            if not existing_has_custom_bg:
                decoration["background"] = zone_deco.get("background", existing_bg)
            for key in ("spacing", "animation", "scroll"):
                if key in zone_deco and key not in decoration:
                    decoration[key] = zone_deco[key]

        # 6. Construir resultado
        result = {
            "type": "regular",
            "module": "divi/section",
            "presets": [],
            "decoration": decoration,
            "rows": rows,
        }

        # 7. Aplicar efectos premium (stagger + CSS)
        self._apply_stagger(result, profile, section_type)
        self._apply_premium_css(result, profile, section_type)

        # 8. Zone divider entre secciones
        prev_zone_name = None
        if index > 0 and self.all_sections:
            prev_sec_type = self.all_sections[index - 1].get("section_type", "hero")
            prev_zone_info = get_zone(profile, prev_sec_type, index - 1)
            if prev_zone_info:
                prev_zone_name = prev_zone_info.get("zone")
        divider = get_zone_divider(zone, prev_zone_name, profile)
        if divider:
            result["decoration"]["shapeDivider"] = divider

        # 9. Module class para CSS targeting
        result["module_class"] = f"{section_type}-section"

        return result

    def _apply_zone_aware_eyebrows(self, result: Dict, profile, is_dark: bool):
        """Replace eyebrow decoration with eyebrow_pill for zone-aware styling."""
        from vie.patterns import eyebrow_pill
        pill = eyebrow_pill(profile, is_dark)
        if not result.get("rows"):
            return
        for row in result["rows"]:
            for col in row.get("columns", []):
                for mod in col.get("modules", []):
                    if mod.get("type") == "divi/text" and mod.get("content", "").strip().isupper() and len(mod.get("content", "").strip()) < 40:
                        current = mod.get("decoration", {})
                        if current and "font" in current:
                            mod["decoration"] = pill

    def _apply_zone_aware_headings(self, result: Dict, profile, zone: str):
        """Replace heading colors with zone-aware text colors."""
        from vie.patterns import heading_decoration, body_decoration
        if not result.get("rows"):
            return
        for row in result["rows"]:
            for col in row.get("columns", []):
                for mod in col.get("modules", []):
                    if mod.get("type") == "divi/heading":
                        level = mod.get("level", "h2")
                        mod["decoration"] = heading_decoration(profile, level, zone)

    def _apply_stagger(self, result: Dict, profile, section_type: str):
        """Add progressive reveal animation delays to modules in hero/CTA/stats sections."""
        from vie.patterns import stagger_delay
        stagger_sections = {"hero", "hero-centered", "hero-split", "cta", "stats"}
        if section_type not in stagger_sections:
            return
        stagger_key = f"stagger_{section_type.replace('-', '_').replace('hero_centered', 'hero').replace('hero_split', 'hero')}"
        if not getattr(profile, stagger_key, False):
            if not getattr(profile, 'stagger_hero', False) and section_type in ("hero", "hero-centered", "hero-split"):
                return
            if section_type not in ("hero", "hero-centered", "hero-split"):
                return
        style = "dramatic" if profile.motion_intensity == "dramatic" else "subtle"
        if not result.get("rows"):
            return
        mod_idx = 0
        for row in result["rows"]:
            for col in row.get("columns", []):
                for mod in col.get("modules", []):
                    delay = stagger_delay(mod_idx, style=style)
                    deco = mod.get("decoration", {})
                    if not deco:
                        mod["decoration"] = deco
                    deco["animation"] = {
                        "desktop": {
                            "value": {
                                "style": "fade",
                                "duration": "800ms",
                                "delay": delay,
                                "speedCurve": "cubic-bezier(0.22, 1, 0.36, 1)",
                            }
                        }
                    }
                    mod_idx += 1

    def _apply_premium_css(self, result: Dict, profile, section_type: str):
        """Add premium CSS (grain, orb, fade, column-dividers, blur-reveal) to section and modules."""
        from vie.building import PremiumCSSBuilder
        css_builder = PremiumCSSBuilder(
            accent=profile.accent,
            accent_light=getattr(profile, 'accent_light', ''),
            accent_muted=getattr(profile, 'accent_muted', ''),
            bg_dark=profile.bg_dark,
            bg_light=profile.bg_light,
        )

        section_features = []
        module_features = []

        if section_type in ("hero", "hero-centered", "hero-split"):
            section_features.append("orb")
            section_features.append("blur_reveal")
            module_features.append("blur_reveal")
        elif section_type == "cta":
            section_features.append("orb")
            section_features.append("fade_bottom")
            section_features.append("blur_reveal")
            module_features.append("blur_reveal")
        elif section_type == "stats":
            section_features.append("column_dividers")
            section_features.append("blur_reveal")
            module_features.append("blur_reveal")
        elif section_type in ("features", "testimonials"):
            pass

        if getattr(profile, 'grain_texture', False):
            section_features.append("grain")

        if section_features:
            section_css = css_builder.compose_section_css(section_features)
            if section_css:
                if "css" not in result:
                    result["css"] = {}
                for bp, css_str in section_css.items():
                    if bp not in result["css"]:
                        result["css"][bp] = {"value": {"freeForm": css_str}}
                    else:
                        existing = result["css"][bp].get("value", {}).get("freeForm", "")
                        if existing:
                            result["css"][bp]["value"]["freeForm"] = existing + "\n" + css_str
                        else:
                            result["css"][bp]["value"]["freeForm"] = css_str

        if module_features and result.get("rows"):
            mod_idx = 0
            style = "dramatic" if profile.motion_intensity == "dramatic" else "subtle"
            stagger_on = getattr(profile, f"stagger_{section_type.replace('-', '_').replace('hero_centered', 'hero').replace('hero_split', 'hero')}", False)
            if not stagger_on and section_type in ("hero", "hero-centered", "hero-split"):
                stagger_on = getattr(profile, 'stagger_hero', False)
            for row in result["rows"]:
                for col in row.get("columns", []):
                    for mod in col.get("modules", []):
                        from vie.patterns import stagger_delay
                        delay = stagger_delay(mod_idx, style=style) if stagger_on else "0ms"
                        mod_css = css_builder.compose_module_css(module_features, delay=delay)
                        if mod_css:
                            if "css" not in mod:
                                mod["css"] = {}
                            for bp, css_str in mod_css.items():
                                if bp not in mod["css"]:
                                    mod["css"][bp] = {"value": {"freeForm": css_str}}
                                else:
                                    existing = mod["css"][bp].get("value", {}).get("freeForm", "")
                                    if existing:
                                        mod["css"][bp]["value"]["freeForm"] = existing + "\n" + css_str
                                    else:
                                        mod["css"][bp]["value"]["freeForm"] = css_str
                        mod_idx += 1

    def _build_designer_hero(self, sec_def, profile, get_hero_decoration,
                                get_eyebrow_font, get_heading_font, get_body_font,
                                get_button_decoration, get_title_divider):
        layout = profile.hero_layout

        if layout == "asymmetric":
            return self._build_hero_asymmetric(
                sec_def, profile, get_hero_decoration,
                get_eyebrow_font, get_heading_font, get_body_font,
                get_button_decoration, get_title_divider,
            )

        # Centered (default)
        rows = []
        content_col = {"type": "4_4", "modules": []}

        eyebrow = sec_def.get("eyebrow")
        if eyebrow:
            content_col["modules"].append({
                "type": "divi/text", "module": "divi/text",
                "content": eyebrow,
                "decoration": get_eyebrow_font(profile),
            })

        title = sec_def.get("title", "")
        if title:
            content_col["modules"].append({
                "type": "divi/heading", "module": "divi/heading",
                "content": title, "level": "h1",
                "decoration": get_heading_font(profile, "h1"),
            })

        divider = get_title_divider(profile)
        if divider:
            content_col["modules"].append({
                "type": "divi/divider", "module": "divi/divider",
                "decoration": divider,
            })

        text = sec_def.get("text", "")
        if text:
            content_col["modules"].append({
                "type": "divi/text", "module": "divi/text",
                "content": f"<p>{text}</p>",
                "decoration": get_body_font(profile, "muted_dark"),
            })

        btn_text = sec_def.get("btn_primary_text")
        btn_url = sec_def.get("btn_primary_url")
        if btn_text and btn_url:
            content_col["modules"].append({
                "type": "divi/button", "module": "divi/button",
                "button_text": btn_text, "button_url": btn_url,
                "decoration": get_button_decoration(profile),
            })

        rows.append({
            "type": "divi/row", "module": "divi/row",
            "column_structure": "4_4",
            "columns": [content_col],
        })

        return {
            "type": "regular", "module": "divi/section",
            "presets": [],
            "decoration": get_hero_decoration(profile),
            "rows": rows,
        }

    def _build_hero_asymmetric(self, sec_def, profile, get_hero_decoration,
                                 get_eyebrow_font, get_heading_font, get_body_font,
                                 get_button_decoration, get_title_divider):
        rows = []
        left_col = {"type": "2_5", "modules": []}
        right_col = {"type": "3_5", "modules": []}

        eyebrow = sec_def.get("eyebrow")
        if eyebrow:
            left_col["modules"].append({
                "type": "divi/text", "module": "divi/text",
                "content": eyebrow,
                "decoration": get_eyebrow_font(profile),
            })

        title = sec_def.get("title", "")
        if title:
            left_col["modules"].append({
                "type": "divi/heading", "module": "divi/heading",
                "content": title, "level": "h1",
                "decoration": get_heading_font(profile, "h1"),
            })

        divider = get_title_divider(profile)
        if divider:
            left_col["modules"].append({
                "type": "divi/divider", "module": "divi/divider",
                "decoration": divider,
            })

        text = sec_def.get("text", "")
        if text:
            left_col["modules"].append({
                "type": "divi/text", "module": "divi/text",
                "content": f"<p>{text}</p>",
                "decoration": get_body_font(profile, "muted_dark"),
            })

        btn_text = sec_def.get("btn_primary_text")
        btn_url = sec_def.get("btn_primary_url")
        if btn_text and btn_url:
            left_col["modules"].append({
                "type": "divi/button", "module": "divi/button",
                "button_text": btn_text, "button_url": btn_url,
                "decoration": get_button_decoration(profile),
            })

        right_col["modules"].append({
            "type": "divi/text", "module": "divi/text",
            "content": "<p style='height:400px; display:flex; align-items:center; justify-content:center;"
                       f" background:{profile.bg_mid}; border-radius:4px;"
                       f" color:{profile.text_muted}; font-size:14px;'>\u0026nbsp;</p>",
            "decoration": {},
        })

        rows.append({
            "type": "divi/row", "module": "divi/row",
            "column_structure": "2_5,3_5",
            "columns": [left_col, right_col],
        })

        return {
            "type": "regular", "module": "divi/section",
            "presets": [],
            "decoration": get_hero_decoration(profile),
            "rows": rows,
        }

    def _build_designer_features(self, sec_def, profile, get_features_decoration,
                                    get_card_decoration, get_eyebrow_font,
                                    get_heading_font, get_body_font):
        from vie.patterns import card_system, eyebrow_pill, heading_decoration, body_decoration, stagger_delay, is_dark_zone

        rows = []
        header_col = {"type": "4_4", "modules": []}

        eyebrow = sec_def.get("eyebrow")
        if eyebrow:
            header_col["modules"].append({
                "type": "divi/text", "module": "divi/text",
                "content": eyebrow,
                "decoration": eyebrow_pill(profile, is_dark_zone=False),
            })

        title = sec_def.get("title", "")
        if title:
            header_col["modules"].append({
                "type": "divi/heading", "module": "divi/heading",
                "content": title, "level": "h2",
                "decoration": heading_decoration(profile, "h2", "light"),
            })

        rows.append({
            "type": "divi/row", "module": "divi/row",
            "column_structure": "4_4",
            "columns": [header_col],
        })

        items = sec_def.get("items", [])
        if items:
            col_type = "1_2" if profile.features_layout == "grid_2" else "1_3"
            columns = []
            card_style = profile.card_style if hasattr(profile, 'card_style') else "glass"
            card = card_system(profile, card_style, is_dark_zone=False)
            card_base = card["base"]
            card_hover = card["hover"]

            for i, item in enumerate(items[:6]):
                icon = item.get("icon", "")
                item_title = item.get("title", "")
                item_text = item.get("text", "")
                card_css = card.get("css", {})
                blurb = {
                    "type": "divi/blurb", "module": "divi/blurb",
                    "icon": icon or "&#xe03a;",
                    "title": item_title,
                    "content": item_text,
                    "decoration": dict(card_base),
                }
                if card_css:
                    blurb["css"] = dict(card_css)
                if icon:
                    blurb["icon"] = icon

                if card_hover:
                    blurb["decoration"]["transform"] = card_hover.get("transform", card_hover)

                delay = stagger_delay(i, total=len(items), style="subtle" if profile.motion_intensity in ("subtle", "none") else "dramatic")
                blurb["animation"] = {
                    "desktop": {
                        "value": {
                            "style": "fade",
                            "duration": "700ms",
                            "delay": delay,
                            "speedCurve": "cubic-bezier(0.22, 1, 0.36, 1)",
                        }
                    }
                }

                col = {
                    "type": col_type,
                    "modules": [blurb],
                }
                columns.append(col)

            if columns:
                rows.append({
                    "type": "divi/row", "module": "divi/row",
                    "column_structure": ",".join([col_type] * len(columns)),
                    "columns": columns,
                })

        return {
            "type": "regular", "module": "divi/section",
            "presets": [],
            "decoration": get_features_decoration(profile),
            "rows": rows,
        }

    def _build_designer_cta(self, sec_def, profile, get_cta_decoration,
                             get_eyebrow_font, get_heading_font, get_body_font,
                             get_button_decoration):
        rows = []

        if profile.cta_layout == "1_3_2_3":
            left_col = {"type": "1_3", "modules": []}
            right_col = {"type": "2_3", "modules": []}

            eyebrow = sec_def.get("eyebrow")
            if eyebrow:
                left_col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": eyebrow,
                    "decoration": get_eyebrow_font(profile),
                })

            title = sec_def.get("title", "")
            if title:
                left_col["modules"].append({
                    "type": "divi/heading", "module": "divi/heading",
                    "content": title, "level": "h2",
                    "decoration": get_heading_font(profile, "h2"),
                })

            text = sec_def.get("text", "")
            if text:
                right_col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": f"<p>{text}</p>",
                    "decoration": get_body_font(profile, "muted_dark"),
                })

            btn_text = sec_def.get("btn_primary_text")
            btn_url = sec_def.get("btn_primary_url")
            if btn_text and btn_url:
                right_col["modules"].append({
                    "type": "divi/button", "module": "divi/button",
                    "button_text": btn_text, "button_url": btn_url,
                    "decoration": get_button_decoration(profile),
                })

            rows.append({
                "type": "divi/row", "module": "divi/row",
                "column_structure": "1_3,2_3",
                "columns": [left_col, right_col],
            })
        else:
            col = {"type": "4_4", "modules": []}

            eyebrow = sec_def.get("eyebrow")
            if eyebrow:
                col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": eyebrow,
                    "decoration": get_eyebrow_font(profile),
                })

            title = sec_def.get("title", "")
            if title:
                col["modules"].append({
                    "type": "divi/heading", "module": "divi/heading",
                    "content": title, "level": "h2",
                    "decoration": get_heading_font(profile, "h2"),
                })

            text = sec_def.get("text", "")
            if text:
                col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": f"<p>{text}</p>",
                    "decoration": get_body_font(profile, "muted_dark"),
                })

            btn_text = sec_def.get("btn_primary_text")
            btn_url = sec_def.get("btn_primary_url")
            if btn_text and btn_url:
                col["modules"].append({
                    "type": "divi/button", "module": "divi/button",
                    "button_text": btn_text, "button_url": btn_url,
                    "decoration": get_button_decoration(profile),
                })

            rows.append({
                "type": "divi/row", "module": "divi/row",
                "column_structure": "4_4",
                "columns": [col],
            })

        return {
            "type": "regular", "module": "divi/section",
            "presets": [],
            "decoration": get_cta_decoration(profile),
            "rows": rows,
        }

    def _build_designer_content(self, sec_def, profile, get_content_decoration,
                                 get_eyebrow_font, get_heading_font, get_body_font,
                                 get_title_divider):
        rows = []

        layout = profile.about_layout

        if layout == "image_left":
            left = {"type": "1_2", "modules": []}
            right = {"type": "1_2", "modules": []}
            left["modules"].append({
                "type": "divi/text", "module": "divi/text",
                "content": "<p style='height:300px; display:flex; align-items:center; justify-content:center;"
                           f" background:{profile.bg_mid}; border-radius:4px;"
                           f" color:{profile.text_muted}; font-size:14px;'>\u0026nbsp;</p>",
                "decoration": {},
            })
            eyebrow = sec_def.get("eyebrow")
            if eyebrow:
                right["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": eyebrow,
                    "decoration": get_eyebrow_font(profile),
                })
            title = sec_def.get("title", "")
            if title:
                right["modules"].append({
                    "type": "divi/heading", "module": "divi/heading",
                    "content": title, "level": "h2",
                    "decoration": get_heading_font(profile, "h2"),
                })
            text = sec_def.get("text", "")
            if text:
                right["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": f"<p>{text}</p>",
                    "decoration": get_body_font(profile, "muted_dark"),
                })
            rows.append({
                "type": "divi/row", "module": "divi/row",
                "column_structure": "1_2,1_2",
                "columns": [left, right],
            })
            return {
                "type": "regular", "module": "divi/section",
                "presets": [],
                "decoration": get_content_decoration(profile, is_light=True),
                "rows": rows,
            }

        if profile.about_layout == "2_5_3_5":
            left_col = {"type": "2_5", "modules": []}
            right_col = {"type": "3_5", "modules": []}

            eyebrow = sec_def.get("eyebrow")
            if eyebrow:
                left_col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": eyebrow,
                    "decoration": get_eyebrow_font(profile),
                })

            title = sec_def.get("title", "")
            if title:
                left_col["modules"].append({
                    "type": "divi/heading", "module": "divi/heading",
                    "content": title, "level": "h2",
                    "decoration": {
                        "font": {
                            "desktop": {
                                "value": {
                                    "color": profile.text_on_light,
                                    "size": "clamp(2rem, 4vw, 3rem)",
                                    "lineHeight": "1.15",
                                    "font": profile.font_display,
                                }
                            }
                        }
                    },
                })

            divider = get_title_divider(profile)
            if divider:
                left_col["modules"].append({
                    "type": "divi/divider", "module": "divi/divider",
                    "decoration": divider,
                })

            text = sec_def.get("text", "")
            if text:
                left_col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": f"<p>{text}</p>",
                    "decoration": {
                        "font": {
                            "desktop": {
                                "value": {
                                    "color": profile.text_secondary,
                                    "size": "16px",
                                    "lineHeight": "1.75",
                                    "font": profile.font_body,
                                }
                            }
                        }
                    },
                })

            image = sec_def.get("image", "")
            right_col["modules"].append({
                "type": "divi/text", "module": "divi/text",
                "content": f"<p style='font-size:14px; color:{profile.text_muted};'>[imagen]{image}</p>" if image else "[imagen]",
                "decoration": {
                    "background": {
                        "desktop": {
                            "value": {"color": profile.bg_mid}
                        }
                    },
                    "spacing": {
                        "desktop": {
                            "value": {
                                "padding": {"top": "40px", "bottom": "40px", "left": "40px", "right": "40px"}
                            }
                        }
                    },
                },
            })

            rows.append({
                "type": "divi/row", "module": "divi/row",
                "column_structure": "2_5,3_5",
                "columns": [left_col, right_col],
            })
        else:
            col = {"type": "4_4", "modules": []}

            eyebrow = sec_def.get("eyebrow")
            if eyebrow:
                col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": eyebrow,
                    "decoration": get_eyebrow_font(profile),
                })

            title = sec_def.get("title", "")
            if title:
                col["modules"].append({
                    "type": "divi/heading", "module": "divi/heading",
                    "content": title, "level": "h2",
                    "decoration": {
                        "font": {
                            "desktop": {
                                "value": {
                                    "color": profile.text_on_light,
                                    "size": "clamp(2rem, 4vw, 3rem)",
                                    "font": profile.font_display,
                                }
                            }
                        }
                    },
                })

            text = sec_def.get("text", "")
            if text:
                col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": f"<p>{text}</p>",
                    "decoration": {
                        "font": {
                            "desktop": {
                                "value": {
                                    "color": profile.text_secondary,
                                    "size": "17px",
                                    "lineHeight": "1.6",
                                    "textAlign": "center",
                                }
                            }
                        }
                    },
                })

            rows.append({
                "type": "divi/row", "module": "divi/row",
                "column_structure": "4_4",
                "columns": [col],
            })

        return {
            "type": "regular", "module": "divi/section",
            "presets": [],
            "decoration": get_content_decoration(profile, is_light=True),
            "rows": rows,
        }

    def _build_designer_stats(self, sec_def, profile, get_stats_decoration,
                                get_eyebrow_font, get_heading_font):
        rows = []

        eyebrow = sec_def.get("eyebrow")
        title = sec_def.get("title")
        if eyebrow or title:
            header_col = {"type": "4_4", "modules": []}
            if eyebrow:
                header_col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": eyebrow,
                    "decoration": get_eyebrow_font(profile),
                })
            if title:
                header_col["modules"].append({
                    "type": "divi/heading", "module": "divi/heading",
                    "content": title, "level": "h2",
                    "decoration": get_heading_font(profile, "h2") if hasattr(profile, 'text_on_light') else get_heading_font(profile, "h2"),
                })
            rows.append({
                "type": "divi/row", "module": "divi/row",
                "column_structure": "4_4",
                "columns": [header_col],
            })

        stats = sec_def.get("stats", [])
        if stats:
            stat_cols = []
            for s in stats[:4]:
                num_val = s.get("number", "0")
                label = s.get("label", "")
                stat_cols.append({
                    "type": "divi/number-counter", "module": "divi/number-counter",
                    "number": num_val.replace("+", "").replace("%", "").strip(),
                    "title": label,
                    "decoration": {
                        "font": {
                            "desktop": {
                                "value": {
                                    "size": "clamp(2.5rem, 5vw, 4rem)",
                                    "color": profile.accent,
                                    "font": profile.font_display,
                                    "textAlign": "center",
                                    "lineHeight": "1.1",
                                }
                            }
                        },
                        "spacing": {
                            "desktop": {
                                "value": {
                                    "padding": {"top": "32px", "bottom": "32px"},
                                }
                            }
                        },
                    },
                })

            if stat_cols:
                rows.append({
                    "type": "divi/row", "module": "divi/row",
                    "column_structure": ",".join(["1_4"] * len(stat_cols)),
                    "columns": [{"type": "1_4", "modules": [m]} for m in stat_cols],
                })

        return {
            "type": "regular", "module": "divi/section",
            "presets": [],
            "decoration": get_stats_decoration(profile),
            "rows": rows,
        }

    def _build_designer_team(self, sec_def, profile, get_content_decoration,
                              get_team_card_decoration, get_eyebrow_font,
                              get_heading_font):
        rows = []

        eyebrow = sec_def.get("eyebrow")
        title = sec_def.get("title")
        if eyebrow or title:
            header_col = {"type": "4_4", "modules": []}
            if eyebrow:
                header_col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": eyebrow,
                    "decoration": get_eyebrow_font(profile),
                })
            if title:
                header_col["modules"].append({
                    "type": "divi/heading", "module": "divi/heading",
                    "content": title, "level": "h2",
                    "decoration": get_heading_font(profile, "h2"),
                })
            rows.append({
                "type": "divi/row", "module": "divi/row",
                "column_structure": "4_4",
                "columns": [header_col],
            })

        members = sec_def.get("members", [])
        if members:
            member_cols = []
            for m in members[:4]:
                img = m.get("image", "")
                name = m.get("name", "")
                role = m.get("role", "")
                bio = m.get("text", m.get("bio", ""))
                mods = []
                if img:
                    mods.append({
                        "type": "divi/image", "module": "divi/image",
                        "src": img,
                        "alt": name,
                        "decoration": {
                            "sizing": {
                                "desktop": {
                                    "value": {
                                        "width": "100%",
                                        "height": "280px",
                                        "objectFit": "cover",
                                    }
                                }
                            },
                            "spacing": {
                                "desktop": {
                                    "value": {
                                        "margin": {"bottom": "16px"},
                                    }
                                }
                            },
                        },
                    })
                if name:
                    mods.append({
                        "type": "divi/heading", "module": "divi/heading",
                        "content": name, "level": "h3",
                        "decoration": {
                            "font": {
                                "desktop": {
                                    "value": {
                                        "color": profile.text_on_dark,
                                        "size": "20px",
                                        "font": profile.font_display,
                                        "textAlign": "center",
                                        "lineHeight": "1.3",
                                    }
                                }
                            },
                        },
                    })
                if role:
                    mods.append({
                        "type": "divi/text", "module": "divi/text",
                        "content": role,
                        "decoration": {
                            "font": {
                                "desktop": {
                                    "value": {
                                        "color": profile.accent,
                                        "size": "13px",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "1px",
                                        "textAlign": "center",
                                        "font": profile.font_ui,
                                    }
                                }
                            },
                        },
                    })
                if bio:
                    mods.append({
                        "type": "divi/text", "module": "divi/text",
                        "content": f"<p>{bio}</p>",
                        "decoration": {
                            "font": {
                                "desktop": {
                                    "value": {
                                        "color": f"{profile.text_on_dark}b3",
                                        "size": "14px",
                                        "lineHeight": "1.6",
                                        "textAlign": "center",
                                    }
                                }
                            },
                        },
                    })
                member_cols.append({
                    "type": "1_4",
                    "decoration": get_team_card_decoration(profile),
                    "modules": mods,
                })

            rows.append({
                "type": "divi/row", "module": "divi/row",
                "column_structure": ",".join(["1_4"] * len(member_cols)),
                "columns": member_cols,
            })

        return {
            "type": "regular", "module": "divi/section",
            "presets": [],
            "decoration": get_content_decoration(profile),
            "rows": rows,
        }

    def _build_designer_process(self, sec_def, profile, get_process_decoration,
                                 get_eyebrow_font, get_heading_font, get_body_font):
        rows = []

        eyebrow = sec_def.get("eyebrow")
        title = sec_def.get("title")
        if eyebrow or title:
            header_col = {"type": "4_4", "modules": []}
            if eyebrow:
                header_col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": eyebrow,
                    "decoration": get_eyebrow_font(profile),
                })
            if title:
                header_col["modules"].append({
                    "type": "divi/heading", "module": "divi/heading",
                    "content": title, "level": "h2",
                    "decoration": get_heading_font(profile, "h2"),
                })
            rows.append({
                "type": "divi/row", "module": "divi/row",
                "column_structure": "4_4",
                "columns": [header_col],
            })

        phases = sec_def.get("phases", sec_def.get("items", []))
        if phases:
            phase_cols = []
            for p in phases[:4]:
                mods = []
                icon = p.get("icon", "")
                if icon:
                    mods.append({
                        "type": "divi/blurb", "module": "divi/blurb",
                        "icon": icon,
                        "title": p.get("title", ""),
                        "content": p.get("text", ""),
                        "decoration": {
                            "font": {
                                "desktop": {
                                    "value": {
                                        "textAlign": "center",
                                    }
                                }
                            },
                            "spacing": {
                                "desktop": {
                                    "value": {
                                        "padding": {"top": "32px", "bottom": "32px", "left": "24px", "right": "24px"},
                                    }
                                }
                            },
                        },
                    })
                phase_cols.append({
                    "type": "1_4",
                    "modules": mods,
                })

            if phase_cols:
                rows.append({
                    "type": "divi/row", "module": "divi/row",
                    "column_structure": ",".join(["1_4"] * len(phase_cols)),
                    "columns": phase_cols,
                })

        return {
            "type": "regular", "module": "divi/section",
            "presets": [],
            "decoration": get_process_decoration(profile),
            "rows": rows,
        }

    def _build_designer_gallery(self, sec_def, profile, get_gallery_decoration,
                                 get_eyebrow_font, get_heading_font):
        rows = []

        eyebrow = sec_def.get("eyebrow")
        title = sec_def.get("title")
        if eyebrow or title:
            header_col = {"type": "4_4", "modules": []}
            if eyebrow:
                header_col["modules"].append({
                    "type": "divi/text", "module": "divi/text",
                    "content": eyebrow,
                    "decoration": get_eyebrow_font(profile),
                })
            if title:
                header_col["modules"].append({
                    "type": "divi/heading", "module": "divi/heading",
                    "content": title, "level": "h2",
                    "decoration": get_heading_font(profile, "h2"),
                })
            rows.append({
                "type": "divi/row", "module": "divi/row",
                "column_structure": "4_4",
                "columns": [header_col],
            })

        items = sec_def.get("items", [])
        if items:
            img_cols = []
            for item in items[:6]:
                src = item.get("image", "")
                alt = item.get("alt", item.get("title", ""))
                img_cols.append({
                    "type": "1_3",
                    "modules": [{
                        "type": "divi/image", "module": "divi/image",
                        "src": src,
                        "alt": alt,
                        "decoration": {
                            "sizing": {
                                "desktop": {
                                    "value": {
                                        "width": "100%",
                                        "height": "280px",
                                        "objectFit": "cover",
                                    }
                                }
                            },
                            "spacing": {
                                "desktop": {
                                    "value": {
                                        "margin": {"bottom": "0px"},
                                    }
                                }
                            },
                            "transform": {
                                "hover": {
                                    "value": {
                                        "scale": {"x": "1.05", "y": "1.05"},
                                    }
                                }
                            },
                        },
                    }],
                })

            if img_cols:
                rows.append({
                    "type": "divi/row", "module": "divi/row",
                    "column_structure": ",".join(["1_3"] * len(img_cols)),
                    "columns": img_cols,
                })

        return {
            "type": "regular", "module": "divi/section",
            "presets": [],
            "decoration": get_gallery_decoration(profile),
            "rows": rows,
        }

    def _build_designer_pricing(self, sec_def, profile, get_content_decoration,
                                 get_card_decoration, get_eyebrow_font,
                                 get_heading_font, get_body_font):
        from vie.patterns import card_system, eyebrow_pill, heading_decoration, body_decoration, stagger_delay, is_dark_zone

        rows = []
        header_col = {"type": "4_4", "modules": []}

        eyebrow = sec_def.get("eyebrow")
        if eyebrow:
            header_col["modules"].append({
                "type": "divi/text", "module": "divi/text",
                "content": eyebrow,
                "decoration": eyebrow_pill(profile, False),
            })

        title = sec_def.get("title", "Precios")
        if title:
            header_col["modules"].append({
                "type": "divi/heading", "module": "divi/heading",
                "content": title, "level": "h2",
                "decoration": heading_decoration(profile, "h2", "light"),
            })

        rows.append({"type": "divi/row", "module": "divi/row", "column_structure": "4_4", "columns": [header_col]})

        features = sec_def.get("features", [])
        if features:
            tables = []
            for i, feat in enumerate(features[:3]):
                is_featured = i == 1
                table = {
                    "type": "divi/pricing-table",
                    "module": "divi/pricing-table",
                    "title": feat.get("title", ""),
                    "subtitle": feat.get("subtitle", ""),
                    "price": feat.get("price", ""),
                    "currencyFrequency": {
                        "currency": "",
                        "per": feat.get("currency_frequency", "/mes"),
                    },
                    "content": feat.get("text", ""),
                    "featured": "on" if is_featured else "off",
                    "decoration": {
                        "module": {
                            "advanced": {
                                "featured": {
                                    "desktop": {
                                        "value": "on" if is_featured else "off"
                                    }
                                }
                            }
                        }
                    },
                }
                if feat.get("button_text") or is_featured:
                    table["button_text"] = feat.get("button_text", "Elegir Plan" if is_featured else "")
                    table["button_url"] = feat.get("button_url", "/contacto" if is_featured else "")
                tables.append(table)

            rows.append({
                "type": "divi/row", "module": "divi/row",
                "column_structure": "4_4",
                "columns": [{"type": "4_4", "modules": [
                    {
                        "type": "divi/pricing-tables", "module": "divi/pricing-tables",
                        "title": sec_def.get("title", ""),
                        "children": tables,
                    }
                ]}],
            })

        return {"type": "regular", "module": "divi/section", "presets": [],
                "decoration": get_content_decoration(profile, is_light=True), "rows": rows}

    def _build_designer_faq(self, sec_def, profile, get_content_decoration,
                             get_eyebrow_font, get_heading_font):
        rows = []
        header_col = {"type": "4_4", "modules": []}
        eyebrow = sec_def.get("eyebrow")
        if eyebrow:
            header_col["modules"].append({"type": "divi/text", "module": "divi/text",
                                           "content": eyebrow, "decoration": get_eyebrow_font(profile)})
        title = sec_def.get("title", "Preguntas Frecuentes")
        if title:
            header_col["modules"].append({"type": "divi/heading", "module": "divi/heading",
                                           "content": title, "level": "h2",
                                           "decoration": get_heading_font(profile, "h2")})
        rows.append({"type": "divi/row", "module": "divi/row", "column_structure": "4_4", "columns": [header_col]})

        faqs = sec_def.get("faqs", sec_def.get("items", []))
        if faqs:
            left_items = faqs[:(len(faqs)+1)//2]
            right_items = faqs[(len(faqs)+1)//2:]

            def build_accordion_items(items):
                children = []
                for f in items[:8]:
                    children.append({"type": "divi/accordion-item", "module": "divi/accordion-item",
                                     "title": f.get("question", f.get("title", "")),
                                     "content": f.get("answer", f.get("text", ""))})
                return {"type": "divi/accordion", "module": "divi/accordion", "children": children}

            if len(faqs) <= 4:
                rows.append({"type": "divi/row", "module": "divi/row", "column_structure": "4_4",
                              "columns": [{"type": "4_4", "modules": [build_accordion_items(faqs[:8])]}]})
            else:
                rows.append({"type": "divi/row", "module": "divi/row", "column_structure": "1_2,1_2",
                              "columns": [{"type": "1_2", "modules": [build_accordion_items(left_items)]},
                                           {"type": "1_2", "modules": [build_accordion_items(right_items)]}]})

        return {"type": "regular", "module": "divi/section", "presets": [],
                "decoration": get_content_decoration(profile), "rows": rows}

    def _build_designer_trust_bar(self, sec_def, profile, get_content_decoration):
        items = sec_def.get("logos", sec_def.get("items", []))
        if not items:
            return {"type": "regular", "module": "divi/section", "presets": [],
                    "decoration": get_content_decoration(profile), "rows": []}
        logo_cols = []
        for item in items[:5]:
            logo_cols.append({
                "type": "1_5" if len(items) >= 5 else "1_4",
                "modules": [{
                    "type": "divi/image", "module": "divi/image",
                    "src": item.get("image", ""), "alt": item.get("alt", ""),
                    "decoration": {
                        "sizing": {"desktop": {"value": {"width": "120px", "objectFit": "contain"}}},
                        "spacing": {"desktop": {"value": {"padding": {"top": "16px", "bottom": "16px"}}}},
                        "filter": {"desktop": {"value": {"grayscale": "100%"}}},
                        "transform": {"hover": {"value": {"scale": {"x": "1.05", "y": "1.05"},
                                                            "filter": {"grayscale": "0%"}}}},
                    },
                }],
            })
        ncols = min(len(logo_cols), 5)
        col_type = "1_5" if ncols == 5 else "1_4"
        rows = [{"type": "divi/row", "module": "divi/row",
                 "column_structure": ",".join([col_type] * ncols), "columns": logo_cols[:ncols]}]
        return {"type": "regular", "module": "divi/section", "presets": [],
                "decoration": get_content_decoration(profile), "rows": rows}

    def _build_designer_contact(self, sec_def, profile, get_cta_decoration,
                                get_eyebrow_font, get_heading_font, get_body_font, get_button_decoration):
        rows = []
        left_col = {"type": "1_2", "modules": [
            {"type": "divi/contact-form", "module": "divi/contact-form"}
        ]}
        right_col = {"type": "1_2", "modules": []}

        eyebrow = sec_def.get("eyebrow")
        if eyebrow:
            right_col["modules"].append({"type": "divi/text", "module": "divi/text",
                                          "content": eyebrow, "decoration": get_eyebrow_font(profile)})
        title = sec_def.get("title", "Cont\u00e1ctanos")
        if title:
            right_col["modules"].append({"type": "divi/heading", "module": "divi/heading",
                                           "content": title, "level": "h2",
                                           "decoration": get_heading_font(profile, "h2")})
        text = sec_def.get("text", "")
        if text:
            right_col["modules"].append({"type": "divi/text", "module": "divi/text",
                                           "content": f"<p>{text}</p>",
                                           "decoration": get_body_font(profile, "muted_dark")})

        rows.append({"type": "divi/row", "module": "divi/row", "column_structure": "1_2,1_2",
                      "columns": [left_col, right_col]})

        return {"type": "regular", "module": "divi/section", "presets": [],
                "decoration": get_cta_decoration(profile), "rows": rows}

    # ── PATH B: Comportamiento original (sin design_direction) ────────────────

    def _resolve_section_presets(self, section_type: str, block: Dict) -> List[str]:
        """Resolve section-level presets based on type and strategy."""
        strategy = self.resolver.get_strategy()
        has_glass = "glass" in strategy
        has_luxury = "luxury" in strategy
        presets = []

        if section_type in ("hero", "hero-split"):
            if has_glass or section_type == "hero-split":
                presets.append("section:hero-glass")
            else:
                presets.append("section:hero-dark")
        elif section_type == "hero-centered":
            presets.append("section:hero-dark")
        elif section_type == "cta":
            presets.append("section:cta-epic")
        elif section_type in ("features", "stats", "faq"):
            if has_glass or has_luxury:
                presets.append("section:dark")
            else:
                presets.append("section:light")
        elif section_type == "testimonials":
            presets.append("section:white")
        elif section_type == "pricing":
            if has_luxury:
                presets.append("section:dark")
            else:
                presets.append("section:light")
        else:
            presets.append("section:light")

        return [p for p in presets if self.resolver.has_preset(p.split(":")[0], p.split(":")[1]) if ":" in p]

    def _build_section_decoration(self, section_props: Dict, section_type: str) -> Dict:
        """Construct decoration object from block section props."""
        deco = {}

        if "bg_color" in section_props:
            overlay = section_props.get("overlay_gradient")
            deco["background"] = self.decorator.build_background(section_props["bg_color"], overlay)

        if "padding" in section_props:
            pad = section_props["padding"]
            deco["spacing"] = self.decorator.build_spacing(
                pad.get("top", "80px"),
                pad.get("bottom", "80px"),
                pad.get("right", "96px"),
                pad.get("left", "96px")
            )

        if "anim_style" in section_props:
            deco["animation"] = self.decorator.build_animation(
                style=section_props.get("anim_style", "fade"),
                duration=section_props.get("anim_duration", "600ms"),
                delay=section_props.get("anim_delay", "0ms"),
                speed_curve=section_props.get("anim_speed_curve", "ease-out")
            )

        if "scroll_vertical_motion" in section_props:
            sm = section_props["scroll_vertical_motion"]
            if sm.get("enable") == "on":
                deco["scroll"] = self.decorator.build_scroll("verticalMotion", offset=sm.get("offset"))
        elif "scroll_fade" in section_props:
            sf = section_props["scroll_fade"]
            if sf.get("enable") == "on":
                deco["scroll"] = self.decorator.build_scroll("fade", offset=sf.get("offset"))
        elif "scroll_scaling" in section_props:
            sc = section_props["scroll_scaling"]
            if sc.get("enable") == "on":
                deco["scroll"] = self.decorator.build_scroll("scaling", offset=sc.get("offset"))

        if "shape_divider_top" in section_props:
            sd = section_props["shape_divider_top"]
            deco["shapeDivider"] = self.decorator.build_shape_divider(
                "top", sd.get("style", "curve"), sd.get("color", "{{design:color:surface-light}}"),
                sd.get("height", "100px"), sd.get("flip", "off"), sd.get("invert", "off")
            )
        if "shape_divider_bottom" in section_props:
            sd = section_props["shape_divider_bottom"]
            if "shapeDivider" not in deco:
                deco["shapeDivider"] = {}
            deco["shapeDivider"].update(self.decorator.build_shape_divider(
                "bottom", sd.get("style", "curve"), sd.get("color", "{{design:color:surface-light}}"),
                sd.get("height", "100px"), sd.get("flip", "off"), sd.get("invert", "off")
            ))

        return deco

    def _build_rows(self, sec_def: Dict, section_type: str, block: Dict, props: Dict) -> List[Dict]:
        """Delegate to the registered section handler (OCP)."""
        from vie.handlers import get_handler, has_handler
        if has_handler(section_type):
            handler = get_handler(section_type)
            return handler.build(
                sec_def, self._current_index,
                self.director, self.mb, self.decorator,
                block, props,
            )
        return []

    def _build_fallback_section(self, sec_def: Dict) -> Dict:
        """Build a minimal fallback section when no block matches."""
        return {
            "type": "regular",
            "module": "divi/section",
            "presets": ["section:light"],
            "decoration": {},
            "rows": [RowBuilder.full_row([
                self.mb.make_text(sec_def.get("title", "Section"), "body")
            ])]
        }
