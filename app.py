"""Cycle Demand — London Santander Cycles daily hire demand.

Run locally:  uv run python app.py
Served by:    gunicorn app:server
"""

from __future__ import annotations

import os

from dash import Dash, Input, Output, callback, dcc, html

import callbacks
import layout as L
from data_loader import dataset_span, load_bikes
from model import load_fit, load_model, load_vif, numeric_sources
from theme import google_fonts_href, write_tokens_css

write_tokens_css()                        # assets/tokens.css, read by Dash below

app = Dash(__name__, title="Cycle Demand — London Santander Cycles",
           update_title=None, suppress_callback_exceptions=True)
server = app.server                      # gunicorn entry point

app.index_string = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    {{%metas%}}
    <title>{{%title%}}</title>
    {{%favicon%}}
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="{google_fonts_href()}">
    {{%css%}}
  </head>
  <body>
    {{%app_entry%}}
    <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
  </body>
</html>"""

app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="retry-store", data=0),
    html.Div(id="shell"),
])


@callback(Output("shell", "children"), Input("url", "pathname"))
def route(pathname):
    bike = load_bikes()
    span = dataset_span(bike)
    active = "predict" if (pathname or "").rstrip("/").endswith("predict") else "explore"
    page = (L.predict_page(load_model(), load_fit(), load_vif(), numeric_sources())
            if active == "predict" else L.explore_page(bike))
    return html.Div(
        [
            L.rail(active, span),
            html.Div(page, className="main"),
        ],
        className="shell",
    )


callbacks.register(app)
callbacks.register_predict(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)
