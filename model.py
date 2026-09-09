"""Read the notebook's exported model and apply it. Never fits anything.

`model_coefficients.csv` is the contract between the analysis and this app:
two columns, `term` and `coefficient`, holding `Intercept`, one row per numeric
predictor, and one `day_<weekday>` row per weekday with Monday as the baseline
at 0.0. The numeric predictor set is read from the file, so a different final
model needs no code change here.

Two companion files are optional. `model_fit.csv` and `model_vif.csv` are read
if present and ignored if absent; nothing in this module derives, re-ranks or
recomputes their numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
COEFFICIENTS_CSV = ROOT / "model_coefficients.csv"
FIT_CSV = ROOT / "model_fit.csv"
VIF_CSV = ROOT / "model_vif.csv"

DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
BASELINE_DAY = "Mon"

# Every numeric term the app can actually fetch a value for. The first five come
# straight from open_meteo.py; `solarradiation` needs the extra Open-Meteo field
# and unit conversion that weather.py performs, following the notebook's Part 5.
# A term outside this set cannot be forecast at all, and the app says so rather
# than dropping it or substituting a zero.
FORECASTABLE = ("temp", "humidity", "precip", "windspeed", "cloudcover",
                "solarradiation")

# Plain-English readings of the units, used to phrase the coefficient sentences.
# A term absent here still works; it just gets a generic sentence.
UNITS = {
    "temp": ("one degree warmer", "°C"),
    "humidity": ("one point more humid", "%"),
    "precip": ("one more millimetre of rain", "mm"),
    "windspeed": ("one km/h more wind", "km/h"),
    "cloudcover": ("one point more cloud", "%"),
    "solarradiation": ("one more W/m² of sunshine", "W/m²"),
}


@dataclass
class Model:
    """The notebook's model, as read from disk."""

    intercept: float = 0.0
    numeric: dict[str, float] = field(default_factory=dict)
    days: dict[str, float] = field(default_factory=dict)
    #: numeric terms Open-Meteo cannot supply — non-empty means no forecasting
    unforecastable: list[str] = field(default_factory=list)
    #: a fatal problem reading the file; None when the model loaded
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def can_forecast(self) -> bool:
        return self.ok and not self.unforecastable

    def predict(self, weather: pd.DataFrame) -> pd.Series:
        """Intercept + sum(coefficient x value) + that day's weekday effect.

        `weather` needs one column per numeric term plus `day_of_week`, which is
        exactly the shape open_meteo.py returns.
        """
        if not self.can_forecast:
            raise RuntimeError("this model cannot be applied to Open-Meteo weather")
        total = pd.Series(self.intercept, index=weather.index, dtype=float)
        for term, coef in self.numeric.items():
            total += weather[term].astype(float) * coef
        total += weather["day_of_week"].map(self.days).astype(float)
        return total

    def sentences(self) -> list[tuple[str, float, str]]:
        """Each numeric effect as (subject, coefficient, plain-English reading)."""
        out = []
        for term, coef in self.numeric.items():
            phrase, _ = UNITS.get(term, (f"one more unit of {term}", ""))
            verb = "adds" if coef >= 0 else "removes"
            out.append((term, coef, f"{phrase} {verb} {abs(coef):,.0f} hires"))
        return out


def load_model(path: Path | None = None) -> Model:
    """Read the coefficients file, validating it rather than trusting it.

    The path is resolved on every call rather than bound as a default, so the
    module constant stays overridable.
    """
    path = path or COEFFICIENTS_CSV
    if not path.exists():
        return Model(error=f"{path.name} is missing, so no prediction can be made.")
    try:
        raw = pd.read_csv(path)
    except Exception as exc:                       # malformed CSV
        return Model(error=f"{path.name} could not be read: {exc}")

    if not {"term", "coefficient"} <= set(raw.columns):
        return Model(error=f"{path.name} must have columns 'term' and 'coefficient'.")

    coefs = dict(zip(raw["term"].astype(str), pd.to_numeric(raw["coefficient"], errors="coerce")))
    if "Intercept" not in coefs:
        return Model(error=f"{path.name} has no Intercept row.")

    days = {d: coefs[f"day_{d}"] for d in DAY_ORDER if f"day_{d}" in coefs}
    missing_days = [d for d in DAY_ORDER if d not in days]
    if missing_days:
        return Model(error=f"{path.name} is missing weekday rows: "
                           + ", ".join(f"day_{d}" for d in missing_days) + ".")

    numeric = {t: c for t, c in coefs.items()
               if t != "Intercept" and not t.startswith("day_")}
    if not numeric:
        return Model(error=f"{path.name} names no numeric predictors.")
    if any(pd.isna(v) for v in list(numeric.values()) + list(days.values())):
        return Model(error=f"{path.name} has a coefficient that is not a number.")

    return Model(
        intercept=float(coefs["Intercept"]),
        numeric=numeric,
        days={d: float(v) for d, v in days.items()},
        unforecastable=[t for t in numeric if t not in FORECASTABLE],
    )


def numeric_sources(path: Path | None = None) -> dict[str, str]:
    """The optional `source` column: where each predictor's value comes from.
    Written by the notebook's Part 5; absent on an older two-column file."""
    path = path or COEFFICIENTS_CSV
    if not path.exists():
        return {}
    try:
        raw = pd.read_csv(path)
    except Exception:
        return {}
    if "source" not in raw.columns:
        return {}
    return dict(zip(raw["term"].astype(str), raw["source"].astype(str)))


def load_fit(path: Path | None = None) -> pd.DataFrame | None:
    """The candidate-model comparison, or None when the notebook has not
    exported one. Read and returned untouched: never re-ranked or recomputed."""
    path = path or FIT_CSV
    if not path.exists():
        return None
    try:
        fit = pd.read_csv(path)
    except Exception:
        return None
    return fit if {"model", "is_final"} <= set(fit.columns) else None


def load_vif(path: Path | None = None) -> pd.DataFrame | None:
    """The collinearity check, or None when absent. Values are displayed exactly
    as exported — never recomputed with a constant, rescaled, capped or logged."""
    path = path or VIF_CSV
    if not path.exists():
        return None
    try:
        vif = pd.read_csv(path)
    except Exception:
        return None
    return vif if {"feature", "vif"} <= set(vif.columns) else None


def vif_band(value: float) -> tuple[str, str]:
    """The notebook's own thresholds, as (key, written label).

    The label exists so severity never depends on colour alone.
    """
    if value < 5:
        return "fine", "Fine"
    if value <= 10:
        return "warning", "Warning"
    return "serious", "Serious"
