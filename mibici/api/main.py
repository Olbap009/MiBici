"""Punto de entrada de la API FastAPI para la inferencia del modelo P2."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from loguru import logger

from mibici.api.db import init_db, log_predictions
from mibici.api.model import ModelService, get_model_service, model_service
from mibici.api.schemas import (
    BatchP2PredictionRequest,
    BatchP2PredictionResponse,
    HealthResponse,
    ModelInfoResponse,
    P2PredictionRequest,
    P2PredictionResponse,
)
from mibici.api.ui import get_ui_html


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación: carga el modelo al iniciar."""
    logger.info("Iniciando servicio de API FastAPI para MiBici P2...")
    init_db()
    try:
        model_service.load_model()
    except (RuntimeError, ValueError, OSError) as e:
        logger.error("Error al inicializar el modelo durante el arranque: {}", e)
    yield
    logger.info("Deteniendo servicio de API FastAPI...")


app = FastAPI(
    title="MiBici — API de Predicción de Presión en Estaciones (P2)",
    description=(
        "Servicio REST para estimar la clase de **presión neta de movimientos** "
        "(sin presión neta elevada, presión sin bicicletas, o presión sin anclajes) "
        "en estaciones del sistema de bicicleta pública del Área Metropolitana de Guadalajara (MiBici).\n\n"
        "**Aviso Académico:** Esta API estima un proxy operacional a partir de flujos de viajes "
        "y capacidad, no disponibilidad física de inventario en tiempo real."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.get(
    "/",
    summary="Información general de la API o interfaz interactiva",
    tags=["General"],
)
async def root(request: Request) -> Any:
    """Retorna información general de la API en JSON o la interfaz web si se consulta desde navegador."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return HTMLResponse(content=get_ui_html())
    return {
        "title": "MiBici — API de Predicción de Presión en Estaciones (P2)",
        "version": "1.0.0",
        "documentation": "/docs",
        "interactive_ui": "/ui",
        "health": "/health",
        "model_name": model_service.model_name,
        "model_version": model_service.model_version,
        "status": "online",
    }


@app.get(
    "/ui",
    response_class=HTMLResponse,
    summary="Interfaz gráfica interactiva para predicción",
    tags=["General"],
)
async def ui() -> HTMLResponse:
    """Sirve la interfaz web moderna para simulación e inferencia visual del modelo P2."""
    return HTMLResponse(content=get_ui_html())


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Verificación de salud del servicio",
    tags=["Monitoreo"],
    responses={
        200: {"description": "Servicio saludable y modelo listo para inferencia."},
        503: {"description": "El servicio está activo pero el modelo no pudo inicializarse."},
    },
)
async def health(
    service: Annotated[ModelService, Depends(get_model_service)],
) -> HealthResponse:
    """Verifica si la API y el modelo están disponibles para responder peticiones."""
    if not service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El modelo de predicción no se encuentra disponible.",
        )

    return HealthResponse(
        status="healthy",
        model_loaded=service.is_loaded,
        model_name=service.model_name,
        model_version=service.model_version,
    )


@app.get(
    "/model/info",
    response_model=ModelInfoResponse,
    summary="Información y contrato del modelo",
    tags=["Modelo"],
)
async def model_info(
    service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelInfoResponse:
    """Retorna metadatos técnicos del modelo cargado, variables requeridas y clases posibles."""
    return service.get_info()


@app.post(
    "/predict",
    response_model=P2PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predicción de presión para una estación",
    tags=["Inferencia"],
    responses={
        200: {"description": "Predicción calculada exitosamente."},
        422: {"description": "Error de validación en los datos de entrada (esquema inválido)."},
        500: {"description": "Error interno durante la inferencia."},
    },
)
async def predict(
    request: P2PredictionRequest,
    service: Annotated[ModelService, Depends(get_model_service)],
) -> P2PredictionResponse:
    """Estima la clase de presión neta para el siguiente intervalo de 30 minutos.

    - **departures_prev_30m**: Salidas en los 30 minutos anteriores (>= 0).
    - **arrivals_prev_30m**: Llegadas en los 30 minutos anteriores (>= 0).
    - **departures_prev_2h**: Salidas en las dos horas anteriores (>= 0).
    - **arrivals_prev_2h**: Llegadas en las dos horas anteriores (>= 0).
    - **hour**: Hora local del intervalo (0 a 23).
    - **minute**: Minuto inicial del intervalo (0 o 30).
    - **day_of_week**: Día de la semana (0 = lunes, 6 = domingo).
    - **capacity**: Capacidad total de anclajes de la estación (> 0).
    """
    try:
        response = service.predict(request)
        log_predictions([(request, response)])
        return response
    except (ValueError, TypeError, RuntimeError) as e:
        logger.error("Error al procesar la predicción: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno durante la inferencia: {e}",
        ) from e


@app.post(
    "/predict/batch",
    response_model=BatchP2PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predicción por lotes para múltiples estaciones",
    tags=["Inferencia"],
)
async def predict_batch(
    request: BatchP2PredictionRequest,
    service: Annotated[ModelService, Depends(get_model_service)],
) -> BatchP2PredictionResponse:
    """Realiza inferencias vectorizadas sobre una lista de instancias."""
    try:
        predictions = service.predict_batch(request.instances)
        log_predictions(list(zip(request.instances, predictions, strict=True)))
        return BatchP2PredictionResponse(predictions=predictions)
    except (ValueError, TypeError, RuntimeError) as e:
        logger.error("Error al procesar lote de predicciones: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno durante la inferencia en lote: {e}",
        ) from e
