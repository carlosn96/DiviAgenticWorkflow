"""Visual Impact Engine — deterministic, schema-driven page-def generator.

Public API:
    from vie.engine import VisualImpactEngine
    from vie.factory import create_vie
"""
from vie.adapters import CatalogLoader, DatasetLoader
from vie.analysis import PageProfileAnalyzer
from vie.building import DecorationBuilder, RowBuilder
from vie.director import ImpactDirector
from vie.engine import VisualImpactEngine
from vie.factory import create_vie
from vie.module import ModuleBuilder
from vie.protocols import BlockSelector, ImpactEvaluator, PropAdapter, SectionHandler
from vie.resolver import BrandResolver
from vie.section import SectionBuilder
from vie.selection import BlockSelectionEngine

__all__ = [
    "CatalogLoader",
    "DatasetLoader",
    "PageProfileAnalyzer",
    "DecorationBuilder",
    "RowBuilder",
    "ImpactDirector",
    "VisualImpactEngine",
    "create_vie",
    "ModuleBuilder",
    "BlockSelector",
    "ImpactEvaluator",
    "PropAdapter",
    "SectionHandler",
    "BrandResolver",
    "SectionBuilder",
    "BlockSelectionEngine",
]
