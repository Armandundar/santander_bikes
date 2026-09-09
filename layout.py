"""Dashboard components. Structure only — no analysis, no figure building."""

from __future__ import annotations

import pandas as pd
from dash import dcc, html

from data_loader import DAY_ORDER, WEATHER_CHOICES, dataset_span
from model import BASELINE_DAY as BASELINE, vif_band

SEASONS = ["Winter", "Spring", "Summer", "Autumn"]


def chip(text: str, kind: str = "static") -> html.Span:
    """A status chip. The word carries the state; colour only reinforces it."""
    return html.Span(
        [html.Span(className="chip-dot"), text],
        className=f"chip is-{kind}",
    )


def rail(active: str, span: dict) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Img(src="/assets/mark.svg", className="rail-mark",
                             width=26, height=26, alt=""),
                    html.Div([
                        html.Div("Cycle Demand", className="rail-word"),
                        html.Div("Santander Cycles · London", className="rail-sub"),
                    ]),
                ],
                className="rail-brand",
            ),
            html.Div("Dashboard", className="rail-group"),
            dcc.Link(
                [html.Span(className="ic ic-explore"), "Explore the data"],
                href="/app", className=f"rail-link{' is-active' if active == 'explore' else ''}",
            ),
            dcc.Link(
                [html.Span(className="ic ic-predict"), "Predict"],
                href="/app/predict", className=f"rail-link{' is-active' if active == 'predict' else ''}",
            ),
            html.Div(
                [
                    html.Div([html.B(f"{span['rows']:,}"), " daily records"]),
                    html.Div(f"{span['first']:%b %Y} – {span['last']:%b %Y}"),
                    html.Div("Independent student project. Not affiliated "
                             "with Santander or Transport for London.",
                             style={"marginTop": "9px", "opacity": 0.8}),
                ],
                className="rail-foot",
            ),
        ],
        className="rail",
    )


def tile(label: str, value: str, foot: str) -> html.Div:
    return html.Div(
        [
            html.Div(label, className="tile-label"),
            html.Div(value, className="tile-value num"),
            html.Div(foot, className="tile-foot"),
        ],
        className="tile",
    )


def controls(bike: pd.DataFrame) -> html.Div:
    span = dataset_span(bike)
    return html.Div(
        [
            html.Div(
                [
                    html.Label("Weather variable", htmlFor="weather-var"),
                    dcc.Dropdown(
                        id="weather-var", clearable=False,
                        value="temp",
                        options=[{"label": v, "value": k}
                                 for k, v in WEATHER_CHOICES.items()],
                    ),
                ],
                className="field",
            ),
            html.Div(
                [
                    html.Label("Colour by", htmlFor="colour-by"),
                    dcc.Dropdown(
                        id="colour-by", clearable=False, value="weekend",
                        options=[{"label": "Weekend vs weekday", "value": "weekend"},
                                 {"label": "Season", "value": "season_name"}],
                    ),
                ],
                className="field",
            ),
            html.Div(
                [
                    html.Label("Date range", htmlFor="date-range"),
                    dcc.DatePickerRange(
                        id="date-range",
                        min_date_allowed=span["first"], max_date_allowed=span["last"],
                        start_date=span["first"], end_date=span["last"],
                        display_format="D MMM YYYY", first_day_of_week=1,
                    ),
                ],
                className="field",
            ),
            html.Div(
                [
                    html.Label("Season", htmlFor="season"),
                    dcc.Dropdown(id="season", multi=True, placeholder="All seasons",
                                 options=[{"label": s, "value": s} for s in SEASONS]),
                ],
                className="field",
            ),
            html.Div(
                [
                    html.Label("Day of week", htmlFor="days"),
                    dcc.Dropdown(id="days", multi=True, placeholder="All days",
                                 options=[{"label": d, "value": d} for d in DAY_ORDER]),
                ],
                className="field",
            ),
        ],
        className="controls",
    )


def card(title: str, note: str | None, body, right=None) -> html.Div:
    # The roundel marker is always in the markup and shown by one world only.
    head = [html.H2([html.Span(className="roundel-mark"), title])]
    if right is not None:
        head.append(right)
    children = [html.Div(head, className="card-head")]
    if note:
        children.append(html.P(note, className="card-note"))
    children.append(body)
    return html.Div(children, className="card")


def graph(fig_id: str, height: int) -> dcc.Graph:
    return dcc.Graph(
        id=fig_id, config={"displayModeBar": False, "responsive": True},
        style={"height": f"{height}px"},
    )


def explore_page(bike: pd.DataFrame) -> html.Div:
    span = dataset_span(bike)
    return html.Div(
        [
            html.Div(
                [
                    html.Div([
                        html.H1("Explore the data"),
                        html.P(f"Every daily hire on the scheme from "
                               f"{span['first']:%-d %B %Y} to {span['last']:%-d %B %Y}, "
                               f"against the weather that day. Filters apply to "
                               f"every figure at once."),
                    ]),
                    chip("Static dataset", "static"),
                ],
                className="hero",
            ),
            html.Div(id="status-strip", className="grid grid-4",
                     style={"marginBottom": "14px"}),
            html.Div(
                [
                    card("Filters", None, controls(bike)),
                    card("Hires against weather",
                         "One dot is one day. The colour split is also a marker "
                         "shape, so it survives a greyscale print.",
                         graph("fig-scatter", 380)),
                    html.Div(
                        [
                            card("Average hires by day of week",
                                 "Weekend bars are hatched as well as red.",
                                 graph("fig-dow", 300)),
                            card("Average hires by month", None,
                                 graph("fig-month", 300)),
                        ],
                        className="grid grid-2",
                    ),
                    card("Daily hires over the window", None, graph("fig-series", 260)),
                    card("What the weather variables share",
                         "Correlation across the window. The bracketed square is "
                         "why temperature, feels-like, max, min and dew point "
                         "cannot all enter one model.",
                         graph("fig-heat", 470)),
                ],
                className="stack",
            ),
        ],
        className="enter",
    )


# --- Predict tab -----------------------------------------------------------

def table(headers: list, rows: list[list], *, right_from: int = 1,
          row_classes: list[str] | None = None, narrow: bool = False) -> html.Div:
    """A plain semantic table in its own scroll container.

    The wrapper is not decoration: a wide table's min-content width cannot
    shrink, so without it the table widens the whole page on a phone instead of
    scrolling inside its card. `right_from` is the first column to right-align,
    since every column from there on holds figures.
    """
    row_classes = row_classes or [""] * len(rows)
    inner = html.Table(
        [
            html.Thead(html.Tr([
                html.Th(h, className="tbl-num" if i >= right_from else "")
                for i, h in enumerate(headers)
            ])),
            html.Tbody([
                html.Tr(
                    [html.Td(c, className="tbl-num num" if i >= right_from else "")
                     for i, c in enumerate(row)],
                    className=cls,
                )
                for row, cls in zip(rows, row_classes)
            ]),
        ],
        className="tbl",
    )
    return html.Div(inner, className="tbl-wrap" + (" is-narrow" if narrow else ""),
                    tabIndex="0")


def notice(title: str, body: str, action=None, kind: str = "alert") -> html.Div:
    """The designed stand-in for a section that cannot be drawn: a dead network,
    a model the weather feed cannot serve, an unreadable file."""
    return html.Div(
        [
            html.Div([html.Span(className="chip-dot"), title], className=f"chip is-{kind}"),
            html.P(body, className="notice-body"),
            action if action is not None else html.Span(),
        ],
        className="notice",
    )


def weather_table(pred: pd.DataFrame, sources: dict) -> html.Div:
    """Each predicted day beside the weather values that produced it."""
    headers = ["Day", "Date", "Temp °C", "Humidity %", "Rain mm",
               "Wind km/h", "Sun W/m²", "Predicted hires"]
    rows, classes = [], []
    for _, r in pred.iterrows():
        rows.append([
            r["day_of_week"], f"{r['date']:%-d %b %Y}",
            f"{r['temp']:.1f}", f"{r['humidity']:.0f}", f"{r['precip']:.1f}",
            f"{r['windspeed']:.1f}", f"{r['solarradiation']:.0f}",
            f"{r['predicted']:,.0f}",
        ])
        classes.append("is-weekend" if r["day_of_week"] in ("Sat", "Sun") else "")
    return table(headers, rows, right_from=2, row_classes=classes)


def coefficient_block(m, sources: dict) -> html.Div:
    """The model in words, then the weekday effects, always against Monday."""
    day_rows = [
        [d, "baseline" if d == BASELINE else f"{m.days[d]:+,.0f}"]
        for d in DAY_ORDER
    ]
    return html.Div(
        [
            html.Ul([html.Li(s) for _, _, s in m.sentences()], className="plain-list"),
            html.P("Each effect holds the others fixed. Weekday effects are read "
                   "against Monday, which is the baseline at zero.",
                   className="card-note"),
            table(["Day", "Effect vs Monday"], day_rows, narrow=True,
                  row_classes=["is-baseline" if d == BASELINE else "" for d in DAY_ORDER]),
        ]
    )


def fit_block(fit) -> html.Div:
    """The candidate comparison, exactly as the notebook ranked it."""
    final = fit[fit["is_final"].astype(str).str.lower() == "true"]

    def num(value, spec: str) -> str:
        """A blank cell reads as an em dash. Not every model has every measure:
        a boosted tree has no adjusted R² or residual SE to report."""
        if pd.isna(value) or str(value).strip() == "":
            return "—"
        return format(float(value), spec)

    optional = [c for c in ("cv_rmse", "forecast_rmse_2025") if c in fit.columns]
    titles = {"cv_rmse": "5-fold CV RMSE", "forecast_rmse_2025": "2025 forecast RMSE"}
    headers = (["Model", "Predictors", "Days fitted", "Adj R²", "Residual SE"]
               + [titles[c] for c in optional])

    rows, classes = [], []
    for _, r in fit.iterrows():
        is_final = str(r["is_final"]).lower() == "true"
        name = [r["model"], html.Span("final", className="pill")] if is_final else r["model"]
        formula = str(r.get("formula", "")).replace("bikes_hired ~ ", "")
        row = [name, html.Span(formula, className="wrap-cell"), f"{int(r['n_obs']):,}",
               num(r["adj_r_squared"], ".3f"), num(r["residual_se"], ",.0f")]
        row += [num(r[c], ",.0f") for c in optional]
        rows.append(row)
        classes.append("is-final" if is_final else "")

    words = html.Span()
    if not final.empty:
        f = final.iloc[0]
        words = html.P(
            [f"The chosen model explains ",
             html.B(f"{float(f['adj_r_squared']) * 100:.1f}%"),
             " of the day-to-day variation, and a typical day's miss is about ",
             html.B(f"{float(f['residual_se']):,.0f} hires"),
             f". It was fitted on {int(f['n_obs']):,} days."],
            className="card-note", style={"marginTop": "14px", "marginBottom": 0},
        )
    extra = html.Span()
    if fit["model"].astype(str).str.contains("XGBoost", case=False).any():
        extra = html.P(
            "The last row is a different kind of model, scored on the same two "
            "tests. It forecasts 2025 about 4% better and was still not chosen: "
            "it has no coefficients to read, no residual checks, and no "
            "two-column file a dashboard can apply. That was the notebook's "
            "call, recorded here rather than re-argued.",
            className="card-note", style={"marginTop": "10px", "marginBottom": 0})
    return html.Div([table(headers, rows, right_from=2, row_classes=classes),
                     words, extra])


def vif_block(vif) -> html.Div:
    """VIF exactly as exported. Severity is a colour and a written word."""
    stages = [s for s in ("before", "after") if s in set(vif.get("stage", []))]
    if not stages:
        stages = [None]

    def one(stage):
        part = vif if stage is None else vif[vif["stage"] == stage]
        rows, classes = [], []
        for _, r in part.iterrows():
            key, label = vif_band(float(r["vif"]))
            rows.append([r["feature"], f"{float(r['vif']):,.2f}",
                         html.Span(label, className=f"band band-{key}")])
            classes.append("")
        title = {"before": "Before — with feels-like alongside temperature",
                 "after": "After — the final model"}.get(stage, "Variance inflation")
        return html.Div([html.H3(title, className="sub"),
                         table(["Predictor", "VIF", "Reading"], rows, right_from=1,
                               narrow=True)])

    return html.Div(
        [
            html.Div([one(s) for s in stages],
                     className="grid grid-2" if len(stages) > 1 else "stack"),
            html.P("Rule of thumb: under 5 is fine, 5 to 10 a warning, above 10 "
                   "serious. Values are shown exactly as the notebook exported them.",
                   className="card-note", style={"marginTop": "14px", "marginBottom": 0}),
        ]
    )


def predict_page(m, fit, vif, sources: dict) -> html.Div:
    blocks = [
        html.Div(
            [
                html.Div([
                    html.H1("Predict"),
                    html.P("The notebook's model applied to real Open-Meteo weather. "
                           "These are point predictions: the coefficients file carries "
                           "no standard errors, so the app cannot draw a prediction "
                           "interval and does not pretend to."),
                ]),
                chip("Point predictions", "static"),
            ],
            className="hero",
        ),
    ]

    if not m.ok:
        blocks.append(card("The model could not be read", None,
                           notice("Cannot predict", m.error)))
        return html.Div([blocks[0], html.Div(blocks[1:], className="stack")],
                        className="enter")

    if not m.can_forecast:
        terms = ", ".join(f"“{t}”" for t in m.unforecastable)
        blocks.append(card(
            "This model cannot be forecast", None,
            notice("Missing predictor",
                   f"The coefficients file names {terms}, which Open-Meteo does not "
                   f"supply. Rather than drop the term or substitute a zero — either "
                   f"would produce a confidently wrong number — no prediction is made. "
                   f"Re-export the model using predictors the weather feed provides.")))
    else:
        blocks += [
            card("First week of January 2026",
                 "Open-Meteo's historical archive: that week has already happened, "
                 "but it is outside the data the model was fitted on.",
                 html.Div(id="jan-2026"), right=html.Span(id="jan-2026-chip")),
            card("The next five days",
                 "Open-Meteo's live forecast, fetched when this page loaded.",
                 html.Div(id="next-five"), right=html.Span(id="next-five-chip")),
        ]

    blocks.append(card("What the model says", None, coefficient_block(m, sources)))

    if fit is not None:
        blocks.append(card("How this model was chosen",
                           "Every candidate the notebook fitted. The ranking is the "
                           "notebook's own and is reproduced, not recomputed.",
                           fit_block(fit)))
    if vif is not None:
        blocks.append(card("Collinearity check",
                           "How much each predictor is explained by the others.",
                           vif_block(vif)))

    return html.Div([blocks[0], html.Div(blocks[1:], className="stack")],
                    className="enter")
