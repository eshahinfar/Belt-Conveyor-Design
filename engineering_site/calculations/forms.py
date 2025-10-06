"""Forms used for engineering design calculations."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Callable

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


class ShaftDesignForm(forms.Form):
    """Design a rotating shaft for fatigue using Shigley's distortion-energy relations."""

    DEFAULT_GEOMETRY = json.dumps(
        [
            {"length_mm": 150.0, "diameter_mm": 60.0},
            {"length_mm": 120.0, "diameter_mm": 45.0},
            {"length_mm": 150.0, "diameter_mm": 60.0},
        ]
    )

    alternating_bending_moment = forms.FloatField(
        label="Alternating bending moment M_a (N·m)",
        min_value=0,
        help_text="Fluctuating component of the bending moment at the critical location.",
    )
    mean_bending_moment = forms.FloatField(
        label="Mean bending moment M_m (N·m)",
        min_value=0,
        help_text="Steady component of bending at the critical location.",
        initial=0.0,
    )
    alternating_torque = forms.FloatField(
        label="Alternating torque T_a (N·m)",
        min_value=0,
        help_text="Fluctuating component of transmitted torque.",
        initial=0.0,
    )
    mean_torque = forms.FloatField(
        label="Mean torque T_m (N·m)",
        min_value=0,
        help_text="Steady component of transmitted torque.",
    )
    bending_kf = forms.FloatField(
        label="Fatigue stress concentration Kf",
        min_value=1.0,
        initial=1.8,
        help_text="Use Figure A-15-9/6-26 values for the critical shoulder or keyway.",
    )
    torsion_kfs = forms.FloatField(
        label="Torsional fatigue factor Kfs",
        min_value=1.0,
        initial=1.5,
        help_text="Use Figure A-15-8/6-27 values for the same feature in torsion.",
    )
    endurance_limit = forms.FloatField(
        label="Corrected endurance limit S_e (MPa)",
        min_value=1.0,
        initial=210.0,
        help_text="Fully corrected endurance limit at the design location.",
    )
    ultimate_strength = forms.FloatField(
        label="Ultimate tensile strength S_ut (MPa)",
        min_value=1.0,
        initial=700.0,
    )
    true_fracture_strength = forms.FloatField(
        label="True fracture strength σ'_f (MPa)",
        min_value=1.0,
        required=False,
        help_text="Needed for the DE-Morrow criterion; ≈ 1.45·S_ut for many steels.",
    )
    yield_strength = forms.FloatField(
        label="Yield strength S_y (MPa)",
        min_value=1.0,
        required=False,
        help_text="Optional check using the static von Mises stress (Eq. 7-15).",
    )
    design_factor = forms.FloatField(
        label="Design factor n",
        min_value=1.0,
        initial=2.0,
    )
    shaft_geometry = forms.CharField(
        label="Shaft geometry",
        widget=forms.HiddenInput(),
        initial=DEFAULT_GEOMETRY,
    )
    failure_criterion = forms.ChoiceField(
        label="Fatigue criterion",
        choices=(
            ("de_goodman", "DE-Goodman"),
            ("de_morrow", "DE-Morrow"),
            ("de_gerber", "DE-Gerber"),
            ("de_swt", "DE-SWT"),
        ),
        initial="de_goodman",
    )

    def clean(self) -> dict[str, float]:
        data = super().clean()
        criterion = data.get("failure_criterion")
        if criterion == "de_morrow" and not data.get("true_fracture_strength"):
            raise forms.ValidationError(
                "Provide the true fracture strength to use the DE-Morrow relation."
            )

        raw_geometry = data.get("shaft_geometry")
        try:
            geometry = json.loads(raw_geometry) if raw_geometry else []
        except (TypeError, json.JSONDecodeError) as exc:
            raise forms.ValidationError("Unable to parse the shaft geometry definition.") from exc

        if not isinstance(geometry, list) or not geometry:
            raise forms.ValidationError("Define at least one shaft segment in the geometry designer.")

        parsed_geometry: list[dict[str, float]] = []
        for index, segment in enumerate(geometry, start=1):
            if not isinstance(segment, dict):
                raise forms.ValidationError(
                    f"Segment {index} is not a valid geometry description."
                )
            try:
                length = float(segment["length_mm"])
                diameter = float(segment["diameter_mm"])
            except (KeyError, TypeError, ValueError) as exc:
                raise forms.ValidationError(
                    f"Segment {index} must include numeric length and diameter values."
                ) from exc
            if length <= 0 or diameter <= 0:
                raise forms.ValidationError(
                    f"Segment {index} requires positive length and diameter dimensions."
                )
            parsed_geometry.append({"length_mm": length, "diameter_mm": diameter})

        self.geometry_segments = parsed_geometry
        data["shaft_geometry"] = json.dumps(parsed_geometry)
        return data

    def calculate(self) -> CalculationResult:
        design_factor = self.cleaned_data["design_factor"]
        criterion = self.cleaned_data["failure_criterion"]

        ma = self.cleaned_data["alternating_bending_moment"]
        mm = self.cleaned_data["mean_bending_moment"]
        ta = self.cleaned_data["alternating_torque"]
        tm = self.cleaned_data["mean_torque"]
        kf = self.cleaned_data["bending_kf"]
        kfs = self.cleaned_data["torsion_kfs"]

        se = self.cleaned_data["endurance_limit"] * 1_000_000.0
        sut = self.cleaned_data["ultimate_strength"] * 1_000_000.0
        sigma_f_prime = (
            self.cleaned_data["true_fracture_strength"] * 1_000_000.0
            if self.cleaned_data.get("true_fracture_strength")
            else None
        )
        sy = (
            self.cleaned_data["yield_strength"] * 1_000_000.0
            if self.cleaned_data.get("yield_strength")
            else None
        )

        def von_mises_components(diameter_m: float) -> tuple[float, float, float, float]:
            """Return alternating/mean von Mises stresses for a solid shaft."""

            if diameter_m <= 0:
                raise ValueError("Diameter must be positive.")

            denom = math.pi * diameter_m**3
            bending_alt = (32.0 * kf * ma) / denom
            bending_mean = (32.0 * kf * mm) / denom
            torsion_alt = (16.0 * kfs * ta) / denom
            torsion_mean = (16.0 * kfs * tm) / denom

            sigma_a = math.sqrt(bending_alt**2 + 3.0 * torsion_alt**2)
            sigma_m = math.sqrt(bending_mean**2 + 3.0 * torsion_mean**2)
            return sigma_a, sigma_m, bending_alt + bending_mean, torsion_alt + torsion_mean

        def safety_goodman(diameter_m: float) -> float:
            sigma_a, sigma_m, *_ = von_mises_components(diameter_m)
            denom = sigma_a / se + sigma_m / sut
            if denom <= 0:
                return math.inf
            return 1.0 / denom

        def safety_morrow(diameter_m: float) -> float:
            if not sigma_f_prime:
                return math.inf
            sigma_a, sigma_m, *_ = von_mises_components(diameter_m)
            denom = sigma_a / se + sigma_m / sigma_f_prime
            if denom <= 0:
                return math.inf
            return 1.0 / denom

        def safety_gerber(diameter_m: float) -> float:
            sigma_a, sigma_m, *_ = von_mises_components(diameter_m)
            denom = sigma_a / se + (sigma_m / sut) ** 2
            if denom <= 0:
                return math.inf
            return 1.0 / denom

        def safety_swt(diameter_m: float) -> float:
            sigma_a, sigma_m, *_ = von_mises_components(diameter_m)
            base = sigma_a**2 + sigma_a * sigma_m
            if base <= 0:
                return math.inf
            return se / math.sqrt(base)

        safety_functions = {
            "de_goodman": safety_goodman,
            "de_morrow": safety_morrow,
            "de_gerber": safety_gerber,
            "de_swt": safety_swt,
        }
        safety_functions_labels = {
            "de_goodman": "DE-Goodman",
            "de_morrow": "DE-Morrow",
            "de_gerber": "DE-Gerber",
            "de_swt": "DE-SWT",
        }

        def solve_diameter(safety_fn: Callable[[float], float]) -> float:
            """Binary search the smallest diameter meeting the requested design factor."""

            # If the safety factor already exceeds the requirement for a 1 mm shaft,
            # return that minimum practical size.
            lower = 0.001
            if safety_fn(lower) >= design_factor:
                return lower

            upper = lower
            for _ in range(40):
                upper *= 2.0
                if safety_fn(upper) >= design_factor:
                    break
            else:
                # Loads are so large that even a 1 m shaft is insufficient.
                raise ValueError(
                    "Unable to satisfy the requested design factor below 1 metre diameter."
                )

            for _ in range(80):
                mid = 0.5 * (lower + upper)
                if safety_fn(mid) >= design_factor:
                    upper = mid
                else:
                    lower = mid
            return upper

        diameters_m: dict[str, float] = {}
        for key, fn in safety_functions.items():
            if key == "de_morrow" and not sigma_f_prime:
                continue
            diameters_m[key] = solve_diameter(fn)

        if criterion == "de_morrow" and "de_morrow" not in diameters_m:
            raise forms.ValidationError(
                "Unable to evaluate the DE-Morrow criterion without σ'_f."
            )

        selected_diameter_m = diameters_m[criterion]
        selected_mm = selected_diameter_m * 1000.0
        recommended_mm = math.ceil(selected_mm)

        # Calculate the static von Mises check using Eq. (7-15).
        sigma_a, sigma_m, bending_total, torsion_total = von_mises_components(
            selected_diameter_m
        )
        sigma_max = math.sqrt(bending_total**2 + 3.0 * torsion_total**2)
        ny = sy / sigma_max if sy else None

        lines: list[str] = []
        for key in safety_functions:
            if key not in diameters_m:
                continue
            value_mm = diameters_m[key] * 1000.0
            lines.append(f"{safety_functions_labels[key]} → {value_mm:.2f} mm")

        if ny:
            lines.append(
                f"Static yield factor of safety n_y ≈ {ny:.2f} at the selected diameter."
            )

        description = (
            "Fatigue diameters solved by binary search using the distortion-energy "
            "relations (Eqs. 7-6 to 7-14). "
            "Recommended to specify a {recommended_mm:.0f} mm shaft or the next larger "
            "standard size."
        ).format(recommended_mm=recommended_mm)

        geometry_segments = getattr(self, "geometry_segments", [])
        if geometry_segments:
            min_geometry_diameter = min(segment["diameter_mm"] for segment in geometry_segments)
            total_length = sum(segment["length_mm"] for segment in geometry_segments)
            lines.append(
                (
                    "Drawn shaft summary → minimum diameter {min_d:.1f} mm over {count} segments "
                    "spanning {length:.0f} mm total length."
                ).format(
                    min_d=min_geometry_diameter,
                    count=len(geometry_segments),
                    length=total_length,
                )
            )
            if min_geometry_diameter + 1e-6 < selected_mm:
                lines.append(
                    "Warning: the required diameter exceeds the thinnest segment in the geometry."
                )

        if lines:
            description += "\n" + "\n".join(lines)

        return CalculationResult(
            title="Required shaft diameter",
            description=description,
            value=round(selected_mm, 2),
            units="mm",
        )


CALCULATION_FORMS: tuple[tuple[str, str, type[forms.Form]], ...] = (
    ("belt_power", "Belt power", BeltPowerForm),
    ("pulley_torque", "Pulley torque", PulleyTorqueForm),
    ("belt_tension", "Belt tension", BeltTensionForm),
    ("shaft_design", "Shaft design", ShaftDesignForm),
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


def get_calculator_form(slug: str, bound_data: dict[str, str] | None = None) -> tuple[str, forms.Form]:
    """Return the configured calculator form for the provided slug."""

    for form_slug, title, form_cls in CALCULATION_FORMS:
        if slug == form_slug:
            return title, form_cls(bound_data)
    raise KeyError(f"Unknown calculator slug: {slug}")


def get_calculator_links() -> list[tuple[str, str]]:
    """Provide slug/title pairs for navigation menus."""

    return [(slug, title) for slug, title, _ in CALCULATION_FORMS]
