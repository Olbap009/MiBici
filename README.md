# MiBici — Proyecto MLOps (Equipo 23)

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Plantilla%20de%20proyecto-328F97?logo=cookiecutter" />
</a>

Proyecto de MLOps con datos del sistema de bicicleta pública del Área Metropolitana de Guadalajara (**MiBici**).

**Integrantes:**
- Miguel Ángel Durán Betancourt — A01797974
- Juan Pablo Islas Guzmán — A01797727
- Bryan Steve Ortega Castillo — A01797846
- Kevin Rogelio Rodriguez Magaña — A01840418

---

## Problemas y modelos del proyecto

El proyecto aborda tres preguntas operativas sobre el sistema MiBici mediante distintos enfoques de aprendizaje automático:

| Código | Enfoque ML | Pregunta que responde | Modelo registrado |
| :--- | :--- | :--- | :--- |
| **P1** | **Regresión** | ¿Cuántos viajes diarios se esperan en el sistema? | `mibici-equipo23-p1-demanda` |
| **P2** *(desplegado)* | **Clasificación multiclase** | ¿Habrá presión neta elevada en una estación (riesgo de quedar sin bicis o sin anclajes) en los próximos 30 min? | `MiBici_Equipo23_P2_Presion_Proxy_Academica` |
| **P3** | **Clustering** | ¿Qué perfiles operativos y horarios agrupan a las estaciones del sistema? | `mibici-equipo23-p3-grupos` |

Para conocer a detalle cómo funciona el modelo desplegado en la API (**P2**), consulta [docs/modelo_p2_presion.md](docs/modelo_p2_presion.md).

---

## Estructura del proyecto

```text
├── .github/workflows/ci.yml   <- CI en GitHub Actions (Ruff, Pytest, imagen Docker)
├── Containerfile              <- Imagen reproducible de la API FastAPI (uv.lock)
├── MLproject                  <- Puntos de entrada MLflow (ingest, train, search, serve)
├── Taskfile.yml               <- Atajos de tareas (`task test`, `task lint`, `task stack:up`, etc.)
├── docker-compose.yml         <- Stack local/producción (nginx, api, postgres, grafana)
├── dvc.yaml / dvc.lock        <- Pipeline y versionado de datos (remoto en DagsHub)
├── pyproject.toml / uv.lock   <- Dependencias principales, dev y loadtest
├── requirements-*.txt         <- Entornos aislados (deepchecks y evidently)
├── docs/                      <- Guías detalladas de uso, datos, modelos y despliegue
├── infra/                     <- Configuraciones de Nginx, PostgreSQL y Grafana
├── mibici/                    <- Código fuente (ingesta, features, modelos, API)
├── models/p2_champion/        <- Artefacto empaquetado del modelo P2 vigente
├── references/                <- Contratos, protocolos, JSON de ejemplo y referencias
├── reports/                   <- Evidencias, auditorías de seguridad y figuras
└── tests/                     <- Suite de pruebas unitarias, API y carga (`loadtests/`)
```

---

## Primeros pasos: datos, entrenamiento y registro en MLflow

Sigue estos pasos si quieres descargar los datos del proyecto, entrenar un modelo nuevo y registrarlo en el **MLflow Model Registry** de DagsHub:

1. **Instalar dependencias y autenticarse en DagsHub:**
   ```bash
   uv sync --locked
   uv run --locked dagshub login
   ```
2. **Descargar el dataset versionado desde DagsHub (DVC):**
   *(Configura primero tu usuario y token local de DagsHub según [docs/datos_y_dvc.md](docs/datos_y_dvc.md).)*
   ```bash
   uv run --locked dvc pull
   ```
3. **Entrenar y registrar corridas en MLflow:**
   Exporta `MLFLOW_TRACKING_URI=https://dagshub.com/bryan-s-ortega/TC5061-Proyecto-Equipo23.mlflow` (o usa un servidor local) y ejecuta cualquiera de los entry points de [MLproject](MLproject):
   ```bash
   # Ejemplo: entrenar modelo de clasificación de presión (P2)
   uv run --locked mlflow run . --env-manager local \
     --experiment-name mibici-equipo23-mlprojects \
     -e train -P question=P2 -P model=tree -P max_depth=5 -P class_weight=balanced
   ```
4. **Promover el modelo en el Model Registry:**
   ```bash
   uv run --locked python -m mibici.register_project_models --question P2 --run-id <RUN_ID_GANADOR>
   ```

---

## Levantar el servicio desplegado (Docker Compose)

```bash
cp .env.example .env
docker compose up -d --build
```
- **Interfaz web / simulador (P2):** `http://localhost/ui`
- **Documentación Swagger:** `http://localhost/docs`
- **Monitoreo en tiempo real (Grafana):** `http://localhost/monitoring/`

---

## Documentación detallada

| Tema | Guía |
| :--- | :--- |
| Qué responde y cómo funciona el modelo desplegado (P2) | [docs/modelo_p2_presion.md](docs/modelo_p2_presion.md) |
| Model Card del modelo desplegado (`champion` v1 y `challenger` v2) | [docs/model_card_p2.md](docs/model_card_p2.md) |
| Gestión de datos, DVC y DagsHub | [docs/datos_y_dvc.md](docs/datos_y_dvc.md) |
| Experimentos base y MLflow Projects (regresión, clasificación, clustering) | [docs/experimentos_mlflow.md](docs/experimentos_mlflow.md) |
| API REST: despliegue, contrato y consumo | [docs/api_p2.md](docs/api_p2.md) |
| Docker Compose, pruebas de carga y operación | [docs/operacion_compose_finops.md](docs/operacion_compose_finops.md) |
| Demo pública temporal con Docker Compose y ngrok | [docs/demo_docker_ngrok.md](docs/demo_docker_ngrok.md) |
| Guion de presentación final (Equipo 23) | [docs/presentacion_equipo23.md](docs/presentacion_equipo23.md) |

---

## Pruebas y validación del proyecto

- **Unit tests (Pytest):** validan ingesta, features sin fuga temporal, MLproject, contrato de esquemas y endpoints de la API.
  ```bash
  uv run --locked pytest tests -q
  ```
- **Load tests y FinOps (Locust):** evalúan latencia, rendimiento y costo unitario bajo carga concurrente contra el stack en Compose (ver [reports/evidence/finops/](reports/evidence/finops/)).
  ```bash
  uv run --locked --group loadtest python tests/loadtests/run_load.py --host http://127.0.0.1 --users 5 25 --seconds 60
  ```
- **Security tests (Bandit + pip-audit):** análisis estático SAST y auditoría de dependencias SCA (ver [auditoria_seguridad.md](reports/security/auditoria_seguridad.md)).
  ```bash
  uv run --locked bandit -r mibici -ll
  uv run --locked pip-audit
  ```
- **Validación de datos (DeepChecks):** requiere entorno aislado por incompatibilidad con `pandas 3.x` / `scikit-learn 1.9` (ver [reports/evidence/actividad7/README.md](reports/evidence/actividad7/README.md)).
  ```bash
  uv venv --python 3.12 .venv-deepchecks
  uv pip install --python .venv-deepchecks/bin/python -r requirements-deepchecks.txt
  .venv-deepchecks/bin/python -m mibici.validation.deepchecks_validation
  ```

---

## Monitoreo

- **Monitoreo en tiempo real (PostgreSQL + Grafana):** cada llamada a `/predict` o `/predict/batch` registra la petición y predicción en PostgreSQL (`mibici/api/db.py`) y se visualiza en Grafana bajo `http://localhost/monitoring/` (dashboard *MiBici P2 — Monitoreo de Predicciones*).
- **Monitoreo de data drift (Evidently):** compara julio–septiembre de 2025 vs 2026 sobre las 8 variables de entrada del modelo de clasificación (ver [reports/evidence/p2_drift/README.md](reports/evidence/p2_drift/README.md)). Se ejecuta en entorno aislado porque `evidently==0.7.23` requiere `pandas<3`:
  ```bash
  uv venv --python 3.13 .venv-evidently
  uv pip install --python .venv-evidently/bin/python -r requirements-evidently.txt
  .venv-evidently/bin/python -m mibici.monitor_p2_drift
  ```

---

## Calidad de código y contribución (GitHub Flow)

### Estilo y hooks (Ruff + pre-commit)

El proyecto usa [Ruff](https://docs.astral.sh/ruff/) (longitud máxima de línea de 99 caracteres y ordenamiento de imports con `isort`) y `pre-commit` ([.pre-commit-config.yaml](.pre-commit-config.yaml)):

```bash
task lint          # uv run ruff format --check && uv run ruff check
task format        # uv run ruff check --fix && uv run ruff format
task hooks:install # uv run pre-commit install
```

### Flujo de trabajo

1. **Crear una rama** desde `main` actualizada usando `kebab-case` con prefijo:
   - `feat/<descripcion>`, `fix/<descripcion>`, `docs/<descripcion>`, `refactor/<descripcion>`, `test/<descripcion>`, `chore/<descripcion>`.
2. **Hacer commits atómicos** siguiendo [Conventional Commits](https://www.conventionalcommits.org/) en modo imperativo y título `< 72` caracteres:
   - `<tipo>(<alcance-opcional>): <descripción>` (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`).
3. **Verificar localmente** antes de subir (`task lint` y `task test`).
4. **Abrir Pull Request** hacia `main` (el workflow [.github/workflows/ci.yml](.github/workflows/ci.yml) ejecuta Ruff, Pytest, construcción de la imagen y smoke test de `/health`).
5. **Merge y limpieza** una vez aprobado.
