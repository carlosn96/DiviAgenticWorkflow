"""Shared constants for the DAW bundle.

Frontend design principles and defaults used by VIE, the design system
builder, and the brief generators. Single source of truth so that a
change in one place propagates everywhere.
"""

FRONTEND_PRINCIPLES = {
    "typography": {
        "penalize_generic_fonts": True,
        "generic_fonts": ["Inter", "Arial", "Roboto", "Helvetica", "sans-serif"],
        "headline_line_height": "1.1em",
        "body_line_height": "1.6em",
        "eyebrow_letter_spacing": "2px",
        "eyebrow_transform": "uppercase",
        "heading_text_shadow": {
            "glow": "0 0 80px {accent}12",
            "depth": "0 4px 60px rgba(0,0,0,0.4)",
        },
        "eyebrow_line": {
            "width": "32px",
            "height": "1px",
            "gradient": "90deg, {accent}, transparent",
            "position": "before",
        },
    },
    "motion": {
        "stagger_step_ms": 100,
        "hero_duration_ms": 800,
        "content_duration_ms": 600,
        "micro_duration_ms": 300,
        "preferred_easing": "cubic-bezier(0.16,1,0.3,1)",
        "fallback_easing": "ease-out",
        "blur_reveal": {
            "initial_blur": "4px",
            "initial_translateY": "40px",
            "duration": "900ms",
            "easing": "cubic-bezier(0.16,1,0.3,1)",
            "keyframe_name": "revealUp",
        },
    },
    "spacing": {
        "section_padding_min": "80px",
        "section_padding_hero": "140px",
        "section_padding_cta": "120px",
        "container_padding_x": "96px",
        "mobile_padding_x": "24px",
        "responsive": {
            "hero": {"desktop": "200px", "tablet": "140px", "phone": "120px"},
            "section": {"desktop": "160px", "tablet": "100px", "phone": "80px"},
            "cta": {"desktop": "180px", "tablet": "120px", "phone": "100px"},
        },
    },
    "color": {
        "prefers_high_contrast": True,
        "minimum_contrast_ratio": 4.5,
    },
    "aesthetic": {
        "prefers_distinctive": True,
        "glass_alpha_min": 0.80,
        "glow_intensity_map": {"none": 0, "low": 0.1, "medium": 0.15, "high": 0.25},
        "glass": {
            "blur": "20px",
            "saturate": 1.4,
            "border_opacity": 0.08,
            "border_color": "{accent}",
        },
        "grain": {
            "base_frequency": "0.65",
            "octaves": 3,
            "opacity_section": 0.02,
            "opacity_card": 0.03,
            "stitch": "stitch",
        },
        "multi_shadow": {
            "ambient": {"spread": "-12px", "blur": "48px", "color": "{accent}0.08"},
            "hover_ambient": {"spread": "-16px", "blur": "64px", "color": "{accent}0.14"},
            "button_ambient": {"y": "8px", "blur": "32px", "spread": "-4px", "color": "{accent}0.25"},
            "button_directional": {"y": "2px", "blur": "8px", "color": "{accent}0.15"},
            "button_inset": {"y": "1px", "color": "rgba(255,255,255,0.2)"},
        },
        "button_gradient": {
            "angle": "135deg",
            "stops": ["{accent} 0%", "{accent_light} 40%", "{accent_muted} 100%"],
        },
        "icon_container": {
            "size": "64px",
            "radius": "16px",
            "bg_opacity": 0.08,
            "hover_bg_opacity": 0.14,
            "hover_scale": 1.1,
            "hover_translateY": "-4px",
        },
        "column_divider": {
            "width": "1px",
            "gradient": "180deg, transparent 0%, {accent}0.15 50%, transparent 100%",
            "top_crop": "20%",
            "bottom_crop": "20%",
        },
        "quote_mark": {
            "char": "\u201C",
            "font_family": "serif",
            "size": "72px",
            "opacity": 0.1,
            "position_top": "20px",
            "position_left": "28px",
        },
        "orb_glow": {
            "size": "80%",
            "opacity_center": 0.14,
            "opacity_edge": 0.04,
            "fade_to_transparent": "60%",
        },
        "fade_overlay": {
            "height": "120px",
            "direction": "0deg",
            "from_color": "{bg_dark}",
            "to_color": "transparent",
        },
    },
}


CONTENT_BANK = {
    "titles": [
        "Transformamos Ideas en Resultados",
        "Diseñamos el Futuro, Hoy",
        "Tu Visión, Nuestra Misión",
        "Construimos Experiencias Memorables",
    ],
    "paragraphs": [
        "Combinamos diseño, tecnología y estrategia para crear productos que la gente ama usar.",
        "Cada proyecto es una oportunidad para innovar y superar las expectativas del cliente.",
        "Trabajamos con equipos apasionados por la excelencia y el detalle.",
    ],
    "features": [
        "Diseño centrado en el usuario final",
        "Rendimiento y accesibilidad de primera",
        "Integración con tu stack existente",
        "Iteración continua basada en datos",
        "Soporte dedicado y documentación clara",
    ],
    "pricing_tiers": [
        {"name": "Starter", "price": "29", "period": "mes",
         "features": ["Hasta 3 proyectos", "Soporte por email", "Actualizaciones mensuales"]},
        {"name": "Pro", "price": "79", "period": "mes",
         "features": ["Proyectos ilimitados", "Soporte prioritario", "Analítica avanzada"]},
        {"name": "Enterprise", "price": "—", "period": "custom",
         "features": ["Soluciones a medida", "SLA dedicado", "Onboarding personalizado"]},
    ],
    "testimonials": [
        {"name": "María González", "role": "CTO, Acme Corp",
         "quote": "El equipo entendió nuestra visión desde el primer día. La entrega fue impecable."},
        {"name": "Luis Pérez", "role": "Founder, Studio X",
         "quote": "Pasamos de idea a producto en tiempo récord. La calidad del diseño es excepcional."},
    ],
    "portfolio": [
        {"title": "Rebranding Aurora", "category": "Brand & Web",
         "summary": "Sistema visual completo y plataforma de marketing para B2B SaaS."},
        {"title": "E-commerce Helios", "category": "E-commerce",
         "summary": "Tienda online con +35% de conversión frente a la versión anterior."},
    ],
    "timeline": [
        {"year": "2018", "event": "Fundación del estudio"},
        {"year": "2020", "event": "Primeros 50 proyectos entregados"},
        {"year": "2023", "event": "Expansión a LATAM y Europa"},
        {"year": "2026", "event": "100+ clientes activos"},
    ],
}


