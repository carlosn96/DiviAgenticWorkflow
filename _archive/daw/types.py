"""Domain enums and types for the DAW bundle.

Replaces stringly-typed code paths with proper Enum types. Subclasses `str`
to remain JSON-serializable (e.g. SectionType.HERO == "hero" in JSON dumps).
"""
from enum import Enum


class SectionType(str, Enum):
    HERO = "hero"
    HERO_SPLIT = "hero-split"
    HERO_CENTERED = "hero-centered"
    FEATURES = "features"
    STATS = "stats"
    TESTIMONIALS = "testimonials"
    PRICING = "pricing"
    FAQ = "faq"
    CTA = "cta"
    GALLERY = "gallery"
    CONTACT = "contact"
    TIMELINE = "timeline"
    TRUST_BAR = "trust-bar"
    CONTENT = "content"

    @classmethod
    def from_str(cls, s: str) -> "SectionType":
        """Safe conversion; raises ValueError if unknown."""
        try:
            return cls(s)
        except ValueError:
            raise ValueError(f"Unknown SectionType: {s}")


class Strategy(str, Enum):
    COOL_LUXURY = "cool-luxury"
    WARM_LUXURY = "warm-luxury"
    TECH_GLASS = "tech-glass"
    MINIMAL = "minimal"
    ORGANIC = "organic"

    def contains_glass(self) -> bool:
        return self in (self.TECH_GLASS, self.COOL_LUXURY, self.WARM_LUXURY)

    def contains_luxury(self) -> bool:
        return self in (self.COOL_LUXURY, self.WARM_LUXURY)

    def is_dark_background(self) -> bool:
        return self in (self.COOL_LUXURY, self.WARM_LUXURY, self.TECH_GLASS)


class ImpactLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class NarrativeProfile(str, Enum):
    LANDING = "landing"
    STORY = "story"
    EDUCATIONAL = "educational"
    SHOWCASE = "showcase"


class ContrastTransition(str, Enum):
    START = "start"
    MATCH = "match"
    BREAK = "break"
    SUBTLE_SHIFT = "subtle_shift"
    CLIMAX = "climax"
