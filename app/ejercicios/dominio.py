"""Sección: Problemáticas de dominio — pedidos narrativos con umbrales (TP1 · Sección 2)."""

EJERCICIOS = [
    # ------------------------------------------------------------------
    # Originales del TP1 · Sección 2
    # ------------------------------------------------------------------
    dict(
        id="dom-01",
        origen="TP1 · Sección 2 · Ej. 1",
        titulo="Carreras con alta demanda",
        dificultad=3,
        tipo="select",
        enunciado="Desde el área de planificación académica nos informan que necesitan identificar aquellas carreras "
                  "que tienen una alta demanda de estudiantes activos. Consideran que una carrera tiene alta demanda "
                  "cuando supera los 90 alumnos inscriptos actualmente en comisiones con estado distinto de 'Baja'. "
                  "Esta información será utilizada para evaluar la apertura de nuevas comisiones y asignación de más docentes.\n\n"
                  "*Aclaración:* mostrá la carrera (id o nombre) y la cantidad de alumnos.",
        solucion="""SELECT ca.id_carrera, ca.nombre, COUNT(DISTINCT i.id_alumno) AS alumnos
FROM carreras ca
JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
JOIN inscripcion_alumno_comision i ON i.id_alumno = ac.id_alumno
WHERE i.estado <> 'Baja'
GROUP BY ca.id_carrera, ca.nombre
HAVING COUNT(DISTINCT i.id_alumno) > 90;""",
        alternativas=[
            dict(titulo="Sin JOIN con carreras (solo el id)", sql="""SELECT ac.id_carrera, COUNT(DISTINCT i.id_alumno) AS alumnos
FROM alumno_carrera ac
JOIN inscripcion_alumno_comision i ON i.id_alumno = ac.id_alumno
WHERE i.estado <> 'Baja'
GROUP BY ac.id_carrera
HAVING COUNT(DISTINCT i.id_alumno) > 90;"""),
        ],
        variantes=[
            dict(titulo="«Actualmente» = comisiones de 2026 (además de estado <> 'Baja')", sql="""SELECT ca.id_carrera, ca.nombre, COUNT(DISTINCT i.id_alumno) AS alumnos
FROM carreras ca
JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
JOIN inscripcion_alumno_comision i ON i.id_alumno = ac.id_alumno
JOIN comisiones c ON c.id_comision = i.id_comision
WHERE i.estado <> 'Baja'
  AND c.anio = 2026
GROUP BY ca.id_carrera, ca.nombre
HAVING COUNT(DISTINCT i.id_alumno) > 90;"""),
        ],
        columnas=[["id_carrera", "alumnos"], ["nombre", "alumnos"]],
        debe_contener=[dict(patron=r"\bestado\b",
                            mensaje="El pedido habla de inscripciones con estado distinto de 'Baja': falta filtrar por "
                                    "el estado de la inscripción (con estos datos da igual, pero en el parcialito te lo marcan).")],
        pistas=[
            "La carrera de un alumno está en `alumno_carrera`; sus inscripciones a comisiones, en `inscripcion_alumno_comision`. Uní esas tablas por `id_alumno`.",
            "Después del JOIN hay una fila por **inscripción**: un alumno aparece una vez por cada comisión. ¿Querés contar inscripciones o alumnos?",
            "`WHERE i.estado <> 'Baja'` filtra filas; `GROUP BY` la carrera; `HAVING COUNT(DISTINCT i.id_alumno) > 90` filtra carreras.",
        ],
        explicacion="""**Traducción del pedido:**

- *Qué se lista:* carreras → `GROUP BY ca.id_carrera, ca.nombre`.
- *Qué se mide:* alumnos (personas) → `COUNT(DISTINCT i.id_alumno)`.
- *Filtro de filas:* inscripciones con `estado <> 'Baja'` → `WHERE`.
- *Umbral del grupo:* más de 90 → `HAVING ... > 90`.

El camino es `carreras → alumno_carrera → inscripcion_alumno_comision`: la carrera es **la del alumno**.

**¿Por qué DISTINCT?** Un alumno con 15 comisiones aparece 15 veces después del JOIN. Con `COUNT(*)` contás inscripciones (más de 1000 por carrera) y *todas* las carreras «superan 90»: un informe que no sirve para decidir nada.

**Otras lecturas:**
- «Actualmente» como comisiones de 2026: agregá `c.anio = 2026` (también se acepta).
- Ir por `asignaturas → departamento → carreras` está mal: una materia no es de una carrera, y cada inscripción se contaría para todas las carreras del departamento.
- Agregar `ac.estado = 'activa'` suma una condición que el pedido no pide (y con 90 da vacío).""",
        errores_comunes=[
            "`COUNT(*)` en vez de `COUNT(DISTINCT i.id_alumno)`: cuenta inscripciones y todas las carreras pasan el umbral.",
            "Vincular la carrera por departamento (asignatura → departamento → carreras) en vez de por `alumno_carrera`.",
            "Agregar condiciones que el pedido no tiene, como `ac.estado = 'activa'`.",
        ],
        trampas=[
            dict(titulo="COUNT(*) (cuenta inscripciones)", sql="""SELECT ca.id_carrera, ca.nombre, COUNT(*) AS alumnos
FROM carreras ca
JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
JOIN inscripcion_alumno_comision i ON i.id_alumno = ac.id_alumno
WHERE i.estado <> 'Baja'
GROUP BY ca.id_carrera, ca.nombre
HAVING COUNT(*) > 90;"""),
            dict(titulo="Carrera por departamento de la asignatura", sql="""SELECT ca.id_carrera, ca.nombre, COUNT(DISTINCT i.id_alumno) AS alumnos
FROM carreras ca
JOIN asignaturas a ON a.id_departamento = ca.id_departamento
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
WHERE i.estado <> 'Baja'
GROUP BY ca.id_carrera, ca.nombre
HAVING COUNT(DISTINCT i.id_alumno) > 90;"""),
            dict(titulo="Filtro extra: solo alumnos con carrera 'activa'", sql="""SELECT ca.id_carrera, ca.nombre, COUNT(DISTINCT i.id_alumno) AS alumnos
FROM carreras ca
JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
JOIN inscripcion_alumno_comision i ON i.id_alumno = ac.id_alumno
WHERE i.estado <> 'Baja'
  AND ac.estado = 'activa'
GROUP BY ca.id_carrera, ca.nombre
HAVING COUNT(DISTINCT i.id_alumno) > 90;"""),
        ],
        tags=["JOIN", "GROUP BY", "HAVING", "COUNT DISTINCT", "umbral"],
    ),
    dict(
        id="dom-02",
        origen="TP1 · Sección 2 · Ej. 2",
        titulo="Docentes sobrecargados",
        dificultad=3,
        tipo="select",
        enunciado="El departamento de recursos humanos quiere detectar docentes que podrían estar sobrecargados de trabajo. "
                  "Para esto, necesitan identificar aquellos docentes que, sumando todas sus comisiones asignadas, "
                  "superan las 80 horas este año. La idea es utilizar esta información para redistribuir la carga "
                  "horaria entre el plantel docente.\n\n"
                  "*Aclaración:* tomá «este año» como **2026** (el último año con datos). Mostrá el docente "
                  "(id o nombre y apellido) y el total de horas.",
        solucion="""SELECT d.id_docente, d.nombre, d.apellido, SUM(da.horas_asignadas) AS horas
FROM docentes d
JOIN docente_asignatura da ON da.id_docente = d.id_docente
WHERE da.anio = 2026
GROUP BY d.id_docente, d.nombre, d.apellido
HAVING SUM(da.horas_asignadas) > 80;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id del docente)", sql="""SELECT id_docente, SUM(horas_asignadas) AS horas
FROM docente_asignatura
WHERE anio = 2026
GROUP BY id_docente
HAVING SUM(horas_asignadas) > 80;"""),
        ],
        variantes=[
            dict(titulo="Horas = carga horaria de las asignaturas de sus comisiones de 2026", sql="""SELECT d.id_docente, d.nombre, d.apellido, SUM(a.carga_horaria) AS horas
FROM docentes d
JOIN comisiones c ON c.id_docente = d.id_docente
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
WHERE c.anio = 2026
GROUP BY d.id_docente, d.nombre, d.apellido
HAVING SUM(a.carga_horaria) > 80;"""),
        ],
        columnas=[["id_docente", "horas"], ["nombre", "apellido", "horas"]],
        pistas=[
            "`comisiones` no tiene una columna de horas. ¿Dónde se registran las horas asignadas a cada docente? Mirá `docente_asignatura`.",
            "Primero quedate con las filas de 2026 (`WHERE`), después sumá por docente (`SUM` + `GROUP BY`).",
            "`... WHERE da.anio = 2026 GROUP BY d.id_docente, d.nombre, d.apellido HAVING SUM(da.horas_asignadas) > 80`.",
        ],
        explicacion="""**Decisión de modelado:** `comisiones` no tiene horas. Las horas asignadas a cada docente están en `docente_asignatura.horas_asignadas` (por asignatura, año y cuatrimestre). Esa es la solución:

- *Filtro de filas:* `da.anio = 2026` → `WHERE`.
- *Métrica:* `SUM(da.horas_asignadas)` por docente.
- *Umbral:* `HAVING SUM(...) > 80`.

**Otra lectura (también aceptada):** sumar la `carga_horaria` de las asignaturas de sus comisiones de 2026, siguiendo el «sumando sus comisiones» literal. Ojo: `carga_horaria` es la carga **total** de la materia (48 a 143 h), así que con 80 casi todos «superan» (150 de 163). Es una señal de que el umbral se pensó para las horas asignadas.

**«Este año»:** podrías escribir `YEAR(CURDATE())`. Hoy da 2026, pero el resultado cambia según el día en que se ejecuta. Acá lo fijamos.

Agrupá por `id_docente`: hay docentes con el mismo nombre y apellido.""",
        errores_comunes=[
            "Olvidar el filtro de año: suma 2024–2026 y salen casi todos los docentes (198).",
            "Usar `>= 80` cuando dice «superan las 80».",
            "Agrupar solo por nombre y apellido: los homónimos se suman juntos.",
        ],
        trampas=[
            dict(titulo="Sin filtro de año", sql="""SELECT d.id_docente, d.nombre, d.apellido, SUM(da.horas_asignadas) AS horas
FROM docentes d
JOIN docente_asignatura da ON da.id_docente = d.id_docente
GROUP BY d.id_docente, d.nombre, d.apellido
HAVING SUM(da.horas_asignadas) > 80;"""),
            dict(titulo=">= 80 en vez de > 80", sql="""SELECT d.id_docente, d.nombre, d.apellido, SUM(da.horas_asignadas) AS horas
FROM docentes d
JOIN docente_asignatura da ON da.id_docente = d.id_docente
WHERE da.anio = 2026
GROUP BY d.id_docente, d.nombre, d.apellido
HAVING SUM(da.horas_asignadas) >= 80;"""),
            dict(titulo="Agrupar por nombre y apellido (junta homónimos)", sql="""SELECT d.nombre, d.apellido, SUM(da.horas_asignadas) AS horas
FROM docentes d
JOIN docente_asignatura da ON da.id_docente = d.id_docente
WHERE da.anio = 2026
GROUP BY d.nombre, d.apellido
HAVING SUM(da.horas_asignadas) > 80;"""),
        ],
        tags=["JOIN", "WHERE", "GROUP BY", "HAVING", "SUM", "umbral"],
    ),
    dict(
        id="dom-03",
        origen="TP1 · Sección 2 · Ej. 3",
        titulo="Materias con muchos desaprobados",
        dificultad=2,
        tipo="select",
        enunciado="La dirección académica está preocupada por el rendimiento de los alumnos en ciertas asignaturas. "
                  "Solicitan un informe que permita identificar aquellas materias que registran más de 90 exámenes "
                  "desaprobados (considerando como desaprobado una nota menor a 4). Esto permitirá tomar medidas como "
                  "reforzar contenidos o modificar estrategias de enseñanza.\n\n"
                  "*Aclaración:* cada fila de `notas` es el examen de un alumno. Mostrá la asignatura (id o nombre) "
                  "y la cantidad de desaprobados.",
        solucion="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS desaprobados
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
WHERE n.nota < 4
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > 90;""",
        alternativas=[
            dict(titulo="Conteo condicional en el HAVING (sin WHERE)", sql="""SELECT a.id_asignatura, a.nombre, SUM(n.nota < 4) AS desaprobados
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
GROUP BY a.id_asignatura, a.nombre
HAVING SUM(n.nota < 4) > 90;"""),
            dict(titulo="Usando la vista vw_notas_por_asignatura", sql="""SELECT id_asignatura, asignatura, desaprobados
FROM vw_notas_por_asignatura
WHERE desaprobados > 90;"""),
        ],
        columnas=[["id_asignatura", "desaprobados"], ["nombre", "desaprobados"]],
        pistas=[
            "Las notas no conocen la asignatura: hay que recorrer `asignaturas → comisiones → examenes → notas`.",
            "El desaprobado se define por la nota (`nota < 4`): eso es un filtro de **filas**.",
            "`... WHERE n.nota < 4 GROUP BY a.id_asignatura, a.nombre HAVING COUNT(*) > 90`.",
        ],
        explicacion="""**Camino de JOINs:** `notas` tiene `id_examen`; `examenes` tiene `id_comision`; `comisiones` tiene `id_asignatura`. Hay que atravesar las cuatro tablas para llegar de la nota a la materia.

**Dos filtros distintos:**

- `WHERE n.nota < 4` → se queda con las notas desaprobadas (cada fila, antes de agrupar).
- `HAVING COUNT(*) > 90` → se queda con las materias que tienen más de 90 de esas filas.

Alternativa equivalente: no filtrar en el WHERE y contar con condición, `HAVING SUM(n.nota < 4) > 90`. También podés usar la vista `vw_notas_por_asignatura`, que ya tiene la columna `desaprobados`.

**Usá la definición del enunciado** (`nota < 4`), no la columna `aprobado`: en estos datos no es coherente con la nota, y además el pedido define el criterio explícitamente. `nota <= 4` también está mal: un 4 aprueba.""",
        errores_comunes=[
            "Usar `aprobado = 0` en vez de la definición pedida (`nota < 4`).",
            "Escribir `nota <= 4`: el 4 es aprobado.",
            "Olvidar el filtro de desaprobados y contar todas las notas.",
        ],
        trampas=[
            dict(titulo="aprobado = 0 en vez de nota < 4", sql="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS desaprobados
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
WHERE n.aprobado = 0
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > 90;"""),
            dict(titulo="nota <= 4", sql="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS desaprobados
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
WHERE n.nota <= 4
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > 90;"""),
            dict(titulo="Sin filtrar desaprobados (cuenta todas las notas)", sql="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS desaprobados
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > 90;"""),
        ],
        tags=["JOIN", "WHERE", "GROUP BY", "HAVING", "umbral"],
    ),
    dict(
        id="dom-04",
        origen="TP1 · Sección 2 · Ej. 4",
        titulo="Aulas con uso intensivo en finales",
        dificultad=2,
        tipo="select",
        enunciado="Desde el área de infraestructura desean analizar el uso intensivo de las aulas durante los turnos "
                  "de exámenes finales. Necesitan identificar aquellas aulas que han sido utilizadas en al menos 250 "
                  "mesas finales, para evaluar el desgaste de las instalaciones y planificar mantenimiento preventivo.\n\n"
                  "*Aclaración:* mostrá el aula (id o nombre) y la cantidad de mesas.",
        solucion="""SELECT au.id_aula, au.nombre, COUNT(*) AS mesas
FROM aulas au
JOIN mesas_finales m ON m.id_aula = au.id_aula
GROUP BY au.id_aula, au.nombre
HAVING COUNT(*) >= 250;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id del aula)", sql="""SELECT id_aula, COUNT(*) AS mesas
FROM mesas_finales
GROUP BY id_aula
HAVING COUNT(*) >= 250;"""),
        ],
        columnas=[["id_aula", "mesas"], ["nombre", "mesas"]],
        pistas=[
            "Cada mesa final tiene su `id_aula`. «Usada en una mesa» = una fila de `mesas_finales`.",
            "Contá mesas por aula y filtrá los grupos.",
            "«Al menos 250» es `>= 250`: `... GROUP BY id_aula HAVING COUNT(*) >= 250`.",
        ],
        explicacion="""**Traducción:**

- *Qué se lista:* aulas.
- *Qué se mide:* mesas finales en las que se usó → filas de `mesas_finales` por `id_aula`.
- *Umbral:* «al menos 250» → `HAVING COUNT(*) >= 250` (**al menos** incluye el 250; «más de» no).

No hay filtro de filas: el pedido considera todas las mesas (todas pertenecen a algún turno de examen).

**Errores de modelado típicos:**
- Unir con `inscripciones_finales`: cada mesa se repite una vez por inscripto y terminás contando alumnos, no usos del aula.
- Contar `comisiones`: eso es el uso del aula para cursadas, no para finales.

Y como siempre, una condición sobre `COUNT(*)` no puede ir en el `WHERE` (error 1111).""",
        errores_comunes=[
            "Unir con `inscripciones_finales`: cuenta inscriptos en vez de mesas.",
            "Contar comisiones en lugar de mesas finales.",
            "Poner `COUNT(*) >= 250` en el WHERE (error 1111).",
        ],
        trampas=[
            dict(titulo="JOIN con inscripciones (cuenta inscriptos)", sql="""SELECT au.id_aula, au.nombre, COUNT(*) AS mesas
FROM aulas au
JOIN mesas_finales m ON m.id_aula = au.id_aula
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
GROUP BY au.id_aula, au.nombre
HAVING COUNT(*) >= 250;"""),
            dict(titulo="Cuenta comisiones en vez de mesas", sql="""SELECT au.id_aula, au.nombre, COUNT(*) AS mesas
FROM aulas au
JOIN comisiones c ON c.id_aula = au.id_aula
GROUP BY au.id_aula, au.nombre
HAVING COUNT(*) >= 250;"""),
            dict(titulo="WHERE con agregado (error)", sql="""SELECT id_aula, COUNT(*) AS mesas
FROM mesas_finales
WHERE COUNT(*) >= 250
GROUP BY id_aula;"""),
        ],
        tags=["JOIN", "GROUP BY", "HAVING", "umbral"],
    ),
    dict(
        id="dom-05",
        origen="TP1 · Sección 2 · Ej. 5",
        titulo="Alumnos con muchas inasistencias",
        dificultad=2,
        tipo="select",
        enunciado="El equipo de seguimiento estudiantil quiere detectar alumnos con bajo nivel de asistencia. Para ello, "
                  "necesitan identificar aquellos alumnos que registran más de 40 inasistencias en total a lo largo de "
                  "todas sus comisiones. Esta información se utilizará para implementar políticas de acompañamiento.\n\n"
                  "*Aclaración:* una inasistencia es un registro de `asistencias` con `presente = 0`. Mostrá el alumno "
                  "(id o nombre y apellido) y la cantidad de inasistencias.",
        solucion="""SELECT al.id_alumno, al.nombre, al.apellido, COUNT(*) AS inasistencias
FROM alumnos al
JOIN asistencias asi ON asi.id_alumno = al.id_alumno
WHERE asi.presente = 0
GROUP BY al.id_alumno, al.nombre, al.apellido
HAVING COUNT(*) > 40;""",
        alternativas=[
            dict(titulo="Conteo condicional (sin WHERE)", sql="""SELECT al.id_alumno, al.nombre, al.apellido, SUM(asi.presente = 0) AS inasistencias
FROM alumnos al
JOIN asistencias asi ON asi.id_alumno = al.id_alumno
GROUP BY al.id_alumno, al.nombre, al.apellido
HAVING SUM(asi.presente = 0) > 40;"""),
            dict(titulo="Sin JOIN (solo el id del alumno)", sql="""SELECT id_alumno, COUNT(*) AS inasistencias
FROM asistencias
WHERE presente = 0
GROUP BY id_alumno
HAVING COUNT(*) > 40;"""),
        ],
        columnas=[["id_alumno", "inasistencias"], ["nombre", "apellido", "inasistencias"]],
        pistas=[
            "«A lo largo de todas sus comisiones» significa que agrupás solo por alumno, no por alumno y comisión.",
            "Las inasistencias son las filas con `presente = 0`: filtralas en el `WHERE` (o contalas con `SUM(presente = 0)`).",
            "`... WHERE asi.presente = 0 GROUP BY al.id_alumno, al.nombre, al.apellido HAVING COUNT(*) > 40`.",
        ],
        explicacion="""**Traducción:**

- *Qué se lista:* alumnos → `GROUP BY al.id_alumno` (+ nombre y apellido para mostrarlos).
- *Qué se mide:* inasistencias = filas de `asistencias` con `presente = 0`.
- *Alcance:* «en total, a lo largo de todas sus comisiones» → **no** agrupes por comisión.
- *Umbral:* «más de 40» → `HAVING COUNT(*) > 40` (con `>= 40` aparecen 114 alumnos en vez de 87).

**¿Por qué agrupar por id y no solo por nombre y apellido?** En `alumnos` hay muchísimos homónimos (1000 alumnos, solo 364 combinaciones distintas de nombre y apellido). Si agrupás por nombre, sumás las faltas de varias personas distintas.

Las dos formas de contar son equivalentes: filtrar en el `WHERE` y usar `COUNT(*)`, o no filtrar y usar `SUM(asi.presente = 0)`.""",
        errores_comunes=[
            "Agrupar por nombre y apellido sin el id: se mezclan alumnos homónimos.",
            "Usar `>= 40` en vez de `> 40`.",
            "Contar `presente = 1` (son las asistencias, no las faltas).",
        ],
        trampas=[
            dict(titulo=">= 40 en vez de > 40", sql="""SELECT al.id_alumno, al.nombre, al.apellido, COUNT(*) AS inasistencias
FROM alumnos al
JOIN asistencias asi ON asi.id_alumno = al.id_alumno
WHERE asi.presente = 0
GROUP BY al.id_alumno, al.nombre, al.apellido
HAVING COUNT(*) >= 40;"""),
            dict(titulo="Agrupar por nombre y apellido (junta homónimos)", sql="""SELECT al.nombre, al.apellido, COUNT(*) AS inasistencias
FROM alumnos al
JOIN asistencias asi ON asi.id_alumno = al.id_alumno
WHERE asi.presente = 0
GROUP BY al.nombre, al.apellido
HAVING COUNT(*) > 40;"""),
            dict(titulo="Cuenta presentes en vez de faltas", sql="""SELECT al.id_alumno, al.nombre, al.apellido, COUNT(*) AS inasistencias
FROM alumnos al
JOIN asistencias asi ON asi.id_alumno = al.id_alumno
WHERE asi.presente = 1
GROUP BY al.id_alumno, al.nombre, al.apellido
HAVING COUNT(*) > 40;"""),
        ],
        tags=["JOIN", "WHERE", "GROUP BY", "HAVING", "umbral"],
    ),
    dict(
        id="dom-06",
        origen="TP1 · Sección 2 · Ej. 6",
        titulo="Asignaturas con bajo rendimiento",
        dificultad=2,
        tipo="select",
        enunciado="El consejo académico quiere identificar asignaturas con bajo rendimiento general. Se considera que "
                  "una asignatura tiene bajo rendimiento cuando el promedio general de notas de sus exámenes es menor a 5. "
                  "Esta información permitirá revisar los contenidos y metodologías de enseñanza.\n\n"
                  "*Aclaración:* mostrá la asignatura (id o nombre) y su promedio.",
        solucion="""SELECT a.id_asignatura, a.nombre, ROUND(AVG(n.nota), 2) AS promedio
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
GROUP BY a.id_asignatura, a.nombre
HAVING AVG(n.nota) < 5;""",
        alternativas=[
            dict(titulo="Usando la vista vw_notas_por_asignatura", sql="""SELECT id_asignatura, asignatura, promedio
FROM vw_notas_por_asignatura
WHERE promedio < 5;"""),
        ],
        columnas=[["id_asignatura", "promedio"], ["nombre", "promedio"]],
        pistas=[
            "Igual que con los desaprobados: `asignaturas → comisiones → examenes → notas`.",
            "La condición es sobre el **promedio de la asignatura**, no sobre cada nota.",
            "`... GROUP BY a.id_asignatura, a.nombre HAVING AVG(n.nota) < 5`.",
        ],
        explicacion="""El umbral es sobre un **agregado del grupo** (el promedio de todas las notas de la asignatura), así que va en `HAVING`.

Compará con este error frecuente:

```sql
WHERE n.nota < 5          -- filtra NOTAS
GROUP BY ...              -- promedia solo las notas bajas
```

Eso descarta las notas buenas **antes** de promediar: el promedio de lo que queda es siempre menor a 5 y aparecen todas las asignaturas. El `WHERE` decide qué filas entran al cálculo; el `HAVING` decide qué grupos se muestran.

Otro error de granularidad: agrupar por comisión. El pedido es por **asignatura** (una asignatura tiene varias comisiones).

Si querés reutilizar, la vista `vw_notas_por_asignatura` ya tiene el promedio por asignatura y alcanza con un `WHERE promedio < 5` (en la vista ya es una columna, no un agregado).""",
        errores_comunes=[
            "Filtrar `nota < 5` en el WHERE: cambia qué notas se promedian.",
            "Agrupar por comisión en vez de por asignatura.",
            "Poner `AVG(...)` en el WHERE (error 1111).",
        ],
        trampas=[
            dict(titulo="WHERE nota < 5 (filtra notas, no asignaturas)", sql="""SELECT a.id_asignatura, a.nombre, ROUND(AVG(n.nota), 2) AS promedio
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
WHERE n.nota < 5
GROUP BY a.id_asignatura, a.nombre;"""),
            dict(titulo="Agrupar por comisión", sql="""SELECT c.id_comision, a.nombre, ROUND(AVG(n.nota), 2) AS promedio
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
GROUP BY c.id_comision, a.nombre
HAVING AVG(n.nota) < 5;"""),
            dict(titulo="AVG en el WHERE (error)", sql="""SELECT a.id_asignatura, a.nombre, AVG(n.nota) AS promedio
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
WHERE AVG(n.nota) < 5
GROUP BY a.id_asignatura, a.nombre;"""),
        ],
        tags=["JOIN", "GROUP BY", "HAVING", "AVG", "umbral"],
    ),
    dict(
        id="dom-07",
        origen="TP1 · Sección 2 · Ej. 7",
        titulo="Docentes sin comisiones",
        dificultad=2,
        tipo="select",
        enunciado="Desde la administración se desea identificar docentes que actualmente no tengan asignadas comisiones. "
                  "Esto es importante para poder asignarles nuevas responsabilidades o detectar posibles inconsistencias "
                  "en la planificación académica.\n\n"
                  "*Aclaración:* mostrá id, nombre y apellido del docente.",
        solucion="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
WHERE NOT EXISTS (
    SELECT 1
    FROM comisiones c
    WHERE c.id_docente = d.id_docente
);""",
        alternativas=[
            dict(titulo="Con LEFT JOIN … IS NULL", sql="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
LEFT JOIN comisiones c ON c.id_docente = d.id_docente
WHERE c.id_comision IS NULL;"""),
            dict(titulo="Con NOT IN", sql="""SELECT id_docente, nombre, apellido
FROM docentes
WHERE id_docente NOT IN (SELECT id_docente FROM comisiones);"""),
            dict(titulo="Con LEFT JOIN + GROUP BY + HAVING COUNT(col) = 0", sql="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
LEFT JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY d.id_docente, d.nombre, d.apellido
HAVING COUNT(c.id_comision) = 0;"""),
        ],
        variantes=[
            dict(titulo="«Actualmente» = sin comisiones en 2026", sql="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
WHERE NOT EXISTS (
    SELECT 1
    FROM comisiones c
    WHERE c.id_docente = d.id_docente
      AND c.anio = 2026
);"""),
        ],
        columnas=[["id_docente"], ["nombre", "apellido"]],
        casos_borde=True,
        pistas=[
            "Es un problema de **ausencia**: docentes para los que no existe ninguna fila en `comisiones`.",
            "Caminos clásicos: `NOT EXISTS`, `NOT IN` o `LEFT JOIN … WHERE c.id_comision IS NULL`.",
            "En clave de agrupación: `LEFT JOIN` + `GROUP BY` docente + `HAVING COUNT(c.id_comision) = 0`.",
        ],
        explicacion="""Este pedido no tiene umbral: es de **ausencia** («los que no tienen»). Se resuelve comparando contra la tabla que registra la relación (`comisiones`).

Las cuatro formas aceptadas dan lo mismo:

- `NOT EXISTS (subconsulta correlacionada)`: para cada docente, ¿existe alguna comisión suya?
- `LEFT JOIN … WHERE c.id_comision IS NULL`: los docentes sin match quedan con NULL del lado de `comisiones`.
- `NOT IN (SELECT id_docente FROM comisiones)`: ojo si la subconsulta pudiera traer NULL.
- `LEFT JOIN` + `GROUP BY` + `HAVING COUNT(c.id_comision) = 0`: el conteo de una columna de la derecha es 0 justo cuando no hubo match. Con `COUNT(*)` nunca es 0.

Con los datos originales devuelve **0 filas** (todos los docentes tienen comisiones), por eso el corrector lo prueba con **casos borde** (dos docentes nuevos sin comisiones).

Si «actualmente» lo leés como «sin comisiones en 2026», agregá `AND c.anio = 2026` dentro de la subconsulta: también se acepta.""",
        errores_comunes=[
            "`INNER JOIN` + `IS NULL`: el INNER JOIN ya descartó a los docentes sin comisión.",
            "`HAVING COUNT(*) = 0` con LEFT JOIN: `COUNT(*)` cuenta la fila con NULL, nunca da 0.",
        ],
        trampas=[
            dict(titulo="INNER JOIN con IS NULL", sql="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
JOIN comisiones c ON c.id_docente = d.id_docente
WHERE c.id_comision IS NULL;"""),
            dict(titulo="LEFT JOIN + HAVING COUNT(*) = 0", sql="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
LEFT JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY d.id_docente, d.nombre, d.apellido
HAVING COUNT(*) = 0;"""),
        ],
        tags=["NOT EXISTS", "LEFT JOIN", "HAVING", "ausencia"],
    ),
    dict(
        id="dom-08",
        origen="TP1 · Sección 2 · Ej. 8",
        titulo="Comisiones críticas por inscriptos",
        dificultad=2,
        tipo="select",
        enunciado="El área de planificación necesita detectar comisiones que estén superando su capacidad operativa. "
                  "Consideran críticas aquellas comisiones que tienen más de 30 alumnos inscriptos. Esta información "
                  "será utilizada para abrir nuevas comisiones o redistribuir estudiantes.\n\n"
                  "*Aclaración:* con estos datos solo una comisión supera los 30 inscriptos; para practicar, **usá más de 25**. "
                  "Contá todas las inscripciones (sin importar el estado) y mostrá el id de la comisión y la cantidad.",
        solucion="""SELECT c.id_comision, a.nombre AS asignatura, COUNT(*) AS inscriptos
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.id_comision, a.nombre
HAVING COUNT(*) > 25;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id de la comisión)", sql="""SELECT id_comision, COUNT(*) AS inscriptos
FROM inscripcion_alumno_comision
GROUP BY id_comision
HAVING COUNT(*) > 25;"""),
            dict(titulo="Usando la vista vw_inscriptos_por_comision", sql="""SELECT id_comision, asignatura, cantidad_inscriptos
FROM vw_inscriptos_por_comision
WHERE cantidad_inscriptos > 25;"""),
        ],
        columnas=[["id_comision", "inscriptos"]],
        pistas=[
            "Contá inscripciones por comisión en `inscripcion_alumno_comision`.",
            "El filtro «más de 25» es sobre el conteo → `HAVING`.",
            "`SELECT id_comision, COUNT(*) FROM inscripcion_alumno_comision GROUP BY id_comision HAVING COUNT(*) > 25`.",
        ],
        explicacion="""Es el patrón más directo de la sección: **contar por grupo y filtrar el grupo**.

```sql
GROUP BY c.id_comision   -- una fila por comisión
HAVING COUNT(*) > 25     -- solo las que superan el umbral
```

`COUNT(*)` cuenta alumnos porque `(id_alumno, id_comision)` es UNIQUE: no hay alumnos repetidos en una comisión.

**Sobre el umbral:** con 30 el resultado es una sola comisión (32 inscriptos), así que bajamos a 25 para que se note la diferencia entre `>` y `>=` (con `>= 25` salen 17 en vez de 9). En el parcialito usá el número del enunciado.

**Para pensar:** «superar su capacidad operativa» también podría medirse contra el `cupo` de cada comisión: `HAVING COUNT(*) > c.cupo` (y agregar `c.cupo` al `GROUP BY`). No es lo que pide este enunciado, pero es un buen ejercicio.""",
        errores_comunes=[
            "Usar `>= 25` cuando dice «más de».",
            "Agrupar por asignatura: el pedido es por **comisión** (una asignatura tiene varias).",
            "Excluir las bajas cuando el pedido no lo dice (con estos datos no queda ninguna comisión).",
        ],
        trampas=[
            dict(titulo=">= 25 en vez de > 25", sql="""SELECT id_comision, COUNT(*) AS inscriptos
FROM inscripcion_alumno_comision
GROUP BY id_comision
HAVING COUNT(*) >= 25;"""),
            dict(titulo="Agrupar por asignatura", sql="""SELECT a.id_asignatura, a.nombre AS asignatura, COUNT(*) AS inscriptos
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > 25;"""),
            dict(titulo="Excluyendo bajas (no lo pide)", sql="""SELECT id_comision, COUNT(*) AS inscriptos
FROM inscripcion_alumno_comision
WHERE estado <> 'Baja'
GROUP BY id_comision
HAVING COUNT(*) > 25;"""),
        ],
        tags=["GROUP BY", "HAVING", "COUNT", "umbral"],
    ),
    dict(
        id="dom-09",
        origen="TP1 · Sección 2 · Ej. 9",
        titulo="Carreras con baja demanda",
        dificultad=3,
        tipo="select",
        enunciado="La universidad está evaluando cerrar o reestructurar carreras con baja demanda. Para esto, necesitan "
                  "identificar aquellas carreras que tengan menos de 15 alumnos activos. Este análisis es clave para la "
                  "toma de decisiones estratégicas.\n\n"
                  "*Aclaración:* «alumno activo» = inscripción a la carrera con `estado = 'activa'` en `alumno_carrera`. "
                  "Con estos datos solo una carrera tiene menos de 15, así que **usá menos de 20**. Mostrá la carrera "
                  "(id o nombre) y la cantidad de alumnos activos.",
        solucion="""SELECT ca.id_carrera, ca.nombre, COUNT(ac.id_alumno) AS activos
FROM carreras ca
LEFT JOIN alumno_carrera ac
       ON ac.id_carrera = ca.id_carrera
      AND ac.estado = 'activa'
GROUP BY ca.id_carrera, ca.nombre
HAVING COUNT(ac.id_alumno) < 20;""",
        alternativas=[
            dict(titulo="Conteo condicional con COUNT(CASE WHEN …)", sql="""SELECT ca.id_carrera, ca.nombre,
       COUNT(CASE WHEN ac.estado = 'activa' THEN 1 END) AS activos
FROM carreras ca
LEFT JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
GROUP BY ca.id_carrera, ca.nombre
HAVING COUNT(CASE WHEN ac.estado = 'activa' THEN 1 END) < 20;"""),
            dict(titulo="Con SUM(condición) y COALESCE", sql="""SELECT ca.id_carrera, ca.nombre,
       COALESCE(SUM(ac.estado = 'activa'), 0) AS activos
FROM carreras ca
LEFT JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
GROUP BY ca.id_carrera, ca.nombre
HAVING COALESCE(SUM(ac.estado = 'activa'), 0) < 20;"""),
        ],
        columnas=[["id_carrera", "activos"], ["nombre", "activos"]],
        casos_borde=True,
        pistas=[
            "Contá, por carrera, las filas de `alumno_carrera` con `estado = 'activa'`.",
            "¿Qué pasa con una carrera que tiene **0** alumnos activos? Tiene «menos de 20», pero un `JOIN` común (o un `WHERE estado = 'activa'`) la hace desaparecer.",
            "`LEFT JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera AND ac.estado = 'activa'` + `HAVING COUNT(ac.id_alumno) < 20`.",
        ],
        explicacion="""Con umbrales **«menos de»** hay que pensar en el **cero**: una carrera sin alumnos activos es justo la más urgente de revisar, y un `JOIN` común la descarta porque no tiene filas que unir.

Por eso: `LEFT JOIN` + contar una columna de la derecha (`COUNT(ac.id_alumno)` da 0 si no hubo match).

**¿Por qué la condición de estado va en el `ON` y no en el `WHERE`?** El `WHERE` se aplica después del JOIN: las filas «rellenadas» con NULL tienen `ac.estado = NULL`, no pasan `estado = 'activa'` y desaparecen. El LEFT JOIN se vuelve, en la práctica, un INNER JOIN. En el `ON`, la condición solo decide qué filas de `alumno_carrera` se unen; la carrera queda igual.

Alternativas sin filtrar en el ON: `COUNT(CASE WHEN ac.estado = 'activa' THEN 1 END)`, o `SUM(ac.estado = 'activa')` con `COALESCE(..., 0)` (sin filas, `SUM` da NULL, y `NULL < 20` no es verdadero).

El corrector lo prueba con casos borde: dos carreras nuevas sin alumnos.""",
        errores_comunes=[
            "Usar `JOIN` (o `LEFT JOIN` con `WHERE ac.estado = 'activa'`): se pierden las carreras con 0 activos.",
            "`LEFT JOIN` con `COUNT(*)`: una carrera sin activos cuenta 1.",
            "`SUM(condición)` sin `COALESCE`: para una carrera sin filas da NULL y el HAVING la descarta.",
        ],
        trampas=[
            dict(titulo="LEFT JOIN con el filtro en el WHERE (se vuelve INNER)", sql="""SELECT ca.id_carrera, ca.nombre, COUNT(ac.id_alumno) AS activos
FROM carreras ca
LEFT JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
WHERE ac.estado = 'activa'
GROUP BY ca.id_carrera, ca.nombre
HAVING COUNT(ac.id_alumno) < 20;"""),
            dict(titulo="LEFT JOIN con COUNT(*)", sql="""SELECT ca.id_carrera, ca.nombre, COUNT(*) AS activos
FROM carreras ca
LEFT JOIN alumno_carrera ac
       ON ac.id_carrera = ca.id_carrera
      AND ac.estado = 'activa'
GROUP BY ca.id_carrera, ca.nombre
HAVING COUNT(*) < 20;"""),
            dict(titulo="SUM(condición) sin COALESCE", sql="""SELECT ca.id_carrera, ca.nombre, SUM(ac.estado = 'activa') AS activos
FROM carreras ca
LEFT JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
GROUP BY ca.id_carrera, ca.nombre
HAVING SUM(ac.estado = 'activa') < 20;"""),
        ],
        tags=["LEFT JOIN", "GROUP BY", "HAVING", "umbral", "casos borde"],
    ),
    dict(
        id="dom-10",
        origen="TP1 · Sección 2 · Ej. 10",
        titulo="Mesas finales con alta concurrencia",
        dificultad=2,
        tipo="select",
        enunciado="Desde la secretaría académica necesitan detectar las próximas mesas de examen final con alta "
                  "concurrencia. Se considera que una mesa tiene alta concurrencia cuando posee más de 15 alumnos "
                  "inscriptos. Esta información permitirá mejorar la organización logística de los exámenes.\n\n"
                  "*Aclaración:* en la base todas las mesas ya pasaron (la última es de junio de 2026), así que "
                  "«próximas» con `CURDATE()` daría vacío: tomá las mesas con fecha **desde el 2026-01-01**. "
                  "Contá todas las inscripciones de cada mesa y mostrá la mesa (id) y la cantidad de inscriptos.",
        solucion="""SELECT m.id_mesa, a.nombre AS asignatura, m.fecha, COUNT(*) AS inscriptos
FROM mesas_finales m
JOIN asignaturas a ON a.id_asignatura = m.id_asignatura
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
WHERE m.fecha >= '2026-01-01'
GROUP BY m.id_mesa, a.nombre, m.fecha
HAVING COUNT(*) > 15;""",
        alternativas=[
            dict(titulo="Sin JOIN con asignaturas (solo el id)", sql="""SELECT m.id_mesa, COUNT(*) AS inscriptos
FROM mesas_finales m
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
WHERE m.fecha >= '2026-01-01'
GROUP BY m.id_mesa
HAVING COUNT(*) > 15;"""),
        ],
        columnas=[["id_mesa", "inscriptos"], ["asignatura", "fecha", "inscriptos"]],
        pistas=[
            "Las inscripciones a cada mesa están en `inscripciones_finales` (`id_mesa`).",
            "«Próximas» es un filtro sobre la **fecha de la mesa** (fila) → `WHERE`. «Más de 15 inscriptos» es sobre el grupo → `HAVING`.",
            "`... WHERE m.fecha >= '2026-01-01' GROUP BY m.id_mesa HAVING COUNT(*) > 15`.",
        ],
        explicacion="""**Traducción:**

- *Qué se lista:* mesas finales → `GROUP BY m.id_mesa`.
- *Filtro de filas:* «próximas» → condición sobre `m.fecha` en el `WHERE`.
- *Métrica:* inscriptos = filas de `inscripciones_finales` de la mesa.
- *Umbral:* `HAVING COUNT(*) > 15`.

**Sobre las fechas:** en la vida real escribirías `WHERE m.fecha >= CURDATE()`. Pero acá todas las mesas son anteriores a hoy (2026-10-15) y daría vacío, por eso fijamos una fecha de corte. Siempre que el resultado dependa del día, conviene probar con una fecha fija.

Si olvidás el filtro de fecha, salen 46 mesas (todas las de la historia) en vez de 10. Si usás `>= 15`, salen 18.

Si mostrás la asignatura y la fecha, agregalas al `GROUP BY` (`ONLY_FULL_GROUP_BY`).""",
        errores_comunes=[
            "Usar `CURDATE()` con estos datos: todas las mesas son pasadas y el resultado queda vacío.",
            "Olvidar el filtro de fecha (cuenta mesas de toda la historia).",
            "Usar `>= 15` cuando dice «más de 15».",
        ],
        trampas=[
            dict(titulo="Con CURDATE() (vacío)", sql="""SELECT m.id_mesa, COUNT(*) AS inscriptos
FROM mesas_finales m
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
WHERE m.fecha >= CURDATE()
GROUP BY m.id_mesa
HAVING COUNT(*) > 15;"""),
            dict(titulo="Sin filtro de fecha", sql="""SELECT m.id_mesa, COUNT(*) AS inscriptos
FROM mesas_finales m
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
GROUP BY m.id_mesa
HAVING COUNT(*) > 15;"""),
            dict(titulo=">= 15 en vez de > 15", sql="""SELECT m.id_mesa, COUNT(*) AS inscriptos
FROM mesas_finales m
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
WHERE m.fecha >= '2026-01-01'
GROUP BY m.id_mesa
HAVING COUNT(*) >= 15;"""),
        ],
        tags=["JOIN", "WHERE", "GROUP BY", "HAVING", "fechas", "umbral"],
    ),

    # ------------------------------------------------------------------
    # Variantes nuevas
    # ------------------------------------------------------------------
    dict(
        id="dom-n01",
        origen="Variante",
        titulo="Carreras con más graduados que abandonos",
        dificultad=2,
        tipo="select",
        enunciado="La secretaría de asuntos estudiantiles quiere saber en qué carreras la cantidad de **graduados** "
                  "supera a la cantidad de **abandonos** (según el estado en `alumno_carrera`), para tomarlas como "
                  "modelo en un programa de retención. Mostrá la carrera (id o nombre), la cantidad de graduados y la "
                  "de abandonos.",
        solucion="""SELECT ca.id_carrera, ca.nombre,
       SUM(ac.estado = 'graduado') AS graduados,
       SUM(ac.estado = 'abandonado') AS abandonos
FROM carreras ca
JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
GROUP BY ca.id_carrera, ca.nombre
HAVING SUM(ac.estado = 'graduado') > SUM(ac.estado = 'abandonado');""",
        alternativas=[
            dict(titulo="Con CASE WHEN y alias en el HAVING", sql="""SELECT ca.id_carrera, ca.nombre,
       SUM(CASE WHEN ac.estado = 'graduado' THEN 1 ELSE 0 END) AS graduados,
       SUM(CASE WHEN ac.estado = 'abandonado' THEN 1 ELSE 0 END) AS abandonos
FROM carreras ca
JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
GROUP BY ca.id_carrera, ca.nombre
HAVING graduados > abandonos;"""),
        ],
        columnas=[["id_carrera", "graduados", "abandonos"], ["nombre", "graduados", "abandonos"]],
        pistas=[
            "Necesitás dos conteos condicionales por carrera: uno de `estado = 'graduado'` y otro de `estado = 'abandonado'`.",
            "No sirve filtrar con `WHERE estado = 'graduado'`: perdés los abandonos. Contá con `SUM(condición)`.",
            "`... GROUP BY ca.id_carrera, ca.nombre HAVING SUM(ac.estado = 'graduado') > SUM(ac.estado = 'abandonado')`.",
        ],
        explicacion="""Acá el umbral no es un número fijo: se **comparan dos agregados del mismo grupo**.

```sql
SUM(ac.estado = 'graduado')    -- graduados de la carrera
SUM(ac.estado = 'abandonado')  -- abandonos de la carrera
HAVING graduados > abandonos
```

No podés usar `WHERE` para separar estados, porque necesitás **los dos** conteos en la misma fila. La solución es el conteo condicional: la comparación vale 1 o 0 y `SUM` la acumula.

En MySQL podés usar los alias del SELECT en el `HAVING` (`HAVING graduados > abandonos`); en otros motores hay que repetir la expresión.

Cuidado con `COUNT(ac.estado = 'graduado')`: `COUNT` cuenta valores no NULL, y 0 no es NULL, así que da el total de filas en los dos lados y nunca uno supera al otro.""",
        errores_comunes=[
            "`COUNT(condición)` en vez de `SUM(condición)`: cuenta todas las filas.",
            "Usar `>=` (incluye carreras con empate, que no «superan»).",
        ],
        trampas=[
            dict(titulo="COUNT(condición) en vez de SUM", sql="""SELECT ca.id_carrera, ca.nombre,
       COUNT(ac.estado = 'graduado') AS graduados,
       COUNT(ac.estado = 'abandonado') AS abandonos
FROM carreras ca
JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
GROUP BY ca.id_carrera, ca.nombre
HAVING COUNT(ac.estado = 'graduado') > COUNT(ac.estado = 'abandonado');"""),
            dict(titulo=">= (incluye empates)", sql="""SELECT ca.id_carrera, ca.nombre,
       SUM(ac.estado = 'graduado') AS graduados,
       SUM(ac.estado = 'abandonado') AS abandonos
FROM carreras ca
JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
GROUP BY ca.id_carrera, ca.nombre
HAVING SUM(ac.estado = 'graduado') >= SUM(ac.estado = 'abandonado');"""),
        ],
        tags=["GROUP BY", "HAVING", "SUM", "conteo condicional"],
    ),
    dict(
        id="dom-n02",
        origen="Variante",
        titulo="Docentes dispersos en muchas materias",
        dificultad=2,
        tipo="select",
        enunciado="La secretaría académica sospecha que algunos docentes están repartidos en **demasiadas materias "
                  "distintas**, lo que dificulta preparar bien las clases. Quieren identificar a los docentes que, "
                  "considerando todas sus comisiones (de cualquier año), dictan o dictaron **más de 8 asignaturas "
                  "distintas**. Mostrá el docente (id o nombre y apellido) y la cantidad de asignaturas.",
        solucion="""SELECT d.id_docente, d.nombre, d.apellido, COUNT(DISTINCT c.id_asignatura) AS asignaturas
FROM docentes d
JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY d.id_docente, d.nombre, d.apellido
HAVING COUNT(DISTINCT c.id_asignatura) > 8;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id del docente)", sql="""SELECT id_docente, COUNT(DISTINCT id_asignatura) AS asignaturas
FROM comisiones
GROUP BY id_docente
HAVING COUNT(DISTINCT id_asignatura) > 8;"""),
        ],
        columnas=[["id_docente", "asignaturas"], ["nombre", "apellido", "asignaturas"]],
        pistas=[
            "Cada comisión tiene un docente y una asignatura. Un docente puede tener varias comisiones **de la misma** asignatura (teórica y práctica, distintos años).",
            "Si contás filas, contás comisiones. Lo pedido son asignaturas **distintas**.",
            "`... GROUP BY d.id_docente, d.nombre, d.apellido HAVING COUNT(DISTINCT c.id_asignatura) > 8`.",
        ],
        explicacion="""La clave está en la palabra **distintas**. En `comisiones` un docente aparece una vez por comisión, y varias de sus comisiones pueden ser de la misma asignatura (otro año, teórica y práctica).

| expresión | qué mide por docente |
|---|---|
| `COUNT(*)` | comisiones |
| `COUNT(DISTINCT c.id_asignatura)` | asignaturas distintas ✔ |

Con `COUNT(*) > 8` aparecen docentes con muchas comisiones pero pocas materias, que no son el problema que se quiere detectar.

`COUNT(DISTINCT ...)` también se puede usar en el `HAVING`: el filtro se hace sobre el mismo valor que mostrás.

Agrupá por `id_docente` (hay docentes homónimos).""",
        errores_comunes=[
            "`COUNT(*)`: cuenta comisiones, no asignaturas distintas.",
            "Agrupar solo por nombre y apellido: junta docentes homónimos.",
        ],
        trampas=[
            dict(titulo="COUNT(*) (cuenta comisiones)", sql="""SELECT d.id_docente, d.nombre, d.apellido, COUNT(*) AS asignaturas
FROM docentes d
JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY d.id_docente, d.nombre, d.apellido
HAVING COUNT(*) > 8;"""),
            dict(titulo="Agrupar por nombre y apellido (junta homónimos)", sql="""SELECT d.nombre, d.apellido, COUNT(DISTINCT c.id_asignatura) AS asignaturas
FROM docentes d
JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY d.nombre, d.apellido
HAVING COUNT(DISTINCT c.id_asignatura) > 8;"""),
        ],
        tags=["GROUP BY", "HAVING", "COUNT DISTINCT", "umbral"],
    ),
    dict(
        id="dom-n03",
        origen="Variante",
        titulo="Cuadro de honor",
        dificultad=2,
        tipo="select",
        enunciado="Bienestar estudiantil quiere armar un **cuadro de honor** con los alumnos de mejor rendimiento en "
                  "parciales: los que tienen un **promedio de notas igual o superior a 6** y que además rindieron "
                  "**al menos 60 exámenes** (para que un buen promedio con pocas notas no alcance). Mostrá el alumno "
                  "(id o nombre y apellido), su promedio y la cantidad de exámenes.\n\n"
                  "*Nota:* los datos de práctica son aleatorios y los promedios son bajos; en la vida real el umbral sería mayor (por ejemplo 8).",
        solucion="""SELECT al.id_alumno, al.nombre, al.apellido,
       ROUND(AVG(n.nota), 2) AS promedio,
       COUNT(*) AS examenes
FROM alumnos al
JOIN notas n ON n.id_alumno = al.id_alumno
GROUP BY al.id_alumno, al.nombre, al.apellido
HAVING AVG(n.nota) >= 6
   AND COUNT(*) >= 60;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id del alumno)", sql="""SELECT id_alumno, AVG(nota) AS promedio, COUNT(*) AS examenes
FROM notas
GROUP BY id_alumno
HAVING AVG(nota) >= 6
   AND COUNT(*) >= 60;"""),
        ],
        columnas=[["id_alumno", "promedio", "examenes"], ["nombre", "apellido", "promedio", "examenes"]],
        pistas=[
            "Cada fila de `notas` es un examen rendido por un alumno: agrupá por alumno.",
            "Las dos condiciones son sobre el grupo (promedio y cantidad), así que las dos van en el `HAVING`.",
            "`... GROUP BY al.id_alumno, al.nombre, al.apellido HAVING AVG(n.nota) >= 6 AND COUNT(*) >= 60`.",
        ],
        explicacion="""El `HAVING` admite **varias condiciones** combinadas con `AND` / `OR`, igual que el `WHERE`:

```sql
HAVING AVG(n.nota) >= 6     -- buen promedio
   AND COUNT(*) >= 60       -- con suficientes exámenes
```

Las dos son propiedades del **grupo** (del alumno), no de cada nota. Si filtrás `WHERE n.nota >= 6`, descartás las notas bajas antes de promediar y casi todos los alumnos «tienen promedio 6 o más».

Fijate en las palabras: «igual o superior» es `>=`, y «al menos 60» también es `>=` (con `> 60` quedan 15 alumnos en vez de 19). Y si unís las condiciones con `OR` en vez de `AND`, alcanza con cumplir una sola y el cuadro se llena de alumnos.""",
        errores_comunes=[
            "Olvidar la condición de cantidad mínima de exámenes.",
            "Unir las condiciones con `OR` en vez de `AND`.",
            "Usar `> 60` cuando dice «al menos 60».",
        ],
        trampas=[
            dict(titulo="Sin mínimo de exámenes", sql="""SELECT al.id_alumno, al.nombre, al.apellido, ROUND(AVG(n.nota), 2) AS promedio, COUNT(*) AS examenes
FROM alumnos al
JOIN notas n ON n.id_alumno = al.id_alumno
GROUP BY al.id_alumno, al.nombre, al.apellido
HAVING AVG(n.nota) >= 6;"""),
            dict(titulo="OR en vez de AND", sql="""SELECT al.id_alumno, al.nombre, al.apellido, ROUND(AVG(n.nota), 2) AS promedio, COUNT(*) AS examenes
FROM alumnos al
JOIN notas n ON n.id_alumno = al.id_alumno
GROUP BY al.id_alumno, al.nombre, al.apellido
HAVING AVG(n.nota) >= 6 OR COUNT(*) >= 60;"""),
            dict(titulo="> 60 en vez de >= 60", sql="""SELECT al.id_alumno, al.nombre, al.apellido, ROUND(AVG(n.nota), 2) AS promedio, COUNT(*) AS examenes
FROM alumnos al
JOIN notas n ON n.id_alumno = al.id_alumno
GROUP BY al.id_alumno, al.nombre, al.apellido
HAVING AVG(n.nota) >= 6 AND COUNT(*) > 60;"""),
        ],
        tags=["GROUP BY", "HAVING", "AVG", "AND", "umbral"],
    ),
    dict(
        id="dom-n04",
        origen="Variante",
        titulo="Comisiones con baja asistencia",
        dificultad=3,
        tipo="select",
        enunciado="El equipo de seguimiento estudiantil quiere detectar **comisiones con baja asistencia** para hablar "
                  "con los docentes a cargo. Se considera baja asistencia cuando el **porcentaje de presentes** (sobre "
                  "el total de registros de asistencia de la comisión) es **menor al 75 %**. Mostrá el id de la comisión "
                  "y su porcentaje de asistencia (de 0 a 100).",
        solucion="""SELECT asi.id_comision,
       ROUND(SUM(asi.presente = 1) * 100 / COUNT(*), 2) AS porcentaje
FROM asistencias asi
GROUP BY asi.id_comision
HAVING SUM(asi.presente = 1) * 100 / COUNT(*) < 75;""",
        alternativas=[
            dict(titulo="Con AVG(presente)", sql="""SELECT asi.id_comision, ROUND(AVG(asi.presente) * 100, 2) AS porcentaje
FROM asistencias asi
GROUP BY asi.id_comision
HAVING AVG(asi.presente) * 100 < 75;"""),
            dict(titulo="Mostrando el docente a cargo", sql="""SELECT c.id_comision, d.nombre, d.apellido,
       ROUND(SUM(asi.presente = 1) * 100 / COUNT(*), 2) AS porcentaje
FROM comisiones c
JOIN docentes d ON d.id_docente = c.id_docente
JOIN asistencias asi ON asi.id_comision = c.id_comision
GROUP BY c.id_comision, d.nombre, d.apellido
HAVING SUM(asi.presente = 1) * 100 / COUNT(*) < 75;"""),
        ],
        columnas=[["id_comision", "porcentaje"]],
        pistas=[
            "Primero armá el porcentaje por comisión: presentes × 100 / total de registros.",
            "Los presentes se cuentan con `SUM(presente = 1)` (o `SUM(presente)`); el total con `COUNT(*)`. Como `presente` vale 0/1, `AVG(presente)` ya es la proporción.",
            "`... GROUP BY asi.id_comision HAVING SUM(asi.presente = 1) * 100 / COUNT(*) < 75`.",
        ],
        explicacion="""El umbral es sobre un **porcentaje**, que es un cociente de agregados. Primero se arma la métrica y después se filtra en el `HAVING`:

```sql
SUM(asi.presente = 1) * 100 / COUNT(*)   -- % de presentes de la comisión
HAVING ... < 75
```

Equivalente y más corto: `AVG(asi.presente) * 100`, porque el promedio de una columna 0/1 es la proporción de unos.

Detalles que el corrector distingue:
- «Menor al 75 %» es `<`: hay comisiones con **exactamente** 75,00 % que con `<=` aparecerían (23 en vez de 19).
- `COUNT(presente = 1)` cuenta todas las filas: el porcentaje da 100 % y no aparece nada.
- Calcular el % de **ausencias** e invertir el sentido sin darse cuenta es otro clásico.

Redondear para mostrar está bien; para filtrar, conviene comparar el valor sin redondear.""",
        errores_comunes=[
            "Usar `<= 75` cuando dice «menor al 75 %».",
            "`COUNT(presente = 1)` en el numerador: siempre da 100 %.",
            "Calcular el porcentaje de ausencias en lugar del de asistencia.",
        ],
        trampas=[
            dict(titulo="<= 75 en vez de < 75", sql="""SELECT asi.id_comision, ROUND(AVG(asi.presente) * 100, 2) AS porcentaje
FROM asistencias asi
GROUP BY asi.id_comision
HAVING AVG(asi.presente) * 100 <= 75;"""),
            dict(titulo="COUNT(condición) en el numerador", sql="""SELECT asi.id_comision, ROUND(COUNT(asi.presente = 1) * 100 / COUNT(*), 2) AS porcentaje
FROM asistencias asi
GROUP BY asi.id_comision
HAVING COUNT(asi.presente = 1) * 100 / COUNT(*) < 75;"""),
            dict(titulo="Porcentaje de ausencias", sql="""SELECT asi.id_comision, ROUND(SUM(asi.presente = 0) * 100 / COUNT(*), 2) AS porcentaje
FROM asistencias asi
GROUP BY asi.id_comision
HAVING SUM(asi.presente = 0) * 100 / COUNT(*) < 75;"""),
        ],
        tags=["GROUP BY", "HAVING", "porcentaje", "AVG", "umbral"],
    ),
    dict(
        id="dom-n05",
        origen="Variante",
        titulo="Mesas de 2025 con más ausentes",
        dificultad=3,
        tipo="select",
        enunciado="La secretaría académica quiere revisar las mesas de examen final de **2025** en las que hubo **más "
                  "ausentes que presentes**, para analizar si conviene cambiar las fechas. En `inscripciones_finales`, "
                  "un alumno es **ausente** si su estado es `'ausente'`, y se considera **presente** si su estado es "
                  "`'presente'`, `'aprobado'` o `'desaprobado'` (los que rindieron). Mostrá el id de la mesa, la "
                  "cantidad de ausentes y la de presentes.",
        solucion="""SELECT m.id_mesa,
       SUM(inf.estado = 'ausente') AS ausentes,
       SUM(inf.estado IN ('presente', 'aprobado', 'desaprobado')) AS presentes
FROM mesas_finales m
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
WHERE m.fecha BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY m.id_mesa
HAVING SUM(inf.estado = 'ausente') > SUM(inf.estado IN ('presente', 'aprobado', 'desaprobado'));""",
        alternativas=[
            dict(titulo="Con YEAR(), CASE WHEN y alias en el HAVING", sql="""SELECT m.id_mesa,
       SUM(CASE WHEN inf.estado = 'ausente' THEN 1 ELSE 0 END) AS ausentes,
       SUM(CASE WHEN inf.estado IN ('presente', 'aprobado', 'desaprobado') THEN 1 ELSE 0 END) AS presentes
FROM mesas_finales m
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
WHERE YEAR(m.fecha) = 2025
GROUP BY m.id_mesa
HAVING ausentes > presentes;"""),
        ],
        columnas=[["id_mesa", "ausentes", "presentes"]],
        pistas=[
            "El año es un filtro sobre la fecha de la mesa (`WHERE`). La comparación ausentes vs presentes es sobre el grupo (`HAVING`).",
            "Contá cada categoría con un conteo condicional: `SUM(estado = 'ausente')` y `SUM(estado IN (...))`.",
            "`... WHERE m.fecha BETWEEN '2025-01-01' AND '2025-12-31' GROUP BY m.id_mesa HAVING SUM(inf.estado = 'ausente') > SUM(inf.estado IN ('presente','aprobado','desaprobado'))`.",
        ],
        explicacion="""Este pedido combina todo lo de la sección:

1. **Filtro de filas** (`WHERE`): mesas de 2025. `BETWEEN '2025-01-01' AND '2025-12-31'` o `YEAR(m.fecha) = 2025`.
2. **Agrupación**: una fila por mesa.
3. **Dos conteos condicionales** en el mismo grupo: `SUM(inf.estado = 'ausente')` y `SUM(inf.estado IN ('presente','aprobado','desaprobado'))`.
4. **Comparación entre agregados** (`HAVING`): ausentes > presentes.

**El detalle de dominio:** «presente» no es solo el estado `'presente'`. Quien aprobó o desaprobó también se presentó. Si contás solo `'presente'`, subestimás los presentes y aparecen muchísimas mesas de más (379 en vez de 55).

`IN (...)` dentro del `SUM` funciona igual que cualquier otra condición: vale 1 o 0 por fila.""",
        errores_comunes=[
            "Contar como presentes solo el estado `'presente'` (los aprobados y desaprobados también rindieron).",
            "`COUNT(condición)` en vez de `SUM(condición)`.",
            "Olvidar el filtro de año.",
        ],
        trampas=[
            dict(titulo="Presentes = solo estado 'presente'", sql="""SELECT m.id_mesa,
       SUM(inf.estado = 'ausente') AS ausentes,
       SUM(inf.estado = 'presente') AS presentes
FROM mesas_finales m
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
WHERE m.fecha BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY m.id_mesa
HAVING SUM(inf.estado = 'ausente') > SUM(inf.estado = 'presente');"""),
            dict(titulo="COUNT(condición) en vez de SUM", sql="""SELECT m.id_mesa,
       COUNT(inf.estado = 'ausente') AS ausentes,
       COUNT(inf.estado IN ('presente', 'aprobado', 'desaprobado')) AS presentes
FROM mesas_finales m
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
WHERE m.fecha BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY m.id_mesa
HAVING COUNT(inf.estado = 'ausente') > COUNT(inf.estado IN ('presente', 'aprobado', 'desaprobado'));"""),
            dict(titulo="Sin filtro de año", sql="""SELECT m.id_mesa,
       SUM(inf.estado = 'ausente') AS ausentes,
       SUM(inf.estado IN ('presente', 'aprobado', 'desaprobado')) AS presentes
FROM mesas_finales m
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
GROUP BY m.id_mesa
HAVING SUM(inf.estado = 'ausente') > SUM(inf.estado IN ('presente', 'aprobado', 'desaprobado'));"""),
        ],
        tags=["WHERE", "GROUP BY", "HAVING", "conteo condicional", "IN"],
    ),
    dict(
        id="dom-n06",
        origen="Semana 10 · Ej. 29 (Actividad IA)",
        titulo="Materias que «andan mal» (Actividad IA)",
        dificultad=3,
        tipo="select",
        enunciado="Un directivo te manda este pedido: «*Quiero ver las materias que andan mal en rendimiento.*»\n\n"
                  "Así no se puede programar: ¿qué es «andar mal»?, ¿medido cómo?, ¿con cuántos datos alcanza? "
                  "Después de hablar con el área, el requerimiento quedó así:\n\n"
                  "> Listar las **asignaturas** que tengan **al menos 30 notas** registradas y que cumplan **alguna** de "
                  "estas condiciones: su **promedio** de notas es **menor a 5**, o **más del 40 %** de sus notas son "
                  "desaprobadas (nota menor a 4).\n\n"
                  "Mostrá la asignatura (id o nombre). Para justificar el informe podés agregar la cantidad de notas, "
                  "el promedio y el porcentaje de desaprobadas.",
        solucion="""SELECT a.id_asignatura, a.nombre,
       COUNT(*) AS notas,
       ROUND(AVG(n.nota), 2) AS promedio,
       ROUND(SUM(n.nota < 4) * 100 / COUNT(*), 2) AS porc_desaprobadas
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) >= 30
   AND (AVG(n.nota) < 5 OR SUM(n.nota < 4) * 100 / COUNT(*) > 40);""",
        alternativas=[
            dict(titulo="Usando la vista vw_notas_por_asignatura", sql="""SELECT id_asignatura, asignatura, cantidad_notas, promedio,
       ROUND(desaprobados * 100 / cantidad_notas, 2) AS porc_desaprobadas
FROM vw_notas_por_asignatura
WHERE cantidad_notas >= 30
  AND (promedio < 5 OR desaprobados * 100 / cantidad_notas > 40);"""),
        ],
        columnas=[["id_asignatura"], ["nombre"]],
        pistas=[
            "Traducí cada parte: «materia» = asignatura (agrupás por ella); «rendimiento» = sus notas (`asignaturas → comisiones → examenes → notas`).",
            "Las tres condiciones son sobre el grupo: `COUNT(*)`, `AVG(nota)` y el porcentaje `SUM(nota < 4) * 100 / COUNT(*)`. Van todas en el `HAVING`.",
            "Ojo con la precedencia: `AND` se evalúa antes que `OR`. Escribí `HAVING COUNT(*) >= 30 AND (AVG(n.nota) < 5 OR ... > 40)`.",
        ],
        explicacion="""**De un pedido vago a uno técnico.** «Las materias que andan mal» no se puede programar hasta definir:

1. **Entidad:** ¿materia = asignatura o comisión? → asignatura.
2. **Métrica:** ¿rendimiento = notas de parciales, finales, asistencia? → notas de `notas`.
3. **Criterio:** ¿qué es «mal»? → promedio < 5 **o** más del 40 % de desaprobadas (dos síntomas distintos).
4. **Representatividad:** una materia con 8 notas no permite concluir nada → mínimo 30 notas.

Recién ahí se escribe la consulta. Todas las condiciones son sobre el **grupo**, así que van en el `HAVING`.

**La trampa de la precedencia:** `AND` tiene más prioridad que `OR`. Sin paréntesis,

```sql
HAVING COUNT(*) >= 30 AND AVG(n.nota) < 5 OR porc > 40
```

se lee `(COUNT >= 30 AND AVG < 5) OR porc > 40`, y se cuelan materias con pocas notas (41 filas en vez de 33).

Este es el tipo de trabajo que conviene hacer antes de pedirle una consulta a una IA: un requerimiento preciso da una consulta verificable.""",
        errores_comunes=[
            "Olvidar los paréntesis al combinar `AND` con `OR`.",
            "Usar `AND` entre los dos síntomas («alguna de estas condiciones» es `OR`).",
            "No exigir una cantidad mínima de notas: aparecen materias con muy pocos datos.",
        ],
        trampas=[
            dict(titulo="Sin paréntesis (AND antes que OR)", sql="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS notas
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) >= 30 AND AVG(n.nota) < 5 OR SUM(n.nota < 4) * 100 / COUNT(*) > 40;"""),
            dict(titulo="AND entre los dos síntomas", sql="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS notas
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) >= 30 AND AVG(n.nota) < 5 AND SUM(n.nota < 4) * 100 / COUNT(*) > 40;"""),
            dict(titulo="Sin mínimo de notas", sql="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS notas
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
JOIN examenes e ON e.id_comision = c.id_comision
JOIN notas n ON n.id_examen = e.id_examen
GROUP BY a.id_asignatura, a.nombre
HAVING AVG(n.nota) < 5 OR SUM(n.nota < 4) * 100 / COUNT(*) > 40;"""),
        ],
        tags=["GROUP BY", "HAVING", "AND/OR", "porcentaje", "requerimientos"],
    ),
]
