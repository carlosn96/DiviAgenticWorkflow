# daw/ — DAW Shared Kernel

Layer 1 of the DAW architecture. **No side effects on import** — this is the
contract that all higher layers depend on.

## Modules

| Module | Purpose |
|--------|---------|
| `cfg.py` | Single source of truth for `.env` parsing and path resolvers |
| `types.py` | Domain enums (`SectionType`, `Strategy`, `ImpactLevel`, etc.) |
| `tokens.py` | `TokenResolver` — resolves `{{design:*}}` recursively |
| `constants.py` | `FRONTEND_PRINCIPLES`, `CONTENT_BANK` (shared by VIE + design system) |
| `exc.py` | Domain exceptions (`DawError`, `ConfigError`, etc.) |

## Public API

```python
import sys
sys.path.insert(0, "DAW_bundle")
from daw import (
    # Config
    load_daw_site,        # Read DAW_SITE from env or .env. Raises ConfigError.
    load_env,             # Read any var from env or .env. Never fails.
    get_site_dir,         # Path: DAW_bundle/site/<DAW_SITE>/
    get_brand_dir,        # Path: site/<DAW_SITE>/brand/
    get_plans_dir,        # Path: site/<DAW_SITE>/plans/
    get_design_system_path,  # Path: site/<DAW_SITE>/design-system/divitheme.json
    get_data_dir,         # Path: DAW_bundle/workspace/data/
    DAW_ROOT,             # Path: DAW_bundle/ (package parent)

    # Types
    SectionType,          # Enum: HERO, FEATURES, STATS, ...
    Strategy,             # Enum: COOL_LUXURY, WARM_LUXURY, TECH_GLASS, MINIMAL, ORGANIC
    ImpactLevel,          # Enum: LOW, MEDIUM, HIGH, VERY_HIGH
    NarrativeProfile,     # Enum: LANDING, STORY, EDUCATIONAL, SHOWCASE
    ContrastTransition,   # Enum: START, MATCH, BREAK, SUBTLE_SHIFT, CLIMAX

    # Tokens
    TokenResolver,        # Recursive {{design:*}} resolver

    # Constants
    FRONTEND_PRINCIPLES,  # Dict: typography, motion, spacing, color, aesthetic
    CONTENT_BANK,         # Dict: titles, paragraphs, features, pricing_tiers, ...

    # Exceptions
    ConfigError,          # Missing/invalid site config
    BlockNotFoundError,   # No compatible block for section+strategy
    SectionTypeNotRegisteredError,  # No handler for section type
    StrategyError,        # Invalid strategy
    DawError,             # Base exception
)
```

## Side-effect-free contract

```python
# This must be silent:
import daw

# This must raise ConfigError if DAW_SITE is not set:
load_daw_site()
```

The module-level `DAW_ROOT` constant is set at import time (it's a path
literal, not a side effect). All other configuration is **lazy** — `.env` is
parsed only on the first call to `load_daw_site()` or `load_env()`.

## Migration history (2026-06-01)

Before this package existed, every module in DAW_bundle implemented its own
`_load_daw_site()` and `.env` parser. The refactor consolidated:

| Before | After |
|--------|-------|
| 3 copies of `_load_daw_site()` | 1 in `daw.cfg.load_daw_site()` |
| 6 `.env` parsers (3 Python, 2 PHP, 1 inline) | 1 in `daw.cfg` (PHP kept its own) |
| 3 token resolvers (`BrandResolver.resolve_deep`, `substitute_tokens`, `resolve_tokens_recursive`) | 1 in `daw.tokens.TokenResolver` |
| 2 content banks (in `ux_pro_brief_generator.py` and `ml_brief_generator.py`) | 1 base in `daw.constants.CONTENT_BANK` + per-script overrides |
| Inline `_FRONTEND_PRINCIPLES` in `ImpactDirector` | 1 in `daw.constants.FRONTEND_PRINCIPLES` + VIE-specific override |
| Stringly-typed strategy/section type checks | `daw.types.SectionType` / `Strategy` enums |

## Verification

```python
import sys
sys.path.insert(0, "DAW_bundle")
import daw                    # no stdout, no .env read
print(daw.DAW_ROOT)            # Path("...DAW_bundle")
print(daw.Strategy.COOL_LUXURY.value)  # "cool-luxury"
```

See `PLAN_RESOLVE_ANTIPATRONES.md` for the architectural plan and
`_tools/verify_regression.py` for end-to-end regression checks.
