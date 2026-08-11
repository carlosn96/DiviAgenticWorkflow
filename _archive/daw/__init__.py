"""DAW shared kernel: configuration, types, tokens, constants, exceptions.

Single source of truth for cross-cutting concerns used by all DAW_bundle
modules. Importing this package has no side effects (no .env reads, no
sys.exit, no stdout output).
"""
from daw.cfg import load_daw_site, load_env, get_site_dir, get_brand_dir
from daw.cfg import get_plans_dir, get_design_system_path, get_data_dir, DAW_ROOT
from daw.exc import (
    DawError,
    ConfigError,
    BlockNotFoundError,
    SectionTypeNotRegisteredError,
    StrategyError,
)
from daw.tokens import TokenResolver
from daw.types import (
    SectionType,
    Strategy,
    ImpactLevel,
    NarrativeProfile,
    ContrastTransition,
)
from daw.constants import FRONTEND_PRINCIPLES, CONTENT_BANK

__all__ = [
    "load_daw_site",
    "load_env",
    "get_site_dir",
    "get_brand_dir",
    "get_plans_dir",
    "get_design_system_path",
    "get_data_dir",
    "DAW_ROOT",
    "DawError",
    "ConfigError",
    "BlockNotFoundError",
    "SectionTypeNotRegisteredError",
    "StrategyError",
    "TokenResolver",
    "SectionType",
    "Strategy",
    "ImpactLevel",
    "NarrativeProfile",
    "ContrastTransition",
    "FRONTEND_PRINCIPLES",
    "CONTENT_BANK",
]
