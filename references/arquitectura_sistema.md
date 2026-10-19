# Arquitectura del Sistema MLOps — Equipo 23

Este documento describe la arquitectura técnica integral propuesta para el sistema de aprendizaje automático de MiBici (Área Metropolitana de Guadalajara), atendiendo la actividad 5 y los requisitos de la Parte B de la rúbrica.

![Diagrama de Arquitectura del Sistema MLOps](diagrama_arquitectura.png)

---

## 1. Componentes de la Solución y Conexiones

El flujo de información opera a través de 7 capas modulares desacopladas:

1. **Fuentes Externas de Datos:**
   - Portal de datos abiertos de MiBici (`https://mibici.net/es/datos-abiertos/`).
   - Archivos CSV mensuales de viajes históricos y catálogos de nomenclatura de estaciones.
2. **Ingesta y Estandarización (`mibici.dataset`):**
   - Interfaz CLI desarrollada con `Typer`.
   - Lectura por bloques y streaming con `PyArrow` y `pandas`.
   - Limpieza de codificaciones mixtas (`utf-8`, `utf-8-sig`, `latin-1`), normalización de identificadores y tipos temporales (`pd.to_datetime`).
3. **Almacenamiento y Versionado:**
   - **Formato Parquet:** `data/processed/trips.parquet` (almacenamiento columnar eficiente, compresión Snappy y tipado estricto).
   - **DVC (Data Version Control):** Rastreo de datos en [`dvc.yaml`](../dvc.yaml) y [`dvc.lock`](../dvc.lock) respaldado en bucket de Google Cloud Storage (`gs://mibici-mlops-project`).
   - **Manifiesto SHA-256:** [`references/data_manifest.csv`](data_manifest.csv) para auditoría criptográfica complementaria e integridad de microdatos.
4. **Feature Engineering Reutilizable (`mibici.features`):**
   - Funciones modulares con docstrings detallados que evitan fuga de información futura (*data leakage*):
     - **P1:** Rezagos temporales (`lag_1`, `lag_7`), variables de calendario y estacionalidad.
     - **P2:** Conteo de movimientos por ventana temporal de 30 minutos y balance neto respecto a capacidad.
     - **P3:** Extracción de firma de movilidad por estación (proporción matutina, mediodía, vespertina, fin de semana, ratio de flujo neto y coordenadas).
   - Parámetros, rutas y semillas centralizadas en [`mibici.config`](../mibici/config.py).
5. **Modelado y Experimentación:**
   - **P1 (Regresión de demanda):** Baseline autorregresivo semanal vs. `RandomForestRegressor`.
   - **P2 (Clasificación de riesgo de desbalance):** Regla de clase mayoritaria vs. `DecisionTreeClassifier` balanceado.
   - **P3 (Clustering no supervisado):** `KMeans` ($k=4$) vs. `AgglomerativeClustering`.
6. **MLOps Tracking y Reproducibilidad (MLflow):**
   - Servidor unificado bajo el experimento `mibici-equipo23`.
   - Registro de parámetros (semilla, ventana de fechas, hash SHA-256 de los datos, hiperparámetros).
   - Métricas clave (MAE, RMSE, $R^2$, Accuracy, F1 macro, Silhouette Score, Davies-Bouldin, Calinski-Harabasz).
   - Etiquetas obligatorias: `equipo: 23`, `pregunta: P1|P2|P3`, `git_commit: <sha>`.
   - Artefactos registrados: modelos serializados, mapas espaciales, gráficos de perfiles, curvas de codo y matrices de confusión.
7. **Consumo y Toma de Decisiones:**
   - **AMIM (Planeación Urbana):** Expansión de estaciones y adición física de anclajes basada en clusters de movilidad.
   - **BKT Bici Pública (Operaciones):** Rutas logísticas dinámicas de camionetas de rebalanceo entre polos expulsores y receptores.
   - **Gestión de Mantenimiento:** Previsión de demanda futura a nivel de red para asignación óptima de personal.

---

## 2. Justificación de Herramientas Elegidas

Con base en las lecturas de la semana y buenas prácticas de ingeniería de software para ML:

* **uv (Astral):** Gestor de paquetes y entornos virtuales de alto rendimiento en Rust. Reemplaza pip/virtualenv proporcionando resolución determinista de dependencias mediante `uv.lock`.
* **PyArrow y Apache Parquet:** Formato columnar binario optimizado para analítica que reduce drásticamente el espacio en disco (~390 MB vs. gigabytes en CSV) y permite escaneos por lotes sin saturar la memoria RAM.
* **DVC (Data Version Control) + Google Cloud Storage:** Separa el versionado de código (Git) del versionado de datos pesados (Object Storage), permitiendo sincronizar datasets exactos con `dvc pull` sin ensuciar el repositorio.
* **MLflow Tracking:** Plataforma estándar de trazabilidad que vincula cada corrida con el commit de Git exacto, garantizando reproducibilidad completa de experimentos y gobierno de modelos.
* **Scikit-learn:** Biblioteca madura con APIs estandarizadas (`fit`, `predict`, `score`), validadores de métricas y transformadores reproducibles.
* **Ruff & Pre-commit:** Herramientas de aseguramiento de calidad de código que imponen estándares PEP 8, longitud de línea (99 caracteres) y orden de importaciones automáticamente antes de cada commit.
