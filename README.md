# mibici

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Proyecto de MLOps con datos del sistema de bicicleta pública del Área Metropolitana de Guadalajara. MiBici

## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Taskfile.yml       <- Taskfile with convenience commands like `task data` or `task test`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         mibici and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── mibici   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes mibici a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

## Download and version the dataset

The dataset command reads the monthly CSV links and the latest station
nomenclature CSV from [MiBici's open-data page](https://mibici.net/es/datos-abiertos/).
By default, it includes trips from the last three years through the current time,
normalizes the Spanish source columns to English snake case, preserves UTF-8 station
names, parses trip timestamps, and adds station names and coordinates.

Install the project and run the DVC stage to build and track the outputs:

```bash
uv sync
uv run dvc repro --force dataset
```

The cleaned trips are written to `data/processed/trips.parquet`, and the downloaded
station nomenclature is saved to `data/raw/stations_nomenclature.csv`. DVC tracks
both outputs; `--force` refreshes the external MiBici data and the rolling date
window.
Optional `--start-date YYYY-MM-DD` and `--end-date YYYY-MM-DD` CLI options can be
passed to `uv run python -m mibici.dataset` to set a custom inclusive date range.

## DVC remote storage

The configured remote uses the Google Cloud Storage bucket
`gs://mibici-mlops-project`. Authenticate locally with Google Application Default
Credentials, then upload the DVC-tracked data:

```bash
gcloud auth application-default login
uv run dvc push
```

Your Google account needs permission to write objects to the bucket. Ask the project owner to grant you the `roles/storage.objectUser` role.

---

## Flujo de trabajo y contribución (GitHub Flow)

Para colaborar en este proyecto se sigue la metodología [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow), diseñada para mantener un ciclo de entrega continuo, simple y ordenado:

1. **Crear una rama (`branch`):** Parte siempre de la rama `main` actualizada con un nombre descriptivo según la convención de ramas.
2. **Realizar cambios y commits:** Haz commits frecuentes, atómicos y con mensajes claros siguiendo la convención de commits.
3. **Verificar calidad localmente:** Antes de subir tus cambios o solicitar revisión, ejecuta las herramientas de formateo y tests:
   ```bash
   task lint
   task test
   ```
4. **Abrir un Pull Request (PR):** Publica tu rama en GitHub y abre un Pull Request hacia `main`. Describe qué cambios introdujiste, capturas/resultados si aplica, y referencia los issues relacionados.
5. **Revisión de código:** Resuelve comentarios, sugerencias o verificaciones automáticas de CI.
6. **Merge y limpieza:** Una vez aprobado, el PR se fusiona a `main` y la rama de trabajo se elimina.

---

### Convención de nombres de ramas

Las ramas deben nombrarse en minúsculas, usando `kebab-case` (palabras separadas por guiones) y organizadas mediante un prefijo que describa el propósito del cambio:

```text
<tipo>/<descripcion-corta>
```

#### Prefijos disponibles:

| Prefijo | Propósito | Ejemplo |
| :--- | :--- | :--- |
| **`feat/`** | Nueva funcionalidad o módulo del proyecto | `feat/weather-feature-extraction` |
| **`fix/`** | Corrección de un bug o error en datos/código | `fix/station-id-type-mismatch` |
| **`docs/`** | Cambios exclusivamente en documentación | `docs/add-contributing-guide` |
| **`refactor/`** | Cambios en el código que no alteran la lógica ni añaden funcionalidades | `refactor/dataset-cleaning-pipeline` |
| **`test/`** | Adición o corrección de pruebas unitarias o de integración | `test/add-dataset-schema-checks` |
| **`chore/`** | Tareas de mantenimiento, dependencias o tooling | `chore/update-uv-lock` |

---

### Convención de mensajes de commits (Conventional Commits)

Adoptamos la especificación de [Conventional Commits](https://www.conventionalcommits.org/) para mantener un historial de cambios legible, uniforme y automatizable:

```text
<tipo>(<alcance-opcional>): <descripción concisa en imperativo>

[cuerpo opcional explicando el porqué o detalles del cambio]
```

#### Tipos de commits comunes:
- **`feat`**: Incorpora una nueva funcionalidad (`feat(dataset): add holiday indicator feature`).
- **`fix`**: Corrige un error o bug (`fix(dvc): set correct quota project in adc`).
- **`docs`**: Modificaciones en documentación (`docs(readme): document git workflow and branch conventions`).
- **`refactor`**: Reorganización de código sin cambiar comportamiento (`refactor(dataset): simplify date parsing loop`).
- **`test`**: Pruebas automáticas (`test(dataset): add tests for raw stations nomenclature`).
- **`chore`**: Actualizaciones de paquetes, configuraciones o tareas rutinarias (`chore(deps): update hydra-core`).

#### Buenas prácticas:
- **Modo imperativo:** Redacta el mensaje como una orden directa (ej. `add feature`, no `added feature` / `agrega validación`, no `agregando validación`).
- **Línea de título concisa:** Mantén la primera línea en menos de 72 caracteres.
- **Commits atómicos:** Cada commit debe resolver una única unidad lógica de trabajo.

--------
