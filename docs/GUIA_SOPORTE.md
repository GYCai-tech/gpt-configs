# Guía de uso y soporte — GPTs corporativos

Esta guía es para quien **usa los asistentes de ChatGPT de la empresa** (Jira, Producción y Documentador
ISO) o atiende sus incidencias sin ser programador.

Para mantener o modificar los asistentes, ver [DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md).

---

## 1. Qué es

Tres **asistentes personalizados de ChatGPT** («GPTs») preparados para Gómez y Crespo:

| Asistente | Para qué sirve |
|---|---|
| **Gestión de proyectos (Jira)** | Planificar proyectos, crear tareas en Jira y ver cómo va el trabajo de cada persona, hablando en lenguaje normal |
| **Producción** | Preguntar por el estado de la planta: órdenes activas u olvidadas, carga de operarios y máquinas, tiempos de fabricación |
| **Documentador ISO** | Redactar o revisar procedimientos ISO 9001 / 14001 con el estilo de la empresa y descargarlos en Word |

Se usan desde ChatGPT con la cuenta de la empresa. El enlace a cada uno lo facilita sistemas.

## 2. Cómo se usa cada asistente

### 2.1 Gestión de proyectos (Jira)

En Jira, cada persona tiene un **espacio**; dentro, cada **Epic** es un proyecto y las **tareas** son el
trabajo.

Ejemplos de peticiones:

- «¿Cómo va Santiago?» → resume sus proyectos, tareas sueltas y tareas asignadas en otros espacios.
- «Quiero ver el estado de un espacio» → enseña la lista para elegir.
- «Crea un proyecto para implantar X en mi espacio».

Al crear un proyecto, el asistente **pregunta cuántas horas al día** se le van a dedicar, propone tareas
con horas estimadas y fechas (días laborables, 8 h) y **pide confirmación** antes de crearlas en Jira.
Revisar bien la propuesta: lo que se confirma se crea de verdad.

### 2.2 Producción

Ejemplos:

- «¿Cuál es el estado general de la planta?» → actividad en curso, alertas, reparto de carga y tiempos.
- «¿Qué órdenes llevan más de un mes sin moverse?»
- «¿Qué máquinas no han trabajado este mes?»
- «Compara las horas de los operarios este mes».

Los datos vienen de la **copia analítica del ERP**, que se actualiza periódicamente: no es el ERP al
segundo. Las cifras son tan buenas como la consulta que genera el asistente; ante una decisión importante,
contrastar con el ERP.

### 2.3 Documentador ISO

1. Pedir «Quiero crear un procedimiento nuevo sobre …» (o subir uno existente para revisarlo).
2. El asistente propone el **código** (p. ej. el siguiente PC libre) y pide confirmación.
3. Va **sección por sección** (objeto, alcance, definiciones, responsabilidades, entradas y salidas,
   desarrollo, archivo, referencias, anexos), redacta el texto y pregunta «¿Es así, o lo ajustamos?».
4. Al confirmar todo, genera el **Word** para descargar, con la plantilla de la empresa.

Elabora siempre el Responsable de Calidad y Medio Ambiente y aprueba Gerencia; el asistente ya lo pone así.

## 3. Buenas prácticas

- **No pegar datos personales** (DNI, salud, salarios) en las conversaciones.
- Revisar siempre lo que el asistente va a **crear o cambiar** en Jira antes de confirmar.
- Pedir la consulta o la fuente cuando una cifra de producción parezca rara.

## 4. Preguntas habituales

| Pregunta | Respuesta |
|---|---|
| «El asistente dice que no encuentra a una persona en Jira» | Escribir el nombre como aparece en Jira o el correo |
| «Ha creado tareas que no quería» | Borrarlas o editarlas en Jira. El asistente no deshace |
| «Producción me da datos de ayer» | La copia analítica no es en tiempo real |
| «El Word del procedimiento sale sin formato» | Al asistente le falta la plantilla: avisar a sistemas |

## 5. Si no funciona

| Lo que se ve | Causa probable | Qué hacer |
|---|---|---|
| Error al «hablar con» la acción / no puede conectar (Jira o Producción) | El servidor de la empresa o el túnel que lo publica está caído, o ha cambiado su dirección | Avisar a sistemas. El Documentador ISO sigue funcionando porque no lo usa |
| Errores de permiso de Jira | Credencial de Jira caducada o cambiada | Avisar a sistemas |
| Respuestas que no siguen el estilo de la empresa | Instrucciones del GPT cambiadas | Avisar a quien mantiene los GPT |

### 5.1 Comprobaciones (sistemas)

Por SSH en `10.0.0.12`:

```bash
cd /home/goyco/apps/gpts
docker ps --filter name=jira-gpt --filter name=ngrok     # ¿los dos en marcha?
docker logs --tail 50 jira-gpt                           # errores de la API
docker logs --tail 20 ngrok-jira-gpt                     # URL pública del túnel
curl http://localhost:8090/health                        # {"status":"ok"}
```

Si la URL del túnel ha cambiado, hay que actualizarla en las Acciones de los GPT de Jira y Producción.

## 6. Qué recoger antes de escalar

- Qué asistente, qué se pidió y la hora.
- Captura del mensaje de error.

## 7. Glosario

| Término | Significado |
|---|---|
| **GPT** | Asistente de ChatGPT con instrucciones y conexiones propias |
| **Acción** | Conexión de un GPT con un sistema externo (Jira, base de datos) |
| **Espacio / Epic / Tarea** | Niveles de organización del trabajo en Jira |
| **Copia analítica** | Base de datos `gyc_analytics`, copia periódica del ERP para informes |
