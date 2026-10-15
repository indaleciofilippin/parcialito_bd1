"""Sección: Agrupación — COUNT, SUM, AVG, MIN, MAX, GROUP BY y HAVING (TP1 · Parte C)."""

EJERCICIOS = [
    # ------------------------------------------------------------------
    # Originales del TP1 · Parte C
    # ------------------------------------------------------------------
    dict(
        id="agr-11",
        origen="TP1 · Parte C · Ej. 11",
        titulo="Alumnos inscriptos por carrera",
        dificultad=1,
        tipo="select",
        enunciado="Obtener la cantidad de alumnos inscriptos en cada carrera.\n\n"
                  "*Aclaración:* mostrá la carrera (id o nombre) y la cantidad. Contá todas las inscripciones "
                  "a la carrera, sin importar su estado.",
        solucion="""SELECT ca.id_carrera, ca.nombre, COUNT(*) AS cantidad
FROM carreras ca
JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
GROUP BY ca.id_carrera, ca.nombre;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id de la carrera)", sql="""SELECT id_carrera, COUNT(*) AS cantidad
FROM alumno_carrera
GROUP BY id_carrera;"""),
        ],
        variantes=[
            dict(titulo="Incluyendo carreras sin alumnos (LEFT JOIN, cuentan 0)", sql="""SELECT ca.id_carrera, ca.nombre, COUNT(ac.id_alumno) AS cantidad
FROM carreras ca
LEFT JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
GROUP BY ca.id_carrera, ca.nombre;"""),
        ],
        columnas=[["id_carrera", "cantidad"], ["nombre", "cantidad"]],
        casos_borde=True,
        pistas=[
            "La relación alumno–carrera está en `alumno_carrera`: una fila por cada alumno inscripto en una carrera.",
            "Necesitás una fila por carrera: `GROUP BY` por la carrera, y `COUNT(*)` cuenta las filas de cada grupo.",
            "`SELECT ca.id_carrera, ca.nombre, COUNT(*) FROM carreras ca JOIN alumno_carrera ac ON ... GROUP BY ca.id_carrera, ca.nombre`.",
        ],
        explicacion="""`alumno_carrera` tiene una fila por cada inscripción de un alumno a una carrera. Contar alumnos por carrera es contar esas filas agrupadas por `id_carrera`.

- El `JOIN` con `carreras` solo hace falta para mostrar el nombre.
- `GROUP BY ca.id_carrera, ca.nombre`: una fila por carrera. Con `ONLY_FULL_GROUP_BY`, todo lo que está en el SELECT sin agregar tiene que estar en el GROUP BY. Agrupamos por el id porque es lo que identifica a la carrera (dos podrían llamarse igual).
- `COUNT(*)` alcanza: `(id_alumno, id_carrera)` es UNIQUE, así que un alumno no se repite dentro de una carrera.

**Carreras sin alumnos.** El `JOIN` las descarta. Si las querés ver con 0, usá `LEFT JOIN` y contá una columna de la tabla de la derecha: `COUNT(ac.id_alumno)` ignora los NULL. `COUNT(*)` daría **1**, porque cuenta la fila rellenada con NULL. El corrector acepta las dos versiones y las prueba con casos borde (carreras sin alumnos).""",
        errores_comunes=[
            "Usar `LEFT JOIN` con `COUNT(*)`: las carreras sin alumnos aparecen con 1 en vez de 0.",
            "Escribir el JOIN sin `ON`: MySQL lo acepta y hace un producto cartesiano (cada carrera queda con 1737).",
            "Agrupar solo por `ca.nombre`: acá funciona, pero si dos carreras se llamaran igual se sumarían juntas. Agrupá por el id (y por el nombre si lo mostrás).",
        ],
        trampas=[
            dict(titulo="LEFT JOIN con COUNT(*)", sql="""SELECT ca.id_carrera, ca.nombre, COUNT(*) AS cantidad
FROM carreras ca
LEFT JOIN alumno_carrera ac ON ac.id_carrera = ca.id_carrera
GROUP BY ca.id_carrera, ca.nombre;"""),
            dict(titulo="JOIN sin condición (producto cartesiano)", sql="""SELECT ca.nombre, COUNT(*) AS cantidad
FROM carreras ca
JOIN alumno_carrera ac
GROUP BY ca.nombre;"""),
        ],
        tags=["GROUP BY", "COUNT", "JOIN", "LEFT JOIN"],
    ),
    dict(
        id="agr-12",
        origen="TP1 · Parte C · Ej. 12",
        titulo="Asignaturas por departamento",
        dificultad=1,
        tipo="select",
        enunciado="Calcular la cantidad de asignaturas que tiene cada departamento.\n\n"
                  "*Aclaración:* mostrá el departamento (id o nombre) y la cantidad.",
        solucion="""SELECT dep.id_departamento, dep.nombre, COUNT(*) AS cantidad
FROM departamentos dep
JOIN asignaturas a ON a.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id del departamento)", sql="""SELECT id_departamento, COUNT(*) AS cantidad
FROM asignaturas
GROUP BY id_departamento;"""),
        ],
        variantes=[
            dict(titulo="Incluyendo departamentos sin asignaturas (LEFT JOIN, cuentan 0)", sql="""SELECT dep.id_departamento, dep.nombre, COUNT(a.id_asignatura) AS cantidad
FROM departamentos dep
LEFT JOIN asignaturas a ON a.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre;"""),
        ],
        columnas=[["id_departamento", "cantidad"], ["nombre", "cantidad"]],
        casos_borde=True,
        pistas=[
            "Cada asignatura tiene su `id_departamento`. Contá asignaturas agrupando por ese campo.",
            "Si querés el nombre del departamento, unilo con `departamentos` y agrupá por id y nombre.",
            "`SELECT dep.id_departamento, dep.nombre, COUNT(*) FROM departamentos dep JOIN asignaturas a ON a.id_departamento = dep.id_departamento GROUP BY dep.id_departamento, dep.nombre`.",
        ],
        explicacion="""La relación es **uno a muchos**: un departamento tiene muchas asignaturas. Para contar «cuántas X tiene cada Y» agrupás por Y y contás las filas de X.

```sql
GROUP BY dep.id_departamento, dep.nombre   -- una fila por departamento
COUNT(*)                                   -- asignaturas de ese departamento
```

**Cuidado con los JOIN de más.** Si además unís `carreras` (que también tiene `id_departamento`), cada asignatura se repite una vez por cada carrera del departamento y el conteo se multiplica. Uní solo las tablas que necesitás.

**Departamentos sin asignaturas:** el `JOIN` los descarta. Con `LEFT JOIN` + `COUNT(a.id_asignatura)` aparecen con 0 (el corrector acepta ambas y lo prueba con un departamento nuevo, «Artes», sin asignaturas).""",
        errores_comunes=[
            "Unir tablas que no hacen falta (por ejemplo `carreras`): el JOIN multiplica filas y el conteo sale inflado.",
            "`LEFT JOIN` con `COUNT(*)`: un departamento sin asignaturas cuenta 1.",
        ],
        trampas=[
            dict(titulo="JOIN de más con carreras (multiplica)", sql="""SELECT dep.nombre, COUNT(*) AS cantidad
FROM departamentos dep
JOIN asignaturas a ON a.id_departamento = dep.id_departamento
JOIN carreras ca ON ca.id_departamento = dep.id_departamento
GROUP BY dep.nombre;"""),
            dict(titulo="LEFT JOIN con COUNT(*)", sql="""SELECT dep.id_departamento, dep.nombre, COUNT(*) AS cantidad
FROM departamentos dep
LEFT JOIN asignaturas a ON a.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre;"""),
        ],
        tags=["GROUP BY", "COUNT", "JOIN", "LEFT JOIN"],
    ),
    dict(
        id="agr-13",
        origen="TP1 · Parte C · Ej. 13",
        titulo="Comisiones por asignatura",
        dificultad=2,
        tipo="select",
        enunciado="Obtener la cantidad de comisiones que existen por cada asignatura.\n\n"
                  "*Aclaración:* mostrá la asignatura (id o nombre) y la cantidad.",
        solucion="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS cantidad
FROM asignaturas a
JOIN comisiones c ON c.id_asignatura = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id de la asignatura)", sql="""SELECT id_asignatura, COUNT(*) AS cantidad
FROM comisiones
GROUP BY id_asignatura;"""),
        ],
        variantes=[
            dict(titulo="Incluyendo asignaturas sin comisiones (LEFT JOIN, cuentan 0)", sql="""SELECT a.id_asignatura, a.nombre, COUNT(c.id_comision) AS cantidad
FROM asignaturas a
LEFT JOIN comisiones c ON c.id_asignatura = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre;"""),
        ],
        columnas=[["id_asignatura", "cantidad"], ["nombre", "cantidad"]],
        pistas=[
            "Cada comisión pertenece a una asignatura (`comisiones.id_asignatura`).",
            "Agrupá por asignatura y contá comisiones. ¿Querés ver también las asignaturas que no tienen ninguna? Eso pide `LEFT JOIN`.",
            "Con `LEFT JOIN`, contá `COUNT(c.id_comision)` (no `COUNT(*)`), así las asignaturas sin comisiones quedan en 0.",
        ],
        explicacion="""Con `JOIN` obtenés las **459** asignaturas que tienen al menos una comisión. Pero hay **41 asignaturas sin comisiones**: si «por cada asignatura» incluye a esas, necesitás `LEFT JOIN` y el resultado tiene 500 filas.

La diferencia clave está en qué contás:

| consulta | asignatura sin comisiones |
|---|---|
| `LEFT JOIN` + `COUNT(c.id_comision)` | 0 ✔ |
| `LEFT JOIN` + `COUNT(*)` | 1 ✘ |

`COUNT(columna)` ignora los NULL; `COUNT(*)` cuenta filas, y el `LEFT JOIN` genera una fila (con NULL) para la asignatura sin comisiones.

Las dos lecturas (con y sin las de 0) son válidas y el corrector acepta ambas. Lo que no se acepta es el `LEFT JOIN` con `COUNT(*)`.""",
        errores_comunes=[
            "`LEFT JOIN` con `COUNT(*)`: las 41 asignaturas sin comisiones aparecen con 1.",
            "Unir por columnas que no se corresponden (por ejemplo `c.id_comision = a.id_asignatura`): no da error, pero cuenta cualquier cosa. Seguí siempre la FK.",
        ],
        trampas=[
            dict(titulo="LEFT JOIN con COUNT(*)", sql="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS cantidad
FROM asignaturas a
LEFT JOIN comisiones c ON c.id_asignatura = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre;"""),
            dict(titulo="JOIN por la columna equivocada", sql="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS cantidad
FROM asignaturas a
JOIN comisiones c ON c.id_comision = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre;"""),
        ],
        tags=["GROUP BY", "COUNT", "LEFT JOIN"],
    ),
    dict(
        id="agr-14",
        origen="TP1 · Parte C · Ej. 14",
        titulo="Docentes por departamento",
        dificultad=1,
        tipo="select",
        enunciado="Listar la cantidad de docentes que hay en cada departamento.\n\n"
                  "*Aclaración:* mostrá el departamento (id o nombre) y la cantidad.",
        solucion="""SELECT dep.id_departamento, dep.nombre, COUNT(*) AS cantidad
FROM departamentos dep
JOIN docentes d ON d.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id del departamento)", sql="""SELECT id_departamento, COUNT(*) AS cantidad
FROM docentes
GROUP BY id_departamento;"""),
        ],
        variantes=[
            dict(titulo="Incluyendo departamentos sin docentes (LEFT JOIN, cuentan 0)", sql="""SELECT dep.id_departamento, dep.nombre, COUNT(d.id_docente) AS cantidad
FROM departamentos dep
LEFT JOIN docentes d ON d.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre;"""),
        ],
        columnas=[["id_departamento", "cantidad"], ["nombre", "cantidad"]],
        casos_borde=True,
        pistas=[
            "`docentes` tiene `id_departamento`: no hace falta ninguna otra tabla para contar.",
            "Agrupá los docentes por departamento y contá filas.",
            "`SELECT id_departamento, COUNT(*) FROM docentes GROUP BY id_departamento` (y si querés el nombre, JOIN con `departamentos`).",
        ],
        explicacion="""Es el mismo patrón que «asignaturas por departamento»: agrupás la tabla del lado «muchos» (`docentes`) por la FK (`id_departamento`) y contás.

**No pases por tablas que no necesitás.** Un error muy común es unir con `comisiones` («los docentes dictan comisiones»). Eso repite a cada docente una vez por comisión y `COUNT(*)` termina contando comisiones. Aunque lo arregles con `COUNT(DISTINCT d.id_docente)`, perdés a los docentes que no tienen comisiones: el `JOIN` los descarta.

El corrector lo prueba con casos borde: un departamento nuevo sin docentes y dos docentes nuevos sin comisiones.""",
        errores_comunes=[
            "Unir con `comisiones`: `COUNT(*)` cuenta comisiones, no docentes.",
            "Corregirlo con `COUNT(DISTINCT ...)` pero manteniendo el JOIN con comisiones: se pierden los docentes sin comisiones.",
            "`LEFT JOIN` con `COUNT(*)`: un departamento sin docentes cuenta 1.",
        ],
        trampas=[
            dict(titulo="Pasando por comisiones (cuenta comisiones)", sql="""SELECT dep.nombre, COUNT(*) AS cantidad
FROM departamentos dep
JOIN docentes d ON d.id_departamento = dep.id_departamento
JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY dep.nombre;"""),
            dict(titulo="Comisiones + COUNT(DISTINCT) (pierde docentes sin comisiones)", sql="""SELECT dep.nombre, COUNT(DISTINCT d.id_docente) AS cantidad
FROM departamentos dep
JOIN docentes d ON d.id_departamento = dep.id_departamento
JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY dep.nombre;"""),
            dict(titulo="LEFT JOIN con COUNT(*)", sql="""SELECT dep.id_departamento, dep.nombre, COUNT(*) AS cantidad
FROM departamentos dep
LEFT JOIN docentes d ON d.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre;"""),
        ],
        tags=["GROUP BY", "COUNT", "JOIN"],
    ),
    dict(
        id="agr-15",
        origen="TP1 · Parte C · Ej. 15",
        titulo="Salario promedio por departamento",
        dificultad=1,
        tipo="select",
        enunciado="Calcular el salario promedio de los docentes por departamento.\n\n"
                  "*Aclaración:* mostrá el departamento (id o nombre) y el promedio (podés redondearlo a 2 decimales).",
        solucion="""SELECT dep.id_departamento, dep.nombre, ROUND(AVG(d.salario_base), 2) AS promedio
FROM departamentos dep
JOIN docentes d ON d.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id del departamento)", sql="""SELECT id_departamento, AVG(salario_base) AS promedio
FROM docentes
GROUP BY id_departamento;"""),
        ],
        columnas=[["id_departamento", "promedio"], ["nombre", "promedio"]],
        pistas=[
            "La función de agregación para el promedio es `AVG(...)`.",
            "Una fila por departamento → `GROUP BY id_departamento` (y el nombre si lo mostrás).",
            "`SELECT id_departamento, ROUND(AVG(salario_base), 2) FROM docentes GROUP BY id_departamento`.",
        ],
        explicacion="""`AVG(d.salario_base)` calcula el promedio **dentro de cada grupo** definido por el `GROUP BY`. Sin `GROUP BY`, `AVG` devuelve un único promedio de toda la tabla; y si además ponés `id_departamento` en el SELECT, MySQL da el error **1140** (columna no agregada en una consulta agregada sin GROUP BY).

`ROUND(..., 2)` es solo presentación (el corrector compara redondeando a 2 decimales igual).

**Ojo con los JOIN que repiten filas:** si unís `comisiones`, cada docente aparece una vez por comisión y el promedio queda **ponderado** por la cantidad de comisiones de cada uno: ya no es «el salario promedio de los docentes». Para promediar docentes, cada docente tiene que aparecer una sola vez.""",
        errores_comunes=[
            "Unir con `comisiones` u otra tabla «muchos»: los docentes con más comisiones pesan más en el promedio.",
            "Olvidar el `GROUP BY` (error 1140 o un solo promedio general).",
        ],
        trampas=[
            dict(titulo="Promedio ponderado por comisiones (JOIN de más)", sql="""SELECT dep.id_departamento, dep.nombre, ROUND(AVG(d.salario_base), 2) AS promedio
FROM departamentos dep
JOIN docentes d ON d.id_departamento = dep.id_departamento
JOIN comisiones c ON c.id_docente = d.id_docente
GROUP BY dep.id_departamento, dep.nombre;"""),
            dict(titulo="Sin GROUP BY (error 1140)", sql="""SELECT id_departamento, AVG(salario_base) AS promedio
FROM docentes;"""),
        ],
        tags=["GROUP BY", "AVG", "ROUND"],
    ),
    dict(
        id="agr-16",
        origen="TP1 · Parte C · Ej. 16",
        titulo="Alumnos inscriptos por comisión",
        dificultad=1,
        tipo="select",
        enunciado="Obtener la cantidad de alumnos inscriptos en cada comisión.\n\n"
                  "*Aclaración:* mostrá el id de la comisión y la cantidad.",
        solucion="""SELECT i.id_comision, COUNT(*) AS inscriptos
FROM inscripcion_alumno_comision i
GROUP BY i.id_comision;""",
        alternativas=[
            dict(titulo="Con el nombre de la asignatura", sql="""SELECT c.id_comision, a.nombre AS asignatura, COUNT(*) AS inscriptos
FROM comisiones c
JOIN asignaturas a ON a.id_asignatura = c.id_asignatura
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.id_comision, a.nombre;"""),
            dict(titulo="Usando la vista vw_inscriptos_por_comision", sql="""SELECT id_comision, cantidad_inscriptos
FROM vw_inscriptos_por_comision;"""),
        ],
        variantes=[
            dict(titulo="Sin contar las bajas (estado <> 'Baja')", sql="""SELECT i.id_comision, COUNT(*) AS inscriptos
FROM inscripcion_alumno_comision i
WHERE i.estado <> 'Baja'
GROUP BY i.id_comision;"""),
        ],
        columnas=[["id_comision", "inscriptos"]],
        pistas=[
            "Las inscripciones están en `inscripcion_alumno_comision` (una fila por alumno y comisión).",
            "Agrupá por `id_comision` y contá filas.",
            "`SELECT id_comision, COUNT(*) FROM inscripcion_alumno_comision GROUP BY id_comision`.",
        ],
        explicacion="""La pregunta es «¿cuántas filas de inscripción hay **por comisión**?». Entonces:

- `GROUP BY i.id_comision` → un grupo por comisión.
- `COUNT(*)` → filas del grupo = alumnos inscriptos. Como `(id_alumno, id_comision)` es UNIQUE, no hay alumnos repetidos dentro de una comisión y no hace falta `COUNT(DISTINCT i.id_alumno)` (daría lo mismo).

La columna del GROUP BY es lo que va **después de «por cada»**: si agrupás por `id_alumno` obtenés «comisiones por alumno», otra cosa.

Si interpretás que las bajas ya no están inscriptas, agregá `WHERE i.estado <> 'Baja'` (el corrector acepta ambas lecturas). Todas las comisiones tienen inscriptos, así que no hace falta `LEFT JOIN`.""",
        errores_comunes=[
            "Agrupar por `id_alumno` (cuenta comisiones por alumno, no alumnos por comisión).",
            "`COUNT(DISTINCT id_comision)` dentro de un `GROUP BY id_comision`: siempre da 1.",
        ],
        trampas=[
            dict(titulo="Agrupar por alumno", sql="""SELECT i.id_alumno, COUNT(*) AS inscriptos
FROM inscripcion_alumno_comision i
GROUP BY i.id_alumno;"""),
            dict(titulo="COUNT(DISTINCT id_comision)", sql="""SELECT i.id_comision, COUNT(DISTINCT i.id_comision) AS inscriptos
FROM inscripcion_alumno_comision i
GROUP BY i.id_comision;"""),
        ],
        tags=["GROUP BY", "COUNT"],
    ),
    dict(
        id="agr-17",
        origen="TP1 · Parte C · Ej. 17",
        titulo="Nota promedio por examen",
        dificultad=1,
        tipo="select",
        enunciado="Calcular la nota promedio obtenida en cada examen.\n\n"
                  "*Aclaración:* mostrá el id del examen y el promedio (podés redondearlo a 2 decimales).",
        solucion="""SELECT n.id_examen, ROUND(AVG(n.nota), 2) AS promedio
FROM notas n
GROUP BY n.id_examen;""",
        alternativas=[
            dict(titulo="Con datos del examen (JOIN examenes)", sql="""SELECT e.id_examen, e.fecha, e.tipo, ROUND(AVG(n.nota), 2) AS promedio
FROM examenes e
JOIN notas n ON n.id_examen = e.id_examen
GROUP BY e.id_examen, e.fecha, e.tipo;"""),
        ],
        variantes=[
            dict(titulo="Sin redondear el promedio", sql="""SELECT n.id_examen, AVG(n.nota) AS promedio
FROM notas n
GROUP BY n.id_examen;"""),
        ],
        columnas=[["id_examen", "promedio"]],
        pistas=[
            "Las notas están en `notas`, y cada nota indica a qué examen corresponde (`id_examen`).",
            "Un promedio por examen → `GROUP BY id_examen` + `AVG(nota)`.",
            "`SELECT id_examen, ROUND(AVG(nota), 2) FROM notas GROUP BY id_examen`.",
        ],
        explicacion="""Cada fila de `notas` es la nota de **un alumno** en **un examen**. «Promedio por examen» = agrupar por `id_examen` y promediar `nota`.

No hace falta unir con `examenes` salvo que quieras mostrar la fecha o el tipo; si lo hacés, agregá esas columnas al `GROUP BY` (o MySQL se queja con `ONLY_FULL_GROUP_BY`).

Fijate qué cambia según la columna del `GROUP BY`:

- `GROUP BY id_examen` → promedio de cada examen (4800 filas).
- `GROUP BY id_alumno` → promedio de cada alumno (otra pregunta).

Y no filtres con `WHERE nota >= 4`: eso calcula el promedio **solo de los aprobados**, que no es lo pedido.""",
        errores_comunes=[
            "Agrupar por `id_alumno` en vez de `id_examen`.",
            "Filtrar notas (por ejemplo `WHERE nota >= 4`) antes de promediar: cambia el promedio.",
        ],
        trampas=[
            dict(titulo="Promedio por alumno", sql="""SELECT n.id_alumno, ROUND(AVG(n.nota), 2) AS promedio
FROM notas n
GROUP BY n.id_alumno;"""),
            dict(titulo="Promedio solo de aprobados", sql="""SELECT n.id_examen, ROUND(AVG(n.nota), 2) AS promedio
FROM notas n
WHERE n.nota >= 4
GROUP BY n.id_examen;"""),
        ],
        tags=["GROUP BY", "AVG"],
    ),
    dict(
        id="agr-18",
        origen="TP1 · Parte C · Ej. 18",
        titulo="Mesas finales por turno",
        dificultad=1,
        tipo="select",
        enunciado="Obtener la cantidad de mesas finales por cada turno ('Febrero', 'Julio', 'Diciembre').",
        solucion="""SELECT m.turno, COUNT(*) AS cantidad
FROM mesas_finales m
GROUP BY m.turno;""",
        pistas=[
            "El turno es una columna de `mesas_finales` (un ENUM con tres valores).",
            "No hace falta ningún JOIN: agrupá `mesas_finales` por `turno`.",
            "`SELECT turno, COUNT(*) FROM mesas_finales GROUP BY turno`.",
        ],
        explicacion="""Agrupar por una columna de la misma tabla: `GROUP BY m.turno` genera un grupo por cada valor distinto (tres) y `COUNT(*)` cuenta las mesas de cada uno.

No hace falta `WHERE turno IN ('Febrero','Julio','Diciembre')`: el ENUM no admite otros valores.

**Ojo con los JOIN:** si unís con `inscripciones_finales`, cada mesa se repite una vez por inscripto y `COUNT(*)` cuenta **inscripciones**, no mesas. Y `COUNT(DISTINCT m.id_asignatura)` contaría asignaturas, no mesas.

Dato útil: `ORDER BY turno` sobre un ENUM ordena por la posición en la definición (Febrero, Julio, Diciembre), no alfabéticamente.""",
        errores_comunes=[
            "Unir con `inscripciones_finales` y contar: da la cantidad de inscripciones por turno.",
            "Contar otra cosa (por ejemplo `COUNT(DISTINCT id_asignatura)`).",
        ],
        trampas=[
            dict(titulo="JOIN con inscripciones (cuenta inscriptos)", sql="""SELECT m.turno, COUNT(*) AS cantidad
FROM mesas_finales m
JOIN inscripciones_finales inf ON inf.id_mesa = m.id_mesa
GROUP BY m.turno;"""),
            dict(titulo="Cuenta asignaturas distintas", sql="""SELECT m.turno, COUNT(DISTINCT m.id_asignatura) AS cantidad
FROM mesas_finales m
GROUP BY m.turno;"""),
        ],
        tags=["GROUP BY", "COUNT", "ENUM"],
    ),
    dict(
        id="agr-19",
        origen="TP1 · Parte C · Ej. 19",
        titulo="Presentes y ausentes por comisión",
        dificultad=2,
        tipo="select",
        enunciado="Calcular la cantidad de asistencias presentes y ausentes por comisión.\n\n"
                  "*Aclaración:* en `asistencias`, `presente` vale 1 (presente) o 0 (ausente). "
                  "Mostrá una fila por comisión con la cantidad de presentes y la de ausentes.",
        solucion="""SELECT asi.id_comision,
       SUM(asi.presente = 1) AS presentes,
       SUM(asi.presente = 0) AS ausentes
FROM asistencias asi
GROUP BY asi.id_comision;""",
        alternativas=[
            dict(titulo="Con CASE WHEN (estándar SQL)", sql="""SELECT asi.id_comision,
       SUM(CASE WHEN asi.presente = 1 THEN 1 ELSE 0 END) AS presentes,
       SUM(CASE WHEN asi.presente = 0 THEN 1 ELSE 0 END) AS ausentes
FROM asistencias asi
GROUP BY asi.id_comision;"""),
            dict(titulo="SUM(presente) y COUNT(*) - SUM(presente)", sql="""SELECT asi.id_comision,
       SUM(asi.presente) AS presentes,
       COUNT(*) - SUM(asi.presente) AS ausentes
FROM asistencias asi
GROUP BY asi.id_comision;"""),
        ],
        variantes=[
            dict(titulo="Una fila por comisión y valor de presente (GROUP BY id_comision, presente)", sql="""SELECT asi.id_comision, asi.presente, COUNT(*) AS cantidad
FROM asistencias asi
GROUP BY asi.id_comision, asi.presente;"""),
        ],
        columnas=[["id_comision", "presentes", "ausentes"]],
        pistas=[
            "Necesitás dos conteos condicionales en la misma fila: uno de los registros con `presente = 1` y otro de los que tienen `presente = 0`.",
            "En MySQL una comparación vale 1 (verdadero) o 0 (falso), así que `SUM(presente = 1)` cuenta las filas que cumplen la condición.",
            "`SELECT id_comision, SUM(presente = 1) AS presentes, SUM(presente = 0) AS ausentes FROM asistencias GROUP BY id_comision`.",
        ],
        explicacion="""Es un **conteo condicional**: dentro de cada grupo (comisión) querés contar solo las filas que cumplen una condición.

- `SUM(asi.presente = 1)`: la comparación da 1 o 0 por fila; sumarla cuenta las que dan 1.
- `SUM(CASE WHEN asi.presente = 1 THEN 1 ELSE 0 END)`: lo mismo en SQL estándar (funciona en cualquier motor).
- Como `presente` ya es 0/1: `SUM(presente)` son los presentes y `COUNT(*) - SUM(presente)` los ausentes.

**La trampa clásica:** `COUNT(presente = 1)`. `COUNT` cuenta valores **no NULL**, y `0` no es NULL: cuenta todas las filas. Para contar con condición usá `SUM(condición)` o `COUNT(CASE WHEN cond THEN 1 END)` (sin ELSE, así lo que no cumple queda NULL).

También se acepta `GROUP BY id_comision, presente` (dos filas por comisión), aunque la versión con columnas separadas es más fácil de leer.""",
        errores_comunes=[
            "`COUNT(presente = 1)`: COUNT no mira si el valor es 0 o 1, solo si es NULL. Cuenta todo.",
            "Filtrar con `WHERE presente = 1`: perdés los ausentes (y no podés calcular los dos en la misma consulta).",
        ],
        trampas=[
            dict(titulo="COUNT(condición) en vez de SUM", sql="""SELECT asi.id_comision,
       COUNT(asi.presente = 1) AS presentes,
       COUNT(asi.presente = 0) AS ausentes
FROM asistencias asi
GROUP BY asi.id_comision;"""),
            dict(titulo="WHERE presente = 1 (solo presentes)", sql="""SELECT asi.id_comision, COUNT(*) AS presentes
FROM asistencias asi
WHERE asi.presente = 1
GROUP BY asi.id_comision;"""),
        ],
        tags=["GROUP BY", "SUM", "CASE WHEN", "conteo condicional"],
    ),
    dict(
        id="agr-20",
        origen="TP1 · Parte C · Ej. 20",
        titulo="Asignaturas con más de 5 correlativas",
        dificultad=2,
        tipo="select",
        enunciado="Listar aquellas asignaturas que tienen más de 5 correlatividades.\n\n"
                  "*Aclaración:* en `correlatividades`, cada fila indica que `id_asignatura` tiene como "
                  "correlativa a `id_asignatura_correlativa`.",
        solucion="""SELECT a.id_asignatura, a.nombre, COUNT(*) AS cantidad
FROM asignaturas a
JOIN correlatividades co ON co.id_asignatura = a.id_asignatura
GROUP BY a.id_asignatura, a.nombre
HAVING COUNT(*) > 5;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id)", sql="""SELECT id_asignatura, COUNT(*) AS cantidad
FROM correlatividades
GROUP BY id_asignatura
HAVING COUNT(*) > 5;"""),
        ],
        columnas=[["id_asignatura"], ["nombre"]],
        pistas=[
            "Primero calculá cuántas correlatividades tiene cada asignatura (`GROUP BY id_asignatura` en `correlatividades`).",
            "Ahora hay que quedarse con los **grupos** que superan 5. Un filtro sobre un agregado no va en `WHERE`.",
            "`... GROUP BY id_asignatura HAVING COUNT(*) > 5`.",
        ],
        explicacion="""Dos pasos: **agrupar** y después **filtrar grupos**.

1. `GROUP BY a.id_asignatura, a.nombre` con `COUNT(*)` da cuántas correlativas tiene cada asignatura.
2. `HAVING COUNT(*) > 5` se queda con las que superan 5.

**¿Por qué HAVING y no WHERE?** `WHERE` filtra **filas** antes de agrupar, cuando `COUNT(*)` todavía no existe; por eso `WHERE COUNT(*) > 5` da el error *Invalid use of group function* (1111). `HAVING` filtra **grupos**, después de calcular los agregados.

Fijate en la columna: «la asignatura que tiene correlativas» es `id_asignatura`. Si agrupás por `id_asignatura_correlativa` respondés otra pregunta: «de cuántas asignaturas es correlativa cada una».

«Más de 5» es `> 5`: con `>= 5` salen 27 asignaturas en vez de 5.""",
        errores_comunes=[
            "Poner la condición sobre el agregado en el `WHERE` (error 1111).",
            "Usar `>= 5` cuando dice «más de 5».",
            "Agrupar por `id_asignatura_correlativa` (invierte el sentido de la relación).",
        ],
        trampas=[
            dict(titulo="WHERE con agregado (error)", sql="""SELECT id_asignatura, COUNT(*) AS cantidad
FROM correlatividades
WHERE COUNT(*) > 5
GROUP BY id_asignatura;"""),
            dict(titulo=">= 5 en vez de > 5", sql="""SELECT id_asignatura, COUNT(*) AS cantidad
FROM correlatividades
GROUP BY id_asignatura
HAVING COUNT(*) >= 5;"""),
            dict(titulo="Agrupar por la correlativa", sql="""SELECT id_asignatura_correlativa AS id_asignatura, COUNT(*) AS cantidad
FROM correlatividades
GROUP BY id_asignatura_correlativa
HAVING COUNT(*) > 5;"""),
        ],
        tags=["GROUP BY", "HAVING", "COUNT"],
    ),

    # ------------------------------------------------------------------
    # Variantes nuevas
    # ------------------------------------------------------------------
    dict(
        id="agr-n01",
        origen="Variante",
        titulo="Brecha salarial por departamento",
        dificultad=1,
        tipo="select",
        enunciado="Para cada departamento, mostrar el **salario base mínimo**, el **máximo** y la **diferencia** "
                  "entre ambos (la brecha salarial).",
        solucion="""SELECT dep.id_departamento, dep.nombre,
       MIN(d.salario_base) AS minimo,
       MAX(d.salario_base) AS maximo,
       MAX(d.salario_base) - MIN(d.salario_base) AS brecha
FROM departamentos dep
JOIN docentes d ON d.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id del departamento)", sql="""SELECT id_departamento,
       MIN(salario_base) AS minimo,
       MAX(salario_base) AS maximo,
       MAX(salario_base) - MIN(salario_base) AS brecha
FROM docentes
GROUP BY id_departamento;"""),
        ],
        columnas=[["id_departamento", "minimo", "maximo", "brecha"], ["nombre", "minimo", "maximo", "brecha"]],
        pistas=[
            "`MIN(...)` y `MAX(...)` funcionan igual que `COUNT` o `AVG`: se calculan por grupo.",
            "Podés operar entre agregados en el SELECT: `MAX(x) - MIN(x)`.",
            "`SELECT id_departamento, MIN(salario_base), MAX(salario_base), MAX(salario_base) - MIN(salario_base) FROM docentes GROUP BY id_departamento`.",
        ],
        explicacion="""Con un mismo `GROUP BY` podés calcular **varios agregados a la vez**: cada uno se evalúa sobre las filas del grupo.

```sql
MIN(d.salario_base)                        -- el menor del departamento
MAX(d.salario_base)                        -- el mayor
MAX(d.salario_base) - MIN(d.salario_base)  -- expresión entre agregados
```

Lo único que va en el `GROUP BY` es lo que define el grupo (el departamento). Si agregás `salario_base` al `GROUP BY`, cada docente queda en su propio grupo y `MIN` = `MAX` = su salario: perdiste la agrupación.

Sin `GROUP BY`, `MIN`/`MAX` se calculan sobre toda la tabla y obtenés una sola fila.""",
        errores_comunes=[
            "Agregar `salario_base` al GROUP BY «porque aparece en el SELECT»: solo van las columnas **no agregadas**.",
            "Olvidar el GROUP BY: una sola fila con el mínimo y máximo de toda la universidad.",
        ],
        trampas=[
            dict(titulo="Agrupar también por salario", sql="""SELECT id_departamento,
       MIN(salario_base) AS minimo,
       MAX(salario_base) AS maximo,
       MAX(salario_base) - MIN(salario_base) AS brecha
FROM docentes
GROUP BY id_departamento, salario_base;"""),
            dict(titulo="Sin GROUP BY (toda la tabla)", sql="""SELECT MIN(salario_base) AS minimo,
       MAX(salario_base) AS maximo,
       MAX(salario_base) - MIN(salario_base) AS brecha
FROM docentes;"""),
        ],
        tags=["GROUP BY", "MIN", "MAX"],
    ),
    dict(
        id="agr-n02",
        origen="Variante",
        titulo="Comisiones por año y cuatrimestre",
        dificultad=1,
        tipo="select",
        enunciado="Obtener la cantidad de comisiones de cada **año y cuatrimestre**, ordenado por año y luego por cuatrimestre.",
        solucion="""SELECT c.anio, c.cuatrimestre, COUNT(*) AS cantidad
FROM comisiones c
GROUP BY c.anio, c.cuatrimestre
ORDER BY c.anio, c.cuatrimestre;""",
        ordenado=True,
        orden=[("anio", "asc"), ("cuatrimestre", "asc")],
        pistas=[
            "Cada grupo es una **combinación** de año y cuatrimestre (por ejemplo 2025-1).",
            "Se puede agrupar por más de una columna: `GROUP BY anio, cuatrimestre`.",
            "`SELECT anio, cuatrimestre, COUNT(*) FROM comisiones GROUP BY anio, cuatrimestre ORDER BY anio, cuatrimestre`.",
        ],
        explicacion="""Con `GROUP BY anio, cuatrimestre` se forma un grupo por cada **combinación distinta** de los dos valores: 3 años × 2 cuatrimestres = 6 filas.

Si agrupás solo por `anio` pero dejás `cuatrimestre` en el SELECT, MySQL da el error **1055** (`ONLY_FULL_GROUP_BY`): dentro del grupo «2025» hay dos cuatrimestres distintos y no sabe cuál mostrar.

`ORDER BY anio, cuatrimestre` ordena primero por año y, a igualdad de año, por cuatrimestre. El orden va al final de la consulta (después de `GROUP BY` / `HAVING`).""",
        errores_comunes=[
            "Agrupar solo por año dejando el cuatrimestre en el SELECT (error 1055).",
            "Agrupar por columnas de más (por ejemplo también por `tipo`): los grupos se parten.",
        ],
        trampas=[
            dict(titulo="GROUP BY solo por año (error 1055)", sql="""SELECT c.anio, c.cuatrimestre, COUNT(*) AS cantidad
FROM comisiones c
GROUP BY c.anio;"""),
            dict(titulo="Agrupar también por tipo", sql="""SELECT c.anio, c.cuatrimestre, COUNT(*) AS cantidad
FROM comisiones c
GROUP BY c.anio, c.cuatrimestre, c.tipo
ORDER BY c.anio, c.cuatrimestre;"""),
            dict(titulo="Orden incorrecto", sql="""SELECT c.anio, c.cuatrimestre, COUNT(*) AS cantidad
FROM comisiones c
GROUP BY c.anio, c.cuatrimestre
ORDER BY cantidad DESC;"""),
        ],
        tags=["GROUP BY", "COUNT", "ORDER BY", "varias columnas"],
    ),
    dict(
        id="agr-n03",
        origen="Variante",
        titulo="Alumnos que cursaron cada año",
        dificultad=2,
        tipo="select",
        enunciado="Para cada año, obtener la cantidad de **alumnos** que se inscribieron en al menos una comisión "
                  "de ese año (no la cantidad de inscripciones). Usá el año de la comisión.",
        solucion="""SELECT c.anio, COUNT(DISTINCT i.id_alumno) AS alumnos
FROM comisiones c
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.anio;""",
        pistas=[
            "El año está en `comisiones`; las inscripciones, en `inscripcion_alumno_comision`.",
            "Un alumno se inscribe en varias comisiones el mismo año: si contás filas, lo contás varias veces.",
            "`COUNT(DISTINCT i.id_alumno)` cuenta cada alumno una sola vez por grupo.",
        ],
        explicacion="""Después del `JOIN` hay **una fila por inscripción**. En cada año, un mismo alumno aparece tantas veces como comisiones haya cursado.

| expresión | qué cuenta en cada año |
|---|---|
| `COUNT(*)` | inscripciones (filas) |
| `COUNT(i.id_alumno)` | lo mismo: valores no NULL, con repetidos |
| `COUNT(DISTINCT i.id_alumno)` | alumnos distintos ✔ |

Con estos datos la diferencia es enorme: unas 6000 inscripciones por año, pero 997 alumnos.

Regla práctica: si la pregunta es «cuántos **X**» y X se puede repetir dentro del grupo por culpa del JOIN, usá `COUNT(DISTINCT X)`.""",
        errores_comunes=[
            "`COUNT(*)` o `COUNT(id_alumno)`: cuentan inscripciones, no alumnos.",
            "Agrupar por `id_alumno` en vez de por año.",
        ],
        trampas=[
            dict(titulo="COUNT(*) (cuenta inscripciones)", sql="""SELECT c.anio, COUNT(*) AS alumnos
FROM comisiones c
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.anio;"""),
            dict(titulo="COUNT(id_alumno) sin DISTINCT", sql="""SELECT c.anio, COUNT(i.id_alumno) AS alumnos
FROM comisiones c
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
GROUP BY c.anio;"""),
        ],
        tags=["GROUP BY", "COUNT DISTINCT", "JOIN"],
    ),
    dict(
        id="agr-n04",
        origen="Variante",
        titulo="Total pagado a cada docente en 2026",
        dificultad=2,
        tipo="select",
        enunciado="Calcular el **monto total pagado** a cada docente durante **2026** (según `docente_asignatura`), "
                  "ordenado de mayor a menor. Mostrá el docente (id o nombre y apellido) y el total.",
        solucion="""SELECT d.id_docente, d.nombre, d.apellido, SUM(da.monto_pagado) AS total
FROM docentes d
JOIN docente_asignatura da ON da.id_docente = d.id_docente
WHERE da.anio = 2026
GROUP BY d.id_docente, d.nombre, d.apellido
ORDER BY total DESC;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id del docente)", sql="""SELECT id_docente, SUM(monto_pagado) AS total
FROM docente_asignatura
WHERE anio = 2026
GROUP BY id_docente
ORDER BY total DESC;"""),
        ],
        columnas=[["id_docente", "total"], ["nombre", "apellido", "total"]],
        ordenado=True,
        orden=[("total", "desc")],
        pistas=[
            "Primero filtrá las filas de 2026 (`WHERE anio = 2026`), después agrupá por docente.",
            "El total es `SUM(monto_pagado)`. Para ordenar por el total podés usar el alias en el `ORDER BY`.",
            "`... WHERE da.anio = 2026 GROUP BY d.id_docente, d.nombre, d.apellido ORDER BY total DESC`.",
        ],
        explicacion="""El orden lógico de una consulta agrupada es:

`FROM/JOIN` → `WHERE` (filtra filas) → `GROUP BY` → agregados → `HAVING` → `SELECT` → `ORDER BY`.

- `WHERE da.anio = 2026` descarta los pagos de otros años **antes** de sumar.
- `SUM(da.monto_pagado)` suma por docente.
- `ORDER BY total DESC` ordena por el agregado. En MySQL podés usar el alias porque el `ORDER BY` se evalúa después del SELECT (también vale `ORDER BY SUM(da.monto_pagado) DESC`).

Agrupá por `id_docente` además del nombre: hay docentes con el **mismo nombre y apellido**, y si agrupás solo por nombre los sumás juntos.""",
        errores_comunes=[
            "Olvidar el filtro de año: suma los pagos de 2024 a 2026.",
            "Agrupar por nombre y apellido sin el id: los homónimos se suman como si fueran una persona.",
            "Ordenar ascendente (por defecto `ORDER BY` es ASC).",
        ],
        trampas=[
            dict(titulo="Sin filtro de año", sql="""SELECT d.id_docente, d.nombre, d.apellido, SUM(da.monto_pagado) AS total
FROM docentes d
JOIN docente_asignatura da ON da.id_docente = d.id_docente
GROUP BY d.id_docente, d.nombre, d.apellido
ORDER BY total DESC;"""),
            dict(titulo="Agrupar por nombre y apellido (junta homónimos)", sql="""SELECT d.nombre, d.apellido, SUM(da.monto_pagado) AS total
FROM docentes d
JOIN docente_asignatura da ON da.id_docente = d.id_docente
WHERE da.anio = 2026
GROUP BY d.nombre, d.apellido
ORDER BY total DESC;"""),
            dict(titulo="Orden ascendente", sql="""SELECT d.id_docente, SUM(da.monto_pagado) AS total
FROM docentes d
JOIN docente_asignatura da ON da.id_docente = d.id_docente
WHERE da.anio = 2026
GROUP BY d.id_docente
ORDER BY total;"""),
        ],
        tags=["GROUP BY", "SUM", "WHERE", "ORDER BY"],
    ),
    dict(
        id="agr-n05",
        origen="Variante",
        titulo="Departamentos con salario promedio alto",
        dificultad=2,
        tipo="select",
        enunciado="Listar los departamentos cuyo **salario base promedio** supera los **$300.000**. "
                  "Mostrá el departamento (id o nombre) y el promedio.",
        solucion="""SELECT dep.id_departamento, dep.nombre, ROUND(AVG(d.salario_base), 2) AS promedio
FROM departamentos dep
JOIN docentes d ON d.id_departamento = dep.id_departamento
GROUP BY dep.id_departamento, dep.nombre
HAVING AVG(d.salario_base) > 300000;""",
        alternativas=[
            dict(titulo="Sin JOIN (solo el id del departamento)", sql="""SELECT id_departamento, AVG(salario_base) AS promedio
FROM docentes
GROUP BY id_departamento
HAVING AVG(salario_base) > 300000;"""),
        ],
        columnas=[["id_departamento", "promedio"], ["nombre", "promedio"]],
        pistas=[
            "Calculá primero el promedio por departamento (`AVG` + `GROUP BY`).",
            "La condición es sobre el **promedio** (un agregado), no sobre cada docente.",
            "`... GROUP BY id_departamento HAVING AVG(salario_base) > 300000`.",
        ],
        explicacion="""La condición «promedio mayor a 300.000» es sobre el **grupo**, así que va en `HAVING`.

Compará con este error muy común:

```sql
WHERE d.salario_base > 300000   -- filtra DOCENTES
GROUP BY ...
```

Eso primero descarta a los docentes que ganan menos y después promedia a los que quedan: todos los departamentos aparecen, con promedios altísimos. Es otra pregunta («promedio de los que ganan más de 300.000»).

Y `WHERE AVG(...) > 300000` directamente da error 1111: en el WHERE todavía no hay grupos.""",
        errores_comunes=[
            "Filtrar `salario_base > 300000` en el WHERE: cambia qué docentes se promedian.",
            "Poner `AVG(...)` en el WHERE (error 1111).",
        ],
        trampas=[
            dict(titulo="WHERE sobre el salario de cada docente", sql="""SELECT dep.id_departamento, dep.nombre, ROUND(AVG(d.salario_base), 2) AS promedio
FROM departamentos dep
JOIN docentes d ON d.id_departamento = dep.id_departamento
WHERE d.salario_base > 300000
GROUP BY dep.id_departamento, dep.nombre;"""),
            dict(titulo="AVG en el WHERE (error)", sql="""SELECT id_departamento, AVG(salario_base) AS promedio
FROM docentes
WHERE AVG(salario_base) > 300000
GROUP BY id_departamento;"""),
        ],
        tags=["GROUP BY", "HAVING", "AVG"],
    ),
    dict(
        id="agr-n06",
        origen="Variante",
        titulo="Comisiones 2025 con más de 18 vigentes",
        dificultad=3,
        tipo="select",
        enunciado="Para las comisiones del año **2025**, mostrar cuántos alumnos tienen una inscripción **vigente** "
                  "(estado distinto de `'Baja'`), pero solo las comisiones con **más de 18** inscriptos vigentes. "
                  "Mostrá el id de la comisión y la cantidad.",
        solucion="""SELECT c.id_comision, COUNT(*) AS inscriptos
FROM comisiones c
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
WHERE c.anio = 2025
  AND i.estado <> 'Baja'
GROUP BY c.id_comision
HAVING COUNT(*) > 18;""",
        columnas=[["id_comision", "inscriptos"]],
        pistas=[
            "Hay dos tipos de filtro: sobre **filas** (año de la comisión, estado de la inscripción) y sobre **grupos** (cantidad > 18).",
            "Los filtros de filas van en `WHERE`; el filtro sobre `COUNT(*)` va en `HAVING`.",
            "`... WHERE c.anio = 2025 AND i.estado <> 'Baja' GROUP BY c.id_comision HAVING COUNT(*) > 18`.",
        ],
        explicacion="""Esta consulta usa las tres cláusulas, cada una con su rol:

```sql
WHERE c.anio = 2025 AND i.estado <> 'Baja'  -- 1) qué FILAS entran
GROUP BY c.id_comision                      -- 2) cómo se agrupan
HAVING COUNT(*) > 18                        -- 3) qué GRUPOS quedan
```

- El año y el estado son propiedades de **cada fila**: van en `WHERE`. Si los ponés en `HAVING`, MySQL da error (1054: la columna no está en el GROUP BY ni agregada).
- `COUNT(*) > 18` es una propiedad del **grupo**: va en `HAVING`.

El orden importa: como el `WHERE` saca las bajas antes de agrupar, `COUNT(*)` ya cuenta solo inscripciones vigentes. Si olvidás el filtro de estado, el conteo incluye las bajas y aparecen más comisiones.""",
        errores_comunes=[
            "Olvidar `estado <> 'Baja'`: cuenta también las bajas.",
            "Poner el filtro de estado en el HAVING (error 1054).",
            "Usar `>= 18` cuando dice «más de 18».",
        ],
        trampas=[
            dict(titulo="Sin filtrar las bajas", sql="""SELECT c.id_comision, COUNT(*) AS inscriptos
FROM comisiones c
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
WHERE c.anio = 2025
GROUP BY c.id_comision
HAVING COUNT(*) > 18;"""),
            dict(titulo="Filtro de filas en el HAVING (error)", sql="""SELECT c.id_comision, COUNT(*) AS inscriptos
FROM comisiones c
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
WHERE c.anio = 2025
GROUP BY c.id_comision
HAVING COUNT(*) > 18 AND i.estado <> 'Baja';"""),
            dict(titulo=">= 18 en vez de > 18", sql="""SELECT c.id_comision, COUNT(*) AS inscriptos
FROM comisiones c
JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
WHERE c.anio = 2025
  AND i.estado <> 'Baja'
GROUP BY c.id_comision
HAVING COUNT(*) >= 18;"""),
        ],
        tags=["WHERE", "GROUP BY", "HAVING", "COUNT"],
    ),
    dict(
        id="agr-n07",
        origen="Variante",
        titulo="Porcentaje de asistencia por comisión",
        dificultad=3,
        tipo="select",
        enunciado="Calcular el **porcentaje de asistencia** de cada comisión: presentes sobre el total de registros "
                  "de asistencia, expresado **de 0 a 100** y **redondeado a 2 decimales**.",
        solucion="""SELECT asi.id_comision,
       ROUND(SUM(asi.presente = 1) * 100 / COUNT(*), 2) AS porcentaje
FROM asistencias asi
GROUP BY asi.id_comision;""",
        alternativas=[
            dict(titulo="Con AVG (presente vale 0 o 1)", sql="""SELECT asi.id_comision, ROUND(AVG(asi.presente) * 100, 2) AS porcentaje
FROM asistencias asi
GROUP BY asi.id_comision;"""),
        ],
        variantes=[
            dict(titulo="Sin redondear (el cálculo es correcto)", sql="""SELECT asi.id_comision, SUM(asi.presente = 1) * 100 / COUNT(*) AS porcentaje
FROM asistencias asi
GROUP BY asi.id_comision;"""),
        ],
        columnas=[["id_comision", "porcentaje"]],
        pistas=[
            "Porcentaje = (cantidad de presentes / total de registros) × 100, calculado por comisión.",
            "Los presentes se cuentan con `SUM(presente = 1)` (o `SUM(presente)`); el total, con `COUNT(*)`.",
            "`ROUND(SUM(presente = 1) * 100 / COUNT(*), 2)` agrupando por `id_comision`.",
        ],
        explicacion="""Un porcentaje por grupo es un **cociente de dos agregados**:

```sql
SUM(asi.presente = 1) * 100 / COUNT(*)
```

- `SUM(presente = 1)`: presentes de la comisión (conteo condicional).
- `COUNT(*)`: todos los registros de la comisión.
- `* 100` para expresarlo de 0 a 100, y `ROUND(..., 2)` para los decimales.

Atajo: como `presente` vale 0 o 1, su **promedio** ya es la proporción de presentes: `AVG(presente) * 100`.

En MySQL `/` siempre hace división decimal (`DIV` es la entera), así que no hay problema de truncamiento. Lo que sí rompe todo es `COUNT(presente = 1)`: cuenta todas las filas y da 100% en todas las comisiones.""",
        errores_comunes=[
            "`COUNT(presente = 1)` en el numerador: da 100% siempre.",
            "Olvidar el `* 100` (queda una proporción entre 0 y 1).",
            "Calcular el porcentaje de ausencias en vez del de asistencia.",
        ],
        trampas=[
            dict(titulo="COUNT(condición) en el numerador", sql="""SELECT asi.id_comision,
       ROUND(COUNT(asi.presente = 1) * 100 / COUNT(*), 2) AS porcentaje
FROM asistencias asi
GROUP BY asi.id_comision;"""),
            dict(titulo="Proporción sin * 100", sql="""SELECT asi.id_comision, ROUND(AVG(asi.presente), 2) AS porcentaje
FROM asistencias asi
GROUP BY asi.id_comision;"""),
            dict(titulo="Porcentaje de ausencias", sql="""SELECT asi.id_comision,
       ROUND(SUM(asi.presente = 0) * 100 / COUNT(*), 2) AS porcentaje
FROM asistencias asi
GROUP BY asi.id_comision;"""),
        ],
        tags=["GROUP BY", "SUM", "AVG", "ROUND", "porcentaje"],
    ),
]
