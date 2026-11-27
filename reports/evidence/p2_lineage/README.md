# Auditoría de linaje de P2 v1

Consulta del 27 de noviembre de 2026 mediante la API pública de MLflow,
sin modificar corridas, versiones, alias ni artefactos.

## Identidad verificada

La versión `1`, alias `champion`, corresponde a la corrida
`55225195968642979a681bf751d9e2f8` y al modelo registrado
`m-f5e368ba2fb94a4fbf376a1cd6df2aa9`.

El `MLmodel` y el `model.pkl` descargados del Registry coinciden byte a
byte con los de [`models/p2_champion/`](../../../models/p2_champion/).
SHA-256 de `model.pkl`:
`79f72b41f34e5ff13fba3c5d9871d0aa90ba47f9107e27d075e7fc1458d68f35`.

Los identificadores, hashes, lista de artefactos y fuentes públicas quedan
en [`lineage_audit.json`](lineage_audit.json).

## Dataset histórico sin identificar

La corrida se llama `P2_decision_tree_champion_registered`: registra un
modelo existente. No conserva parámetros, métricas ni entradas de
entrenamiento; el objeto de modelo registrado tampoco añade esos datos.
Sus siete artefactos incluyen el estimador, sus dependencias y ejemplos
de inferencia, pero no una tabla de entrenamiento ni su manifiesto.

La etiqueta Git de esa corrida apunta a
`77dc91cb26a3c7c90de5a56f7d7154c20d2fb86a`. El script indicado por la
corrida aún no estaba versionado en ese commit, por lo que esa etiqueta
no basta para reconstruir el contenido local ejecutado.

El árbol contiene 36 muestras en la raíz. Su estructura coincide con la
que produce el ejemplo de pruebas de
[`tests/test_mlproject.py`](../../../tests/test_mlproject.py), pero esa
coincidencia no demuestra qué tabla se utilizó históricamente: distintos
datasets pueden generar el mismo árbol. El ejemplo de entrada guardado
con el modelo tampoco constituye su dataset de entrenamiento.

El hash `65e71b0f8d489210ce185ac3e3de0ab85c0c50df75473128aeb5e32e61a477a3`
identifica el archivo de evaluación y el pipeline de datos. No se atribuye
retrospectivamente al entrenamiento de v1.

## Evidencia necesaria para cerrar la brecha

Recuperar el artefacto local que se seleccionó al publicar v1 y su corrida
original de entrenamiento, junto con el archivo o manifiesto que indique
el dataset, su hash, la partición o muestra, la semilla y el commit de
entrenamiento. Debe comprobarse su relación con el artefacto registrado.

Si esa evidencia no se conserva, debe mantenerse explícita la limitación.
Un nuevo entrenamiento con linaje completo produciría otra versión y
necesitaría su propia evaluación; no reconstruye el historial de v1.

El entrenamiento actual de
[`project_p2.py`](../../../mibici/modeling/project_p2.py) ya registra
hash del dataset, conteos, commit, entrada de MLflow y manifiesto. Esos
registros deben conservarse al trasladar un modelo entre corridas.
