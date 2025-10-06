"""Database models for storing saved calculation results."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class CalculationRecord(models.Model):
    """A persisted calculation result associated with a user account."""

    CALCULATOR_CHOICES = (
        ("belt_power", "Belt power"),
        ("pulley_torque", "Pulley torque"),
        ("belt_tension", "Belt tension"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    calculator_slug = models.CharField(max_length=64, choices=CALCULATOR_CHOICES)
    input_data = models.JSONField(help_text="Cleaned input values used for the calculation.")
    result_title = models.CharField(max_length=255)
    result_description = models.TextField(blank=True)
    result_value = models.FloatField()
    result_units = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_calculator_slug_display()} result for {self.user}"  # pragma: no cover
