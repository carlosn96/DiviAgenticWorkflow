# vie/ — Visual Impact Engine (VIE v3.0)

Deterministic, schema-driven page-def generator. Architecture refactored from a
1,480-line monolith into a layered package with OCP-ready registries.

## Entry points

| Use case | Command |
|----------|---------|
| CLI (preferred) | `python DAW_bundle/vie/cli.py --brief-file ... --design-system ... --output ...` |
| Python module | `python -m vie.cli ...` |
| Python factory | `from vie.factory import create_vie; engine = create_vie(design_system)` |
| Legacy shim | `python DAW_bundle/ml-dataset/artifacts/visual_impact_engine.py ...` (re-exports vie/) |

## Module map

```
vie/
├── __init__.py        # Public API: VisualImpactEngine, create_vie, etc.
├── engine.py          # VisualImpactEngine — main orchestrator (DI-friendly)
├── factory.py         # create_vie() — preferred constructor for new code
├── cli.py             # CLI entry point
├── protocols.py       # Protocols (interfaces): BlockSelector, PropAdapter,
│                      # ImpactEvaluator, SectionHandler
├── adapters.py        # CatalogLoader, DatasetLoader
├── resolver.py        # BrandResolver (delegates to daw.tokens.TokenResolver)
├── analysis.py        # PageProfileAnalyzer (narrative + contrast plan)
├── selection.py       # BlockSelectionEngine (4D weighted scoring + harmony matrix)
├── director.py        # ImpactDirector (frontend-design → Divi params)
├── building.py        # DecorationBuilder, RowBuilder
├── module.py          # ModuleBuilder
├── section.py         # SectionBuilder (delegates to handlers/ registry)
│
├── handlers/          # ⭐ OCP registry for section types
│   ├── _registry.py   # SectionHandler Protocol + register()/get_handler()
│   ├── hero.py        # HeroSectionHandler + HeroCenteredSectionHandler
│   ├── features.py    # FeaturesSectionHandler
│   ├── stats.py       # StatsSectionHandler
│   ├── testimonials.py
│   ├── pricing.py
│   ├── faq.py
│   ├── cta.py
│   ├── gallery.py
│   ├── contact.py
│   ├── timeline.py
│   ├── trust_bar.py
│   └── content.py
│
└── strategies/        # ⭐ StrategyProfile — strategy-specific behavior
    └── __init__.py    # cool-luxury, warm-luxury, tech-glass, minimal, organic
```

## Adding a new section type (OCP)

```python
# 1. Create vie/handlers/my_type.py
from vie.handlers._registry import register
from vie.building import RowBuilder

@register("my-type")
class MyTypeSectionHandler:
    section_type = "my-type"
    def build(self, sec_def, index, director, module_builder, decorator,
              block, props):
        # ... return List[Dict] of rows
        ...

# 2. Add import to vie/handlers/__init__.py:
#    from . import my_type
```

`SectionBuilder._build_rows()` will pick it up via the registry. **No edits
to existing code required.**

## Adding a new strategy

```python
# 1. Add to daw/types.py
class Strategy(str, Enum):
    ...
    PLAYFUL = "playful"

# 2. Add to vie/strategies/__init__.py
PLAYFUL_PROFILE: Dict[str, Any] = {
    "name": "playful",
    "preferred_blocks": [...],
    "avoid_blocks": [...],
    "glass_enabled": True,
    "glow_intensity": "high",
    ...
    "preset_map": {...},
}

_PROFILE_BY_STRATEGY[Strategy.PLAYFUL.value] = PLAYFUL_PROFILE
```

## Dependency injection (advanced)

`VisualImpactEngine` accepts pre-built collaborators via keyword arguments:

```python
from vie.engine import VisualImpactEngine
from vie.adapters import CatalogLoader
from vie.resolver import BrandResolver
from vie.section import SectionBuilder

engine = VisualImpactEngine(
    design_system,
    resolver=BrandResolver(design_system),
    catalog=CatalogLoader(custom_path),
    section_builder=SectionBuilder(...),
)
```

This enables swapping any component in tests or alternative pipelines.

## Side-effect-free imports

```python
import sys
sys.path.insert(0, "DAW_bundle")
import vie  # no .env read, no sys.exit, no stdout
```

This is guaranteed: `vie/` does not call `_load_daw_site()` at import time.
DAW_SITE is only read by the `factory.create_vie()` and the CLI.

## Verification

```powershell
$env:DAW_SITE="<DAW_SITE>"
python _tools/verify_regression.py --seed 42
# Expected: PASS: hash identical (0ba2d6e76ea62607942064b982c85694)
```

## Refactor history

- 2026-06-01: Monolith `ml-dataset/artifacts/visual_impact_engine.py`
  (1,480 L, 11 classes) extracted into this package. Output remains
  byte-identical to the pre-refactor baseline.
- See `PLAN_RESOLVE_ANTIPATRONES.md` and `TASKS_RESOLVE_ANTIPATRONES.md` in
  the project root for the full plan and execution log.
