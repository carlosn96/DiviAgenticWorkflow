"""Protocols (interfaces) for VIE — used for typing and DI seams.

These Protocols document the contracts between major VIE collaborators and
make dependencies swappable for testing. They do not need to be imported at
runtime for the engine to work — they are TypeScript-style hints for humans
and tools.
"""
from typing import Any, Dict, List, Optional, Protocol


class BlockSelector(Protocol):
    def select_blocks(self, sections: List[Dict], page_profile: str,
                      contrast_plan: List[Dict], seed: Optional[int] = None) -> List[Optional[Dict]]: ...


class PropAdapter(Protocol):
    def adapt_block_props(self, block: Dict) -> Dict: ...
    def apply_combination_rules(self, props: Dict) -> Dict: ...


class ImpactEvaluator(Protocol):
    def evaluate_impact(self, section: Dict) -> int: ...
    def evaluate_page_impact(self, page_def: Dict) -> Dict: ...


class SectionHandler(Protocol):
    """Interface for section type builders. One impl per section_type.

    The full SectionHandler registry will be introduced in Phase 3; for now
    this Protocol documents the contract that the existing SectionBuilder
    satisfies and that handlers will implement.
    """
    section_type: str

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]: ...
