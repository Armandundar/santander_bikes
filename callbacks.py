"""Wiring: controls -> filtered data -> figures. No analysis lives here."""

from __future__ import annotations

import pandas as pd
from dash import ALL, Input, Output, State, callback, html

import figures as F
from data_loader import load_bikes
from layout import tile


def filtered(start, end, seasons, days) -> pd.DataFrame:
    """Apply the global filters. Existing columns only."""
    bike = load_bikes()
    if start:
        bike = bike[bike["date"] >= pd.to_datetime(start)]
    if end:
        bike = bike[bike["date"] <= pd.to_datetime(end)]
    if seasons:
        bike = bike[bike["season_name"].isin(seasons)]
    if days:
        bike = bike[bike["day_of_week"].isin(days)]
    return bike


def register(app):
    @callback(
        Output("status-strip", "children"),
        Output("fig-scatter", "figure"),
        Output("fig-dow", "figure"),
        Output("fig-month", "figure"),
        Output("fig-series", "figure"),
        Output("fig-heat", "figure"),
        Input("weather-var", "value"),
        Input("colour-by", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("season", "value"),
        Input("days", "value"),
    )
    def redraw(weather_var, colour_by, start, end, seasons, days):
        bike = filtered(start, end, seasons, days)
        return (
            _strip(bike),
            F.scatter_weather(bike, weather_var, colour_by),
            F.bar_day_of_week(bike),
            F.month_profile(bike),
            F.daily_series(bike),
            F.correlation_heatmap(bike),
        )


def _strip(bike: pd.DataFrame) -> list:
    """Four tiles describing the filtered window, each against a reference."""
    if bike.empty:
        return [html.Div(
            [html.Div("No days in view", className="tile-label"),
             html.Div("—", className="tile-value num"),
             html.Div("Widen the date range, or clear a season or day filter.",
                      className="tile-foot")],
            className="tile", style={"gridColumn": "1 / -1"})]

    total_days = len(load_bikes())
    busiest = bike.loc[bike["bikes_hired"].idxmax()]
    quietest = bike.loc[bike["bikes_hired"].idxmin()]
    return [
        tile("Days in view", f"{len(bike):,}",
             f"of {total_days:,} in the dataset"),
        tile("Mean daily hires", f"{bike['bikes_hired'].mean():,.0f}",
             f"median {bike['bikes_hired'].median():,.0f}"),
        tile("Busiest day", f"{busiest['bikes_hired']:,.0f}",
             f"{busiest['date']:%a %-d %b %Y} · {busiest['temp']:.1f}°C"),
        tile("Quietest day", f"{quietest['bikes_hired']:,.0f}",
             f"{quietest['date']:%a %-d %b %Y} · {quietest['temp']:.1f}°C"),
    ]


def register_predict(app):
    """Fill the two forecast sections. Kept out of the page render so a slow or
    dead network cannot stop the rest of the page from appearing."""
    from dash import dcc

    import layout as L
    from model import load_model, numeric_sources
    from weather import get_weather

    @callback(
        Output("jan-2026", "children"),
        Output("jan-2026-chip", "children"),
        Output("next-five", "children"),
        Output("next-five-chip", "children"),
        Input("retry-store", "data"),
    )
    def fill(retry):
        model = load_model()
        sources = numeric_sources()
        out = []
        for kind, label in (("history", "Archive"), ("forecast", "Live forecast")):
            result = get_weather(kind, retry or 0)
            if not result.ok:
                out += [
                    L.notice(
                        "Weather unavailable", result.error or "No weather returned.",
                        action=html.Button("Try again", id={"role": "retry", "kind": kind},
                                           n_clicks=0, className="btn"),
                    ),
                    L.chip("Offline", "alert"),
                ]
                continue
            pred = result.df.copy()
            pred["predicted"] = model.predict(pred)
            out += [
                html.Div([
                    dcc.Graph(figure=F.forecast_bars(pred),
                              config={"displayModeBar": False, "responsive": True},
                              style={"height": "300px"}),
                    L.weather_table(pred, sources),
                ]),
                L.chip(label, "live"),
            ]
        return out[0], out[1], out[2], out[3]

    @callback(
        Output("retry-store", "data"),
        Input({"role": "retry", "kind": ALL}, "n_clicks"),
        State("retry-store", "data"),
        prevent_initial_call=True,
    )
    def retry(clicks, current):
        if not any(c or 0 for c in (clicks or [])):
            return current or 0
        return (current or 0) + 1
