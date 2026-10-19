"""Pruebas unitarias para el módulo de Clustering P3."""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from mibici.features import extract_p3_station_features


def test_extract_p3_station_features_structure() -> None:
    # Datos sintéticos de viajes
    trips = pd.DataFrame(
        {
            "started_at": [
                "2026-01-01 08:30:00",
                "2026-01-01 08:45:00",
                "2026-01-01 18:15:00",
                "2026-01-03 14:00:00",  # Fin de semana (sábado)
            ],
            "ended_at": [
                "2026-01-01 08:40:00",
                "2026-01-01 09:00:00",
                "2026-01-01 18:30:00",
                "2026-01-03 14:15:00",
            ],
            "origin_station_id": [10, 10, 20, 10],
            "destination_station_id": [20, 20, 10, 20],
        }
    )

    # Datos sintéticos de nomenclatura
    nomenclature = pd.DataFrame(
        {
            "id": [10, 20],
            "name": ["Estacion A", "Estacion B"],
            "latitude": [20.67, 20.68],
            "longitude": [-103.35, -103.36],
            "dpcapacity": [15, 20],
        }
    )

    features = extract_p3_station_features(trips, nomenclature)

    assert len(features) == 2
    assert "pct_pico_matutino" in features.columns
    assert "pct_pico_vespertino" in features.columns
    assert "pct_fin_semana" in features.columns
    assert "ratio_flujo_neto" in features.columns
    assert "capacidad" in features.columns
    assert "viajes_promedio_diario" in features.columns

    # Para estación 10: 2 viajes en la mañana (8am), 1 en fin de semana de un total de 3 salidas
    row_10 = features.loc[10]
    assert row_10["pct_pico_matutino"] > 0.6
    assert row_10["pct_fin_semana"] > 0.3
    assert row_10["capacidad"] == 15


def test_clustering_kmeans_execution() -> None:
    # Simular matriz de características
    df_feat = pd.DataFrame(
        {
            "viajes_promedio_diario": [10.0, 50.0, 12.0, 48.0],
            "pct_pico_matutino": [0.4, 0.1, 0.45, 0.12],
            "pct_pico_vespertino": [0.1, 0.35, 0.12, 0.38],
            "pct_fin_semana": [0.2, 0.15, 0.22, 0.14],
            "ratio_flujo_neto": [-0.3, 0.4, -0.28, 0.39],
            "capacidad": [11, 23, 11, 23],
            "latitude": [20.67, 20.68, 20.671, 20.682],
            "longitude": [-103.35, -103.36, -103.351, -103.361],
        }
    )

    X_scaled = StandardScaler().fit_transform(df_feat)
    km = KMeans(n_clusters=2, random_state=42, n_init=5)
    labels = km.fit_predict(X_scaled)

    assert len(labels) == 4
    assert len(set(labels)) == 2
