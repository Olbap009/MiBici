# mibici

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Plantilla%20de%20proyecto-328F97?logo=cookiecutter" />
</a>

Proyecto de MLOps con datos del sistema de bicicleta pública del Área Metropolitana de Guadalajara, MiBici.

## Estructura del proyecto

```
├── LICENSE            <- Licencia de código abierto (si se define una)
├── Taskfile.yml       <- Archivo de tareas con comandos convenientes como `task data` o `task test`
├── README.md          <- Documento principal para desarrolladores del proyecto.
├── data
│   ├── external       <- Datos provenientes de fuentes de terceros.
│   ├── interim        <- Datos intermedios que han sido transformados.
│   ├── processed      <- Conjuntos de datos finales y canónicos para modelado.
│   └── raw            <- Datos originales e inmutables descargados.
│
├── docs               <- Proyecto predeterminado de mkdocs; consulta www.mkdocs.org para detalles.
│
├── models             <- Modelos entrenados y serializados, predicciones o resúmenes de modelos.
│
├── notebooks          <- Jupyter notebooks. La convención de nombres es un número (para ordenamiento),
│                         las iniciales del autor y una descripción breve separada por `-`, ej.
│                         `1.0-jqp-exploracion-inicial-datos`.
│
├── pyproject.toml     <- Archivo de configuración del proyecto con metadatos del paquete
│                         mibici y configuración de herramientas como ruff.
│
├── references         <- Diccionarios de datos, manuales y materiales explicativos.
│
├── reports            <- Análisis generados en HTML, PDF, LaTeX, etc.
│   └── figures        <- Gráficos y figuras generadas para su uso en reportes.
│
├── requirements.txt   <- Archivo de requerimientos para reproducir el entorno (si aplica).
│
├── setup.cfg          <- Archivo de configuración para linters.
│
└── mibici             <- Código fuente del proyecto.
    │
    ├── __init__.py             <- Convierte a mibici en un módulo de Python
    │
    ├── config.py               <- Variables útiles y configuraciones del proyecto
    │
    ├── dataset.py              <- Scripts para descargar o procesar datos
    │
    ├── features.py             <- Código para generar variables (features) para modelado
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Código para inferencia con modelos entrenados          
    │   └── train.py            <- Código para entrenar modelos
    │
    └── plots.py                <- Código para generar visualizaciones
```

## Descargar y versionar el conjunto de datos

El módulo del dataset consulta los enlaces a los archivos CSV mensuales y la nomenclatura de estaciones más reciente desde la [página de datos abiertos de MiBici](https://mibici.net/es/datos-abiertos/). Por defecto, incluye los viajes de los últimos tres años hasta la fecha actual, normaliza los nombres de columnas originales en español a `snake_case` en inglés, preserva los nombres de estaciones en codificación UTF-8, procesa las marcas de tiempo de los viajes y añade los nombres y coordenadas de las estaciones asociadas.

Para instalar las dependencias y ejecutar la etapa de DVC que construye y rastrea los artefactos:

```bash
uv sync
uv run dvc repro --force dataset
# o alternativamente con Task:
task data
```

Los viajes limpios se generan en `data/processed/trips.parquet` y la nomenclatura descargada se guarda en `data/raw/stations_nomenclature.csv`. DVC rastrea ambas salidas; el indicador `--force` actualiza los datos externos de MiBici y la ventana móvil de fechas.

Se pueden especificar las opciones `--start-date AAAA-MM-DD` y `--end-date AAAA-MM-DD` en la línea de comandos ejecutando `uv run python -m mibici.dataset` para delimitar un rango de fechas personalizado.

## Almacenamiento remoto en DVC

El repositorio utiliza un bucket de Google Cloud Storage como almacenamiento remoto: `gs://mibici-mlops-project`. Para sincronizar los datos, primero autentícate localmente mediante las Credenciales Predeterminadas de la Aplicación (ADC) de Google Cloud y posteriormente sube los archivos versionados:

```bash
gcloud auth application-default login
uv run dvc push
# o alternativamente con Task:
task dvc:push
```

Tu cuenta de Google requiere permisos para escribir objetos en el bucket. Solicita al propietario del proyecto que te otorgue el rol `roles/storage.objectUser` (puedes consultar el comando en el archivo [Taskfile.yml](file:///home/bryan/learning/mibici/Taskfile.yml) mediante `task grant-access`).

---

## Calidad de código y estilo (Ruff y Pre-commit Hooks)

El proyecto utiliza [Ruff](https://docs.astral.sh/ruff/) como linter y formateador de código extremadamente rápido, configurado en el archivo [pyproject.toml](file:///home/bryan/learning/mibici/pyproject.toml) (longitud máxima de línea de 99 caracteres y ordenamiento automático de imports con `isort`).

### Uso de Ruff

Puedes verificar o aplicar formato manualmente utilizando `task` o directamente `uv`:

- **Verificar formato y linteo (sin modificar archivos):**
  ```bash
  task lint
  # Equivalente a:
  # uv run ruff format --check
  # uv run ruff check
  ```

- **Aplicar formateo y autocorrección de errores:**
  ```bash
  task format
  # Equivalente a:
  # uv run ruff check --fix
  # uv run ruff format
  ```

### Git Pre-commit Hook

Para evitar subir código con errores de estilo o sintaxis, se incluye la configuración de [pre-commit](https://pre-commit.com/) en [.pre-commit-config.yaml](file:///home/bryan/learning/mibici/.pre-commit-config.yaml), la cual ejecuta automáticamente `ruff-check --fix` y `ruff-format` antes de cada `git commit`.

1. **Instalar el hook en tu entorno Git local:**
   ```bash
   task hooks:install
   # o: uv run pre-commit install
   ```

2. **Ejecutar el hook manualmente sobre todos los archivos:**
   ```bash
   task hooks:run
   # o: uv run pre-commit run --all-files
   ```

Una vez instalado, cada vez que ejecutes `git commit`, Ruff revisará y formateará los archivos modificados de manera transparente.

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
