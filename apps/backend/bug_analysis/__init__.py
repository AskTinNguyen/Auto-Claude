"""
Bug Analysis Module
===================

Port of Ralph CLI Bug Wikipedia feature to Auto-Claude.

Features:
- Git history scanning for bug-related commits
- AI-powered categorization using Claude Haiku
- Markdown documentation generation
- Pattern detection and GitHub issue creation
- Deep dive root cause analysis using Auto-Claude agents
- QA integration for recurring issue detection
"""

from .models import BugCategory, BugData, CategorizedBug, BugPattern

# Lazy imports for modules (to avoid circular imports)
def _lazy_import(module_name: str):
    """Lazy import helper to avoid circular dependencies"""
    import importlib
    return importlib.import_module(f".{module_name}", package=__name__)


def get_scanner():
    """Get scanner module"""
    return _lazy_import("scanner")


def get_categorizer():
    """Get categorizer module"""
    return _lazy_import("categorizer")


def get_generator():
    """Get generator module"""
    return _lazy_import("generator")


def get_detector():
    """Get detector module"""
    return _lazy_import("detector")


def get_deep_dive():
    """Get deep_dive module"""
    return _lazy_import("deep_dive")


def get_integration():
    """Get integration module"""
    return _lazy_import("integration")


__all__ = [
    "BugCategory",
    "BugData",
    "CategorizedBug",
    "BugPattern",
    "get_scanner",
    "get_categorizer",
    "get_generator",
    "get_detector",
    "get_deep_dive",
    "get_integration",
]
