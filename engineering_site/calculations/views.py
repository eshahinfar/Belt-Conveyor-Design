"""Views for the engineering calculations website."""

from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .forms import CALCULATION_FORMS, CalculationResult, get_calculator_form
from .models import CalculationRecord


def home(request: HttpRequest) -> HttpResponse:
    """Redirect to the first calculator to satisfy the single-topic-per-page UX."""

    first_slug = CALCULATION_FORMS[0][0]
    return redirect("calculations:calculator", slug=first_slug)


def calculator(request: HttpRequest, slug: str) -> HttpResponse:
    """Render and process a single calculator form identified by ``slug``."""

    try:
        title, form = get_calculator_form(slug, request.POST or None)
    except KeyError as exc:  # pragma: no cover - defensive branch
        raise Http404("Calculator not found") from exc

    result: CalculationResult | None = None

    if request.method == "POST" and form.is_valid():
        result = form.calculate()
        action = request.POST.get("action", "calculate")
        if action == "save":
            if request.user.is_authenticated:
                CalculationRecord.objects.create(
                    user=request.user,
                    calculator_slug=slug,
                    input_data=form.cleaned_data,
                    result_title=result.title,
                    result_description=result.description,
                    result_value=result.value,
                    result_units=result.units,
                )
                messages.success(request, "Result saved to your account.")
            else:
                messages.error(request, "Sign in to save calculation results.")

    context = {
        "calculator_slug": slug,
        "calculator_title": title,
        "calculator_form": form,
        "result": result,
    }
    return render(request, "calculations/calculator_detail.html", context)


class SavedResultsView(LoginRequiredMixin, ListView):
    """Display saved calculation results for the authenticated user."""

    model = CalculationRecord
    template_name = "calculations/saved_results.html"
    context_object_name = "records"
    extra_context = {"calculator_slug": None}

    def get_queryset(self) -> Any:  # pragma: no cover - thin wrapper
        return CalculationRecord.objects.filter(user=self.request.user).select_related("user")


def signup(request: HttpRequest) -> HttpResponse:
    """Allow new users to register an account and start saving results."""

    if request.user.is_authenticated:
        return redirect("calculations:home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("calculations:home")
    else:
        form = UserCreationForm()

    context = {
        "form": form,
    }
    return render(request, "registration/signup.html", context)
