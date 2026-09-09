"""The design system: three candidate visual worlds, one Plotly template each.

Every figure in the app is built from `template_for(variant)`. Nothing sets a
font, a grid colour or a margin on its own.

The three worlds share the layout language pinned in `design_inspo/`: a light
ground, a persistent left rail, rounded cards, Santander red and the navy of
the bike frame. They differ in which colour owns the rail, how much air the
composition carries, and what the structural device is.
"""

from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

# --- The three worlds ------------------------------------------------------
# `ink` is body text, `ink_soft` secondary, `rule` hairlines. `series` is the
# categorical palette, ordered; `scale` is the sequential one, cold to hot.

VARIANTS: dict[str, dict] = {
    "control": {
        "label": "Control Room",
        "blurb": "Red rail, instrument density, a status chip on every card.",
        "font": "Hanken Grotesk",
        "font_url": "Hanken+Grotesk:wght@400;500;600;700;800",
        "ground": "#F3F4F7",
        "card": "#FFFFFF",
        "rail": "#EC0000",
        "rail_ink": "#FFFFFF",
        "rail_ink_soft": "#F9C3C3",
        "rail_active": "#FFFFFF",
        "ink": "#10162A",
        "ink_soft": "#5C6478",
        "rule": "#E2E5EB",
        "accent": "#EC0000",
        "accent_soft": "#FDECEC",
        "navy": "#1B2A5B",
        "radius": "12px",
        "radius_sm": "8px",
        "shadow": "0 1px 2px rgba(16,22,42,.06), 0 1px 3px rgba(16,22,42,.04)",
        "series": ["#1B2A5B", "#EC0000", "#7A8496", "#5E7CC4", "#C2410C"],
        "scale": ["#EEF1F8", "#B9C4DE", "#7A8CBE", "#3F5596", "#1B2A5B"],
        "diverging": ["#5C74AE", "#AEBBD8", "#F4F5F8", "#F3B4B4", "#E97A7A"],
        "grid": "#EDEFF4",
        "chart": {"size": 12.5, "margin": (62, 18, 30, 46), "gridx": True},
    },
    "concourse": {
        "label": "Concourse",
        "blurb": "Navy rail, ruled departure-board tables, red only as a lamp.",
        "font": "Archivo",
        "font_url": "Archivo:wght@400;500;600;700",
        "ground": "#FAFAF8",
        "card": "#FFFFFF",
        "rail": "#0E1B33",
        "rail_ink": "#FFFFFF",
        "rail_ink_soft": "#8E9BB5",
        "rail_active": "#EC0000",
        "ink": "#0E1B33",
        "ink_soft": "#606B80",
        "rule": "#DFE0DB",
        "accent": "#EC0000",
        "accent_soft": "#FCEBEA",
        "navy": "#0E1B33",
        "radius": "6px",
        "radius_sm": "4px",
        "shadow": "none",
        "series": ["#0E1B33", "#EC0000", "#8A9099", "#39506F", "#B08900"],
        "scale": ["#F0F1EF", "#C2C7CF", "#8996A8", "#4A5C79", "#0E1B33"],
        "diverging": ["#5A6D8C", "#AAB4C2", "#F2F3F0", "#F0B6B2", "#E88A84"],
        "grid": "#EDEEEA",
        # A board rules horizontally only; vertical grid lines are noise on it.
        "chart": {"size": 12.5, "margin": (66, 18, 34, 48), "gridx": False},
    },
    "roundel": {
        "label": "Roundel",
        "blurb": "Navy rail, wide air, roundel geometry, closest to your reference.",
        "font": "Public Sans",
        "font_url": "Public+Sans:wght@400;500;600;700;800",
        "ground": "#F7F8FA",
        "card": "#FFFFFF",
        "rail": "#14213D",
        "rail_ink": "#FFFFFF",
        "rail_ink_soft": "#98A2B8",
        "rail_active": "#FFFFFF",
        "ink": "#14213D",
        "ink_soft": "#667085",
        "rule": "#E7EAF0",
        "accent": "#EC0000",
        "accent_soft": "#FDEDED",
        "navy": "#14213D",
        "radius": "18px",
        "radius_sm": "12px",
        "shadow": "0 2px 4px rgba(20,33,61,.05), 0 8px 20px rgba(20,33,61,.05)",
        "series": ["#14213D", "#EC0000", "#98A2B8", "#4F6699", "#D97706"],
        "scale": ["#EEF1F6", "#C3CBDA", "#8B9AB8", "#4A5D85", "#14213D"],
        "diverging": ["#586C97", "#A9B4CA", "#F1F3F7", "#F4B7B7", "#E98080"],
        "grid": "#EFF1F5",
        "chart": {"size": 13.5, "margin": (74, 22, 38, 54), "gridx": True},
    },
}

DEFAULT_VARIANT = "control"


def tokens(variant: str) -> dict:
    return VARIANTS.get(variant, VARIANTS[DEFAULT_VARIANT])


def font_stack(variant: str) -> str:
    return f'"{tokens(variant)["font"]}", "Helvetica Neue", Helvetica, Arial, sans-serif'


def template_for(variant: str) -> go.layout.Template:
    """The one Plotly template every figure uses. Built once per variant."""
    name = f"cycle-{variant}"
    if name in pio.templates:
        return pio.templates[name]

    t = tokens(variant)
    c = t["chart"]
    ml, mr, mt, mb = c["margin"]
    tpl = go.layout.Template()
    tpl.layout = go.Layout(
        font=dict(family=font_stack(variant), size=c["size"], color=t["ink"]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=t["series"],
        margin=dict(l=ml, r=mr, t=mt, b=mb),
        hoverlabel=dict(
            bgcolor=t["ink"],
            bordercolor=t["ink"],
            font=dict(family=font_stack(variant), size=12.5, color="#FFFFFF"),
            align="left",
        ),
        hovermode="closest",
        xaxis=dict(
            showgrid=c["gridx"],
            gridcolor=t["grid"], zeroline=False, linecolor=t["rule"],
            ticks="outside", tickcolor=t["rule"], ticklen=4,
            tickfont=dict(size=c["size"] - 0.5, color=t["ink_soft"]),
            title=dict(font=dict(size=c["size"], color=t["ink_soft"]), standoff=10),
            automargin=True,
        ),
        yaxis=dict(
            gridcolor=t["grid"], zeroline=False, linecolor=t["rule"],
            ticks="outside", tickcolor=t["rule"], ticklen=4,
            tickfont=dict(size=c["size"] - 0.5, color=t["ink_soft"]),
            title=dict(font=dict(size=c["size"], color=t["ink_soft"]), standoff=14),
            automargin=True,
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            font=dict(size=12.5, color=t["ink_soft"]),
            title=dict(text=""), bgcolor="rgba(0,0,0,0)",
        ),
        colorscale=dict(sequential=_scale(t["scale"]), diverging=_scale(t["diverging"])),
    )
    pio.templates[name] = tpl
    return tpl


def _scale(colors: list[str]) -> list[list]:
    last = len(colors) - 1
    return [[i / last, c] for i, c in enumerate(colors)]


def css_variables(variant: str) -> str:
    """This variant's tokens as a CSS declaration block."""
    t = tokens(variant)
    pairs = {
        "--ground": t["ground"], "--card": t["card"], "--rail": t["rail"],
        "--rail-ink": t["rail_ink"], "--rail-ink-soft": t["rail_ink_soft"],
        "--rail-active": t["rail_active"], "--ink": t["ink"],
        "--ink-soft": t["ink_soft"], "--rule": t["rule"], "--accent": t["accent"],
        "--accent-soft": t["accent_soft"], "--navy": t["navy"],
        "--radius": t["radius"], "--radius-sm": t["radius_sm"],
        "--shadow": t["shadow"], "--font": font_stack(variant),
    }
    return " ".join(f"{k}: {v};" for k, v in pairs.items())


def write_tokens_css(path: Path | None = None) -> Path:
    """Generate assets/tokens.css from VARIANTS, so the palette is defined once
    in Python and CSS and Plotly can never drift apart."""
    path = path or Path(__file__).parent / "assets" / "tokens.css"
    blocks = [f"/* Generated by theme.write_tokens_css(). Do not edit. */",
              f":root {{ {css_variables(DEFAULT_VARIANT)} }}"]
    for key in VARIANTS:
        blocks.append(f'[data-variant="{key}"] {{ {css_variables(key)} }}')
    path.write_text("\n".join(blocks) + "\n")
    return path


def google_fonts_href() -> str:
    families = "&".join(f"family={v['font_url']}" for v in VARIANTS.values())
    return f"https://fonts.googleapis.com/css2?{families}&display=swap"
