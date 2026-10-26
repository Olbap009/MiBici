"""Corridas comparables y registro de Model Registry para P3 (Clustering de Estaciones)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

import matplotlib

matplotlib.use("Agg")
import mlflow
from mlflow.models import infer_signature
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mibici.config import (
    FIGURES_DIR,
    P3_DEFAULT_K,
    P3_RANDOM_STATE,
    P3_STATIONS_PATH,
    P3_TRIPS_PATH,
    PROJ_ROOT,
)
from mibici.features import extract_p3_station_features
from mibici.modeling.train_p3 import (
    BASELINE_FEATURES,
    CANDIDATE_FEATURES,
    CLUSTER_NAMES,
    file_hash,
    plot_cluster_profiles,
    plot_k_evaluation,
    plot_spatial_clusters,
    sweep_k_metrics,
)

EXPERIMENT_NAME = "mibici-equipo23-mlprojects"
REGISTERED_MODEL_NAME = "mibici-equipo23-p3-grupos"
LEGACY_MODEL_NAME = "MiBici_Equipo23_P3_Estaciones"


def run_p3(
    *,
    model_type: str = "candidato",
    algorithm: str = "kmeans",
    k: int = P3_DEFAULT_K,
    seed: int = P3_RANDOM_STATE,
    sweep_k: bool = False,
) -> dict[str, any]:
    """Entrena una variante de clustering para P3 y registra métricas y artefactos."""
    if k < 2:
        raise ValueError("k debe ser al menos 2 para clustering")
    if algorithm not in {"kmeans", "agglomerative"}:
        raise ValueError(f"Algoritmo no soportado: {algorithm}")
    if model_type not in {"baseline", "candidato"}:
        raise ValueError(f"Tipo de modelo no soportado: {model_type}")

    trips = pd.read_parquet(
        P3_TRIPS_PATH,
        columns=["started_at", "origin_station_id", "destination_station_id"],
    )
    nom = pd.read_csv(P3_STATIONS_PATH)
    features_df = extract_p3_station_features(trips, nom)

    feature_cols = BASELINE_FEATURES if model_type == "baseline" else CANDIDATE_FEATURES
    X = features_df[feature_cols].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if algorithm == "kmeans":
        cluster_estimator = KMeans(n_clusters=k, random_state=seed, n_init=10)
    else:
        cluster_estimator = AgglomerativeClustering(n_clusters=k, linkage="ward")

    pipeline_model = Pipeline([("scale", StandardScaler()), ("cluster", cluster_estimator)])
    labels = pipeline_model.fit_predict(X)
    features_df["cluster"] = labels

    sil_score = float(silhouette_score(X_scaled, labels))
    db_score = float(davies_bouldin_score(X_scaled, labels))
    ch_score = float(calinski_harabasz_score(X_scaled, labels))
    inertia = float(cluster_estimator.inertia_) if algorithm == "kmeans" else float("nan")

    metrics = {
        "silhouette_score": sil_score,
        "davies_bouldin_score": db_score,
        "calinski_harabasz_score": ch_score,
        "n_stations": float(len(features_df)),
        "n_clusters": float(k),
    }
    if not np.isnan(inertia):
        metrics["inertia"] = inertia

    stage = "baseline" if model_type == "baseline" else "candidate"
    run_name = f"P3_{algorithm}_{model_type}_k{k}"

    with mlflow.start_run(run_name=run_name, nested=mlflow.active_run() is not None) as run:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJ_ROOT, text=True
        ).strip()

        mlflow.set_tags(
            {
                "question": "P3",
                "model_family": algorithm,
                "stage_of_work": stage,
                "team": "23",
                "commit": commit,
                "tipo_tarea": "Clustering",
                "tipo_modelo": model_type,
            }
        )

        params = {
            "algorithm": algorithm,
            "k": k,
            "model_type": model_type,
            "seed": seed,
            "num_features": len(feature_cols),
            "features_usadas": ",".join(feature_cols),
            "data_sha256": file_hash(P3_TRIPS_PATH),
            "nomenclature_sha256": file_hash(P3_STATIONS_PATH),
            "periodo_inicio": str(trips["started_at"].min()),
            "periodo_fin": str(trips["started_at"].max()),
        }
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)

        # Dataset input registration
        mlflow.log_input(
            mlflow.data.from_pandas(
                X.assign(station_key=features_df.index.astype(str)),
                source=str(P3_TRIPS_PATH),
                name="p3_perfiles_estacion",
            ),
            context="training",
        )

        # Organizar artefactos en subcarpetas estructuradas: plots/, data/, config/
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            plots_dir = temp_path / "plots"
            data_dir = temp_path / "data"
            config_dir = temp_path / "config"
            plots_dir.mkdir()
            data_dir.mkdir()
            config_dir.mkdir()

            # Plots
            plot_spatial_clusters(features_df, plots_dir / "p3_mapa_espacial_clusters.png")
            plot_cluster_profiles(
                features_df, feature_cols, plots_dir / "p3_perfiles_clusters.png"
            )
            if sweep_k and algorithm == "kmeans":
                k_range, inertias, silhouettes = sweep_k_metrics(X_scaled, seed, max_k=8)
                plot_k_evaluation(
                    k_range, inertias, silhouettes, k, plots_dir / "p3_seleccion_k.png"
                )

            # Data
            export_cols = ["nombre", "capacidad", "latitude", "longitude", "cluster"] + [
                c for c in feature_cols if c not in ["latitude", "longitude", "capacidad"]
            ]
            features_df[export_cols].to_csv(data_dir / "p3_estaciones_clustering.csv")
            counts = features_df["cluster"].value_counts().to_dict()
            summary = {
                "metricas": metrics,
                "distribucion_clusters": {
                    f"Cluster_{c} ({CLUSTER_NAMES.get(c, 'N/A')})": int(cnt)
                    for c, cnt in counts.items()
                },
                "variables": feature_cols,
            }
            (data_dir / "resumen_p3.json").write_text(
                json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            (data_dir / "manifiesto.json").write_text(
                json.dumps(
                    {
                        "trips_sha256": file_hash(P3_TRIPS_PATH),
                        "stations_sha256": file_hash(P3_STATIONS_PATH),
                        "stations_count": len(features_df),
                        "note": "Clustering descriptivo; evaluado por métricas internas",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            # Config
            (config_dir / "configuracion.json").write_text(
                json.dumps(
                    {
                        "model_type": model_type,
                        "algorithm": algorithm,
                        "k": k,
                        "seed": seed,
                        "features": feature_cols,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            # Registrar carpetas organizadas
            mlflow.log_artifacts(str(plots_dir), artifact_path="plots")
            mlflow.log_artifacts(str(data_dir), artifact_path="data")
            mlflow.log_artifacts(str(config_dir), artifact_path="config")

            # También mantener copia fija en reports/figures/ para la documentación
            FIGURES_DIR.mkdir(parents=True, exist_ok=True)
            for f in plots_dir.glob("*"):
                (FIGURES_DIR / f.name).write_bytes(f.read_bytes())
            for f in data_dir.glob("*"):
                (FIGURES_DIR / f.name).write_bytes(f.read_bytes())

        # Log model with signature and input example
        signature = (
            infer_signature(X.head(5), pipeline_model.predict(X.head(5)))
            if algorithm == "kmeans"
            else infer_signature(X.head(5))
        )
        mlflow.sklearn.log_model(
            sk_model=pipeline_model,
            name="modelo_p3",
            input_example=X.head(5),
            signature=signature,
            serialization_format="cloudpickle",
        )

        return {
            "run_id": run.info.run_id,
            "metrics": metrics,
            "model_type": model_type,
            "algorithm": algorithm,
            "k": k,
        }


def search_p3(*, seed: int = P3_RANDOM_STATE) -> dict[str, any]:
    """Búsqueda anidada (nested runs) para P3: baseline + variantes candidatas."""
    client = MlflowClient()

    with mlflow.start_run(run_name="P3_busqueda", nested=mlflow.active_run() is not None):
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJ_ROOT, text=True
        ).strip()
        mlflow.set_tags(
            {
                "question": "P3",
                "model_family": "search",
                "stage_of_work": "hyperparameter_search",
                "team": "23",
                "commit": commit,
            }
        )

        # 1. Ejecutar baseline como corrida hija
        baseline_res = run_p3(
            model_type="baseline",
            algorithm="kmeans",
            k=4,
            seed=seed,
            sweep_k=False,
        )
        baseline_run_id = baseline_res["run_id"]

        # 2. Ejecutar variantes candidatas como corridas hijas
        candidate_configs = [
            ("kmeans", 3),
            ("kmeans", 4),
            ("kmeans", 5),
            ("agglomerative", 4),
        ]
        candidates = []
        for algo, k_val in candidate_configs:
            res = run_p3(
                model_type="candidato",
                algorithm=algo,
                k=k_val,
                seed=seed,
                sweep_k=(algo == "kmeans" and k_val == 4),
            )
            candidates.append(res)

        # 3. Selección justificada del modelo ganador:
        # Entre los modelos capaces de realizar inferencia sobre nuevas estaciones (KMeans),
        # k=4 balancea compacidad (silhouette 0.1834) con la máxima interpretabilidad operativa
        # de los 4 cuadrantes funcionales urbanos (Polo laboral, Residencial, Ocio/Fin de semana, Periféricas).
        kmeans_candidates = [c for c in candidates if c["algorithm"] == "kmeans"]
        # Seleccionamos k=4 explícitamente justificado
        winner = next(
            (c for c in kmeans_candidates if c["k"] == 4),
            max(kmeans_candidates, key=lambda c: c["metrics"]["silhouette_score"]),
        )
        winner_run_id = winner["run_id"]

        mlflow.log_params(
            {
                "winner_run_id": winner_run_id,
                "baseline_run_id": baseline_run_id,
                "winner_algorithm": winner["algorithm"],
                "winner_k": winner["k"],
            }
        )
        mlflow.log_metric("best_silhouette", winner["metrics"]["silhouette_score"])
        mlflow.log_metric("best_davies_bouldin", winner["metrics"]["davies_bouldin_score"])
        mlflow.log_metric("best_calinski_harabasz", winner["metrics"]["calinski_harabasz_score"])

        # Etiquetar la corrida ganadora
        client.set_tag(winner_run_id, "stage_of_work", "selected_unsupervised")

        # 4. Registrar en el Model Registry
        # Registramos con ambos nombres para compatibilidad completa
        for model_name in (REGISTERED_MODEL_NAME, LEGACY_MODEL_NAME):
            registered_model = mlflow.register_model(
                model_uri=f"runs:/{winner_run_id}/modelo_p3",
                name=model_name,
                await_registration_for=60,
            )

            client.update_registered_model(
                name=model_name,
                description=(
                    "Modelo de tipología y agrupamiento funcional de estaciones MiBici (P3). "
                    "Implementa K-Means (k=4) sobre un espacio 9D de dinámicas horarias, "
                    "flujo neto y localización espacial para la optimización de rutas de balanceo."
                ),
            )

            client.set_model_version_tag(
                model_name, registered_model.version, "academic_review", "required"
            )
            client.set_model_version_tag(model_name, registered_model.version, "question", "P3")
            client.set_model_version_tag(
                model_name, registered_model.version, "source_run", winner_run_id
            )
            client.set_model_version_tag(model_name, registered_model.version, "commit", commit)

            # Asignar alias champion al modelo ganador
            client.set_registered_model_alias(
                name=model_name,
                alias="champion",
                version=registered_model.version,
            )

        # 5. Comprobación de carga e inferencia vía alias champion
        champion_uri = f"models:/{REGISTERED_MODEL_NAME}@champion"
        loaded_model = mlflow.sklearn.load_model(champion_uri)

        # Cargar datos para prueba de humo
        nom = pd.read_csv(P3_STATIONS_PATH)
        trips = pd.read_parquet(
            P3_TRIPS_PATH,
            columns=["started_at", "origin_station_id", "destination_station_id"],
        )
        features = extract_p3_station_features(trips, nom)
        sample_input = features[CANDIDATE_FEATURES].head(5)
        smoke_preds = loaded_model.predict(sample_input)

        if len(smoke_preds) != 5:
            raise RuntimeError("El modelo registrado no generó el número esperado de predicciones")

        result = {
            "winner_run_id": winner_run_id,
            "baseline_run_id": baseline_run_id,
            "registered_model": REGISTERED_MODEL_NAME,
            "alias": "champion",
            "model_version": registered_model.version,
            "metrics": winner["metrics"],
            "smoke_predictions": smoke_preds.tolist(),
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
