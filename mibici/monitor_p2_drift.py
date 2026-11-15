"""Genera un reporte de drift y calidad de datos para los dos periodos de P2."""

import argparse
from datetime import datetime
import hashlib
from importlib.metadata import version
import json
from pathlib import Path

from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset, DataSummaryPreset
import numpy as np
import pyarrow.compute as pc
import pyarrow.dataset as ds

from mibici.api.schemas import P2PredictionRequest
from mibici.config import P2_EXAMPLES_PATH

FEATURES = list(P2PredictionRequest.model_fields)
CALENDAR_FEATURES = ["hour", "minute", "day_of_week"]
PERIODS = {
    "reference": ("train", "2025-07-01", "2025-10-01"),
    "current": ("test", "2026-07-01", "2026-10-01"),
}


def sample_period(source, period, sample_size, seed):
    split, start, end = period
    selection = (
        (ds.field("split") == split)
        & (ds.field("prediction_time") >= datetime.fromisoformat(start))
        & (ds.field("prediction_time") < datetime.fromisoformat(end))
    )
    rows = source.to_table(columns=[*FEATURES, "target"], filter=selection)
    if not rows.num_rows:
        raise ValueError(f"No hay filas para {split} entre {start} y {end} (fin exclusivo).")

    size = min(sample_size, rows.num_rows)
    indices = np.random.default_rng(seed).choice(rows.num_rows, size=size, replace=False)
    sample = rows.select(FEATURES).take(np.sort(indices)).to_pandas()
    distribution = pc.value_counts(rows["target"]).to_pylist()
    return sample, {
        "split": split,
        "start_inclusive": start,
        "end_exclusive": end,
        "total_rows": rows.num_rows,
        "sample_rows": len(sample),
        "target_distribution_full_period": [
            {
                "label": item["values"],
                "count": item["counts"],
                "rate": item["counts"] / rows.num_rows,
            }
            for item in distribution
        ],
        "feature_types": {feature: str(rows.schema.field(feature).type) for feature in FEATURES},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=P2_EXAMPLES_PATH)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/evidence/p2_drift"))
    parser.add_argument("--sample-size", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.sample_size < 1 or args.seed < 0:
        parser.error("--sample-size debe ser positivo y --seed no puede ser negativo.")
    if not args.dataset.is_file():
        parser.error(f"No se encontró el archivo Parquet: {args.dataset}")

    source = ds.dataset(args.dataset, format="parquet")
    definition = DataDefinition(
        numerical_columns=[feature for feature in FEATURES if feature not in CALENDAR_FEATURES],
        categorical_columns=CALENDAR_FEATURES,
    )
    datasets, metadata = {}, {}
    for name, period in PERIODS.items():
        sample, metadata[name] = sample_period(source, period, args.sample_size, args.seed)
        datasets[name] = Dataset.from_pandas(sample, data_definition=definition)

    snapshot = Report([DataDriftPreset(), DataSummaryPreset()]).run(
        datasets["current"], datasets["reference"]
    )
    with args.dataset.open("rb") as file:
        dataset_hash = hashlib.file_digest(file, "sha256").hexdigest()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    snapshot.save_html(str(args.output_dir / "evidently_p2.html"))
    result = {
        "evidently_version": version("evidently"),
        "dataset": args.dataset.name,
        "dataset_sha256": dataset_hash,
        "sampling": {"method": "uniform_without_replacement", "seed": args.seed},
        "periods": metadata,
        "evidently": json.loads(snapshot.json()),
    }
    (args.output_dir / "evidently_p2.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    for name, period in metadata.items():
        print(f"{name}: {period['sample_rows']:,} de {period['total_rows']:,} filas")
    print(f"Reporte guardado en {args.output_dir}")


if __name__ == "__main__":
    main()
