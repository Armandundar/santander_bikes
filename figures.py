"""Plotly figure builders. Every one takes a DataFrame and returns a Figure.

Nothing here computes a statistic the dataset does not already contain: these
are means, counts and correlations of existing columns. The model lives in
model.py and never enters this module.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from data_loader import DAY_ORDER, MONTH_ORDER, WEATHER_CHOICES
from theme import DIVERGING, SERIES, TOKENS, template

# The five near-duplicate temperature measures Part 1 of the notebook points at.
TEMP_BLOCK = ["temp", "feelslike", "tempmax", "tempmin", "dew"]
# Heatmap order: the target, then the temperature block kept contiguous, then
# the rest. Ordering is what makes the block read as a block.
HEATMAP_ORDER = ["bikes_hired", *TEMP_BLOCK,
                 "humidity", "cloudcover", "precip", "windspeed", "sealevelpressure"]

PRETTY = {
    "bikes_hired": "Hires", "temp": "Temp", "feelslike": "Feels like",
    "tempmax": "Temp max", "tempmin": "Temp min", "dew": "Dew point",
    "humidity": "Humidity", "cloudcover": "Cloud", "precip": "Precip",
    "windspeed": "Wind", "sealevelpressure": "Pressure",
}


def _base(height: int = 340) -> dict:
    return dict(template=template(), height=height)


def empty_state(message: str, height: int = 340) -> go.Figure:
    """Shown instead of a blank chart when a filter combination has no rows."""
    t = TOKENS
    fig = go.Figure()
    fig.update_layout(**_base(height))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(
        text=message, showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5,
        font=dict(size=13.5, color=t["ink_soft"]), align="center",
    )
    return fig


def scatter_weather(bike: pd.DataFrame, xcol: str, colour_by: str,
                    height: int = 380) -> go.Figure:
    """Daily hires against one weather variable, coloured by weekend or season."""
    if bike.empty:
        return empty_state("No days match these filters.<br>"
                                    "Widen the date range or add a season.", height)
    t = TOKENS
    fig = go.Figure()
    label = WEATHER_CHOICES.get(xcol, xcol)

    if colour_by == "weekend":
        groups = [("Weekday", bike[~bike["weekend"]], SERIES[0], "circle"),
                  ("Weekend", bike[bike["weekend"]], t["accent"], "diamond")]
    else:
        order = ["Winter", "Spring", "Summer", "Autumn"]
        marks = ["circle", "diamond", "square", "triangle-up"]
        groups = [(s, bike[bike["season_name"] == s], SERIES[i], marks[i])
                  for i, s in enumerate(order)]

    for name, part, colour, symbol in groups:
        if part.empty:
            continue
        fig.add_trace(go.Scattergl(
            x=part[xcol], y=part["bikes_hired"], mode="markers", name=name,
            marker=dict(color=colour, size=5.5, symbol=symbol,
                        opacity=0.55, line=dict(width=0)),
            customdata=part[["date", "day_of_week"]].astype(str),
            hovertemplate=("%{customdata[1]} %{customdata[0]}<br>"
                           f"{label}: %{{x}}<br>Hires: %{{y:,.0f}}<extra>{name}</extra>"),
        ))

    fig.update_layout(**_base(height))
    fig.update_xaxes(title_text=label)
    fig.update_yaxes(title_text="Daily hires", tickformat=",")
    return fig


def bar_day_of_week(bike: pd.DataFrame, height: int = 300) -> go.Figure:
    """Average hires by day of week — the assignment's required bar chart."""
    if bike.empty:
        return empty_state("No days match these filters.", height)
    t = TOKENS
    means = (bike.groupby("day_of_week", observed=False)["bikes_hired"]
             .mean().reindex(DAY_ORDER))
    counts = (bike.groupby("day_of_week", observed=False)["bikes_hired"]
              .size().reindex(DAY_ORDER))
    # Weekend bars carry the accent *and* a hatch, so the split never rests on
    # colour alone.
    colours = [t["accent"] if d in ("Sat", "Sun") else SERIES[0] for d in DAY_ORDER]
    patterns = ["/" if d in ("Sat", "Sun") else "" for d in DAY_ORDER]

    fig = go.Figure(go.Bar(
        x=DAY_ORDER, y=means.values,
        marker=dict(color=colours,
                    pattern=dict(shape=patterns, size=7, solidity=0.32,
                                 bgcolor=colours, fgcolor="#FFFFFF")),
        customdata=counts.values,
        hovertemplate="%{x}<br>Mean hires: %{y:,.0f}<br>%{customdata:,} days<extra></extra>",
    ))
    fig.update_layout(**_base(height), bargap=0.32)
    fig.update_yaxes(title_text="Mean daily hires", tickformat=",")
    fig.update_xaxes(title_text="")
    return fig


def daily_series(bike: pd.DataFrame, height: int = 260) -> go.Figure:
    """Daily hires over the filtered window."""
    if bike.empty:
        return empty_state("No days match these filters.", height)
    t = TOKENS
    d = bike.sort_values("date")
    fig = go.Figure(go.Scattergl(
        x=d["date"], y=d["bikes_hired"], mode="lines",
        line=dict(color=SERIES[0], width=1),
        hovertemplate="%{x|%a %d %b %Y}<br>%{y:,.0f} hires<extra></extra>",
    ))
    fig.update_layout(**_base(height))
    fig.update_yaxes(title_text="Daily hires", tickformat=",")
    fig.update_xaxes(title_text="")
    return fig


def month_profile(bike: pd.DataFrame, height: int = 260) -> go.Figure:
    """Mean hires by calendar month, in the notebook's Jan→Dec order."""
    if bike.empty:
        return empty_state("No days match these filters.", height)
    t = TOKENS
    means = (bike.groupby("month_name", observed=False)["bikes_hired"]
             .mean().reindex(MONTH_ORDER))
    fig = go.Figure(go.Bar(
        x=MONTH_ORDER, y=means.values, marker_color=SERIES[0],
        hovertemplate="%{x}<br>Mean hires: %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(**_base(height), bargap=0.3)
    fig.update_yaxes(title_text="Mean daily hires", tickformat=",")
    fig.update_xaxes(title_text="")
    return fig


def correlation_heatmap(bike: pd.DataFrame, height: int = 460) -> go.Figure:
    """Part 1's correlation matrix, ordered so the temperature block is one
    contiguous, bracketed square rather than five numbers scattered in a grid."""
    if len(bike) < 2:
        return empty_state("Not enough days to compute correlations.", height)
    t = TOKENS
    cols = [c for c in HEATMAP_ORDER if c in bike.columns]
    corr = bike[cols].corr().round(2)
    labels = [PRETTY.get(c, c) for c in cols]

    fig = go.Figure(go.Heatmap(
        z=corr.values, x=labels, y=labels,
        colorscale=[[i / 4, c] for i, c in enumerate(DIVERGING)],
        zmid=0, zmin=-1, zmax=1,
        text=corr.values, texttemplate="%{text:.2f}",
        textfont=dict(size=10.5),
        hovertemplate="%{y} vs %{x}<br>r = %{z:.2f}<extra></extra>",
        colorbar=dict(thickness=10, outlinewidth=0, len=0.72,
                      tickfont=dict(size=11, color=t["ink_soft"]),
                      title=dict(text="r", font=dict(size=11.5, color=t["ink_soft"]))),
    ))

    # Bracket the temperature block in place. Cells are 1 wide, so the block
    # spans from index-0.5 to index+0.5 on both axes.
    idx = [cols.index(c) for c in TEMP_BLOCK if c in cols]
    if idx:
        lo, hi = min(idx) - 0.5, max(idx) + 0.5
        fig.add_shape(type="rect", x0=lo, x1=hi, y0=lo, y1=hi,
                      line=dict(color=t["ink"], width=2), fillcolor="rgba(0,0,0,0)",
                      layer="above")
        fig.add_annotation(
            x=(lo + hi) / 2, xref="x", y=1.0, yref="paper", yanchor="bottom",
            showarrow=False,
            text="five measures of the same thing · r = 0.83 to 0.99",
            font=dict(size=11.5, color=t["ink"]),
        )

    fig.update_layout(**_base(height), margin=dict(l=90, r=20, t=44, b=90))
    fig.update_xaxes(tickangle=-45, showgrid=False, ticks="")
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="")
    return fig


def forecast_bars(pred: pd.DataFrame, height: int = 300) -> go.Figure:
    """Predicted hires per day. Weekend bars carry the accent and a hatch, the
    same encoding the day-of-week chart uses, so the two read together."""
    if pred.empty:
        return empty_state("No days to predict.", height)
    t = TOKENS
    weekend = pred["day_of_week"].isin(["Sat", "Sun"])
    colours = [t["accent"] if w else SERIES[0] for w in weekend]
    shapes = ["/" if w else "" for w in weekend]
    labels = [f"{d}<br>{dt:%-d %b}" for d, dt in zip(pred["day_of_week"], pred["date"])]

    fig = go.Figure(go.Bar(
        x=labels, y=pred["predicted"],
        marker=dict(color=colours,
                    pattern=dict(shape=shapes, size=7, solidity=0.32,
                                 bgcolor=colours, fgcolor="#FFFFFF")),
        text=[f"{v:,.0f}" for v in pred["predicted"]],
        textposition="outside", textfont=dict(size=12, color=t["ink"]),
        cliponaxis=False,
        customdata=pred[["temp", "precip", "windspeed"]].round(1),
        hovertemplate=("%{x}<br>Predicted %{y:,.0f} hires<br>"
                       "%{customdata[0]}°C · %{customdata[1]} mm · "
                       "%{customdata[2]} km/h<extra></extra>"),
    ))
    fig.update_layout(**_base(height), bargap=0.36)
    # Headroom so the outside value labels are not clipped by the plot edge.
    fig.update_yaxes(title_text="Predicted hires", tickformat=",",
                     range=[0, float(pred["predicted"].max()) * 1.18])
    fig.update_xaxes(title_text="")
    return fig
