# London Santander Cycles — Action Plan

An interactive Dash app that explains and forecasts daily hires on London's
Santander Cycles scheme. **Python 3.12 + pandas + Plotly + Dash**, environment
managed with **uv**, deployed free on **Render**.

> **Scope rule:** every statistical decision — the chosen model, its variables,
> its coefficients, the VIF work, the diagnostics — is owned by
> `~/Code/am01/session10/bikes_assignment.ipynb` and is frozen. This project
> decides only **how results are visualised and arranged**. The app never fits,
> re-fits or invents a model, and no coefficient value is ever hard-coded in
> Python.

---

## 0. Facts verified against the real sources (not assumed)

**Dataset** (`london_bikes.csv`, fetched and inspected):

- Raw: 5,634 rows, 40 columns, starting **2010-07-30**.
- After Part 0's cleaning: **4,383 rows, 2014-01-01 → 2025-12-31**.
- `date` is ISO-8601 with a `Z` suffix, so `pd.to_datetime` returns a
  **tz-aware UTC** series — which is why Part 0 compares against
  `pd.to_datetime('2014-01-01', utc=True)`. We mirror that comparison exactly.
- Zero nulls in `bikes_hired`, `temp`, `humidity`, `precip`, `windspeed`,
  `cloudcover`, `day_of_week`, `season_name`.
- `bikes_hired`: mean ≈ 27,580, min 0, max 73,094. (A handful of genuine zero
  days exist. The notebook does not drop them, so neither do we.)
- Seasons present: Winter, Spring, Summer, Autumn.
- **No station / borough / postcode / coordinate column** → no map, no
  per-station view.
- **January 2026 is outside the data** (it ends 2025-12-31), so the required
  first-week-of-January-2026 prediction is genuinely out of sample.

**The collinearity story is real** (correlations on the post-2014 data):

|  | temp | feelslike | tempmax | tempmin | dew |
|---|---|---|---|---|---|
| **temp** | 1.00 | **0.99** | **0.97** | **0.96** | **0.90** |
| **bikes_hired** | 0.60 | 0.60 | 0.65 | 0.49 | 0.45 |

That five-variable block is what Part 1 is pointing at. The heatmap has to make
it *visible as a block*, not bury it in an undifferentiated grid.

**Notebook status:** Part 0 and Part 1 are complete. **Parts 2, 3, 4 and 5 are
empty scaffolds** — there is no final model yet, and therefore no real
`model_coefficients.csv`, `model_fit.csv` or `model_vif.csv`. We build against a
clearly-labelled placeholder and swap on delivery.

**Weather helper** (`open_meteo.py`, copied in unchanged) returns exactly:
`date, day_of_week, temp, humidity, precip, windspeed, cloudcover`. Wind in
km/h, temp in °C, precip in mm — matching the training data's units.

---

## 1. The contract: `model_coefficients.csv`

Two columns, `term` and `coefficient`:

```
Intercept, <one row per numeric predictor>, day_Mon, day_Tue, … day_Sun
```

Prediction for a day = `Intercept + Σ(coefficient × value)` over the numeric
terms, **plus** that day's `day_<weekday>` coefficient.

Three rules the app enforces at load:

1. **Numeric terms are read from the file**, never listed in Python — so a
   different final variable set just works.
2. **`day_Mon` is the baseline at 0.0.** Every weekday number is
   *relative to Monday* and every label says so.
3. **Predictor guard.** Open-Meteo supplies only
   `{temp, humidity, precip, windspeed, cloudcover}`. If the file names a
   numeric term outside that set, the Predict tab renders a designed error
   naming the offending term and makes no forecast. It never drops the term and
   never substitutes 0. (Explore is unaffected and still works.)

No standard errors and no residual scale are in the file, so **no prediction
intervals, no confidence bands** — point predictions, labelled as such.

### Optional companions (§3a of the brief)

| file | what we render | if absent |
|---|---|---|
| `model_fit.csv` | comparison table of every candidate model, final row visibly marked; final model's `adj_r_squared` and `residual_se` restated in plain words ("a typical day's miss: ±N hires") | section hidden entirely |
| `model_vif.csv` | VIF per predictor; one table if only `after` rows, side-by-side if `before` **and** `after`; bands <5 fine / 5–10 warning / >10 serious, shown as **colour + written label** | section hidden entirely |

VIF values are displayed **exactly as exported**. *(Corrected once the
notebook was finished: it computes VIF **with** `sm.add_constant`, so the final
model's values are small — 1.05 to 2.60. The three-figure values are real but
they belong to the `before` stage, the deliberate `temp + feelslike` demo at
99.22 and 95.96.)* We do not recompute, rescale, cap or log them, and we do not
caption them as errors. **A linear bar chart cannot show 99 next to 1.05**, so
the layout is a table: numeric column plus a severity chip carrying both a
colour and the written word.

---

## 2. Routes and sections

### `/` — landing page

Presentation only. No new analytical content; any figure on it is drawn from the
same loaded CSV and the same `model_coefficients.csv` as the dashboard. Carries
the design language. Lean.

Content: a one-line statement of what the tool answers; the dataset's own scale
computed at runtime (row count, first and last date, years covered); the two
things it does (explain / forecast) as two plain cards; one small live figure
pulled from the real data; and the entry control into `/app`, which triggers the
themed loading state.

### `/app` — the dashboard

#### Tab 1 — Explore the data

Required:
- **Weather-variable dropdown** (temperature, humidity, precipitation, wind,
  cloud) → scatter of daily `bikes_hired` against it.
- **Colour-by control**: `weekend` or `season_name`.
- **Bar chart: average hires by day of week.**
- Genuinely interactive — every control recomputes every figure.

Added (all simple aggregations of existing columns only):
- **Global filters:** date range, season, weekend/weekday, day of week. Existing
  columns only.
- **KPI row** for the filtered window: days in view, mean hires, busiest day
  (date + value), quietest day.
- **Daily-hires time series** over the filtered window.
- **Season / month profile** (mean hires by `month_name`, ordered Jan→Dec).
- **Correlation heatmap** (Part 1's variable list), designed so the
  temp/feelslike/tempmax/tempmin/dew block reads as a block — ordered so the
  block is contiguous, bracketed, and annotated with one line naming why those
  five cannot all enter one model.

Row count and date span shown anywhere are computed from the loaded CSV at
runtime. Never typed into source.

#### Tab 2 — Predict

- **First week of January 2026** (`open_meteo_history("London", "2026-01-01",
  "2026-01-07")`) — table **and** bar chart.
- **Next five days** (`open_meteo("London", 5)`) — table **and** bar chart.
- The **driving weather values shown alongside** each prediction (they arrive in
  the same DataFrame).
- **Coefficients in plain words**, read from the CSV: "one extra degree ≈ +N
  hires", weekday effects **relative to Monday**.
- **Model comparison** and **VIF** sections, if and only if those files exist.
- Nothing about the model that is not in one of those three files.

---

## 3. File structure (flat root, as the brief requires)

```
santander_bikes/            # github.com/Armandundar/santander_bikes
├── app.py                    # Dash app, dcc.Location routing, server = app.server
├── landing.py                # the / page
├── layout.py                 # dashboard shell, both tabs' components
├── callbacks.py              # controls -> data -> figures
├── figures.py                # Plotly figure builders (df in, go.Figure out)
├── theme.py                  # ONE Plotly template + the palette, defined once
├── data_loader.py            # load_bikes(): fetch + Part-0 cleaning, cached
├── model.py                  # read coefficients/fit/VIF; predict(); the guard
├── weather.py                # session cache + graceful failure around open_meteo
├── open_meteo.py             # copied in unchanged
├── model_coefficients.csv    # the contract (placeholder until the notebook lands)
├── model_fit.csv             # optional, from the notebook
├── model_vif.csv             # optional, from the notebook
├── assets/style.css          # theme (Dash auto-loads assets/)
├── pyproject.toml  uv.lock  render.yaml  .python-version  .gitignore
└── README.md                 # screenshot, live URL, local run
```

`model.py` is the only module that reads the three CSVs; nothing else knows
their shape.

---

## 4. Design direction — and the choice I want you to make by seeing it

Theme: London cycling as **transport infrastructure**. Santander red as the
anchor, roundel geometry, Johnston-flavoured humanist sans, tarmac neutrals,
wayfinding cues. Restrained and institutional.

Three visual worlds are genuinely different answers to that brief, so I will
**build all three as a switchable variant on one page** and you pick by looking:

- **A — Roundel.** Light signage. Off-white ground, the roundel's bar-and-circle
  as the structural device, strong horizontal rules, red used sparingly and
  exactly. Reads like a station diagram.
- **B — Night Ride.** Dark tarmac ground, high-contrast data, red as the one
  luminous accent, lane-marking rules as dividers. Reads like the scheme after
  dark.
- **C — Depot.** Utilitarian and engineered. Concrete greys, tabular/monospace
  numerals, hairline rules, a docking-bay grid. Reads like an operations
  console.

Typography (Johnston has no free equivalent, so this is also a look-at-it
choice): candidates are **Hanken Grotesk**, **Public Sans** and **Archivo** for
text, paired with a tabular-numeral face for the data columns. Shown in the same
variant switcher.

Shared regardless of which world wins: one Plotly template in `theme.py`
(fonts, grid, hover, margins, sequential + categorical palettes) used by every
figure; motion limited to the entry loader, tab cross-fade and hover feedback;
colour never the only encoding; visible keyboard focus.

---

## 5. Build order (one verifiable change at a time)

1. Repo, `.gitignore`, `pyproject.toml`, `uv.lock`, `open_meteo.py`, docs. ✅
2. `data_loader.py` — Part-0 cleaning mirrored, asserted against the numbers in
   §0.
3. `model.py` — coefficient reading, the predictor guard, `predict()`; plus the
   optional fit/VIF readers. Verified against a hand-computed row.
4. `theme.py` + `assets/style.css` — the design system, all three worlds
   switchable.
5. **Design review with you** → pick a world → delete the other two.
6. `landing.py`.
7. Tab 1 (Explore) — figures, then filters, then empty states.
8. `weather.py` + Tab 2 (Predict) — including the offline and guard-failure
   states, tested by simulating both.
9. `render.yaml`, `README.md`, screenshot.
10. Deploy (with your go-ahead).

Each step is run locally and checked by me before it is committed.

---

## 6. Decisions I have taken, and things I need from you

**Taken (say the word and I change them):**

1. **Working name "Cycle Demand"** in-app.
2. **Placeholder coefficients.** With Parts 2–5 empty there is no real model, so
   I will generate a placeholder `model_coefficients.csv` **offline** (never in
   the app) using the four forecastable predictors `temp, humidity, precip,
   windspeed` plus day-of-week, purely so magnitudes are realistic while I build
   layout. It is committed because the repo must contain the file, and it is
   labelled as a placeholder in the README until the notebook's real export
   replaces it.
3. **Placeholder `model_fit.csv` / `model_vif.csv` will NOT be committed.**
   Shipping invented fit statistics and VIFs in a public repo is a genuine
   misreading risk. I will generate them locally (gitignored) to build and test
   those sections, then they enter the repo only when the notebook exports the
   real ones. This also lets me verify the "files absent → sections hidden"
   path, which is the state the repo will actually be in.

**Needed from you:**

1. **Nothing has been pushed yet.** This repo already has the remote
   `github.com/Armandundar/santander_bikes`, so no repo creation is needed and
   `gh` is not required. Say the word and I push `main`; I will not push
   without your go-ahead. Confirm the repo is public before the Render deploy.
2. **Design world A / B / C** — but not now: I will build the switcher first so
   you choose by seeing, per step 5.
3. **Confirm the two decisions above** (name, and not committing placeholder
   fit/VIF).

**STOP — awaiting your approval before writing app code.**
