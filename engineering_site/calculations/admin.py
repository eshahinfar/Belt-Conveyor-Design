"""Admin configuration for calculations app."""

from __future__ import annotations

from django.contrib import admin

from .models import CalculationRecord


@admin.register(CalculationRecord)
class CalculationRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "calculator_slug", "result_value", "result_units", "created_at")
    list_filter = ("calculator_slug", "created_at")
    search_fields = ("user__username", "result_title")
    autocomplete_fields = ("user",)
