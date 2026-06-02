"""Visual Impact Engine v3.0 — Schema-Driven Rich Page Generator (legacy shim).

This module is preserved for backwards compatibility with downstream callers
that import classes from this file path. The actual implementation now lives
in the `vie` package (`DAW_bundle/vie/`).

Importing this module re-exports every public class. The CLI entry point is
also preserved as `main()` for compatibility, but new code should use
`python -m vie.cli` or `from vie.factory import create_vie`.
"""
import sys
from pathlib import Path

# Auto-bootstrap sys.path so `python visual_impact_engine.py` and any
# import-from-legacy script still work.
_PKG_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

# Local DAW_bundle path so `from daw.cfg import load_daw_site` works.
_DAW_BUNDLE = Path(__file__).resolve().parent.parent.parent
if str(_DAW_BUNDLE) not in sys.path:
    sys.path.insert(0, str(_DAW_BUNDLE))

# Re-export from vie package.
from vie.adapters import CatalogLoader, DatasetLoader
from vie.analysis import PageProfileAnalyzer
from vie.building import DecorationBuilder, RowBuilder
from vie.cli import main
from vie.director import ImpactDirector
from vie.engine import VisualImpactEngine
from vie.module import ModuleBuilder
from vie.resolver import BrandResolver
from vie.section import SectionBuilder
from vie.selection import BlockSelectionEngine


# Legacy alias preserved for the (deprecated) `_load_daw_site` name.
def _load_daw_site() -> str:
    from daw.cfg import load_daw_site
    return load_daw_site()


__all__ = [
    "CatalogLoader",
    "DatasetLoader",
    "PageProfileAnalyzer",
    "DecorationBuilder",
    "RowBuilder",
    "ImpactDirector",
    "VisualImpactEngine",
    "ModuleBuilder",
    "BrandResolver",
    "SectionBuilder",
    "BlockSelectionEngine",
    "main",
    "_load_daw_site",
]


if __name__ == "__main__":
    main()
