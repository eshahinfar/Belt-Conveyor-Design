"""Context data helpers for templates."""

from __future__ import annotations

from .forms import get_calculator_links


def calculator_navigation(request):
    """Expose calculator links for global navigation menus."""

    return {
        "calculator_links": get_calculator_links(),
    }
