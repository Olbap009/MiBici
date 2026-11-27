# Protocolo previo: drift y comparación de versiones P2

## Pregunta

¿Cambiaron las variables de entrada de P2 entre dos periodos comparables?
Si cambiaron, ¿una segunda versión del modelo mejora el desempeño en el
periodo posterior?

P2 clasifica presión neta de movimientos. Sus etiquetas son un proxy:
no representan el inventario físico observado de bicicletas o anclajes.

## Dataset y periodos fijados

Fuente: `data/processed/p2_examples.parquet`. Los límites son inclusivos
al inicio y exclusivos al final; se usa `prediction_time`.

| Uso | Partición | Periodo | Filas verificadas |
| --- | --- | --- | ---: |
| Referencia de drift | train | 2025-07-01 a 2025-10-01 | 1,620,407 |
| Periodo actual y evaluación A/B | test | 2026-07-01 a 2026-10-01 | 2,010,909 |

Se comparan julio, agosto y septiembre de dos años consecutivos para
reducir la confusión por temporada. Aun así, cambios en estaciones,
capacidad u operación podrían explicar parte del drift.

## Reporte de Evidently

Comparar únicamente las ocho variables disponibles al predecir:
`departures_prev_30m`, `arrivals_prev_30m`, `departures_prev_2h`,
`arrivals_prev_2h`, `hour`, `minute`, `day_of_week` y `capacity`.

Generar drift por variable y calidad de datos. Para mantener manejable
el reporte, tomar una muestra aleatoria reproducible de hasta 50,000 filas
de cada periodo, con semilla 42, sin seleccionar por la etiqueta `target`.
Registrar tamaño, semilla y método de muestreo. Comparar también faltantes,
tipos y rangos. Reportar por separado la proporción de cada clase.

Drift estadístico indica cambio en la distribución de entradas; por sí
solo no demuestra que haya empeorado la calidad de las predicciones.

## Comparación retrospectiva de versiones

- Versión A: versión 1 del modelo registrado
  `MiBici_Equipo23_P2_Presion_Proxy_Academica`.
- Versión B: nueva versión del MISMO nombre en MLflow Model Registry.
  Documentar corrida, configuración, datos y fecha máxima de entrenamiento.
- La versión B puede incorporar datos hasta 2026-06-30. No puede usar
  filas del periodo de evaluación iniciado el 2026-07-01 para entrenar,
  seleccionar parámetros o ajustar umbrales.
- Cargar ambas versiones por número fijo, no mediante el alias mutable
  `champion`, y evaluarlas sobre exactamente las mismas 2,010,909 filas
  del periodo actual. Registrar el identificador/hash del dataset.
- Comparar balanced accuracy, precisión y recall por cada clase de presión,
  matriz de confusión y cantidad de alertas emitidas. La accuracy total
  no basta porque predominan los casos sin presión elevada.
- Definir la configuración de B antes de consultar sus resultados en test.
  Mantener `champion` sin cambios hasta que el equipo revise la evidencia.

Este ejercicio es una comparación retrospectiva sobre datos históricos;
no es un experimento A/B en línea con asignación aleatoria de usuarios.
La versión A ya fue evaluada anteriormente en parte de la partición test:
se debe declarar esa exposición al interpretar el resultado.

## Regla para la recomendación

Recomendar B sólo si mejora el equilibrio entre clases sin aumentar de
forma inaceptable las alertas falsas de presión. Informar el cambio de
cada métrica y sus limitaciones. Si sólo hay drift, o las métricas son
ambiguas, proponer seguimiento y evaluación adicional antes de cambiar
el modelo vigente.
