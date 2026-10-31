"""Comprueba que P2 repite sus resultados con datos y semilla idénticos."""

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from mibici.modeling import train_p2


def test_mismo_dataset_y_semilla_producen_mismas_predicciones(tmp_path, monkeypatch):
    # Construimos datos pequeños en vez de cargar los millones de filas reales.
    rows = []
    for clase, etiqueta in enumerate(train_p2.LABELS):
        for indice in range(30):
            rows.append({
                **{
                    variable: float(clase * 10 + indice % 3)
                    for variable in train_p2.FEATURES
                },
                "target": etiqueta,
                "split": "train",
            })

    dataset = tmp_path / "p2_ejemplos.parquet"
    pd.DataFrame(rows).to_parquet(dataset, index=False)
    monkeypatch.setattr(train_p2, "P2_EXAMPLES_PATH", dataset)

    # Repetimos las dos etapas reales: muestreo y entrenamiento.
    predicciones = []
    for _ in range(2):
        muestra, total = train_p2.sample_training(fraction=0.6, seed=42)
        assert total == len(rows)

        modelo = DecisionTreeClassifier(
            max_depth=7,
            min_samples_leaf=1,
            class_weight="balanced",
            random_state=42,
        )
        modelo.fit(muestra[train_p2.FEATURES], muestra["target"])
        predicciones.append(modelo.predict(pd.DataFrame(rows)[train_p2.FEATURES]))

    np.testing.assert_array_equal(predicciones[0], predicciones[1])
