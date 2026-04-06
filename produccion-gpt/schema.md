# Schema — gyc_analytics · Schema analytics

Todas las vistas están en el schema `analytics` de la base de datos PostgreSQL `gyc_analytics`.
Las tablas base están en el schema `core`.

---

## Vistas disponibles

### `analytics.v_ordenes_activas`
Órdenes en estado Activado o En espera con actividad normal. Excluye órdenes olvidadas (>30 días sin actividad).

| Columna | Tipo | Descripción |
|---|---|---|
| idorden | integer | ID de la orden |
| articulo | varchar | Nombre del artículo |
| idarticulo | varchar | Código del artículo |
| cantidad_pedida | numeric | Unidades a fabricar |
| fecha_orden | date | Fecha de creación de la orden |
| estado | varchar | 'Activado' / 'En espera' |
| pct_completado | numeric | % de operaciones finalizadas |
| horas_trabajadas | numeric | Horas reales acumuladas |
| num_operarios | integer | Operarios distintos que han trabajado en ella |
| ultimo_fichaje | timestamp | Último bono registrado |
| dias_sin_actividad | integer | Días desde el último bono |
| clasificacion | varchar | 'NORMAL' / 'PENDIENTE INICIO' |

**Ejemplo:**
```sql
SELECT idorden, articulo, pct_completado, horas_trabajadas, clasificacion
FROM analytics.v_ordenes_activas
ORDER BY pct_completado DESC
LIMIT 20;
```

---

### `analytics.v_ordenes_olvidadas`
Órdenes activas con trabajo iniciado pero sin actividad en más de 30 días. Candidatas a cerrar en el ERP.

| Columna | Tipo | Descripción |
|---|---|---|
| idorden | integer | ID de la orden |
| articulo | varchar | Nombre del artículo |
| idarticulo | varchar | Código del artículo |
| cantidad_pedida | numeric | Unidades a fabricar |
| fecha_orden | date | Fecha de creación |
| pct_completado | numeric | % completado cuando se olvidó |
| horas_trabajadas | numeric | Horas invertidas |
| num_operarios | integer | Operarios que trabajaron en ella |
| ultimo_fichaje | timestamp | Último bono registrado |
| dias_sin_actividad | integer | Días de inactividad (siempre > 30) |

**Ejemplo:**
```sql
SELECT idorden, articulo, dias_sin_actividad, pct_completado
FROM analytics.v_ordenes_olvidadas
ORDER BY dias_sin_actividad DESC
LIMIT 20;
```

---

### `analytics.v_tiempos_por_articulo`
Tiempo medio real por pieza por artículo, basado en el histórico de órdenes completadas.

| Columna | Tipo | Descripción |
|---|---|---|
| idarticulo | varchar | Código del artículo |
| articulo | varchar | Nombre del artículo |
| num_ordenes | integer | Órdenes completadas con datos válidos |
| min_por_pieza_real | numeric | Minutos reales medios por pieza |
| horas_por_pieza | numeric | Equivalente en horas |
| variabilidad | numeric | Desviación típica (consistencia del proceso) |
| operaciones_media | numeric | Número medio de operaciones por orden |
| secuencia_tipica | varchar | Ruta de fabricación más habitual |
| primera_orden | date | Primera orden registrada |
| ultima_orden | date | Última orden registrada |

**Ejemplo:**
```sql
SELECT articulo, min_por_pieza_real, variabilidad, secuencia_tipica
FROM analytics.v_tiempos_por_articulo
WHERE num_ordenes >= 3
ORDER BY variabilidad DESC NULLS LAST
LIMIT 20;
```

---

### `analytics.v_carga_trabajo_empleado`
Operaciones pendientes en órdenes activas con sugerencia de asignación basada en especialización histórica (últimos 6 meses).

| Columna | Tipo | Descripción |
|---|---|---|
| idorden | integer | Orden con operación pendiente |
| operacion | varchar | Nombre de la operación |
| cantidad_total | numeric | Unidades de la operación |
| fecha_orden | date | Fecha de la orden |
| operario_sugerido | varchar | Empleado con más experiencia en esa operación |
| horas_exp_en_operacion | numeric | Horas acumuladas en esa operación (últimos 6 meses) |
| veces_realizada | integer | Veces que ha realizado esa operación |
| puesto_especialidad | integer | Ranking (1 = más especializado) |
| carga_actual | integer | Bonos activos en curso ahora mismo |

**Ejemplo:**
```sql
SELECT operacion, operario_sugerido, horas_exp_en_operacion, carga_actual
FROM analytics.v_carga_trabajo_empleado
WHERE idorden = 12345;
```

---

### `analytics.v_comparativa_carga_empleado`
Comparativa mensual de horas trabajadas por empleado vs. media del equipo.

| Columna | Tipo | Descripción |
|---|---|---|
| nombre_empleado | varchar | Nombre del operario |
| mes | date | Primer día del mes (ej: 2026-04-01) |
| horas_mes | numeric | Horas trabajadas ese mes |
| ordenes_mes | integer | Órdenes distintas en las que trabajó |
| bonos_mes | integer | Total de bonos ese mes |
| horas_media_equipo | numeric | Media del equipo ese mes |
| desviacion_vs_media | numeric | Horas sobre/bajo la media |
| pct_sobre_media | numeric | 100% = en la media, >100% = sobre la media |
| bonos_en_curso_ahora | integer | Bonos activos en este momento |

**Ejemplo — mes actual:**
```sql
SELECT nombre_empleado, horas_mes, pct_sobre_media, bonos_en_curso_ahora
FROM analytics.v_comparativa_carga_empleado
WHERE mes = DATE_TRUNC('month', CURRENT_DATE)
ORDER BY horas_mes DESC;
```

**Ejemplo — últimos 3 meses:**
```sql
SELECT nombre_empleado, mes, horas_mes, desviacion_vs_media
FROM analytics.v_comparativa_carga_empleado
WHERE mes >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '2 months'
ORDER BY mes DESC, horas_mes DESC;
```

---

### `analytics.v_carga_trabajo_maquina`
Carga mensual por máquina: horas trabajadas, órdenes, operarios y bonos en curso ahora mismo.

| Columna | Tipo | Descripción |
|---|---|---|
| mes | date | Primer día del mes (ej: 2026-04-01) |
| matricula_maquina | varchar | Matrícula/código de la máquina |
| maquina | varchar | Nombre descriptivo de la máquina |
| tipo | varchar | Tipo de máquina (Inyectoras, Prensas, Soldadoras…) |
| area | varchar | Área de planta (INYECION, CHAPA, ENSAMBLAJE, ALAMBRE…) |
| horas_mes | numeric | Horas de uso ese mes |
| ordenes_mes | integer | Órdenes distintas procesadas |
| bonos_mes | integer | Total de bonos registrados |
| operarios_distintos | integer | Operarios que la usaron ese mes |
| operacion_mas_frecuente | varchar | Operación que más se realiza en esta máquina |
| bonos_en_curso_ahora | integer | Bonos activos ahora mismo en esta máquina |

**Ejemplo — máquinas más usadas este mes:**
```sql
SELECT maquina, tipo, area, horas_mes, bonos_en_curso_ahora
FROM analytics.v_carga_trabajo_maquina
WHERE mes = DATE_TRUNC('month', CURRENT_DATE)
ORDER BY horas_mes DESC
LIMIT 20;
```

**Ejemplo — máquinas sin actividad este mes:**
```sql
SELECT maquina, tipo, area
FROM analytics.v_carga_trabajo_maquina
WHERE mes = DATE_TRUNC('month', CURRENT_DATE)
  AND horas_mes = 0
ORDER BY area, maquina;
```

---

## Tablas base (schema core)

Para consultas más detalladas se puede ir a las tablas base:

| Tabla | Descripción |
|---|---|
| `core.fact_tiempos_empleado` | Registro de bonos por empleado con timestamps, operación y máquina |
| `core.fact_operaciones_produccion` | Operaciones de cada bono con tiempos y piezas producidas |
| `core.fact_ordenes_produccion` | Órdenes de producción con estado y cantidad pedida |
| `core.dim_empleados` | Dimensión de empleados |
| `core.dim_maquinas` | Dimensión de máquinas con tipo y área |
| `core.dim_articulo` | Dimensión de artículos |

### Columnas clave de `core.fact_tiempos_empleado`
| Columna | Descripción |
|---|---|
| idorden, idbono, idlinea, idnum | Claves compuestas |
| idempleado | ID del empleado |
| nombre_empleado | Nombre completo |
| matricula_maquina | FK → core.dim_maquinas.matricula |
| operacion | Nombre de la operación (normalizado a Title Case) |
| hinicial, hfinal | Timestamps de inicio y fin del bono |
| minutos_trabajados | Duración calculada (NULL si bono abierto) |
| pct_trabajo | % de trabajo atribuido al empleado |
| clasificacion_bono | NULL (completado) / 'en_curso' / 'anomalia_*' |
