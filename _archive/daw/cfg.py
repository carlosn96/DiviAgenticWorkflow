"""Centralized configuration: .env parser and path resolvers.

This module is the single source of truth for reading .env and resolving
site-specific paths. Importing it has no side effects (parsing is lazy).

Backwards compatibility: this module historically was implemented per-file
as `_load_daw_site()`. New code should use `from daw.cfg import load_daw_site`.
"""
import os
from pathlib import Path
from typing import Optional

from daw.exc import ConfigError

DAW_ROOT: Path = Path(__file__).resolve().parent.parent
"""Absolute path to DAW_bundle/ (parent of daw/ package)."""

_ENV_CACHE: Optional[dict] = None


def _parse_env_file() -> dict:
    """Parse .env file from project root. Single implementation."""
    env_path = DAW_ROOT.parent / ".env"
    if not env_path.exists():
        return {}
    result = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            result[key] = val
    return result


def _get_env() -> dict:
    global _ENV_CACHE
    if _ENV_CACHE is None:
        _ENV_CACHE = _parse_env_file()
    return _ENV_CACHE


def load_daw_site() -> str:
    """Read DAW_SITE from environment or .env. Raises ConfigError if missing.

    Replaces the old per-file `_load_daw_site()` implementations. Never
    calls sys.exit() — callers should let the exception propagate.
    """
    site = os.environ.get("DAW_SITE")
    if site:
        return site
    env = _get_env()
    site = env.get("DAW_SITE", "")
    if site:
        return site
    raise ConfigError(
        "DAW_SITE no está definido. "
        "Defínelo en .env (DAW_SITE=nombre) o como variable de entorno."
    )


def load_env(key: str, default: str = "") -> str:
    """Read any env var from environment or .env. Never fails."""
    val = os.environ.get(key)
    if val:
        return val
    return _get_env().get(key, default)


def get_site_dir() -> Path:
    return DAW_ROOT / "site" / load_daw_site()


def get_brand_dir() -> Path:
    return get_site_dir() / "brand"


def get_plans_dir() -> Path:
    return get_site_dir() / "plans"


def get_design_system_path() -> Path:
    return get_site_dir() / "design-system" / "divitheme.json"


def get_data_dir() -> Path:
    return DAW_ROOT / "workspace" / "data"
