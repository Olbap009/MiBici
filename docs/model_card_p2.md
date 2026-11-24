# Model Card — `MiBici_Equipo23_P2_Presion_Proxy_Academica`

## 1. Detalles del modelo
- **Nombre en MLflow Registry:** `MiBici_Equipo23_P2_Presion_Proxy_Academica`
- **Versión vigente en producción:** Versión `1` (alias `champion`)
- **Run ID de origen (`champion`):** `55225195968642979a681bf751d9e2f8`
- **Versión candidata evaluada:** Versión `2` (alias `challenger`, Run ID `2be806abea9245c5afcbee36c660c9c7`)
- **Tipo de problema:** Clasificación multiclase (3 clases)
- **Algoritmo:** `DecisionTreeClassifier` (scikit-learn), empaquetado en `models/p2_champion/`
- **MLflow Tracking / Registry:** `https://dagshub.com/bryan-s-ortega/TC5061-Proyecto-Equipo23.mlflow`
- **Autores:** Equipo 23 — TC5061 (Miguel Ángel Durán Betancourt, Juan Pablo Islas Guzmán, Bryan Steve Ortega Castillo, Kevin Rogelio Rodriguez Magaña)

---

## 2. Uso previsto y fuera de alcance
- **Uso previsto:** Generar alertas tempranas cada 30 minutos sobre **presión neta de movimientos** en estaciones de MiBici (Guadalajara) para apoyar la planeación de rebalanceo operativo.
- **Fuera de alcance:**
  - No mide el inventario físico real de bicicletas o anclajes disponibles en tiempo real (es un **indicador proxy** derivado de flujos históricos de viajes y capacidad).
  - Con los datos públicos mensuales de MiBici no realiza inferencia en vivo sin conectarse a la telemetría interna de estaciones.

---

## 3. Datos, linaje y variables
- **Fuente:** Portal de datos abiertos de MiBici (`mibici.net/es/datos-abiertos/`), versionado con DVC en DagsHub ([dvc.yaml](../dvc.yaml), [dvc.lock](../dvc.lock)).
- **Pipeline de datos:** `p2_dataset` (`trips_fechas_corregidas.parquet`, 2023-11-01 a 2026-09-30) → `p2_movements` → `p2_examples` (`data/processed/p2_examples.parquet`, SHA-256 `65e71b0f8d489210ce185ac3e3de0ab85c0c50df75473128aeb5e32e61a477a3`).
- **Variables de entrada (8):**
  - Flujos previos sin fuga temporal: `departures_prev_30m`, `arrivals_prev_30m`, `departures_prev_2h`, `arrivals_prev_2h`
  - Calendario: `hour` (`0–23`), `minute` (`0` o `30`), `day_of_week` (`0–6`)
  - Estación: `capacity` ($> 0$)
- **Clases de salida (3):** `sin_presion_neta_elevada`, `presion_sin_bicicletas`, `presion_sin_anclajes`.

---

## 4. Evaluación y comparación A/B retrospectiva
Evaluación sobre exactamente las mismas **2,010,909 filas** de la partición `test` (`2026-07-01` a `2026-10-01`), documentada en [reports/evidence/p2_ab/README.md](../reports/evidence/p2_ab/README.md):

| Métrica | Versión 1 (`champion`) | Versión 2 (`challenger`) |
| --- | ---: | ---: |
| **Balanced accuracy** | 46.76 % | 60.37 % |
| **Precisión `presion_sin_bicicletas`** | 1.97 % | 1.15 % |
| **Recall `presion_sin_bicicletas`** | 31.15 % | 53.24 % |
| **Precisión `presion_sin_anclajes`** | 9.09 % | 0.70 % |
| **Recall `presion_sin_anclajes`** | 12.96 % | 58.57 % |
| **Alertas emitidas totales** | 79,902 | 622,745 |
| **Alertas en filas sin presión** | 76,584 | 614,069 |

**Decisión de gobernanza:** Se mantiene el alias `champion` en la **versión 1** y `challenger` en la **versión 2**. Aunque la versión 2 eleva la *balanced accuracy* (+13.61 pp) y el *recall* de ambas clases de presión, multiplica ~8× las falsas alertas (614,069 frente a 76,584), superando el umbral aceptable de alertas falsas definido en [references/p2_drift_ab_protocolo.md](../references/p2_drift_ab_protocolo.md).

---

## 5. Monitoreo, operación y FinOps
- **Data drift (Evidently):** Comparación reproducible julio–septiembre 2025 vs 2026 (50,000 filas por periodo, semilla `42`) en [reports/evidence/p2_drift/README.md](../reports/evidence/p2_drift/README.md).
- **Monitoreo en línea:** Persistencia de cada predicción en PostgreSQL ([mibici/api/db.py](../mibici/api/db.py)) y visualización en Grafana (`/monitoring/`).
- **Rendimiento y FinOps (Locust):** 1,364 solicitudes (23.49 RPS, p95 21 ms) con 5 usuarios y 7,179 solicitudes (119.96 RPS, p95 10 ms) con 25 usuarios, **0 fallos**, costo estimado de `~3.89e-7` a `~7.61e-8` USD/inferencia sobre referencia AWS Lightsail de 24 USD/mes ([reports/evidence/finops/README.md](../reports/evidence/finops/README.md)).
