# Monitoreo de drift y calidad de datos de P2

Se compararon julio, agosto y septiembre de dos años consecutivos para alinear
la temporada. La selección usa `prediction_time` con límites de inicio
inclusivos y de fin exclusivos.

| Conjunto | Partición | Intervalo | Filas totales | Filas analizadas con Evidently |
| --- | --- | --- | ---: | ---: |
| Referencia de entrenamiento | `train` | 2025-07-01 a 2025-10-01 | 1,620,407 | 50,000 |
| Periodo posterior | `test` | 2026-07-01 a 2026-10-01 | 2,010,909 | 50,000 |

Se tomó una muestra aleatoria uniforme sin reemplazo de cada periodo,
con semilla 42 y sin seleccionar por la clase. Se compararon las ocho
variables del contrato de predicción de P2. La hora, el minuto y el día de
la semana se trataron como categorías de calendario. Los conteos de
viajes en ventanas de 30 minutos y dos horas, y la capacidad, se trataron
como variables numéricas. El resumen de calidad incluye valores faltantes,
estadísticas descriptivas y tipos de origen. La distribución de la etiqueta
`target` se calculó por separado sobre todas las filas de cada periodo.

## Reproducir el reporte

En la raíz del repositorio, con Python 3.13:

```bash
python3.13 -m venv .venv-evidently
source .venv-evidently/bin/activate
python -m pip install -r requirements-evidently.txt
python -m mibici.monitor_p2_drift
```

La entrada predeterminada es `data/processed/p2_examples.parquet`. Si ya se
cuenta con el archivo en otra ubicación, se puede especificar con `--dataset`.
Para reconstruirlo con los insumos del proyecto, consultar la
[sección de MLflow Projects](../../../README.md#mlflow-projects--propuesta-común-de-p1-p2-y-p3)
y la etapa
`p2_examples` de [DVC](../../../dvc.yaml). El archivo utilizado para esta
ejecución coincide con el MD5 de [`dvc.lock`](../../../dvc.lock)
(`2b49d47ce98f26839abe4382546aa9b1`).

El comando genera `evidently_p2.html` (reporte interactivo) y
[`evidently_p2.json`](evidently_p2.json) (métricas de Evidently, trazabilidad
del dataset y distribución agregada de las clases). El HTML se genera localmente.

## Evidencia de la ejecución

- [Resumen de drift de las ocho variables](drift_variables.png).
- [Distribución y estadísticas descriptivas de la capacidad](drift_capacity.png).
- [Resumen de calidad de datos](data_quality.png).

Evidently marcó **0 de 8 variables** con drift en la muestra. Se usó distancia
de Wasserstein normalizada para las numéricas y distancia de Jensen–Shannon
para las categóricas, con umbral de 0.10 por variable en esta ejecución.
`capacity` fue la más cercana a su umbral (0.099484). Ambas muestras registraron
cero valores faltantes en las ocho variables.

En el recuento de los periodos completos, las dos clases de presión sumaron
11,565 de 1,620,407 filas (0.714 %) en 2025 y 9,487 de 2,010,909 filas (0.472 %)
en 2026. Es un cambio descriptivo en la frecuencia de la etiqueta de P2. El
desempeño del modelo se evalúa en la comparación de versiones.
