# Esquema de base de datos — GYC Producción

## Vistas

### PersV_CargaOperarios — Carga de trabajo de operarios hoy

Vista orientada a supervisión de operarios. Muestra todos los operarios que han fichado hoy, su carga acumulada en minutos, en qué máquina y bono están trabajando ahora mismo, y si alguno está sin tarea activa.

Columnas: `IdEmpleado`, `Operario`, `IdMaquina`, `Maquina` (nombre), `OrdenActual`, `BonoActual`, `DescripBono`, `Area`, `EstadoBono` (Espera/Activo/Finalizado/Bloqueado), `InicioFichaje`, `MinutosEnBonoActual`, `MinutosHoy`, `FichajesHoy`, `Situacion` (Trabajando / Sin tarea activa)

Ejemplos:
```sql
-- Resumen general: cuántos trabajando vs parados
SELECT TOP 50 Operario, Maquina, Area, DescripBono, MinutosEnBonoActual, MinutosHoy, Situacion
FROM PersV_CargaOperarios
ORDER BY MinutosHoy DESC

-- Operarios sin tarea activa ahora mismo
SELECT TOP 20 Operario, MinutosHoy, FichajesHoy
FROM PersV_CargaOperarios
WHERE Situacion = 'Sin tarea activa'

-- Carga por máquina (operarios activos y minutos acumulados)
SELECT TOP 20 Maquina, COUNT(*) AS Operarios, SUM(MinutosHoy) AS MinutosTotales
FROM PersV_CargaOperarios
WHERE Situacion = 'Trabajando'
GROUP BY Maquina
ORDER BY Operarios DESC
```

---

### PersV_VerEmpleadosActivos — Empleados trabajando ahora mismo
Vista de uso inmediato para saber quién está fichado, en qué máquina y en qué orden/bono.
Columnas: `empleado` (int), `descripemp` (nombre), `maquina`, `orden`, `bono`, `descripbono`, `descripope` (descripción operación), `fechalin` (varchar), `descripinc`, `hora`

Ejemplo:
```sql
SELECT TOP 50 descripemp, maquina, orden, bono, descripbono, hora
FROM PersV_VerEmpleadosActivos
ORDER BY hora
```

---

### vEstadoCompletoBonos — Estado completo de bonos activos
Vista unificada que combina estado del bono, localización en máquina, tiempos trabajados y alertas de material.
Columnas: `IdOrden`, `IdBono`, `Bono`, `IdEstado` (0=Espera, 1=Activo, 3=Bloqueado), `Area`, `FechaPrevFin`, `IdMaquina`, `Empleado`, `FichajeInicio`, `MinutosTrabajados`, `EmpleadosDistintos`, `MaterialesEnDeficit`, `PeorDisponible`

Ejemplo — bonos activos ahora:
```sql
SELECT TOP 50 IdOrden, IdBono, Bono, Area, IdMaquina, Empleado,
              MinutosTrabajados, MaterialesEnDeficit, PeorDisponible
FROM vEstadoCompletoBonos WHERE IdEstado = 1
ORDER BY MinutosTrabajados DESC
```

Ejemplo — bonos bloqueados con problemas de material:
```sql
SELECT TOP 20 IdOrden, IdBono, Bono, Area, MaterialesEnDeficit, PeorDisponible
FROM vEstadoCompletoBonos WHERE MaterialesEnDeficit > 0
ORDER BY PeorDisponible ASC
```

---

### persV_ConsultaProduccion — Panel de órdenes con estado por área
Columnas: `IdOrden`, `Descrip`, `IdArt`, `Ancho`, `Largo`, `Alto`, `Cliente`, `Ciudad`, `Provincia`,
`NumPedido`, `NumPedCli`, `FechaOrden`, `FechaProduccion`, `Fechapedido`,
`cuantosBonos`, `cuantosBonosEspera`, `cuantosBonosActivo`, `cuantosBonosFinalizado`, `cuantosBonosBloqueado`, `cuantosBonosAnulado`,
`Bloqueado`, `ColorPrioridad`, `UnidadesStockTotal`,
Máquinas asignadas (varchar): `punzonadoras`, `Soldadoras`, `Plegadoras`, `Inyectoras`, `Cizallas`, `Punteadoras`, `Clinchadoras`, `Enderezadoras`, `Prensas`, `Perfiladoras`, `Bordoneadoras`, `Sierras`, `Tronzadoras`, `Rectificadoras`, `Fresadoras`, `Taladros`, `Curvadoras`, `Amoladoras`, `Retractiladoras`, `Remachadoras`, `Otras`,
Estado por tipo: `EstadoPlegadoras`, `EstadoSoldadoras`, `Estadopunzonadoras`, `EstadoCizallas`, `EstadoInyectoras`, `EstadoPunteadoras`, `EstadoClinchadoras`, `EstadoEnderezadoras`, `EstadoPrensas`, `EstadoPerfiladoras`, `EstadoBordoneadoras`, `EstadoSierras`, `EstadoTronzadoras`, `EstadoRectificadoras`, `EstadoFresadoras`, `EstadoTaladros`, `EstadoCurvadoras`, `EstadoAmoladoras`, `EstadoRetractiladoras`, `EstadoRemachadoras`, `EstadoOtras`

Ejemplo:
```sql
SELECT TOP 20 IdOrden, Descrip, Cliente, cuantosBonosActivo, cuantosBonosBloqueado, FechaOrden, FechaProduccion
FROM persV_ConsultaProduccion WHERE cuantosBonosActivo > 0
```

---

### perscosteproduccion — Costes completos por bono
Columnas: `IdOrden`, `IdArticulo`, `Articulo`, `IdBono`, `Bono`, `TipoFichaje` (0=operación, 1=montaje),
`IdMaquina`, `Maquina`, `IdEmpleado`, `Empleado`, `Fecha`, `Horas`,
`CosteMaquina`, `CosteTrabajador`, `CosteTotal`, `PiezasFaf`, `CostePieza`,
`EstadoOrden`, `EstadoBono`, `Ejercicio`, `Mes`,
`ImporteMateriales`, `PiezasOrden`, `CostePiezaOrden`, `CosteMedioProd`, `CosteUltimoProd`

Ejemplo:
```sql
SELECT TOP 1 IdOrden, Articulo, PiezasOrden, CostePiezaOrden, CosteMedioProd
FROM perscosteproduccion WHERE IdOrden = 5000 AND TipoFichaje = 1
```

---

### persmonitoriza — Fichajes con timestamps por bono
Igual que `perscosteproduccion` pero con horas exactas de inicio y fin. Úsala para ver cuándo empezó y terminó cada operación.
Columnas: `IdOrden`, `IdArticulo`, `Articulo`, `IdBono`, `Bono`, `TipoFichaje`,
`IdMaquina`, `Maquina`, `IdEmpleado`, `Empleado`, `Fecha`, `Hinicial`, `Hfinal`,
`CosteMaquina`, `CosteTrabajador`, `CosteTotal`, `PiezasFaf`, `CostePieza`,
`EstadoOrden`, `EstadoBono`, `Ejercicio`, `Mes`,
`ImporteMateriales`, `PiezasOrden`, `CostePiezaOrden`, `CosteMedioProd`, `CosteUltimoProd`

Ejemplo — operaciones en curso:
```sql
SELECT TOP 50 IdOrden, IdBono, Bono, Maquina, Empleado, Hinicial
FROM persmonitoriza WHERE Hfinal IS NULL
ORDER BY Hinicial DESC
```

---

### vTiemposMediosBono — Tiempos históricos por artículo y bono
Columnas: `IdArticulo`, `IdBono`, `Bono`, `Area`, `VecesEjecutado`,
`MediaMinPorPieza`, `MinMinPorPieza`, `MaxMinPorPieza`,
`MediaUlt5MinPorPieza` (media últimas 5 ejecuciones — más relevante), `FechaUltimaEjecucion`

Ejemplo — comparar bonos activos contra su histórico:
```sql
SELECT TOP 20
    e.IdOrden, e.IdBono, e.Bono, e.Area, e.MinutosTrabajados,
    t.MediaUlt5MinPorPieza, o.Cantidad,
    ROUND(t.MediaUlt5MinPorPieza * o.Cantidad, 0) AS MinutosEsperados,
    ROUND(CAST(e.MinutosTrabajados AS float) / NULLIF(t.MediaUlt5MinPorPieza * o.Cantidad, 0) * 100, 0) AS PctProgreso
FROM vEstadoCompletoBonos e
INNER JOIN Ordenes o ON o.IdOrden = e.IdOrden
LEFT JOIN vTiemposMediosBono t ON t.IdArticulo = o.IdArticulo AND t.IdBono = e.IdBono
WHERE e.IdEstado = 1
ORDER BY PctProgreso DESC
```

---

### VOrdenes_Bonos_Lineas_Emp — Localización actual de bonos por máquina
Columnas: `IdOrden`, `IdBono`, `IdLinea`, `IdNum`, `IdEmpleado`, `Empleado`, `Descrip`,
`IdMaquina`, `HInicial`, `HFinal` (NULL=trabajando ahora), `IdCosteTipo`, `PorcentajeTrabajo`, `Usuario`

Ejemplo:
```sql
SELECT TOP 50 IdOrden, IdBono, Empleado, IdMaquina, HInicial
FROM VOrdenes_Bonos_Lineas_Emp WHERE IdOrden = 5000 AND HFinal IS NULL
```

---

### Pers_vOrdenes_Consumos — Materiales necesarios vs. stock disponible por orden
Columnas: `IdOrden`, `IdArticulo`, `Descrip`, `IdAlmacen`,
`Cantidad` (necesaria), `CantidadTotal`, `UnidadesStock`,
`Stock`, `StockReservado`, `Disponible`, `UdStock`, `UdStockReservado`, `UdStockDisponible`

Ejemplo — materiales sin stock suficiente:
```sql
SELECT TOP 20 IdOrden, IdArticulo, Descrip, Cantidad, Stock, Disponible
FROM Pers_vOrdenes_Consumos WHERE IdOrden = 5000 AND Disponible < Cantidad
```

---

### Persv_ArticulosNecesarios — Materiales necesarios por bono con ubicación
Columnas: `IdOrden`, `IdBono`, `IdArticulo`, `Descrip`, `Unidades`, `Cantidad`,
`Nombre`, `IdUbicacion`, `Stock`, `nombreMaquina`

---

### Pers_StocksArticulos — Stock actual por artículo
Columnas: `IdArticulo`, `Descrip`, `Stock`, `Pedido` (pendiente de proveedor), `Reservado`, `Minimo`

Ejemplo:
```sql
SELECT TOP 20 IdArticulo, Descrip, Stock, Minimo, Pedido
FROM Pers_StocksArticulos WHERE Stock < Minimo ORDER BY Stock ASC
```

---

### persV_DatosAsociadoOrdenEmp — Empleados por orden/bono
Columnas: `orden`, `bono`, `Empleado`, `Area`, `Descrip` (descripción máquina), `idsubtipoMaq`

Ejemplo:
```sql
SELECT TOP 10 orden, bono, Empleado, Area, Descrip
FROM persV_DatosAsociadoOrdenEmp WHERE Empleado LIKE '%Juan%'
```

---

### Pers_costetrabajadoresdetalle — Coste de trabajadores por día y orden
Columnas: `Fecha`, `mes`, `Ejercicio`, `Empleado`, `IdOrden`, `IdBono`, `horas`, `CosteTrab`

---

## Tablas base

### Ordenes — Cabecera de órdenes
`IdOrden`, `FechaOrden`, `IdArticulo`, `IdArticuloCli`, `Cantidad`, `IdCliente`,
`IdEstado` (-1=Anulado, 0=Espera, 1=Activado, 2=Finalizado),
`FechaPrevFin`, `FechaTope`, `FechaFin`, `Lote`, `Observaciones`, `IdProyecto`

### Ordenes_Bonos — Operaciones de cada orden
`IdOrden`, `IdBono`, `Descrip`, `IdTrabajo`, `Lote`,
`IdEstado` (-1=Anulado, 0=Espera, 1=Activado, 2=Finalizado, 3=Bloqueado),
`Area` (CHAPA, ENSAMBLAJE, INYECION...), `Operarios`, `FechaPrevFin`, `Matricula`,
`TiempoMontaje`, `TiempoDesMontaje`, `TotalPiezas`, `TotalMinutos`,
`Producido`, `Prioridad`, `IdBonoPadre`, `PiezasGolpe`

### Ordenes_Bonos_Lineas — Fichajes de producción
`IdOrden`, `IdBono`, `IdLinea`, `IdArticulo`, `IdOperacion` (1=inicio, 0=cierre),
`IdEmpleado`, `Matricula`, `Fecha`, `TotalPiezas`,
`Hinicial`, `Hfinal` (NULL=en curso), `Mparada`, `Scrap`, `CausaScrap`, `IdEstado`

### Ordenes_Bonos_Lineas_Emp — Empleados por fichaje
`IdOrden`, `IdBono`, `IdLinea`, `IdEmpleado`, `Descrip` (nombre completo),
`IdMaquina`, `HInicial`, `HFinal` (NULL=trabajando ahora)

### Costes_Bonos — Costes por bono
`IdOrden`, `IdBono`, `TiempoMontaje`, `TiempoDesmontaje`, `TiempoEjecucion`, `CosteMaquina`, `CosteTotal`

---

## Relaciones
- `Ordenes` 1→N `Ordenes_Bonos` (IdOrden)
- `Ordenes_Bonos` 1→N `Ordenes_Bonos_Lineas` (IdOrden + IdBono)
- `Ordenes_Bonos_Lineas` 1→N `Ordenes_Bonos_Lineas_Emp` (IdOrden + IdBono + IdLinea)
- `Ordenes_Bonos` 1→1 `Costes_Bonos` (IdOrden + IdBono)
