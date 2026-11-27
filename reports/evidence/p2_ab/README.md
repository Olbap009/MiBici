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

La [auditoría de linaje del 27 de noviembre](../p2_lineage/README.md)
comprobó la identidad del artefacto remoto y el empaquetado. Los metadatos
y los artefactos disponibles no identifican el dataset histórico de A;
el hash del archivo de evaluación no debe atribuirse a su entrenamiento.

**B** es la versión 2 del mismo modelo, registrada en la corrida
`2be806abea9245c5afcbee36c660c9c7` con el alias `challenger`. Se fijó un
árbol de profundidad 3, pesos balanceados y semilla 42. Se tomó una muestra
uniforme de aproximadamente 5 % de `train` y `validation` (844,359 de
16,903,453 filas elegibles). Cada fila de entrenamiento tenía `prediction_time`
anterior al 1 de julio de 2026 y una ventana de etiqueta cerrada antes o en
ese corte. La configuración de la candidata se fijó antes de evaluar sus
resultados.

## Resultados verificados con el registro de MLflow

Se cargaron directamente de DagsHub las versiones 1 y 2 por número y se
ejecutaron sobre las mismas filas de evaluación. El hash del dataset, las
matrices de confusión y todas las métricas coincidieron exactamente con la
[evaluación local inicial](comparacion.json).

| Métrica | A, versión 1 | B, versión 2 |
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
de confusión, los identificadores de ambas corridas y el hash del archivo
están en [`comparacion_registro.json`](comparacion_registro.json).

## Reproducir la comparación

Ejecutar desde la raíz del repositorio con el entorno de `uv.lock` y el archivo
`data/processed/p2_examples.parquet` de la etapa `p2_examples` de DVC.
Usar `--dataset` si el Parquet está fuera del directorio predeterminado.

```bash
modelo=MiBici_Equipo23_P2_Presion_Proxy_Academica
uv run --locked python -m mibici.modeling.compare_p2_versions \
  --tracking-uri https://dagshub.com/bryan-s-ortega/TC5061-Proyecto-Equipo23.mlflow \
  --model-a "models:/${modelo}/1" \
  --model-b "models:/${modelo}/2" \
  --output /tmp/mibici-p2-comparacion-registro.json
```

Para reproducir el entrenamiento de B y la comparación local inicial,
omitir las opciones de registro. La ruta de `--save-candidate` debe ser
nueva y guarda B como un artefacto estándar de MLflow.

```bash
uv run --locked python -m mibici.modeling.compare_p2_versions \
  --save-candidate /tmp/mibici-p2-candidata \
  --output /tmp/mibici-p2-comparacion.json
```
