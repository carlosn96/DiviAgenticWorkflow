"""DecorationBuilder + RowBuilder — Divi decoration objects and row layouts.

Phase 4: Integrates Pattern Dictionary for zone-aware decoration,
composite backgrounds, card hover system, and eyebrow pills.
"""
from typing import Any, Dict, List, Optional

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
