# Comparación retrospectiva de versiones de P2

La evaluación usa las mismas 2,010,909 filas de la partición `test` de julio
a septiembre de 2026 para los dos modelos. La unidad es una estación en un
intervalo de 30 minutos. P2 predice una etiqueta proxy de presión neta de
movimientos. La evaluación corresponde a datos históricos etiquetados.

**A** es la versión 1 de `MiBici_Equipo23_P2_Presion_Proxy_Academica`.
La corrida `55225195968642979a681bf751d9e2f8` coincide con el artefacto
empaquetado en el repositorio. El árbol almacena 36 muestras en su nodo raíz.
La corrida consultada carece de metadatos sobre el dataset de entrenamiento.
Julio a septiembre de 2025 es la referencia del protocolo de drift, tomada de
la partición `train` de P2. Su uso exacto en el entrenamiento de A queda por
confirmar con el equipo.

**B** es una candidata entrenada y evaluada localmente. Se fijó un árbol de
profundidad 3, pesos balanceados y semilla 42. Se tomó una muestra uniforme de
aproximadamente 5 % de `train` y `validation` (844,359 de 16,903,453 filas
elegibles). Cada fila de entrenamiento tenía `prediction_time` anterior al
1 de julio de 2026 y una ventana de etiqueta cerrada antes o en ese corte.
La configuración de la candidata se fijó antes de evaluar sus resultados.

## Resultados preliminares

| Métrica | A, versión 1 | B, candidata local |
| --- | ---: | ---: |
| Balanced accuracy | 46.76 % | 60.37 % |
| Precisión de presión sin bicicletas | 1.97 % | 1.15 % |
| Recall de presión sin bicicletas | 31.15 % | 53.24 % |
| Precisión de presión sin anclajes | 9.09 % | 0.70 % |
| Recall de presión sin anclajes | 12.96 % | 58.57 % |
| Alertas de presión emitidas | 79,902 | 622,745 |
| Alertas emitidas en filas sin presión | 76,584 | 614,069 |

La candidata aumentó el recall de ambas clases de presión y elevó en
13.61 puntos porcentuales la balanced accuracy. Al mismo tiempo, las
alertas en filas sin presión fueron unas ocho veces más frecuentes
(614,069 frente a 76,584). Estos resultados quedan para la interpretación y
recomendación del equipo antes de cambiar el modelo vigente. Las matrices
de confusión y el hash del archivo están en [`comparacion.json`](comparacion.json).

## Reproducir la comparación

Ejecutar desde la raíz del repositorio con el entorno de `uv.lock` y el archivo
`data/processed/p2_examples.parquet` de la etapa `p2_examples` de DVC.

```bash
uv run --locked python -m mibici.modeling.compare_p2_versions \
  --save-candidate /tmp/mibici-p2-candidata \
  --output /tmp/mibici-p2-comparacion.json
```

Usar `--dataset` si el Parquet está fuera del directorio predeterminado.
La ruta de `--save-candidate` debe ser nueva y guarda un artefacto estándar
de MLflow para que el responsable del Registry pueda registrar B bajo el
mismo nombre de P2. La comparación de arriba usa ese modelo entrenado en
la misma ejecución y el artefacto de la versión 1 incluido en el repositorio.

## Registrar la candidata en MLflow

Ejecutar con una cuenta con acceso de escritura al registro de DagsHub, con
`MLFLOW_TRACKING_URI` apuntando al servidor del equipo. El comando crea una
versión para revisión y conserva el alias `champion` de la versión vigente.

```bash
uv run --locked python - /tmp/mibici-p2-candidata /tmp/mibici-p2-comparacion.json <<'PY'
import json
from pathlib import Path
import sys

import mlflow
from mlflow.models import Model
import mlflow.sklearn

artifact, evidence = map(Path, sys.argv[1:])
report = json.loads(evidence.read_text())
name = "MiBici_Equipo23_P2_Presion_Proxy_Academica"
mlflow.MlflowClient().get_registered_model(name)
mlflow.set_experiment("mibici-equipo23-p2")
with mlflow.start_run(run_name="P2_candidata_drift_ab"):
    mlflow.log_params({
        **report["B"]["params"],
        "dataset_sha256": report["dataset_sha256"],
        "training_cutoff": report["B"]["training_cutoff"],
        "sample_fraction": report["B"]["sample_fraction"],
        "train_rows_used": report["B"]["train_rows_used"],
    })
    mlflow.log_dict(report, "comparacion.json")
    logged = mlflow.sklearn.log_model(
        sk_model=mlflow.sklearn.load_model(str(artifact.resolve())),
        name="modelo",
        signature=Model.load(str(artifact / "MLmodel")).signature,
        serialization_format="cloudpickle",
    )
    candidate = mlflow.register_model(logged.model_uri, name)
    print(f"Versión asignada a B: {candidate.version}")
PY
```

Una vez registrada B, ejecutar la comparación con las dos versiones fijas.
Sustituir `NÚMERO_B` por la versión asignada por MLflow.

```bash
modelo=MiBici_Equipo23_P2_Presion_Proxy_Academica
uv run --locked python -m mibici.modeling.compare_p2_versions \
  --tracking-uri https://dagshub.com/bryan-s-ortega/TC5061-Proyecto-Equipo23.mlflow \
  --model-a "models:/${modelo}/1" \
  --model-b "models:/${modelo}/NÚMERO_B" \
  --output /tmp/mibici-p2-comparacion-registro.json
```
