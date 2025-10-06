"""Forms used for engineering design calculations."""

from __future__ import annotations

from dataclasses import dataclass

from django import forms


@dataclass
class CalculationResult:
    """Container describing a calculation result."""

    title: str
    description: str
    value: float
    units: str

    def as_dict(self) -> dict[str, str | float]:
        return {
            "title": self.title,
            "description": self.description,
            "value": self.value,
            "units": self.units,
        }


class BeltPowerForm(forms.Form):
    """Estimate the power requirement for a belt conveyor."""

    throughput = forms.FloatField(
        label="Material throughput (t/h)",
        min_value=0,
        help_text="Mass flow rate of conveyed material in tonnes per hour.",
    )
    lift_height = forms.FloatField(
        label="Lift height (m)",
        min_value=0,
        help_text="Vertical lift between loading and discharge points.",
    )
    friction_factor = forms.FloatField(
        label="Friction factor (N per tonne)",
        min_value=0,
        initial=15.0,
        help_text="Average resistance per tonne of material to account for idler and skirt friction.",
    )
    belt_speed = forms.FloatField(
        label="Belt speed (m/s)",
        min_value=0.1,
        help_text="Linear speed of the belt.",
    )

    def calculate(self) -> CalculationResult:
        mass_flow = self.cleaned_data["throughput"] / 3.6  # convert t/h to kg/s (approx.)
        lift = self.cleaned_data["lift_height"]
        friction = self.cleaned_data["friction_factor"]
        speed = self.cleaned_data["belt_speed"]

        gravity = 9.80665
        lift_power = mass_flow * gravity * lift / 1000
        friction_power = (self.cleaned_data["throughput"] * friction) / 1000
        shaft_power = lift_power + friction_power
        total_power = shaft_power / 0.92  # assume 92% efficiency
        effective_tension = (shaft_power * 1000) / speed

        return CalculationResult(
            title="Required drive power",
            description=(
                "Estimated power requirement including allowance for lift and friction "
                f"losses. Effective tension ≈ {effective_tension:,.0f} N."
            ),
            value=round(total_power, 2),
            units="kW",
        )


class PulleyTorqueForm(forms.Form):
    """Calculate motor torque from power and rotational speed."""

    power = forms.FloatField(
        label="Drive power (kW)",
        min_value=0,
        help_text="Rated motor power available at the pulley.",
    )
    rotational_speed = forms.FloatField(
        label="Pulley speed (rpm)",
        min_value=0.1,
        help_text="Rotational speed of the conveyor pulley.",
    )

    def calculate(self) -> CalculationResult:
        power_w = self.cleaned_data["power"] * 1000
        rpm = self.cleaned_data["rotational_speed"]
        torque = (power_w * 60) / (2 * 3.141592653589793 * rpm)

        return CalculationResult(
            title="Pulley torque",
            description="Shaft torque delivered to the pulley.",
            value=round(torque, 1),
            units="N·m",
        )


class BeltTensionForm(forms.Form):
    """Estimate belt tensions using Euler's equation."""

    torque = forms.FloatField(
        label="Pulley torque (N·m)",
        min_value=0,
        help_text="Torque transmitted by the drive pulley.",
    )
    pulley_radius = forms.FloatField(
        label="Pulley radius (m)",
        min_value=0.01,
        help_text="Radius of the drive pulley.",
    )
    wrap_angle = forms.FloatField(
        label="Wrap angle (degrees)",
        min_value=10,
        max_value=360,
        initial=180,
        help_text="Angle of belt contact with the pulley.",
    )
    friction_coefficient = forms.FloatField(
        label="Belt/pulley friction coefficient",
        min_value=0.05,
        initial=0.35,
        help_text="Dimensionless coefficient of friction between belt and pulley lagging.",
    )

    def calculate(self) -> CalculationResult:
        torque = self.cleaned_data["torque"]
        radius = self.cleaned_data["pulley_radius"]
        wrap = self.cleaned_data["wrap_angle"]
        mu = self.cleaned_data["friction_coefficient"]

        tight_minus_slack = torque / radius
        wrap_radians = wrap * 3.141592653589793 / 180
        tension_ratio = pow(2.718281828459045, mu * wrap_radians)
        slack_tension = tight_minus_slack / (tension_ratio - 1)
        tight_tension = slack_tension * tension_ratio

        return CalculationResult(
            title="Tight and slack side tensions",
            description="Belt tensions computed using Euler's belt friction equation.",
            value=round(tight_tension, 1),
            units="N (tight side)",
        )


CALCULATION_FORMS: tuple[tuple[str, str, type[forms.Form]], ...] = (
    ("belt_power", "Belt power", BeltPowerForm),
    ("pulley_torque", "Pulley torque", PulleyTorqueForm),
    ("belt_tension", "Belt tension", BeltTensionForm),
)


def prepare_forms(bound_data: dict[str, str] | None = None) -> tuple[
    list[tuple[str, str, forms.Form]], str | None, CalculationResult | None
]:
    """Instantiate the configured calculators and optionally evaluate one of them."""

    forms_list: list[tuple[str, str, forms.Form]] = []
    active_slug: str | None = None
    result: CalculationResult | None = None

    slug = bound_data.get("form_id") if bound_data else None
    for form_slug, title, form_cls in CALCULATION_FORMS:
        if slug and slug == form_slug:
            form = form_cls(bound_data)
            active_slug = form_slug
            if form.is_valid():
                result = form.calculate()
        else:
            form = form_cls()
        forms_list.append((form_slug, title, form))

    return forms_list, active_slug, result
