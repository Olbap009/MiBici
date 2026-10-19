# Evidencia de MLflow — Equipo 23

## Experimentos por Pregunta

- **P1 (Regresión de Demanda Diaria):** `mibici-equipo23-p1` (Runs: `P1_baseline_lag7`, `P1_random_forest_candidato`)
- **P2 (Clasificación de Presión Neta):** `mibici-equipo23-p2` (Runs: `P2_baseline_mayoritario`, `P2_arbol_d5_balanced`)
- **P3 (Clustering de Estaciones):** `mibici-equipo23-p3` (Runs: `P3_kmeans_baseline_k4`, `P3_kmeans_candidato_k4`)
- **Consolidado General:** `mibici-equipo23`

Abrir la interfaz local con:

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlruns.db --port 5001
```

Luego visitar http://127.0.0.1:5001.

## Evidencia guardada en `reports/evidence/`

1. **Lista general de experimentos:** `reports/evidence/mlflow_experimentos_lista.png`
2. **Experimento P1:** `reports/evidence/mlflow_experimento_p1.png`
3. **Experimento P2:** `reports/evidence/mlflow_experimento_p2.png`
4. **Experimento P3:** `reports/evidence/mlflow_experimento_p3.png`
5. **Lista consolidada de corridas:** `reports/evidence/mlflow_1_lista_runs.png` y `mlflow_lista_runs.png`
6. **Detalle de corrida (tags, params, métricas):** `reports/evidence/mlflow_2_detalle_run.png`
7. **Artefactos visuales registrados:** `reports/evidence/mlflow_3_artefactos.png` y `mlflow_detalle_p3_artefacto.png`
8. **Comparación de corridas:** `reports/evidence/mlflow_4_comparacion_runs.png` y `mlflow_comparacion_p1.png`


Los resultados reproducidos el 17 de octubre de 2026 fueron:

| Pregunta | Resultado |
|---|---:|
| P1 MAE | 11.6304 |
| P1 candidato MAE | 6.5447 |
| P1 candidato RMSE | 12.4127 |
| P2 accuracy | 0.6244 |
| P2 F1 | 0.7688 |
| P2 candidato accuracy | 0.8282 |
| P2 candidato F1 | 0.8499 |
| P3 silhouette | 0.4982 |

Cada run guarda `seed`, rango de fechas, tag de equipo, pregunta y commit de
Git. P2 es una etiqueta proxy basada en demanda/capacidad, no inventario real.
