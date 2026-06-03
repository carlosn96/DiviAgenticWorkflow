"""Section handler registry.

`SectionBuilder._build_rows()` looks up the handler for the section type
in this registry. To add a new section type:

  1. Create `vie/handlers/<my_type>.py` with:
        from vie.handlers._registry import register
        @register("my-type")
        class MyTypeSectionHandler:
            section_type = "my-type"
            def build(self, sec_def, index, director, module_builder, decorator, block, props):
                ...
  2. Add the import line below.

The list below mirrors the `SectionType` enum in `daw/types.py`. Phase 3
goal: adding a section type is a 1-file change.
"""
from typing import Dict, List, Type

from vie.handlers._registry import (
    SectionHandler,
    get_handler,
    has_handler,
    list_registered,
    register,
)

# Auto-register all built-in handlers.
from vie.handlers import (  # noqa: E402,F401
    hero,
    features,
    stats,
    testimonials,
    pricing,
    faq,
    cta,
    gallery,
    contact,
    timeline,
    trust_bar,
    content,
    team,
)


__all__ = [
    "SectionHandler",
    "register",
    "get_handler",
    "has_handler",
    "list_registered",
]
