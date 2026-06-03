"""NarrativeComposer — Expande briefs a 6-8 secciones con ritmo visual.

Alternancia forzada claro/oscuro + escalado visual + secciones obligatorias por page_type.
"""
from typing import Any, Dict, List


class NarrativeComposer:
    """Composicion narrativa: ritmo visual y densidad de secciones."""

    # Secciones obligatorias por page_type (en orden)
    _SECTION_TEMPLATES = {
        "home": [
            {"section_type": "hero", "visual_zone": "dark"},
            {"section_type": "trust-bar", "visual_zone": "light"},
            {"section_type": "features", "visual_zone": "light"},
            {"section_type": "stats", "visual_zone": "dark"},
            {"section_type": "testimonials", "visual_zone": "light"},
            {"section_type": "pricing", "visual_zone": "light"},
            {"section_type": "cta", "visual_zone": "dark"},
        ],
        "about": [
            {"section_type": "hero", "visual_zone": "dark"},
            {"section_type": "trust-bar", "visual_zone": "light"},
            {"section_type": "content", "visual_zone": "light"},
            {"section_type": "features", "visual_zone": "light"},
            {"section_type": "team", "visual_zone": "light"},
            {"section_type": "stats", "visual_zone": "dark"},
            {"section_type": "cta", "visual_zone": "dark"},
        ],
        "services": [
            {"section_type": "hero", "visual_zone": "dark"},
            {"section_type": "features", "visual_zone": "light"},
            {"section_type": "process", "visual_zone": "light"},
            {"section_type": "pricing", "visual_zone": "light"},
            {"section_type": "testimonials", "visual_zone": "light"},
            {"section_type": "cta", "visual_zone": "dark"},
        ],
        "destinations": [
            {"section_type": "hero", "visual_zone": "dark"},
            {"section_type": "slider", "visual_zone": "light"},
            {"section_type": "features", "visual_zone": "light"},
            {"section_type": "testimonials", "visual_zone": "light"},
            {"section_type": "cta", "visual_zone": "dark"},
        ],
        "contact": [
            {"section_type": "hero", "visual_zone": "dark"},
            {"section_type": "content", "visual_zone": "light"},
            {"section_type": "contact", "visual_zone": "light"},
            {"section_type": "cta", "visual_zone": "dark"},
        ],
    }

    @staticmethod
    def compose(brief: Dict) -> Dict:
        """Expande un brief a composicion narrativa completa."""
        page_type = brief.get("page_type", "home")
        sections_in = brief.get("sections", [])

        # Template de secciones para este page_type
        template = NarrativeComposer._SECTION_TEMPLATES.get(page_type, NarrativeComposer._SECTION_TEMPLATES["home"])

        # Indexar secciones del brief por tipo
        by_type: Dict[str, List[Dict]] = {}
        for s in sections_in:
            st = s.get("section_type", s.get("type", "generic"))
            by_type.setdefault(st, []).append(s)

        composed_sections = []
        for tmpl in template:
            st = tmpl["section_type"]
            zone = tmpl["visual_zone"]

            if st in by_type and by_type[st]:
                # Usar seccion del brief
                sec = by_type[st].pop(0)
                sec["_visual_zone"] = zone
                composed_sections.append(sec)
            else:
                # Seccion faltante: generar con contenido minimo
                composed_sections.append(NarrativeComposer._generate_fallback(st, zone, brief))

        # Agregar secciones sobrantes del brief que no estaban en el template
        for st, remaining in by_type.items():
            for sec in remaining:
                sec["_visual_zone"] = "light"
                composed_sections.append(sec)

        result = dict(brief)
        result["sections"] = composed_sections
        result["_composed"] = True
        return result

    @staticmethod
    def _generate_fallback(section_type: str, zone: str, brief: Dict) -> Dict:
        """Genera una seccion minima si el brief no la incluyo."""
        title = brief.get("title", "Nomade Viajes")
        if section_type == "hero":
            return {
                "section_type": "hero",
                "eyebrow": "NOMADE VIAJES",
                "title": title,
                "text": "Experiencias de viaje premium diseñadas para ti.",
                "btn_primary_text": "Explorar",
                "btn_primary_url": "/",
                "_visual_zone": zone,
            }
        if section_type == "cta":
            return {
                "section_type": "cta",
                "eyebrow": "CONTACTO",
                "title": "¿Listo para tu próxima aventura?",
                "text": "Déjanos sorprenderte.",
                "btn_primary_text": "Contactar",
                "btn_primary_url": "/contacto",
                "_visual_zone": zone,
            }
        if section_type == "features":
            return {
                "section_type": "features",
                "eyebrow": "SERVICIOS",
                "title": "Lo Que Ofrecemos",
                "items": [
                    {"title": "Experiencia Única", "text": "Cada viaje es diseñado a la medida.", "icon": "&#xe03a;"},
                    {"title": "Atención Personal", "text": "Guías nativos y grupos reducidos.", "icon": "&#xe065;"},
                    {"title": "Destinos Exóticos", "text": "Acceso a lugares fuera del radar.", "icon": "&#xe0b4;"},
                ],
                "_visual_zone": zone,
            }
        if section_type == "stats":
            return {
                "section_type": "stats",
                "eyebrow": "NÚMEROS",
                "title": "Nuestra Trayectoria",
                "stats": [
                    {"number": "12", "label": "Años de Experiencia"},
                    {"number": "3000", "label": "Viajeros Felices"},
                    {"number": "40", "label": "Países Recorridos"},
                    {"number": "4.9", "label": "Calificación"},
                ],
                "_visual_zone": zone,
            }
        if section_type == "testimonials":
            return {
                "section_type": "testimonials",
                "eyebrow": "TESTIMONIOS",
                "title": "Lo Que Dicen Nuestros Viajeros",
                "testimonials": [
                    {"name": "María G.", "role": "Viajera Frecuente", "text": "La mejor experiencia de viaje que he tenido."},
                    {"name": "Carlos R.", "role": "Aventurero", "text": "Atención impecable y destinos inolvidables."},
                ],
                "_visual_zone": zone,
            }
        if section_type == "pricing":
            return {
                "section_type": "pricing",
                "eyebrow": "PRECIOS",
                "title": "Planes de Viaje",
                "packages": [
                    {"name": "Escapada", "price": "$1,200", "features": ["3 días", "Hotel boutique", "Guía local"]},
                    {"name": "Aventura", "price": "$2,800", "features": ["7 días", "Todas las comidas", "Transporte incluido"]},
                    {"name": "Expedición", "price": "$5,500", "features": ["14 días", "Experiencia VIP", "Soporte 24/7"]},
                ],
                "_visual_zone": zone,
            }
        if section_type == "slider":
            return {
                "section_type": "slider",
                "eyebrow": "GALERÍA",
                "title": "Destinos en Imágenes",
                "slider": [
                    {"image": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800&q=80", "heading": "Patagonia", "content": "Trekking, glaciares y una naturaleza que te silencia."},
                    {"image": "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=800&q=80", "heading": "Bali", "content": "Cultura, templos y playas que parecen de otro mundo."},
                    {"image": "https://images.unsplash.com/photo-1506929562872-bb421503ef21?w=800&q=80", "heading": "Japón", "content": "Tradición y futuro en cada rincón. Gastronomía impecable."},
                    {"image": "https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=800&q=80", "heading": "Perú", "content": "Machu Picchu y mucho más. Historia viva en los Andes."},
                ],
                "_visual_zone": zone,
            }
        if section_type == "contact":
            return {
                "section_type": "contact",
                "eyebrow": "CONTACTO",
                "title": "Hablemos",
                "text": "Cuéntanos sobre tu próximo viaje.",
                "form": {
                    "fields": [
                        {"label": "Nombre", "type": "text", "required": True},
                        {"label": "Email", "type": "email", "required": True},
                        {"label": "Teléfono", "type": "text", "required": False},
                        {"label": "Mensaje", "type": "textarea", "required": True},
                    ]
                },
                "map": {"address": "Ciudad de México, México"},
                "_visual_zone": zone,
            }
        if section_type == "process":
            return {
                "section_type": "process",
                "eyebrow": "PROCESO",
                "title": "Cómo Funciona",
                "steps": [
                    {"title": "Consulta", "text": "Nos cuentas qué buscas."},
                    {"title": "Diseño", "text": "Creamos tu itinerario a medida."},
                    {"title": "Viaje", "text": "Vives la experiencia."},
                    {"title": "Recuerdo", "text": "Regresas con una historia única."},
                ],
                "_visual_zone": zone,
            }
        if section_type == "team":
            return {
                "section_type": "team",
                "eyebrow": "EQUIPO",
                "title": "Quiénes Somos",
                "team": [
                    {"name": "Ana M.", "role": "Fundadora", "text": "Apasionada por los viajes auténticos."},
                    {"name": "Luis R.", "role": "Director", "text": "Expert en destinos exóticos."},
                ],
                "_visual_zone": zone,
            }
        if section_type == "content":
            return {
                "section_type": "content",
                "eyebrow": "SOBRE NOSOTROS",
                "title": "Nuestra Historia",
                "text": "Nacimos del amor por los viajes auténticos. Diseñamos experiencias que conectan personas y culturas.",
                "btn_primary_text": "Conocer Más",
                "btn_primary_url": "/sobre-nosotros",
                "_visual_zone": zone,
            }
        if section_type == "contact":
            return {
                "section_type": "contact",
                "eyebrow": "CONTACTO",
                "title": "Hablemos",
                "text": "Cuéntanos sobre tu próximo viaje.",
                "_visual_zone": zone,
            }
        return {"section_type": section_type, "_visual_zone": zone}
