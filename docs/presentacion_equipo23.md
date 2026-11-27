# Guion de presentación final — Equipo 23

MiBici: presión por estación. TC5061.10 — Operaciones de aprendizaje automático. Noviembre de 2026.

Este guion acompaña la presentación final y las evidencias del repositorio.

## 1. MiBici. Presión por estación

**Narra:** Miguel Ángel Durán Betancourt

Somos el Equipo 23. Presentamos MiBici: un proyecto de MLOps para anticipar la presión en estaciones de bicicletas compartidas de Guadalajara.

## 2. Anticipación de presión a 30 minutos

**Narra:** Miguel Ángel Durán Betancourt

El desbalance entre salidas y llegadas dificulta el rebalanceo. Exploramos demanda diaria, presión por estación y perfiles operativos. Desplegamos P2 para clasificar presión a treinta minutos con ocho variables. Usamos flujos previos, calendario y capacidad. Es un proxy académico de movimientos. La disponibilidad física de bicicletas y anclajes requiere telemetría adicional.

## 3. Predicción desde la API

**Narra:** Bryan Steve Ortega Castillo

Mostramos primero el resultado para el usuario. La interfaz solicita las ocho variables del contrato. Ahora enviamos un ejemplo válido. El servicio responde con la clase de presión y el alias del modelo activo. En Swagger vemos la petición JSON, la respuesta HTTP doscientos y los metadatos de champion. Esta es una inferencia real del artefacto empaquetado de MLflow. Después mostraremos cómo queda registrada en el monitoreo.

## 4. Datos y experimentos reproducibles

**Narra:** Miguel Ángel Durán Betancourt

Detrás de la petición hay un flujo reproducible. DVC en DagsHub versiona los datos. El feature engineering agrega viajes en las ventanas previas de treinta minutos y dos horas, sin información futura. MLflow Project integra ingestión, entrenamiento, búsqueda y servicio. Tracking conserva parámetros, métricas y artefactos. Cookiecutter organiza el código y uv.lock fija las dependencias. El README documenta cómo repetir el proceso.

## 5. Modelo vigente y versión candidata

**Narra:** Kevin Rogelio Rodriguez Magaña

El Registry distingue champion v1, que atiende la API, y challenger v2, un árbol balanceado que evaluamos antes de promoverlo. El Model Card reúne el uso previsto, las métricas y las limitaciones. La corrida de v1 enlaza el artefacto, pero falta identificar su dataset exacto de entrenamiento. Esa brecha permanece documentada y forma parte de los siguientes pasos.

## 6. Arquitectura y validación automática

**Narra:** Kevin Rogelio Rodriguez Magaña

Docker Compose reúne cuatro servicios. Nginx recibe las peticiones y las enruta a FastAPI. La API ejecuta P2 y registra las predicciones en PostgreSQL. Grafana consulta esos registros. Solo Nginx expone un puerto al equipo anfitrión. En cada actualización de main, GitHub Actions ejecuta Ruff y PyTest, construye la imagen y comprueba health. La ejecución consultada terminó correctamente.

## 7. Predicciones registradas en Grafana

**Narra:** Bryan Steve Ortega Castillo

Volvemos al sistema para cerrar el recorrido de la petición. Grafana consulta PostgreSQL y muestra el conteo y las últimas predicciones. Aquí comprobamos las solicitudes que acabamos de ejecutar, con su momento, su clase y el alias champion. Así verificamos la respuesta y su persistencia durante esta ejecución.

## 8. Rendimiento y costo de referencia

**Narra:** Juan Pablo Islas Guzmán

Las pruebas de Locust sumaron ocho mil quinientas cuarenta y tres solicitudes sin fallos. Probamos cinco y veinticinco usuarios durante sesenta segundos por escenario. El segundo alcanzó cerca de ciento veinte solicitudes por segundo. Para FinOps asignamos un servidor de referencia de veinticuatro dólares mensuales. Al ritmo local medido, eso equivale a unos ocho centavos de dólar por millón de inferencias. Es una proyección que requiere validación en la infraestructura objetivo.

## 9. Drift y riesgo de falsas alertas

**Narra:** Juan Pablo Islas Guzmán

Comparamos julio a septiembre de dos mil veinticinco contra el mismo periodo de dos mil veintiséis, con cincuenta mil filas por muestra. Evidently no detectó drift en las ocho variables, aunque capacidad quedó cerca del umbral. En la comparación retrospectiva, v2 mejora la exactitud balanceada y el recall, pero genera ocho veces más falsas alertas. Conservamos v1 provisionalmente y recomendamos calibrar v2 antes de promoverla. Esto tampoco demuestra que v1 alcance un desempeño operativo suficiente.

## 10. Decisiones y siguiente validación

**Narra:** Juan Pablo Islas Guzmán

Mantenemos champion v1 de forma provisional. Los siguientes pasos son cerrar su linaje, calibrar v2 y validar rendimiento y costo en la infraestructura objetivo. El repositorio reúne el código, el Model Card y las evidencias. Gracias.

## Evidencias del proyecto

- [Modelo y límites de uso](model_card_p2.md).
- [Pipeline de datos y MLflow](experimentos_mlflow.md).
- [Contrato y ejecución de la API](api_p2.md).
- [Comparación retrospectiva de versiones](../reports/evidence/p2_ab/README.md).
- [Reporte de drift](../reports/evidence/p2_drift/README.md).
- [Pruebas de carga y FinOps](../reports/evidence/finops/README.md).
