"""Artefactos de procedencia compartidos por las tres preguntas."""

import mlflow

from mibici.config import PROJ_ROOT


def log_provenance():
    for rel in (
        "data/interim/project_sources_manifest.json",
        "dvc.lock",
        "references/data_manifest.csv",
    ):
        path = PROJ_ROOT / rel
        if path.exists():
            mlflow.log_artifact(str(path), artifact_path="data")
    for rel in ("mibici/config.py", "MLproject", "python_env.yaml", "uv.lock"):
        path = PROJ_ROOT / rel
        if path.exists():
            mlflow.log_artifact(str(path), artifact_path="config")
