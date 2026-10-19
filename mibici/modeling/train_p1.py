import hashlib
from pathlib import Path
import subprocess
from urllib.error import URLError
from urllib.request import urlopen

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from mibici.config import (
    FIGURES_DIR,
    P1_DATA_PATH,
    P1_EXPERIMENT_NAME,
    P1_MODEL_PATH,
    P1_RANDOM_STATE,
    PROJ_ROOT,
)

FEATURES = [
    "dia_semana",
    "mes",
    "fin_semana",
    "lag_1",
    "lag_7",
]


def file_hash(path: Path) -> str:
    """Calcula hash SHA-256 del dataset para trazabilidad."""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_tracking_uri(uri: str = "http://127.0.0.1:5001") -> str:
    """Verifica si el servidor HTTP de MLflow responde; si no, usa SQLite local."""
    try:
        with urlopen(uri, timeout=1.5):
            return uri
    except (URLError, TimeoutError, OSError):
        return f"sqlite:///{PROJ_ROOT}/mlruns.db"


def evaluar(y_real, y_pred):
    return {
        "mae": float(mean_absolute_error(y_real, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_real, y_pred))),
        "r2": float(r2_score(y_real, y_pred)),
    }


def main():
    if not P1_DATA_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el dataset {P1_DATA_PATH}. "
            "Ejecuta 'uv run python notebooks/preparacion_p1.py' primero."
        )

    # Cargar datos
    df = pd.read_csv(P1_DATA_PATH, parse_dates=["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)

    # División cronológica
    split = int(len(df) * 0.8)

    train = df.iloc[:split]
    test = df.iloc[split:]

    X_train = train[FEATURES]
    y_train = train["viajes"]

    X_test = test[FEATURES]
    y_test = test["viajes"]

    periodo_inicio = str(df["fecha"].min())
    periodo_fin = str(df["fecha"].max())
    data_sha = file_hash(P1_DATA_PATH)

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJ_ROOT, text=True
        ).strip()
    except (subprocess.SubprocessError, OSError):
        commit = "unknown"

    tracking_uri = get_tracking_uri()
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(P1_EXPERIMENT_NAME)

    common_tags = {
        "equipo": "23",
        "pregunta": "P1",
        "tipo_tarea": "Regresion",
        "target_tipo": "demanda_diaria",
        "git_commit": commit,
    }

    # Experimento 1: Baseline semanal
    with mlflow.start_run(run_name="P1_baseline_lag7"):
        pred_baseline = test["lag_7"].to_numpy()
        metricas_baseline = evaluar(y_test, pred_baseline)

        mlflow.set_tags({**common_tags, "tipo_modelo": "baseline"})
        mlflow.log_params(
            {
                "modelo": "baseline_lag7",
                "test_size": 0.2,
                "data_sha256": data_sha,
                "periodo_inicio": periodo_inicio,
                "periodo_fin": periodo_fin,
            }
        )
        mlflow.log_metrics(metricas_baseline)
        print("\nBASELINE P1:", metricas_baseline)

    # Experimento 2: Random Forest Candidato
    with mlflow.start_run(run_name="P1_random_forest_candidato"):
        modelo = RandomForestRegressor(
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=3,
            random_state=P1_RANDOM_STATE,
            n_jobs=-1,
        )

        modelo.fit(X_train, y_train)
        pred_rf = modelo.predict(X_test)
        metricas_rf = evaluar(y_test, pred_rf)

        mlflow.set_tags({**common_tags, "tipo_modelo": "candidato"})
        mlflow.log_params(
            {
                "modelo": "RandomForestRegressor",
                "n_estimators": 200,
                "max_depth": 8,
                "min_samples_leaf": 3,
                "random_state": P1_RANDOM_STATE,
                "test_size": 0.2,
                "features_usadas": ",".join(FEATURES),
                "data_sha256": data_sha,
                "periodo_inicio": periodo_inicio,
                "periodo_fin": periodo_fin,
            }
        )
        mlflow.log_metrics(metricas_rf)
        mlflow.sklearn.log_model(
            modelo,
            name="modelo_p1",
            input_example=X_train.head(5),
            serialization_format="cloudpickle",
        )

        # Registrar artefactos de figuras si existen
        for fig_name in (
            "p1_real_vs_predicho.png",
            "p1_errores.png",
            "p1_importancia_variables.png",
        ):
            fig_path = FIGURES_DIR / fig_name
            if fig_path.exists():
                mlflow.log_artifact(str(fig_path), artifact_path="artefactos_p1")

        P1_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(modelo, P1_MODEL_PATH)
        print("\nRANDOM FOREST P1:", metricas_rf)

    print("\nEntrenamiento P1 finalizado.")


if __name__ == "__main__":
    main()
