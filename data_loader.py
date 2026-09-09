"""Load the London bikes dataset with the notebook's Part 0 cleaning.

The cleaning here mirrors Part 0 of bikes_assignment.ipynb line for line. If it
drifts, the app's numbers stop agreeing with the model, so treat this module as
a transcription rather than as code to improve.
"""

from __future__ import annotations

import functools
from pathlib import Path

import pandas as pd

SOURCE_URL = (
    "https://raw.githubusercontent.com/kostis-christodoulou/"
    "am01-code-sep2026/main/data/london_bikes.csv"
)
LOCAL_CSV = Path(__file__).parent / "data" / "london_bikes.csv"

# The two orderings the notebook fixes in Part 0.
DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# The weather variables Part 1's correlation heatmap is built from, in the
# notebook's own order.
HEATMAP_VARS = ["bikes_hired", "temp", "feelslike", "tempmax", "tempmin", "dew",
                "humidity", "precip", "windspeed", "cloudcover", "sealevelpressure"]

# The five weather variables a planner can put on the scatter's x axis. Keys are
# dataset columns; values are what a person calls them.
WEATHER_CHOICES = {
    "temp": "Temperature (°C)",
    "humidity": "Humidity (%)",
    "precip": "Precipitation (mm)",
    "windspeed": "Wind speed (km/h)",
    "cloudcover": "Cloud cover (%)",
}


@functools.lru_cache(maxsize=1)
def load_bikes() -> pd.DataFrame:
    """Return the cleaned daily dataset. Cached: the file is read once."""
    source = LOCAL_CSV if LOCAL_CSV.exists() else SOURCE_URL
    bike = pd.read_csv(source)

    # --- Part 0, verbatim ---------------------------------------------------
    bike["date"] = pd.to_datetime(bike["date"])
    bike["weekend"] = bike["wday"].isin(["Sat", "Sun"])
    bike["day_of_week"] = pd.Categorical(
        bike["day_of_week"], categories=DAY_ORDER, ordered=True)
    bike["month_name"] = pd.Categorical(
        bike["month_name"], categories=MONTH_ORDER, ordered=True)
    bike = bike[bike["date"] >= pd.to_datetime("2014-01-01", utc=True)].copy()
    # --- end Part 0 ---------------------------------------------------------

    # The CSV's dates carry a UTC offset, which Dash's date pickers cannot
    # round-trip. Dropping the offset *after* the filter above leaves the row
    # selection identical to the notebook's.
    bike["date"] = bike["date"].dt.tz_localize(None)

    return bike.reset_index(drop=True)


def dataset_span(bike: pd.DataFrame) -> dict:
    """Facts about the loaded data, computed at runtime and never typed in."""
    first, last = bike["date"].min(), bike["date"].max()
    return {
        "rows": len(bike),
        "first": first,
        "last": last,
        "years": last.year - first.year + 1,
    }
