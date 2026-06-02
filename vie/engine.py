"""VisualImpactEngine — main orchestrator. Brief + design system → rich page-def.

Phase 2 keeps the original constructor signature (positional design_system,
optional paths, optional seed) so the existing CLI and daw_build.py keep
working unchanged. The factory (`vie.factory.create_vie`) is the preferred
entry point for new callers.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from vie.adapters import CatalogLoader, DatasetLoader
from vie.analysis import PageProfileAnalyzer
from vie.building import DecorationBuilder
from vie.director import ImpactDirector
from vie.module import ModuleBuilder
from vie.resolver import BrandResolver
from vie.section import SectionBuilder
from vie.selection import BlockSelectionEngine


class VisualImpactEngine:
    """Main translator: brief + design system + catalog + dataset → rich page-def."""

    def __init__(self, design_system: Dict[str, Any],
                 catalog_path: Optional[Path] = None,
                 dataset_path: Optional[Path] = None,
                 seed: Optional[int] = None,
                 *, resolver: Optional[BrandResolver] = None,
                 catalog: Optional[CatalogLoader] = None,
                 dataset: Optional[DatasetLoader] = None,
                 block_engine: Optional[BlockSelectionEngine] = None):
        # Allow DI of pre-built collaborators (Phase 3+); default to constructing them.
        self.resolver = resolver or BrandResolver(design_system)
        self.catalog = catalog or CatalogLoader(catalog_path)
        self.dataset = dataset or DatasetLoader(dataset_path)
        self.strategy = self.resolver.get_strategy()
        self.block_engine = block_engine or BlockSelectionEngine(
            self.dataset, self.strategy,
            self.dataset.get_strategy_adaptation(self.strategy)
        )
        self.director = ImpactDirector(self.resolver, self.catalog, self.dataset,
                                       block_engine=self.block_engine, seed=seed)
        self.decorator = DecorationBuilder(self.catalog, self.resolver)
        self.module_builder = ModuleBuilder(self.director, self.decorator)
        # Pasamos design_direction al SectionBuilder para habilitar diseño calculado
        self.section_builder = SectionBuilder(
            self.director, self.module_builder, self.decorator,
            design_direction=None  # Se actualiza en translate_brief
        )

    def translate_brief(self, brief: Dict[str, Any]) -> Dict[str, Any]:
        """Convert brief sections into rich page-def with intelligent block selection."""
        sections_list = brief.get("sections", [])

        # Activar design_direction si está presente en el brief
        design_direction = brief.get("design_direction")
        if design_direction != self.section_builder.design_direction:
            # Recrear SectionBuilder con la nueva dirección de diseño
            self.section_builder = SectionBuilder(
                self.director, self.module_builder, self.decorator,
                design_direction=design_direction,
                all_sections=sections_list
            )

        page_profile = PageProfileAnalyzer.detect_narrative_profile(brief)
        contrast_plan = PageProfileAnalyzer.build_contrast_plan(sections_list, self.strategy)

        self.director._block_cache = self.block_engine.select_blocks(
            sections_list, page_profile, contrast_plan, seed=self.director.seed
        )

        sections = []
        for i, sec_def in enumerate(sections_list):
            section = self.section_builder.build(sec_def, i)
            sections.append(section)

        return {
            "title": brief.get("title", "Page"),
            "slug": brief.get("slug", "page"),
            "description": brief.get("description", ""),
            "sections": sections,
            "_meta": {
                "narrative_profile": page_profile,
                "strategy": self.strategy,
            }
        }

    def evaluate_page_impact(self, page_def: Dict) -> Dict:
        """Score the visual impact of the entire page."""
        scores: Dict[str, int] = {}
        total = 0
        for i, section in enumerate(page_def.get("sections", [])):
            score = self.director.evaluate_impact(section)
            st = section.get("presets", ["unknown"])[0] if section.get("presets") else f"section_{i}"
            scores[st] = score
            total += score
        return {
            "total": total,
            "per_section": scores,
            "average": total / len(scores) if scores else 0,
            "max_possible": len(scores) * 50 if scores else 0,
            "impact_percentage": (total / (len(scores) * 50) * 100) if scores else 0
        }
