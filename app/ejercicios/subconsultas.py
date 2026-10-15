"""Sección: Subconsultas y ausencia/presencia de relaciones (Clase Semana 10 · Sección 1)."""

EJERCICIOS = [
    # ------------------------------------------------------------------
    # Originales de la Clase Semana 10 (ej. 1 a 10)
    # ------------------------------------------------------------------
    dict(
        id="sub-01",
        origen="Semana 10 · Ej. 1",
        titulo="Alumnos inscriptos en alguna comisión",
        dificultad=1,
        tipo="select",
        enunciado="Obtener los alumnos que actualmente estén **inscriptos en alguna comisión**. "
                  "Mostrá id, nombre y apellido del alumno (cada alumno una sola vez).",
        solucion="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
WHERE a.id_alumno IN (
    SELECT i.id_alumno
    FROM inscripcion_alumno_comision i
);""",
        alternativas=[
            dict(titulo="Con EXISTS", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
WHERE EXISTS (
    SELECT 1
    FROM inscripcion_alumno_comision i
    WHERE i.id_alumno = a.id_alumno
);"""),
            dict(titulo="Con JOIN + DISTINCT", sql="""SELECT DISTINCT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
JOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno;"""),
        ],
        variantes=[
            dict(titulo="Inscripción vigente (sin contar las bajas)", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
WHERE a.id_alumno IN (
    SELECT i.id_alumno
    FROM inscripcion_alumno_comision i
    WHERE i.estado <> 'Baja'
);"""),
            dict(titulo="Cursando actualmente (estado = 'Cursa')", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
WHERE a.id_alumno IN (
    SELECT i.id_alumno
    FROM inscripcion_alumno_comision i
    WHERE i.estado = 'Cursa'
);"""),
            dict(titulo="Inscriptos en comisiones del año actual (2026)", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
WHERE a.id_alumno IN (
    SELECT i.id_alumno
    FROM inscripcion_alumno_comision i
    JOIN comisiones c ON c.id_comision = i.id_comision
    WHERE c.anio = 2026
);"""),
        ],
        columnas=[["id_alumno"], ["nombre", "apellido"]],
        casos_borde=True,
        pistas=[
            "Es un problema de **presencia**: querés los alumnos para los que existe al menos una fila en `inscripcion_alumno_comision`.",
            "Podés filtrar `alumnos` con `WHERE id_alumno IN (SELECT id_alumno FROM inscripcion_alumno_comision)`.",
            "Si lo resolvés con `JOIN`, cada alumno aparece una vez por cada inscripción: agregá `DISTINCT`.",
        ],
        explicacion="""Para «los que **tienen** algo» alcanza con verificar que exista al menos una fila relacionada:

- **`IN`**: la subconsulta arma la lista de ids de alumnos con inscripciones y el `WHERE` se queda con los alumnos de esa lista.
- **`EXISTS`**: por cada alumno, la subconsulta correlacionada busca alguna inscripción suya; con encontrar una ya alcanza.
- **`JOIN`**: también sirve, pero el alumno se repite una vez por comisión → hace falta `DISTINCT`.

Con `IN`/`EXISTS` no hay repetidos porque solo se **filtra** `alumnos`, nunca se multiplican filas.

**«Actualmente»** es ambiguo: la solución toma cualquier inscripción, pero también se aceptan «sin bajas» (`estado <> 'Baja'`), «cursando» (`estado = 'Cursa'`) o «en comisiones de 2026». En el parcialito, aclará en un comentario qué interpretación usaste.""",
        errores_comunes=[
            "Hacer `JOIN` sin `DISTINCT`: cada alumno aparece tantas veces como comisiones tenga (17.877 filas en vez de 1.000).",
            "Confundir tablas: `alumno_carrera` es la inscripción a una **carrera**; la inscripción a **comisiones** está en `inscripcion_alumno_comision`.",
            "Usar `LEFT JOIN` sin filtrar: trae también a los alumnos sin inscripciones (con NULL del lado derecho).",
        ],
        trampas=[
            dict(titulo="JOIN sin DISTINCT", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
JOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno;"""),
            dict(titulo="Inscriptos en una carrera (tabla equivocada)", sql="""SELECT id_alumno, nombre, apellido
FROM alumnos
WHERE id_alumno IN (SELECT id_alumno FROM alumno_carrera);"""),
            dict(titulo="LEFT JOIN sin filtrar", sql="""SELECT DISTINCT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
LEFT JOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno;"""),
        ],
        tags=["IN", "EXISTS", "DISTINCT", "presencia"],
    ),
    dict(
        id="sub-02",
        origen="Semana 10 · Ej. 2",
        titulo="Docentes sin comisiones asignadas",
        dificultad=2,
        tipo="select",
        enunciado="Detectar a los docentes que actualmente **no tengan comisiones asignadas**. "
                  "Mostrar id, nombre y apellido del docente.",
        solucion="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
WHERE NOT EXISTS (
    SELECT 1
    FROM comisiones c
    WHERE c.id_docente = d.id_docente
);""",
        alternativas=[
            dict(titulo="Con NOT IN", sql="""SELECT id_docente, nombre, apellido
FROM docentes
WHERE id_docente NOT IN (SELECT id_docente FROM comisiones);"""),
            dict(titulo="Con LEFT JOIN … IS NULL", sql="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
LEFT JOIN comisiones c ON c.id_docente = d.id_docente
WHERE c.id_comision IS NULL;"""),
        ],
        variantes=[
            dict(titulo="Sin comisiones en el año actual (2026)", sql="""SELECT d.id_docente, d.nombre, d.apellido
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
            "Es un problema de **ausencia**: buscás docentes para los que NO existe ninguna fila en `comisiones`.",
            "La relación es `comisiones.id_docente → docentes.id_docente`.",
            "Tres caminos clásicos: `NOT IN (subconsulta)`, `NOT EXISTS (subconsulta correlacionada)` o `LEFT JOIN … WHERE c.id_comision IS NULL`.",
        ],
        explicacion="""Para encontrar «los que **no** tienen» algo hay que comparar contra la tabla que registra la relación (`comisiones`).

**Con `NOT EXISTS`** la subconsulta se evalúa por cada docente `d`: si no encuentra ninguna comisión con `c.id_docente = d.id_docente`, el docente queda en el resultado.

**Con `LEFT JOIN`** se conservan todos los docentes; los que no tienen comisión quedan con las columnas de `comisiones` en `NULL`, y eso es lo que filtramos con `IS NULL` (sobre una columna que nunca es NULL cuando hay match, como la PK).

**Con `NOT IN`** funciona porque `comisiones.id_docente` es NOT NULL; si la subconsulta pudiera devolver un `NULL`, el resultado quedaría vacío.

Con los datos originales la consulta devuelve **0 filas** (todos los docentes tienen comisiones). Por eso el corrector también la prueba con **casos borde** (docentes nuevos sin comisiones). También se acepta leer «actualmente» como «sin comisiones en 2026».""",
        errores_comunes=[
            "Usar `INNER JOIN` + `WHERE c.id_docente IS NULL`: el INNER JOIN ya descartó a los docentes sin comisión, nunca va a haber NULL.",
            "Con `NOT IN`, si la subconsulta devuelve algún `NULL` el resultado queda vacío. Acá `id_docente` es NOT NULL, pero en otros casos usá `NOT EXISTS`.",
            "Hacer el `IS NULL` sobre una columna que puede ser NULL aun habiendo match (por ejemplo `cupo`).",
        ],
        trampas=[
            dict(titulo="INNER JOIN con IS NULL", sql="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d JOIN comisiones c ON c.id_docente = d.id_docente
WHERE c.id_comision IS NULL;"""),
            dict(titulo="Docentes CON comisiones", sql="""SELECT DISTINCT d.id_docente, d.nombre, d.apellido
FROM docentes d JOIN comisiones c ON c.id_docente = d.id_docente;"""),
        ],
        tags=["NOT EXISTS", "NOT IN", "LEFT JOIN", "ausencia"],
    ),
    dict(
        id="sub-03",
        origen="Semana 10 · Ej. 3",
        titulo="Asignaturas con al menos una comisión",
        dificultad=1,
        tipo="select",
        enunciado="Mostrar asignaturas que posean **al menos una comisión**. "
                  "Mostrá id y nombre de la asignatura (cada una una sola vez).",
        solucion="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
WHERE EXISTS (
    SELECT 1
    FROM comisiones c
    WHERE c.id_asignatura = a.id_asignatura
);""",
        alternativas=[
            dict(titulo="Con IN", sql="""SELECT id_asignatura, nombre
FROM asignaturas
WHERE id_asignatura IN (SELECT id_asignatura FROM comisiones);"""),
            dict(titulo="Con JOIN + DISTINCT", sql="""SELECT DISTINCT a.id_asignatura, a.nombre
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura;"""),
        ],
        columnas=[["id_asignatura"], ["nombre"]],
        casos_borde=True,
        pistas=[
            "Es **presencia**: te quedás con las asignaturas que aparecen en `comisiones`.",
            "La relación es `comisiones.id_asignatura → asignaturas.id_asignatura`.",
            "`WHERE EXISTS (SELECT 1 FROM comisiones c WHERE c.id_asignatura = a.id_asignatura)` o, si usás JOIN, no te olvides del `DISTINCT`.",
        ],
        explicacion="""«Posee al menos una» = **existe** al menos una fila relacionada.

```sql
WHERE EXISTS (SELECT 1 FROM comisiones c
              WHERE c.id_asignatura = a.id_asignatura)
```

`EXISTS` devuelve verdadero apenas encuentra una comisión de esa asignatura; el `SELECT 1` es una convención: no importa qué columnas devuelva la subconsulta, solo si devuelve filas.

`IN` hace lo mismo comparando contra la lista de ids. Con `JOIN` la asignatura aparece una vez por comisión (hay asignaturas con hasta 8), por eso necesita `DISTINCT`.

Resultado: 459 de las 500 asignaturas (las otras 41 no tienen comisiones).""",
        errores_comunes=[
            "Hacer `JOIN` sin `DISTINCT`: devuelve 1.200 filas (una por comisión) en vez de 459.",
            "Usar `LEFT JOIN` y agrupar sin `HAVING`: el LEFT JOIN conserva también las asignaturas sin comisiones.",
        ],
        trampas=[
            dict(titulo="JOIN sin DISTINCT", sql="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura;"""),
            dict(titulo="LEFT JOIN agrupado sin filtrar", sql="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
LEFT JOIN comisiones c ON c.id_asignatura = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre;"""),
        ],
        tags=["EXISTS", "IN", "DISTINCT", "presencia"],
    ),
    dict(
        id="sub-04",
        origen="Semana 10 · Ej. 4",
        titulo="Aulas nunca utilizadas",
        dificultad=2,
        tipo="select",
        enunciado="Detectar aulas que **nunca hayan sido utilizadas** para el dictado de comisiones. "
                  "Mostrá id y nombre del aula.",
        solucion="""SELECT au.id_aula, au.nombre
FROM aulas au
WHERE NOT EXISTS (
    SELECT 1
    FROM comisiones c
    WHERE c.id_aula = au.id_aula
);""",
        alternativas=[
            dict(titulo="Con NOT IN", sql="""SELECT id_aula, nombre
FROM aulas
WHERE id_aula NOT IN (SELECT id_aula FROM comisiones);"""),
            dict(titulo="Con LEFT JOIN … IS NULL", sql="""SELECT au.id_aula, au.nombre
FROM aulas au
LEFT JOIN comisiones c ON c.id_aula = au.id_aula
WHERE c.id_comision IS NULL;"""),
        ],
        columnas=[["id_aula"], ["nombre"]],
        casos_borde=True,
        pistas=[
            "Es **ausencia**: aulas para las que no existe ninguna comisión con ese `id_aula`.",
            "Podés usar `NOT EXISTS` con una subconsulta correlacionada sobre `comisiones`.",
            "Con `LEFT JOIN`, el `IS NULL` va sobre una columna de la tabla de la **derecha** (`c.id_comision`), no sobre `au.id_aula`.",
        ],
        explicacion="""Mismo patrón que «docentes sin comisiones», ahora con `id_aula`. Las tres formas son equivalentes:

- `NOT EXISTS (SELECT 1 FROM comisiones c WHERE c.id_aula = au.id_aula)`
- `id_aula NOT IN (SELECT id_aula FROM comisiones)` — seguro acá porque `comisiones.id_aula` es NOT NULL.
- `LEFT JOIN comisiones c ... WHERE c.id_comision IS NULL`

En el `LEFT JOIN` las aulas sin comisiones quedan con **todas** las columnas de `c` en NULL. Por eso se pregunta por una columna de `c` que nunca es NULL cuando hay match (la PK). Preguntar `au.id_aula IS NULL` no tiene sentido: la tabla izquierda siempre está completa.

Con los datos originales todas las aulas se usaron (0 filas); el corrector agrega aulas nuevas sin uso para verificar.""",
        errores_comunes=[
            "Hacer el `IS NULL` sobre la tabla izquierda (`au.id_aula IS NULL`): nunca es NULL, devuelve siempre vacío.",
            "Usar `INNER JOIN` + `IS NULL`: el INNER JOIN ya eliminó las aulas sin comisiones.",
            "Conformarse con «da 0 filas»: con los datos reales una consulta mal hecha también da 0. Probá agregar un aula nueva.",
        ],
        trampas=[
            dict(titulo="INNER JOIN con IS NULL", sql="""SELECT au.id_aula, au.nombre
FROM aulas au JOIN comisiones c ON c.id_aula = au.id_aula
WHERE c.id_comision IS NULL;"""),
            dict(titulo="IS NULL sobre la tabla izquierda", sql="""SELECT au.id_aula, au.nombre
FROM aulas au
LEFT JOIN comisiones c ON c.id_aula = au.id_aula
WHERE au.id_aula IS NULL;"""),
            dict(titulo="Aulas usadas (IN en vez de NOT IN)", sql="""SELECT id_aula, nombre
FROM aulas
WHERE id_aula IN (SELECT id_aula FROM comisiones);"""),
        ],
        tags=["NOT EXISTS", "NOT IN", "LEFT JOIN", "ausencia"],
    ),
    dict(
        id="sub-05",
        origen="Semana 10 · Ej. 5",
        titulo="Carreras sin alumnos",
        dificultad=2,
        tipo="select",
        enunciado="Obtener carreras que actualmente **no poseen alumnos asociados**. "
                  "Mostrá id y nombre de la carrera.",
        solucion="""SELECT c.id_carrera, c.nombre
FROM carreras c
WHERE NOT EXISTS (
    SELECT 1
    FROM alumno_carrera ac
    WHERE ac.id_carrera = c.id_carrera
);""",
        alternativas=[
            dict(titulo="Con NOT IN", sql="""SELECT id_carrera, nombre
FROM carreras
WHERE id_carrera NOT IN (SELECT id_carrera FROM alumno_carrera);"""),
            dict(titulo="Con LEFT JOIN … IS NULL", sql="""SELECT c.id_carrera, c.nombre
FROM carreras c
LEFT JOIN alumno_carrera ac ON ac.id_carrera = c.id_carrera
WHERE ac.id IS NULL;"""),
            dict(titulo="Con LEFT JOIN + HAVING COUNT(columna) = 0", sql="""SELECT c.id_carrera, c.nombre
FROM carreras c
LEFT JOIN alumno_carrera ac ON ac.id_carrera = c.id_carrera
GROUP BY c.id_carrera, c.nombre
HAVING COUNT(ac.id_alumno) = 0;"""),
        ],
        variantes=[
            dict(titulo="Sin alumnos con estado 'activa'", sql="""SELECT c.id_carrera, c.nombre
FROM carreras c
WHERE NOT EXISTS (
    SELECT 1
    FROM alumno_carrera ac
    WHERE ac.id_carrera = c.id_carrera
      AND ac.estado = 'activa'
);"""),
        ],
        columnas=[["id_carrera"], ["nombre"]],
        casos_borde=True,
        pistas=[
            "La relación alumno–carrera vive en la tabla intermedia `alumno_carrera`.",
            "Buscás carreras para las que **no existe** ninguna fila en `alumno_carrera` con su `id_carrera`.",
            "`NOT EXISTS (SELECT 1 FROM alumno_carrera ac WHERE ac.id_carrera = c.id_carrera)`.",
        ],
        explicacion="""La relación N a N entre alumnos y carreras se registra en `alumno_carrera`, así que «carrera sin alumnos» = carrera que **no aparece** en esa tabla. Ni siquiera hace falta tocar `alumnos`.

Otra forma muy usada es contar con `LEFT JOIN` y quedarse con las que dan 0:

```sql
HAVING COUNT(ac.id_alumno) = 0
```

Ojo: tiene que ser `COUNT(columna_de_la_derecha)`. `COUNT(*)` cuenta filas, y la fila «vacía» que genera el `LEFT JOIN` también cuenta → daría 1, nunca 0.

**«Actualmente»** también se puede leer como «sin alumnos **activos**» (`estado = 'activa'`); esa interpretación también se acepta. Con los datos reales todas las carreras tienen alumnos: el corrector agrega dos carreras vacías.""",
        errores_comunes=[
            "`LEFT JOIN` + `HAVING COUNT(*) = 0`: COUNT(*) cuenta la fila con NULLs del LEFT JOIN, así que nunca da 0.",
            "Usar `INNER JOIN` + `IS NULL`: el INNER JOIN ya descartó las carreras sin alumnos.",
            "Hacer `JOIN` con `alumnos` directamente: no hay FK entre `alumnos` y `carreras`.",
        ],
        trampas=[
            dict(titulo="INNER JOIN con IS NULL", sql="""SELECT c.id_carrera, c.nombre
FROM carreras c JOIN alumno_carrera ac ON ac.id_carrera = c.id_carrera
WHERE ac.id IS NULL;"""),
            dict(titulo="LEFT JOIN + HAVING COUNT(*) = 0", sql="""SELECT c.id_carrera, c.nombre
FROM carreras c
LEFT JOIN alumno_carrera ac ON ac.id_carrera = c.id_carrera
GROUP BY c.id_carrera, c.nombre
HAVING COUNT(*) = 0;"""),
        ],
        tags=["NOT EXISTS", "NOT IN", "LEFT JOIN", "COUNT", "ausencia"],
    ),
    dict(
        id="sub-06",
        origen="Semana 10 · Ej. 6",
        titulo="Alumnos que nunca se inscribieron",
        dificultad=2,
        tipo="select",
        enunciado="Mostrar alumnos que **nunca se hayan inscripto a una comisión**. "
                  "Mostrá id, nombre y apellido.",
        solucion="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
WHERE a.id_alumno NOT IN (
    SELECT i.id_alumno
    FROM inscripcion_alumno_comision i
);""",
        alternativas=[
            dict(titulo="Con NOT EXISTS", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
WHERE NOT EXISTS (
    SELECT 1
    FROM inscripcion_alumno_comision i
    WHERE i.id_alumno = a.id_alumno
);"""),
            dict(titulo="Con LEFT JOIN … IS NULL", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
LEFT JOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno
WHERE i.id_inscripcion IS NULL;"""),
        ],
        columnas=[["id_alumno"], ["nombre", "apellido"]],
        casos_borde=True,
        pistas=[
            "«Nunca» = no existe ninguna fila en `inscripcion_alumno_comision` para ese alumno (sin importar el estado).",
            "Es el opuesto exacto del ejercicio 1: cambiá `IN` por `NOT IN` (o `EXISTS` por `NOT EXISTS`).",
            "Con `LEFT JOIN`, filtrá `WHERE i.id_inscripcion IS NULL`.",
        ],
        explicacion="""Es el **complemento** del ejercicio 1: alumnos que no aparecen en `inscripcion_alumno_comision`.

`NOT IN` es la forma más directa y acá es segura porque `id_alumno` en la tabla de inscripciones es NOT NULL. Recordá la trampa general: si la subconsulta devuelve aunque sea un `NULL`, `x NOT IN (..., NULL)` nunca es verdadero y el resultado queda **vacío**. `NOT EXISTS` no tiene ese problema, por eso es la opción más segura cuando no sabés si hay NULLs.

Una inscripción con estado `'Baja'` igual cuenta como «se inscribió alguna vez»: no hay que filtrar por estado.

Con los datos reales todos los alumnos tienen inscripciones (0 filas); el corrector agrega dos alumnos nuevos sin inscripciones (uno de ellos sí está en una carrera).""",
        errores_comunes=[
            "Confundir con `alumno_carrera`: estar en una carrera no es lo mismo que estar inscripto a una comisión.",
            "Filtrar por `estado = 'Baja'`: «se dio de baja» no es «nunca se inscribió».",
            "Usar `INNER JOIN` + `IS NULL`: siempre da vacío.",
        ],
        trampas=[
            dict(titulo="INNER JOIN con IS NULL", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a JOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno
WHERE i.id_inscripcion IS NULL;"""),
            dict(titulo="Sin carrera en vez de sin comisión", sql="""SELECT id_alumno, nombre, apellido
FROM alumnos
WHERE id_alumno NOT IN (SELECT id_alumno FROM alumno_carrera);"""),
            dict(titulo="Alumnos dados de baja", sql="""SELECT DISTINCT a.id_alumno, a.nombre, a.apellido
FROM alumnos a JOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno
WHERE i.estado = 'Baja';"""),
        ],
        tags=["NOT IN", "NOT EXISTS", "LEFT JOIN", "NULL", "ausencia"],
    ),
    dict(
        id="sub-07",
        origen="Semana 10 · Ej. 7",
        titulo="Asignaturas sin correlatividades",
        dificultad=2,
        tipo="select",
        enunciado="Detectar asignaturas que aún **no posean correlatividades asociadas**. Mostrá id y nombre.\n\n"
                  "Recordá: en `correlatividades` cada fila dice que `id_asignatura` tiene como correlativa "
                  "(requisito) a `id_asignatura_correlativa`.",
        solucion="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
WHERE a.id_asignatura NOT IN (
    SELECT co.id_asignatura
    FROM correlatividades co
);""",
        alternativas=[
            dict(titulo="Con NOT EXISTS", sql="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
WHERE NOT EXISTS (
    SELECT 1
    FROM correlatividades co
    WHERE co.id_asignatura = a.id_asignatura
);"""),
            dict(titulo="Con LEFT JOIN … IS NULL", sql="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
LEFT JOIN correlatividades co ON co.id_asignatura = a.id_asignatura
WHERE co.id IS NULL;"""),
        ],
        variantes=[
            dict(titulo="Tampoco es correlativa de otra (no figura en ninguna columna)", sql="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
WHERE NOT EXISTS (
    SELECT 1
    FROM correlatividades co
    WHERE co.id_asignatura = a.id_asignatura
       OR co.id_asignatura_correlativa = a.id_asignatura
);"""),
        ],
        columnas=[["id_asignatura"], ["nombre"]],
        casos_borde=True,
        pistas=[
            "«Poseer correlatividades» = tener requisitos, o sea, aparecer como `id_asignatura` en `correlatividades`.",
            "Buscás las asignaturas que **no** aparecen en esa columna.",
            "`WHERE id_asignatura NOT IN (SELECT id_asignatura FROM correlatividades)`.",
        ],
        explicacion="""`correlatividades` tiene **dos** FKs a `asignaturas`: la asignatura (`id_asignatura`) y su requisito (`id_asignatura_correlativa`). Lo importante es elegir la columna correcta.

«No posee correlatividades» = no tiene requisitos → no aparece como `id_asignatura`. Son 81 asignaturas.

Si comparás contra `id_asignatura_correlativa` estás respondiendo otra pregunta: «asignaturas que **no son requisito** de ninguna» (91 filas).

También se acepta la interpretación estricta: asignaturas que no figuran en **ninguna** de las dos columnas (21 filas). En `NOT EXISTS` eso se escribe con un `OR` dentro de la subconsulta.

`NOT IN` es seguro porque las dos columnas son NOT NULL.""",
        errores_comunes=[
            "Comparar contra `id_asignatura_correlativa`: eso da las asignaturas que no son requisito de ninguna otra.",
            "Usar `INNER JOIN` + `IS NULL`: siempre vacío.",
        ],
        trampas=[
            dict(titulo="INNER JOIN con IS NULL", sql="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a JOIN correlatividades co ON co.id_asignatura = a.id_asignatura
WHERE co.id IS NULL;"""),
            dict(titulo="Columna equivocada (las que no son requisito)", sql="""SELECT id_asignatura, nombre
FROM asignaturas
WHERE id_asignatura NOT IN (SELECT id_asignatura_correlativa FROM correlatividades);"""),
        ],
        tags=["NOT IN", "NOT EXISTS", "LEFT JOIN", "ausencia"],
    ),
    dict(
        id="sub-08",
        origen="Semana 10 · Ej. 8",
        titulo="Docentes con más de una comisión",
        dificultad=2,
        tipo="select",
        enunciado="Obtener docentes que tengan asignadas **más de una comisión**, y la cantidad de ellas. "
                  "Mostrá id, nombre, apellido y cantidad de comisiones.",
        solucion="""SELECT d.id_docente, d.nombre, d.apellido,
       COUNT(*) AS cantidad_comisiones
FROM docentes d
JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY d.id_docente, d.nombre, d.apellido
HAVING COUNT(*) > 1;""",
        alternativas=[
            dict(titulo="Con subconsulta correlacionada", sql="""SELECT d.id_docente, d.nombre, d.apellido,
       (SELECT COUNT(*) FROM comisiones c WHERE c.id_docente = d.id_docente) AS cantidad_comisiones
FROM docentes d
WHERE (SELECT COUNT(*) FROM comisiones c WHERE c.id_docente = d.id_docente) > 1;"""),
            dict(titulo="Con tabla derivada", sql="""SELECT d.id_docente, d.nombre, d.apellido, t.cantidad_comisiones
FROM docentes d
JOIN (
    SELECT id_docente, COUNT(*) AS cantidad_comisiones
    FROM comisiones
    GROUP BY id_docente
    HAVING COUNT(*) > 1
) t ON t.id_docente = d.id_docente;"""),
        ],
        columnas=[["id_docente", "cantidad_comisiones"], ["nombre", "apellido", "cantidad_comisiones"]],
        pistas=[
            "Necesitás contar comisiones **por docente**: `GROUP BY` el docente.",
            "La condición «más de una» es sobre el grupo, no sobre cada fila → va en `HAVING`, no en `WHERE`.",
            "`... GROUP BY d.id_docente, d.nombre, d.apellido HAVING COUNT(*) > 1`.",
        ],
        explicacion="""Primero se arma un grupo por docente (`GROUP BY d.id_docente, ...`) y se cuenta cuántas comisiones tiene. La condición sobre ese conteo va en **`HAVING`**, porque `WHERE` se evalúa fila por fila, **antes** de agrupar, y ahí todavía no existe `COUNT(*)` (error 1111 *Invalid use of group function*).

Agrupá por el **id** del docente: hay docentes con el mismo nombre y apellido, y agrupar solo por nombre los mezclaría en un único grupo.

La versión con subconsulta correlacionada calcula el conteo por cada docente dentro del `WHERE`. Es más larga, pero muestra que una subconsulta puede devolver un valor por fila.

Resultado: 197 docentes (solo 3 tienen una única comisión).""",
        errores_comunes=[
            "Poner `COUNT(*) > 1` en el `WHERE` → error 1111: las funciones de agregación van en `HAVING`.",
            "Agrupar por `nombre, apellido` sin el id: los docentes homónimos se suman como si fueran uno.",
            "Usar `>= 1` en vez de `> 1`: «más de una» excluye al que tiene exactamente una.",
        ],
        trampas=[
            dict(titulo="COUNT en el WHERE", sql="""SELECT d.id_docente, d.nombre, d.apellido, COUNT(*) AS cantidad
FROM docentes d JOIN comisiones c ON c.id_docente = d.id_docente
WHERE COUNT(*) > 1
GROUP BY d.id_docente, d.nombre, d.apellido;"""),
            dict(titulo="Agrupar por nombre y apellido", sql="""SELECT d.nombre, d.apellido, COUNT(*) AS cantidad
FROM docentes d JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY d.nombre, d.apellido
HAVING COUNT(*) > 1;"""),
            dict(titulo="Mayor o igual a 1", sql="""SELECT d.id_docente, d.nombre, d.apellido, COUNT(*) AS cantidad
FROM docentes d JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY d.id_docente, d.nombre, d.apellido
HAVING COUNT(*) >= 1;"""),
        ],
        tags=["GROUP BY", "HAVING", "subconsulta correlacionada", "COUNT"],
    ),
    dict(
        id="sub-09",
        origen="Semana 10 · Ej. 9",
        titulo="Comisiones sin alumnos inscriptos",
        dificultad=2,
        tipo="select",
        enunciado="Detectar comisiones que actualmente **no tengan alumnos inscriptos**. "
                  "Mostrá id de la comisión, año y cuatrimestre.",
        solucion="""SELECT c.id_comision, c.anio, c.cuatrimestre
FROM comisiones c
WHERE NOT EXISTS (
    SELECT 1
    FROM inscripcion_alumno_comision i
    WHERE i.id_comision = c.id_comision
);""",
        alternativas=[
            dict(titulo="Con NOT IN", sql="""SELECT id_comision, anio, cuatrimestre
FROM comisiones
WHERE id_comision NOT IN (SELECT id_comision FROM inscripcion_alumno_comision);"""),
            dict(titulo="Con LEFT JOIN … IS NULL", sql="""SELECT c.id_comision, c.anio, c.cuatrimestre
FROM comisiones c
LEFT JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
WHERE i.id_inscripcion IS NULL;"""),
            dict(titulo="Con LEFT JOIN + HAVING COUNT(columna) = 0", sql="""SELECT c.id_comision, c.anio, c.cuatrimestre
FROM comisiones c
LEFT JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.id_comision, c.anio, c.cuatrimestre
HAVING COUNT(i.id_inscripcion) = 0;"""),
        ],
        variantes=[
            dict(titulo="Sin inscriptos vigentes (ignorando las bajas)", sql="""SELECT c.id_comision, c.anio, c.cuatrimestre
FROM comisiones c
WHERE NOT EXISTS (
    SELECT 1
    FROM inscripcion_alumno_comision i
    WHERE i.id_comision = c.id_comision
      AND i.estado <> 'Baja'
);"""),
        ],
        columnas=[["id_comision"]],
        casos_borde=True,
        pistas=[
            "Es **ausencia**: comisiones que no aparecen en `inscripcion_alumno_comision`.",
            "Correlacioná por `id_comision`.",
            "`NOT EXISTS (SELECT 1 FROM inscripcion_alumno_comision i WHERE i.id_comision = c.id_comision)`.",
        ],
        explicacion="""Mismo patrón de ausencia, ahora desde `comisiones`. Las cuatro formas son equivalentes:

1. `NOT EXISTS` con subconsulta correlacionada (la más segura frente a NULLs).
2. `NOT IN` (segura acá: `id_comision` es NOT NULL en las inscripciones).
3. `LEFT JOIN ... WHERE i.id_inscripcion IS NULL`.
4. `LEFT JOIN ... GROUP BY ... HAVING COUNT(i.id_inscripcion) = 0`.

En la 4, `COUNT(columna)` ignora los NULL y por eso da 0 en las comisiones vacías; `COUNT(*)` daría 1.

**«Actualmente»** también puede leerse como «sin inscriptos que no se hayan dado de baja»; esa variante también se acepta (ahí la condición `estado <> 'Baja'` va **dentro** de la subconsulta).

Con los datos reales todas las comisiones tienen inscriptos: el corrector agrega dos comisiones nuevas vacías.""",
        errores_comunes=[
            "`LEFT JOIN` + `HAVING COUNT(*) = 0`: nunca da 0 por la fila con NULLs del LEFT JOIN.",
            "Usar `INNER JOIN` + `IS NULL`: siempre vacío.",
            "En la variante sin bajas, poner `estado <> 'Baja'` en el WHERE de un LEFT JOIN: elimina justo las filas con NULL.",
        ],
        trampas=[
            dict(titulo="INNER JOIN con IS NULL", sql="""SELECT c.id_comision, c.anio, c.cuatrimestre
FROM comisiones c JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
WHERE i.id_inscripcion IS NULL;"""),
            dict(titulo="LEFT JOIN + HAVING COUNT(*) = 0", sql="""SELECT c.id_comision, c.anio, c.cuatrimestre
FROM comisiones c
LEFT JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.id_comision, c.anio, c.cuatrimestre
HAVING COUNT(*) = 0;"""),
        ],
        tags=["NOT EXISTS", "NOT IN", "LEFT JOIN", "COUNT", "ausencia"],
    ),
    dict(
        id="sub-10",
        origen="Semana 10 · Ej. 10",
        titulo="Asignaturas con más comisiones que el promedio",
        dificultad=3,
        tipo="select",
        enunciado="Obtener aquellas asignaturas cuya **cantidad de comisiones abiertas sea superior al promedio general** "
                  "(de comisiones) de la universidad. Además del nombre de la asignatura, necesitan conocer "
                  "**cuántas comisiones** posee cada una.\n\n"
                  "Tomá como «abiertas» todas las comisiones registradas, y el promedio general como el promedio "
                  "de comisiones por asignatura.",
        solucion="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS cantidad_comisiones
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > (
    SELECT AVG(t.cantidad)
    FROM (
        SELECT COUNT(*) AS cantidad
        FROM comisiones
        GROUP BY id_asignatura
    ) t
);""",
        alternativas=[
            dict(titulo="Promedio como total / asignaturas con comisiones", sql="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS cantidad_comisiones
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > (
    SELECT COUNT(*) / COUNT(DISTINCT id_asignatura)
    FROM comisiones
);"""),
            dict(titulo="Con tabla derivada en el FROM", sql="""SELECT a.id_asignatura, a.nombre, t.cantidad_comisiones
FROM asignaturas a
JOIN (
    SELECT id_asignatura, COUNT(*) AS cantidad_comisiones
    FROM comisiones
    GROUP BY id_asignatura
) t ON t.id_asignatura = a.id_asignatura
WHERE t.cantidad_comisiones > (
    SELECT AVG(x.cantidad)
    FROM (SELECT COUNT(*) AS cantidad FROM comisiones GROUP BY id_asignatura) x
);"""),
        ],
        variantes=[
            dict(titulo="Promedio sobre TODAS las asignaturas (incluye las que no tienen comisiones)", sql="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS cantidad_comisiones
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > (SELECT COUNT(*) FROM comisiones) / (SELECT COUNT(*) FROM asignaturas);"""),
        ],
        columnas=[["nombre", "cantidad_comisiones"], ["id_asignatura", "cantidad_comisiones"]],
        casos_borde_sql="""INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo)
SELECT id_asignatura, id_docente, id_aula, 2027, cuatrimestre, cupo, tipo
FROM comisiones
WHERE anio = 2026;""",
        pistas=[
            "Partilo en dos: (1) cuántas comisiones tiene cada asignatura y (2) cuál es el promedio de esas cantidades.",
            "No podés anidar `AVG(COUNT(*))`. El promedio se calcula sobre una **tabla derivada**: `SELECT AVG(cantidad) FROM (SELECT COUNT(*) AS cantidad FROM comisiones GROUP BY id_asignatura) t`.",
            "Agrupá por asignatura y compará en el `HAVING`: `HAVING COUNT(*) > (subconsulta del promedio)`.",
        ],
        explicacion="""Hay dos niveles de agregación: contar comisiones **por asignatura** y después promediar **esos conteos**. MySQL no permite `AVG(COUNT(*))` (error 1111), así que el promedio sale de una tabla derivada:

```sql
SELECT AVG(t.cantidad)
FROM (SELECT COUNT(*) AS cantidad
      FROM comisiones GROUP BY id_asignatura) t
```

Esa subconsulta devuelve **un solo valor** (2,61), y se compara en el `HAVING` contra el conteo de cada grupo. Es equivalente a `COUNT(*) / COUNT(DISTINCT id_asignatura)` sobre `comisiones`.

Si el promedio se toma sobre las 500 asignaturas (contando las que no tienen comisiones) da 2,40; esa interpretación también se acepta.

**No escribas el promedio a mano** (`> 2.61`): si cambian los datos la consulta queda mal. El corrector la prueba también agregando las comisiones de 2027 (copia de las de 2026).""",
        errores_comunes=[
            "Escribir `HAVING COUNT(*) > AVG(COUNT(*))` → error 1111: no se pueden anidar funciones de agregación.",
            "Calcular el promedio a mano y pegarlo como número: deja de funcionar si cambian los datos.",
            "Olvidarse de mostrar la cantidad de comisiones (el enunciado la pide).",
        ],
        trampas=[
            dict(titulo="AVG(COUNT(*)) anidado", sql="""SELECT a.nombre, COUNT(*) AS cantidad
FROM asignaturas a JOIN comisiones c ON c.id_asignatura = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > AVG(COUNT(*));"""),
            dict(titulo="Promedio escrito a mano", sql="""SELECT a.nombre, COUNT(*) AS cantidad
FROM asignaturas a JOIN comisiones c ON c.id_asignatura = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > 2.61;"""),
            dict(titulo="Sin la cantidad de comisiones", sql="""SELECT a.nombre
FROM asignaturas a JOIN comisiones c ON c.id_asignatura = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > (SELECT AVG(t.cantidad) FROM (SELECT COUNT(*) AS cantidad FROM comisiones GROUP BY id_asignatura) t);"""),
        ],
        tags=["subconsulta escalar", "tabla derivada", "HAVING", "AVG", "GROUP BY"],
    ),

    # ------------------------------------------------------------------
    # Variantes nuevas (de menor a mayor dificultad)
    # ------------------------------------------------------------------
    dict(
        id="sub-n01",
        origen="Variante",
        titulo="Alumnos que no están en ninguna carrera",
        dificultad=2,
        tipo="select",
        enunciado="Mostrar los alumnos que **no están inscriptos en ninguna carrera**. "
                  "Mostrá id, nombre y apellido.",
        solucion="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
WHERE NOT EXISTS (
    SELECT 1
    FROM alumno_carrera ac
    WHERE ac.id_alumno = a.id_alumno
);""",
        alternativas=[
            dict(titulo="Con NOT IN", sql="""SELECT id_alumno, nombre, apellido
FROM alumnos
WHERE id_alumno NOT IN (SELECT id_alumno FROM alumno_carrera);"""),
            dict(titulo="Con LEFT JOIN … IS NULL", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
LEFT JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
WHERE ac.id IS NULL;"""),
        ],
        columnas=[["id_alumno"], ["nombre", "apellido"]],
        casos_borde=True,
        casos_borde_sql="""INSERT INTO alumnos (id_alumno, nombre, apellido, dni, fecha_nacimiento, email, telefono, fecha_ingreso)
VALUES (90003, 'Dario', 'Pendiente', '99000003', '2003-07-07', 'borde3@mail.com', '3510000003', '2026-03-01');
INSERT INTO alumno_carrera (id_alumno, id_carrera, fecha_inscripcion, estado)
VALUES (90003, 3, '2026-03-01', NULL);""",
        pistas=[
            "La pertenencia a una carrera está en `alumno_carrera` (tabla intermedia).",
            "Buscás alumnos cuyo `id_alumno` **no aparece** en `alumno_carrera`.",
            "Con `LEFT JOIN`, preguntá `IS NULL` sobre una columna que nunca es NULL cuando hay match: `ac.id` o `ac.id_alumno`.",
        ],
        explicacion="""Patrón de ausencia sobre la tabla intermedia `alumno_carrera`. Con los datos reales son **176 alumnos**.

Dos detalles que el corrector controla con casos borde:

- En el `NOT IN`, la subconsulta tiene que devolver **`id_alumno`**, no `id` (la PK de la intermedia). Los `id` de `alumno_carrera` numeran inscripciones, no alumnos: comparar contra ellos da un resultado sin sentido (21 filas).
- En el `LEFT JOIN`, el `IS NULL` va sobre una columna que **nunca** es NULL cuando hay match (`ac.id`, `ac.id_alumno`). `estado` admite NULL: un alumno con una carrera cargada sin estado aparecería como «sin carrera».

```sql
LEFT JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
WHERE ac.id IS NULL
```""",
        errores_comunes=[
            "`NOT IN (SELECT id FROM alumno_carrera)`: compara contra la PK de la intermedia, no contra el alumno.",
            "Hacer el `IS NULL` sobre `ac.estado`, que puede ser NULL aunque el alumno sí tenga carrera.",
            "Usar `INNER JOIN` + `IS NULL`: siempre vacío.",
        ],
        trampas=[
            dict(titulo="IS NULL sobre una columna que admite NULL", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
LEFT JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
WHERE ac.estado IS NULL;"""),
            dict(titulo="NOT IN contra la PK de la intermedia", sql="""SELECT id_alumno, nombre, apellido
FROM alumnos
WHERE id_alumno NOT IN (SELECT id FROM alumno_carrera);"""),
            dict(titulo="INNER JOIN con IS NULL", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
WHERE ac.id IS NULL;"""),
        ],
        tags=["NOT EXISTS", "NOT IN", "LEFT JOIN", "NULL", "ausencia"],
    ),
    dict(
        id="sub-n02",
        origen="Variante",
        titulo="Asignaturas que nunca tuvieron mesa final",
        dificultad=2,
        tipo="select",
        enunciado="Mostrar las asignaturas para las que **nunca se armó una mesa de examen final**. "
                  "Mostrá id y nombre.",
        solucion="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
WHERE NOT EXISTS (
    SELECT 1
    FROM mesas_finales m
    WHERE m.id_asignatura = a.id_asignatura
);""",
        alternativas=[
            dict(titulo="Con NOT IN", sql="""SELECT id_asignatura, nombre
FROM asignaturas
WHERE id_asignatura NOT IN (SELECT id_asignatura FROM mesas_finales);"""),
            dict(titulo="Con LEFT JOIN … IS NULL", sql="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
LEFT JOIN mesas_finales m ON m.id_asignatura = a.id_asignatura
WHERE m.id_mesa IS NULL;"""),
        ],
        columnas=[["id_asignatura"], ["nombre"]],
        casos_borde=True,
        pistas=[
            "Las mesas de final están en `mesas_finales`, con su `id_asignatura`.",
            "Es ausencia: asignaturas sin ninguna fila en `mesas_finales`.",
            "`WHERE NOT EXISTS (SELECT 1 FROM mesas_finales m WHERE m.id_asignatura = a.id_asignatura)`.",
        ],
        explicacion="""Mismo patrón de ausencia, con otra tabla «hija»: `mesas_finales`.

```sql
WHERE NOT EXISTS (SELECT 1 FROM mesas_finales m
                  WHERE m.id_asignatura = a.id_asignatura)
```

Con los datos reales son **5 asignaturas**. Fijate que no es lo mismo que «asignaturas sin comisiones» (41): que una asignatura no tenga cursada no impide que tenga mesas de final, y viceversa. Leé bien qué tabla registra la relación que te piden.

Las tres formas (`NOT EXISTS`, `NOT IN`, `LEFT JOIN … IS NULL`) son equivalentes acá porque `mesas_finales.id_asignatura` es NOT NULL.""",
        errores_comunes=[
            "Buscar contra `comisiones` en vez de `mesas_finales`: eso responde «asignaturas sin cursada».",
            "Usar `INNER JOIN` + `IS NULL`: siempre vacío.",
        ],
        trampas=[
            dict(titulo="INNER JOIN con IS NULL", sql="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a JOIN mesas_finales m ON m.id_asignatura = a.id_asignatura
WHERE m.id_mesa IS NULL;"""),
            dict(titulo="Sin comisiones en vez de sin mesas", sql="""SELECT id_asignatura, nombre
FROM asignaturas
WHERE id_asignatura NOT IN (SELECT id_asignatura FROM comisiones);"""),
        ],
        tags=["NOT EXISTS", "NOT IN", "LEFT JOIN", "ausencia"],
    ),
    dict(
        id="sub-n03",
        origen="Variante",
        titulo="Asignaturas que son correlativas de otra",
        dificultad=2,
        tipo="select",
        enunciado="Mostrar las asignaturas que **son correlativas (requisito) de alguna otra** asignatura. "
                  "Mostrá id y nombre, cada una una sola vez.\n\n"
                  "Recordá: en `correlatividades`, `id_asignatura_correlativa` es el requisito de `id_asignatura`.",
        solucion="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
WHERE a.id_asignatura IN (
    SELECT co.id_asignatura_correlativa
    FROM correlatividades co
);""",
        alternativas=[
            dict(titulo="Con EXISTS", sql="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
WHERE EXISTS (
    SELECT 1
    FROM correlatividades co
    WHERE co.id_asignatura_correlativa = a.id_asignatura
);"""),
            dict(titulo="Con JOIN + DISTINCT", sql="""SELECT DISTINCT a.id_asignatura, a.nombre
FROM asignaturas a
JOIN correlatividades co ON co.id_asignatura_correlativa = a.id_asignatura;"""),
        ],
        columnas=[["id_asignatura"], ["nombre"]],
        casos_borde=True,
        pistas=[
            "Te interesa la columna `id_asignatura_correlativa` de `correlatividades`.",
            "Una asignatura puede ser requisito de varias: la subconsulta devuelve **muchas filas** → usá `IN`, no `=`.",
            "`WHERE id_asignatura IN (SELECT id_asignatura_correlativa FROM correlatividades)`.",
        ],
        explicacion="""`IN (subconsulta)` compara contra **una lista** de valores. Acá la lista son todos los ids que aparecen como requisito.

Si escribís `= (SELECT ...)` y la subconsulta devuelve más de una fila, MySQL da el error **1242** (*Subquery returns more than 1 row*): `=` solo sirve con subconsultas que devuelven un único valor (por ejemplo un `MAX` o un `AVG`).

Con `JOIN`, una asignatura que es requisito de varias aparece repetida → `DISTINCT`. Con `IN`/`EXISTS` no pasa, porque solo filtran.

Ojo con la columna: `id_asignatura` son las asignaturas que **tienen** requisitos (otra pregunta). Resultado: 409 asignaturas.""",
        errores_comunes=[
            "Usar `=` con una subconsulta de varias filas → error 1242. Para listas va `IN`.",
            "Usar la columna `id_asignatura`: eso da las asignaturas que tienen correlativas, no las que son correlativas.",
            "`JOIN` sin `DISTINCT`: repite la asignatura por cada materia que la exige.",
        ],
        trampas=[
            dict(titulo="= con una subconsulta de varias filas", sql="""SELECT id_asignatura, nombre
FROM asignaturas
WHERE id_asignatura = (SELECT id_asignatura_correlativa FROM correlatividades);"""),
            dict(titulo="Columna equivocada (las que tienen requisitos)", sql="""SELECT id_asignatura, nombre
FROM asignaturas
WHERE id_asignatura IN (SELECT id_asignatura FROM correlatividades);"""),
            dict(titulo="JOIN sin DISTINCT", sql="""SELECT a.id_asignatura, a.nombre
FROM asignaturas a
JOIN correlatividades co ON co.id_asignatura_correlativa = a.id_asignatura;"""),
        ],
        tags=["IN", "EXISTS", "subconsulta", "presencia"],
    ),
    dict(
        id="sub-n04",
        origen="Variante",
        titulo="Docentes que ganan más que el promedio",
        dificultad=2,
        tipo="select",
        enunciado="Mostrar los docentes cuyo **salario base es mayor al promedio general** de salarios de todos los docentes. "
                  "Mostrá id, nombre, apellido y salario.",
        solucion="""SELECT d.id_docente, d.nombre, d.apellido, d.salario_base
FROM docentes d
WHERE d.salario_base > (
    SELECT AVG(salario_base)
    FROM docentes
);""",
        alternativas=[
            dict(titulo="Con JOIN a una tabla derivada", sql="""SELECT d.id_docente, d.nombre, d.apellido, d.salario_base
FROM docentes d
JOIN (SELECT AVG(salario_base) AS promedio FROM docentes) p
  ON d.salario_base > p.promedio;"""),
        ],
        columnas=[["id_docente"], ["nombre", "apellido"]],
        pistas=[
            "Primero escribí aparte la consulta del promedio: `SELECT AVG(salario_base) FROM docentes`.",
            "Esa consulta devuelve un único valor: podés usarla como **subconsulta escalar** en el `WHERE`.",
            "`WHERE salario_base > (SELECT AVG(salario_base) FROM docentes)`.",
        ],
        explicacion="""No se puede escribir `WHERE salario_base > AVG(salario_base)`: el `WHERE` evalúa **una fila por vez** y ahí no existe el promedio del conjunto (error 1111).

La solución es calcular el promedio en una **subconsulta escalar** (devuelve una fila y una columna) y comparar contra ella:

```sql
WHERE d.salario_base > (SELECT AVG(salario_base) FROM docentes)
```

Tampoco sirve `GROUP BY id_docente HAVING salario_base > AVG(salario_base)`: cada grupo tiene un solo docente, así que su «promedio» es su propio salario y nunca es mayor.

Resultado: 101 de 200 docentes. Si comparás contra el promedio de **su departamento** (subconsulta correlacionada) da otro resultado: es otra pregunta.""",
        errores_comunes=[
            "`WHERE salario_base > AVG(salario_base)` → error 1111.",
            "Agrupar por docente y comparar en el HAVING: el promedio de un grupo de una fila es el mismo valor.",
            "Comparar con el promedio del propio departamento cuando se pide el promedio general.",
        ],
        trampas=[
            dict(titulo="AVG en el WHERE", sql="""SELECT id_docente, nombre, apellido, salario_base
FROM docentes
WHERE salario_base > AVG(salario_base);"""),
            dict(titulo="HAVING agrupando por docente", sql="""SELECT id_docente, nombre, apellido, salario_base
FROM docentes
GROUP BY id_docente, nombre, apellido, salario_base
HAVING salario_base > AVG(salario_base);"""),
            dict(titulo="Promedio de su departamento", sql="""SELECT d.id_docente, d.nombre, d.apellido, d.salario_base
FROM docentes d
WHERE d.salario_base > (SELECT AVG(x.salario_base) FROM docentes x
                        WHERE x.id_departamento = d.id_departamento);"""),
        ],
        tags=["subconsulta escalar", "AVG", "WHERE"],
    ),
    dict(
        id="sub-n05",
        origen="Variante",
        titulo="Aula(s) con mayor capacidad",
        dificultad=2,
        tipo="select",
        enunciado="Mostrar el aula (o las aulas, si hay empate) con **mayor capacidad**. "
                  "Mostrá id, nombre y capacidad.",
        solucion="""SELECT au.id_aula, au.nombre, au.capacidad
FROM aulas au
WHERE au.capacidad = (
    SELECT MAX(capacidad)
    FROM aulas
);""",
        alternativas=[
            dict(titulo="Con >= ALL", sql="""SELECT id_aula, nombre, capacidad
FROM aulas
WHERE capacidad >= ALL (SELECT capacidad FROM aulas);"""),
            dict(titulo="Con NOT EXISTS (no hay otra más grande)", sql="""SELECT au.id_aula, au.nombre, au.capacidad
FROM aulas au
WHERE NOT EXISTS (
    SELECT 1
    FROM aulas otra
    WHERE otra.capacidad > au.capacidad
);"""),
        ],
        columnas=[["id_aula"], ["nombre"]],
        casos_borde_sql="""INSERT INTO aulas (id_aula, nombre, capacidad, tipo)
VALUES (903, 'Aula Magna B', 60, 'normal');""",
        pistas=[
            "El valor máximo se obtiene con `SELECT MAX(capacidad) FROM aulas`.",
            "Usalo como subconsulta escalar y quedate con las aulas cuya capacidad es **igual** a ese máximo.",
            "No uses `ORDER BY ... LIMIT 1`: si hay dos aulas empatadas, perdés una.",
        ],
        explicacion="""La subconsulta `(SELECT MAX(capacidad) FROM aulas)` devuelve un único número (60), y el `WHERE` se queda con **todas** las aulas que lo tienen:

```sql
WHERE au.capacidad = (SELECT MAX(capacidad) FROM aulas)
```

¿Por qué no `ORDER BY capacidad DESC LIMIT 1`? Porque si hay **empate** devuelve una sola aula al azar. El corrector lo prueba agregando otra aula de 60.

Tampoco funciona `WHERE capacidad = MAX(capacidad)` (error 1111: agregación en el WHERE) ni `SELECT nombre, MAX(capacidad) FROM aulas` (error 1140: mezcla una columna normal con una agregada sin `GROUP BY`; y aunque MySQL lo dejara, el nombre no tendría por qué corresponder al máximo).""",
        errores_comunes=[
            "`ORDER BY capacidad DESC LIMIT 1`: ignora los empates.",
            "`WHERE capacidad = MAX(capacidad)` → error 1111.",
            "`SELECT nombre, MAX(capacidad) FROM aulas` → error 1140 (columna no agregada sin GROUP BY).",
        ],
        trampas=[
            dict(titulo="ORDER BY + LIMIT 1", sql="""SELECT id_aula, nombre, capacidad
FROM aulas
ORDER BY capacidad DESC
LIMIT 1;"""),
            dict(titulo="MAX en el WHERE", sql="""SELECT id_aula, nombre, capacidad
FROM aulas
WHERE capacidad = MAX(capacidad);"""),
            dict(titulo="Columna suelta con MAX", sql="""SELECT nombre, MAX(capacidad)
FROM aulas;"""),
        ],
        tags=["subconsulta escalar", "MAX", "ALL", "empates"],
    ),
    dict(
        id="sub-n06",
        origen="Variante",
        titulo="Departamentos sin docentes",
        dificultad=2,
        tipo="select",
        enunciado="Mostrar los departamentos que **no tienen ningún docente**. Mostrá id y nombre.\n\n"
                  "Ojo: `docentes.id_departamento` admite NULL (puede haber docentes todavía sin departamento asignado).",
        solucion="""SELECT dep.id_departamento, dep.nombre
FROM departamentos dep
WHERE NOT EXISTS (
    SELECT 1
    FROM docentes d
    WHERE d.id_departamento = dep.id_departamento
);""",
        alternativas=[
            dict(titulo="Con LEFT JOIN … IS NULL", sql="""SELECT dep.id_departamento, dep.nombre
FROM departamentos dep
LEFT JOIN docentes d ON d.id_departamento = dep.id_departamento
WHERE d.id_docente IS NULL;"""),
            dict(titulo="Con NOT IN (filtrando los NULL)", sql="""SELECT id_departamento, nombre
FROM departamentos
WHERE id_departamento NOT IN (
    SELECT id_departamento
    FROM docentes
    WHERE id_departamento IS NOT NULL
);"""),
        ],
        columnas=[["id_departamento"], ["nombre"]],
        casos_borde=True,
        casos_borde_sql="""INSERT INTO docentes (id_docente, nombre, apellido, email, fecha_ingreso, salario_base, id_departamento)
VALUES (9003, 'Franco', 'Sindepto', 'borde.doc3@universidad.edu', '2026-03-01', 240000.00, NULL);""",
        pistas=[
            "Es ausencia: departamentos para los que no existe ningún docente con ese `id_departamento`.",
            "Si usás `NOT IN`, pensá qué pasa si la subconsulta devuelve un `NULL`.",
            "`NOT EXISTS` no tiene problemas con NULL. Con `NOT IN`, agregá `WHERE id_departamento IS NOT NULL` en la subconsulta.",
        ],
        explicacion="""Este es el ejemplo clásico de la **trampa de `NOT IN` con NULL**.

`x NOT IN (1, 2, NULL)` equivale a `x <> 1 AND x <> 2 AND x <> NULL`. Comparar con NULL da *desconocido*, así que la condición **nunca** es verdadera y la consulta devuelve **vacío**, aunque haya departamentos sin docentes.

Como `docentes.id_departamento` admite NULL, basta un docente sin departamento para romper el `NOT IN`. Soluciones:

- `NOT EXISTS` (recomendado): compara fila a fila con `=` y los NULL simplemente no coinciden.
- `LEFT JOIN … WHERE d.id_docente IS NULL`.
- `NOT IN (... WHERE id_departamento IS NOT NULL)`.

Con los datos reales todos los departamentos tienen docentes; el corrector agrega el departamento «Artes» (sin docentes, pero con una carrera) y un docente sin departamento.""",
        errores_comunes=[
            "`NOT IN` sin filtrar los NULL de la subconsulta: con un solo NULL el resultado queda vacío.",
            "Buscar contra `carreras` o `asignaturas`: un departamento puede tener carreras y ningún docente.",
            "Usar `INNER JOIN` + `IS NULL`: siempre vacío.",
        ],
        trampas=[
            dict(titulo="NOT IN sin filtrar los NULL", sql="""SELECT id_departamento, nombre
FROM departamentos
WHERE id_departamento NOT IN (SELECT id_departamento FROM docentes);"""),
            dict(titulo="Tabla equivocada (carreras)", sql="""SELECT id_departamento, nombre
FROM departamentos
WHERE id_departamento NOT IN (SELECT id_departamento FROM carreras WHERE id_departamento IS NOT NULL);"""),
            dict(titulo="INNER JOIN con IS NULL", sql="""SELECT dep.id_departamento, dep.nombre
FROM departamentos dep JOIN docentes d ON d.id_departamento = dep.id_departamento
WHERE d.id_docente IS NULL;"""),
        ],
        tags=["NOT EXISTS", "NOT IN", "NULL", "LEFT JOIN", "ausencia"],
    ),
    dict(
        id="sub-n07",
        origen="Variante",
        titulo="Alumnos con promedio superior al general",
        dificultad=3,
        tipo="select",
        enunciado="Mostrar los alumnos cuyo **promedio de notas supera el promedio general de todas las notas** "
                  "(tabla `notas`). Mostrá id, nombre, apellido y el promedio del alumno.",
        solucion="""SELECT a.id_alumno, a.nombre, a.apellido,
       ROUND(AVG(n.nota), 2) AS promedio
FROM alumnos a
JOIN notas n ON n.id_alumno = a.id_alumno
GROUP BY a.id_alumno, a.nombre, a.apellido
HAVING AVG(n.nota) > (
    SELECT AVG(nota)
    FROM notas
);""",
        alternativas=[
            dict(titulo="Con subconsulta correlacionada en el WHERE", sql="""SELECT a.id_alumno, a.nombre, a.apellido,
       (SELECT ROUND(AVG(n.nota), 2) FROM notas n WHERE n.id_alumno = a.id_alumno) AS promedio
FROM alumnos a
WHERE (SELECT AVG(n.nota) FROM notas n WHERE n.id_alumno = a.id_alumno)
      > (SELECT AVG(nota) FROM notas);"""),
            dict(titulo="Con tabla derivada", sql="""SELECT a.id_alumno, a.nombre, a.apellido, ROUND(p.promedio, 2) AS promedio
FROM alumnos a
JOIN (SELECT id_alumno, AVG(nota) AS promedio FROM notas GROUP BY id_alumno) p
  ON p.id_alumno = a.id_alumno
WHERE p.promedio > (SELECT AVG(nota) FROM notas);"""),
        ],
        columnas=[["id_alumno"], ["nombre", "apellido"]],
        pistas=[
            "Hay dos promedios: el de **cada alumno** (`AVG` con `GROUP BY` alumno) y el **general** (`AVG` de toda la tabla).",
            "El general es una subconsulta escalar: `(SELECT AVG(nota) FROM notas)`.",
            "La comparación es sobre el promedio del grupo → va en el `HAVING`: `HAVING AVG(n.nota) > (SELECT AVG(nota) FROM notas)`.",
        ],
        explicacion="""Se combinan las dos ideas de la sección: **agrupar** para obtener el promedio de cada alumno y una **subconsulta escalar** para el promedio general (5,50).

```sql
GROUP BY a.id_alumno, a.nombre, a.apellido
HAVING AVG(n.nota) > (SELECT AVG(nota) FROM notas)
```

La comparación va en el `HAVING` porque usa `AVG(n.nota)`, que existe recién después de agrupar.

Cuidado: «promedio general de todas las notas» **no** es el promedio de los promedios de cada alumno. Los alumnos con más notas pesan más en el promedio general; con estos datos la diferencia cambia el resultado (499 vs 500 alumnos).

Tampoco sirve filtrar `WHERE n.nota > (promedio)` antes de agrupar: eso se queda con las notas altas de **todos** los alumnos.""",
        errores_comunes=[
            "Comparar contra el promedio de los promedios por alumno: no es el promedio general de todas las notas.",
            "Filtrar `WHERE nota > (SELECT AVG(nota) ...)` antes de agrupar: devuelve casi todos los alumnos.",
            "Agrupar solo por nombre y apellido: hay muchísimos alumnos homónimos.",
        ],
        trampas=[
            dict(titulo="Promedio de los promedios", sql="""SELECT a.id_alumno, a.nombre, a.apellido, AVG(n.nota) AS promedio
FROM alumnos a JOIN notas n ON n.id_alumno = a.id_alumno
GROUP BY a.id_alumno, a.nombre, a.apellido
HAVING AVG(n.nota) > (SELECT AVG(p) FROM (SELECT AVG(nota) AS p FROM notas GROUP BY id_alumno) t);"""),
            dict(titulo="Filtrar notas antes de agrupar", sql="""SELECT a.id_alumno, a.nombre, a.apellido, AVG(n.nota) AS promedio
FROM alumnos a JOIN notas n ON n.id_alumno = a.id_alumno
WHERE n.nota > (SELECT AVG(nota) FROM notas)
GROUP BY a.id_alumno, a.nombre, a.apellido;"""),
        ],
        tags=["subconsulta escalar", "HAVING", "AVG", "GROUP BY"],
    ),
    dict(
        id="sub-n08",
        origen="Variante",
        titulo="Comisiones con más inscriptos que cupo",
        dificultad=3,
        tipo="select",
        enunciado="Detectar las comisiones en las que la **cantidad de inscriptos supera el cupo**. "
                  "Mostrá id de la comisión, su cupo y la cantidad de inscriptos.",
        solucion="""SELECT c.id_comision, c.cupo,
       (SELECT COUNT(*)
        FROM inscripcion_alumno_comision i
        WHERE i.id_comision = c.id_comision) AS inscriptos
FROM comisiones c
WHERE (SELECT COUNT(*)
       FROM inscripcion_alumno_comision i
       WHERE i.id_comision = c.id_comision) > c.cupo;""",
        alternativas=[
            dict(titulo="Con JOIN + GROUP BY + HAVING", sql="""SELECT c.id_comision, c.cupo, COUNT(*) AS inscriptos
FROM comisiones c
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.id_comision, c.cupo
HAVING COUNT(*) > c.cupo;"""),
        ],
        variantes=[
            dict(titulo="Sin contar las inscripciones dadas de baja", sql="""SELECT c.id_comision, c.cupo, COUNT(*) AS inscriptos
FROM comisiones c
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
WHERE i.estado <> 'Baja'
GROUP BY c.id_comision, c.cupo
HAVING COUNT(*) > c.cupo;"""),
        ],
        columnas=[["id_comision", "inscriptos"]],
        casos_borde_sql="""INSERT INTO comisiones (id_comision, id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo) VALUES
 (90011, 3, 3, 3, 2026, 2, 3, 'practica'),
 (90012, 4, 4, 4, 2026, 2, 4, 'practica');
INSERT INTO inscripcion_alumno_comision (id_alumno, id_comision, fecha_inscripcion, estado)
SELECT id_alumno, 90011, '2026-08-01', 'Cursa' FROM alumnos WHERE id_alumno BETWEEN 1 AND 4;
INSERT INTO inscripcion_alumno_comision (id_alumno, id_comision, fecha_inscripcion, estado)
SELECT id_alumno, 90012, '2026-08-01', 'Cursa' FROM alumnos WHERE id_alumno BETWEEN 5 AND 8;""",
        pistas=[
            "Para cada comisión necesitás contar sus inscriptos y compararlo con **su propio** `cupo`.",
            "Una subconsulta correlacionada puede devolver ese conteo: `(SELECT COUNT(*) FROM inscripcion_alumno_comision i WHERE i.id_comision = c.id_comision)`.",
            "Usá esa subconsulta en el `WHERE` con `> c.cupo` (o agrupá y compará en el `HAVING`). «Supera» es `>`, no `>=`.",
        ],
        explicacion="""La subconsulta **correlacionada** se recalcula para cada comisión `c` y devuelve cuántos inscriptos tiene; después se compara con el cupo de esa misma fila:

```sql
WHERE (SELECT COUNT(*) FROM inscripcion_alumno_comision i
       WHERE i.id_comision = c.id_comision) > c.cupo
```

La alternativa con `JOIN` + `GROUP BY c.id_comision, c.cupo` + `HAVING COUNT(*) > c.cupo` es equivalente. `cupo` tiene que estar en el `GROUP BY` (o depender de la PK agrupada) para poder usarlo en el `HAVING`.

Con los datos reales solo la comisión 1163 está sobrevendida (32 inscriptos, cupo 27). El corrector agrega una comisión que supera el cupo y otra que lo iguala exactamente (esa **no** supera).

Si no contás las bajas, también se acepta.""",
        errores_comunes=[
            "Usar `>=`: una comisión con exactamente tantos inscriptos como cupo no lo supera.",
            "Poner `COUNT(*) > cupo` en el `WHERE` de una consulta agrupada → error 1111.",
            "Comparar contra la capacidad del aula: el enunciado habla del `cupo` de la comisión.",
        ],
        trampas=[
            dict(titulo="Mayor o igual al cupo", sql="""SELECT c.id_comision, c.cupo, COUNT(*) AS inscriptos
FROM comisiones c JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.id_comision, c.cupo
HAVING COUNT(*) >= c.cupo;"""),
            dict(titulo="COUNT en el WHERE", sql="""SELECT c.id_comision, c.cupo, COUNT(*) AS inscriptos
FROM comisiones c JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
WHERE COUNT(*) > c.cupo
GROUP BY c.id_comision, c.cupo;"""),
            dict(titulo="Contra la capacidad del aula", sql="""SELECT c.id_comision, c.cupo, COUNT(*) AS inscriptos
FROM comisiones c
JOIN aulas au ON au.id_aula = c.id_aula
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.id_comision, c.cupo, au.capacidad
HAVING COUNT(*) > au.capacidad;"""),
        ],
        tags=["subconsulta correlacionada", "COUNT", "HAVING"],
    ),
    dict(
        id="sub-n09",
        origen="Variante",
        titulo="Salario mayor que todos los de Humanidades",
        dificultad=3,
        tipo="select",
        enunciado="Mostrar los docentes cuyo salario base es **mayor que el de TODOS los docentes del departamento "
                  "'Humanidades'**. Buscá el departamento por su nombre. Mostrá id, nombre, apellido y salario.",
        solucion="""SELECT d.id_docente, d.nombre, d.apellido, d.salario_base
FROM docentes d
WHERE d.salario_base > ALL (
    SELECT h.salario_base
    FROM docentes h
    JOIN departamentos dep ON dep.id_departamento = h.id_departamento
    WHERE dep.nombre = 'Humanidades'
);""",
        alternativas=[
            dict(titulo="Comparando con el MAX", sql="""SELECT d.id_docente, d.nombre, d.apellido, d.salario_base
FROM docentes d
WHERE d.salario_base > (
    SELECT MAX(h.salario_base)
    FROM docentes h
    JOIN departamentos dep ON dep.id_departamento = h.id_departamento
    WHERE dep.nombre = 'Humanidades'
);"""),
            dict(titulo="Con subconsultas anidadas (sin JOIN)", sql="""SELECT id_docente, nombre, apellido, salario_base
FROM docentes
WHERE salario_base > ALL (
    SELECT salario_base
    FROM docentes
    WHERE id_departamento = (SELECT id_departamento FROM departamentos WHERE nombre = 'Humanidades')
);"""),
        ],
        columnas=[["id_docente"], ["nombre", "apellido"]],
        casos_borde_sql="""INSERT INTO docentes (id_docente, nombre, apellido, email, fecha_ingreso, salario_base, id_departamento)
VALUES (9101, 'Gabriela', 'Altosueldo', 'borde.doc9101@universidad.edu', '2026-02-01', 429000.00, 5);""",
        pistas=[
            "Primero escribí la subconsulta que devuelve los salarios de los docentes de Humanidades (JOIN con `departamentos`).",
            "«Mayor que todos» se escribe `> ALL (subconsulta)`. «Mayor que alguno» sería `> ANY`.",
            "Equivale a ser mayor que el **máximo**: `> (SELECT MAX(salario_base) ...)`.",
        ],
        explicacion="""`> ALL (subconsulta)` es verdadero cuando el valor supera a **cada uno** de los valores de la lista. Ser mayor que todos = ser mayor que el máximo, por eso la alternativa con `MAX` da lo mismo.

`> ANY` (o `> SOME`) es «mayor que al menos uno» = mayor que el mínimo: devuelve casi todos los docentes.

Diferencia sutil: si la subconsulta no devuelve filas (un departamento sin docentes), `> ALL` es **verdadero para todos**, mientras que `> (SELECT MAX ...)` compara contra NULL y no devuelve nada.

Con los datos reales hay un solo docente que cumple; por eso `ORDER BY salario_base DESC LIMIT 1` parece andar, pero no responde la pregunta. El corrector agrega otro docente que también supera a Humanidades.""",
        errores_comunes=[
            "Usar `> ANY`: alcanza con superar al que menos gana de Humanidades.",
            "Comparar con el promedio de Humanidades en vez de con todos.",
            "Usar `ORDER BY ... LIMIT 1`: devuelve el que más gana, no los que superan a Humanidades.",
        ],
        trampas=[
            dict(titulo="> ANY en vez de > ALL", sql="""SELECT d.id_docente, d.nombre, d.apellido, d.salario_base
FROM docentes d
WHERE d.salario_base > ANY (
    SELECT h.salario_base FROM docentes h
    JOIN departamentos dep ON dep.id_departamento = h.id_departamento
    WHERE dep.nombre = 'Humanidades');"""),
            dict(titulo="Contra el promedio de Humanidades", sql="""SELECT d.id_docente, d.nombre, d.apellido, d.salario_base
FROM docentes d
WHERE d.salario_base > (
    SELECT AVG(h.salario_base) FROM docentes h
    JOIN departamentos dep ON dep.id_departamento = h.id_departamento
    WHERE dep.nombre = 'Humanidades');"""),
            dict(titulo="El que más gana (LIMIT 1)", sql="""SELECT id_docente, nombre, apellido, salario_base
FROM docentes
ORDER BY salario_base DESC
LIMIT 1;"""),
        ],
        tags=["ALL", "ANY", "MAX", "subconsulta"],
    ),
    dict(
        id="sub-n10",
        origen="Variante",
        titulo="Rindieron finales pero nunca aprobaron",
        dificultad=3,
        tipo="select",
        enunciado="Mostrar los alumnos que **rindieron algún examen final pero nunca aprobaron ninguno**. "
                  "Mostrá id, nombre y apellido.\n\n"
                  "Consideramos que un alumno **rindió** si tiene alguna inscripción a final con estado `'aprobado'` o "
                  "`'desaprobado'`, y que **aprobó** si alguna tiene estado `'aprobado'`.",
        solucion="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
WHERE EXISTS (
    SELECT 1
    FROM inscripciones_finales f
    WHERE f.id_alumno = a.id_alumno
      AND f.estado IN ('aprobado', 'desaprobado')
)
AND NOT EXISTS (
    SELECT 1
    FROM inscripciones_finales f
    WHERE f.id_alumno = a.id_alumno
      AND f.estado = 'aprobado'
);""",
        alternativas=[
            dict(titulo="Con IN + NOT IN", sql="""SELECT id_alumno, nombre, apellido
FROM alumnos
WHERE id_alumno IN (SELECT id_alumno FROM inscripciones_finales
                    WHERE estado IN ('aprobado', 'desaprobado'))
  AND id_alumno NOT IN (SELECT id_alumno FROM inscripciones_finales
                        WHERE estado = 'aprobado');"""),
            dict(titulo="Con GROUP BY + HAVING", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
JOIN inscripciones_finales f ON f.id_alumno = a.id_alumno
WHERE f.estado IN ('aprobado', 'desaprobado')
GROUP BY a.id_alumno, a.nombre, a.apellido
HAVING SUM(f.estado = 'aprobado') = 0;"""),
        ],
        columnas=[["id_alumno"], ["nombre", "apellido"]],
        casos_borde=True,
        pistas=[
            "Son **dos** condiciones sobre la misma tabla: que exista una inscripción rendida y que NO exista ninguna aprobada.",
            "«Nunca aprobó» no es «tiene alguna desaprobada»: un alumno puede tener desaprobados y también aprobados.",
            "`WHERE EXISTS (... estado IN ('aprobado','desaprobado')) AND NOT EXISTS (... estado = 'aprobado')`.",
        ],
        explicacion="""Se combinan **presencia** y **ausencia** sobre la misma tabla, cada una con su subconsulta correlacionada:

- `EXISTS (... estado IN ('aprobado','desaprobado'))` → rindió al menos uno.
- `NOT EXISTS (... estado = 'aprobado')` → no hay ninguno aprobado.

El error típico es escribir `WHERE f.estado = 'desaprobado'` (o `<> 'aprobado'`) con un `JOIN`: eso devuelve los alumnos que tienen **alguna** fila desaprobada, aunque también tengan aprobadas. «Nunca» siempre pide mirar **todas** las filas del alumno → `NOT EXISTS`, `NOT IN` o un `HAVING` sobre el grupo completo.

Y el `EXISTS` no sobra: sin él aparecerían también los alumnos que nunca se anotaron a un final (el corrector agrega alumnos así). Resultado con los datos reales: 13 alumnos.""",
        errores_comunes=[
            "Filtrar `estado = 'desaprobado'` con JOIN: trae alumnos que también aprobaron otros finales.",
            "Olvidarse del `EXISTS`: aparecen alumnos que nunca rindieron.",
            "Usar `nota < 4`: en estos datos la nota no es coherente con el estado; el enunciado define todo por estado.",
        ],
        trampas=[
            dict(titulo="Alguna desaprobada (no «nunca aprobó»)", sql="""SELECT DISTINCT a.id_alumno, a.nombre, a.apellido
FROM alumnos a JOIN inscripciones_finales f ON f.id_alumno = a.id_alumno
WHERE f.estado = 'desaprobado';"""),
            dict(titulo="Solo NOT EXISTS (sin exigir que haya rendido)", sql="""SELECT a.id_alumno, a.nombre, a.apellido
FROM alumnos a
WHERE NOT EXISTS (SELECT 1 FROM inscripciones_finales f
                  WHERE f.id_alumno = a.id_alumno AND f.estado = 'aprobado');"""),
            dict(titulo="Distinto de aprobado con JOIN", sql="""SELECT DISTINCT a.id_alumno, a.nombre, a.apellido
FROM alumnos a JOIN inscripciones_finales f ON f.id_alumno = a.id_alumno
WHERE f.estado <> 'aprobado';"""),
        ],
        tags=["EXISTS", "NOT EXISTS", "presencia", "ausencia"],
    ),
    dict(
        id="sub-n11",
        origen="Variante",
        titulo="Docentes con comisiones en 2026 y no en 2025",
        dificultad=3,
        tipo="select",
        enunciado="Mostrar los docentes que **tienen comisiones en 2026 pero ninguna en 2025**. "
                  "Mostrá id, nombre y apellido.",
        solucion="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
WHERE d.id_docente IN (
    SELECT c.id_docente
    FROM comisiones c
    WHERE c.anio = 2026
)
AND d.id_docente NOT IN (
    SELECT c.id_docente
    FROM comisiones c
    WHERE c.anio = 2025
);""",
        alternativas=[
            dict(titulo="Con EXISTS + NOT EXISTS", sql="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
WHERE EXISTS (SELECT 1 FROM comisiones c
              WHERE c.id_docente = d.id_docente AND c.anio = 2026)
  AND NOT EXISTS (SELECT 1 FROM comisiones c
                  WHERE c.id_docente = d.id_docente AND c.anio = 2025);"""),
            dict(titulo="Con LEFT JOIN (año en el ON)", sql="""SELECT DISTINCT d.id_docente, d.nombre, d.apellido
FROM docentes d
JOIN comisiones c26 ON c26.id_docente = d.id_docente AND c26.anio = 2026
LEFT JOIN comisiones c25 ON c25.id_docente = d.id_docente AND c25.anio = 2025
WHERE c25.id_comision IS NULL;"""),
            dict(titulo="Con GROUP BY + HAVING", sql="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY d.id_docente, d.nombre, d.apellido
HAVING SUM(c.anio = 2026) > 0
   AND SUM(c.anio = 2025) = 0;"""),
        ],
        columnas=[["id_docente"], ["nombre", "apellido"]],
        casos_borde=True,
        pistas=[
            "Una sola fila de `comisiones` no puede ser de 2026 y de 2025 a la vez: son condiciones sobre **distintas** filas del docente.",
            "Usá una subconsulta para «tiene en 2026» y otra para «no tiene en 2025».",
            "`WHERE id_docente IN (... WHERE anio = 2026) AND id_docente NOT IN (... WHERE anio = 2025)`.",
        ],
        explicacion="""La trampa es pensar fila por fila: `WHERE c.anio = 2026 AND c.anio <> 2025` es redundante (si es 2026 ya no es 2025) y devuelve **todos** los docentes con alguna comisión en 2026, aunque también hayan dado clases en 2025.

«Ninguna en 2025» habla de **todas** las comisiones del docente, así que necesita una subconsulta de ausencia: `NOT IN (... WHERE anio = 2025)` o `NOT EXISTS`.

En la versión con `LEFT JOIN`, el filtro `c25.anio = 2025` tiene que ir en el **`ON`**. Si lo ponés en el `WHERE`, descarta las filas con NULL que justamente estás buscando y el resultado queda vacío.

Resultado: 20 docentes.""",
        errores_comunes=[
            "`WHERE anio = 2026 AND anio <> 2025` en un JOIN: evalúa cada comisión por separado.",
            "Poner la condición del año en el `WHERE` de un LEFT JOIN: lo convierte en INNER y da vacío.",
            "Olvidar el filtro de año dentro del `NOT IN`: excluye a todos los docentes que tienen alguna comisión.",
        ],
        trampas=[
            dict(titulo="Condiciones sobre la misma fila", sql="""SELECT DISTINCT d.id_docente, d.nombre, d.apellido
FROM docentes d JOIN comisiones c ON c.id_docente = d.id_docente
WHERE c.anio = 2026 AND c.anio <> 2025;"""),
            dict(titulo="Año del LEFT JOIN en el WHERE", sql="""SELECT DISTINCT d.id_docente, d.nombre, d.apellido
FROM docentes d
JOIN comisiones c26 ON c26.id_docente = d.id_docente AND c26.anio = 2026
LEFT JOIN comisiones c25 ON c25.id_docente = d.id_docente
WHERE c25.anio = 2025 AND c25.id_comision IS NULL;"""),
            dict(titulo="NOT IN sin filtrar el año", sql="""SELECT d.id_docente, d.nombre, d.apellido
FROM docentes d
WHERE d.id_docente IN (SELECT id_docente FROM comisiones WHERE anio = 2026)
  AND d.id_docente NOT IN (SELECT id_docente FROM comisiones);"""),
        ],
        tags=["IN", "NOT IN", "EXISTS", "NOT EXISTS", "LEFT JOIN"],
    ),
]
