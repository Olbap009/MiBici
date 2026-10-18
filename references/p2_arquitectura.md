# Arquitectura de experimentación de P2

## Flujo

1. Descargar viajes y catálogo de MiBici.
2. Normalizar y validar fechas en dataset.py.
3. Construir movimientos por estación e intervalos de 30 minutos.
4. Generar variables históricas y separar entrenamiento, validación y prueba.
5. Entrenar baseline y árboles de decisión.
6. Registrar parámetros, métricas, modelos y artefactos en MLflow.
7. Comparar resultados mediante revisión humana.

## Herramientas

- Python, pandas y PyArrow: transformación y lectura por bloques.
- Scikit-learn: árboles de decisión.
- MLflow: registro y comparación de experimentos.
- uv y uv.lock: entorno y dependencias.
- GitHub: código, historial y revisiones.
- DVC y GCS: versionado y distribución de datos.

## Estado

La integración de los datos corregidos de P2 con DVC/GCS está pendiente
de verificación. No existe un despliegue en producción.

Este archivo documenta el flujo en texto. Falta incorporar el diagrama
visual requerido por la entrega.
