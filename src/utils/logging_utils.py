"""Utilities for standardized logging configuration."""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Create and return a configured logger."""
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(asctime)s - %(levelname)s - %(message)s")
    return logging.getLogger(__name__)
