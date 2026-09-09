# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are **TfL demand planners and the analysts who brief them**. They
come with operational questions — how busy will the scheme be on Thursday, does
rain actually stop people cycling, is the weekend dip as big as everyone says —
and they need answers they can repeat in a meeting without a caveat that
collapses. They read charts to make a call about bike redistribution,
maintenance windows and docking-station staffing.

The **landing page at `/` has a second visitor**, and this one is concrete: the
**course marker**, plus any general data-curious arrival. Confirmed 2026-09-09 —
this is a school assignment and the marker is the real evaluating audience.
Success there is two-part: the visitor understands in seconds what questions the
tool answers and enters the dashboard, *and* it reads as a real analytical
product rather than a coursework submission. That second half is why the landing
page exists at all; the assignment does not require it.

## Product Purpose

An interactive dashboard for London's Santander Cycles scheme that does two
jobs with one dataset. It **explains** daily hires — how they move with
temperature, humidity, rain, wind and cloud, and how the week's shape differs
from Monday to Sunday — and it **forecasts** them, applying a fitted linear
model to real Open-Meteo weather for the first week of January 2026 and for the
next five days. Success is a planner leaving with a number they trust and an
explanation they can repeat.

## Positioning

Most coursework dashboards are either analytically sound and visually generic,
or attractive and statistically loose. This one keeps every statistical decision
**owned by the source notebook and verifiable against it**, and invests the
effort in interface craft and in stating the model's limits out loud. Its
defining trustworthiness move: the app **never fits anything**. It reads
coefficients from a CSV, applies them, and refuses to forecast at all if the
model asks for a variable the weather feed cannot supply — rather than silently
substituting a zero and shipping a wrong number.

## Operating Context

- Two routes behind one Dash shell (`app.py` + `dcc.Location`): a **landing
  page at `/`** and the **dashboard at `/app`**. Entering the dashboard is the
  moment that carries the themed loading state.
- The dashboard is two tabs: **Explore the data** and **Predict**.
- Desktop is primary; the layout degrades sensibly on mobile.
- Deployed free on Render (`render.yaml`); the free tier sleeps after
  inactivity, so a first load can be slow to wake. Python 3.12, managed with
  `uv`.
- No API keys and no environment variables anywhere in the stack. Open-Meteo is
  free and unauthenticated.

## Capabilities and Constraints

- **Stack:** Python 3.12 + pandas + Plotly + **Dash** (not Streamlit), served by
  gunicorn. Flat repo root: `app.py`, `open_meteo.py`, `model_coefficients.csv`,
  `pyproject.toml`, `uv.lock`, `render.yaml`, `README.md`, plus supporting
  modules (`data_loader.py`, `figures.py`, `layout.py`, `callbacks.py`,
  `landing.py`, `theme.py`, `model.py`, `assets/style.css`).
- **Statistical logic is frozen and lives in the notebook**
  (`~/Code/am01/session10/bikes_assignment.ipynb`). The chosen model, its
  variables, its coefficients, the VIF decisions and the diagnostics are the
  notebook's. This project decides only **how results are visualised and
  arranged**. The app never fits, re-fits or infers a model.
- **Data grain:** one row per **day**, whole scheme. Target `bikes_hired`.
  Verified against the live CSV: **4,383 rows, 2014-01-01 → 2025-12-31**, after
  Part 0's cleaning. (These figures are computed at runtime in the app, never
  typed into source.) The raw file starts 2010-07-30 and has 5,634 rows; Part 0
  drops everything before 2014.
- **Cleaning mirrors Part 0 exactly:** parse `date` (the CSV is ISO-8601 with a
  `Z`, so it parses tz-aware UTC), derive `weekend` from `wday`, set
  `day_of_week` (Mon→Sun) and `month_name` (Jan→Dec) as ordered categoricals,
  keep `date >= 2014-01-01`.
- **No geography.** There is no station, borough, postcode or coordinate column.
  No map, no per-station view.
- **The coefficients file is the contract.** `model_coefficients.csv` has two
  columns, `term` and `coefficient`: `Intercept`, one row per numeric predictor,
  and `day_Mon` … `day_Sun`. **`day_Mon` is the baseline at `0.0`**, so every
  weekday effect is read *relative to Monday* and must be labelled that way.
  Coefficient values are never hard-coded in Python; the numeric predictor set
  is read from the file at load.
- **The model cannot express uncertainty.** The file carries coefficients only —
  no standard errors, no residual scale — so there are **no prediction intervals
  and no confidence bands**. Point predictions only, said plainly.
- **The forecast is bounded by the weather feed.** If the coefficients file
  names a numeric term the app cannot fetch a value for (`tempmax`,
  `feelslike`, `dew`, …), the Predict tab cannot forecast: it names the
  offending term and stops. It never drops the term and never substitutes zero.
- **The final model (notebook completed 2026-09-09)** is
  `temp + humidity + precip + windspeed + solarradiation + C(day_of_week)`,
  fitted on **1,096 days from 2023 onwards** — average daily hires fell by
  about 6,000 in 2023, so earlier years carry the wrong level into a forecast.
  Adj R² 0.685, residual SE 3,491.
- **Two model inputs need more than `open_meteo.py` supplies**, so `weather.py`
  fetches them alongside while the helper itself stays byte-identical:
  `solarradiation` (`shortwave_radiation_sum` × 11.57, named by Part 5) and
  `windspeed` as `wind_speed_10m_max` rather than the helper's mean. Measured
  over 184 days of 2024, the mean sits 6.9 km/h under the training data and the
  max within 0.5 km/h; at −185 hires per km/h the mean would over-predict by
  roughly 1,280 hires a day.
- **A known, accepted bias:** the ×11.57 solar conversion does not reproduce the
  training variable — it runs about +59.5 W/m² high (r = 0.758), worth roughly
  +875 hires a day. The user decided on 2026-09-09 to **ship as the notebook
  specifies**, since the notebook owns the model. Do not silently rescale it.
- **Two optional companion files.** `model_fit.csv` (candidate-model comparison)
  and `model_vif.csv` (collinearity, `before`/`after` stages) are read if
  present and their sections are hidden entirely if absent. Their numbers are
  laid out and captioned, never derived, re-ranked or recomputed.
- **Network failure is a designed state.** If Open-Meteo is unreachable the page
  still renders, with an inline explanation and a retry — never a stack trace.
  Responses are cached for the session so switching tabs does not re-fetch.

## Brand Commitments

- Name in-app: **Cycle Demand** for the London Santander Cycles scheme.
- **Santander branding is approved for use** (confirmed 2026-09-09, on the
  grounds that this is a school project). The mark and wordmark identify the
  *scheme being analysed*. Binding condition attached at the same time: the app
  carries an unambiguous **"independent student project — not affiliated with
  Santander or Transport for London"** line, so it identifies its subject
  without presenting itself as an official product.
- **Binding visual references (user-supplied 2026-09-09, in `design_inspo/`):**
  - `dashboardstyle.jpeg` is the **primary layout reference** — light
    card-based dashboard, persistent left sidebar nav, rounded cards, a KPI/
    summary row, a wide hero band, pill toggles.
  - `colors.jpeg` governs **colour handling** — a red rail against white and
    light-grey cards, with charts drawn in red / black / grey rather than a
    rainbow.
  - The palette anchors are **Santander red** (`logo.jpeg`, `bank.jpeg`) and
    the **navy of the bike frame** (`bike.jpeg`).
- Theme: London cycling as **transport infrastructure**, not lifestyle.
  Restrained and institutional in the working surfaces — charts, tables and
  controls carry no ornament.
- **Revised 2026-09-09 at the user's request:** the earlier "no cartoon"
  commitment is lifted for the rail alone. It carries a cartoon London skyline
  (the London Eye, Elizabeth Tower, 30 St Mary Axe) as `assets/skyline.svg`,
  drawn only in white at low opacity so it reads as tone rather than as a
  second graphic competing with the brand mark. Windows and the Gherkin's
  curtain wall are masked out of their silhouettes, so no palette colour is
  named inside the file and the artwork survives a change of rail colour.
- One Plotly template defined once and shared by every figure: fonts, grid,
  hover, margins, and both a sequential and a categorical palette.
- Motion is purposeful only: a themed loading state on entry, soft tab
  transitions, hover feedback. Nothing that competes with the data.

## Evidence on Hand

- Real dataset (verified, live URL):
  `https://raw.githubusercontent.com/kostis-christodoulou/am01-code-sep2026/main/data/london_bikes.csv`
  — 40 columns; weather, calendar and `bikes_hired`. Zero nulls across the
  model's variables after Part 0.
- **The temperature block is real and measured** (post-2014 correlations):
  `temp`↔`feelslike` r = 0.99, `temp`↔`tempmax` 0.97, `temp`↔`tempmin` 0.96,
  `temp`↔`dew` 0.90. This is the collinearity the notebook's Part 1 is pointing
  at and Part 3 tests, and the heatmap must make that block legible rather than
  bury it in a uniform grid.
- Source notebook: `~/Code/am01/session10/bikes_assignment.ipynb`. Part 0 and
  Part 1 are complete; **Parts 2–5 are still empty scaffolds**, so no real
  coefficients, fit table or VIF table exist yet.
- Weather helper: `open_meteo.py`, copied into the repo unchanged.
- **Design references (user-supplied, `design_inspo/`, gitignored — they are
  third-party screenshots and brand photos and do not belong in a public repo):**
  `dashboardstyle.jpeg`, `colors.jpeg`, `bank.jpeg`, `bike.jpeg`, `logo.jpeg`.
  `logo.jpeg` is a low-resolution screenshot with a search-tool watermark, so it
  is unusable as a shipped asset; the mark has to be redrawn as vector.
- Calibration reference (quality bar, not a style to copy):
  `~/Documents/GitHub/avocados/avocado_dashboard`.
- No testimonials, customers, benchmarks, usage numbers or accuracy claims
  exist. The landing page's only honest proof is the dataset's own scale and the
  tool itself.

## Product Principles

1. **The numbers are the notebook's; the presentation is ours.** Never alter,
   re-derive or second-guess an analytical result.
2. **Refuse rather than fudge.** A prediction that cannot be made honestly is
   not made. Name what is missing and say so on screen.
3. **State the baseline.** Weekday effects are meaningless without "relative to
   Monday" attached; every table, chart and sentence carries it.
4. **Every control has a visible consequence.** No decorative filters.
5. **Never a blank.** An empty filter result, a missing optional file and a dead
   network each get a designed, explanatory state.
6. **Premium through precision.** This is a planner's instrument; it earns
   "impressive" through scannability, typographic rhythm and exact detail, not
   ornament.

## Accessibility & Inclusion

No formal standard specified. Treat as binding: colour is never the only
encoding (the VIF severity bands and every categorical series carry a label or
shape as well), contrast is legible on whichever ground the chosen visual world
uses, controls are keyboard-reachable and focus is visible, and charts stay
readable at mobile widths.
