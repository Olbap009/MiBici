# P2. Presión futura en estaciones de MiBici

Autor: Miguel Ángel Durán Betancourt  
Equipo: 23  
Rama: feat/p2-riesgo-estaciones

## Pregunta y alcance

¿Una estación estará en riesgo de quedarse sin bicicletas o sin anclajes
disponibles en un periodo futuro?

Se operacionaliza como clasificación de presión neta durante los próximos
30 minutos. No se dispone de inventarios históricos ni movimientos de
redistribución, por lo que no se predice directamente una estación vacía
o llena.

Presión = (salidas del intervalo - llegadas del intervalo) / capacidad.

- Presión >= 0.30: presion_sin_bicicletas.
- Presión <= -0.30: presion_sin_anclajes.
- En otro caso: sin_presion_neta_elevada.

El umbral es una decisión inicial del experimento, no un límite operativo
validado.

## ML Canvas

| Componente | Definición |
| --- | --- |
| Problema | Anticipar desequilibrios de movimientos en estaciones. |
| Usuario propuesto | Personal de supervisión y redistribución. |
| Decisión | Priorizar estaciones para revisión humana. |
| Unidad | Estación y momento de predicción. |
| Horizonte | Próximos 30 minutos. |
| Datos | Viajes históricos y catálogo de estaciones. |
| Entradas | Movimientos anteriores, horario y capacidad. |
| Salida | Tres clases de presión neta. |
| Evaluación | F1 macro, balanced accuracy y precision/recall por clase. |
| Criterio operativo | Pendiente de definir costos de falsas alarmas y omisiones. |
| Limitación | La presión neta no equivale al inventario disponible. |

## Datos y preparación

Periodo reconstruido: 2023-11-01 a 2026-09-30.

Se corrigió la interpretación ambigua de fechas día/mes/año mediante
formatos explícitos y validación del mes de origen.

| Concepto | Cantidad |
| --- | ---: |
| Viajes reconstruidos | 13,238,646 |
| Copias adicionales por identificador eliminadas | 758 |
| Registros únicos con duración no positiva excluidos | 37,002 |
| Viajes únicos con duración válida | 13,200,886 |
| Eventos de salida válidos | 13,198,927 |
| Eventos de llegada válidos | 13,198,763 |
| Ejemplos estación-intervalo | 18,914,362 |

Los extremos sin capacidad válida se excluyeron por separado.
La duración cero puede reflejar precisión temporal limitada; su exclusión
es una decisión provisional.

Estas cifras corresponden a la reconstrucción con fechas corregidas.
Sustituyen, para esta versión, los conteos iniciales anteriores a esa
corrección.

## Variables y partición

Variables predictoras:

- departures_prev_30m y arrivals_prev_30m.
- departures_prev_2h y arrivals_prev_2h.
- hour, minute y day_of_week.
- capacity.

Las ventanas usan intervalos anteriores al momento de predicción.
Se exige historial de siete días y actividad previa.
La etiqueta, target_end, split e identificador de estación no se usan
como predictores de los árboles ejecutados.

| Partición | Periodo | Filas |
| --- | --- | ---: |
| Entrenamiento | Desde noviembre de 2023, tras historial inicial, hasta diciembre de 2025 | 13,677,649 |
| Validación | Enero a junio de 2026 | 3,225,804 |
| Prueba | Julio a septiembre de 2026 | 2,010,909 |

El objetivo debe terminar dentro de su partición.
Prueba permanece reservada.

## Experimentos

Baseline: clase mayoritaria del entrenamiento.

Árboles: max_depth=5, min_samples_leaf=100, semilla 42.
Muestreo Bernoulli uniforme aproximado del 5 % del entrenamiento.
Validación completa para los tres modelos.

Solo se cambió class_weight entre ambos árboles.

| Métrica | Baseline | Árbol balanced | Árbol none |
| --- | ---: | ---: | ---: |
| Accuracy | 0.994542 | 0.744202 | 0.994456 |
| Balanced accuracy | 0.333333 | 0.637990 | 0.350464 |
| F1 macro | 0.332421 | 0.309572 | 0.362679 |
| Recall presión sin bicicletas | 0 | 0.726379 | 0 |
| Recall presión sin anclajes | 0 | 0.442480 | 0.051626 |
| Precision presión sin bicicletas | Sin alertas | 0.008737 | 0 |
| Precision presión sin anclajes | Sin alertas | 0.030934 | 0.376892 |

El cero de precision debe interpretarse con la matriz de confusión;
no distingue por sí solo ausencia de alertas de alertas incorrectas.

## Interpretación

El baseline obtiene alta accuracy por el desbalance, pero no detecta
ninguno de los 17,608 ejemplos de presión de validación.

El árbol balanceado detecta más presión, con numerosas falsas alarmas.
El árbol sin balanceo tiene el mayor F1 macro observado, pero detecta
solo el 5.16 % de presión sin anclajes y ningún caso sin bicicletas.

Ninguna configuración justifica automatizar redistribuciones.
No se demuestra significancia estadística ni superioridad universal.

## Trazabilidad

Experimento MLflow: mibici-equipo23.

| Corrida | Run ID |
| --- | --- |
| Baseline | ef58bbe3440342048ed802dc902abc58 |
| Árbol balanced | 1aa8b7ede8304962aa894641df418f2d |
| Árbol none | 19890a56549a4b3c9b836a3938fce9eb |

Commits identificados:

- 24ace70: diagnóstico inicial.
- 31cf206: corrección de fechas y pruebas.
- ae1fd80: variables y baseline.
- e5c9f86: árbol parametrizable y evaluación.

Las corridas guardan una copia del código y el estado de trabajo.
El commit posterior no debe confundirse con el commit registrado al
ejecutar cada experimento.

## Limitaciones y pendientes

- Integrar datos corregidos y derivados en el flujo compartido de DVC.
- Confirmar capacidad histórica y cobertura por estación.
- Revisar disponibilidad temporal de datos para una operación en línea:
  la limpieza por duración utiliza información conocida al finalizar.
- Evaluar estabilidad por periodo y estación.
- Definir costos operativos y criterio de selección antes de evaluar prueba.
- Adjuntar capturas reales de comparación y artefactos.
- Agregar enlace al PR y evidencia de revisión.

## Referencias

MiBici. (s. f.). Datos abiertos. https://mibici.net/es/datos-abiertos/

MLflow. (s. f.). mlflow.sklearn.
https://mlflow.org/docs/latest/api_reference/python_api/mlflow.sklearn.html

Scikit-learn developers. (s. f.). DecisionTreeClassifier.
https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html
