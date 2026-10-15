"""Sección: Consultas con varias tablas — INNER JOIN, LEFT JOIN y auto-JOIN (TP1 · Parte B + variantes)."""

EJERCICIOS = [
    # ------------------------------------------------------------------
    # Originales del TP1 · Parte B
    # ------------------------------------------------------------------
    dict(
        id="join-06",
        origen="TP1 · Parte B · Ej. 6",
        titulo="Alumnos con sus carreras",
        dificultad=1,
        tipo="select",
        enunciado="Obtener el nombre y apellido de los alumnos junto con el nombre de las carreras en las que "
                  "están inscriptos.",
        solucion="""SELECT a.nombre, a.apellido, c.nombre AS carrera
FROM alumnos a
JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
JOIN carreras c ON c.id_carrera = ac.id_carrera;""",
        alternativas=[
            dict(titulo="JOIN implícito (coma + WHERE)", sql="""SELECT a.nombre, a.apellido, c.nombre AS carrera
FROM alumnos a, alumno_carrera ac, carreras c
WHERE ac.id_alumno = a.id_alumno
  AND c.id_carrera = ac.id_carrera;"""),
            dict(titulo="Con USING", sql="""SELECT a.nombre, a.apellido, c.nombre AS carrera
FROM alumnos a
JOIN alumno_carrera ac USING (id_alumno)
JOIN carreras c USING (id_carrera);"""),
        ],
        variantes=[
            dict(titulo="Solo inscripciones con estado 'activa'", sql="""SELECT a.nombre, a.apellido, c.nombre AS carrera
FROM alumnos a
JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
JOIN carreras c ON c.id_carrera = ac.id_carrera
WHERE ac.estado = 'activa';"""),
        ],
        pistas=[
            "`alumnos` y `carreras` no se relacionan directamente: la relación está en la tabla intermedia `alumno_carrera`.",
            "Son dos JOIN: `alumnos` → `alumno_carrera` (por `id_alumno`) y `alumno_carrera` → `carreras` (por `id_carrera`).",
            "Las dos tablas tienen una columna `nombre`: calificá con el alias (`a.nombre`, `c.nombre AS carrera`).",
        ],
        explicacion="""Es una relación **muchos a muchos**: un alumno puede estar en varias carreras y una carrera tiene muchos alumnos. Eso se modela con una tabla intermedia (`alumno_carrera`) que tiene las dos claves foráneas.

Para «cruzar» hay que pasar por ella:

```
alumnos ──id_alumno── alumno_carrera ──id_carrera── carreras
```

Cada `JOIN ... ON` une una tabla siguiendo una FK. El resultado tiene **una fila por inscripción** (1737), así que un alumno con dos carreras aparece dos veces: es correcto.

Como `alumnos` y `carreras` tienen columna `nombre`, sin alias MySQL da *Column 'nombre' is ambiguous*.

El enunciado no filtra por estado, así que van todas las inscripciones. Si interpretás «están inscriptos» como «inscripción activa» (`ac.estado = 'activa'`), el corrector también lo acepta.""",
        errores_comunes=[
            "Intentar unir `alumnos` con `carreras` directamente: no hay una columna en común con sentido (no existe `alumnos.id_carrera`).",
            "Unir con la columna equivocada de la intermedia, por ejemplo `c.id_carrera = ac.id` (`id` es la PK de `alumno_carrera`, no la FK).",
            "No calificar `nombre`: error de columna ambigua.",
        ],
        trampas=[
            dict(titulo="Unir por la PK de la intermedia", sql="""SELECT a.nombre, a.apellido, c.nombre AS carrera
FROM alumnos a
JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
JOIN carreras c ON c.id_carrera = ac.id;"""),
            dict(titulo="Saltear la tabla intermedia", sql="""SELECT a.nombre, a.apellido, c.nombre AS carrera
FROM alumnos a
JOIN carreras c ON c.id_carrera = a.id_alumno;"""),
        ],
        tags=["JOIN", "tabla intermedia", "muchos a muchos"],
    ),
    dict(
        id="join-07",
        origen="TP1 · Parte B · Ej. 7",
        titulo="Asignaturas con su departamento",
        dificultad=1,
        tipo="select",
        enunciado="Listar todas las asignaturas junto con el nombre del departamento al que pertenecen.",
        solucion="""SELECT a.id_asignatura, a.nombre AS asignatura, d.nombre AS departamento
FROM asignaturas a
JOIN departamentos d ON d.id_departamento = a.id_departamento;""",
        alternativas=[
            dict(titulo="Con USING", sql="""SELECT a.id_asignatura, a.nombre AS asignatura, d.nombre AS departamento
FROM asignaturas a
JOIN departamentos d USING (id_departamento);"""),
            dict(titulo="LEFT JOIN (conserva asignaturas sin departamento)", sql="""SELECT a.id_asignatura, a.nombre AS asignatura, d.nombre AS departamento
FROM asignaturas a
LEFT JOIN departamentos d ON d.id_departamento = a.id_departamento;"""),
        ],
        columnas=[["id_asignatura", "asignatura", "departamento"], ["asignatura", "departamento"]],
        pistas=[
            "`asignaturas` tiene la FK `id_departamento`.",
            "Un solo JOIN: `asignaturas` con `departamentos`.",
            "`JOIN departamentos d ON d.id_departamento = a.id_departamento`.",
        ],
        explicacion="""Relación **uno a muchos**: cada asignatura pertenece a un departamento (FK `asignaturas.id_departamento`). La condición del JOIN iguala la FK con la PK:

```sql
ON d.id_departamento = a.id_departamento
```

`USING (id_departamento)` es un atajo cuando la columna se llama igual en las dos tablas.

**No uses `NATURAL JOIN`**: une por *todas* las columnas con el mismo nombre, y acá `asignaturas` y `departamentos` comparten `id_departamento` **y** `nombre`. Terminaría pidiendo que la asignatura se llame igual que el departamento → 0 filas.

Como ninguna asignatura tiene `id_departamento` en NULL, `JOIN` y `LEFT JOIN` dan lo mismo. Si existiera alguna sin departamento, solo `LEFT JOIN` la mostraría (con NULL), lo que cumple mejor con «todas las asignaturas».""",
        errores_comunes=[
            "Usar `NATURAL JOIN`: también compara `nombre` con `nombre` y no devuelve nada.",
            "Olvidar la condición del JOIN (`FROM asignaturas, departamentos` sin WHERE): producto cartesiano de 500 × 5 filas.",
            "Unir PK con PK (`a.id_asignatura = d.id_departamento`): no tiene sentido y da 5 filas.",
        ],
        trampas=[
            dict(titulo="NATURAL JOIN", sql="""SELECT a.id_asignatura, a.nombre AS asignatura, d.nombre AS departamento
FROM asignaturas a
NATURAL JOIN departamentos d;"""),
            dict(titulo="Producto cartesiano (sin condición)", sql="""SELECT a.id_asignatura, a.nombre AS asignatura, d.nombre AS departamento
FROM asignaturas a, departamentos d;"""),
            dict(titulo="PK contra PK", sql="""SELECT a.id_asignatura, a.nombre AS asignatura, d.nombre AS departamento
FROM asignaturas a
JOIN departamentos d ON d.id_departamento = a.id_asignatura;"""),
        ],
        tags=["JOIN", "USING", "NATURAL JOIN"],
    ),
    dict(
        id="join-08",
        origen="TP1 · Parte B · Ej. 8",
        titulo="Comisiones con asignatura, docente y aula",
        dificultad=2,
        tipo="select",
        enunciado="Mostrar todas las comisiones junto con el nombre de la asignatura, el docente a cargo y el aula "
                  "donde se dictan. (Del docente mostrá nombre y apellido; del aula, su nombre.)",
        solucion="""SELECT c.id_comision,
       a.nombre   AS asignatura,
       d.nombre   AS nombre_docente,
       d.apellido AS apellido_docente,
       au.nombre  AS aula
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN docentes d    ON d.id_docente = c.id_docente
JOIN aulas au      ON au.id_aula = c.id_aula;""",
        alternativas=[
            dict(titulo="JOIN implícito (coma + WHERE)", sql="""SELECT c.id_comision, a.nombre AS asignatura, d.nombre AS nombre_docente,
       d.apellido AS apellido_docente, au.nombre AS aula
FROM comisiones c, asignaturas a, docentes d, aulas au
WHERE a.id_asignatura = c.id_asignatura
  AND d.id_docente = c.id_docente
  AND au.id_aula = c.id_aula;"""),
        ],
        variantes=[
            dict(titulo="Docente en una sola columna (CONCAT)", sql="""SELECT c.id_comision,
       a.nombre AS asignatura,
       CONCAT(d.nombre, ' ', d.apellido) AS docente,
       au.nombre AS aula
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN docentes d    ON d.id_docente = c.id_docente
JOIN aulas au      ON au.id_aula = c.id_aula;"""),
            dict(titulo="Docente como «Apellido, Nombre» (CONCAT)", sql="""SELECT c.id_comision,
       a.nombre AS asignatura,
       CONCAT(d.apellido, ', ', d.nombre) AS docente,
       au.nombre AS aula
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN docentes d    ON d.id_docente = c.id_docente
JOIN aulas au      ON au.id_aula = c.id_aula;"""),
        ],
        columnas=[
            ["id_comision", "asignatura", "nombre_docente", "apellido_docente", "aula"],
            ["asignatura", "nombre_docente", "apellido_docente", "aula"],
            # para la variante con CONCAT
            ["id_comision", "asignatura", "docente", "aula"],
            ["asignatura", "docente", "aula"],
        ],
        pistas=[
            "`comisiones` tiene tres FK: `id_asignatura`, `id_docente` e `id_aula`.",
            "Partí de `comisiones` y hacé un JOIN por cada FK (tres JOIN).",
            "Las tres tablas tienen `nombre`: usá alias distintos (`AS asignatura`, `AS aula`...).",
        ],
        explicacion="""Cuando una tabla tiene varias FK, se parte de ella y se agrega **un JOIN por cada FK** («estrella»):

```
asignaturas ← comisiones → docentes
                  ↓
                aulas
```

Cada JOIN tiene su propia condición `ON`, siempre **FK = PK**. El resultado conserva una fila por comisión (1200).

`asignaturas`, `docentes` y `aulas` tienen columna `nombre`: hay que calificarlas y conviene renombrarlas para que el resultado se entienda.

«El docente a cargo» es `comisiones.id_docente`. No hace falta pasar por `docente_asignatura` (esa tabla registra asignaciones por cuatrimestre y multiplicaría las filas).

Si mostrás al docente en una sola columna con `CONCAT(d.nombre, ' ', d.apellido)` o `CONCAT(d.apellido, ', ', d.nombre)`, el corrector también lo acepta.""",
        errores_comunes=[
            "Unir por una columna que no corresponde (por ejemplo docentes por `id_departamento`): multiplica las filas.",
            "Olvidar una condición en el JOIN implícito (con comas): esa tabla se cruza con todas las filas.",
            "No renombrar las columnas `nombre`: el resultado tiene tres columnas «nombre» y no se entiende cuál es cuál.",
        ],
        trampas=[
            dict(titulo="Docente unido por departamento", sql="""SELECT c.id_comision, a.nombre AS asignatura, d.nombre AS nombre_docente,
       d.apellido AS apellido_docente, au.nombre AS aula
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN docentes d ON d.id_departamento = a.id_departamento
JOIN aulas au ON au.id_aula = c.id_aula;"""),
            dict(titulo="Falta la condición del aula (coma)", sql="""SELECT c.id_comision, a.nombre AS asignatura, d.nombre AS nombre_docente,
       d.apellido AS apellido_docente, au.nombre AS aula
FROM comisiones c, asignaturas a, docentes d, aulas au
WHERE a.id_asignatura = c.id_asignatura
  AND d.id_docente = c.id_docente;"""),
        ],
        tags=["JOIN", "varias tablas"],
    ),
    dict(
        id="join-09",
        origen="TP1 · Parte B · Ej. 9",
        titulo="Alumnos en estado Regular",
        dificultad=2,
        tipo="select",
        enunciado="Obtener todos los alumnos que se encuentran en estado 'Regular' en alguna comisión. "
                  "(Mostrá id, nombre y apellido del alumno.)",
        solucion="""SELECT DISTINCT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
JOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno
WHERE i.estado = 'Regular';""",
        alternativas=[
            dict(titulo="Con IN (subconsulta)", sql="""SELECT id_alumno, nombre, apellido
FROM alumnos
WHERE id_alumno IN (
    SELECT id_alumno
    FROM inscripcion_alumno_comision
    WHERE estado = 'Regular'
);"""),
            dict(titulo="Con EXISTS", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
WHERE EXISTS (
    SELECT 1
    FROM inscripcion_alumno_comision i
    WHERE i.id_alumno = a.id_alumno
      AND i.estado = 'Regular'
);"""),
        ],
        variantes=[
            dict(titulo="Una fila por inscripción, mostrando la comisión", sql="""SELECT a.id_alumno AS alumno,
       a.nombre    AS nombre_alumno,
       a.apellido  AS apellido_alumno,
       i.id_comision
FROM alumnos a
JOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno
WHERE i.estado = 'Regular';"""),
        ],
        columnas=[
            ["id_alumno", "nombre", "apellido"],
            ["id_alumno"],
            ["nombre", "apellido"],
            # para la variante «una fila por inscripción»: tiene que incluir la comisión
            ["alumno", "id_comision"],
            ["nombre_alumno", "apellido_alumno", "id_comision"],
        ],
        pistas=[
            "El estado de cada alumno en cada comisión está en `inscripcion_alumno_comision`.",
            "Un alumno puede estar Regular en varias comisiones: pensá qué pasa con las filas repetidas.",
            "`SELECT DISTINCT a.id_alumno, a.nombre, a.apellido ... WHERE i.estado = 'Regular'` (o `WHERE id_alumno IN (subconsulta)`).",
        ],
        explicacion="""El JOIN `alumnos` ↔ `inscripcion_alumno_comision` devuelve **una fila por inscripción**. Hay 3486 inscripciones en estado Regular, pero solo 976 alumnos distintos: si no eliminás repetidos, un alumno regular en 5 comisiones aparece 5 veces.

Como se piden **alumnos**, lo natural es una fila por alumno:

- `SELECT DISTINCT` sobre las columnas del alumno, **incluyendo el id**. `DISTINCT a.nombre, a.apellido` juntaría a dos alumnos distintos que se llaman igual (hay muchos homónimos).
- O un `IN`/`EXISTS`: el filtro se hace sobre `alumnos`, así que no se generan repetidos.

Otra lectura válida es listar cada inscripción regular **mostrando la comisión** (`i.id_comision`): ahí las repeticiones tienen sentido y el corrector también la acepta. Lo que no tiene sentido es repetir al alumno sin mostrar en qué comisión.""",
        errores_comunes=[
            "Olvidar `DISTINCT`: el alumno aparece una vez por cada comisión en la que está regular, sin ninguna información que lo justifique.",
            "Hacer `DISTINCT` solo sobre nombre y apellido: se fusionan alumnos distintos con el mismo nombre (de 976 quedan 363).",
            "Escribir el estado distinto a como está en el `ENUM` (por ejemplo `'Regularizado'`).",
        ],
        trampas=[
            dict(titulo="Sin DISTINCT (alumnos repetidos)", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
JOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno
WHERE i.estado = 'Regular';"""),
            dict(titulo="DISTINCT sin el id (junta homónimos)", sql="""SELECT DISTINCT a.nombre, a.apellido
FROM alumnos a
JOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno
WHERE i.estado = 'Regular';"""),
            dict(titulo="Sin filtrar el estado", sql="""SELECT DISTINCT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
JOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno;"""),
        ],
        tags=["JOIN", "DISTINCT", "IN", "EXISTS"],
    ),
    dict(
        id="join-10",
        origen="TP1 · Parte B · Ej. 10",
        titulo="Mesas finales con todos sus datos",
        dificultad=2,
        tipo="select",
        enunciado="Listar todas las mesas finales mostrando la asignatura, el docente, el aula, la fecha y el turno. "
                  "(Mostrá nombres, no ids: nombre de la asignatura, nombre y apellido del docente y nombre del aula.)",
        solucion="""SELECT m.id_mesa,
       a.nombre   AS asignatura,
       d.nombre   AS nombre_docente,
       d.apellido AS apellido_docente,
       au.nombre  AS aula,
       m.fecha,
       m.turno
FROM mesas_finales m
JOIN asignaturas a ON a.id_asignatura = m.id_asignatura
JOIN docentes d    ON d.id_docente = m.id_docente
JOIN aulas au      ON au.id_aula = m.id_aula;""",
        alternativas=[
            dict(titulo="JOIN implícito (coma + WHERE)", sql="""SELECT m.id_mesa, a.nombre AS asignatura, d.nombre AS nombre_docente,
       d.apellido AS apellido_docente, au.nombre AS aula, m.fecha, m.turno
FROM mesas_finales m, asignaturas a, docentes d, aulas au
WHERE a.id_asignatura = m.id_asignatura
  AND d.id_docente = m.id_docente
  AND au.id_aula = m.id_aula;"""),
        ],
        variantes=[
            dict(titulo="Docente en una sola columna (CONCAT)", sql="""SELECT m.id_mesa,
       a.nombre AS asignatura,
       CONCAT(d.nombre, ' ', d.apellido) AS docente,
       au.nombre AS aula,
       m.fecha,
       m.turno
FROM mesas_finales m
JOIN asignaturas a ON a.id_asignatura = m.id_asignatura
JOIN docentes d    ON d.id_docente = m.id_docente
JOIN aulas au      ON au.id_aula = m.id_aula;"""),
            dict(titulo="Docente como «Apellido, Nombre» (CONCAT)", sql="""SELECT m.id_mesa,
       a.nombre AS asignatura,
       CONCAT(d.apellido, ', ', d.nombre) AS docente,
       au.nombre AS aula,
       m.fecha,
       m.turno
FROM mesas_finales m
JOIN asignaturas a ON a.id_asignatura = m.id_asignatura
JOIN docentes d    ON d.id_docente = m.id_docente
JOIN aulas au      ON au.id_aula = m.id_aula;"""),
        ],
        columnas=[
            ["id_mesa", "asignatura", "nombre_docente", "apellido_docente", "aula", "fecha", "turno"],
            ["asignatura", "nombre_docente", "apellido_docente", "aula", "fecha", "turno"],
            # para la variante con CONCAT
            ["id_mesa", "asignatura", "docente", "aula", "fecha", "turno"],
            ["asignatura", "docente", "aula", "fecha", "turno"],
        ],
        pistas=[
            "Mismo esquema que el ejercicio de comisiones: `mesas_finales` tiene FK a asignatura, docente y aula.",
            "Tres JOIN partiendo de `mesas_finales`; `fecha` y `turno` son columnas de la propia mesa.",
            "`JOIN asignaturas a ON a.id_asignatura = m.id_asignatura JOIN docentes d ON ... JOIN aulas au ON ...`.",
        ],
        explicacion="""Es el mismo patrón «estrella» que en comisiones: partís de la tabla que tiene las FK (`mesas_finales`) y sumás un JOIN por cada una.

```sql
FROM mesas_finales m
JOIN asignaturas a ON a.id_asignatura = m.id_asignatura
JOIN docentes d    ON d.id_docente   = m.id_docente
JOIN aulas au      ON au.id_aula     = m.id_aula
```

`fecha` y `turno` ya están en `mesas_finales`, no requieren JOIN.

Si usás la sintaxis con comas (`FROM t1, t2, t3 WHERE ...`), **cada tabla agregada necesita su condición** en el `WHERE`. Si te olvidás una, esa tabla se combina con todas las filas (producto cartesiano): con las 10 aulas, las 2500 mesas se convierten en 25000 filas. Por eso es preferible `JOIN ... ON`: la condición queda pegada a cada tabla y es difícil olvidarla.""",
        errores_comunes=[
            "Olvidar una condición de unión con la sintaxis de comas: producto cartesiano.",
            "Mostrar los ids (`id_docente`, `id_aula`) en lugar de los nombres: el ejercicio pide justamente hacer los JOIN.",
        ],
        trampas=[
            dict(titulo="Falta la condición del aula (coma)", sql="""SELECT m.id_mesa, a.nombre AS asignatura, d.nombre AS nombre_docente,
       d.apellido AS apellido_docente, au.nombre AS aula, m.fecha, m.turno
FROM mesas_finales m, asignaturas a, docentes d, aulas au
WHERE a.id_asignatura = m.id_asignatura
  AND d.id_docente = m.id_docente;"""),
            dict(titulo="Ids en lugar de nombres", sql="""SELECT id_mesa, id_asignatura, id_docente, id_aula, fecha, turno
FROM mesas_finales;"""),
        ],
        tags=["JOIN", "varias tablas", "producto cartesiano"],
    ),

    # ------------------------------------------------------------------
    # Variantes nuevas (de menor a mayor dificultad)
    # ------------------------------------------------------------------
    dict(
        id="join-n01",
        origen="Variante",
        titulo="Comisiones de 2026 en laboratorios",
        dificultad=1,
        tipo="select",
        enunciado="Mostrá el id de la comisión, el nombre de la asignatura y el nombre del aula de las comisiones "
                  "del año **2026** que se dictan en aulas de tipo **'laboratorio'**.",
        solucion="""SELECT c.id_comision, a.nombre AS asignatura, au.nombre AS aula
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN aulas au      ON au.id_aula = c.id_aula
WHERE au.tipo = 'laboratorio'
  AND c.anio = 2026;""",
        columnas=[["id_comision", "asignatura", "aula"], ["id_comision", "aula"]],
        pistas=[
            "El tipo de aula está en `aulas.tipo`, no en `comisiones`.",
            "Uní `comisiones` con `asignaturas` y con `aulas`, y filtrá en el `WHERE` usando columnas de las dos.",
            "Ojo: `comisiones` también tiene una columna `tipo` ('teorica'/'practica'). Calificá: `au.tipo = 'laboratorio'`.",
        ],
        explicacion="""Después de hacer los JOIN, el `WHERE` puede filtrar por columnas de **cualquiera** de las tablas unidas: `au.tipo` (del aula) y `c.anio` (de la comisión).

La trampa está en el nombre `tipo`: existe en `aulas` (`'normal'`, `'laboratorio'`, `'centro de computos'`) **y** en `comisiones` (`'teorica'`, `'practica'`).

- Sin calificar (`WHERE tipo = 'laboratorio'`) → error *Column 'tipo' in where clause is ambiguous*.
- Con `c.tipo` → no da error, pero ninguna comisión tiene tipo 'laboratorio' → 0 filas.

Regla práctica: en consultas con JOIN, **calificá siempre** las columnas con el alias de la tabla.""",
        errores_comunes=[
            "Filtrar por `c.tipo` (tipo de comisión) en vez de `au.tipo` (tipo de aula).",
            "No calificar `tipo`: error de columna ambigua.",
            "Olvidar el filtro del año.",
        ],
        trampas=[
            dict(titulo="Tipo de la comisión en vez del aula", sql="""SELECT c.id_comision, a.nombre AS asignatura, au.nombre AS aula
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN aulas au ON au.id_aula = c.id_aula
WHERE c.tipo = 'laboratorio' AND c.anio = 2026;"""),
            dict(titulo="Sin filtrar el año", sql="""SELECT c.id_comision, a.nombre AS asignatura, au.nombre AS aula
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN aulas au ON au.id_aula = c.id_aula
WHERE au.tipo = 'laboratorio';"""),
        ],
        tags=["JOIN", "WHERE", "columna ambigua"],
    ),
    dict(
        id="join-n02",
        origen="Variante",
        titulo="Alumnos activos en Medicina",
        dificultad=1,
        tipo="select",
        enunciado="Listá nombre, apellido y fecha de inscripción de los alumnos que tienen una inscripción en estado "
                  "**'activa'** en la carrera **'Medicina'**. Buscá la carrera por su nombre.",
        solucion="""SELECT a.nombre, a.apellido, ac.fecha_inscripcion
FROM alumnos a
JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
JOIN carreras c        ON c.id_carrera = ac.id_carrera
WHERE c.nombre = 'Medicina'
  AND ac.estado = 'activa';""",
        alternativas=[
            dict(titulo="Carrera con subconsulta", sql="""SELECT a.nombre, a.apellido, ac.fecha_inscripcion
FROM alumnos a
JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
WHERE ac.estado = 'activa'
  AND ac.id_carrera = (SELECT id_carrera FROM carreras WHERE nombre = 'Medicina');"""),
        ],
        pistas=[
            "Necesitás `alumnos` (nombre), `alumno_carrera` (estado y fecha) y `carreras` (nombre de la carrera).",
            "Son dos condiciones en el `WHERE`, sobre tablas distintas.",
            "`WHERE c.nombre = 'Medicina' AND ac.estado = 'activa'`.",
        ],
        explicacion="""El estado y la fecha de inscripción **no son del alumno ni de la carrera**: son de la relación entre ambos, por eso están en `alumno_carrera`. Un mismo alumno puede estar activo en una carrera y haber abandonado otra.

Se hacen los dos JOIN de siempre y se filtra con columnas de dos tablas:

- `c.nombre = 'Medicina'` → de `carreras`.
- `ac.estado = 'activa'` → de `alumno_carrera`.

`estado` es un `ENUM('activa','pausada','graduado','abandonado')`: hay que escribir el valor **exacto**. `'activo'` (en masculino) no coincide con ninguno y devuelve 0 filas sin dar error.

La alternativa reemplaza el JOIN con `carreras` por una subconsulta que obtiene el id de 'Medicina'.""",
        errores_comunes=[
            "Olvidar el filtro de estado: aparecen también los que abandonaron, pausaron o se graduaron.",
            "Escribir un valor que no está en el ENUM (`'activo'`, `'Activa '`): no da error, simplemente no encuentra nada.",
        ],
        trampas=[
            dict(titulo="Sin filtrar el estado", sql="""SELECT a.nombre, a.apellido, ac.fecha_inscripcion
FROM alumnos a
JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
JOIN carreras c ON c.id_carrera = ac.id_carrera
WHERE c.nombre = 'Medicina';"""),
            dict(titulo="Valor de ENUM mal escrito ('activo')", sql="""SELECT a.nombre, a.apellido, ac.fecha_inscripcion
FROM alumnos a
JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
JOIN carreras c ON c.id_carrera = ac.id_carrera
WHERE c.nombre = 'Medicina' AND ac.estado = 'activo';"""),
        ],
        tags=["JOIN", "WHERE", "ENUM"],
    ),
    dict(
        id="join-n03",
        origen="Variante",
        titulo="Asignaturas con sus correlativas (auto-JOIN)",
        dificultad=2,
        tipo="select",
        enunciado="En `correlatividades`, cada fila indica que para cursar `id_asignatura` hay que tener aprobada "
                  "`id_asignatura_correlativa`. Listá el **nombre de cada asignatura** junto con el **nombre de cada "
                  "una de sus correlativas** (una fila por correlatividad).",
        solucion="""SELECT a.nombre AS asignatura, c.nombre AS correlativa
FROM correlatividades co
JOIN asignaturas a ON a.id_asignatura = co.id_asignatura
JOIN asignaturas c ON c.id_asignatura = co.id_asignatura_correlativa;""",
        pistas=[
            "Los dos ids de `correlatividades` apuntan a la **misma** tabla `asignaturas`.",
            "Hay que unir `asignaturas` **dos veces**, con dos alias distintos (uno para la asignatura y otro para la correlativa).",
            "`JOIN asignaturas a ON a.id_asignatura = co.id_asignatura JOIN asignaturas c ON c.id_asignatura = co.id_asignatura_correlativa`.",
        ],
        explicacion="""`correlatividades` tiene **dos FK a la misma tabla**. Para traer dos nombres distintos de `asignaturas` en la misma fila, la tabla se usa **dos veces** con alias diferentes (un *auto-JOIN* o *self-join*):

```
asignaturas a ← co.id_asignatura
asignaturas c ← co.id_asignatura_correlativa
```

Pensá en `a` y `c` como dos «copias» de la tabla: una juega el rol de «materia» y la otra el de «correlativa».

Si usás un solo alias con las dos condiciones (`ON a.id_asignatura = co.id_asignatura AND a.id_asignatura = co.id_asignatura_correlativa`), pedís que una asignatura sea correlativa de sí misma → 0 filas.

Fijate también en la **dirección**: si intercambiás qué alias va con qué columna, obtenés la relación al revés («es correlativa de»). El siguiente ejercicio lo pone a prueba.""",
        errores_comunes=[
            "Unir `asignaturas` una sola vez: no se pueden obtener dos nombres distintos de un mismo alias en la misma fila.",
            "Mostrar `id_asignatura_correlativa` en vez del nombre: el ejercicio pide nombres.",
            "Intercambiar las columnas del ON (la relación queda al revés).",
        ],
        trampas=[
            dict(titulo="Un solo alias con las dos condiciones", sql="""SELECT a.nombre AS asignatura, a.nombre AS correlativa
FROM correlatividades co
JOIN asignaturas a ON a.id_asignatura = co.id_asignatura
                  AND a.id_asignatura = co.id_asignatura_correlativa;"""),
            dict(titulo="Id de la correlativa en vez del nombre", sql="""SELECT a.nombre AS asignatura, co.id_asignatura_correlativa AS correlativa
FROM correlatividades co
JOIN asignaturas a ON a.id_asignatura = co.id_asignatura;"""),
        ],
        tags=["auto-JOIN", "self-join", "alias"],
    ),
    dict(
        id="join-n04",
        origen="Variante",
        titulo="¿Qué necesito para cursar esta materia?",
        dificultad=2,
        tipo="select",
        enunciado="Un alumno quiere cursar **'Gestión de Programación 286'**. Mostrá el id y el nombre de las "
                  "asignaturas que necesita tener aprobadas (sus correlativas). Buscá la asignatura por su nombre. "
                  "(Recordá: en `correlatividades`, `id_asignatura` requiere `id_asignatura_correlativa`.)",
        solucion="""SELECT c.id_asignatura, c.nombre AS correlativa
FROM correlatividades co
JOIN asignaturas a ON a.id_asignatura = co.id_asignatura
JOIN asignaturas c ON c.id_asignatura = co.id_asignatura_correlativa
WHERE a.nombre = 'Gestión de Programación 286';""",
        alternativas=[
            dict(titulo="Subconsulta para el id de la materia", sql="""SELECT c.id_asignatura, c.nombre AS correlativa
FROM correlatividades co
JOIN asignaturas c ON c.id_asignatura = co.id_asignatura_correlativa
WHERE co.id_asignatura = (
    SELECT id_asignatura
    FROM asignaturas
    WHERE nombre = 'Gestión de Programación 286'
);"""),
            dict(titulo="Solo con subconsultas (IN)", sql="""SELECT id_asignatura, nombre AS correlativa
FROM asignaturas
WHERE id_asignatura IN (
    SELECT id_asignatura_correlativa
    FROM correlatividades
    WHERE id_asignatura = (SELECT id_asignatura FROM asignaturas
                           WHERE nombre = 'Gestión de Programación 286')
);"""),
        ],
        columnas=[["id_asignatura", "correlativa"], ["correlativa"]],
        pistas=[
            "Es el auto-JOIN del ejercicio anterior, con un filtro.",
            "El filtro va sobre el alias que representa a la materia que se quiere cursar (la que está en `co.id_asignatura`).",
            "Mostrás el nombre del **otro** alias: `WHERE a.nombre = '...'` y `SELECT c.nombre`.",
        ],
        explicacion="""Con el auto-JOIN, `a` es la materia que se quiere cursar y `c` es cada correlativa. Entonces:

- **Filtrás** por el nombre de `a` (`a.nombre = 'Gestión de Programación 286'`).
- **Mostrás** los datos de `c`.

La dirección importa. Si filtrás por `c.nombre` y mostrás `a.nombre`, respondés la pregunta inversa: «¿para qué materias es correlativa *Gestión de Programación 286*?». Con estos datos esa respuesta es 1 materia, mientras que las correlativas que se piden son 5.

Si no querés hacer el auto-JOIN, podés resolver el id de la materia con una subconsulta y unir `asignaturas` una sola vez (ver alternativas).""",
        errores_comunes=[
            "Invertir la dirección: filtrar por la correlativa y mostrar la materia (responde «¿para qué es correlativa?»).",
            "Mostrar el nombre de la materia buscada en vez del de sus correlativas.",
        ],
        trampas=[
            dict(titulo="Dirección invertida", sql="""SELECT a.id_asignatura, a.nombre AS correlativa
FROM correlatividades co
JOIN asignaturas a ON a.id_asignatura = co.id_asignatura
JOIN asignaturas c ON c.id_asignatura = co.id_asignatura_correlativa
WHERE c.nombre = 'Gestión de Programación 286';"""),
            dict(titulo="Muestra la materia buscada", sql="""SELECT a.id_asignatura, a.nombre AS correlativa
FROM correlatividades co
JOIN asignaturas a ON a.id_asignatura = co.id_asignatura
JOIN asignaturas c ON c.id_asignatura = co.id_asignatura_correlativa
WHERE a.nombre = 'Gestión de Programación 286';"""),
        ],
        tags=["auto-JOIN", "dirección de la relación", "subconsulta"],
    ),
    dict(
        id="join-n05",
        origen="Variante",
        titulo="Docentes asignados a Programación en 2025",
        dificultad=2,
        tipo="select",
        enunciado="Mostrá qué docentes estuvieron asignados (tabla `docente_asignatura`) a asignaturas de "
                  "**Programación** (nombre que contiene 'Programación') durante **2025**: nombre y apellido del "
                  "docente, nombre de la asignatura, cuatrimestre y horas asignadas.",
        solucion="""SELECT d.nombre, d.apellido, a.nombre AS asignatura, da.cuatrimestre, da.horas_asignadas
FROM docente_asignatura da
JOIN docentes d    ON d.id_docente = da.id_docente
JOIN asignaturas a ON a.id_asignatura = da.id_asignatura
WHERE da.anio = 2025
  AND a.nombre LIKE '%Programación%';""",
        pistas=[
            "`docente_asignatura` es una tabla intermedia entre `docentes` y `asignaturas`, con datos propios (año, cuatrimestre, horas).",
            "Uní por `id_docente` y por `id_asignatura`. Ojo: la PK de esta tabla se llama `id`.",
            "Filtrá con `da.anio = 2025 AND a.nombre LIKE '%Programación%'`.",
        ],
        explicacion="""`docente_asignatura` relaciona docentes y asignaturas (muchos a muchos) y además guarda datos **de la asignación**: año, cuatrimestre, horas y monto. Se resuelve igual que `alumno_carrera`: dos JOIN desde la intermedia.

Un detalle que suele confundir: la PK de la intermedia se llama simplemente `id`. Si escribís `d.id_docente = da.id`, MySQL no da error (son dos enteros), pero estás uniendo cada docente con la **fila número N** de la asignación, no con sus asignaciones reales. Revisá siempre que la condición sea **FK = PK**: `da.id_docente = d.id_docente`.

El filtro combina una columna de la intermedia (`da.anio`) con un `LIKE` sobre otra tabla (`a.nombre`).""",
        errores_comunes=[
            "Unir con la PK de la intermedia (`da.id`) en vez de la FK (`da.id_docente`): no da error pero el resultado es basura.",
            "Olvidar el filtro del año.",
            "Usar `comisiones` en lugar de `docente_asignatura`: es otra relación (y no tiene horas asignadas).",
        ],
        trampas=[
            dict(titulo="Unir por la PK de la intermedia", sql="""SELECT d.nombre, d.apellido, a.nombre AS asignatura, da.cuatrimestre, da.horas_asignadas
FROM docente_asignatura da
JOIN docentes d ON d.id_docente = da.id
JOIN asignaturas a ON a.id_asignatura = da.id_asignatura
WHERE da.anio = 2025 AND a.nombre LIKE '%Programación%';"""),
            dict(titulo="Sin filtrar el año", sql="""SELECT d.nombre, d.apellido, a.nombre AS asignatura, da.cuatrimestre, da.horas_asignadas
FROM docente_asignatura da
JOIN docentes d ON d.id_docente = da.id_docente
JOIN asignaturas a ON a.id_asignatura = da.id_asignatura
WHERE a.nombre LIKE '%Programación%';"""),
        ],
        tags=["JOIN", "tabla intermedia", "LIKE"],
    ),
    dict(
        id="join-n06",
        origen="Variante",
        titulo="Inscriptos a las mesas del 16/03/2026",
        dificultad=2,
        tipo="select",
        enunciado="Listá los alumnos inscriptos a las mesas finales que se tomaron el **16 de marzo de 2026**: "
                  "nombre y apellido del alumno, nombre de la asignatura de la mesa y estado de la inscripción.",
        solucion="""SELECT al.nombre, al.apellido, a.nombre AS asignatura, i.estado
FROM inscripciones_finales i
JOIN mesas_finales m ON m.id_mesa = i.id_mesa
JOIN alumnos al      ON al.id_alumno = i.id_alumno
JOIN asignaturas a   ON a.id_asignatura = m.id_asignatura
WHERE m.fecha = '2026-03-16';""",
        pistas=[
            "Partí de `inscripciones_finales`: tiene el alumno (`id_alumno`) y la mesa (`id_mesa`).",
            "La asignatura no está en la inscripción sino en la **mesa**: `inscripciones_finales → mesas_finales → asignaturas`.",
            "La fecha del examen es `m.fecha` (no `i.fecha_inscripcion`).",
        ],
        explicacion="""Son 4 tablas, encadenadas por sus FK:

```
alumnos ← inscripciones_finales → mesas_finales → asignaturas
```

La asignatura se obtiene **a través de la mesa**: `inscripciones_finales` no tiene `id_asignatura`. Por eso el JOIN con `asignaturas` usa `m.id_asignatura`.

Hay dos fechas que se pueden confundir:

- `mesas_finales.fecha`: el día del examen. Es la que pide el enunciado.
- `inscripciones_finales.fecha_inscripcion`: el día en que el alumno se anotó.

Filtrar por la fecha equivocada no da error, pero devuelve otra cosa (inscripciones hechas ese día, a mesas de cualquier fecha).""",
        errores_comunes=[
            "Filtrar por `fecha_inscripcion` en lugar de la fecha de la mesa.",
            "Intentar unir `asignaturas` directamente con `inscripciones_finales` (no tiene `id_asignatura`).",
        ],
        trampas=[
            dict(titulo="Fecha de inscripción en vez de fecha de la mesa", sql="""SELECT al.nombre, al.apellido, a.nombre AS asignatura, i.estado
FROM inscripciones_finales i
JOIN mesas_finales m ON m.id_mesa = i.id_mesa
JOIN alumnos al ON al.id_alumno = i.id_alumno
JOIN asignaturas a ON a.id_asignatura = m.id_asignatura
WHERE i.fecha_inscripcion = '2026-03-16';"""),
            dict(titulo="Asignatura unida por el id de la mesa", sql="""SELECT al.nombre, al.apellido, a.nombre AS asignatura, i.estado
FROM inscripciones_finales i
JOIN mesas_finales m ON m.id_mesa = i.id_mesa
JOIN alumnos al ON al.id_alumno = i.id_alumno
JOIN asignaturas a ON a.id_asignatura = i.id_mesa
WHERE m.fecha = '2026-03-16';"""),
        ],
        tags=["JOIN", "varias tablas", "fechas"],
    ),
    dict(
        id="join-n07",
        origen="Variante",
        titulo="Todas las asignaturas y sus comisiones (LEFT JOIN)",
        dificultad=2,
        tipo="select",
        enunciado="Listá **todas** las asignaturas (id y nombre) junto con el id de cada una de sus comisiones. "
                  "Las asignaturas que **no tienen comisiones** también tienen que aparecer, con la comisión en `NULL`.",
        solucion="""SELECT a.id_asignatura, a.nombre, c.id_comision
FROM asignaturas a
LEFT JOIN comisiones c ON c.id_asignatura = a.id_asignatura;""",
        alternativas=[
            dict(titulo="RIGHT JOIN con las tablas invertidas", sql="""SELECT a.id_asignatura, a.nombre, c.id_comision
FROM comisiones c
RIGHT JOIN asignaturas a ON a.id_asignatura = c.id_asignatura;"""),
        ],
        columnas=[["id_asignatura", "nombre", "id_comision"], ["nombre", "id_comision"], ["id_asignatura", "id_comision"]],
        casos_borde=True,
        pistas=[
            "Un `JOIN` común (INNER) descarta las asignaturas sin comisiones.",
            "`LEFT JOIN` conserva **todas** las filas de la tabla de la izquierda, tengan o no pareja.",
            "`FROM asignaturas a LEFT JOIN comisiones c ON c.id_asignatura = a.id_asignatura`.",
        ],
        explicacion="""**INNER JOIN** solo deja las filas que tienen pareja en las dos tablas. Las 41 asignaturas sin comisiones desaparecerían.

**LEFT JOIN** conserva todas las filas de la tabla de la **izquierda** (la del `FROM`); cuando no hay pareja, las columnas de la derecha vienen en `NULL`:

| id_asignatura | nombre | id_comision |
|---|---|---|
| 2 | Análisis de Salud 2 | 462 |
| 2 | Análisis de Salud 2 | 995 |
| 6 | Introducción a Física 6 | `NULL` |

Con datos reales son 1241 filas: 1200 comisiones + 41 asignaturas sin comisión.

El orden de las tablas importa: `FROM comisiones LEFT JOIN asignaturas` conserva las **comisiones** (que siempre tienen asignatura) y no agrega nada. `RIGHT JOIN` es el espejo de `LEFT JOIN`.

Si después quisieras **solo** las que no tienen comisiones, agregarías `WHERE c.id_comision IS NULL` (eso es el patrón de «ausencia» de la sección de subconsultas).""",
        errores_comunes=[
            "Usar `JOIN` (INNER): se pierden las asignaturas sin comisiones.",
            "Poner las tablas al revés (`FROM comisiones LEFT JOIN asignaturas`): conserva las comisiones, no las asignaturas.",
        ],
        trampas=[
            dict(titulo="INNER JOIN", sql="""SELECT a.id_asignatura, a.nombre, c.id_comision
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura;"""),
            dict(titulo="LEFT JOIN con las tablas invertidas", sql="""SELECT a.id_asignatura, a.nombre, c.id_comision
FROM comisiones c
LEFT JOIN asignaturas a ON a.id_asignatura = c.id_asignatura;"""),
        ],
        tags=["LEFT JOIN", "RIGHT JOIN", "NULL"],
    ),
    dict(
        id="join-n08",
        origen="Variante",
        titulo="Notas de un alumno (4 JOIN)",
        dificultad=3,
        tipo="select",
        enunciado="Mostrá todas las notas de exámenes del alumno con **DNI '30000010'**: nombre de la asignatura, "
                  "fecha del examen, tipo de examen (parcial/recuperatorio) y nota. Ordená por fecha del examen "
                  "(de la más antigua a la más reciente).",
        solucion="""SELECT a.nombre AS asignatura, e.fecha, e.tipo AS tipo_examen, n.nota
FROM notas n
JOIN alumnos al    ON al.id_alumno = n.id_alumno
JOIN examenes e    ON e.id_examen = n.id_examen
JOIN comisiones c  ON c.id_comision = e.id_comision
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
WHERE al.dni = '30000010'
ORDER BY e.fecha;""",
        alternativas=[
            dict(titulo="Alumno por subconsulta", sql="""SELECT a.nombre AS asignatura, e.fecha, e.tipo AS tipo_examen, n.nota
FROM notas n
JOIN examenes e    ON e.id_examen = n.id_examen
JOIN comisiones c  ON c.id_comision = e.id_comision
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
WHERE n.id_alumno = (SELECT id_alumno FROM alumnos WHERE dni = '30000010')
ORDER BY e.fecha;"""),
        ],
        orden=[("fecha", "asc")],
        pistas=[
            "Seguí el camino de FK: `notas → examenes → comisiones → asignaturas`. El DNI está en `alumnos`.",
            "`examenes` no tiene `id_asignatura`: la asignatura se obtiene a través de la comisión.",
            "Filtrá con `al.dni = '30000010'` (el DNI es texto) y ordená con `ORDER BY e.fecha`.",
        ],
        explicacion="""Para llegar de una nota al nombre de la materia hay que recorrer la cadena de FK completa:

```
notas → examenes → comisiones → asignaturas
  ↓
alumnos (para filtrar por DNI)
```

No hay atajos: `examenes` solo conoce su `id_comision`, y es la comisión la que conoce la asignatura. Un error típico es saltear `comisiones` y escribir `a.id_asignatura = e.id_comision`: MySQL no se queja (son enteros), pero une con una asignatura cualquiera.

Otros detalles:

- `dni` es `VARCHAR`: compará con texto (`'30000010'`). No confundas DNI con `id_alumno` (este alumno tiene id 10).
- `tipo` existe en `examenes` y en `comisiones`: calificalo (`e.tipo`).
- Para ordenar por fecha se usa la fecha del **examen** (`e.fecha`).""",
        errores_comunes=[
            "Saltear `comisiones` uniendo `asignaturas` con `e.id_comision`: no da error, pero las materias son incorrectas.",
            "Filtrar por `id_alumno = 30000010` confundiendo el DNI con el id del alumno.",
            "Escribir `tipo` sin alias: es ambiguo entre `examenes` y `comisiones`.",
        ],
        trampas=[
            dict(titulo="Saltear comisiones", sql="""SELECT a.nombre AS asignatura, e.fecha, e.tipo AS tipo_examen, n.nota
FROM notas n
JOIN alumnos al ON al.id_alumno = n.id_alumno
JOIN examenes e ON e.id_examen = n.id_examen
JOIN asignaturas a ON a.id_asignatura = e.id_comision
WHERE al.dni = '30000010'
ORDER BY e.fecha;"""),
            dict(titulo="DNI confundido con id_alumno", sql="""SELECT a.nombre AS asignatura, e.fecha, e.tipo AS tipo_examen, n.nota
FROM notas n
JOIN examenes e ON e.id_examen = n.id_examen
JOIN comisiones c ON c.id_comision = e.id_comision
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
WHERE n.id_alumno = 30000010
ORDER BY e.fecha;"""),
            dict(titulo="Tipo de la comisión en vez del examen", sql="""SELECT a.nombre AS asignatura, e.fecha, c.tipo AS tipo_examen, n.nota
FROM notas n
JOIN alumnos al ON al.id_alumno = n.id_alumno
JOIN examenes e ON e.id_examen = n.id_examen
JOIN comisiones c ON c.id_comision = e.id_comision
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
WHERE al.dni = '30000010'
ORDER BY e.fecha;"""),
        ],
        tags=["JOIN", "varias tablas", "ORDER BY"],
    ),
]
