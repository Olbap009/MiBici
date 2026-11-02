"""Validacion de calidad de datos P1 mediante DeepChecks."""

from pathlib import Path
import json

import pandas as pd

from deepchecks.tabular import Dataset
from deepchecks.tabular.checks import (
    DataDuplicates,
    MixedDataTypes,
    FeatureDrift,
)
from deepchecks.tabular.suites import data_integrity

ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = ROOT / "data" / "processed" / "p1_demanda_diaria.csv"
OUTPUT_DIR = ROOT / "reports" / "evidence" / "deepchecks"

FEATURES = [
    "dia_semana",
    "mes",
    "fin_semana",
    "lag_1",
    "lag_7",
]


def load_data():
    """Carga y ordena el dataset de P1."""
    df = pd.read_csv(DATA_PATH, parse_dates=["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)
    return df


def validate_rules(df):
    """Verifica reglas basicas de integridad."""
    issues = {}

    required = ["fecha", "viajes"] + FEATURES

    issues["missing_values"] = df[required].isna().sum().to_dict()
    issues["duplicate_rows"] = int(df.duplicated().sum())
    issues["duplicate_dates"] = int(df["fecha"].duplicated().sum())

    issues["negative_values"] = {
        col: int((df[col] < 0).sum())
        for col in ["viajes", "lag_1", "lag_7"]
    }

    issues["invalid_weekdays"] = int(
        (~df["dia_semana"].between(0, 6)).sum()
    )

    issues["invalid_months"] = int(
        (~df["mes"].between(1, 12)).sum()
    )

    issues["invalid_weekend"] = int(
        (~df["fin_semana"].isin([0, 1])).sum()
    )

    return issues


def split_data(df):
    """Replica el corte temporal 60/20/20 de P1."""
    first = int(len(df) * 0.6)
    second = int(len(df) * 0.8)

    train = df.iloc[:first].copy()
    validation = df.iloc[first:second].copy()
    test = df.iloc[second:].copy()

    return train, validation, test


def run_validation():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()

    print("Registros:", len(df))
    print("Columnas:", df.columns.tolist())

    # Reglas de integridad
    issues = validate_rules(df)

    with open(
        OUTPUT_DIR / "integrity_summary.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(issues, file, indent=2, ensure_ascii=False)

    print("\nResumen de integridad:")
    print(json.dumps(issues, indent=2, ensure_ascii=False))

    # Division temporal
    train, validation, test = split_data(df)

    print("\nDivision temporal:")
    print("Train:", len(train))
    print("Validation:", len(validation))
    print("Test:", len(test))

    # Dataset para DeepChecks
    full_dataset = Dataset(
        df[FEATURES + ["viajes"]],
        label="viajes",
        cat_features=["dia_semana", "mes", "fin_semana"],
    )

    train_dataset = Dataset(
        train[FEATURES + ["viajes"]],
        label="viajes",
        cat_features=["dia_semana", "mes", "fin_semana"],
    )

    test_dataset = Dataset(
        test[FEATURES + ["viajes"]],
        label="viajes",
        cat_features=["dia_semana", "mes", "fin_semana"],
    )

    # Chequeos de integridad
    integrity_suite = data_integrity()

    integrity_result = integrity_suite.run(full_dataset)

    integrity_result.save_as_html(
        str(OUTPUT_DIR / "deepchecks_integrity.html")
    )

    # Chequeos especificos
    duplicates_result = DataDuplicates().run(full_dataset)
    mixed_types_result = MixedDataTypes().run(full_dataset)

    # Drift entre entrenamiento y prueba
    drift_result = FeatureDrift().run(
        train_dataset,
        test_dataset,
    )
    print("\n========== RESULTADOS DATA DRIFT ==========")
    print(drift_result.value)
    print("==========================================")
    drift_result.save_as_html(
        str(OUTPUT_DIR / "deepchecks_drift.html")
    )

    print("\nChequeos ejecutados:")
    print("Duplicados:", duplicates_result.value)
    print("Tipos mixtos:", mixed_types_result.value)

    print("\nReportes generados en:")
    print(OUTPUT_DIR)


if __name__ == "__main__":
    run_validation()