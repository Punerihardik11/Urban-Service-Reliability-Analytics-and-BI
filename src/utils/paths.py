"""Path helpers for consistent project directory resolution."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


def get_data_dir() -> Path:
    """Return the data directory."""
    return PROJECT_ROOT / "data"
