# Gestión y descarga del conjunto de datos (DVC + DagsHub)

El proyecto utiliza **DVC** con almacenamiento remoto en **DagsHub** (`https://dagshub.com/bryan-s-ortega/TC5061-Proyecto-Equipo23.dvc`, configurado como remoto por defecto en [.dvc/config](../.dvc/config)). Existen dos maneras de obtener los datos: **descargar los datos versionados desde DagsHub** (recomendado) o **reconstruir el dataset desde los archivos públicos de MiBici**.

---

## Catálogo de datasets versionados

| Archivo | Etapa DVC | Qué contiene |
| :--- | :--- | :--- |
| `data/processed/trips.parquet` y `data/raw/stations_nomenclature.csv` | `dataset` | Viajes individuales descargados desde MiBici (ventana móvil de 3 años) y catálogo de estaciones |
| `data/processed/trips_fechas_corregidas.parquet` y `data/raw/stations_nomenclature_reconstruccion.csv` | `p2_dataset` | Viajes individuales limpios con rango fijo (`2023-11-01` a `2026-09-30`) y nomenclatura de estaciones |
| `data/interim/p2_movimientos_corregidos.parquet` | `p2_movements` | Conteos agregados de salidas y llegadas por estación e intervalo de 30 minutos |
| **`data/processed/p2_examples.parquet`** | `p2_examples` | **Dataset preparado para el modelo de clasificación de presión (P2)**: una fila por estación y ventana de 30 min con las 8 variables de entrada (`prev_30m`, `prev_2h`, calendario, `capacity`), `target` y `split` |

---

## 1. Descargar el dataset desde DagsHub (Recomendado)

1. **Inicia sesión en DagsHub** (una sola vez, abre OAuth en tu navegador):
   ```bash
   uv run --locked dagshub login
   ```
2. **Configura tus credenciales locales de DVC usando únicamente tu token de DagsHub** (se guardan en `.dvc/config.local`, ignorado por Git):
   ```bash
   # Opción A: reutilizar automáticamente el token guardado por `dagshub login`
   uv run --locked python -c 'import subprocess, dagshub; tok = dagshub.auth.get_token(); subprocess.run(["dvc", "remote", "modify", "dagshub", "--local", "user", tok], check=True); subprocess.run(["dvc", "remote", "modify", "dagshub", "--local", "password", tok], check=True)'

   # Opción B: pasar manualmente un token de DagsHub
   # uv run --locked dvc remote modify dagshub --local user <TU_TOKEN_DAGSHUB>
   # uv run --locked dvc remote modify dagshub --local password <TU_TOKEN_DAGSHUB>
   ```
3. **Descarga los artefactos versionados:**
   ```bash
   uv run --locked dvc pull
   # o para un archivo específico:
   uv run --locked dvc pull data/processed/p2_examples.parquet
   ```

---

## 2. Reconstruir o actualizar el dataset desde la fuente externa

Si necesitas reconstruir el dataset desde cero o actualizarlo con datos recién publicados en la [página de datos abiertos de MiBici](https://mibici.net/es/datos-abiertos/), puedes usar DVC o ejecutar el script directamente.

### A. Ejecución de la etapa de DVC (`dvc repro`)

```bash
uv sync --locked
uv run --locked dvc repro --force dataset
# o alternativamente con Task:
task data
```

**¿Qué hace exactamente este comando?**
- Ejecuta `uv run python -m mibici.dataset` configurado en [dvc.yaml](../dvc.yaml).
- Descarga los CSV mensuales correspondientes a la **ventana por defecto (los últimos 3 años hasta la fecha actual)**, normaliza los viajes, une la nomenclatura de estaciones y genera:
  - `data/processed/trips.parquet` (~390 MB)
  - `data/raw/stations_nomenclature.csv` (~40 KB)
- `--force` reejecuta la etapa ignorando el caché previo.
- Dado que el rango por defecto se calcula a partir de `date.today()`, ejecutarlo en distintas fechas actualizará los hashes en [dvc.lock](../dvc.lock).

### B. Delimitar un rango de fechas personalizado

Puedes personalizar el período de descarga con `--start-date` y `--end-date` (`AAAA-MM-DD`):

```bash
# Ejemplo: Descargar únicamente los viajes del año 2023
uv run --locked python -m mibici.dataset --start-date 2023-01-01 --end-date 2023-12-31

# Ejemplo: Descargar un mes específico para pruebas rápidas
uv run --locked python -m mibici.dataset --start-date 2024-05-01 --end-date 2024-05-31
```

**Parámetros disponibles:**
- `--start-date`: Primer día del rango (`AAAA-MM-DD`). Por defecto: hace 3 años.
- `--end-date`: Último día del rango (`AAAA-MM-DD`). Por defecto: fecha actual.
- `--output-path`: Ruta de salida para el archivo parquet limpio (por defecto: `data/processed/trips.parquet`).
- `--nomenclature-output-path`: Ruta de salida para la nomenclatura (por defecto: `data/raw/stations_nomenclature.csv`).

---

## 3. Subir nuevos datos versionados a DagsHub (Mantenedores)

Si actualizas el dataset oficial y deseas compartirlo con el equipo en DagsHub:

```bash
uv run --locked dvc push
# o alternativamente con Task:
task dvc:push
```

Posteriormente, haz commit y push del archivo `dvc.lock` actualizado a Git para que tus compañeros puedan sincronizar los nuevos datos con `uv run --locked dvc pull`.
