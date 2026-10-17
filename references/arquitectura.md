# Arquitectura propuesta

```mermaid
flowchart LR
  A[Portal abierto MiBici] --> B[data/raw]
  B --> C[ingestion.py]
  C --> D[data/processed]
  D --> E[features.py]
  E --> F[P1 regresión]
  E --> G[P2 clasificación]
  E --> H[P3 clustering]
  F --> I[MLflow Tracking]
  G --> I
  H --> I
  I --> J[reports/figures]
  D -. DVC .-> K[Versionado de datos]
```

La ejecución local usa Python, pandas y scikit-learn. MLflow conserva
parámetros, métricas, tags y artefactos; Git conserva código y documentación;
DVC debe conservar las versiones de los CSV sin incluirlos directamente en
GitHub.

