# Generated manually because makemigrations could not be run in this environment.
from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CalculationRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "calculator_slug",
                    models.CharField(
                        choices=[
                            ("belt_power", "Belt power"),
                            ("pulley_torque", "Pulley torque"),
                            ("belt_tension", "Belt tension"),
                        ],
                        max_length=64,
                    ),
                ),
                ("input_data", models.JSONField(help_text="Cleaned input values used for the calculation.")),
                ("result_title", models.CharField(max_length=255)),
                ("result_description", models.TextField(blank=True)),
                ("result_value", models.FloatField()),
                ("result_units", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
