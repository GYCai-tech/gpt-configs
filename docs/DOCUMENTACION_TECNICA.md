# Documentación técnica — GPTs corporativos y su API (gpt-configs)

Documento de relevo para quien mantenga los GPT de ChatGPT de la empresa y la API que usan. Para el uso
del día a día ver [GUIA_SOPORTE.md](GUIA_SOPORTE.md).

---

> **Aviso de seguridad (leer primero).** En el estado actual de `main`:
>
> 1. `main.py` contiene **credenciales escritas en el código** y subidas a GitHub: el token de la API de
>    Jira (cabecera `Basic`), usuario y contraseña del ERP SQL Server (`10.0.0.6`) y usuario y contraseña
>    de `gyc_analytics` (`gyc_etl`). Deben considerarse **comprometidas**: rotarlas y pasarlas a un `.env`.
> 2. La API **no tiene ninguna autenticación** y el `docker-compose.yml` la publica en internet con un
>    túnel **ngrok** (la URL está en los `openapi.json`).
> 3. `/query` y `/query-dw` ejecutan **el SQL que se les envíe** contra el ERP y contra `gyc_analytics`;
>    lo único que se comprueba es que la primera palabra sea `SELECT` o `WITH`.
>
> En conjunto, quien conozca la URL puede leer datos del ERP y del data warehouse y operar sobre Jira con la
> cuenta de la empresa. Ver el apartado 7.

## 1. Resumen

| Aspecto | Detalle |
|---|---|
| Qué es | Instrucciones y esquemas de **tres GPT personalizados de ChatGPT** + la API FastAPI que les da acceso a Jira, al ERP y al data warehouse |
| Repositorio | `GYCai-tech/gpt-configs` (rama `main`) |
| Stack API | Python 3.11, FastAPI + uvicorn, `requests` (Jira Cloud REST v3), pyodbc (ODBC Driver **17**), psycopg2 |
| Ejecución | Docker: contenedor `jira-gpt` (puerto 8090) + contenedor `ngrok-jira-gpt` (túnel; inspector en 4041) |
| Producción | `/home/goyco/apps/gpts` en `10.0.0.12`. Los GPT llaman a la URL pública de ngrok |
| Tests / CI | No hay |

## 2. Archivos

| Ruta | Qué es |
|---|---|
| `main.py` | La API completa (Jira, consultas SQL, webhook Synapsales) |
| `openapi-gpt.json` | Esquema de acciones del GPT de Jira con `/query` (versión con acceso al ERP) |
| `jira-gpt/prompt.md`, `jira-gpt/openapi.json` | GPT de **gestión de proyectos en Jira** |
| `produccion-gpt/prompt.md`, `openapi.json`, `schema.md` | GPT de **análisis de producción** sobre `analytics.*` vía `/query-dw` |
| `documentador-iso/prompt.md`, `dict_schema.md`, `generar_iso.py` | GPT **Documentador ISO**: redacta procedimientos y genera el Word con Code Interpreter (no usa la API) |
| `Dockerfile`, `docker-compose.yml`, `start.sh` | Despliegue (`start.sh` es un arranque manual antiguo que apunta a `/home/goyco/apps/jira-gpt`) |

Los `prompt.md` y `openapi.json` **no se aplican solos**: hay que copiarlos a mano en el editor de cada GPT
en ChatGPT (Instrucciones y Acciones). El repositorio es la copia de referencia.

## 3. API

| Método y ruta | Qué hace |
|---|---|
| `POST /jira` | Crea, consulta, lista o actualiza issues por lotes (`accion` por fila). Resuelve proyecto, tipo, usuario y padre (`parent_ref` local o key real) |
| `POST /jira-csv` | Lo mismo desde un CSV subido |
| `GET /proyectos` · `/usuarios?proyecto=` · `/epics?proyecto=` · `/tareas?epic=` | Consultas a Jira |
| `GET /issues?proyecto=&tipo=&asignado=` · `/worklogs?proyecto=&asignado=&dias=` | Issues y horas imputadas |
| `POST /query` | SQL contra el ERP `GOMEZYCRESPO`; máx. 500 filas; anonimiza columnas llamadas `empleado`, `operario`, `descripemp`, `nombre`, `trabajador` (`OP-xxxxx`) |
| `POST /query-dw` | SQL contra `gyc_analytics`; máx. 500 filas |
| `POST /synapsales/contacto` | Webhook de leads de Synapsales (ver trampas) |
| `GET /health` | `{"status":"ok"}` |

### 3.1 Jira

- Base `https://gomezycrespo.atlassian.net`. Cada persona tiene un **espacio** (proyecto Jira); las
  **Epics** son proyectos concretos, las **Tareas/Subtareas** el trabajo.
- `tiempoEstimado` (horas) → `timetracking.originalEstimate`; `fechaInicio` → `customfield_10015`;
  `fechaFin` → `duedate`.
- Cachés en memoria de proyectos, tipos y usuarios (se pierden al reiniciar).

### 3.2 GPT de producción

Consulta las vistas `analytics.v_ordenes_activas`, `v_ordenes_olvidadas`, `v_tiempos_por_articulo`,
`v_carga_trabajo_empleado`, `v_comparativa_carga_empleado` y `v_carga_trabajo_maquina` (descritas en
`produccion-gpt/schema.md`). El GPT genera el SQL; la API lo ejecuta tal cual.

### 3.3 Documentador ISO

No depende de la API. En el GPT se suben como conocimiento `generar_iso.py`, la plantilla
`PLANTILLA_PROCEDIMIENTO.docx` (no está en el repositorio) y los procedimientos existentes. El GPT
entrevista sección por sección y llama a `generar(data)` en Code Interpreter para producir el `.docx`.

## 4. Ejecutar

```bash
# .env con NGROK_AUTHTOKEN (el resto de credenciales, hoy, están en main.py)
docker compose up -d --build
curl http://localhost:8090/health
```

La URL pública la da ngrok (inspector en `http://<servidor>:4041`). Si cambia, hay que actualizar
`servers` en cada `openapi.json` **y** en las Acciones de cada GPT en ChatGPT.

## 5. Despliegue actual

| Qué | Valor |
|---|---|
| Carpeta | `/home/goyco/apps/gpts` |
| Puertos | 8090 (API), 4041 (inspector ngrok) |
| Remoto en el servidor | HTTPS sin credenciales de escritura: `pull` sí, `push` no |
| Actualizar | `git pull && docker compose up -d --build`, y copiar a ChatGPT los prompts/esquemas cambiados |

## 6. Cambios habituales

| Quiero… | Dónde |
|---|---|
| Cambiar el comportamiento de un GPT | Su `prompt.md` y pegarlo en ChatGPT |
| Añadir una acción | Endpoint en `main.py` + `openapi.json` + pegar el esquema en ChatGPT |
| Añadir vistas al GPT de producción | `schema.md` y la guía de vistas de `prompt.md` |
| Cambiar la plantilla ISO | Subir la nueva `PLANTILLA_PROCEDIMIENTO.docx` al GPT (y revisar `generar_iso.py`) |

## 7. Trampas y riesgos conocidos

- **Credenciales en el código** (ver aviso inicial). Rotar: token de Jira, usuario del ERP, `gyc_etl` y,
  por precaución, el token de ngrok. Después, leerlas de variables de entorno y purgar el historial o, como
  mínimo, dar las antiguas por revocadas.
- **Sin autenticación + ngrok**: añadir al menos una API key (las Acciones de los GPT admiten cabecera
  `Authorization`/API key) o servirla solo por una vía controlada.
- **SQL libre**: usar usuarios de base de datos de **solo lectura** con acceso a lo estrictamente necesario
  (en el DW hoy se usa `gyc_etl`, el usuario del ETL). Sustituir el filtro por primera palabra por
  permisos reales.
- **Anonimización débil**: solo por nombre de columna; un alias (`AS persona`) la esquiva.
- **Webhook Synapsales roto**: `/synapsales/contacto` está definido dos veces; FastAPI usa el primero (solo
  registra en el log). El segundo, que haría `INSERT … ON CONFLICT` en `marketing.fact_leads_linkedin`,
  nunca se ejecuta y además usa `DW_CONN`, que no está definido. **Ningún lead se está guardando.**
- La URL de ngrok gratuita puede cambiar al reiniciar el túnel: los GPT dejan de funcionar hasta
  actualizar el esquema.
- El `Dockerfile` instala `msodbcsql17` desde el repositorio apt de Microsoft (firma SHA-1 rechazada desde
  2026-02 en otras imágenes); un rebuild puede fallar en ese paso.
- Dependencias sin versión en el `Dockerfile`.

## 8. Checklist de relevo

- [ ] Credenciales rotadas y fuera del código.
- [ ] Decidido cómo se protege la API (API key, red privada…).
- [ ] Acceso de edición a los tres GPT en ChatGPT y lista de quién los usa.
- [ ] Plantilla `PLANTILLA_PROCEDIMIENTO.docx` localizada.
- [ ] Webhook de Synapsales corregido o dado de baja.
