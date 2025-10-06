"""Views for the engineering calculations website."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .forms import prepare_forms


def home(request: HttpRequest) -> HttpResponse:
    """Render the landing page with engineering calculators."""

    forms, active_slug, result = prepare_forms(request.POST if request.method == "POST" else None)

    context = {
        "forms": forms,
        "active_slug": active_slug,
        "result": result,
    }
    return render(request, "calculations/home.html", context)
