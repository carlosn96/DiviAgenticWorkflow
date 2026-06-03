"""DecorationBuilder + RowBuilder — Divi decoration objects and row layouts.

Phase 4: Integrates Pattern Dictionary for zone-aware decoration,
composite backgrounds, card hover system, and eyebrow pills.
Phase 5: Premium CSS generators for effects beyond Divi-native decoration
(grain textures, glow orbs, blur-reveal animations, multi-layer shadows,
column dividers, decorative quote marks, icon containers, gradient buttons).
"""
from typing import Any, Dict, List, Optional

from daw.constants import FRONTEND_PRINCIPLES
from vie.adapters import CatalogLoader
from vie.resolver import BrandResolver


class DecorationBuilder:
    """Builds Divi-native decoration objects from prop definitions."""

    def __init__(self, catalog: CatalogLoader, resolver: BrandResolver):
        self.catalog = catalog
        self.resolver = resolver

    def _resolve_value(self, value: Any) -> Any:
        return self.resolver.resolve_deep(value)

    def build_background(self, color: str, overlay_gradient: Optional[str] = None) -> Dict:
        """Build a background decoration."""
        val = {"color": self._resolve_value(color)}
        if overlay_gradient:
            val["overlay"] = {"gradient": self._resolve_value(overlay_gradient)}
        return {"desktop": {"value": val}}

    def build_spacing(self, top: str, bottom: str, right: str = "96px", left: str = "96px") -> Dict:
        return {"desktop": {"value": {
            "padding": {
                "top": self._resolve_value(top),
                "bottom": self._resolve_value(bottom),
                "right": self._resolve_value(right),
                "left": self._resolve_value(left)
            }
        }}}

    def build_animation(self, style: str = "fade", duration: str = "600ms",
                       delay: str = "0ms", speed_curve: str = "ease-out") -> Dict:
        return {"desktop": {"value": {
            "style": style,
            "duration": self._resolve_value(duration),
            "delay": self._resolve_value(delay),
            "speedCurve": speed_curve
        }}}

    def build_scroll(self, effect_type: str, **kwargs) -> Dict:
        if effect_type == "verticalMotion":
            return {"desktop": {"value": {
                "verticalMotion": {
                    "enable": "on",
                    "offset": kwargs.get("offset", {"start": "6", "mid": "0", "end": "-4"})
                },
                "motionTriggerStart": kwargs.get("trigger", "middle")
            }}}
        if effect_type == "fade":
            return {"desktop": {"value": {
                "fade": {
                    "enable": "on",
                    "offset": kwargs.get("offset", {"start": "0", "mid": "100", "end": "100"})
                },
                "motionTriggerStart": kwargs.get("trigger", "middle")
            }}}
        if effect_type == "scaling":
            return {"desktop": {"value": {
                "scaling": {
                    "enable": "on",
                    "offset": kwargs.get("offset", {"start": "80", "mid": "100", "end": "100"})
                },
                "motionTriggerStart": kwargs.get("trigger", "middle")
            }}}
        return {}

    def build_shape_divider(self, position: str, style: str, color: str,
                           height: str = "100px", flip: str = "off", invert: str = "off") -> Dict:
        return {position: {"desktop": {"value": {
            "style": style,
            "color": self._resolve_value(color),
            "height": height,
            "flip": flip,
            "invert": invert
        }}}}

    def build_box_shadow(self, horizontal: str, vertical: str, blur: str,
                        spread: str, color: str, position: str = "outer") -> Dict:
        return {"desktop": {"value": {
            "horizontal": horizontal,
            "vertical": vertical,
            "blur": blur,
            "spread": spread,
            "color": self._resolve_value(color),
            "position": position
        }}}

    def build_transform_hover(self, scale_x: str = "1.02", scale_y: str = "1.02",
                               translate_y: str = "-2px") -> Dict:
        return {"hover": {"value": {
            "scale": {"x": scale_x, "y": scale_y},
            "translate": {"y": translate_y}
        }}}

    def build_border_radius(self, radius: str) -> Dict:
        return {"desktop": {"value": {
            "radius": {
                "topLeft": self._resolve_value(radius),
                "topRight": self._resolve_value(radius),
                "bottomRight": self._resolve_value(radius),
                "bottomLeft": self._resolve_value(radius)
            }
        }}}

    def glass_card(self, bg_opacity: str = "0.08") -> Dict:
        """Card with semi-transparent background, border-radius, and subtle shadow."""
        return {
            "background": self.build_background("rgba(255,255,255," + bg_opacity + ")"),
            "border": {"desktop": {"value": {
                "width": {"top": "1px", "right": "1px", "bottom": "1px", "left": "1px"},
                "color": "rgba(255,255,255,0.15)",
                "style": "solid"
            }}},
            "borderRadius": self.build_border_radius("16px"),
            "boxShadow": self.build_box_shadow("0", "4px", "24px", "0", "rgba(0,0,0,0.08)"),
            "spacing": self.build_spacing("32px", "32px", "24px", "24px"),
        }

    def solid_card(self, bg_color: str = "rgba(255,255,255,0.06)") -> Dict:
        """Card with solid dark background, border-radius, and hover lift."""
        return {
            "background": self.build_background(bg_color),
            "borderRadius": self.build_border_radius("12px"),
            "boxShadow": self.build_box_shadow("0", "2px", "12px", "0", "rgba(0,0,0,0.12)"),
            "spacing": self.build_spacing("28px", "28px", "20px", "20px"),
            "transform": self.build_transform_hover("1.03", "1.03", "-4px"),
        }

    def outline_card(self, border_color: str = "rgba(255,255,255,0.12)") -> Dict:
        """Card with border-only, no background fill."""
        return {
            "border": {"desktop": {"value": {
                "width": {"top": "1px", "right": "1px", "bottom": "1px", "left": "1px"},
                "color": self._resolve_value(border_color),
                "style": "solid"
            }}},
            "borderRadius": self.build_border_radius("12px"),
            "spacing": self.build_spacing("24px", "24px", "20px", "20px"),
        }

    def elevated_card(self, profile, card_style: str = None, is_dark_zone: bool = False) -> Dict:
        """Card with full hover system: lift + shadow escalation + border transition.

        Uses vie.patterns.card_system() for reference-quality card decoration
        that matches the UX-Pro HTML references (translateY, shadow progression).
        """
        from vie.patterns import card_system, is_dark_zone as _is_dark
        cs = card_system(profile, card_style, is_dark_zone)
        base = cs["base"]
        hover = cs["hover"]

        merged = dict(base)
        for key, val in hover.items():
            if key in merged:
                if isinstance(merged[key], dict) and isinstance(val, dict):
                    merged[key] = {**merged[key], **val}
                else:
                    merged[key] = val
            else:
                merged[key] = val

        return merged

    def compose_zone_background(self, profile, zone: str) -> Dict:
        """Generate composite background decoration using Pattern Dictionary zones.

        Replaces flat color backgrounds with multi-layer compositions
        (gradient overlays, accent tinting) matching reference HTML quality.
        """
        from vie.patterns import compose_background
        return compose_background(profile, zone)

    def zone_eyebrow(self, profile, is_dark_zone: bool = False) -> Dict:
        """Generate eyebrow with pill background (reference-quality).

        Uses accent color at 10-18% opacity for background, with
        border-radius 9999px, accent border, and proper spacing.
        """
        from vie.patterns import eyebrow_pill
        return eyebrow_pill(profile, is_dark_zone)

    def zone_heading(self, profile, level: str = "h2", zone: str = "dark_gradient") -> Dict:
        """Generate heading decoration with zone-aware colors and professional letter-spacing.

        Uses -0.04em letter-spacing for h1/h2 matching reference HTMLs.
        """
        from vie.patterns import heading_decoration
        return heading_decoration(profile, level, zone)

    def zone_body(self, profile, color_type: str = "muted", zone: str = "dark_gradient") -> Dict:
        """Generate body text decoration with zone-aware colors."""
        from vie.patterns import body_decoration
        return body_decoration(profile, color_type, zone)

    def container_width_row(self, width: str = "1100px") -> Dict:
        """Generate row decoration that constrains inner content width."""
        return {
            "sizing": {
                "desktop": {
                    "value": {
                        "maxWidth": width,
                        "margin": {"left": "auto", "right": "auto"},
                    }
                }
            }
        }

    def stagger_animation(self, delay_ms: str = "0ms") -> Dict:
        """Generate fade-up animation with stagger delay for progressive reveal."""
        return {
            "animation": {
                "desktop": {
                    "value": {
                        "style": "fade",
                        "duration": "700ms",
                        "delay": delay_ms,
                        "speedCurve": "cubic-bezier(0.22, 1, 0.36, 1)",
                    }
                }
            }
        }


class PremiumCSSBuilder:
    """Generates premium CSS strings for css.freeForm — effects beyond Divi-native decoration.

    All methods return CSS strings using .selector placeholder (Divi 5 convention).
    These are consumed by section/module builders and output as the `css` field
    in plan.json, which the Layout Engine maps to css.desktop.value.freeForm.
    """

    def __init__(self, accent: str, accent_light: str = "", accent_muted: str = "",
                 bg_dark: str = "#1A110A", bg_light: str = "#F5F0E8"):
        self.accent = accent
        self.accent_light = accent_light or self._lighten(accent)
        self.accent_muted = accent_muted or self._muted(accent)
        self.bg_dark = bg_dark
        self.bg_light = bg_light
        self.P = FRONTEND_PRINCIPLES

    def _lighten(self, hex_color: str) -> str:
        return hex_color

    def _muted(self, hex_color: str) -> str:
        return hex_color

    def _fmt(self, template: str, **kwargs) -> str:
        """Format template replacing {accent} etc with brand colors."""
        return template.format(
            accent=self.accent,
            accent_light=self.accent_light,
            accent_muted=self.accent_muted,
            bg_dark=self.bg_dark,
            bg_light=self.bg_light,
            **kwargs
        )

    def grain_overlay_css(self, target: str = "section", opacity: Optional[float] = None) -> str:
        """SVG noise grain overlay via ::before pseudo-element."""
        P = self.P["aesthetic"]["grain"]
        op = opacity or (P["opacity_section"] if target == "section" else P["opacity_card"])
        bf = P["base_frequency"]
        octv = P["octaves"]
        stitch = P["stitch"]
        return (
            f".selector {{\n  position: relative;\n}}\n"
            f".selector::before {{\n"
            f"  content: '';\n"
            f"  position: absolute;\n"
            f"  top: 0; left: 0; right: 0; bottom: 0;\n"
            f'  background: url("data:image/svg+xml,%3Csvg viewBox=\'0 0 256 256\' xmlns=\'http://www.w3.org/2000/svg\'%3E'
            f'%3Cfilter id=\'noise\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'{bf}\' numOctaves=\'{octv}\' stitchTiles=\'{stitch}\'/%3E%3C/filter%3E'
            f'%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noise)\' opacity=\'{op}\'/%3E%3C/svg%3E");\n'
            f"  opacity: 0.5;\n"
            f"  pointer-events: none;\n}}"
        )

    def orb_glow_css(self, position: str = "top-right", opacity_center: Optional[float] = None) -> str:
        """Radial gradient glow orb via ::before pseudo-element."""
        P = self.P["aesthetic"]["orb_glow"]
        oc = opacity_center or P["opacity_center"]
        oe = P["opacity_edge"]
        ft = P["fade_to_transparent"]
        sz = P["size"]
        pos_map = {
            "top-right": "top: -60%; right: -30%;",
            "top-left": "top: -40%; left: -20%;",
            "bottom-left": "bottom: -40%; left: -20%;",
        }
        pos_css = pos_map.get(position, pos_map["top-right"])
        return (
            f".selector {{ position: relative; overflow: hidden; }}\n"
            f".selector::before {{\n"
            f"  content: '';\n  position: absolute;\n  {pos_css}\n"
            f"  width: {sz}; height: {sz};\n"
            f"  background: radial-gradient(ellipse at center, rgba({self._accent_rgb()},{oc}) 0%, "
            f"rgba({self._accent_rgb()},{oe}) 30%, transparent {ft});\n"
            f"  pointer-events: none;\n}}"
        )

    def _accent_rgb(self) -> str:
        h = self.accent.lstrip("#")
        return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"

    def fade_overlay_css(self, position: str = "bottom") -> str:
        """Gradient fade overlay at section edges via ::after."""
        P = self.P["aesthetic"]["fade_overlay"]
        h = P["height"]
        if position == "bottom":
            return (
                f".selector::after {{\n"
                f"  content: '';\n  position: absolute;\n  bottom: 0; left: 0; right: 0;\n"
                f"  height: {h};\n"
                f"  background: linear-gradient(0deg, {self.bg_dark} 0%, transparent 100%);\n"
                f"  pointer-events: none; z-index: 1;\n}}"
            )
        return (
            f".selector::after {{\n"
            f"  content: '';\n  position: absolute;\n  top: 0; left: 0; right: 0;\n"
            f"  height: {h};\n"
            f"  background: linear-gradient(180deg, {self.bg_light + 'cc'} 0%, transparent 100%);\n"
            f"  pointer-events: none; z-index: 1;\n}}"
        )

    def gradient_line_css(self, target: str = "eyebrow", side: str = "before",
                           width: str = "32px", angle: str = "90deg") -> str:
        """Gradient fade line decoration on eyebrow or heading."""
        accent = self.accent
        pseudo = "::before" if side == "before" else "::after"
        if target == "eyebrow":
            return (
                f".selector p {{{{ display: inline-flex; align-items: center; gap: 12px; }}}}\n"
                f".selector p{pseudo} {{{{ content: ''; width: {width}; height: 1px; "
                f"background: linear-gradient({angle}, {accent}, transparent); }}}}"
            )
        return (
            f".selector .et_pb_module_header{pseudo} {{{{ content: ''; width: {width}; height: 1px; "
            f"background: linear-gradient({angle}, {accent}, transparent); }}}}"
        )

    def column_divider_css(self, selector_target: str = ".et_pb_column") -> str:
        """Gradient vertical lines between columns via ::after."""
        P = self.P["aesthetic"]["column_divider"]
        accent_rgb = self._accent_rgb()
        return (
            f".selector {selector_target} {{ position: relative; }}\n"
            f".selector {selector_target}::after {{\n"
            f"  content: ''; position: absolute;\n"
            f"  top: {P['top_crop']}; bottom: {P['bottom_crop']}; right: 0;\n"
            f"  width: {P['width']};\n"
            f"  background: linear-gradient({P['gradient'].replace('{accent}0.15', f'rgba({accent_rgb},0.15)')});\n"
            f"  pointer-events: none;\n}}\n"
            f".selector {selector_target}:last-child::after {{ display: none; }}"
        )

    def quote_mark_css(self) -> str:
        """Decorative opening quote mark on testimonials."""
        P = self.P["aesthetic"]["quote_mark"]
        ch = P["char"]
        sz = P["size"]
        op = P["opacity"]
        tp = P["position_top"]
        lf = P["position_left"]
        ff = P["font_family"]
        return (
            f".selector {{ position: relative; }}\n"
            f".selector::before {{\n"
            f"  content: '{ch}';\n  position: absolute;\n"
            f"  top: {tp}; left: {lf};\n"
            f"  font-family: '{ff}', serif;\n  font-size: {sz};\n"
            f"  color: rgba({self._accent_rgb()},{op});\n"
            f"  line-height: 1; pointer-events: none;\n}}"
        )

    def icon_container_css(self, size: str = "64px", radius: str = "16px") -> str:
        """Styled icon wrapper with background, hover scale."""
        P = self.P["aesthetic"]["icon_container"]
        sz = size or P["size"]
        rad = radius or P["radius"]
        bg_op = P["bg_opacity"]
        hbg_op = P["hover_bg_opacity"]
        hs = P["hover_scale"]
        ht = P["hover_translateY"]
        accent_rgb = self._accent_rgb()
        return (
            f".selector .et_pb_main_blurb_icon {{\n"
            f"  display: inline-flex; align-items: center; justify-content: center;\n"
            f"  width: {sz}; height: {sz}; border-radius: {rad};\n"
            f"  background: rgba({accent_rgb},{bg_op});\n"
            f"  transition: transform 0.5s cubic-bezier(0.16,1,0.3,1);\n}}\n"
            f".selector:hover .et_pb_main_blurb_icon {{\n"
            f"  transform: scale({hs}) translateY({ht});\n"
            f"  background: rgba({accent_rgb},{hbg_op});\n}}"
        )

    def blur_reveal_keyframes_css(self) -> str:
        """Custom @keyframes for blur-reveal entry animation."""
        P = self.P["motion"]["blur_reveal"]
        name = P["keyframe_name"]
        ib = P["initial_blur"]
        ity = P["initial_translateY"]
        return (
            f"@keyframes {name} {{\n"
            f"  from {{ opacity: 0; transform: translateY({ity}); filter: blur({ib}); }}\n"
            f"  to {{ opacity: 1; transform: translateY(0); filter: blur(0); }}\n}}"
        )

    def blur_reveal_animation_css(self, delay: str = "0ms") -> str:
        """Per-module blur-reveal animation with stagger delay."""
        P = self.P["motion"]["blur_reveal"]
        name = P["keyframe_name"]
        dur = P["duration"]
        easing = P["easing"]
        return (
            f".selector {{\n"
            f"  animation: {name} {dur} {easing} {delay} both;\n}}"
        )

    def multi_shadow_css(self, target: str = "button") -> str:
        """Multi-layer box-shadow for buttons or cards."""
        P = self.P["aesthetic"]["multi_shadow"]
        accent_rgb = self._accent_rgb()
        if target == "button":
            ba = P["button_ambient"]
            bd = P["button_directional"]
            bi = P["button_inset"]
            base = (
                f"box-shadow:\n"
                f"    0 {ba['y']} {ba['blur']} {ba['spread']} rgba({accent_rgb},{ba['color'].split('{accent}')[-1]}),\n"
                f"    0 {bd['y']} {bd['blur']} rgba({accent_rgb},{bd['color'].split('{accent}')[-1]}),\n"
                f"    inset 0 {bi['y']} {bi['color']};"
            )
            return f".selector .et_pb_button {{\n  {base}\n}}"
        return ""

    def button_gradient_css(self) -> str:
        """Multi-stop gradient fill for buttons."""
        P = self.P["aesthetic"]["button_gradient"]
        angle = P["angle"]
        stops = self._fmt(", ".join(P["stops"]))
        return (
            f".selector .et_pb_button {{\n"
            f"  background: linear-gradient({angle}, {stops});\n"
            f"  border: none;\n}}"
        )

    def compose_section_css(self, features: List[str], **kwargs) -> Dict:
        """Compose responsive css object from feature list.

        Returns: {"desktop": "...", "tablet": "...", "phone": "..."}
        where each value is a CSS string for that breakpoint.
        """
        desktop_parts = []
        phone_parts = []
        for feature in features:
            if feature == "grain":
                desktop_parts.append(self.grain_overlay_css("section"))
            elif feature == "orb":
                desktop_parts.append(self.orb_glow_css(kwargs.get("orb_pos", "top-right")))
            elif feature == "fade_bottom":
                desktop_parts.append(self.fade_overlay_css("bottom"))
            elif feature == "fade_top":
                desktop_parts.append(self.fade_overlay_css("top"))
            elif feature == "column_dividers":
                desktop_parts.append(self.column_divider_css())
            elif feature == "blur_reveal":
                desktop_parts.append(self.blur_reveal_keyframes_css())

        desktop = "\n".join(p for p in desktop_parts if p)
        phone_parts.append(".selector::before { display: none; }" if "orb" in features else "")
        phone = "\n".join(p for p in phone_parts if p)

        result = {"desktop": desktop}
        if phone:
            result["phone"] = phone
        return result

    def compose_module_css(self, features: List[str], delay: str = "0ms") -> Dict:
        """Compose module-level css object from feature list.

        Returns: {"desktop": "...", "tablet": "...", "phone": "..."}
        """
        desktop_parts = []
        if "blur_reveal" in features:
            desktop_parts.append(self.blur_reveal_animation_css(delay))
        if "icon_container" in features:
            desktop_parts.append(self.icon_container_css())
        if "gradient_line" in features:
            desktop_parts.append(self.gradient_line_css(
                kwargs.get("line_target", "eyebrow"),
                kwargs.get("line_side", "before")
            ))
        desktop = "\n".join(p for p in desktop_parts if p)
        return {"desktop": desktop} if desktop else {}


class RowBuilder:
    """Builds row structures for different layouts."""

    @staticmethod
    def grid_row(modules: List[Dict], max_cols: int = 3,
                 col_decoration: Optional[Dict] = None) -> Dict:
        n = len(modules)
        ncols = min(n, max_cols)
        col_type = {1: "4_4", 2: "1_2", 4: "1_4", 5: "1_5"}.get(ncols, "1_3")
        cols = []
        for m in modules:
            col = {"type": col_type, "modules": [m]}
            if col_decoration:
                col["decoration"] = col_decoration
            cols.append(col)
        while len(cols) < ncols:
            col = {"type": col_type, "modules": []}
            if col_decoration:
                col["decoration"] = col_decoration
            cols.append(col)
        return {
            "type": "divi/row",
            "module": "divi/row",
            "column_structure": ",".join([col_type] * ncols),
            "columns": cols,
        }

    @staticmethod
    def split_row(left_modules: List[Dict], right_modules: List[Dict],
                  left_type: str = "1_2", right_type: str = "1_2") -> Dict:
        return {
            "type": "divi/row",
            "module": "divi/row",
            "column_structure": f"{left_type},{right_type}",
            "columns": [
                {"type": left_type, "modules": left_modules},
                {"type": right_type, "modules": right_modules},
            ],
        }

    @staticmethod
    def full_row(modules: List[Dict]) -> Dict:
        return {
            "type": "divi/row",
            "module": "divi/row",
            "column_structure": "4_4",
            "columns": [{"type": "4_4", "modules": modules}],
        }
