"""Dashboard powered by Plotly Dash."""


import locale

import dash
import dash_html_components as html
import yaml
from sqlalchemy import create_engine

from .plot import Box, Line, Pie

locale.setlocale(locale.LC_TIME, "")


DEFAULT_TITLE = "HiBro: Home Assistant History Browser"


class HiBro:
    """Base class for the HiBro app."""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self.read_config()

    @property
    def engine(self):
        return create_engine(self.config["db_url"])

    def read_config(self) -> dict:
        """Read the config file."""
        with open(self.config_file, "r") as f:
            d = yaml.safe_load(f)
        return d

    def get_layout(self):
        """Get the Dash layout."""
        elements = []
        layout = self.config.get("elements")
        for element in layout:
            typ = element.get("type")
            if typ == "line":
                elements += [Line(engine=self.engine, config=element).graph()]
            elif typ == "box":
                elements += [Box(engine=self.engine, config=element).graph()]
            elif typ == "pie":
                elements += [Pie(engine=self.engine, config=element).graph()]
            else:
                raise ValueError(f"Element type {typ} not recognized.")
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [html.H1(self.config.get("title", DEFAULT_TITLE))],
                            className="container",
                        )
                    ],
                    id="title",
                ),
                html.Div(elements, className="container"),
            ]
        )


EXTERNAL_STYLESHEETS = []


def create_app(config_file: str):
    """Dash app factory."""
    app = dash.Dash(
        __name__,
        meta_tags=[{"name": "viewport", "content": "width=device-width"},],
        external_stylesheets=EXTERNAL_STYLESHEETS,
    )

    app.config.suppress_callback_exceptions = True

    hibro_inst = HiBro(config_file)
    app.title = hibro_inst.config.get("title", DEFAULT_TITLE)
    app.layout = hibro_inst.get_layout

    return app.server
