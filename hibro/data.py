"""Module to fetch history data."""

import json
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import tzlocal
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import Session

# SQLAlchemy Schema
# pylint: disable=invalid-name
Base = declarative_base()


class States(Base):  # type: ignore
    """State change history SQLAlchemy model.

    Directly taken from homeassistant."""

    __tablename__ = "states"
    state_id = Column(Integer, primary_key=True)
    domain = Column(String(64))
    entity_id = Column(String(255), index=True)
    state = Column(String(255))
    attributes = Column(Text)
    event_id = Column(Integer, ForeignKey("events.event_id"), index=True)
    last_changed = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    created = Column(DateTime(timezone=True), default=datetime.utcnow)
    context_id = Column(String(36), index=True)
    context_user_id = Column(String(36), index=True)


def get_data(
    engine: Engine,
    entity: str,
    attribute: Optional[str] = None,
    duration: Optional[timedelta] = None,
    resample: Optional[str] = None,
    aggregate: Optional[str] = None,
):
    """Fetch the data from the database and apply the necessary operations."""
    session = Session()
    query = (
        session.query(States.created, States.state, States.attributes)
        .filter_by(entity_id=entity)
        .order_by(States.created)
    )
    if duration is not None:
        query = query.filter(States.created >= datetime.utcnow() - duration)
    df = pd.read_sql_query(query.statement, con=engine)
    if len(df) == 0:
        return None
    attributes = json.loads(df.iloc[0]["attributes"])
    if attribute is not None:
        df.loc[:, "attributes"] = df.loc[:, "attributes"].map(
            lambda s: json.loads(s).get(attribute)
        )
        df = df.drop("state", axis=1)
    else:
        df = df.drop("attributes", axis=1)
    df.columns = ["time", entity]
    # drop rows with unkown state
    df = df[(df[entity] != "unknown") & (df[entity] != "Invalid")]
    if resample is not None:
        df = df.set_index("time")
        df = (
            df.astype(float)
            .resample("s")
            .pad()
            .resample(resample)
            .agg(aggregate or "mean")
        )
        df = df.reset_index()
    elif aggregate is not None:
        if aggregate == "ptp":
            agg = np.ptp
        else:
            agg = aggregate
        df = df.set_index("time")
        df = df.astype(float).resample("s").agg(agg)
        df = df.reset_index()
    if df.loc[:, "time"].dt.tz is None:
        # localize to UTC if tz-naive
        df.loc[:, "time"] = df.loc[:, "time"].dt.tz_localize("UTC")
    df.loc[:, "time"] = df.loc[:, "time"].dt.tz_convert(tzlocal.get_localzone())
    return {
        "name": attributes.get("friendly_name"),
        "unit": attributes.get("unit_of_measurement"),
        "data": df,
    }
