"""Open-Meteo access for the Predict tab: caching, unit conversion, and failure
that the page can render.

`open_meteo.py` is the supplied helper and is kept byte-identical. It returns
`date, day_of_week, temp, humidity, precip, windspeed, cloudcover`, and it
drives everything here. Two of the final model's inputs are not in that shape,
so this module fetches them alongside and merges on date:

* **`solarradiation`** is not returned at all. Part 5 of the notebook names its
  source as Open-Meteo's `shortwave_radiation_sum` (MJ/m² per day) multiplied
  by 11.57 (= 1e6 / 86400) to reach the daily mean W/m² the model was fitted on.
* **`windspeed`** is returned, but as `wind_speed_10m_mean`, while the notebook
  fits on `wind_speed_10m_max`. Measured against the training data over 184 days
  of 2024, the mean runs 6.9 km/h below the dataset's own `windspeed` and the
  max within 0.5 km/h of it. At -185 hires per km/h the mean would over-predict
  by roughly 1,280 hires every day, so the max replaces it, as the notebook
  specifies.

Nothing here fits, adjusts or second-guesses a coefficient.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass

import pandas as pd
import requests

from open_meteo import ARCHIVE_URL, FORECAST_URL, geocode, open_meteo, open_meteo_history

#: MJ/m² per day -> mean W/m², the conversion Part 5 of the notebook specifies.
MJ_PER_DAY_TO_W_PER_M2 = 11.57

#: The daily fields open_meteo.py does not provide in the form the model needs.
EXTRA_DAILY = "wind_speed_10m_max,shortwave_radiation_sum"

JAN_2026 = ("2026-01-01", "2026-01-07")
FORECAST_DAYS = 5
LOCATION = "London"


@dataclass
class WeatherResult:
    """Either a frame or a reason there isn't one. Never an exception."""

    df: pd.DataFrame | None = None
    error: str | None = None
    location: str = ""

    @property
    def ok(self) -> bool:
        return self.df is not None and not self.df.empty


def _extras(lat: float, lon: float, *, url: str, params: dict) -> pd.DataFrame:
    """Fetch wind max and solar for the same days, as a two-column frame."""
    resp = requests.get(url, params={**params, "latitude": lat, "longitude": lon,
                                     "daily": EXTRA_DAILY, "timezone": "auto",
                                     "wind_speed_unit": "kmh"}, timeout=30)
    resp.raise_for_status()
    daily = resp.json()["daily"]
    return pd.DataFrame({
        "date": pd.to_datetime(daily["time"]),
        "windspeed": daily["wind_speed_10m_max"],
        "solarradiation": [
            None if v is None else v * MJ_PER_DAY_TO_W_PER_M2
            for v in daily["shortwave_radiation_sum"]
        ],
    })


def _merge(base: pd.DataFrame, extra: pd.DataFrame) -> pd.DataFrame:
    """Join the extra fields on date, letting them replace `windspeed`."""
    base = base.drop(columns=["windspeed"])
    return base.merge(extra, on="date", how="left")


def _fetch(kind: str) -> WeatherResult:
    try:
        lat, lon, label = geocode(LOCATION)
        if kind == "history":
            base = open_meteo_history(LOCATION, *JAN_2026)
            extra = _extras(lat, lon, url=ARCHIVE_URL,
                            params={"start_date": JAN_2026[0], "end_date": JAN_2026[1]})
        else:
            base = open_meteo(LOCATION, FORECAST_DAYS)
            extra = _extras(lat, lon, url=FORECAST_URL,
                            params={"forecast_days": FORECAST_DAYS})
        df = _merge(base, extra)
    except requests.exceptions.Timeout:
        return WeatherResult(error="Open-Meteo did not respond in time.")
    except requests.exceptions.RequestException:
        return WeatherResult(error="Open-Meteo could not be reached. "
                                   "This needs a working internet connection.")
    except (KeyError, ValueError) as exc:
        return WeatherResult(error=f"Open-Meteo returned an unexpected response: {exc}")

    missing = [c for c in ("windspeed", "solarradiation") if df[c].isna().any()]
    if missing:
        return WeatherResult(error="Open-Meteo returned no value for "
                                   + " and ".join(missing) + " on some of these days.")
    return WeatherResult(df=df, location=label)


@functools.lru_cache(maxsize=2)
def _cached(kind: str, _bust: int) -> WeatherResult:
    return _fetch(kind)


def get_weather(kind: str, refresh_token: int = 0) -> WeatherResult:
    """Cached for the session. `refresh_token` changes to force a retry."""
    return _cached(kind, refresh_token)
