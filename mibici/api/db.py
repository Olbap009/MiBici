"""Persistencia opcional de predicciones en PostgreSQL para monitoreo."""

from __future__ import annotations

from collections.abc import Sequence
import os

from loguru import logger
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from mibici.api.schemas import P2PredictionRequest, P2PredictionResponse

_CREATE_TABLE_SQL = text(
    """
    CREATE TABLE IF NOT EXISTS predictions (
        id BIGSERIAL PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        departures_prev_30m INTEGER NOT NULL,
        arrivals_prev_30m INTEGER NOT NULL,
        departures_prev_2h INTEGER NOT NULL,
        arrivals_prev_2h INTEGER NOT NULL,
        hour INTEGER NOT NULL,
        minute INTEGER NOT NULL,
        day_of_week INTEGER NOT NULL,
        capacity INTEGER NOT NULL,
        prediction TEXT NOT NULL,
        model_name TEXT NOT NULL,
        model_version TEXT NOT NULL
    )
    """
)

_INSERT_PREDICTION_SQL = text(
    """
    INSERT INTO predictions (
        departures_prev_30m,
        arrivals_prev_30m,
        departures_prev_2h,
        arrivals_prev_2h,
        hour,
        minute,
        day_of_week,
        capacity,
        prediction,
        model_name,
        model_version
    ) VALUES (
        :departures_prev_30m,
        :arrivals_prev_30m,
        :departures_prev_2h,
        :arrivals_prev_2h,
        :hour,
        :minute,
        :day_of_week,
        :capacity,
        :prediction,
        :model_name,
        :model_version
    )
    """
)

_engine: Engine | None = None
_engine_url: str | None = None


def _get_engine() -> Engine | None:
    """Retorna el engine SQLAlchemy si DATABASE_URL está configurado."""
    global _engine, _engine_url
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        return None
    if _engine is None or _engine_url != database_url:
        _engine = create_engine(database_url, pool_pre_ping=True)
        _engine_url = database_url
    return _engine


def init_db() -> None:
    """Inicializa la tabla de predicciones si DATABASE_URL está configurado."""
    engine = _get_engine()
    if engine is None:
        return
    try:
        with engine.begin() as conn:
            conn.execute(_CREATE_TABLE_SQL)
        logger.info("Base de datos de predicciones inicializada.")
    except SQLAlchemyError as exc:
        logger.warning("No fue posible inicializar la base de datos de predicciones: {}", exc)


def log_predictions(
    records: Sequence[tuple[P2PredictionRequest, P2PredictionResponse]],
) -> None:
    """Guarda predicciones en PostgreSQL sin interrumpir la inferencia si hay fallos."""
    engine = _get_engine()
    if engine is None or not records:
        return
    rows = [
        {
            **req.model_dump(),
            "prediction": resp.prediction,
            "model_name": resp.model_name,
            "model_version": resp.model_version,
        }
        for req, resp in records
    ]
    try:
        with engine.begin() as conn:
            conn.execute(_INSERT_PREDICTION_SQL, rows)
    except SQLAlchemyError as exc:
        logger.warning("No fue posible registrar predicciones en PostgreSQL: {}", exc)
