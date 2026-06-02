"""Token resolution for design system references.

Replaces the 3 separate recursive token resolvers
(`BrandResolver.resolve_deep`, `substitute_tokens`, `resolve_tokens_recursive`)
with a single implementation.
"""
import re
from typing import Any, Dict, Optional

TOKEN_PATTERN = re.compile(r"\{\{design:([^}]+)\}\}")


class TokenResolver:
    """Resolve `{{design:type:name}}` tokens against a design system dict.

    Backed by `design_system["tokens"]`. Falls back to returning the original
    string for unknown tokens (preserves call sites that may include literal
    braces that are not tokens).
    """

    def __init__(self, design_system: Dict[str, Any]):
        self.ds = design_system
        self.tokens = design_system.get("tokens", {}) if isinstance(design_system, dict) else {}

    def resolve(self, token_expr: str) -> str:
        if not isinstance(token_expr, str):
            return token_expr

        def _replace(match):
            inner = match.group(0).strip("{}").replace("design:", "")
            parts = inner.split(":")
            if len(parts) >= 2:
                cat, name = parts[0], parts[1]
                cat_data = self.tokens.get(cat, {})
                if isinstance(cat_data, dict) and name in cat_data:
                    return cat_data[name]
            return match.group(0)

        return TOKEN_PATTERN.sub(_replace, token_expr)

    def resolve_deep(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self.resolve(obj)
        if isinstance(obj, dict):
            return {k: self.resolve_deep(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.resolve_deep(item) for item in obj]
        return obj

    def has_token(self, category: str, name: str) -> bool:
        cat = self.tokens.get(category, {})
        return isinstance(cat, dict) and name in cat

    def get_token(self, category: str, name: str) -> Optional[str]:
        cat = self.tokens.get(category, {})
        if isinstance(cat, dict) and name in cat:
            return cat[name]
        return None
