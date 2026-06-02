"""BrandResolver — adapts design tokens and exposes strategy.

Implementation delegates token recursion to `daw.tokens.TokenResolver` so
the same algorithm powers VIE, build_design_system, and the PHP resolver.
Preset / strategy accessors are kept here for backwards compatibility.
"""
from typing import Any, Dict, Optional

from daw.tokens import TokenResolver


class BrandResolver:
    """Resolves {{design:*}} tokens using the design system."""

    def __init__(self, design_system: Dict[str, Any]):
        self.ds = design_system
        self.tokens = design_system.get("tokens", {})
        self.presets = design_system.get("presets", {})
        self.strategy = design_system.get("strategy", "generic")
        self._token_resolver = TokenResolver(design_system)

    def has_token(self, token_name: str) -> bool:
        for cat in self.tokens.values():
            if isinstance(cat, dict) and token_name in cat:
                return True
        return False

    def has_preset(self, category: str, name: str) -> bool:
        return category in self.presets and name in self.presets[category]

    def resolve(self, token_expr: str) -> str:
        return self._token_resolver.resolve(token_expr)

    def resolve_deep(self, obj: Any) -> Any:
        return self._token_resolver.resolve_deep(obj)

    def get_token_value(self, category: str, name: str) -> Optional[str]:
        return self._token_resolver.get_token(category, name)

    def get_strategy(self) -> str:
        return self.strategy
