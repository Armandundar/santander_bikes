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

#: How each predictor's unit is said out loud on an axis tick.
UNIT_LABELS = {
    "temp": "°C", "humidity": "%", "precip": "mm",
    "windspeed": "km/h", "cloudcover": "% cloud", "solarradiation": "W/m²",
}

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
    """Daily hires against one weather variable, coloured by weekend or season.

    Plain SVG scatter, not Scattergl: the WebGL renderer draws nothing at all on
    a machine without it, and 4,383 markers do not need the GPU.
    """
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
        fig.add_trace(go.Scatter(
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
    fig = go.Figure(go.Scatter(
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


def coefficient_effects(effects: list[tuple[str, float, str]],
                        height: int = 230) -> go.Figure:
    """Each numeric coefficient as a diverging bar from zero.

    The axis is 'hires per one unit', and every tick names its own unit,
    because a degree, a millimetre and a W/m² are not comparable quantities.
    Sunshine looking small here is the honest reading: one extra W/m² really
    does very little, which is why it moved the fit by under one percent.
    """
    if not effects:
        return empty_state("No numeric predictors in the coefficients file.", height)
    t = TOKENS
    rows = sorted(effects, key=lambda e: e[1])
    labels = [f"{term} ({UNIT_LABELS.get(term, 'unit')})" for term, _, _ in rows]
    values = [coef for _, coef, _ in rows]
    colours = [SERIES[0] if v >= 0 else t["accent"] for v in values]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=colours),
        text=[f"{v:+,.0f}" for v in values],
        textposition="outside", cliponaxis=False,
        textfont=dict(size=12.5, color=t["ink"]),
        hovertemplate="%{y}<br>%{x:+,.1f} hires<extra></extra>",
    ))
    span = max(abs(min(values)), abs(max(values))) * 1.45
    fig.update_layout(**_base(height), bargap=0.4,
                      margin=dict(l=132, r=26, t=14, b=46))
    fig.update_xaxes(title_text="Hires per one unit increase", range=[-span, span],
                     zeroline=True, zerolinecolor=t["ink_soft"], zerolinewidth=1.5)
    fig.update_yaxes(title_text="", ticklen=0)
    return fig


def weekday_effects(days: dict[str, float], baseline: str = "Mon",
                    height: int = 230) -> go.Figure:
    """The weekly shape as bars either side of the Monday baseline."""
    t = TOKENS
    order = [d for d in DAY_ORDER if d in days][::-1]     # Monday at the top
    values = [days[d] for d in order]
    colours = [t["ink_soft"] if d == baseline
               else (SERIES[0] if days[d] >= 0 else t["accent"]) for d in order]
    labels = list(order)

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h", marker=dict(color=colours),
        text=[("0 · baseline" if d == baseline else f"{v:+,.0f}")
              for d, v in zip(order, values)],
        textposition="outside", cliponaxis=False,
        textfont=dict(size=12.5, color=t["ink"]),
        hovertemplate="%{y}<br>%{x:+,.0f} hires vs Monday<extra></extra>",
    ))
    span = (max(abs(v) for v in values) or 1) * 1.55
    fig.update_layout(**_base(height), bargap=0.34,
                      margin=dict(l=54, r=26, t=14, b=46))
    fig.update_xaxes(title_text="Hires relative to Monday", range=[-span, span],
                     zeroline=True, zerolinecolor=t["ink_soft"], zerolinewidth=1.5)
    fig.update_yaxes(title_text="", ticklen=0)
    return fig


def vif_chart(vif: pd.DataFrame, height: int = 300) -> go.Figure:
    """VIF on a logarithmic axis, with the notebook's thresholds as bands.

    The axis is logarithmic, not the values: every dot sits at its exported
    number and every number is printed beside it. That is the only way 99.22
    and 1.05 can share one chart without one of them becoming invisible.
    When both stages are present each predictor is a dumbbell, so the drop
    from dropping a collinear twin is the thing you see first.
    """
    if vif is None or vif.empty:
        return empty_state("No VIF values exported.", height)
    t = TOKENS
    has_stage = "stage" in vif.columns
    before = (vif[vif["stage"] == "before"].set_index("feature")["vif"].to_dict()
              if has_stage else {})
    after = (vif[vif["stage"] == "after"].set_index("feature")["vif"].to_dict()
             if has_stage else vif.set_index("feature")["vif"].to_dict())

    order = sorted(set(before) | set(after),
                   key=lambda f: before.get(f, after.get(f, 0)))
    # A predictor with a "before" and no "after" is one the notebook dropped;
    # say so on the axis rather than leaving a lone dot to be puzzled over.
    name_of = {f: (f"{f} — dropped" if f in before and f not in after else f)
               for f in order}
    order = [name_of[f] for f in order]
    before = {name_of[f]: v for f, v in before.items()}
    after = {name_of[f]: v for f, v in after.items()}
    fig = go.Figure()

    # Threshold bands: under 5 fine, 5-10 warning, above 10 serious.
    for x0, x1, colour in ((0.5, 5, "#F0FDF4"), (5, 10, "#FEFCE8"), (10, 400, "#FEF2F2")):
        fig.add_vrect(x0=x0, x1=x1, fillcolor=colour, layer="below", line_width=0)
    for x, label in ((5, "5"), (10, "10")):
        fig.add_vline(x=x, line=dict(color=t["rule"], width=1, dash="dot"))
        fig.add_annotation(x=_log(x), y=1.02, yref="paper", yanchor="bottom",
                           text=label, showarrow=False,
                           font=dict(size=11, color=t["ink_soft"]))

    # The connector, drawn first so the dots sit on top of it.
    for f in order:
        if f in before and f in after:
            fig.add_shape(type="line", x0=_log(before[f]), x1=_log(after[f]),
                          y0=f, y1=f, line=dict(color=t["ink_soft"], width=1.6))

    # Where the two stages nearly coincide the labels would sit on top of each
    # other, so one rides above the dot and the other below.
    if before:
        # Where a predictor barely moved, two numbers on top of each other read
        # as a smudge. Label the "after" dot only; the exact pair is in the
        # table below and in the hover.
        quiet = {f for f in order if f in before and f in after
                 and abs(before[f] - after[f]) / max(before[f], 1e-9) < 0.18}
        fig.add_trace(_vif_dots(before, order, "Before", t["accent"], "circle", t,
                                "top center", hide_text=quiet))
    fig.add_trace(_vif_dots(after, order, "After" if before else "Variance inflation",
                            SERIES[0], "diamond", t,
                            "bottom center" if before else "top center"))

    fig.update_layout(**_base(height), showlegend=bool(before),
                      margin=dict(l=112, r=30, t=34, b=52))
    # Plotly's log minor ticks read as a row of stray digits; name them instead.
    fig.update_xaxes(type="log", title_text="Variance inflation factor (log scale)",
                     range=[_log(0.55), _log(320)], showgrid=False,
                     tickmode="array", tickvals=[1, 2, 5, 10, 20, 50, 100, 200],
                     ticktext=["1", "2", "5", "10", "20", "50", "100", "200"],
                     minor=dict(ticks=""))
    fig.update_yaxes(title_text="", categoryorder="array", categoryarray=order)
    return fig


def _vif_dots(values: dict, order: list, name: str, colour: str, symbol: str,
              t: dict, textposition: str, hide_text: set | None = None) -> go.Scatter:
    hide_text = hide_text or set()
    feats = [f for f in order if f in values]
    return go.Scatter(
        x=[values[f] for f in feats], y=feats, name=name, mode="markers+text",
        marker=dict(color=colour, size=13, symbol=symbol,
                    line=dict(color="#FFFFFF", width=1.5)),
        text=["" if f in hide_text else f"{values[f]:,.2f}" for f in feats],
        textposition=textposition, textfont=dict(size=11, color=t["ink"]),
        hovertemplate="%{y} · " + name + "<br>VIF %{x:,.2f}<extra></extra>",
    )


def _log(v: float) -> float:
    import math
    return math.log10(v)


def head_to_head(models: list[str], cv: list[float], fc: list[float],
                 height: int = 250) -> go.Figure:
    """The two models the notebook scored on the same tests, on one axis.

    Both bars are a root-mean-square error in hires, so they are directly
    comparable — unlike adjusted R-squared, which a boosted tree does not have.
    Lower is better, and the gap is the whole argument.
    """
    t = TOKENS
    fig = go.Figure()
    for i, (name, colour) in enumerate(zip(models, (SERIES[0], t["accent"]))):
        fig.add_trace(go.Bar(
            name=name, x=["5-fold cross-validation", "2025 forecast"],
            y=[cv[i], fc[i]], marker_color=colour,
            text=[f"{cv[i]:,.0f}", f"{fc[i]:,.0f}"],
            textposition="outside", cliponaxis=False,
            textfont=dict(size=12.5, color=t["ink"]),
            hovertemplate="%{fullData.name}<br>%{x}<br>RMSE %{y:,.0f} hires<extra></extra>",
        ))
    top = max(cv + fc) * 1.22
    fig.update_layout(**_base(height), barmode="group", bargap=0.42,
                      bargroupgap=0.1, margin=dict(l=72, r=24, t=16, b=44))
    fig.update_yaxes(title_text="RMSE in hires — lower is better",
                     range=[0, top], tickformat=",")
    fig.update_xaxes(title_text="")
    return fig
