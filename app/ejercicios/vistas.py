"""Sección: Vistas (Clase Semana 10 · Sección 2)."""

EJERCICIOS = [
    # ------------------------------------------------------------------
    # Originales de la Clase Semana 10 (ej. 11 a 14)
    # ------------------------------------------------------------------
    dict(
        id="vis-11",
        origen="Semana 10 · Ej. 11",
        titulo="Vista de alumnos con sus carreras",
        dificultad=2,
        tipo="view",
        enunciado="Crear una vista que permita visualizar a los **alumnos junto con las carreras** a las que pertenecen. "
                  "La vista debe mostrar al menos: id del alumno, nombre, apellido y el nombre de la carrera.",
        solucion="""CREATE VIEW vw_alumnos_carreras AS
SELECT a.id_alumno,
       a.nombre,
       a.apellido,
       c.id_carrera,
       c.nombre AS carrera,
       ac.estado AS estado_carrera
FROM alumnos a
JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
JOIN carreras c        ON c.id_carrera = ac.id_carrera;""",
        alternativas=[
            dict(titulo="Nombrando las columnas en la cabecera", sql="""CREATE VIEW vw_alumnos_carreras (id_alumno, nombre, apellido, carrera) AS
SELECT a.id_alumno, a.nombre, a.apellido, c.nombre
FROM alumnos a
JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
JOIN carreras c        ON c.id_carrera = ac.id_carrera;"""),
        ],
        columnas=[["id_alumno", "carrera"], ["nombre", "apellido", "carrera"]],
        pistas=[
            "Una vista es un `SELECT` guardado con nombre: `CREATE VIEW nombre AS SELECT ...;`",
            "La relación alumno–carrera es N a N: pasa por la tabla intermedia `alumno_carrera`.",
            "Ojo: `alumnos` y `carreras` tienen ambas una columna `nombre`. En una vista no puede haber dos columnas con el mismo nombre → usá un alias (`c.nombre AS carrera`).",
        ],
        explicacion="""Primero pensá el `SELECT` que querés reutilizar: alumnos → `alumno_carrera` → carreras (dos `JOIN`).

Después lo envolvés en `CREATE VIEW vw_alumnos_carreras AS ...`. A partir de ahí podés consultar la vista como si fuera una tabla:

```sql
SELECT * FROM vw_alumnos_carreras WHERE carrera = 'Medicina';
```

El detalle clave es el **alias**: sin `AS carrera` MySQL da el error **1060** (*Duplicate column name 'nombre'*). También podés nombrar las columnas en la cabecera: `CREATE VIEW v (id_alumno, nombre, apellido, carrera) AS ...`.

En la base de práctica esta vista **ya existe**: si la creás de nuevo desde la consola vas a ver el error **1050** (*Table already exists*). Para redefinirla usá `CREATE OR REPLACE VIEW`.""",
        errores_comunes=[
            "No poner alias a `c.nombre` → error 1060 «Duplicate column name».",
            "Unir `alumnos` con `carreras` directamente: no hay FK entre ellas, la relación pasa por `alumno_carrera`.",
            "Crear una vista con un nombre que ya existe → error 1050. Usá `CREATE OR REPLACE VIEW` u otro nombre.",
        ],
        trampas=[
            dict(titulo="Columnas duplicadas (error 1060)", sql="""CREATE VIEW vw_alumnos_carreras AS
SELECT a.id_alumno, a.nombre, a.apellido, c.nombre
FROM alumnos a
JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
JOIN carreras c ON c.id_carrera = ac.id_carrera;"""),
            dict(titulo="JOIN directo sin la tabla intermedia", sql="""CREATE VIEW vw_alumnos_carreras AS
SELECT a.id_alumno, a.nombre, a.apellido, c.nombre AS carrera
FROM alumnos a
JOIN carreras c ON c.id_carrera = a.id_alumno;"""),
        ],
        tags=["CREATE VIEW", "JOIN", "alias"],
    ),
    dict(
        id="vis-12",
        origen="Semana 10 · Ej. 12",
        titulo="Vista de comisiones y docentes",
        dificultad=2,
        tipo="view",
        enunciado="Crear una vista que simplifique el análisis de **comisiones y docentes asignados**. "
                  "La vista debe mostrar al menos: id de la comisión, nombre de la asignatura, año, cuatrimestre "
                  "y el docente a cargo (id, nombre y apellido).",
        solucion="""CREATE VIEW vw_comisiones_docentes AS
SELECT c.id_comision,
       a.nombre     AS asignatura,
       c.anio,
       c.cuatrimestre,
       c.tipo,
       d.id_docente,
       d.nombre     AS nombre_docente,
       d.apellido   AS apellido_docente
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN docentes d    ON d.id_docente = c.id_docente;""",
        alternativas=[
            dict(titulo="Con CREATE OR REPLACE e incluyendo el aula", sql="""CREATE OR REPLACE VIEW vw_comisiones_docentes AS
SELECT c.id_comision, c.anio, c.cuatrimestre, c.tipo, c.cupo,
       a.id_asignatura, a.nombre AS asignatura,
       d.id_docente, d.nombre AS nombre_docente, d.apellido AS apellido_docente,
       au.nombre AS aula
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN docentes d    ON d.id_docente = c.id_docente
JOIN aulas au      ON au.id_aula = c.id_aula;"""),
        ],
        columnas=[["id_comision", "asignatura", "id_docente"],
                  ["id_comision", "asignatura", "nombre_docente", "apellido_docente"]],
        pistas=[
            "El docente a cargo de cada comisión está en `comisiones.id_docente` (no hace falta `docente_asignatura`).",
            "Necesitás dos JOIN desde `comisiones`: uno a `asignaturas` y otro a `docentes`.",
            "`asignaturas.nombre` y `docentes.nombre` chocan: poneles alias (`AS asignatura`, `AS nombre_docente`).",
        ],
        explicacion="""Cada comisión tiene **un** docente (`comisiones.id_docente`) y **una** asignatura, así que la vista tiene exactamente una fila por comisión (1.200).

```sql
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN docentes d    ON d.id_docente   = c.id_docente
```

Los alias son obligatorios: `a.nombre` y `d.nombre` se llamarían igual (error **1060**). Lo mismo pasa con `SELECT c.*, d.*`: las dos tablas tienen `id_docente`.

`docente_asignatura` registra qué docentes dictan cada asignatura (por año/cuatrimestre), no quién está a cargo de cada comisión: si la usás, las filas se multiplican.

Si la vista ya existe (en la base de práctica existe una con este nombre), `CREATE VIEW` da error **1050**; para modificarla usá `CREATE OR REPLACE VIEW`.""",
        errores_comunes=[
            "`SELECT c.*, d.*` → error 1060 porque `id_docente` aparece dos veces.",
            "Buscar al docente por `docente_asignatura`: multiplica las filas (varios docentes por asignatura).",
            "No poner alias a las columnas `nombre` de asignatura y docente.",
        ],
        trampas=[
            dict(titulo="c.* y d.* (error 1060)", sql="""CREATE VIEW vw_comisiones_docentes AS
SELECT c.*, d.*
FROM comisiones c
JOIN docentes d ON d.id_docente = c.id_docente;"""),
            dict(titulo="Docentes por docente_asignatura", sql="""CREATE VIEW vw_comisiones_docentes AS
SELECT c.id_comision, a.nombre AS asignatura, c.anio, c.cuatrimestre,
       d.id_docente, d.nombre AS nombre_docente, d.apellido AS apellido_docente
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN docente_asignatura da ON da.id_asignatura = c.id_asignatura
JOIN docentes d ON d.id_docente = da.id_docente;"""),
        ],
        tags=["CREATE VIEW", "JOIN", "alias", "CREATE OR REPLACE"],
    ),
    dict(
        id="vis-13",
        origen="Semana 10 · Ej. 13",
        titulo="Vista de inscriptos por comisión",
        dificultad=2,
        tipo="view",
        enunciado="Crear una vista que muestre la **cantidad de alumnos inscriptos por comisión**. "
                  "Incluí el id de la comisión, la asignatura, año, cuatrimestre, cupo y la cantidad de inscriptos "
                  "(las comisiones sin inscriptos deberían aparecer con 0).",
        solucion="""CREATE VIEW vw_inscriptos_por_comision AS
SELECT c.id_comision,
       a.nombre AS asignatura,
       c.anio,
       c.cuatrimestre,
       c.cupo,
       COUNT(i.id_inscripcion) AS cantidad_inscriptos
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
LEFT JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.id_comision, a.nombre, c.anio, c.cuatrimestre, c.cupo;""",
        alternativas=[
            dict(titulo="Con subconsulta correlacionada en el SELECT", sql="""CREATE VIEW vw_inscriptos_por_comision AS
SELECT c.id_comision,
       a.nombre AS asignatura,
       c.anio,
       c.cuatrimestre,
       c.cupo,
       (SELECT COUNT(*)
        FROM inscripcion_alumno_comision i
        WHERE i.id_comision = c.id_comision) AS cantidad_inscriptos
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura;"""),
        ],
        variantes=[
            dict(titulo="Sin contar las inscripciones dadas de baja", sql="""CREATE VIEW vw_inscriptos_por_comision AS
SELECT c.id_comision,
       a.nombre AS asignatura,
       c.anio,
       c.cuatrimestre,
       c.cupo,
       COUNT(i.id_inscripcion) AS cantidad_inscriptos
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
LEFT JOIN inscripcion_alumno_comision i
       ON i.id_comision = c.id_comision AND i.estado <> 'Baja'
GROUP BY c.id_comision, a.nombre, c.anio, c.cuatrimestre, c.cupo;"""),
        ],
        columnas=[["id_comision", "cantidad_inscriptos"]],
        casos_borde=True,
        pistas=[
            "Es un conteo por grupo: `GROUP BY` la comisión y `COUNT(...)` de sus inscripciones.",
            "Para que aparezcan las comisiones sin inscriptos, el JOIN con `inscripcion_alumno_comision` tiene que ser `LEFT JOIN`.",
            "Contá una columna de la tabla de la derecha (`COUNT(i.id_inscripcion)`), no `COUNT(*)`. Y todo lo que no está agregado va en el `GROUP BY`.",
        ],
        explicacion="""Una vista puede guardar una consulta **agrupada**: después la usás como si fuera una tabla con una fila por comisión.

Tres detalles:

1. **`LEFT JOIN`** con las inscripciones, para no perder las comisiones vacías.
2. **`COUNT(i.id_inscripcion)`**: cuenta solo las filas con inscripción real. `COUNT(*)` contaría 1 en las comisiones vacías (la fila con NULLs del LEFT JOIN).
3. Con `ONLY_FULL_GROUP_BY`, todas las columnas no agregadas (`asignatura`, `anio`, `cupo`…) van en el `GROUP BY`; si no, error **1055**.

El alias `cantidad_inscriptos` es importante: sin él la columna de la vista se llamaría `COUNT(i.id_inscripcion)`.

Si preferís no contar las bajas, la condición `i.estado <> 'Baja'` va en el **`ON`** (en el `WHERE` eliminaría las comisiones sin inscriptos). También se acepta.""",
        errores_comunes=[
            "Usar `JOIN` + `COUNT(*)`: con datos reales da igual, pero una comisión sin inscriptos desaparece (o cuenta 1 con LEFT JOIN). El corrector lo prueba con comisiones vacías.",
            "Olvidar columnas en el `GROUP BY` → error 1055 (ONLY_FULL_GROUP_BY).",
            "Agrupar por asignatura en vez de por comisión: una asignatura tiene varias comisiones.",
        ],
        trampas=[
            dict(titulo="Agrupa por asignatura", sql="""CREATE VIEW vw_inscriptos_por_comision AS
SELECT a.id_asignatura, a.nombre AS asignatura, COUNT(i.id_inscripcion) AS cantidad_inscriptos
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
LEFT JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY a.id_asignatura, a.nombre;"""),
            dict(titulo="Sin GROUP BY", sql="""CREATE VIEW vw_inscriptos_por_comision AS
SELECT c.id_comision, COUNT(i.id_inscripcion) AS cantidad_inscriptos
FROM comisiones c
LEFT JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision;"""),
            dict(titulo="INNER JOIN: pierde las comisiones vacías", sql="""CREATE VIEW vw_inscriptos_por_comision AS
SELECT c.id_comision, a.nombre AS asignatura, c.anio, c.cuatrimestre, c.cupo, COUNT(*) AS cantidad_inscriptos
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.id_comision, a.nombre, c.anio, c.cuatrimestre, c.cupo;"""),
            dict(titulo="LEFT JOIN con COUNT(*): cuenta 1 en las vacías", sql="""CREATE VIEW vw_inscriptos_por_comision AS
SELECT c.id_comision, COUNT(*) AS cantidad_inscriptos
FROM comisiones c
LEFT JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.id_comision;"""),
        ],
        tags=["CREATE VIEW", "GROUP BY", "COUNT", "LEFT JOIN"],
    ),
    dict(
        id="vis-14",
        origen="Semana 10 · Ej. 14",
        titulo="Reutilizar una vista: más de 30 inscriptos",
        dificultad=2,
        tipo="select",
        enunciado="Utilizar alguna de las vistas creadas anteriormente para obtener únicamente las **comisiones que "
                  "superen los 30 alumnos inscriptos**. Además: indicar qué vista utilizaron, explicar por qué eligieron "
                  "esa vista, y describir qué ventajas aporta re-utilizarla en lugar de reescribir toda la consulta nuevamente.\n\n"
                  "En la base de práctica ya existe `vw_inscriptos_por_comision` (id_comision, asignatura, anio, "
                  "cuatrimestre, cupo, cantidad_inscriptos). Las respuestas teóricas están en la explicación.",
        solucion="""SELECT id_comision, asignatura, anio, cuatrimestre, cantidad_inscriptos
FROM vw_inscriptos_por_comision
WHERE cantidad_inscriptos > 30;""",
        alternativas=[
            dict(titulo="Con SELECT *", sql="""SELECT *
FROM vw_inscriptos_por_comision
WHERE cantidad_inscriptos > 30;"""),
        ],
        columnas=[["id_comision"]],
        debe_contener=[dict(patron=r"\bvw_inscriptos_por_comision\b",
                            mensaje="El ejercicio pide reutilizar una vista: consultá `vw_inscriptos_por_comision` "
                                    "en lugar de reescribir los JOIN y el GROUP BY.")],
        casos_borde_sql="""INSERT INTO comisiones (id_comision, id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo) VALUES
 (90021, 5, 5, 5, 2026, 2, 60, 'teorica'),
 (90022, 6, 6, 5, 2026, 2, 60, 'teorica');
INSERT INTO inscripcion_alumno_comision (id_alumno, id_comision, fecha_inscripcion, estado)
SELECT id_alumno, 90021, '2026-08-01', 'Cursa' FROM alumnos WHERE id_alumno BETWEEN 1 AND 30;
INSERT INTO inscripcion_alumno_comision (id_alumno, id_comision, fecha_inscripcion, estado)
SELECT id_alumno, 90022, '2026-08-01', 'Cursa' FROM alumnos WHERE id_alumno BETWEEN 1 AND 31;""",
        pistas=[
            "¿Cuál de las vistas ya tiene calculada la cantidad de inscriptos por comisión?",
            "En la vista, `cantidad_inscriptos` es una columna común: se filtra con `WHERE`, no hace falta `GROUP BY` ni `HAVING`.",
            "`SELECT * FROM vw_inscriptos_por_comision WHERE cantidad_inscriptos > 30;` («superen» = `>`, no `>=`).",
        ],
        explicacion="""```sql
SELECT * FROM vw_inscriptos_por_comision
WHERE cantidad_inscriptos > 30;
```

**¿Qué vista?** `vw_inscriptos_por_comision` (la del ejercicio 13).

**¿Por qué esa?** Porque ya tiene calculado, por comisión, el dato que hay que filtrar (`cantidad_inscriptos`). `vw_comisiones_docentes` no tiene conteos.

**Ventajas de reutilizarla:**
- No se repiten los `JOIN`, el `LEFT JOIN` ni el `GROUP BY`: menos código y menos chances de equivocarse.
- El conteo pasa a ser una columna más, así que alcanza con un `WHERE` (sin `HAVING`).
- La lógica queda en un solo lugar: si cambia (por ejemplo, no contar las bajas) se corrige la vista con `CREATE OR REPLACE VIEW` y todas las consultas que la usan quedan actualizadas.

Con los datos reales hay una sola comisión con más de 30 (la 1163, con 32). El corrector agrega una con exactamente 30 (no supera) y otra con 31.""",
        errores_comunes=[
            "Reescribir toda la consulta con JOIN y GROUP BY: da bien, pero el ejercicio pide reutilizar la vista.",
            "Filtrar por `cupo > 30` en vez de por la cantidad de inscriptos.",
            "Usar `>= 30`: «superen los 30» excluye a las que tienen exactamente 30.",
        ],
        trampas=[
            dict(titulo="Sin usar la vista", sql="""SELECT c.id_comision, COUNT(*) AS cantidad_inscriptos
FROM comisiones c
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.id_comision
HAVING COUNT(*) > 30;"""),
            dict(titulo="Filtra por cupo", sql="""SELECT *
FROM vw_inscriptos_por_comision
WHERE cupo > 30;"""),
            dict(titulo="Mayor o igual a 30", sql="""SELECT *
FROM vw_inscriptos_por_comision
WHERE cantidad_inscriptos >= 30;"""),
        ],
        tags=["vista", "reutilización", "WHERE"],
    ),

    # ------------------------------------------------------------------
    # Variantes nuevas (de menor a mayor dificultad)
    # ------------------------------------------------------------------
    dict(
        id="vis-n01",
        origen="Variante",
        titulo="Vista de notas con alumno y asignatura",
        dificultad=2,
        tipo="view",
        enunciado="Crear una vista con el **detalle de las notas**: para cada nota, el alumno (id, nombre y apellido), "
                  "la asignatura, el tipo de examen (parcial/recuperatorio) y la nota.",
        solucion="""CREATE VIEW vw_notas_detalle AS
SELECT n.id_nota,
       al.id_alumno,
       al.nombre,
       al.apellido,
       asg.nombre AS asignatura,
       e.tipo     AS tipo_examen,
       e.fecha,
       n.nota
FROM notas n
JOIN alumnos al      ON al.id_alumno = n.id_alumno
JOIN examenes e      ON e.id_examen = n.id_examen
JOIN comisiones c    ON c.id_comision = e.id_comision
JOIN asignaturas asg ON asg.id_asignatura = c.id_asignatura;""",
        columnas=[["id_alumno", "asignatura", "tipo_examen", "nota"],
                  ["nombre", "apellido", "asignatura", "tipo_examen", "nota"]],
        pistas=[
            "Seguí las FKs desde `notas`: `notas → examenes → comisiones → asignaturas`, y `notas → alumnos`.",
            "El tipo de examen está en `examenes.tipo`; la asignatura recién aparece al llegar a `comisiones`.",
            "`alumnos.nombre` y `asignaturas.nombre` chocan: alias para la asignatura (`AS asignatura`).",
        ],
        explicacion="""La tabla `notas` no conoce la asignatura: solo sabe a qué **examen** pertenece. Hay que recorrer el camino de FKs:

```sql
FROM notas n
JOIN examenes e      ON e.id_examen     = n.id_examen
JOIN comisiones c    ON c.id_comision   = e.id_comision
JOIN asignaturas asg ON asg.id_asignatura = c.id_asignatura
JOIN alumnos al      ON al.id_alumno    = n.id_alumno
```

No se puede «saltear» `comisiones`: `examenes` solo tiene `id_comision`, y compararlo con `id_asignatura` une filas que no tienen nada que ver.

El alias `asg.nombre AS asignatura` evita el error **1060** con `al.nombre`. Resultado: una fila por nota (54.661).

Con la vista creada, consultas como «notas de Juan Pérez en parciales» se vuelven un `SELECT ... WHERE` sobre una sola «tabla».""",
        errores_comunes=[
            "Saltear `comisiones` y unir `examenes.id_comision` con `asignaturas.id_asignatura`.",
            "Dejar `al.nombre` y `asg.nombre` sin alias → error 1060.",
        ],
        trampas=[
            dict(titulo="Columnas duplicadas (error 1060)", sql="""CREATE VIEW vw_notas_detalle AS
SELECT al.id_alumno, al.nombre, al.apellido, asg.nombre, e.tipo, n.nota
FROM notas n
JOIN alumnos al ON al.id_alumno = n.id_alumno
JOIN examenes e ON e.id_examen = n.id_examen
JOIN comisiones c ON c.id_comision = e.id_comision
JOIN asignaturas asg ON asg.id_asignatura = c.id_asignatura;"""),
            dict(titulo="Saltea comisiones", sql="""CREATE VIEW vw_notas_detalle AS
SELECT al.id_alumno, al.nombre, al.apellido, asg.nombre AS asignatura, e.tipo AS tipo_examen, n.nota
FROM notas n
JOIN alumnos al ON al.id_alumno = n.id_alumno
JOIN examenes e ON e.id_examen = n.id_examen
JOIN asignaturas asg ON asg.id_asignatura = e.id_comision;"""),
        ],
        tags=["CREATE VIEW", "JOIN", "alias"],
    ),
    dict(
        id="vis-n02",
        origen="Variante",
        titulo="Vista de mesas finales",
        dificultad=2,
        tipo="view",
        enunciado="Crear una vista de **mesas de examen final** que muestre, para cada mesa: id, fecha y turno, "
                  "la asignatura, el docente (nombre y apellido) y el aula (nombre).",
        solucion="""CREATE VIEW vw_mesas_detalle AS
SELECT m.id_mesa,
       m.fecha,
       m.turno,
       m.llamado,
       asg.nombre AS asignatura,
       d.nombre   AS nombre_docente,
       d.apellido AS apellido_docente,
       au.nombre  AS aula
FROM mesas_finales m
JOIN asignaturas asg ON asg.id_asignatura = m.id_asignatura
JOIN docentes d      ON d.id_docente = m.id_docente
JOIN aulas au        ON au.id_aula = m.id_aula;""",
        columnas=[["id_mesa", "asignatura", "nombre_docente", "apellido_docente", "aula"],
                  ["fecha", "turno", "asignatura", "nombre_docente", "apellido_docente", "aula"]],
        pistas=[
            "`mesas_finales` tiene tres FKs: `id_asignatura`, `id_docente` e `id_aula`.",
            "Un JOIN por cada FK; el docente de la mesa es `mesas_finales.id_docente` (no el de las comisiones).",
            "Tres tablas tienen una columna `nombre`: alias para cada una (`asignatura`, `nombre_docente`, `aula`).",
        ],
        explicacion="""Cada mesa tiene su propia asignatura, su docente y su aula, así que alcanza con un `JOIN` por cada FK de `mesas_finales` y la vista queda con una fila por mesa (2.500).

El problema típico es el de los nombres: `asignaturas.nombre`, `docentes.nombre` y `aulas.nombre` se llaman igual. En un `SELECT` suelto MySQL lo tolera, pero en una vista no → error **1060**. Solución: alias para todas.

Otro error: buscar al docente a través de `comisiones` o `docente_asignatura`. El docente que toma la mesa está registrado en la propia mesa; pasar por otras tablas multiplica filas y mezcla docentes.

Si después necesitás cambiar la vista (por ejemplo agregar la capacidad del aula), usá `CREATE OR REPLACE VIEW vw_mesas_detalle AS ...`.""",
        errores_comunes=[
            "Dejar varias columnas `nombre` sin alias → error 1060.",
            "Tomar el docente desde `comisiones` o `docente_asignatura`: multiplica filas.",
        ],
        trampas=[
            dict(titulo="Tres columnas 'nombre' (error 1060)", sql="""CREATE VIEW vw_mesas_detalle AS
SELECT m.id_mesa, m.fecha, m.turno, asg.nombre, d.nombre, d.apellido, au.nombre
FROM mesas_finales m
JOIN asignaturas asg ON asg.id_asignatura = m.id_asignatura
JOIN docentes d ON d.id_docente = m.id_docente
JOIN aulas au ON au.id_aula = m.id_aula;"""),
            dict(titulo="Docente tomado de las comisiones", sql="""CREATE VIEW vw_mesas_detalle AS
SELECT m.id_mesa, m.fecha, m.turno, asg.nombre AS asignatura,
       d.nombre AS nombre_docente, d.apellido AS apellido_docente, au.nombre AS aula
FROM mesas_finales m
JOIN asignaturas asg ON asg.id_asignatura = m.id_asignatura
JOIN comisiones c ON c.id_asignatura = m.id_asignatura
JOIN docentes d ON d.id_docente = c.id_docente
JOIN aulas au ON au.id_aula = m.id_aula;"""),
        ],
        tags=["CREATE VIEW", "JOIN", "alias"],
    ),
    dict(
        id="vis-n03",
        origen="Variante",
        titulo="Usar vw_alumnos_carreras: activos por carrera",
        dificultad=2,
        tipo="select",
        enunciado="Usando la vista **`vw_alumnos_carreras`** (ya existe en la base de práctica, con las columnas id_alumno, "
                  "nombre, apellido, dni, id_carrera, carrera, estado_carrera, fecha_inscripcion), mostrá la "
                  "**cantidad de alumnos activos por carrera**: nombre de la carrera y cantidad.",
        solucion="""SELECT id_carrera, carrera, COUNT(*) AS alumnos_activos
FROM vw_alumnos_carreras
WHERE estado_carrera = 'activa'
GROUP BY id_carrera, carrera;""",
        alternativas=[
            dict(titulo="Agrupando solo por el nombre de la carrera", sql="""SELECT carrera, COUNT(*) AS alumnos_activos
FROM vw_alumnos_carreras
WHERE estado_carrera = 'activa'
GROUP BY carrera;"""),
        ],
        columnas=[["carrera", "alumnos_activos"], ["id_carrera", "alumnos_activos"]],
        debe_contener=[dict(patron=r"\bvw_alumnos_carreras\b",
                            mensaje="El ejercicio pide usar la vista `vw_alumnos_carreras` (no las tablas originales).")],
        pistas=[
            "La vista ya resolvió los JOIN: tratala como una tabla con una fila por alumno-carrera.",
            "Filtrá los activos con `WHERE estado_carrera = 'activa'` (mirá el nombre exacto de la columna en la vista).",
            "`GROUP BY carrera` y `COUNT(*)`.",
        ],
        explicacion="""Sin la vista, esta consulta necesitaría dos `JOIN` (alumnos → alumno_carrera → carreras). Con la vista queda un `SELECT` sobre una sola «tabla»:

```sql
SELECT carrera, COUNT(*) AS alumnos_activos
FROM vw_alumnos_carreras
WHERE estado_carrera = 'activa'
GROUP BY carrera;
```

El orden de evaluación es el de siempre: primero el `WHERE` deja solo las filas activas y después el `GROUP BY` las cuenta por carrera.

Ojo con los **nombres de columna de la vista**: son los alias que se definieron al crearla (`carrera`, `estado_carrera`), no los de las tablas originales (`nombre`, `estado`). Si no te acordás, mirá con `DESCRIBE vw_alumnos_carreras;`.""",
        errores_comunes=[
            "Olvidar el filtro de estado: cuenta también pausados, graduados y abandonados.",
            "Usar los nombres de las tablas originales (`estado`, `nombre`) en vez de los alias de la vista.",
            "Reescribir los JOIN sobre las tablas: el ejercicio pide usar la vista.",
        ],
        trampas=[
            dict(titulo="Sin filtrar activos", sql="""SELECT carrera, COUNT(*) AS alumnos
FROM vw_alumnos_carreras
GROUP BY carrera;"""),
            dict(titulo="Sin usar la vista", sql="""SELECT c.nombre AS carrera, COUNT(*) AS alumnos_activos
FROM alumno_carrera ac
JOIN carreras c ON c.id_carrera = ac.id_carrera
WHERE ac.estado = 'activa'
GROUP BY c.id_carrera, c.nombre;"""),
        ],
        tags=["vista", "GROUP BY", "COUNT", "WHERE"],
    ),
    dict(
        id="vis-n04",
        origen="Variante",
        titulo="Usar vw_comisiones_docentes: más de 10",
        dificultad=2,
        tipo="select",
        enunciado="Usando la vista **`vw_comisiones_docentes`** (ya existe en la base de práctica; tiene, entre otras, "
                  "id_comision, id_docente, nombre_docente y apellido_docente), obtené los docentes que tienen "
                  "**más de 10 comisiones** asignadas. Mostrá el docente y la cantidad de comisiones.",
        solucion="""SELECT id_docente, nombre_docente, apellido_docente,
       COUNT(*) AS cantidad_comisiones
FROM vw_comisiones_docentes
GROUP BY id_docente, nombre_docente, apellido_docente
HAVING COUNT(*) > 10;""",
        columnas=[["id_docente", "cantidad_comisiones"],
                  ["nombre_docente", "apellido_docente", "cantidad_comisiones"]],
        debe_contener=[dict(patron=r"\bvw_comisiones_docentes\b",
                            mensaje="El ejercicio pide usar la vista `vw_comisiones_docentes` (no las tablas originales).")],
        pistas=[
            "La vista tiene una fila por comisión, con los datos de su docente.",
            "Agrupá por docente (incluí el `id_docente`) y contá filas.",
            "La condición sobre el conteo va en el `HAVING`: `HAVING COUNT(*) > 10`.",
        ],
        explicacion="""La vista ya trae, en cada fila, la comisión junto con su docente. Contar comisiones por docente es un `GROUP BY` común y la condición sobre el conteo va en el **`HAVING`** (en el `WHERE` daría error 1111).

```sql
SELECT id_docente, nombre_docente, apellido_docente, COUNT(*) AS cantidad_comisiones
FROM vw_comisiones_docentes
GROUP BY id_docente, nombre_docente, apellido_docente
HAVING COUNT(*) > 10;
```

Agrupá por **`id_docente`**: hay docentes homónimos (por ejemplo, dos «Martín Torres» con 11 comisiones cada uno). Si agrupás solo por nombre y apellido aparecen como uno solo con 22.

«Más de 10» = `> 10`. Resultado: 10 docentes.""",
        errores_comunes=[
            "Poner `COUNT(*) > 10` en el WHERE → error 1111.",
            "Agrupar solo por nombre y apellido: junta a los homónimos.",
            "Usar `>= 10`: incluye a los que tienen exactamente 10.",
        ],
        trampas=[
            dict(titulo="Agrupa por nombre y apellido", sql="""SELECT nombre_docente, apellido_docente, COUNT(*) AS cantidad_comisiones
FROM vw_comisiones_docentes
GROUP BY nombre_docente, apellido_docente
HAVING COUNT(*) > 10;"""),
            dict(titulo="COUNT en el WHERE", sql="""SELECT id_docente, nombre_docente, apellido_docente, COUNT(*) AS cantidad_comisiones
FROM vw_comisiones_docentes
WHERE COUNT(*) > 10
GROUP BY id_docente, nombre_docente, apellido_docente;"""),
            dict(titulo="Mayor o igual a 10", sql="""SELECT id_docente, nombre_docente, apellido_docente, COUNT(*) AS cantidad_comisiones
FROM vw_comisiones_docentes
GROUP BY id_docente, nombre_docente, apellido_docente
HAVING COUNT(*) >= 10;"""),
        ],
        tags=["vista", "GROUP BY", "HAVING", "COUNT"],
    ),
    dict(
        id="vis-n05",
        origen="Variante",
        titulo="Vista con columnas en la cabecera",
        dificultad=2,
        tipo="view",
        enunciado="Crear la vista `vw_resumen_departamentos` que muestre, para cada departamento, su **nombre**, la "
                  "**cantidad de docentes** y el **salario base promedio** (redondeado a 2 decimales). Definí los nombres "
                  "de las columnas **en la cabecera** de la vista:\n\n"
                  "`CREATE VIEW vw_resumen_departamentos (departamento, cantidad_docentes, salario_promedio) AS SELECT ...`",
        solucion="""CREATE VIEW vw_resumen_departamentos (departamento, cantidad_docentes, salario_promedio) AS
SELECT dep.nombre,
       COUNT(d.id_docente),
       ROUND(AVG(d.salario_base), 2)
FROM departamentos dep
LEFT JOIN docentes d ON d.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre;""",
        alternativas=[
            dict(titulo="Con CREATE OR REPLACE", sql="""CREATE OR REPLACE VIEW vw_resumen_departamentos (departamento, cantidad_docentes, salario_promedio) AS
SELECT dep.nombre,
       COUNT(d.id_docente),
       ROUND(AVG(d.salario_base), 2)
FROM departamentos dep
LEFT JOIN docentes d ON d.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre;"""),
        ],
        pistas=[
            "La lista entre paréntesis después del nombre de la vista renombra las columnas del `SELECT`, **en orden**.",
            "Tiene que haber tantos nombres en la cabecera como columnas en el `SELECT`.",
            "Agrupá los docentes por departamento: `COUNT(d.id_docente)` y `ROUND(AVG(d.salario_base), 2)` con `GROUP BY dep.id_departamento, dep.nombre`.",
        ],
        explicacion="""La cabecera `(departamento, cantidad_docentes, salario_promedio)` le pone nombre a las columnas de la vista **por posición**: la 1ª columna del `SELECT` se llama `departamento`, la 2ª `cantidad_docentes`, etc. Es equivalente a poner alias en el `SELECT`, pero queda todo junto y a la vista.

Sin cabecera ni alias, la vista igual se crea, pero las columnas se llamarían `COUNT(d.id_docente)` y `ROUND(AVG(d.salario_base), 2)`: imposibles de usar después.

Si la cantidad de nombres no coincide con la de columnas → error **1353**. La cabecera también resuelve el error **1060**: en `(id, docente, departamento) AS SELECT d.id_docente, d.nombre, dep.nombre`, los dos `nombre` quedan renombrados.

Para modificar una vista existente: `CREATE OR REPLACE VIEW` (si no, error 1050).""",
        errores_comunes=[
            "Poner en la cabecera una cantidad de nombres distinta a la de columnas del SELECT → error 1353.",
            "Contar docentes uniendo también `comisiones`: el JOIN multiplica las filas y el COUNT da cualquier cosa.",
            "Volver a ejecutar `CREATE VIEW` sobre una vista existente → error 1050; usá `CREATE OR REPLACE VIEW`.",
        ],
        trampas=[
            dict(titulo="Cabecera con menos nombres (error 1353)", sql="""CREATE VIEW vw_resumen_departamentos (departamento, cantidad_docentes) AS
SELECT dep.nombre, COUNT(d.id_docente), ROUND(AVG(d.salario_base), 2)
FROM departamentos dep
LEFT JOIN docentes d ON d.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre;"""),
            dict(titulo="JOIN de más: cuenta comisiones", sql="""CREATE VIEW vw_resumen_departamentos (departamento, cantidad_docentes, salario_promedio) AS
SELECT dep.nombre, COUNT(d.id_docente), ROUND(AVG(d.salario_base), 2)
FROM departamentos dep
JOIN docentes d ON d.id_departamento = dep.id_departamento
JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY dep.id_departamento, dep.nombre;"""),
        ],
        tags=["CREATE VIEW", "lista de columnas", "GROUP BY", "CREATE OR REPLACE"],
    ),
    dict(
        id="vis-n06",
        origen="Variante",
        titulo="Vista de porcentaje de asistencia",
        dificultad=3,
        tipo="view",
        enunciado="Crear una vista con el **porcentaje de asistencia de cada alumno** (considerando todas sus clases, "
                  "de todas las comisiones). Mostrá id, nombre, apellido, cantidad de clases, cantidad de presentes y "
                  "el porcentaje (0 a 100, con 2 decimales).",
        solucion="""CREATE VIEW vw_asistencia_alumnos AS
SELECT a.id_alumno,
       a.nombre,
       a.apellido,
       COUNT(*)        AS clases,
       SUM(s.presente) AS presentes,
       ROUND(100 * SUM(s.presente) / COUNT(*), 2) AS porcentaje_asistencia
FROM alumnos a
JOIN asistencias s ON s.id_alumno = a.id_alumno
GROUP BY a.id_alumno, a.nombre, a.apellido;""",
        alternativas=[
            dict(titulo="Con AVG(presente)", sql="""CREATE VIEW vw_asistencia_alumnos AS
SELECT a.id_alumno,
       a.nombre,
       a.apellido,
       COUNT(*) AS clases,
       SUM(s.presente) AS presentes,
       ROUND(AVG(s.presente) * 100, 2) AS porcentaje_asistencia
FROM alumnos a
JOIN asistencias s ON s.id_alumno = a.id_alumno
GROUP BY a.id_alumno, a.nombre, a.apellido;"""),
        ],
        columnas=[["id_alumno", "porcentaje_asistencia"], ["nombre", "apellido", "porcentaje_asistencia"]],
        pistas=[
            "`asistencias` tiene una fila por alumno, comisión y fecha, con `presente` en 1 o 0.",
            "Como `presente` vale 1/0, `SUM(presente)` cuenta los presentes y `COUNT(*)` las clases.",
            "Porcentaje = `100 * SUM(presente) / COUNT(*)`; agrupá por `a.id_alumno, a.nombre, a.apellido` y poné alias a cada cálculo.",
        ],
        explicacion="""`presente` es un `TINYINT` con 1 (presente) o 0 (ausente). Eso permite dos trucos:

- `SUM(s.presente)` = cantidad de presentes.
- `AVG(s.presente)` = proporción de presentes (×100 para el porcentaje).

```sql
ROUND(100 * SUM(s.presente) / COUNT(*), 2) AS porcentaje_asistencia
```

¡No uses `COUNT(s.presente)`! `COUNT(columna)` cuenta los valores **no nulos**, y 0 no es nulo: contaría todas las clases y daría 100% para todos.

En una vista, cada expresión calculada necesita alias (o nombre en la cabecera); si no, la columna se llama `ROUND(100 * SUM(...` y es incómoda de consultar.

Agrupá por `id_alumno`: hay muchos alumnos homónimos. Resultado: 1.000 filas, con porcentajes entre 72% y 90%.""",
        errores_comunes=[
            "Usar `COUNT(presente)` para contar presentes: también cuenta los 0 (solo ignora NULL).",
            "Agrupar por nombre y apellido sin el id: mezcla alumnos homónimos.",
            "Olvidar multiplicar por 100 (queda una proporción, no un porcentaje).",
        ],
        trampas=[
            dict(titulo="COUNT(presente) cuenta también los ausentes", sql="""CREATE VIEW vw_asistencia_alumnos AS
SELECT a.id_alumno, a.nombre, a.apellido,
       ROUND(100 * COUNT(s.presente) / COUNT(*), 2) AS porcentaje_asistencia
FROM alumnos a
JOIN asistencias s ON s.id_alumno = a.id_alumno
GROUP BY a.id_alumno, a.nombre, a.apellido;"""),
            dict(titulo="Agrupa por nombre y apellido", sql="""CREATE VIEW vw_asistencia_alumnos AS
SELECT a.nombre, a.apellido,
       ROUND(100 * SUM(s.presente) / COUNT(*), 2) AS porcentaje_asistencia
FROM alumnos a
JOIN asistencias s ON s.id_alumno = a.id_alumno
GROUP BY a.nombre, a.apellido;"""),
        ],
        tags=["CREATE VIEW", "SUM", "AVG", "GROUP BY", "porcentaje"],
    ),
]
