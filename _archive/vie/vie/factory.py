"""Factory for building a fully-wired VisualImpactEngine.

This is the preferred entry point for new callers (daw_build, tests, etc).
Phase 3+ will be able to swap any collaborator here.
"""
from pathlib import Path
from typing import Any, Dict, Optional

from vie.adapters import CatalogLoader, DatasetLoader
from vie.building import DecorationBuilder
from vie.director import ImpactDirector
from vie.engine import VisualImpactEngine
from vie.module import ModuleBuilder
from vie.resolver import BrandResolver
from vie.section import SectionBuilder
from vie.selection import BlockSelectionEngine


def create_vie(design_system: Dict[str, Any],
               catalog_path: Optional[Path] = None,
               dataset_path: Optional[Path] = None,
               seed: Optional[int] = None) -> VisualImpactEngine:
    """Construct a fully-wired VIE graph."""
    resolver = BrandResolver(design_system)
    catalog = CatalogLoader(catalog_path)
    dataset = DatasetLoader(dataset_path)
    strategy = resolver.get_strategy()
    strategy_adapt = dataset.get_strategy_adaptation(strategy)
    block_engine = BlockSelectionEngine(dataset, strategy, strategy_adapt)
    director = ImpactDirector(resolver, catalog, dataset, block_engine=block_engine, seed=seed)
    decorator = DecorationBuilder(catalog, resolver)
    module_builder = ModuleBuilder(director, decorator)
    section_builder = SectionBuilder(director, module_builder, decorator)
    return VisualImpactEngine(
        design_system,
        resolver=resolver,
        catalog=catalog,
        dataset=dataset,
        block_engine=block_engine,
    )
