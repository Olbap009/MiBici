# Demo pública temporal con Docker Compose y ngrok

Esta guía explica cómo levantar todo el stack local de MiBici (`nginx`, `api`, `postgres` y `grafana`) con [docker-compose.yml](../docker-compose.yml) y exponerlo temporalmente en internet usando **ngrok**.

---

## 1. ¿Qué servicios se levantan?

Al ejecutar Docker Compose se inician cuatro contenedores conectados en una red interna:

- **`nginx`** (puerto `80`): punto de entrada único. Enruta `/` hacia `api:8000` y `/monitoring/` hacia `grafana:3000`.
- **`api`** (`mibici-p2-api`): API FastAPI con el modelo empaquetado (`models/p2_champion`) que atiende `/ui`, `/docs`, `/health`, `/predict` y `/predict/batch`, y guarda cada predicción en PostgreSQL.
- **`postgres`**: base de datos PostgreSQL 16 con la tabla `predictions` inicializada automáticamente mediante [init.sql](../infra/postgres/init.sql).
- **`grafana`**: dashboard de monitoreo en tiempo real conectado a `postgres` y disponible en `/monitoring/`.

---

## 2. ¿Por qué usamos ngrok?

Por defecto, `docker compose up` solo es accesible desde la propia computadora (`http://localhost`). **ngrok** crea un túnel cifrado (HTTPS) desde una URL pública hacia tu puerto local `80` (Nginx) sin necesidad de:

- Contratar ni administrar una máquina virtual en la nube.
- Abrir puertos en el router o configurar reglas de firewall/NAT.
- Gestionar manualmente dominios ni certificados TLS/HTTPS.

Es ideal para **demos académicas, revisiones de equipo o pruebas rápidas**. Su única limitación es que el enlace público funciona únicamente mientras tu computadora, Docker y el proceso de `ngrok` permanezcan encendidos.

---

## 3. Configuración inicial de ngrok (una sola vez)

1. **Crear una cuenta:** regístrate gratis en [https://ngrok.com/](https://ngrok.com/).
2. **Instalar `ngrok`:**
   - macOS (Homebrew): `brew install ngrok`
   - Otros sistemas o descarga directa: [https://ngrok.com/download](https://ngrok.com/download)
3. **Obtener tu `authtoken`:** en el panel web de ngrok ve a **Your Authtoken** y copia tu token personal.
4. **Configurar el token en tu terminal:**
   ```bash
   ngrok config add-authtoken <TU_AUTHTOKEN>
   ```
   *(Opcional)* En el plan gratuito de ngrok puedes reclamar un **dominio estático gratuito** (por ejemplo `https://tu-subdominio.ngrok-free.dev`) desde **Domains** en el dashboard para conservar siempre la misma URL.

---

## 4. Levantar los servicios y abrir el túnel

1. **Crear el archivo de variables de entorno** (si aún no existe) y ajustar contraseñas en `.env`:
   ```bash
   cp .env.example .env
   ```
2. **Construir y levantar el stack con Docker Compose:**
   ```bash
   docker compose up -d --build
   ```
   *(Opcional si usas `go-task`: `task stack:up`.)*
3. **Verificar que los contenedores estén saludables:**
   ```bash
   docker compose ps
   ```
4. **Exponer el puerto `80` de Nginx con ngrok:**
   - Con URL aleatoria:
     ```bash
     ngrok http 80
     ```
   - Con tu dominio estático gratuito de ngrok:
     ```bash
     ngrok http 80 --url https://<tu-subdominio>.ngrok-free.dev
     ```
   *(Con `go-task`: `task demo:tunnel` o `task demo:tunnel URL=https://<tu-subdominio>.ngrok-free.dev`.)*

> **Nota:** Aunque el asistente de ngrok suele sugerir `8080` como puerto de ejemplo, en este proyecto el proxy **Nginx** escucha en el puerto **`80`**, por lo que debes apuntar `ngrok http` al puerto `80`.

---

## 5. Rutas disponibles desde internet

Una vez activo el túnel, reemplaza `<URL_NGROK>` por la URL HTTPS que muestra `ngrok` (por ejemplo `https://<tu-subdominio>.ngrok-free.dev`):

- **Interfaz web interactiva:** `<URL_NGROK>/ui`
- **Documentación Swagger:** `<URL_NGROK>/docs`
- **Verificación de salud:** `<URL_NGROK>/health`
- **Endpoint de predicción:** `POST <URL_NGROK>/predict`
- **Dashboard de monitoreo (Grafana):** `<URL_NGROK>/monitoring/`

Para detener la exposición pública, presiona `Ctrl+C` en la terminal de `ngrok`. Para detener los contenedores locales:

```bash
docker compose down
```
