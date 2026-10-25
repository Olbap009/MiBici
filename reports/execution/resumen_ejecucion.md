# Ejecución real de los experimentos del Equipo 23

Fecha: 25 de octubre de 2026. Entorno: Python 3.13.16 y dependencias de uv.lock.

Experimento: `mibici-equipo23`. Servidor local: http://127.0.0.1:5002.

Se ejecutaron tres búsquedas anidadas, cada una con tres variantes. Hay un baseline por pregunta y doce corridas de modelo terminadas. Las ingestas también se lanzaron mediante MLflow Project.

| Pregunta | Selección | Resultado | Alias |
|---|---|---|---|
| P1 | MiBici_Equipo23_P1_Demanda | MAE validación 801.88; prueba 1299.97 | champion v1 |
| P2 | MiBici_Equipo23_P2_Presion_Proxy_Academica | Balanced accuracy validación 0.64512; prueba 0.64587 | champion v1 |
| P3 | MiBici_Equipo23_P3_Estaciones | Silueta 0.30088 | champion v1 |

## P1
Menor MAE de validación entre las tres variantes RF, con prueba consultada después de elegir. Comparación final con lag_7.
Corrida: `ca0f4557b2664c6b9a89aa54808739ec`.
Carga verificada: `models:/MiBici_Equipo23_P1_Demanda@champion`.

## P2
Mayor balanced accuracy de validación, sujeto a recall >=0.10 en ambas clases de presión. La precisión de alertas sigue siendo baja.
Corrida: `4202303e725f4152ac6632c9901516f7`.
Carga verificada: `models:/MiBici_Equipo23_P2_Presion_Proxy_Academica@champion`.

## P3
Selección conservadora del baseline k=4: las variantes con más variables no aportan evidencia de mejora. La silueta se calcula en espacios de variables diferentes y no demuestra superioridad predictiva ni utilidad urbana por sí sola.
Corrida: `6c1c512b733346f1aa9195c7e2b09236`.
Carga verificada: `models:/MiBici_Equipo23_P3_Estaciones@champion`.

## Límites y procedencia
- No se obtuvo acceso al bucket DVC. Los ejemplos finales y movimientos de P2 reconstruidos coinciden con los MD5 versionados; el parquet de viajes tiene distinta disposición física.
- La ingesta actual interpreta fechas explícitamente. Los baselines se recalcularon con los mismos insumos que los candidatos.
- El P1 actual predice demanda diaria agregada del sistema, como el código del PR. No comparar su MAE con el antiguo baseline local por estación-día.
- P3 usa métricas internas sobre espacios de variables diferentes y requiere interpretación de los grupos.
- Los aliases champion son versiones académicas; no hay un servicio de inferencia desplegado.
- Cambios y resultados locales; no se publicaron en GitHub ni se cargaron al bucket.

## Archivos
`comparacion_experimentos.csv` conserva las métricas y parámetros de las doce corridas; `resultados_experimentos.json` conserva selección, versiones y linaje. Los logs de cada ejecución se guardan en esta carpeta.
