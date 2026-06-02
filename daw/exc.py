"""Domain exceptions for the DAW bundle."""


class DawError(Exception):
    """Base exception for all DAW errors."""


class ConfigError(DawError):
    """Configuration error (missing .env, invalid site, etc)."""


class BlockNotFoundError(DawError):
    """No compatible block found for section type + strategy."""


class SectionTypeNotRegisteredError(DawError):
    """No handler registered for this section type."""


class StrategyError(DawError):
    """Invalid or unsupported strategy."""
