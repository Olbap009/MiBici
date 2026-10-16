# mibici

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Proyecto de MLOps con datos del sistema de bicicleta pública del Área Metropolitana de Guadalajara. MiBici

## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
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

--------
