"""Plot functions."""

from datetime import timedelta

import plotly.graph_objects as go
import dash_core_components as dcc
import voluptuous as vol

from .data import get_data

DEFAULT_DURATION = timedelta(hours=24)


def coerce_entity_dict(v):
    """Coerce entity ID strings to a dictionary with key "entity"."""
    if isinstance(v, str):
        return {"entity": v}
    return v


def coerce_timedelta(v):
    """Coerce a dictionary to a timedelta."""
    if isinstance(v, timedelta):
        return v
    elif isinstance(v, dict):
        return timedelta(**v)
    else:
        raise ValueError(f"Duration {v} not understood")


class Plot:
    """Base class for plots."""

    CONFIG_SCHEMA = None

    def __init__(self, engine, config: dict):
        """Initialize given an SQLAlchemy engine and a config dict."""
        self.engine = engine
        self.raw_config = config
        self.config = self.CONFIG_SCHEMA(self.raw_config)

    def data_entity(self, entity_config):
        """Get data for a single entity."""
        entity = entity_config["entity"]
        attribute = entity_config.get("attribute")
        duration = entity_config["duration"]
        resample = entity_config.get("resample")
        aggregate = entity_config.get("aggregate")
        data = get_data(
            engine=self.engine,
            entity=entity,
            attribute=attribute,
            duration=duration,
            resample=resample,
            aggregate=aggregate,
        )
        name = data.get("name") or entity
        if resample:
            name = f"{name} ({resample}, {aggregate or 'mean'})"
        elif aggregate:
            name = f"{name} ({aggregate or 'ptp'})"
        unit = data.get("unit")
        return name, unit, data


class Line(Plot):
    """Line chart."""

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required("type"): "line",
            vol.Required("entities"): [
                vol.All(
                    coerce_entity_dict,
                    vol.Schema(
                        {
                            vol.Required("entity"): str,
                            vol.Optional(
                                "duration", default=DEFAULT_DURATION
                            ): coerce_timedelta,
                            vol.Optional("attribute"): str,
                            vol.Optional("resample"): str,
                            vol.Optional("aggregate"): str,
                        }
                    ),
                )
            ],
        }
    )

    def trace(self, figure, entity_config: dict):
        """Add a single Plotly trace for one entity to the `figure`."""
        name, unit, data = self.data_entity(entity_config)
        figure.add_trace(
            go.Scatter(
                x=data["data"]["time"],
                y=data["data"][entity_config["entity"]],
                mode="lines",
                line_shape="hv",
                name=name,
            )
        )
        return name, unit

    def graph(self) -> dcc.Graph:
        """Return the dash layout."""
        fig = go.Figure()
        unit = None
        for entity_config in self.config["entities"]:
            _, _unit = self.trace(fig, entity_config)
            unit = _unit or unit
        fig.update_layout(
            xaxis_title=None,
            yaxis_title=unit,
            legend=dict(x=0, y=-0.2, orientation="h"),
            margin=dict(t=10),
            font=dict(family="Roboto", color="#333333"),
            template="plotly_white",
            height=300,
        )
        return dcc.Graph(figure=fig)


class Box(Plot):
    """Box plot."""

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required("type"): "box",
            vol.Required("entities"): [
                vol.All(
                    coerce_entity_dict,
                    vol.Schema(
                        {
                            vol.Required("entity"): str,
                            vol.Optional(
                                "duration", default=DEFAULT_DURATION
                            ): coerce_timedelta,
                            vol.Optional("attribute"): str,
                        }
                    ),
                )
            ],
        }
    )

    def trace(self, figure, entity_config: dict):
        """Add a single Plotly trace for one entity to the `figure`."""
        name, unit, data = self.data_entity(entity_config)
        figure.add_trace(go.Box(y=data["data"][entity_config["entity"]], name=name,))
        return name, unit

    def graph(self) -> dcc.Graph:
        """Return the dash layout."""
        fig = go.Figure()
        unit = None
        for entity_config in self.config["entities"]:
            _, _unit = self.trace(fig, entity_config)
            unit = _unit or unit
        fig.update_layout(
            xaxis_title=None,
            yaxis_title=unit,
            legend=dict(x=0, y=-0.2, orientation="h"),
            margin=dict(t=10),
            font=dict(family="Roboto", color="#333333"),
            template="plotly_white",
            height=300,
        )
        return dcc.Graph(figure=fig)


class Pie(Plot):
    """Pie chart."""

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required("type"): "pie",
            vol.Required("entities"): [
                vol.All(
                    coerce_entity_dict,
                    vol.Schema(
                        {
                            vol.Required("entity"): str,
                            vol.Optional(
                                "duration", default=DEFAULT_DURATION
                            ): coerce_timedelta,
                            vol.Optional("attribute"): str,
                            vol.Optional("aggregate", default="ptp"): str,
                        }
                    ),
                )
            ],
        }
    )

    def piece(self, entity_config: dict):
        """Get label and value for a single piece of the pie."""
        name, unit, data = self.data_entity(entity_config)
        return name, data

    def graph(self) -> dcc.Graph:
        """Return the dash layout."""
        labels = []
        values = []
        for entity_config in self.config["entities"]:
            name, data = self.piece(entity_config)
            labels.append(name)
            values.append(data["data"][0][0])
        fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
        fig.update_layout(
            font=dict(family="Roboto", color="#333333"),
            template="plotly_white",
            margin=dict(t=30, b=30),
            height=300,
        )
        return dcc.Graph(figure=fig)
