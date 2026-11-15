"""Compara dos modelos P2 sobre las mismas filas de julio a septiembre de 2026."""

import argparse
from datetime import datetime
import json
from pathlib import Path

import mlflow
from mlflow.models import infer_signature
import mlflow.sklearn
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from sklearn.metrics import confusion_matrix
from sklearn.tree import DecisionTreeClassifier

from mibici.config import MODELS_DIR, P2_EXAMPLES_PATH
from mibici.modeling.train_p2 import FEATURES, LABELS, file_hash

EVAL_START = datetime(2026, 7, 1)
EVAL_END = datetime(2026, 10, 1)
SEED = 42
FRACTION = 0.05
CANDIDATE_PARAMS = {"max_depth": 3, "class_weight": "balanced", "random_state": SEED}


def read_batches(source, condition):
    """Lee únicamente las columnas de inferencia y la etiqueta."""
    scanner = source.scanner(
        columns=[*FEATURES, "target"],
        filter=condition,
        batch_size=100_000,
        batch_readahead=1,
        fragment_readahead=1,
        use_threads=False,
    )
    for batch in scanner.to_batches():
        frame = batch.to_pandas()
        if not frame["target"].isin(LABELS).all():
            raise ValueError("Hay etiquetas de P2 desconocidas o faltantes.")
        yield frame


def train_candidate(source, candidate_dir):
    # La etiqueta usa movimientos futuros. Su ventana también debe terminar antes de test.
    condition = (
        ds.field("split").isin(["train", "validation"])
        & (ds.field("prediction_time") < EVAL_START)
        & (ds.field("target_end") <= EVAL_START)
    )
    rng = np.random.default_rng(SEED)
    pieces = []
    available = 0
    for frame in read_batches(source, condition):
        available += len(frame)
        selected = rng.random(len(frame)) < FRACTION
        pieces.append(frame.loc[selected].copy())
    if not pieces:
        raise ValueError("El dataset no contiene filas elegibles de entrenamiento.")
    sample = pd.concat(pieces, ignore_index=True)
    if set(sample["target"]) != set(LABELS):
        raise ValueError("La muestra de entrenamiento debe contener las tres clases de P2.")

    features = sample[FEATURES]
    model = DecisionTreeClassifier(**CANDIDATE_PARAMS).fit(features, sample["target"])
    if candidate_dir is not None:
        example = features.head(1)
        mlflow.sklearn.save_model(
            model,
            str(candidate_dir),
            signature=infer_signature(example, model.predict(example)),
            serialization_format="cloudpickle",
        )
    return model, {
        "kind": "local_candidate",
        "model_type": "DecisionTreeClassifier",
        "params": CANDIDATE_PARAMS,
        "splits": ["train", "validation"],
        "training_cutoff": EVAL_START.isoformat(),
        "sample_fraction": FRACTION,
        "train_rows_available": available,
        "train_rows_used": len(sample),
        "sample_class_counts": {label: int((sample["target"] == label).sum()) for label in LABELS},
    }


def load_version(uri):
    if uri.startswith("models:/"):
        name, _, version = uri.removeprefix("models:/").rpartition("/")
        if not name or not version.isdecimal():
            raise ValueError("Indica una versión fija con models:/nombre/número.")
        registry_version = mlflow.MlflowClient().get_model_version(name, version)
        info = {
            "kind": "registry",
            "model_name": name,
            "version": version,
            "run_id": registry_version.run_id,
        }
    else:
        folder = Path(uri)
        manifest = folder / "manifest.json"
        info = {"kind": "local_artifact", "artifact": folder.name}
        if manifest.is_file():
            metadata = json.loads(manifest.read_text(encoding="utf-8"))
            info.update(
                {
                    "model_name": metadata.get("model_name"),
                    "version": metadata.get("version"),
                    "run_id": metadata.get("run_id"),
                }
            )
        uri = str(folder.resolve())
    return mlflow.sklearn.load_model(uri), info


def evaluate(source, models):
    condition = (
        (ds.field("split") == "test")
        & (ds.field("prediction_time") >= EVAL_START)
        & (ds.field("prediction_time") < EVAL_END)
    )
    matrices = {name: np.zeros((len(LABELS), len(LABELS)), dtype=np.int64) for name in models}
    for frame in read_batches(source, condition):
        for name, model in models.items():
            predicted = model.predict(frame[FEATURES])
            if not np.isin(predicted, LABELS).all():
                raise ValueError(f"El modelo {name} produjo una clase ajena a P2.")
            matrices[name] += confusion_matrix(frame["target"], predicted, labels=LABELS)
    return matrices


def metrics(matrix):
    support = matrix.sum(axis=1)
    predicted = matrix.sum(axis=0)
    if (support == 0).any():
        raise ValueError("El conjunto de evaluación debe contener las tres clases de P2.")
    true_positives = matrix.diagonal()
    precision = np.divide(
        true_positives, predicted, out=np.zeros(len(LABELS)), where=predicted > 0
    )
    recall = true_positives / support
    return {
        "balanced_accuracy": float(recall.mean()),
        "precision": dict(zip(LABELS, precision.tolist(), strict=True)),
        "recall": dict(zip(LABELS, recall.tolist(), strict=True)),
        "alerts": int(predicted[1:].sum()),
        "alerts_on_no_pressure": int(matrix[0, 1:].sum()),
        "confusion_matrix": matrix.tolist(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=P2_EXAMPLES_PATH)
    parser.add_argument("--model-a", default=str(MODELS_DIR / "p2_champion"))
    parser.add_argument("--model-b", help="URI fija de MLflow o ruta local de otro artefacto.")
    parser.add_argument(
        "--save-candidate", type=Path, help="Guarda la candidata local como MLmodel."
    )
    parser.add_argument(
        "--tracking-uri", help="Servidor de MLflow al cargar versiones registradas."
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.model_b and args.save_candidate:
        parser.error("--save-candidate solo se usa cuando el comando entrena la candidata.")
    if args.tracking_uri:
        mlflow.set_tracking_uri(args.tracking_uri)

    source = ds.dataset(args.dataset, format="parquet")
    model_a, info_a = load_version(args.model_a)
    if args.model_b:
        model_b, info_b = load_version(args.model_b)
    else:
        model_b, info_b = train_candidate(source, args.save_candidate)
    matrices = evaluate(source, {"A": model_a, "B": model_b})
    results = {
        "dataset_sha256": file_hash(args.dataset),
        "evaluation": {
            "split": "test",
            "start_inclusive": EVAL_START.isoformat(),
            "end_exclusive": EVAL_END.isoformat(),
            "rows": int(matrices["A"].sum()),
        },
        "class_order": LABELS,
        "A": {**info_a, **metrics(matrices["A"])},
        "B": {**info_b, **metrics(matrices["B"])},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Resultados de {results['evaluation']['rows']:,} filas en {args.output}")


if __name__ == "__main__":
    main()
