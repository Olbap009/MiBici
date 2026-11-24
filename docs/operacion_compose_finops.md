# Operación con Compose, pruebas de carga, monitoreo y calidad

---

## 1. Operación con Docker Compose

Requisitos: Docker con Compose y Python 3.13. Desde la raíz del repositorio:

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
curl -fsS http://127.0.0.1/health
curl -fsS http://127.0.0.1/model/info
```

Nginx expone la interfaz en `http://127.0.0.1/ui` y Grafana en `http://127.0.0.1/monitoring/`. El Compose incluye la API (`api`), PostgreSQL (`postgres`), Grafana (`grafana`) y Nginx (`nginx`), con volúmenes persistentes y comprobaciones de salud. Configura las credenciales mediante `.env` según el entorno.

Para usar los puertos alternativos de la evidencia de FinOps, anteponer `NGINX_PORT=18080` al comando de levantamiento. Para detener los servicios conservando sus volúmenes:

```bash
docker compose down
```

El pipeline [.github/workflows/ci.yml](../.github/workflows/ci.yml) se ejecuta en cada `pull_request` y `push` a `main`: corre Ruff y Pytest, construye la imagen desde [Containerfile](../Containerfile) y comprueba `/health`. ([Ejecución verificada en verde](https://github.com/bryan-s-ortega/TC5061-Proyecto-Equipo23/actions/runs/44222997493)).

---

## 2. Pruebas de carga y FinOps (Locust)

La prueba de carga usa el grupo `loadtest` integrado en `uv.lock`:

```bash
uv run --locked --group loadtest python loadtests/run_load.py --host http://127.0.0.1 --users 5 25 --seconds 60
uv run --locked --group loadtest python loadtests/summarize.py
uv run --locked --group loadtest python loadtests/plot_results.py
```

Con puertos alternativos, usar `--host http://127.0.0.1:18080`. Los resultados y estimaciones de costo quedan en [reports/evidence/finops/](../reports/evidence/finops/).

---

## 3. Monitoreo de datos de P2 con Evidently

La [guía de monitoreo](../reports/evidence/p2_drift/README.md) documenta cómo comparar los datos de julio a septiembre de 2025 y 2026, junto con las gráficas y resultados reproducibles de drift y calidad de datos de las ocho variables de P2.

Debido a que `evidently==0.7.23` requiere `pandas<3`, se ejecuta en un entorno aislado sin modificar `uv.lock`:

```bash
uv venv --python 3.13 .venv-evidently
uv pip install --python .venv-evidently/bin/python -r requirements-evidently.txt
.venv-evidently/bin/python -m mibici.monitor_p2_drift
```

---

## 4. Pruebas unitarias, validación de datos (DeepChecks) y seguridad

La [guía de ejecución y evidencias de Actividad 7](../reports/evidence/actividad7/README.md) documenta la preparación de entornos, comandos, capturas y resultados.

```bash
# Entorno principal: Python 3.13, versiones fijadas en uv.lock.
uv sync --locked
uv run --locked python -m pytest tests -q

# Seguridad: un código de salida distinto de cero exige revisar el reporte.
uv run --locked bandit -r mibici -ll
uv run --locked pip-audit

# DeepChecks usa otro entorno (requiere pandas 2.2 / scikit-learn 1.5).
uv venv --python 3.12 .venv-deepchecks
uv pip install --python .venv-deepchecks/bin/python -r requirements-deepchecks.txt
.venv-deepchecks/bin/python -m mibici.validation.deepchecks_validation
```

También están disponibles `task test`, `task deepchecks`, `task security:bandit`, `task security:audit` y `task security:check`. DeepChecks requiere previamente `data/processed/p1_demanda_diaria.csv`; las pruebas unitarias usan datos pequeños de prueba y no requieren descargar el dataset completo.

Para el detalle de hallazgos de seguridad, consultar [auditoria_seguridad.md](../reports/security/auditoria_seguridad.md).
