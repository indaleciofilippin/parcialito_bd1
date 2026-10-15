# Guía para escribir ejercicios — Parcialito BD

App local para que un estudiante practique para un **parcialito de SQL (MySQL 8/9)** mañana.
El parcialito es SOLO de ejercicios prácticos (nada de teoría), al estilo del material de la cátedra:

- `TP1_SQL_Universidad.docx`: consultas básicas, JOINs, agrupación y "problemáticas de dominio"
  (pedidos narrativos del área académica con umbrales: "carreras con más de 90 alumnos activos", etc.).
- `Clase Semana 10.pdf`: subconsultas / ausencia-presencia, vistas, DML, CREATE y ALTER.

Todo el texto para el usuario va en **castellano rioplatense** (voseo: "mostrá", "tené en cuenta"),
claro, didáctico y sin relleno. El usuario tiene que entender de verdad, no solo copiar.

## Entorno de desarrollo

- Proyecto: `/Users/indalecio/proyectos-claude/parcialito_bd1`
- MySQL local (config.json). Base de práctica: `parcialito_sandbox`.
- Consultas ad-hoc: usá la Consola SQL de la app o Workbench sobre `parcialito_sandbox`.
- Validador (OBLIGATORIO correrlo hasta que diga "Sin problemas"):
  `.venv/bin/python -m app.validar <seccion|id> [-v]`
- Esquema completo: `awk '/^CREATE TABLE/,/^\) ENGINE/' BD-Universidad.sql`

## Esquema (resumen)

```
departamentos(id_departamento PK, nombre, presupuesto DECIMAL(12,2), fecha_creacion)          5 filas
aulas(id_aula PK, nombre, capacidad, tipo ENUM('normal','laboratorio','centro de computos'))  10
carreras(id_carrera PK, nombre, titulo_otorgado, nivel ENUM('grado','posgrado','tecnicatura'),
         modalidad ENUM('presencial','virtual','mixta'), duracion_anios, carga_horaria_total,
         id_departamento FK)                                                                 20
docentes(id_docente PK, nombre, apellido, email UNIQUE, fecha_ingreso, salario_base DECIMAL(10,2),
         id_departamento FK)                                                                200
asignaturas(id_asignatura PK, nombre, creditos, carga_horaria, es_obligatoria TINYINT(1),
            id_departamento FK)                                                             500
alumnos(id_alumno PK, nombre, apellido, dni UNIQUE, fecha_nacimiento, email UNIQUE, telefono,
        fecha_ingreso)                                                                     1000
alumno_carrera(id PK, id_alumno FK, id_carrera FK, fecha_inscripcion,
               estado ENUM('activa','pausada','graduado','abandonado'))  UNIQUE(id_alumno,id_carrera) 1737
correlatividades(id PK, id_asignatura FK, id_asignatura_correlativa FK → asignaturas)       897
docente_asignatura(id PK, id_docente FK, id_asignatura FK, anio, cuatrimestre, horas_asignadas,
                   monto_pagado DECIMAL(10,2))                                              3000
comisiones(id_comision PK, id_asignatura FK, id_docente FK, id_aula FK, anio, cuatrimestre, cupo,
           tipo ENUM('teorica','practica'))                                                1200
inscripcion_alumno_comision(id_inscripcion PK, id_alumno FK, id_comision FK, fecha_inscripcion,
           estado ENUM('Cursa','Regular','Libre','Aprobada','Baja'))  UNIQUE(id_alumno,id_comision) 17877
asistencias(id_asistencia PK, id_alumno FK, id_comision FK, fecha, presente TINYINT(1))  180000
examenes(id_examen PK, id_comision FK, fecha, tipo ENUM('parcial','recuperatorio'))        4800
notas(id_nota PK, id_examen FK, id_alumno FK, nota DECIMAL(4,2), aprobado TINYINT(1))     54661
mesas_finales(id_mesa PK, id_asignatura FK, id_docente FK, id_aula FK, fecha,
              turno ENUM('Febrero','Julio','Diciembre'), llamado)                          2500
inscripciones_finales(id_inscripcion_final PK, id_mesa FK, id_alumno FK, fecha_inscripcion,
     estado ENUM('inscripto','presente','ausente','aprobado','desaprobado'), nota DECIMAL(4,2)) 21908
```

Vistas que YA EXISTEN en la base de práctica (para ejercicios de "usar una vista"):
`vw_alumnos_carreras`, `vw_comisiones_docentes`, `vw_inscriptos_por_comision`, `vw_notas_por_asignatura`
(ver definición en `app/setup_db.py`, VISTAS_PRECARGADAS).

### Datos a tener en cuenta (son sintéticos/aleatorios)
- Hoy es 2026-10-15. **Todas** las mesas finales son pasadas (2024-01-01 a 2026-06-18) → no uses
  `CURDATE()` para "próximas" mesas: daría vacío. Preferí fechas fijas en el enunciado y explicalo.
- `notas.aprobado` NO es coherente con `notas.nota` (es aleatorio). Desaprobado = `nota < 4` (como dice el TP1).
  Lo mismo `inscripciones_finales.estado` vs `nota`.
- Con los datos originales devuelven 0 filas: alumnos sin inscripciones, docentes sin comisiones,
  aulas sin comisiones, carreras sin alumnos, comisiones sin inscriptos (por eso existen los casos borde).
- 41 asignaturas sin comisiones, 81 sin correlatividades, 5 sin mesas; 176 alumnos sin carrera;
  14 comisiones sin exámenes. Inscriptos por comisión: 4 a 32 (promedio 14.9).
  Comisiones por docente: 1 a 14 (prom 6). Comisiones por asignatura: 1 a 8 (prom 2.61).
- No hay NULL en FKs ni en email/telefono/fecha_nacimiento de alumnos.
- `sql_mode` incluye ONLY_FULL_GROUP_BY: todo lo no agregado del SELECT va en el GROUP BY.

## Formato de un ejercicio

Cada archivo `app/ejercicios/<seccion>.py` define `EJERCICIOS = [dict(...), ...]` (en orden pedagógico:
primero los originales de la cátedra, en su orden, luego las variantes nuevas, de menor a mayor dificultad).
Mirá los ejemplos ya escritos en `subconsultas.py`, `vistas.py`, `dml.py`, `ddl.py` (respetalos y mantenelos).

Campos:

| campo | obligatorio | descripción |
|---|---|---|
| `id` | sí | único, prefijo por sección: `bas-`, `join-`, `agr-`, `dom-`, `sub-`, `vis-`, `dml-`, `ddl-`. Originales usan el número del documento (`agr-11`, `dom-03`, `sub-05`); nuevos `bas-n01`, `sub-n03`… |
| `origen` | sí | `"TP1 · Parte A · Ej. 1"`, `"Semana 10 · Ej. 7"`, o `"Variante"` (para nuevos) |
| `titulo` | sí | corto (≤ 48 caracteres) |
| `dificultad` | sí | 1, 2 o 3 |
| `tipo` | sí | `select` · `dml` · `ddl` · `view` |
| `enunciado` | sí | texto del ejercicio (markdown liviano: `**negrita**`, `` `código` ``). Para originales, copiá el enunciado del documento y, si es ambiguo, agregá UNA aclaración breve de qué mostrar. |
| `solucion` | sí | SQL oficial, bien formateado (mayúsculas en palabras clave, alias cortos, una cláusula por línea) |
| `alternativas` | no | `[dict(titulo, sql)]` otras formas EQUIVALENTES (mismo resultado). Ej: NOT IN / NOT EXISTS / LEFT JOIN. Se muestran al usuario como "otras formas de resolverlo". |
| `variantes` | no | `[dict(titulo, sql)]` interpretaciones DISTINTAS pero razonables de un enunciado ambiguo (ej. "actualmente" = estado <> 'Baja'). También se aceptan como correctas. |
| `columnas` | no | lista de alternativas de columnas que el resultado del usuario DEBE contener (por valores; los alias no importan). Ej: `[["id_docente"], ["nombre","apellido"]]` = alcanza con el id, o con nombre+apellido. Los nombres refieren a columnas de la SOLUCIÓN. Si se omite, se exigen TODAS las columnas de la solución. Usalo siempre que el enunciado no fije exactamente las columnas. |
| `ordenado` / `orden` | no | si el enunciado pide orden: `orden=[("cantidad","desc"), ("apellido","asc")]` (nombres de columnas de la solución). Solo si el enunciado lo pide explícitamente. |
| `casos_borde` | no | `True` para correr también con los casos borde (ver abajo). Usalo en TODO ejercicio de ausencia/presencia. |
| `casos_borde_sql` | no | SQL extra (INSERTs) que se agrega a los casos borde para este ejercicio (se hace ROLLBACK después). |
| `debe_contener` | no | `[dict(patron=r"\bvw_inscriptos_por_comision\b", mensaje="El ejercicio pide usar la vista ...")]` |
| `pistas` | recomendado | 3 pistas progresivas (de orientación general → casi la solución) |
| `explicacion` | recomendado | markdown: el razonamiento paso a paso, por qué cada cláusula, qué cambia entre alternativas. Podés usar bloques ```sql. 60–200 palabras. |
| `errores_comunes` | recomendado | 2–3 errores típicos de estudiantes, con el porqué |
| `trampas` | recomendado | `[dict(titulo, sql)]` consultas INCORRECTAS realistas (los errores comunes escritos en SQL). El validador verifica que el corrector las RECHACE. 1–3 por ejercicio. |
| `tags` | sí | palabras clave: `["GROUP BY","HAVING","JOIN"]` |
| DML: `verificacion` | sí (dml) | SELECT (o lista) que captura el estado relevante. El corrector ejecuta la solución y la del usuario dentro de transacciones (con ROLLBACK) y compara el resultado de la verificación. Poné la PK primero (así el diff muestra filas "modificadas"). Debe cubrir TODO lo que podría romperse (ej. todas las filas de la tabla, no solo las afectadas). Para INSERT con AUTO_INCREMENT, NO incluyas la PK (el id cambia entre ejecuciones): verificá las demás columnas. |
| DML: `preparacion` | no | SQL que se ejecuta antes (dentro de la transacción) para crear la situación del ejercicio (ej. comisiones sin inscriptos para el ej. 19). Mencioná en el enunciado que esos datos existen. |
| DML: `condiciones` | no | para ejercicios ABIERTOS (el usuario elige los valores, ej. ej. 21): `[dict(sql="SELECT COUNT(*) >= 2 FROM ...", desc="Hay al menos 2 alumnos sin inscripciones")]`. Si existe, NO se compara con la solución: se verifica que cada consulta devuelva verdadero. |
| DDL: `checks` | sí (ddl) | lista de verificaciones (ver abajo) |
| DDL: `tablas` | no | tablas a clonar en el espacio temporal (por defecto todas) |
| DDL: `preparacion` | no | SQL previo en el espacio temporal (ej. `ALTER TABLE alumnos DROP INDEX email;` para el ej. 25, o crear `becas` para el 26) |

### Cómo corrige cada tipo
- **select**: ejecuta la consulta del usuario y la solución (y alternativas/variantes) sobre la misma base;
  compara multiconjuntos de filas. Ignora alias, orden de columnas y columnas extra; redondea a 2 decimales.
  Detecta filas repetidas (falta DISTINCT), filas faltantes/sobrantes, columnas faltantes.
  Si `casos_borde=True`, repite la comparación con los datos de `app/ejercicios/fixtures.py` insertados.
- **view**: el usuario escribe `CREATE VIEW ...`; se crea en un espacio temporal y se compara `SELECT * FROM vista`
  contra el SELECT de la solución (mismas reglas que select). El nombre de la vista es libre.
- **dml**: ver `verificacion` / `condiciones` arriba. Tiene que haber al menos un INSERT/UPDATE/DELETE.
- **ddl**: se clona la estructura en `parcialito_scratch` (con datos solo en tablas chicas: departamentos, aulas,
  carreras, docentes, asignaturas, alumnos, comisiones), se ejecuta el script del usuario y se evalúan `checks`:
  - `dict(tipo="columna_nueva", tabla="alumnos", nombre_contiene=["emerg","tel"], tipos=["varchar","char"], msg_tipo="...", alias="col")`
  - `dict(tipo="tabla_nueva", nombre_contiene=["beca"], excluir_contiene=["alumno"], alias="becas", pk=True,
         columnas=[dict(contiene=["nombre"], tipos=["varchar","char"], desc="nombre de la beca", alias="nombre"), ...])`
  - `dict(tipo="fk", tabla="alumno_beca" | tabla_contiene=["beca"], referencia="alumnos")`  (tabla/referencia aceptan `{alias}`)
  - `dict(tipo="unique", tabla="alumnos", columna="email")`
  - `dict(tipo="indice", tabla="alumnos", columna="apellido")`
  - `dict(tipo="check_existe", tabla="docentes", columna="salario_base")`
  - `dict(tipo="columna_tipo", tabla="alumnos", columna="telefono", tipos=["varchar"], largo_min=30, nulo=False)`
  - `dict(tipo="columna_no_existe", ...)`, `dict(tipo="tabla_existe"/"tabla_no_existe", tabla=...)`
  - `dict(tipo="debe_fallar", sql="INSERT ...", errores=[3819])` / `dict(tipo="debe_funcionar", sql="...")`
    (se ejecutan en transacción con ROLLBACK; pueden usar `{becas}` y `{becas.porcentaje}` de los alias).
  - `dict(tipo="consulta", sql="SELECT ... (primer valor verdadero = OK)")` — p.ej. sobre information_schema
    con `TABLE_SCHEMA='{scratch}'` (se reemplaza por el nombre real del espacio temporal).
  - cualquier check acepta `opcional=True` (se muestra como sugerencia extra, no afecta el resultado) y `desc`.
  Los nombres de tablas/columnas nuevas los elige el usuario → usá `nombre_contiene` con varias opciones razonables.
  Preferí checks de COMPORTAMIENTO (debe_fallar/debe_funcionar) además de los estructurales.

### Casos borde estándar (`casos_borde=True`)
Ver `app/ejercicios/fixtures.py`: departamento 901 'Artes' sin docentes/asignaturas (la carrera 902 sí lo usa);
alumnos 90001 y 90002 sin inscripciones (90002 está en la carrera 1); docentes 9001/9002 sin comisiones;
aulas 901/902 sin uso; carreras 901/902 sin alumnos; asignatura 9001 sin comisiones ni correlatividades;
comisiones 90001/90002 (asignaturas 1 y 2, docentes 1 y 2, aulas 1 y 2) sin inscriptos.
Ojo: activar casos borde en ejercicios de conteo puede cambiar el resultado esperado (se agregan comisiones);
está bien mientras la solución, alternativas y variantes sigan siendo correctas. El validador lo comprueba.

## Reglas
1. Solo editá TUS archivos de sección (los que te asignaron). No toques `grader.py`, `validar.py`, ni otras secciones.
   Si encontrás un bug o limitación del corrector, NO lo parchees: contalo en tu respuesta final con un ejemplo.
2. Resultados deterministas: nada de `CURDATE()`/`NOW()` en soluciones de SELECT salvo que el enunciado lo pida
   y el resultado no sea vacío (preferí fechas fijas). En DML se puede, pero preferí fechas fijas.
3. Evitá `LIMIT` cuando hay empates en el corte (verificalo con una consulta). Si lo usás, aclaralo y usá `orden`.
4. Que la solución devuelva un resultado NO trivial con los datos (o con casos borde). Chequeá los umbrales de los
   ejercicios "de dominio" contra los datos: si el umbral original da vacío o devuelve todo, mantené el enunciado
   original pero agregá una nota y/o ajustá el umbral explicándolo ("con estos datos usamos 80 en vez de 90").
5. Enunciados ambiguos ("actualmente", "activos"): elegí la interpretación más razonable como solución y cargá las
   otras razonables como `variantes`.
6. Calidad > cantidad. Cada ejercicio tiene que poder aparecer en el parcialito.
7. Cuando termines: corré el validador sobre tus secciones y dejalo en "Sin problemas". En tu respuesta final
   listá los ids creados, umbrales ajustados, decisiones de interpretación y cualquier problema del corrector.
