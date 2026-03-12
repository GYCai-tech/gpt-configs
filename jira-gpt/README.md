# Jira GPT

GPT de ChatGPT conectado a Jira para planificar y crear proyectos desde lenguaje natural.

## Archivos

- `prompt.md` — Instrucciones del sistema del GPT
- `openapi.json` — Schema de la API para las acciones del GPT

## API (jira-gpt)

Servicio FastAPI desplegado en Docker en `apps/jira-gpt`.

### Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/jira` | Crea o actualiza issues (Epics, Tareas, Subtareas) |
| GET | `/proyectos` | Lista los proyectos disponibles en Jira |
| GET | `/epics?proyecto=DATA` | Lista las Epics de un proyecto |
| GET | `/tareas?epic=DATA-5` | Lista las tareas de una Epic |

### Notas

- El campo `asignado` acepta nombre de persona (ej: Santiago). La API resuelve el `accountId` automáticamente.
- El campo `parent_ref` acepta tanto alias locales (para Epics creadas en el mismo batch) como keys reales de Jira (ej: `DATA-5`).
- La URL del servidor en `openapi.json` apunta a ngrok y puede cambiar si se reinicia el tunnel.
