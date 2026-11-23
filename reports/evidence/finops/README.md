# Evidencia de carga y costo por inferencia

Se midió el sistema P2 de MiBici en Docker Desktop ARM64 durante la noche del
22 al 23 de noviembre de 2026, hora de Ciudad de México. Cada escenario duró
60 segundos, con 5 y 25 usuarios, una rampa aproximada de un segundo y pausas
de 0.1 a 0.3 segundos por usuario. Locust alternó tres entradas válidas a
`POST /predict` y verificó HTTP 200, JSON y la clase de predicción. La carga
entró por Nginx, con el registro en PostgreSQL habilitado.

## Resultados y procedencia

| Usuarios | Solicitudes finales | Fallos | RPS exitosos | Latencia p95 |
| --- | ---: | ---: | ---: | ---: |
| 5 | 1,364 | 0 | 23.49 | 21 ms |
| 25 | 7,179 | 0 | 119.96 | 10 ms |

Los totales proceden de los HTML finales de Locust, `u5.html` y `u25.html`.
`summarize.py` extrae sus estadísticas a `u5_final.json`, `u25_final.json` y
[`summary.json`](summary.json). Los CSV son capturas periódicas y pueden
terminar antes de la última solicitud. Los CSV de historial se usan para las
series temporales de las gráficas.

La suma de las solicitudes finales fue 8,543, igual al recuento de filas de
PostgreSQL registrado en [`database_count.txt`](database_count.txt). La revisión
de logs de la API registró cero líneas de error en
[`api_error_check.txt`](api_error_check.txt).

- [`locust_performance.png`](locust_performance.png) muestra throughput,
  latencia p95 y fallos por segundo de ambos escenarios.
- [`resources.png`](resources.png) muestra CPU y memoria de la API.
- `u5_resources.jsonl` y `u25_resources.jsonl` contienen las muestras originales
  de `docker stats` de los cuatro contenedores. El resumen incluye promedios,
  máximos y cantidad de muestras por servicio.
- [`compose_ps.txt`](compose_ps.txt), [`health.json`](health.json) y
  [`model_info.json`](model_info.json) documentan el despliegue medido.

## Supuestos FinOps

La referencia es un servidor AWS Lightsail Linux/Unix con IPv4 público,
2 vCPU y 4 GB de memoria, por 24 USD al mes, con 80 GB SSD y 4 TB de
transferencia incluidos. Se suponen 730 horas por mes. La tarifa se consultó
el 22 de noviembre de 2026. [Precios oficiales de AWS Lightsail](https://aws.amazon.com/lightsail/pricing/)

El cálculo asigna el precio completo del servidor a los cuatro servicios.
El costo por inferencia se obtiene como `(24 / 730 / 3600) / RPS exitosos`.
Con la tasa medida, resulta aproximadamente 0.000000389 USD por inferencia
para 5 usuarios y 0.0000000761 USD para 25 usuarios. El escenario al 10 % de
utilización mantiene el servidor encendido y reduce la tasa útil media a una
décima parte, multiplicando por diez el costo unitario.

La medición local disponía de 8 CPU y cerca de 7.75 GiB asignados a Docker.
El generador y los servicios compartieron el equipo físico. La proyección
supone que el servidor de referencia de 2 vCPU sostiene la tasa medida y
requiere validación allí. Los ensayos breves permiten comparar dos cargas.
El p95 menor del segundo ensayo puede reflejar calentamiento o variabilidad.
Impuestos, copias de seguridad, transferencia excedente y servicios externos
agregarían cargos a la referencia calculada.

## Reproducir

Desde la raíz del repositorio, con Docker, Compose y Python 3.13 disponibles:

```bash
API_PORT=18000 NGINX_PORT=18080 docker compose -p mibici-finops up -d --build
docker compose -p mibici-finops ps
curl -fsS http://127.0.0.1:18080/health
python3.13 -m venv .venv-locust
source .venv-locust/bin/activate
python -m pip install -r requirements-locust.txt
python loadtests/run_load.py --host http://127.0.0.1:18080 --users 5 25 --seconds 60
python loadtests/summarize.py
python loadtests/plot_results.py
```

El comando de carga reemplaza los archivos de evidencia de esos escenarios.
Para conservar una ejecución previa, indicar otra carpeta mediante `--output`
en `run_load.py`, utilizarla con `--folder` al resumir y pasarla como primer
argumento al ejecutar `plot_results.py`. La guía
principal del repositorio también explica los puertos predeterminados y la
ejecución del pipeline de GitHub Actions.
