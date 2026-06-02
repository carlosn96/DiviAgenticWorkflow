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
    },
    "motion": {
        "stagger_step_ms": 100,
        "hero_duration_ms": 800,
        "content_duration_ms": 600,
        "micro_duration_ms": 300,
        "preferred_easing": "cubic-bezier(0.16,1,0.3,1)",
        "fallback_easing": "ease-out",
    },
    "spacing": {
        "section_padding_min": "80px",
        "section_padding_hero": "140px",
        "section_padding_cta": "120px",
        "container_padding_x": "96px",
        "mobile_padding_x": "24px",
    },
    "color": {
        "prefers_high_contrast": True,
        "minimum_contrast_ratio": 4.5,
    },
    "aesthetic": {
        "prefers_distinctive": True,
        "glass_alpha_min": 0.80,
        "glow_intensity_map": {"none": 0, "low": 0.1, "medium": 0.15, "high": 0.25},
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


