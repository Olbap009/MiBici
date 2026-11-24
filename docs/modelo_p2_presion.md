# Modelo desplegado: Clasificación de presión en estaciones (P2)

Este documento explica qué pregunta de negocio responde el modelo que sirve la API REST (`MiBici_Equipo23_P2_Presion_Proxy_Academica`), cómo transforma los viajes en variables predictivas y qué limitaciones operativas tiene.

---

## 1. ¿Qué pregunta responde?

> **¿En los próximos 30 minutos, una estación de MiBici presentará riesgo de desbalance fuerte por exceso de salidas o exceso de llegadas?**

En un sistema de bicicleta pública como **MiBici** (Área Metropolitana de Guadalajara), los traslados son asimétricos según la hora y la zona (por ejemplo, viajes hacia centros laborales o universidades en horas pico). Anticipar estos desbalances con **30 minutos de margen** ayuda a priorizar el **rebalanceo operativo** antes de que una estación quede vacía o saturada.

---

## 2. Clases de salida

El modelo realiza **clasificación multiclase** con tres categorías posibles ([mibici/api/schemas.py](../mibici/api/schemas.py)):

| Clase | Significado | Impacto operativo |
| :--- | :--- | :--- |
| **`sin_presion_neta_elevada`** | Salidas y llegadas equilibradas respecto a la capacidad | Operación normal; no requiere alerta |
| **`presion_sin_bicicletas`** | Salidas netas elevadas frente a llegadas | Riesgo de estación **vacía** (usuarios sin bicicleta disponible) |
| **`presion_sin_anclajes`** | Llegadas netas elevadas frente a salidas | Riesgo de estación **saturada** (usuarios sin espacio para devolver) |

---

## 3. ¿Cómo funciona? (Variables de entrada)

Al inicio de cada intervalo de 30 minutos, el modelo recibe **8 variables** disponibles antes de que ocurra la ventana a predecir (evitando fuga de información futura):

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| `departures_prev_30m` | Entero $\ge 0$ | Bicicletas que salieron de la estación en los últimos 30 minutos |
| `arrivals_prev_30m` | Entero $\ge 0$ | Bicicletas que llegaron a la estación en los últimos 30 minutos |
| `departures_prev_2h` | Entero $\ge 0$ | Salidas acumuladas en las últimas 2 horas |
| `arrivals_prev_2h` | Entero $\ge 0$ | Llegadas acumuladas en las últimas 2 horas |
| `hour` | Entero `0–23` | Hora local de inicio del intervalo |
| `minute` | `0` o `30` | Minuto de inicio del intervalo |
| `day_of_week` | Entero `0–6` | Día de la semana (`0` = lunes, `6` = domingo) |
| `capacity` | Entero $> 0$ | Capacidad total de anclajes de la estación |

Con estas variables, el clasificador (`DecisionTreeClassifier` empaquetado desde el Registry en `models/p2_champion/`) estima la clase de presión para los siguientes 30 minutos.

---

## 4. Alcance y limitación importante (indicador proxy)

- **Dataset de entrenamiento y evaluación:** el modelo utiliza `data/processed/p2_examples.parquet` (generado por la etapa `p2_examples` de [dvc.yaml](../dvc.yaml) a partir de los viajes individuales descargados de MiBici en `trips_fechas_corregidas.parquet`). Cada fila representa una estación en un intervalo de 30 minutos.
- **Es un indicador proxy basado en flujos:** las etiquetas se construyen a partir de viajes históricos (`departures` y `arrivals`) y la capacidad de la estación; **no miden el inventario físico real** de bicicletas o anclajes en tiempo real.
- **Fuente histórica vs. operación en vivo:** el portal abierto de MiBici publica los viajes cerrados mensualmente, por lo que el histórico sirve para entrenamiento, evaluación y comparación retrospectiva (como el ejercicio A/B entre versión `1` `champion` y versión `2` `challenger`). En un entorno productivo en vivo, los contadores `prev_30m` y `prev_2h` vendrían de la telemetría en tiempo real de las estaciones.
