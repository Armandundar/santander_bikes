"""Dashboard components. Structure only — no analysis, no figure building."""

from __future__ import annotations

import pandas as pd
from dash import dcc, html

from data_loader import DAY_ORDER, WEATHER_CHOICES, dataset_span
from theme import VARIANTS

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


def switcher(variant: str) -> html.Div:
    """Development-only: pick a visual world by looking at it."""
    return html.Div(
        [
            html.Span("Design", className="switcher-label"),
            html.Div(
                [
                    html.Button(v["label"], id={"role": "variant", "name": key},
                                n_clicks=0, title=v["blurb"],
                                className="is-on" if key == variant else "")
                    for key, v in VARIANTS.items()
                ],
                className="seg",
            ),
        ],
        className="switcher",
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
                        html.P(f"{span['rows']:,} days of hires and weather, "
                               f"{span['first']:%B %Y} to {span['last']:%B %Y}."),
                    ]),
                    chip("Static dataset", "static"),
                ],
                className="hero",
            ),
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
                className="titlerow",
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
