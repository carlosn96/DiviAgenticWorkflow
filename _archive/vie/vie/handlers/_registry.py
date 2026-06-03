"""SectionHandler Protocol + Registry — OCP for section types.

Adding a new section type now means:
  1. Create `vie/handlers/<my_type>.py` with a class implementing this Protocol.
  2. Add the import line to `vie/handlers/__init__.py`.

`SectionBuilder._build_rows()` then delegates to the registry. No switch,
no edit to existing handlers when a new one is added.
"""
from typing import Any, Dict, List, Optional, Protocol, Type

from daw.exc import SectionTypeNotRegisteredError


class SectionHandler(Protocol):
    """Interface for section type builders. One impl per section_type."""
    section_type: str

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        """Return list of Row dicts for this section."""
        ...


_registry: Dict[str, Type[SectionHandler]] = {}


def register(section_type: str):
    """Decorator to register a section handler."""
    def wrapper(cls: Type[SectionHandler]):
        _registry[section_type] = cls
        cls.section_type = section_type
        return cls
    return wrapper


def get_handler(section_type: str) -> SectionHandler:
    cls = _registry.get(section_type)
    if not cls:
        raise SectionTypeNotRegisteredError(
            f"No handler registered for '{section_type}'. "
            f"Available: {list(_registry.keys())}"
        )
    return cls()


def list_registered() -> List[str]:
    return list(_registry.keys())


def has_handler(section_type: str) -> bool:
    return section_type in _registry
