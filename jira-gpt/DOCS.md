# Jira GPT — Documentación

> Asistente conversacional conectado a Jira para planificar y registrar proyectos empresariales desde lenguaje natural.

---

## Tabla de contenidos

### Para todos
- [¿Qué es Jira GPT?](#qué-es-jira-gpt)
- [¿Cómo se usa?](#cómo-se-usa)
- [Ejemplo paso a paso](#ejemplo-paso-a-paso)
- [Preguntas frecuentes](#preguntas-frecuentes)

### Para equipos técnicos
- [Cómo está construido](#cómo-está-construido)
- [Conceptos de Jira](#conceptos-de-jira)
- [Flujos de trabajo detallados](#flujos-de-trabajo-detallados)
- [Referencia de API](#referencia-de-api)
- [Reglas del GPT](#reglas-del-gpt)
- [Infraestructura](#infraestructura)

---

# Para todos

## ¿Qué es Jira GPT?

Jira GPT es un **asistente de inteligencia artificial** que te ayuda a organizar proyectos de tu empresa sin necesidad de saber usar Jira.

Le explicas lo que quieres hacer en lenguaje normal, como si hablaras con un compañero, y él se encarga de crear todo en Jira automáticamente.

**¿Para quién es?** Para cualquier persona de cualquier departamento que quiera planificar un proyecto sin complicaciones.

---

## ¿Cómo se usa?

Es tan sencillo como escribir en un chat. No necesitas saber nada de Jira, ni de programación, ni de herramientas técnicas.

**Solo tienes que:**

1. Abrir el chat con Jira GPT en ChatGPT
2. Describir el proyecto que quieres poner en marcha
3. Responder las preguntas que te haga (departamento, responsable, fechas)
4. Revisar el plan que te propone
5. Confirmar y listo — el GPT lo sube a Jira por ti

---

## Ejemplo paso a paso

Imagina que eres del departamento de Marketing y quieres organizar el lanzamiento de un nuevo producto.

**Tú escribes:**
> "Quiero organizar el lanzamiento del Producto X, vamos a hacer materiales gráficos, una campaña en redes y un evento de presentación"

**El GPT te pregunta:**
> "¿A qué proyecto de Jira lo vinculamos? ¿Quién será el responsable del proyecto? ¿Tienes fechas en mente?"

**Tú respondes** y el GPT te muestra un plan así:

```
Proyecto: Lanzamiento Producto X  (Marketing)
📅 1 abril – 30 junio · Responsable: Laura

- Diseño de materiales gráficos → 1-15 abril
- Campaña en redes sociales → 16-30 abril
- Evento de presentación → 1-20 mayo
- Seguimiento post-lanzamiento → 21 mayo – 30 junio

¿Lo subo a Jira tal como está o quieres ajustar algo?
```

**Tú confirmas** y el GPT crea todo en Jira en segundos.

---

## Preguntas frecuentes

**¿Necesito tener cuenta en Jira?**
No necesitas saber usarla, pero sí debes estar dado de alta como miembro del proyecto en Jira para poder ser asignado como responsable.

**¿Puedo añadir cosas a un proyecto que ya existe?**
Sí. Puedes pedirle al GPT que añada tareas nuevas a un proyecto ya creado o incluso desglosar una tarea en pasos más pequeños.

**¿El GPT sube cosas a Jira sin que yo lo confirme?**
No. Siempre te muestra el plan primero y espera tu aprobación antes de subir nada.

**¿En qué idioma habla?**
Siempre en español, y usa un lenguaje de negocio claro: "acciones", "fases", "entregables". Sin tecnicismos.

**¿Qué pasa si me equivoco o quiero cambiar algo?**
Puedes pedirle que ajuste el plan antes de confirmarlo. Una vez subido a Jira, los cambios hay que hacerlos directamente en Jira o volver a pedírselos al GPT.

---

---

# Para equipos técnicos

## Cómo está construido

El GPT es un **GPT personalizado en ChatGPT** que se comunica con un servicio FastAPI (desplegado en Docker) mediante una especificación OpenAPI. Ese servicio actúa de intermediario con la API de Jira Cloud.

```
ChatGPT (GPT personalizado)
        ↓  OpenAPI / HTTPS
   FastAPI + Docker
        ↓  Jira REST API
      Jira Cloud
```

---

## Conceptos de Jira

Jira GPT mapea la estructura organizativa de la empresa a los tipos de issue de Jira:

| Nivel | Tipo en Jira | Significado en la empresa |
|-------|-------------|--------------------------|
| 0 | **Proyecto** | Departamento (ej: `MKT`, `DATA`) |
| 1 | **Epic** | Proyecto concreto dentro del departamento |
| 2 | **Tarea** | Acción necesaria para completar el proyecto |
| 3 | **Subtarea** | Paso específico dentro de una tarea (opcional) |

---

## Flujos de trabajo detallados

### Crear un proyecto nuevo

El GPT siempre recopila estos tres datos antes de generar el plan:

1. **Epic** — ¿Se vincula a una Epic existente o se crea una nueva?
2. **Responsable** — Seleccionado de los miembros reales del proyecto via `listarUsuariosProyecto`.
3. **Fechas** — Inicio y fin. Si no se indican, el GPT propone un timeline y pide confirmación.

```
Usuario describe el proyecto
       ↓
GPT pregunta: Epic, responsable, fechas
       ↓
GPT presenta el plan en lenguaje de negocio
       ↓
Usuario confirma (o ajusta)
       ↓
GPT sube a Jira con subirIssuesJira
```

---

### Añadir tareas a una Epic existente

1. El GPT llama a `listarEpics` para mostrar las Epics del proyecto.
2. El usuario elige la Epic (el GPT anota su `key`, ej: `DATA-5`).
3. El GPT pregunta qué tareas añadir, responsable y fechas.
4. Muestra el plan y pide confirmación.
5. Sube las tareas con `parent_ref: DATA-5`.

---

### Añadir subtareas a una tarea

1. El GPT llama a `listarEpics` para localizar la Epic y luego a `listarTareasDeEpic` para ver las tareas existentes.
2. El usuario elige la tarea padre (el GPT anota su `key`, ej: `DATA-7`).
3. El GPT pregunta qué subtareas añadir, responsable y fechas.
4. Muestra el plan y pide confirmación.
5. Sube las subtareas con `tipo: Subtarea` y `parent_ref: DATA-7`.

---

### Tabla de acciones disponibles

| Situación | Acción del GPT |
|-----------|---------------|
| No se conoce el KEY del proyecto | `listarProyectos` |
| Añadir tareas a un proyecto existente | `listarEpics` |
| Añadir subtareas a una tarea | `listarTareasDeEpic` |
| Saber quién puede ser responsable | `listarUsuariosProyecto` |
| Crear cualquier issue en Jira | `subirIssuesJira` |

---

## Referencia de API

La API corre como servicio FastAPI expuesto vía ngrok. La URL base se configura en `openapi.json`.

### POST /jira

Crea o actualiza issues en Jira (Epics, Tareas, Subtareas) en un único batch.

**Body:**

```json
{
  "issues": [
    {
      "accion": "crear",
      "tipo": "Epic",
      "proyecto": "MKT",
      "titulo": "Lanzamiento Producto X",
      "ref": "epic-lanzamiento-x",
      "fechaInicio": "2026-04-01",
      "fechaFin": "2026-06-30",
      "asignado": "Laura"
    },
    {
      "accion": "crear",
      "tipo": "Tarea",
      "proyecto": "MKT",
      "titulo": "Diseño de materiales gráficos",
      "parent_ref": "epic-lanzamiento-x",
      "fechaInicio": "2026-04-01",
      "fechaFin": "2026-04-15",
      "asignado": "Laura"
    }
  ]
}
```

**Campos del issue:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `accion` | string | Sí | `crear` \| `actualizar` \| `obtener` \| `listar` |
| `proyecto` | string | Sí | Key del proyecto en Jira (ej: `MKT`, `DATA`) |
| `tipo` | string | Sí | `Epic` \| `Tarea` \| `Subtarea` |
| `titulo` | string | Sí | Título del issue |
| `fechaInicio` | string | Sí | Formato `YYYY-MM-DD` |
| `fechaFin` | string | Sí | Formato `YYYY-MM-DD` |
| `asignado` | string | Sí | Nombre de la persona (la API resuelve el `accountId` automáticamente) |
| `ref` | string | No | Alias local para referenciar como padre (solo Epics nuevas) |
| `parent_ref` | string | No | Alias `ref` de la Epic padre, o key real de Jira (ej: `DATA-5`). Para subtareas, key de la tarea padre. |
| `descripcion` | string | No | Descripción del issue |
| `prioridad` | string | No | `Highest` \| `High` \| `Medium` \| `Low` \| `Lowest` |
| `key` | string | No | Key del issue para acciones `obtener`/`actualizar` (ej: `DATA-5`) |
| `jql` | string | No | Query JQL para la acción `listar` |

**Orden de procesamiento:** El servidor procesa primero los issues con `ref` (Epics) y luego los que tienen `parent_ref` (Tareas/Subtareas), permitiendo referencias cruzadas en el mismo batch.

**Respuesta:**

```json
{
  "procesadas": 5,
  "errores": 0,
  "resultados": [...],
  "errores_detalle": []
}
```

---

### GET /proyectos

Lista los proyectos disponibles en Jira.

**Respuesta:**

```json
{
  "proyectos": [
    { "id": "10001", "key": "MKT", "nombre": "Marketing" },
    { "id": "10002", "key": "DATA", "nombre": "Data & Analytics" }
  ]
}
```

---

### GET /epics

Lista las Epics de un proyecto con su estado, responsable y fechas.

**Parámetros:**

| Parámetro | Requerido | Descripción |
|-----------|-----------|-------------|
| `proyecto` | Sí | Key o nombre del proyecto (ej: `DATA`, `MKT`) |

**Respuesta:**

```json
{
  "proyecto": "DATA",
  "epics": [
    {
      "key": "DATA-3",
      "titulo": "Migración de base de datos",
      "estado": "En progreso",
      "responsable": "Santiago",
      "fechaInicio": "2026-03-01",
      "fechaFin": "2026-04-30",
      "url": "https://..."
    }
  ]
}
```

> El campo `key` de cada Epic debe usarse como `parent_ref` al crear tareas vinculadas a ella.

---

### GET /tareas

Lista las tareas y subtareas de una Epic.

**Parámetros:**

| Parámetro | Requerido | Descripción |
|-----------|-----------|-------------|
| `epic` | Sí | Key de Jira de la Epic (ej: `DATA-5`) |

**Respuesta:**

```json
{
  "epic": "DATA-5",
  "tareas": [
    {
      "key": "DATA-7",
      "tipo": "Tarea",
      "titulo": "Análisis de datos actuales",
      "estado": "To Do",
      "responsable": "Ana",
      "fechaInicio": "2026-03-01",
      "fechaFin": "2026-03-15",
      "url": "https://..."
    }
  ]
}
```

> El campo `key` de cada tarea debe usarse como `parent_ref` al crear subtareas.

---

### GET /usuarios

Lista los usuarios asignables a un proyecto Jira.

**Parámetros:**

| Parámetro | Requerido | Descripción |
|-----------|-----------|-------------|
| `proyecto` | Sí | Key o nombre del proyecto (ej: `DATA`, `MKT`) |

**Respuesta:**

```json
{
  "proyecto": "DATA",
  "usuarios": [
    { "nombre": "Santiago", "email": "santiago@empresa.com" },
    { "nombre": "Laura", "email": "laura@empresa.com" }
  ]
}
```

---

## Reglas del GPT

- **Nunca sube nada sin tener definidos: Epic, responsable y fechas.** Si falta alguno, pregunta antes de continuar.
- El plan siempre se muestra en formato legible (nunca como JSON) antes de subirlo.
- Habla siempre en **español** con lenguaje de negocio. Sin jerga técnica de software.
- Las **Epics siempre van primeras** en el JSON enviado a la API y llevan un valor en `ref`.
- Las **Tareas** llevan ese mismo valor en `parent_ref`, o el key real de Jira si la Epic ya existe.
- Las **Subtareas** llevan en `parent_ref` el key de la tarea padre.

---

## Infraestructura

| Componente | Detalle |
|-----------|---------|
| GPT | ChatGPT (GPT personalizado) |
| Backend | FastAPI desplegado en Docker (`apps/jira-gpt`) |
| Túnel | ngrok (URL configurada en `openapi.json`) |
| Integración | Jira Cloud API |

> **Nota:** La URL del servidor en `openapi.json` apunta a ngrok y puede cambiar si se reinicia el túnel. Actualizar el campo `servers[0].url` con la nueva URL en ese caso.

---

### Archivos del repositorio

| Archivo | Descripción |
|---------|-------------|
| [prompt.md](prompt.md) | Instrucciones del sistema del GPT |
| [openapi.json](openapi.json) | Schema OpenAPI 3.0 para las acciones del GPT |
| [DOCS.md](DOCS.md) | Esta documentación |
