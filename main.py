import csv
import io
import json
import logging
import re
import requests
import pyodbc
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-gpt")

app = FastAPI(title="Jira GPT API")

JIRA_BASE_URL = "https://gomezycrespo.atlassian.net"
JIRA_AUTH = "Basic Y29udGFjdEBnb21lenljcmVzcG8uY29tOkFUQVRUM3hGZkdGMGRUbVdmb3hzVi1qN3JqZWo3ZGJVdnBYalM5akM5Z0VTT3RidDRvMXlBbVY3N2pka1lZdFJ5Tm9BRlZJVVY0c1ltN2xGck0zeVh4ajRSaWFodXRuN2VCSDhlYXM4NUlkSWYwZDVld3lvWGxfRkJROVExZERPYWgzTmwzWkZRVE1LYVVlNGdmaXpicDR6T0RwUG5Rbm4ybjRZNlRXcUxaZ2xUNzUteHNYWTltRT02NDNCREVDMw=="
HEADERS = {
    "Authorization": JIRA_AUTH,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

_tipos_cache = {}
_proyectos_cache = {}
_usuarios_cache = {}


def resolver_usuario(nombre: str) -> str:
    """Busca un usuario en Jira por nombre o email y devuelve su accountId."""
    nombre = nombre.strip()
    if not nombre:
        return ""
    clave = nombre.lower()
    if clave in _usuarios_cache:
        return _usuarios_cache[clave]

    # Intento 1: búsqueda general
    r = requests.get(
        f"{JIRA_BASE_URL}/rest/api/3/user/search",
        headers=HEADERS,
        params={"query": nombre, "maxResults": 10}
    )
    r.raise_for_status()
    usuarios = r.json()

    # Intento 2: si no hay resultados, buscar en usuarios asignables de todos los proyectos
    if not usuarios:
        proyectos = get_proyectos()
        keys_vistos = set()
        for key in proyectos.values():
            if key in keys_vistos:
                continue
            keys_vistos.add(key)
            rp = requests.get(
                f"{JIRA_BASE_URL}/rest/api/3/user/assignable/search",
                headers=HEADERS,
                params={"project": key, "maxResults": 50}
            )
            if rp.ok:
                usuarios.extend(rp.json())

    if not usuarios:
        raise ValueError(f"Usuario '{nombre}' no encontrado en Jira.")

    # Coincidencia parcial por displayName
    match = next((u for u in usuarios if clave in u.get("displayName", "").lower()), None)
    if not match:
        match = usuarios[0]
    account_id = match["accountId"]
    _usuarios_cache[clave] = account_id
    return account_id


def get_proyectos(force_refresh: bool = False) -> dict:
    if _proyectos_cache and not force_refresh:
        return _proyectos_cache
    _proyectos_cache.clear()
    r = requests.get(f"{JIRA_BASE_URL}/rest/api/3/project/search", headers=HEADERS)
    r.raise_for_status()
    for p in r.json().get("values", []):
        _proyectos_cache[p["name"].lower()] = p["key"]
        _proyectos_cache[p["key"].lower()] = p["key"]
        _proyectos_cache[p["id"]] = p["key"]
    return _proyectos_cache


def resolver_proyecto_key(nombre: str) -> str:
    clave = nombre.strip().lower()
    proyectos = get_proyectos()
    key = proyectos.get(clave)
    if not key:
        # Reintenta con caché refrescada por si el proyecto es nuevo
        proyectos = get_proyectos(force_refresh=True)
        key = proyectos.get(clave)
    if not key:
        # Búsqueda parcial: busca proyectos cuyo nombre contenga la cadena buscada
        match = next((v for k, v in proyectos.items() if clave in k), None)
        key = match
    if not key:
        raise ValueError(f"Proyecto '{nombre}' no encontrado.")
    return key


def get_tipos_incidencia(project_key: str) -> list:
    if project_key in _tipos_cache:
        return _tipos_cache[project_key]
    # Obtener el ID numérico del proyecto
    r = requests.get(f"{JIRA_BASE_URL}/rest/api/3/project/{project_key}", headers=HEADERS)
    r.raise_for_status()
    project_id = r.json()["id"]
    r2 = requests.get(
        f"{JIRA_BASE_URL}/rest/api/3/issue/createmeta/{project_id}/issuetypes",
        headers=HEADERS
    )
    r2.raise_for_status()
    tipos = r2.json().get("issueTypes", [])
    _tipos_cache[project_key] = tipos
    return tipos


NOMBRES_SUBTAREA = {"subtarea", "subtask", "sub-task", "sub tarea"}

def resolver_tipo(project_key: str, tipo_buscado: str = "") -> str:
    tipos = get_tipos_incidencia(project_key)
    tipo_buscado = tipo_buscado.strip().lower()

    # Si el usuario pide explícitamente una subtarea, buscar tipos con subtask=True
    if tipo_buscado in NOMBRES_SUBTAREA:
        match = next((t for t in tipos if t.get("subtask")), None)
        if match:
            return match["id"]

    if tipo_buscado:
        match = next((t for t in tipos if t["name"].lower() == tipo_buscado), None)
        if match:
            return match["id"]

    for nombre in ["tarea", "task", "historia", "story", "función", "funcion"]:
        match = next((t for t in tipos if t["name"].lower() == nombre), None)
        if match:
            return match["id"]

    match = next((t for t in tipos if not t.get("subtask") and t["name"].lower() != "epic"), None)
    if match:
        return match["id"]

    return tipos[0]["id"] if tipos else ""


def construir_fields(row: dict, ref_map: dict) -> dict:
    project_key = resolver_proyecto_key(row["proyecto"])
    issue_type_id = resolver_tipo(project_key, row.get("tipo", ""))

    fields = {
        "project": {"key": project_key},
        "issuetype": {"id": issue_type_id},
        "summary": row["titulo"],
    }

    if row.get("descripcion"):
        fields["description"] = {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": row["descripcion"]}]}]
        }

    if row.get("asignado"):
        account_id = resolver_usuario(row["asignado"])
        if account_id:
            fields["assignee"] = {"accountId": account_id}

    if row.get("prioridad"):
        fields["priority"] = {"name": row["prioridad"].strip()}

    # Fecha fin → duedate
    if row.get("fechaFin"):
        fields["duedate"] = row["fechaFin"].strip()

    # Fecha inicio → customfield_10015 (Start date, usado en el cronograma)
    if row.get("fechaInicio"):
        fields["customfield_10015"] = row["fechaInicio"].strip()

    # Tiempo estimado en horas → timetracking.originalEstimate (estimación original)
    if row.get("tiempoEstimado"):
        horas = float(row["tiempoEstimado"])
        horas_int = int(horas)
        minutos = int(round((horas % 1) * 60))
        if minutos:
            estimacion_str = f"{horas_int}h {minutos}m"
        else:
            estimacion_str = f"{horas_int}h"
        fields["timetracking"] = {"originalEstimate": estimacion_str}

    # Padre: puede ser un key de Jira directo o una referencia local del CSV
    parent_ref = row.get("parent_ref", "").strip()
    if parent_ref:
        parent_key = ref_map.get(parent_ref)
        if not parent_key:
            # Comprobar si parece una key de Jira real (ej: DATA-1) o una ref local no resuelta
            if re.match(r'^[A-Z]+-\d+$', parent_ref):
                parent_key = parent_ref
            else:
                raise ValueError(
                    f"La referencia de padre '{parent_ref}' no fue resuelta. "
                    f"Probablemente el issue padre falló al crearse."
                )
        fields["parent"] = {"key": parent_key}

    return fields


def crear_issue(row: dict, ref_map: dict) -> dict:
    fields = construir_fields(row, ref_map)
    r = requests.post(f"{JIRA_BASE_URL}/rest/api/3/issue", headers=HEADERS, json={"fields": fields})
    r.raise_for_status()
    data = r.json()
    return {"ok": True, "key": data["key"], "url": f"{JIRA_BASE_URL}/browse/{data['key']}"}


def obtener_issue(row: dict, ref_map: dict) -> dict:
    r = requests.get(f"{JIRA_BASE_URL}/rest/api/3/issue/{row['key']}", headers=HEADERS)
    r.raise_for_status()
    d = r.json()
    return {
        "ok": True,
        "key": d["key"],
        "titulo": d["fields"]["summary"],
        "estado": d["fields"]["status"]["name"],
        "tipo": d["fields"]["issuetype"]["name"],
    }


def listar_issues(row: dict, ref_map: dict) -> dict:
    jql = row.get("jql", f"project = \"{row.get('proyecto', '')}\" ORDER BY created DESC")
    r = requests.post(
        f"{JIRA_BASE_URL}/rest/api/3/search/jql",
        headers=HEADERS,
        json={"jql": jql, "maxResults": 20, "fields": ["summary", "status", "issuetype", "assignee"]}
    )
    r.raise_for_status()
    issues = r.json().get("issues", [])
    return {
        "ok": True,
        "total": len(issues),
        "issues": [{"key": i["key"], "titulo": i["fields"]["summary"], "estado": i["fields"]["status"]["name"]} for i in issues]
    }


def actualizar_issue(row: dict, ref_map: dict) -> dict:
    fields = {}
    if row.get("titulo"):
        fields["summary"] = row["titulo"]
    if row.get("descripcion"):
        fields["description"] = {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": row["descripcion"]}]}]
        }
    if row.get("asignado"):
        account_id = resolver_usuario(row["asignado"])
        if account_id:
            fields["assignee"] = {"accountId": account_id}
    if row.get("fechaFin"):
        fields["duedate"] = row["fechaFin"].strip()
    if row.get("fechaInicio"):
        fields["customfield_10015"] = row["fechaInicio"].strip()
    if row.get("tiempoEstimado"):
        horas = float(row["tiempoEstimado"])
        horas_int = int(horas)
        minutos = int(round((horas % 1) * 60))
        if minutos:
            estimacion_str = f"{horas_int}h {minutos}m"
        else:
            estimacion_str = f"{horas_int}h"
        fields["timetracking"] = {"originalEstimate": estimacion_str}

    r = requests.put(f"{JIRA_BASE_URL}/rest/api/3/issue/{row['key']}", headers=HEADERS, json={"fields": fields})
    r.raise_for_status()
    return {"ok": True, "key": row["key"], "actualizado": list(fields.keys())}


ACCIONES = {
    "crear": crear_issue,
    "obtener": obtener_issue,
    "listar": listar_issues,
    "actualizar": actualizar_issue,
}


def _procesar_filas(filas: list) -> dict:
    resultados = []
    errores = []
    ref_map = {}

    primera_pasada = [f for f in filas if f.get("ref", "").strip()]
    segunda_pasada = [f for f in filas if not f.get("ref", "").strip()]

    for pasada in [primera_pasada, segunda_pasada]:
        for row in pasada:
            try:
                fila_num = filas.index(row) + 2
            except ValueError:
                fila_num = "?"

            accion = row.get("accion", "").strip().lower()
            if not accion:
                continue

            fn = ACCIONES.get(accion)
            if not fn:
                errores.append({"fila": fila_num, "error": f"Acción desconocida: '{accion}'"})
                continue

            try:
                resultado = fn(row, ref_map)
                resultado["fila"] = fila_num
                resultado["accion"] = accion
                resultado["titulo"] = row.get("titulo", "")
                ref = row.get("ref", "").strip()
                if ref and resultado.get("key"):
                    ref_map[ref] = resultado["key"]
                resultados.append(resultado)
            except requests.HTTPError as e:
                errores.append({"fila": fila_num, "accion": accion, "titulo": row.get("titulo", ""), "error": e.response.text})
            except Exception as e:
                errores.append({"fila": fila_num, "accion": accion, "titulo": row.get("titulo", ""), "error": str(e)})

    return {"procesadas": len(resultados), "errores": len(errores), "resultados": resultados, "errores_detalle": errores}


class IssueRow(BaseModel):
    accion: str
    proyecto: Optional[str] = ""
    tipo: Optional[str] = ""
    ref: Optional[str] = ""
    parent_ref: Optional[str] = ""
    titulo: Optional[str] = ""
    descripcion: Optional[str] = ""
    fechaInicio: Optional[str] = ""
    fechaFin: Optional[str] = ""
    asignado: Optional[str] = ""
    prioridad: Optional[str] = ""
    key: Optional[str] = ""
    jql: Optional[str] = ""
    tiempoEstimado: Optional[float] = None


class IssuesPayload(BaseModel):
    issues: List[IssueRow]


@app.post("/jira")
def procesar_issues(payload: IssuesPayload):
    """
    Recibe un array de issues y los ejecuta en Jira.
    Se procesan primero los que tienen 'ref' (Epics), luego el resto.
    """
    filas = [i.model_dump() for i in payload.issues]
    logger.info(f"REQUEST /jira: {json.dumps(filas, ensure_ascii=False)}")
    resultado = _procesar_filas(filas)
    logger.info(f"RESPONSE /jira: {json.dumps(resultado, ensure_ascii=False)}")
    return resultado


@app.post("/jira-csv")
async def procesar_csv(file: UploadFile = File(...)):
    """
    Recibe un CSV y crea/actualiza issues en Jira.

    Columnas del CSV:
    - accion: crear | obtener | listar | actualizar
    - proyecto: nombre o key del proyecto (ej: DAT)
    - tipo: Epic | Tarea | Subtarea | Función (opcional, por defecto Tarea)
    - ref: alias local para referenciar este issue como padre en otras filas (ej: epic-login)
    - parent_ref: alias local de la Epic padre, o key de Jira directamente (ej: DAT-1)
    - titulo: resumen del issue
    - descripcion: descripción detallada (opcional)
    - fechaInicio: fecha de inicio en formato YYYY-MM-DD (opcional)
    - fechaFin: fecha de vencimiento en formato YYYY-MM-DD (opcional)
    - asignado: accountId del usuario en Jira (opcional)
    - key: key del issue para obtener/actualizar (ej: DAT-5)
    - jql: query JQL para la acción listar (opcional)

    El CSV se procesa en dos pasadas:
    1. Se crean primero los issues con columna 'ref' (típicamente Epics)
    2. Se crean el resto resolviendo las referencias de parent_ref
    """
    contenido = await file.read()
    texto = contenido.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(texto))
    filas = list(reader)
    return JSONResponse(_procesar_filas(filas))


@app.get("/usuarios")
def listar_usuarios_proyecto(proyecto: str):
    """
    Lista los usuarios asignables a un proyecto Jira.
    Parámetro: proyecto (key o nombre del proyecto, ej: DATA)
    """
    try:
        project_key = resolver_proyecto_key(proyecto)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    r = requests.get(
        f"{JIRA_BASE_URL}/rest/api/3/user/assignable/search",
        headers=HEADERS,
        params={"project": project_key, "maxResults": 50}
    )
    r.raise_for_status()
    usuarios = [
        {"nombre": u["displayName"], "email": u.get("emailAddress", "")}
        for u in r.json()
        if u.get("active", True)
    ]
    return {"proyecto": project_key, "usuarios": usuarios}


@app.get("/proyectos")
def listar_proyectos():
    """Lista todos los proyectos disponibles en Jira."""
    r = requests.get(f"{JIRA_BASE_URL}/rest/api/3/project/search", headers=HEADERS)
    r.raise_for_status()
    proyectos = [{"id": p["id"], "key": p["key"], "nombre": p["name"]} for p in r.json().get("values", [])]
    return {"proyectos": proyectos}


@app.get("/epics")
def listar_epics(proyecto: str):
    """
    Lista las Epics de un proyecto Jira con su key, título, estado, responsable y fechas.
    Parámetro: proyecto (key o nombre del proyecto, ej: DATA)
    """
    try:
        project_key = resolver_proyecto_key(proyecto)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    jql = f'project = "{project_key}" AND issuetype = Epic ORDER BY created DESC'
    r = requests.post(
        f"{JIRA_BASE_URL}/rest/api/3/search/jql",
        headers=HEADERS,
        json={"jql": jql, "maxResults": 50, "fields": ["summary", "status", "assignee", "duedate", "customfield_10015"]}
    )
    r.raise_for_status()

    epics = []
    for i in r.json().get("issues", []):
        f = i["fields"]
        epics.append({
            "key": i["key"],
            "titulo": f["summary"],
            "estado": f["status"]["name"],
            "responsable": (f.get("assignee") or {}).get("displayName", ""),
            "fechaInicio": f.get("customfield_10015", ""),
            "fechaFin": f.get("duedate", ""),
            "url": f"{JIRA_BASE_URL}/browse/{i['key']}"
        })

    return {"proyecto": project_key, "epics": epics}


@app.get("/tareas")
def listar_tareas(epic: str):
    """
    Lista las tareas (y subtareas) hijas de una Epic dado su key (ej: DATA-5).
    """
    if not re.match(r'^[A-Z]+-\d+$', epic.strip()):
        raise HTTPException(status_code=400, detail="El parámetro 'epic' debe ser un key de Jira válido (ej: DATA-5).")

    jql = f'"Epic Link" = {epic} OR parent = {epic} ORDER BY created ASC'
    r = requests.post(
        f"{JIRA_BASE_URL}/rest/api/3/search/jql",
        headers=HEADERS,
        json={"jql": jql, "maxResults": 100, "fields": ["summary", "status", "issuetype", "assignee", "duedate", "customfield_10015", "parent"]}
    )
    r.raise_for_status()

    tareas = []
    for i in r.json().get("issues", []):
        f = i["fields"]
        tareas.append({
            "key": i["key"],
            "tipo": f["issuetype"]["name"],
            "titulo": f["summary"],
            "estado": f["status"]["name"],
            "responsable": (f.get("assignee") or {}).get("displayName", ""),
            "fechaInicio": f.get("customfield_10015", ""),
            "fechaFin": f.get("duedate", ""),
            "url": f"{JIRA_BASE_URL}/browse/{i['key']}"
        })

    return {"epic": epic, "tareas": tareas}


@app.get("/issues")
def listar_issues(proyecto: str = None, tipo: str = None, asignado: str = None):
    """
    Lista issues de Jira con filtros opcionales.
    Parámetros:
      - proyecto (opcional): key o nombre del proyecto (ej: SAN, DATA). Si no se indica, busca en todos.
      - tipo (opcional): filtrar por tipo de issue (ej: Bug, Task, Story).
      - asignado (opcional): nombre de la persona asignada (ej: Santiago). Busca issues asignados a esa persona.
    Al menos uno de los parámetros debe estar presente.
    """
    if not proyecto and not asignado:
        raise HTTPException(status_code=400, detail="Indica al menos 'proyecto' o 'asignado'.")

    conditions = []

    if proyecto:
        try:
            project_key = resolver_proyecto_key(proyecto)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        conditions.append(f'project = "{project_key}"')

    if asignado:
        try:
            account_id = resolver_usuario(asignado)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        conditions.append(f'assignee = "{account_id}"')

    if tipo:
        conditions.append(f'issuetype = "{tipo}"')

    jql = " AND ".join(conditions) + ' ORDER BY created DESC'

    r = requests.post(
        f"{JIRA_BASE_URL}/rest/api/3/search/jql",
        headers=HEADERS,
        json={"jql": jql, "maxResults": 100, "fields": ["summary", "status", "issuetype", "assignee", "duedate", "customfield_10015", "parent"]}
    )
    r.raise_for_status()

    issues = []
    for i in r.json().get("issues", []):
        f = i["fields"]
        parent = f.get("parent")
        issues.append({
            "key": i["key"],
            "tipo": f["issuetype"]["name"],
            "titulo": f["summary"],
            "estado": f["status"]["name"],
            "responsable": (f.get("assignee") or {}).get("displayName", ""),
            "fechaInicio": f.get("customfield_10015", ""),
            "fechaFin": f.get("duedate", ""),
            "epic": parent.get("key", "") if parent else "",
            "url": f"{JIRA_BASE_URL}/browse/{i['key']}"
        })

    return {"proyecto": project_key if proyecto else None, "asignado": asignado, "issues": issues}


@app.get("/worklogs")
def listar_worklogs(proyecto: str = None, asignado: str = None, dias: int = 30):
    """
    Devuelve los registros de tiempo (worklogs) de las tareas de un espacio o persona.
    Parámetros:
      - proyecto (opcional): key o nombre del espacio (ej: SANTIAGO)
      - asignado (opcional): nombre de la persona (ej: Santiago)
      - dias (opcional): cuántos días hacia atrás consultar (por defecto 30)
    Al menos uno de proyecto o asignado debe estar presente.
    """
    if not proyecto and not asignado:
        raise HTTPException(status_code=400, detail="Indica al menos 'proyecto' o 'asignado'.")

    # Obtener issues del espacio/asignado
    conditions = []
    project_key = None

    if proyecto:
        try:
            project_key = resolver_proyecto_key(proyecto)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        conditions.append(f'project = "{project_key}"')

    if asignado:
        try:
            account_id = resolver_usuario(asignado)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        conditions.append(f'assignee = "{account_id}"')

    conditions.append('timespent > 0')
    jql = " AND ".join(conditions) + " ORDER BY updated DESC"

    r = requests.post(
        f"{JIRA_BASE_URL}/rest/api/3/search/jql",
        headers=HEADERS,
        json={"jql": jql, "maxResults": 100, "fields": ["summary", "status", "issuetype", "assignee", "timeoriginalestimate", "timespent", "parent"]}
    )
    r.raise_for_status()

    desde = datetime.utcnow() - timedelta(days=dias)
    resultado = []
    total_estimado_h = 0
    total_registrado_h = 0

    for issue in r.json().get("issues", []):
        f = issue["fields"]
        issue_key = issue["key"]

        # Obtener worklogs de la tarea
        rw = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/worklog",
            headers=HEADERS
        )
        if not rw.ok:
            continue

        worklogs_filtrados = []
        for wl in rw.json().get("worklogs", []):
            started = wl.get("started", "")
            try:
                fecha = datetime.strptime(started[:19], "%Y-%m-%dT%H:%M:%S")
            except Exception:
                continue
            if fecha < desde:
                continue
            autor = wl.get("author", {}).get("displayName", "")
            # Si hay filtro por asignado, solo incluir worklogs de esa persona
            if asignado and account_id not in wl.get("author", {}).get("accountId", ""):
                continue
            worklogs_filtrados.append({
                "fecha": started[:10],
                "autor": autor,
                "horas": round(wl.get("timeSpentSeconds", 0) / 3600, 2),
                "comentario": (wl.get("comment") or {}).get("content", [{}])[0].get("content", [{}])[0].get("text", "") if wl.get("comment") else ""
            })

        if not worklogs_filtrados:
            continue

        estimado_h = round((f.get("timeoriginalestimate") or 0) / 3600, 2)
        registrado_h = round(sum(w["horas"] for w in worklogs_filtrados), 2)
        total_estimado_h += estimado_h
        total_registrado_h += registrado_h

        parent = f.get("parent")
        resultado.append({
            "key": issue_key,
            "titulo": f["summary"],
            "tipo": f["issuetype"]["name"],
            "estado": f["status"]["name"],
            "epic": parent.get("key", "") if parent else "",
            "estimadoH": estimado_h,
            "registradoH": registrado_h,
            "worklogs": worklogs_filtrados,
            "url": f"{JIRA_BASE_URL}/browse/{issue_key}"
        })

    return {
        "proyecto": project_key,
        "asignado": asignado,
        "dias": dias,
        "totalEstimadoH": round(total_estimado_h, 2),
        "totalRegistradoH": round(total_registrado_h, 2),
        "tareas": resultado
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ── DB Producción GYC ──────────────────────────────────────────────────────────

DB_CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=10.0.0.6;"
    "DATABASE=GOMEZYCRESPO;"
    "UID=gestor_incidencias;"
    "PWD=Auria1973;"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
)
DB_MAX_ROWS = 500

# Columnas que contienen nombres de empleados — se anonomizan antes de enviar
_EMPLOYEE_NAME_COLS = {
    "empleado", "operario", "descripemp", "nombre", "trabajador"
}


def _anonymize(name: str) -> str:
    """Sustituye el nombre real por un código reproducible (misma persona = mismo código)."""
    import hashlib
    h = hashlib.md5(name.strip().lower().encode()).hexdigest()[:5].upper()
    return f"OP-{h}"


def _db_serialize(val):
    if isinstance(val, datetime):
        return val.strftime("%d/%m/%Y %H:%M")
    if isinstance(val, date):
        return val.strftime("%d/%m/%Y")
    return val


class DBQueryRequest(BaseModel):
    sql: str


@app.post("/query")
def db_query(request: DBQueryRequest):
    """
    Ejecuta una consulta SELECT en la base de datos de producción de GYC.
    Solo se permiten SELECT. Devuelve hasta 100 filas.
    """
    sql = request.sql.strip()
    first_word = sql.lstrip("(").split()[0].upper() if sql else ""
    if first_word not in ("SELECT", "WITH"):
        raise HTTPException(status_code=400, detail="Solo se permiten consultas SELECT.")

    try:
        conn = pyodbc.connect(DB_CONN_STR, timeout=15)
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        raw = cursor.fetchmany(DB_MAX_ROWS + 1)
        conn.close()
        truncated = len(raw) > DB_MAX_ROWS
        sensitive = {col for col in columns if col.lower() in _EMPLOYEE_NAME_COLS}
        rows = []
        for row in raw[:DB_MAX_ROWS]:
            record = {}
            for col, val in zip(columns, row):
                val = _db_serialize(val)
                if col in sensitive and isinstance(val, str) and val.strip():
                    val = _anonymize(val)
                record[col] = val
            rows.append(record)
        return {"columns": columns, "rows": rows, "row_count": len(rows), "truncated": truncated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
