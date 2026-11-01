# Auditoría y Chequeos de Seguridad Básicos — Proyecto MiBici (Equipo 23)

## 1. Resumen Ejecutivo

Como parte de los requerimientos de calidad y confiabilidad del proyecto integrador, se realizó una auditoría de seguridad integral orientada a:
1. **Prevenir la fuga de datos sensibles y credenciales** mediante buenas prácticas en `.gitignore`, plantillas de variables de entorno y hooks de prevención.
2. **Ejecutar análisis estático de seguridad de código (SAST)** utilizando **Bandit** sobre el paquete principal `mibici`.
3. **Ejecutar análisis de composición de software y vulnerabilidades de dependencias (SCA)** utilizando **pip-audit** sobre el entorno y árbol de dependencias (`uv.lock`).
4. **Remediar vulnerabilidades detectadas** y documentar evidencias reproducibles.

### Resumen de Resultados

| Control de Seguridad | Herramienta / Mecanismo | Resultado | Estado |
| :--- | :--- | :--- | :--- |
| **Exposición de secretos y credenciales** | Escaneo regex de código e historial Git | 0 credenciales ni contraseñas expuestas | **APROBADO** |
| **Prevención de fugas en Git** | `.gitignore` robustecido + `.pre-commit-config.yaml` (`detect-private-key`) | Reglas exhaustivas para `.env`, llaves nube, certs y db | **APROBADO** |
| **Plantilla de variables de entorno** | `.env.example` | Plantilla documentada sin valores sensibles reales | **APROBADO** |
| **Análisis estático de código (SAST)** | **Bandit 1.9.4** | 0 vulnerabilidades High, 0 Medium, 24 Low (subprocesos controlados de git hash) | **APROBADO** |
| **Auditoría de dependencias (SCA)** | **pip-audit 2.10.1** | Remediadas 86 de 91 vulnerabilidades previas con actualización de lockfile | **APROBADO / CONTROLADO** |

---

## 2. Auditoría de Credenciales, Contraseñas y Datos Sensibles

### 2.1 Escaneo del Repositorio e Historial
Se ejecutó un escaneo automatizado en busca de patrones comunes de secretos:
- Claves privadas (`-----BEGIN PRIVATE KEY-----`, RSA, EC, OpenSSH).
- Patrones de tokens de API (Google API Keys `AIza...`, GitHub Personal Access Tokens `ghp_...`, AWS Access Keys `AKIA...`).
- Asignaciones de contraseñas (`password = "..."`, `secret = "..."`, etc.).

**Resultado:** No se encontraron credenciales, contraseñas ni tokens en el código fuente ni en el historial de Git activo.

### 2.2 Robustecimiento de `.gitignore`
Se actualizó el archivo `.gitignore` para bloquear proactivamente la inclusión accidental de:
- Archivos de entorno y secretos: `.env`, `.env.*` (excepto `.env.example`), `*.env`, `.secrets*`, `*.token`.
- Certificados y llaves criptográficas: `*.pem`, `*.key`, `*.crt`, `*.p12`, `*.pfx`, `id_rsa*`, `id_ed25519*`.
- Credenciales de servicios en la nube: `*credentials*.json`, `*secret*.json`, `service_account*.json`, `gcp_key*.json`, `aws_*.json`, `.aws/`, `.gcp/`.
- Bases de datos locales y artefactos temporales: `*.db`, `mlruns.db`, `/data/`, `*.pkl`, `*.joblib`.

### 2.3 Variables de Entorno y `.env.example`
Se creó el archivo `.env.example` en la raíz del repositorio, sirviendo como guía para desarrolladores sin exponer secretos reales. En `mibici/config.py`, se utiliza `python-dotenv` para cargar variables de entorno en tiempo de ejecución de manera segura.

Variables estandarizadas en `.env.example`:
- `MLFLOW_TRACKING_URI`: Endpoint o base de datos local SQLite para registro de ejecuciones.
- `MLFLOW_EXPERIMENT_NAME`: Nombre del experimento activo.
- `GOOGLE_APPLICATION_CREDENTIALS`: Ruta local a credenciales de servicio de Google Cloud para DVC (opcional).
- `LOG_LEVEL`: Nivel de severidad para `loguru`.

### 2.4 Control Preventivo en Pre-Commit
Se integró el hook oficial `detect-private-key` y `check-added-large-files` dentro de `.pre-commit-config.yaml` para impedir commits que contengan accidentalmente claves privadas o archivos binarios voluminosos.

---

## 3. Análisis Estático de Código (SAST) con Bandit

Se ejecutó **Bandit 1.9.4** escaneando los 2,656 renglones de código fuente en `mibici/`:

```bash
uv run bandit -r mibici -ll
```

### Resultados de Bandit
- **Severidad Alta (High):** 0 incidencias.
- **Severidad Media (Medium):** 0 incidencias activas.
  * *Hallazgo inicial:* Bandit señalaba `B310` (uso de `urllib.request.urlopen` sin verificación estricta de esquema en `dataset.py`, `train_p1.py` y `train_p3.py`).
  * *Remediación:* Se incorporó validación explícita para asegurar que únicamente se permitan esquemas `http` y `https` antes de realizar cualquier solicitud de red, neutralizando el riesgo de esquemas inseguros como `file://`.
- **Severidad Baja (Low):** 24 incidencias correspondientes a llamadas de `subprocess.check_output(["git", "rev-parse", "HEAD"])` para capturar el hash de commit y asegurar la trazabilidad en MLflow. Estas llamadas no aceptan entrada de usuario externa y se ejecutan en entorno controlado.

**Evidencias generadas:**
- `reports/security/bandit_report.txt` (reporte completo en texto plano).
- `reports/security/bandit_report.json` (reporte estructurado en formato JSON).

---

## 4. Análisis de Vulnerabilidades en Dependencias (SCA) con pip-audit

Se ejecutó **pip-audit 2.10.1** consultando la base de datos oficial de vulnerabilidades (PyPI / OSV).

```bash
uv run pip-audit
```

### Proceso de Remediación
1. **Diagnóstico Inicial:** El entorno base contenía 91 vulnerabilidades conocidas en dependencias transitivas heredadas (como versiones desactualizadas de `cryptography`, `pillow`, `filelock`, `virtualenv`, `tornado`, `certifi`, etc.).
2. **Remediación Automatizada:** Se ejecutó una actualización controlada del archivo de bloqueo con `uv lock --upgrade` respetando las restricciones directas del proyecto (`pyproject.toml`).
3. **Resultado Post-Remediación:** Se mitigaron con éxito **86 vulnerabilidades**.
4. **Estado de las 5 vulnerabilidades restantes (bajo monitoreo):**
   - `mlflow (3.16.1)`: 3 CVEs conocidos (CVE-2026-53995, CVE-2026-115886, CVE-2026-116691). La versión se mantiene fijada en `3.16.1` en `pyproject.toml` debido a la compatibilidad contractual de MLflow Projects en la infraestructura académica.
   - `diskcache (5.6.3)`: 2 avisos (PYSEC-2026-2447). Dependencia interna de DVC sin versión de corrección publicada a la fecha por el mantenedor original upstream.

**Evidencias generadas:**
- `reports/security/pip_audit_report.md` (tabla resumen en formato Markdown).
- `reports/security/pip_audit_report.txt` (reporte detallado en columnas).
- `reports/security/pip_audit_report.json` (reporte estructurado en formato JSON).

---

## 5. Instrucciones de Reproducción

Los chequeos de seguridad pueden ejecutarse en cualquier momento con un solo comando mediante `Taskfile` o `uv`:

### Con Taskfile (Recomendado):
```bash
# Ejecutar análisis estático Bandit (solo severidad Media/Alta)
task security:bandit

# Ejecutar auditoría de dependencias pip-audit
task security:audit

# Ejecutar ambos chequeos en secuencia
task security:check

# Regenerar todos los reportes de evidencia en reports/security/
task security:report
```

### Con uv directamente:
```bash
# Análisis estático de código
uv run bandit -r mibici -ll

# Auditoría de dependencias
uv run pip-audit -f markdown -o reports/security/pip_audit_report.md
```
