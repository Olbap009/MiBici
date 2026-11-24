# Experimentos y MLflow Projects (P1, P2 y P3)

---

## Experimentos base

Para ejecutar los experimentos base directamente:

- **P3 (Clustering de Estaciones — ejecuta directamente sobre los datos de la ingesta):**
  ```bash
  uv run python -m mibici.modeling.train_p3
  ```

- **P1 (Regresión de Demanda Diaria):**
  ```bash
  uv run python -m mibici.project_cli ingest --question P1 --build true
  uv run python -m mibici.modeling.train_p1
  ```

- **P2 (Clasificación de Presión Neta):**
  ```bash
  uv run python -m mibici.project_cli train --question P2 --model baseline
  ```

---

## MLflow Projects — propuesta común de P1, P2 y P3

[MLproject](../MLproject) ofrece `ingest`, `train` y `search`. Cada ejecución desde la carpeta del repositorio crea una corrida en el experimento `mibici-equipo23-mlprojects`. El proyecto declara Python 3.13 y dependencias en `uv.lock`.

Los datos **no** se incluyen en Git. Para P2 se añadió la cadena fija de DVC `p2_dataset → p2_movements → p2_examples` en [dvc.yaml](../dvc.yaml). Hay que ejecutar `dvc repro p2_examples`, revisar el `dvc.lock` producido y subir datos mediante `dvc push` desde una cuenta con acceso a GCS.

```bash
uv sync --locked
export MLFLOW_TRACKING_URI=http://127.0.0.1:5001
# En otra terminal: uv run --locked mlflow server --backend-store-uri sqlite:///mlflow_mibici.db --host 127.0.0.1 --port 5001
uv run --locked dvc pull
uv run --locked mlflow run . --env-manager local --experiment-name mibici-equipo23-mlprojects -e ingest -P question=P2
```

Si no existe `p2_examples.parquet`, pero sí los viajes corregidos y el catálogo, `-e ingest -P question=P2 -P build=true` reconstruye movimientos y ejemplos. Para versionarlos realmente en DVC ejecuta `uv run --locked dvc repro p2_examples` sobre la etapa completa y comparte el `dvc.lock` y el cache mediante `dvc push`. La etapa de ingesta fija `2023-11-01` a `2026-09-30`; evita cambiar los cortes temporales entre corridas.

```bash
# P2: baseline, árbol individual y búsqueda anidada (tres árboles + baseline).
uv run --locked mlflow run . --env-manager local --experiment-name mibici-equipo23-mlprojects -e train -P question=P2 -P model=baseline
uv run --locked mlflow run . --env-manager local --experiment-name mibici-equipo23-mlprojects -e train -P question=P2 -P model=tree -P max_depth=5 -P min_samples_leaf=100 -P class_weight=balanced
uv run --locked mlflow run . --env-manager local --experiment-name mibici-equipo23-mlprojects -e search -P question=P2 -P seed=42 -P sample_fraction=0.05

# P1: validar o reconstruir serie de demanda; luego ejecutar variantes.
uv run --locked mlflow run . --env-manager local --experiment-name mibici-equipo23-mlprojects -e ingest -P question=P1 -P build=true
uv run --locked mlflow run . --env-manager local --experiment-name mibici-equipo23-mlprojects -e train -P question=P1 -P model=rf -P max_depth=6 -P min_samples_leaf=8 -P n_estimators=200
uv run --locked mlflow run . --env-manager local --experiment-name mibici-equipo23-mlprojects -e search -P question=P1

# P3: agrupación por estaciones; model=agglomerative no permite inferencia nueva.
uv run --locked mlflow run . --env-manager local --experiment-name mibici-equipo23-mlprojects -e train -P question=P3 -P model=kmeans -P k=4
uv run --locked mlflow run . --env-manager local --experiment-name mibici-equipo23-mlprojects -e search -P question=P3
```

### Criterios de evaluación y Model Registry

Las métricas de P2 se calculan por estación e intervalo de 30 minutos. La etiqueta indica **presión neta estimada a partir de viajes**, no que existan cero bicicletas o cero anclajes reales. La búsqueda usa `train` para ajustar, `validation` para seleccionar y abre `test` una vez para el ganador. El criterio es `balanced_accuracy` de validación, siempre que el recall de cada clase de presión sea al menos `0.10`. Las curvas PR usan un histograma de 200 intervalos y son aproximadas; la matriz de confusión y las métricas son exactas.

Para registrar la versión elegida (una vez revisadas métricas y artefactos), usa el `run_id` impreso por cada script, o permite que el pipeline `search` lo registre de forma automatizada. El alias `champion` distingue la mejor versión académica y promueve el modelo al estado de producción.

Los nombres oficiales de los modelos registrados son:
- **P1 (Demanda Diaria):** `mibici-equipo23-p1-demanda`
- **P2 (Riesgo de Desbalance):** `MiBici_Equipo23_P2_Presion_Proxy_Academica` (y alias `mibici-equipo23-p2-riesgo`)
- **P3 (Segmentación de Estaciones):** `mibici-equipo23-p3-grupos` (y alias `MiBici_Equipo23_P3_Estaciones`)

Para registrar manualmente una versión elegida:
```bash
uv run --locked python -m mibici.register_project_models --question P1 --run-id RUN_ID_GANADOR_P1
uv run --locked python -m mibici.register_project_models --question P2 --run-id RUN_ID_GANADOR_P2
uv run --locked python -m mibici.register_project_models --question P3 --run-id RUN_ID_GANADOR_P3
```

El registro comprueba que el alias resuelva a la nueva versión y que el modelo cargado prediga una fila de ejemplo:
```python
import mlflow
# Carga directa del modelo en producción por nombre y alias champion:
modelo_p1 = mlflow.sklearn.load_model("models:/mibici-equipo23-p1-demanda@champion")
modelo_p2 = mlflow.sklearn.load_model("models:/MiBici_Equipo23_P2_Presion_Proxy_Academica@champion")
modelo_p3 = mlflow.sklearn.load_model("models:/mibici-equipo23-p3-grupos@champion")
```

P3 utiliza K-Means para conservar la capacidad inductiva (`predict`) ante nuevas estaciones. Las búsquedas P1, P2 y P3 ejecutan candidatos organizados como corridas anidadas (*nested runs*). P1 evalúa el conjunto de prueba una sola vez para el ganador seleccionado por MAE de validación. P2 optimiza Balanced Accuracy con umbral mínimo de recall. P3 selecciona K-Means con $k=4$ grupos enriquecidos con 9 variables funcionales y operativas de flujo neto y perfiles horarios.
