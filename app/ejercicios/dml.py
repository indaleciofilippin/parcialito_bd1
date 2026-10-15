"""Sección: DML — INSERT, UPDATE, DELETE (Clase Semana 10 · Sección 3)."""

# Para los ejercicios abiertos (21a / 21b): se guarda una "firma" de los datos existentes antes de que corra
# el script del usuario, para detectar si en vez de INSERTAR borró o modificó filas que ya estaban.
_FIRMA_INSC = "SELECT COALESCE(SUM(CRC32(CONCAT_WS('|', id_inscripcion, id_alumno, id_comision))), 0) " \
              "FROM inscripcion_alumno_comision WHERE id_inscripcion <= @max_insc"
_FIRMA_COM = "SELECT COALESCE(SUM(CRC32(CONCAT_WS('|', id_comision, id_asignatura, id_docente, id_aula))), 0) " \
             "FROM comisiones WHERE id_comision <= @max_com"
_FIRMA_AC = "SELECT COALESCE(SUM(CRC32(CONCAT_WS('|', id, id_alumno, id_carrera))), 0) " \
            "FROM alumno_carrera WHERE id <= @max_ac"

EJERCICIOS = [
    # ------------------------------------------------------------------ 15
    dict(
        id="dml-15",
        origen="Semana 10 · Ej. 15",
        titulo="Registrar una nueva comisión",
        dificultad=1,
        tipo="dml",
        enunciado="Registrar una nueva comisión indicando: asignatura, docente, aula, horario.\n\n"
                  "Datos: asignatura **7**, docente **72**, aula **9**, **2º cuatrimestre de 2026**, "
                  "cupo **40**, tipo **práctica**.\n\n"
                  "> Ojo: la tabla `comisiones` **no tiene** columna de horario (tiene `anio`, `cuatrimestre`, "
                  "`cupo` y `tipo`). Registrá solo lo que la estructura permite.",
        solucion="""INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo)
VALUES (7, 72, 9, 2026, 2, 40, 'practica');""",
        alternativas=[
            dict(titulo="Sin lista de columnas (pasando NULL al id)", sql="""INSERT INTO comisiones
VALUES (NULL, 7, 72, 9, 2026, 2, 40, 'practica');"""),
        ],
        verificacion="SELECT id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo FROM comisiones",
        pistas=[
            "Es un `INSERT INTO comisiones (...) VALUES (...)`. Mirá en el esquema qué columnas tiene la tabla.",
            "`id_comision` es AUTO_INCREMENT: no lo pongas, MySQL lo genera solo. El horario no existe en la tabla.",
            "Columnas: `(id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo)` y el tipo es un ENUM: `'practica'`.",
        ],
        explicacion="""Sintaxis general:

```sql
INSERT INTO tabla (col1, col2, ...) VALUES (valor1, valor2, ...);
```

Conviene **siempre** escribir la lista de columnas: así el orden de los valores queda claro y no dependés del orden físico de la tabla.

- `id_comision` es `AUTO_INCREMENT`: se omite (o se pasa `NULL`) y MySQL asigna el siguiente número.
- `id_asignatura`, `id_docente` e `id_aula` son **claves foráneas**: los valores tienen que existir en sus tablas, si no da error **1452**.
- `tipo` es `ENUM('teorica','practica')`: solo acepta esos valores (otro valor da error **1265**).

¿Y el horario? La tabla real no lo tiene. Si escribís una columna `horario` MySQL responde **1054 (Unknown column)**. En el parcialito, aclaralo y registrá lo que el modelo permite (o proponé un `ALTER TABLE` aparte).""",
        errores_comunes=[
            "Inventar una columna `horario` → error 1054: la estructura real no la tiene.",
            "Confundir el orden de los valores (por ejemplo docente y aula) → error 1452 si el id no existe, o datos cruzados si existe.",
            "Escribir `'práctico'` o `'Practica'` creyendo que el ENUM acepta cualquier cosa: solo acepta sus valores (las mayúsculas y tildes se ignoran por la colación, pero `'practico'` da 1265).",
        ],
        trampas=[
            dict(titulo="Columna horario inventada", sql="""INSERT INTO comisiones (id_asignatura, id_docente, id_aula, horario, cupo, tipo)
VALUES (7, 72, 9, 'Lunes 18 a 22', 40, 'practica');"""),
            dict(titulo="Docente y aula invertidos", sql="""INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo)
VALUES (7, 9, 72, 2026, 2, 40, 'practica');"""),
            dict(titulo="Valor de ENUM inválido", sql="""INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo)
VALUES (7, 72, 9, 2026, 2, 40, 'practico');"""),
        ],
        tags=["INSERT", "AUTO_INCREMENT", "ENUM", "FOREIGN KEY"],
    ),
    # ------------------------------------------------------------------ 16
    dict(
        id="dml-16",
        origen="Semana 10 · Ej. 16",
        titulo="Registrar una nueva mesa final",
        dificultad=1,
        tipo="dml",
        enunciado="Registrar una nueva mesa final.\n\n"
                  "Datos: asignatura **7**, docente **72**, aula **9**, fecha **14 de diciembre de 2026**, "
                  "turno **Diciembre**, **primer** llamado.",
        solucion="""INSERT INTO mesas_finales (id_asignatura, id_docente, id_aula, fecha, turno, llamado)
VALUES (7, 72, 9, '2026-12-14', 'Diciembre', 1);""",
        verificacion="SELECT id_asignatura, id_docente, id_aula, fecha, turno, llamado FROM mesas_finales",
        pistas=[
            "Mirá las columnas de `mesas_finales`: `id_mesa` es AUTO_INCREMENT, así que no va.",
            "Las fechas en MySQL se escriben como texto en formato `'AAAA-MM-DD'`.",
            "`turno` es `ENUM('Febrero','Julio','Diciembre')` y `llamado` es un número: `1`.",
        ],
        explicacion="""Es un `INSERT` simple, pero con tres detalles de tipos de datos:

```sql
INSERT INTO mesas_finales (id_asignatura, id_docente, id_aula, fecha, turno, llamado)
VALUES (7, 72, 9, '2026-12-14', 'Diciembre', 1);
```

- **Fecha**: siempre entre comillas y en formato `'AAAA-MM-DD'`. `'14/12/2026'` da error **1292**; sin comillas, `2026-12-14` es una resta (= 2000) y también falla.
- **ENUM**: `turno` solo acepta `'Febrero'`, `'Julio'` o `'Diciembre'`. Con esta colación (`utf8mb4_0900_ai_ci`) `'diciembre'` en minúscula se acepta y se guarda como `'Diciembre'`, pero `'Dic'` da error **1265**. Escribilo igual que en la definición.
- **Lista de columnas**: si la omitís, tenés que dar valores para las 7 columnas (incluido el id); con 6 valores da error **1136**.""",
        errores_comunes=[
            "Fecha en formato argentino `'14/12/2026'` → error 1292 (MySQL espera `'AAAA-MM-DD'`).",
            "Abreviar el turno (`'Dic'`) → error 1265: no es un valor del ENUM.",
            "Omitir la lista de columnas y pasar solo 6 valores → error 1136 (la tabla tiene 7 columnas).",
        ],
        trampas=[
            dict(titulo="Fecha en formato dd/mm/aaaa", sql="""INSERT INTO mesas_finales (id_asignatura, id_docente, id_aula, fecha, turno, llamado)
VALUES (7, 72, 9, '14/12/2026', 'Diciembre', 1);"""),
            dict(titulo="Turno abreviado", sql="""INSERT INTO mesas_finales (id_asignatura, id_docente, id_aula, fecha, turno, llamado)
VALUES (7, 72, 9, '2026-12-14', 'Dic', 1);"""),
            dict(titulo="Sin lista de columnas", sql="""INSERT INTO mesas_finales
VALUES (7, 72, 9, '2026-12-14', 'Diciembre', 1);"""),
        ],
        tags=["INSERT", "DATE", "ENUM"],
    ),
    # ------------------------------------------------------------------ 17
    dict(
        id="dml-17",
        origen="Semana 10 · Ej. 17",
        titulo="Pasar inscripciones a «Regular»",
        dificultad=1,
        tipo="dml",
        enunciado="Actualizar el estado de inscripción de determinados alumnos a “Regular”.\n\n"
                  "Concretamente: en la comisión **11**, pasar a **'Regular'** a los alumnos que todavía figuran "
                  "como **'Cursa'**. El resto de las inscripciones (de esa y de otras comisiones) no se toca.",
        solucion="""UPDATE inscripcion_alumno_comision
SET estado = 'Regular'
WHERE id_comision = 11
  AND estado = 'Cursa';""",
        verificacion="SELECT id_inscripcion, estado FROM inscripcion_alumno_comision ORDER BY id_inscripcion",
        pistas=[
            "La tabla es `inscripcion_alumno_comision` y la columna a modificar es `estado`.",
            "«Determinados alumnos» son los que cumplen DOS condiciones a la vez: comisión 11 y estado actual 'Cursa'.",
            "`UPDATE ... SET estado = 'Regular' WHERE id_comision = 11 AND estado = 'Cursa';`",
        ],
        explicacion="""Sintaxis general:

```sql
UPDATE tabla SET columna = valor WHERE condición;
```

Todo el trabajo está en el `WHERE`: tiene que seleccionar **exactamente** las filas a modificar. Acá son dos condiciones que se cumplen **a la vez**, así que van con `AND`:

- `id_comision = 11` → solo esa comisión (sin esto cambiarías 3.601 inscripciones de toda la facultad).
- `estado = 'Cursa'` → sin esto pasarías a «Regular» también a los que ya aprobaron, quedaron libres o se dieron de baja.

Con `OR` el resultado sería la unión: todas las de la comisión 11 **más** todas las 'Cursa' del resto.

Dato: `'regular'` en minúscula también funciona (la colación ignora mayúsculas en el ENUM), pero escribilo como en la definición. En Workbench con *Safe Updates* este `UPDATE` anda porque `id_comision` tiene índice.""",
        errores_comunes=[
            "Olvidar filtrar por comisión → se actualizan los 'Cursa' de todas las comisiones.",
            "Olvidar `estado = 'Cursa'` → se pisan estados como 'Aprobada' o 'Baja'.",
            "Usar `OR` en vez de `AND` entre las dos condiciones.",
        ],
        trampas=[
            dict(titulo="Sin filtrar por comisión", sql="""UPDATE inscripcion_alumno_comision
SET estado = 'Regular'
WHERE estado = 'Cursa';"""),
            dict(titulo="Sin filtrar por estado", sql="""UPDATE inscripcion_alumno_comision
SET estado = 'Regular'
WHERE id_comision = 11;"""),
            dict(titulo="OR en vez de AND", sql="""UPDATE inscripcion_alumno_comision
SET estado = 'Regular'
WHERE id_comision = 11 OR estado = 'Cursa';"""),
        ],
        tags=["UPDATE", "WHERE", "ENUM"],
    ),
    # ------------------------------------------------------------------ 18
    dict(
        id="dml-18",
        origen="Semana 10 · Ej. 18",
        titulo="Aumento del 10% a un departamento",
        dificultad=2,
        tipo="dml",
        enunciado="Incrementar en un **10%** el salario base de los docentes que pertenecen al departamento de "
                  "**'Ciencias Exactas'**. (Buscá el departamento por su nombre, no por su id.)",
        solucion="""UPDATE docentes
SET salario_base = salario_base * 1.10
WHERE id_departamento = (
    SELECT id_departamento
    FROM departamentos
    WHERE nombre = 'Ciencias Exactas'
);""",
        alternativas=[
            dict(titulo="UPDATE con JOIN (MySQL)", sql="""UPDATE docentes d
JOIN departamentos dep ON dep.id_departamento = d.id_departamento
SET d.salario_base = d.salario_base * 1.10
WHERE dep.nombre = 'Ciencias Exactas';"""),
            dict(titulo="Sumando el 10%", sql="""UPDATE docentes
SET salario_base = salario_base + salario_base * 0.10
WHERE id_departamento IN (SELECT id_departamento FROM departamentos WHERE nombre = 'Ciencias Exactas');"""),
        ],
        verificacion="SELECT id_docente, salario_base FROM docentes ORDER BY id_docente",
        pistas=[
            "Es un `UPDATE docentes SET salario_base = ... WHERE ...`.",
            "Aumentar un 10% es multiplicar por `1.10` (o sumar `salario_base * 0.10`).",
            "El nombre del departamento está en otra tabla: usá una subconsulta `(SELECT id_departamento FROM departamentos WHERE nombre = '...')`.",
        ],
        explicacion="""`UPDATE` modifica filas existentes. La parte difícil es el filtro: el enunciado da el **nombre** del departamento, pero `docentes` solo tiene `id_departamento`.

La subconsulta devuelve un único valor (el id de 'Ciencias Exactas'), así que se puede comparar con `=`. Si pudiera devolver varias filas, usá `IN` (con `=` daría error **1242**).

**Nunca** ejecutes un `UPDATE` sin `WHERE`: modificarías a todos los docentes. En Workbench, si tenés activado *Safe Updates* (error **1175**), el `WHERE` tiene que usar una columna con índice (acá `id_departamento` es FK, así que tiene índice).""",
        errores_comunes=[
            "Olvidar el WHERE → aumenta el sueldo a TODOS los docentes.",
            "Escribir `salario_base * 10%` (no existe el operador %) o `* 0.10` (eso deja el 10% del sueldo, no lo aumenta).",
            "Comparar `id_departamento = 'Ciencias Exactas'`: se está comparando un número con un nombre.",
        ],
        trampas=[
            dict(titulo="Sin WHERE", sql="UPDATE docentes SET salario_base = salario_base * 1.10;"),
            dict(titulo="Multiplicar por 0.10", sql="""UPDATE docentes SET salario_base = salario_base * 0.10
WHERE id_departamento = (SELECT id_departamento FROM departamentos WHERE nombre = 'Ciencias Exactas');"""),
            dict(titulo="Sumar 0.10 pesos", sql="""UPDATE docentes SET salario_base = salario_base + 0.10
WHERE id_departamento = (SELECT id_departamento FROM departamentos WHERE nombre = 'Ciencias Exactas');"""),
        ],
        tags=["UPDATE", "subconsulta"],
    ),
    # ------------------------------------------------------------------ 19
    dict(
        id="dml-19",
        origen="Semana 10 · Ej. 19",
        titulo="Eliminar comisiones sin inscriptos",
        dificultad=2,
        tipo="dml",
        enunciado="Eliminar comisiones que actualmente no posean alumnos inscriptos.\n\n"
                  "Con los datos originales **todas** las comisiones tienen inscriptos, así que para este ejercicio "
                  "la app agrega **3 comisiones de 2027 (ids 90101, 90102 y 90103) sin ningún inscripto**. "
                  "Resolvelo sin escribir esos ids: buscá las comisiones que no tienen filas en "
                  "`inscripcion_alumno_comision`.",
        preparacion="""INSERT INTO comisiones (id_comision, id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo) VALUES
 (90101, 10, 20, 3, 2027, 1, 40, 'teorica'),
 (90102, 11, 21, 6, 2027, 1, 25, 'practica'),
 (90103, 12, 22, 9, 2027, 2, 35, 'practica');""",
        solucion="""DELETE FROM comisiones
WHERE id_comision NOT IN (
    SELECT id_comision
    FROM inscripcion_alumno_comision
);""",
        alternativas=[
            dict(titulo="Con NOT EXISTS", sql="""DELETE FROM comisiones
WHERE NOT EXISTS (
    SELECT 1
    FROM inscripcion_alumno_comision i
    WHERE i.id_comision = comisiones.id_comision
);"""),
            dict(titulo="DELETE con LEFT JOIN (MySQL)", sql="""DELETE c
FROM comisiones c
LEFT JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
WHERE i.id_inscripcion IS NULL;"""),
            dict(titulo="Tabla derivada (esquiva el error 1093)", sql="""DELETE FROM comisiones
WHERE id_comision IN (
    SELECT id_comision FROM (
        SELECT c.id_comision
        FROM comisiones c
        LEFT JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
        WHERE i.id_inscripcion IS NULL
    ) AS sin_inscriptos
);"""),
        ],
        verificacion="SELECT id_comision, id_asignatura, anio FROM comisiones ORDER BY id_comision",
        pistas=[
            "Primero escribí el SELECT de «comisiones sin inscriptos» (es el ejercicio 9) y después cambialo por un DELETE.",
            "`DELETE FROM comisiones WHERE id_comision NOT IN (SELECT id_comision FROM inscripcion_alumno_comision);`",
            "Si en la subconsulta usás la tabla `comisiones` otra vez, MySQL da error 1093: no hace falta, alcanza con mirar `inscripcion_alumno_comision`.",
        ],
        explicacion="""Es el ejercicio 9 (ausencia de relación) convertido en `DELETE`:

```sql
DELETE FROM tabla WHERE condición;
```

`NOT IN (SELECT id_comision FROM inscripcion_alumno_comision)` deja solo las comisiones cuyo id **no aparece** en las inscripciones. Esas no tienen filas hijas en esa tabla, así que se pueden borrar. (Si tuvieran exámenes o asistencias cargados, el `DELETE` daría **1451** y habría que borrar esas filas primero.)

**Error 1093**: MySQL no deja que la subconsulta lea la **misma tabla** que estás borrando (`... NOT IN (SELECT c.id_comision FROM comisiones c JOIN ...)`). Soluciones: no usar esa tabla en la subconsulta (como acá), usar `DELETE c FROM comisiones c LEFT JOIN ...`, o envolver la subconsulta en una tabla derivada `(SELECT ... ) AS t`, que MySQL materializa antes de borrar.

*Safe Updates* (Workbench) rechaza este `DELETE` con **1175**; ejecutá antes `SET SQL_SAFE_UPDATES = 0;`.""",
        errores_comunes=[
            "Repetir `comisiones` dentro de la subconsulta → error 1093 (no se puede leer la tabla que se está modificando).",
            "Buscar la ausencia en la tabla equivocada (por ejemplo `examenes`) → intenta borrar comisiones con inscriptos y da 1451.",
            "Ejecutar `DELETE FROM comisiones;` sin WHERE → error 1451 (por suerte las FKs te frenan).",
        ],
        trampas=[
            dict(titulo="Subconsulta sobre la misma tabla (1093)", sql="""DELETE FROM comisiones
WHERE id_comision NOT IN (
    SELECT c.id_comision
    FROM comisiones c
    JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision
);"""),
            dict(titulo="Mirar exámenes en vez de inscripciones", sql="""DELETE FROM comisiones
WHERE id_comision NOT IN (SELECT id_comision FROM examenes);"""),
            dict(titulo="Sin WHERE", sql="DELETE FROM comisiones;"),
        ],
        tags=["DELETE", "NOT IN", "NOT EXISTS", "error 1093", "FOREIGN KEY"],
    ),
    # ------------------------------------------------------------------ 20
    dict(
        id="dml-20",
        origen="Semana 10 · Ej. 20",
        titulo="Eliminar mesas finales vencidas",
        dificultad=3,
        tipo="dml",
        enunciado="Eliminar las **mesas finales cuya fecha ya haya pasado** (anteriores a `'2025-01-01'`). "
                  "Tené en cuenta que las mesas pueden tener alumnos inscriptos en `inscripciones_finales`.",
        solucion="""DELETE FROM inscripciones_finales
WHERE id_mesa IN (SELECT id_mesa FROM mesas_finales WHERE fecha < '2025-01-01');

DELETE FROM mesas_finales
WHERE fecha < '2025-01-01';""",
        alternativas=[
            dict(titulo="Primer paso con DELETE ... JOIN (MySQL)", sql="""DELETE i
FROM inscripciones_finales i
JOIN mesas_finales m ON m.id_mesa = i.id_mesa
WHERE m.fecha < '2025-01-01';

DELETE FROM mesas_finales
WHERE fecha < '2025-01-01';"""),
        ],
        verificacion=[
            "SELECT id_mesa FROM mesas_finales",
            "SELECT id_inscripcion_final FROM inscripciones_finales",
        ],
        pistas=[
            "Probá primero `DELETE FROM mesas_finales WHERE fecha < '2025-01-01';` y mirá el error que da.",
            "Error 1451: hay filas en `inscripciones_finales` que apuntan a esas mesas (FOREIGN KEY).",
            "Hay que borrar primero las filas **hijas** (inscripciones a esas mesas) y después las mesas.",
        ],
        explicacion="""Las claves foráneas protegen la integridad: no se puede borrar una mesa si hay inscripciones que la referencian (error **1451**).

Por eso se hace en dos pasos, **de hijo a padre**:

1. Borrar las inscripciones de esas mesas (`id_mesa IN (subconsulta)`).
2. Borrar las mesas.

Ojo con el límite: «anteriores a» es `<`. Con `<=` también borrarías las 5 mesas del mismo 1/1/2025.

> En la versión «real» del ejercicio se usa `fecha < CURDATE()`. Acá fijamos una fecha para que el resultado no dependa del día en que practiques (además, con `CURDATE()` se borrarían **todas**: en estos datos todas las mesas son pasadas).""",
        errores_comunes=[
            "Borrar directamente las mesas → error 1451 por la FK de inscripciones_finales.",
            "Borrar en el orden inverso (primero mesas, después inscripciones): el primer DELETE ya falla.",
            "Usar `<=` cuando se pide «anteriores a» una fecha.",
        ],
        trampas=[
            dict(titulo="Solo inscripciones", sql="""DELETE FROM inscripciones_finales
WHERE id_mesa IN (SELECT id_mesa FROM mesas_finales WHERE fecha < '2025-01-01');"""),
            dict(titulo="Orden inverso", sql="""DELETE FROM mesas_finales WHERE fecha < '2025-01-01';
DELETE FROM inscripciones_finales
WHERE id_mesa IN (SELECT id_mesa FROM mesas_finales WHERE fecha < '2025-01-01');"""),
            dict(titulo="Menor o igual", sql="""DELETE FROM inscripciones_finales
WHERE id_mesa IN (SELECT id_mesa FROM mesas_finales WHERE fecha <= '2025-01-01');
DELETE FROM mesas_finales WHERE fecha <= '2025-01-01';"""),
        ],
        tags=["DELETE", "FOREIGN KEY", "subconsulta"],
    ),
    # ------------------------------------------------------------------ 21a
    dict(
        id="dml-21a",
        origen="Semana 10 · Ej. 21 (a, b, c)",
        titulo="Casos borde (1/2): alumnos, docentes y aulas",
        dificultad=2,
        tipo="dml",
        enunciado="¿Recordás que varias consultas de ausencia (ejercicios 2, 4, 6…) devuelven vacío? Insertá en la base "
                  "la información necesaria para que haya:\n\n"
                  "- a) al menos **2 alumnos** que no estén inscriptos en ninguna comisión,\n"
                  "- b) al menos **2 docentes** que no tengan comisiones asignadas,\n"
                  "- c) al menos **2 aulas** que no estén asociadas a ninguna comisión.\n\n"
                  "Los registros tienen que respetar la estructura real (NOT NULL, UNIQUE, ENUM, FKs). "
                  "Es un ejercicio **abierto**: los valores los elegís vos. Se pide **insertar**: no vale borrar ni "
                  "modificar inscripciones o comisiones existentes.",
        preparacion="""SET @max_insc = (SELECT MAX(id_inscripcion) FROM inscripcion_alumno_comision);
SET @max_com = (SELECT MAX(id_comision) FROM comisiones);
SET @firma_insc = (%s);
SET @firma_com = (%s);""" % (_FIRMA_INSC, _FIRMA_COM),
        solucion="""INSERT INTO alumnos (nombre, apellido, dni, fecha_nacimiento, email, telefono, fecha_ingreso) VALUES
  ('Tomás', 'Benítez', '45111222', '2005-04-12', 'tomas.benitez@mail.com', '3515550001', '2026-08-01'),
  ('Lara', 'Quiroga', '45333444', '2006-09-30', 'lara.quiroga@mail.com', '3515550002', '2026-08-01');

INSERT INTO docentes (nombre, apellido, email, fecha_ingreso, salario_base, id_departamento) VALUES
  ('Ramiro', 'Ledesma', 'rledesma@universidad.edu', '2026-08-01', 280000.00, 1),
  ('Paula', 'Arce', 'parce@universidad.edu', '2026-08-01', 295000.00, 2);

INSERT INTO aulas (nombre, capacidad, tipo) VALUES
  ('Aula B1', 45, 'normal'),
  ('Laboratorio L4', 24, 'laboratorio');""",
        condiciones=[
            dict(sql="""SELECT COUNT(*) >= 2 FROM alumnos a
WHERE NOT EXISTS (SELECT 1 FROM inscripcion_alumno_comision i WHERE i.id_alumno = a.id_alumno)""",
                 desc="a) Hay al menos 2 alumnos sin inscripciones a comisiones"),
            dict(sql="""SELECT COUNT(*) >= 2 FROM docentes d
WHERE NOT EXISTS (SELECT 1 FROM comisiones c WHERE c.id_docente = d.id_docente)""",
                 desc="b) Hay al menos 2 docentes sin comisiones asignadas"),
            dict(sql="""SELECT COUNT(*) >= 2 FROM aulas au
WHERE NOT EXISTS (SELECT 1 FROM comisiones c WHERE c.id_aula = au.id_aula)""",
                 desc="c) Hay al menos 2 aulas que no se usan en ninguna comisión"),
            dict(sql="SELECT (%s) = @firma_insc AND (%s) = @firma_com" % (_FIRMA_INSC, _FIRMA_COM),
                 desc="No se borraron ni modificaron inscripciones o comisiones existentes",
                 fallo_msg="Modificaste o borraste datos que ya existían: el ejercicio pide INSERTAR registros nuevos."),
        ],
        verificacion=[
            """SELECT a.id_alumno, a.nombre, a.apellido FROM alumnos a
WHERE NOT EXISTS (SELECT 1 FROM inscripcion_alumno_comision i WHERE i.id_alumno = a.id_alumno)""",
            """SELECT d.id_docente, d.nombre, d.apellido FROM docentes d
WHERE NOT EXISTS (SELECT 1 FROM comisiones c WHERE c.id_docente = d.id_docente)""",
            """SELECT au.id_aula, au.nombre FROM aulas au
WHERE NOT EXISTS (SELECT 1 FROM comisiones c WHERE c.id_aula = au.id_aula)""",
        ],
        pistas=[
            "Un alumno recién insertado no tiene inscripciones; un docente nuevo no tiene comisiones; un aula nueva no se usa. Alcanza con INSERTs.",
            "Mirá el esquema: en `alumnos` son obligatorios `nombre`, `apellido` y `dni` (y `dni` y `email` son UNIQUE); en `docentes`, `nombre` y `apellido`.",
            "Podés insertar varias filas en una sola sentencia: `INSERT INTO aulas (nombre, capacidad, tipo) VALUES ('Aula B1', 45, 'normal'), ('Lab L4', 24, 'laboratorio');`",
        ],
        explicacion="""La idea del ejercicio: las consultas de **ausencia** (`NOT EXISTS`, `NOT IN`, `LEFT JOIN ... IS NULL`) devuelven vacío con los datos originales, y una consulta **mal hecha** también devolvería vacío. Insertando casos borde podés comprobar que tu consulta funciona de verdad.

No hace falta nada especial: una fila recién creada no tiene relaciones.

```sql
INSERT INTO tabla (col1, col2, ...) VALUES
  (fila 1),
  (fila 2);
```

Lo que hay que cuidar es la **estructura real**:

- `alumnos`: `nombre`, `apellido`, `dni` son NOT NULL; `dni` y `email` son UNIQUE (un DNI repetido da **1062**).
- `docentes`: `nombre` y `apellido` NOT NULL (si falta uno da **1364**); `email` UNIQUE; `id_departamento` tiene que existir (**1452**).
- `aulas`: `tipo` es ENUM (`'normal'`, `'laboratorio'`, `'centro de computos'`).

Borrar inscripciones de alumnos existentes también «cumple» el punto a), pero no es lo que se pide: el corrector lo detecta.""",
        errores_comunes=[
            "Reusar un DNI o email que ya existe → error 1062 (son UNIQUE).",
            "Omitir el apellido del docente → error 1364 (es NOT NULL y no tiene DEFAULT).",
            "Borrar inscripciones o comisiones existentes para «liberar» alumnos o docentes: se pide insertar datos nuevos.",
        ],
        trampas=[
            dict(titulo="DNI repetido", sql="""INSERT INTO alumnos (nombre, apellido, dni, email) VALUES
  ('Tomás', 'Benítez', '30000001', 'tomas.benitez@mail.com'),
  ('Lara', 'Quiroga', '45333444', 'lara.quiroga@mail.com');
INSERT INTO docentes (nombre, apellido, email) VALUES
  ('Ramiro', 'Ledesma', 'rledesma@universidad.edu'), ('Paula', 'Arce', 'parce@universidad.edu');
INSERT INTO aulas (nombre, capacidad, tipo) VALUES ('Aula B1', 45, 'normal'), ('Laboratorio L4', 24, 'laboratorio');"""),
            dict(titulo="Docente sin apellido", sql="""INSERT INTO alumnos (nombre, apellido, dni, email) VALUES
  ('Tomás', 'Benítez', '45111222', 'tomas.benitez@mail.com'),
  ('Lara', 'Quiroga', '45333444', 'lara.quiroga@mail.com');
INSERT INTO docentes (nombre, email) VALUES ('Ramiro', 'rledesma@universidad.edu'), ('Paula', 'parce@universidad.edu');
INSERT INTO aulas (nombre, capacidad, tipo) VALUES ('Aula B1', 45, 'normal'), ('Laboratorio L4', 24, 'laboratorio');"""),
            dict(titulo="Borrar inscripciones en vez de insertar alumnos", sql="""DELETE FROM inscripcion_alumno_comision WHERE id_alumno IN (1, 2);
INSERT INTO docentes (nombre, apellido, email) VALUES
  ('Ramiro', 'Ledesma', 'rledesma@universidad.edu'), ('Paula', 'Arce', 'parce@universidad.edu');
INSERT INTO aulas (nombre, capacidad, tipo) VALUES ('Aula B1', 45, 'normal'), ('Laboratorio L4', 24, 'laboratorio');"""),
        ],
        tags=["INSERT", "casos borde", "UNIQUE", "NOT NULL"],
    ),
    # ------------------------------------------------------------------ 21b
    dict(
        id="dml-21b",
        origen="Semana 10 · Ej. 21 (d, e)",
        titulo="Casos borde (2/2): carreras y comisiones",
        dificultad=2,
        tipo="dml",
        enunciado="Segunda parte del ejercicio 21. Insertá la información necesaria para que haya:\n\n"
                  "- d) al menos **2 carreras** que no posean alumnos asociados,\n"
                  "- e) al menos **2 comisiones** que no tengan alumnos inscriptos.\n\n"
                  "Los registros tienen que respetar la estructura real (NOT NULL, ENUM, claves foráneas). "
                  "Ejercicio **abierto**: elegís los valores. No vale borrar ni modificar datos existentes.",
        preparacion="""SET @max_insc = (SELECT MAX(id_inscripcion) FROM inscripcion_alumno_comision);
SET @max_ac = (SELECT MAX(id) FROM alumno_carrera);
SET @firma_insc = (%s);
SET @firma_ac = (%s);""" % (_FIRMA_INSC, _FIRMA_AC),
        solucion="""INSERT INTO carreras (nombre, titulo_otorgado, nivel, modalidad, duracion_anios, carga_horaria_total, id_departamento) VALUES
  ('Tecnicatura en Ciencia de Datos', 'Técnico en Ciencia de Datos', 'tecnicatura', 'virtual', 3, 1600, 1),
  ('Licenciatura en Bioquímica', 'Licenciado en Bioquímica', 'grado', 'presencial', 5, 3200, 5);

INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo) VALUES
  (7, 72, 9, 2027, 1, 30, 'practica'),
  (12, 11, 3, 2027, 1, 50, 'teorica');""",
        condiciones=[
            dict(sql="""SELECT COUNT(*) >= 2 FROM carreras c
WHERE NOT EXISTS (SELECT 1 FROM alumno_carrera ac WHERE ac.id_carrera = c.id_carrera)""",
                 desc="d) Hay al menos 2 carreras sin alumnos"),
            dict(sql="""SELECT COUNT(*) >= 2 FROM comisiones co
WHERE NOT EXISTS (SELECT 1 FROM inscripcion_alumno_comision i WHERE i.id_comision = co.id_comision)""",
                 desc="e) Hay al menos 2 comisiones sin inscriptos"),
            dict(sql="SELECT (%s) = @firma_insc AND (%s) = @firma_ac" % (_FIRMA_INSC, _FIRMA_AC),
                 desc="No se borraron ni modificaron inscripciones ni vínculos alumno-carrera existentes",
                 fallo_msg="Modificaste o borraste datos que ya existían: el ejercicio pide INSERTAR registros nuevos."),
        ],
        verificacion=[
            """SELECT c.id_carrera, c.nombre, c.nivel, c.modalidad FROM carreras c
WHERE NOT EXISTS (SELECT 1 FROM alumno_carrera ac WHERE ac.id_carrera = c.id_carrera)""",
            """SELECT co.id_comision, co.id_asignatura, co.id_docente, co.id_aula FROM comisiones co
WHERE NOT EXISTS (SELECT 1 FROM inscripcion_alumno_comision i WHERE i.id_comision = co.id_comision)""",
        ],
        pistas=[
            "Igual que en la parte 1: una carrera o una comisión recién insertada no tiene alumnos.",
            "En `carreras`, `nivel` y `modalidad` son ENUM **NOT NULL**: `nivel` ∈ ('grado','posgrado','tecnicatura'), `modalidad` ∈ ('presencial','virtual','mixta').",
            "En `comisiones`, `id_asignatura`, `id_docente` e `id_aula` son FKs obligatorias: usá ids que existan (por ejemplo asignatura 7, docente 72, aula 9).",
        ],
        explicacion="""Acá la dificultad está en respetar **ENUMs y claves foráneas**:

```sql
INSERT INTO carreras (nombre, titulo_otorgado, nivel, modalidad, duracion_anios, carga_horaria_total, id_departamento)
VALUES ('Tecnicatura en Ciencia de Datos', 'Técnico en Ciencia de Datos', 'tecnicatura', 'virtual', 3, 1600, 1), ...;
```

- `nivel` y `modalidad` son `ENUM ... NOT NULL`: un valor que no está en la lista (`'licenciatura'`) da **1265**; omitirlos tampoco es buena idea.
- Una comisión **necesita** asignatura, docente y aula existentes: un id inexistente da **1452**. Es lógico: no puede haber una comisión «de nadie».
- `id_departamento` de la carrera también es FK.

Después, probá tus consultas de los ejercicios 5 y 9: ahora tienen que devolver tus filas nuevas.""",
        errores_comunes=[
            "Usar un nivel que no existe en el ENUM (`'licenciatura'`) → error 1265.",
            "Crear la comisión con un aula o docente inexistente → error 1452 (FK).",
            "«Vaciar» carreras existentes borrando filas de `alumno_carrera`: se pide insertar, no borrar.",
        ],
        trampas=[
            dict(titulo="Nivel fuera del ENUM", sql="""INSERT INTO carreras (nombre, nivel, modalidad, id_departamento) VALUES
  ('Lic. en Ciencia de Datos', 'licenciatura', 'virtual', 1),
  ('Lic. en Bioquímica', 'licenciatura', 'presencial', 5);
INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo) VALUES
  (7, 72, 9, 2027, 1, 30, 'practica'), (12, 11, 3, 2027, 1, 50, 'teorica');"""),
            dict(titulo="Comisión con aula inexistente", sql="""INSERT INTO carreras (nombre, nivel, modalidad, id_departamento) VALUES
  ('Tecnicatura en Ciencia de Datos', 'tecnicatura', 'virtual', 1),
  ('Licenciatura en Bioquímica', 'grado', 'presencial', 5);
INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo) VALUES
  (7, 72, 99, 2027, 1, 30, 'practica'), (12, 11, 98, 2027, 1, 50, 'teorica');"""),
            dict(titulo="Solo una comisión", sql="""INSERT INTO carreras (nombre, nivel, modalidad, id_departamento) VALUES
  ('Tecnicatura en Ciencia de Datos', 'tecnicatura', 'virtual', 1),
  ('Licenciatura en Bioquímica', 'grado', 'presencial', 5);
INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo) VALUES
  (7, 72, 9, 2027, 1, 30, 'practica');"""),
        ],
        tags=["INSERT", "casos borde", "ENUM", "FOREIGN KEY"],
    ),
    # ================================================================== Variantes
    dict(
        id="dml-n01",
        origen="Variante",
        titulo="Cambiar aula y cupo de una comisión",
        dificultad=1,
        tipo="dml",
        enunciado="Por obras, la comisión **37** se muda al aula **8** ('Laboratorio L3') y, como el laboratorio es "
                  "más chico, su cupo pasa a **30**. Actualizá ambos datos.",
        solucion="""UPDATE comisiones
SET id_aula = 8,
    cupo = 30
WHERE id_comision = 37;""",
        alternativas=[
            dict(titulo="Dos UPDATE separados", sql="""UPDATE comisiones SET id_aula = 8 WHERE id_comision = 37;
UPDATE comisiones SET cupo = 30 WHERE id_comision = 37;"""),
        ],
        verificacion="SELECT id_comision, id_aula, cupo FROM comisiones ORDER BY id_comision",
        pistas=[
            "Un solo `UPDATE` puede modificar varias columnas.",
            "Las asignaciones del `SET` se separan con **comas**, no con `AND`.",
            "`UPDATE comisiones SET id_aula = 8, cupo = 30 WHERE id_comision = 37;`",
        ],
        explicacion="""Sintaxis general:

```sql
UPDATE tabla
SET col1 = valor1, col2 = valor2
WHERE condición;
```

El error clásico es escribir `SET id_aula = 8 AND cupo = 30`. MySQL lo lee como **una sola** asignación: `id_aula = (8 AND (cupo = 30))`. Como el cupo actual es 55, `cupo = 30` es falso, la expresión vale `0` y queda `id_aula = 0`… que no existe → error **1452**. (Si la condición hubiera sido verdadera, habría quedado el aula 1 sin ningún error: peor todavía.)

El `WHERE id_comision = 37` usa la clave primaria: es el filtro más seguro (y pasa *Safe Updates* de Workbench sin problema).""",
        errores_comunes=[
            "Separar las asignaciones con `AND` en vez de coma: se convierte en una expresión lógica.",
            "Olvidar el WHERE → se mudan todas las comisiones al laboratorio.",
            "Filtrar por la columna equivocada (`WHERE id_aula = 37`) → no cambia nada.",
        ],
        trampas=[
            dict(titulo="AND en vez de coma", sql="UPDATE comisiones SET id_aula = 8 AND cupo = 30 WHERE id_comision = 37;"),
            dict(titulo="Sin WHERE", sql="UPDATE comisiones SET id_aula = 8, cupo = 30;"),
            dict(titulo="WHERE sobre la columna equivocada", sql="UPDATE comisiones SET id_aula = 8, cupo = 30 WHERE id_aula = 37;"),
        ],
        tags=["UPDATE", "varias columnas"],
    ),
    dict(
        id="dml-n02",
        origen="Variante",
        titulo="INSERT buscando los ids por nombre",
        dificultad=2,
        tipo="dml",
        enunciado="Registrar una comisión **teórica** de la asignatura **'Gestión de Sistemas 7'** para el "
                  "**1er cuatrimestre de 2027**, con cupo **30**, en el aula **'Laboratorio L2'** y a cargo del docente "
                  "con email **'docente86@universidad.edu'**.\n\n"
                  "No escribas los ids a mano: obtenelos con subconsultas a partir del nombre / email.",
        solucion="""INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo)
VALUES (
    (SELECT id_asignatura FROM asignaturas WHERE nombre = 'Gestión de Sistemas 7'),
    (SELECT id_docente FROM docentes WHERE email = 'docente86@universidad.edu'),
    (SELECT id_aula FROM aulas WHERE nombre = 'Laboratorio L2'),
    2027, 1, 30, 'teorica'
);""",
        alternativas=[
            dict(titulo="INSERT ... SELECT", sql="""INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo)
SELECT asg.id_asignatura, d.id_docente, au.id_aula, 2027, 1, 30, 'teorica'
FROM asignaturas asg, docentes d, aulas au
WHERE asg.nombre = 'Gestión de Sistemas 7'
  AND d.email = 'docente86@universidad.edu'
  AND au.nombre = 'Laboratorio L2';"""),
        ],
        verificacion="SELECT id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo FROM comisiones",
        pistas=[
            "En `VALUES (...)` podés poner una subconsulta entre paréntesis en lugar de un valor, siempre que devuelva **un** valor.",
            "Por ejemplo `(SELECT id_aula FROM aulas WHERE nombre = 'Laboratorio L2')`.",
            "Hacé lo mismo para la asignatura (por `nombre`) y el docente (por `email`, que es UNIQUE).",
        ],
        explicacion="""Una **subconsulta escalar** (devuelve una fila y una columna) se puede usar donde va un valor, también dentro de `VALUES`:

```sql
INSERT INTO comisiones (id_asignatura, ...)
VALUES ((SELECT id_asignatura FROM asignaturas WHERE nombre = '...'), ...);
```

Condiciones para que funcione:
- Tiene que devolver **una sola fila**. Si el filtro es ambiguo (`LIKE 'Laboratorio%'`, `apellido = 'Silva'`) devuelve varias → error **1242**. Por eso conviene buscar por una columna única (el email del docente es UNIQUE).
- Si no encuentra nada devuelve `NULL`, y como las FKs de `comisiones` son NOT NULL → error **1048**. Fijate que el nombre esté bien escrito (la colación ignora tildes y mayúsculas, pero no el número de la asignatura).

La alternativa `INSERT ... SELECT` arma la fila con un SELECT sobre las tres tablas.""",
        errores_comunes=[
            "Filtrar con LIKE o por un dato repetido (apellido) → la subconsulta devuelve varias filas: error 1242.",
            "Escribir mal el nombre → la subconsulta da NULL → error 1048 (columna NOT NULL).",
            "Olvidar los paréntesis alrededor de cada subconsulta dentro de VALUES.",
        ],
        trampas=[
            dict(titulo="Aula con LIKE (varias filas)", sql="""INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo)
VALUES ((SELECT id_asignatura FROM asignaturas WHERE nombre = 'Gestión de Sistemas 7'),
        (SELECT id_docente FROM docentes WHERE email = 'docente86@universidad.edu'),
        (SELECT id_aula FROM aulas WHERE nombre LIKE 'Laboratorio%'),
        2027, 1, 30, 'teorica');"""),
            dict(titulo="Docente por apellido", sql="""INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo)
VALUES ((SELECT id_asignatura FROM asignaturas WHERE nombre = 'Gestión de Sistemas 7'),
        (SELECT id_docente FROM docentes WHERE apellido = 'Silva'),
        (SELECT id_aula FROM aulas WHERE nombre = 'Laboratorio L2'),
        2027, 1, 30, 'teorica');"""),
            dict(titulo="Nombre de asignatura incompleto", sql="""INSERT INTO comisiones (id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo)
VALUES ((SELECT id_asignatura FROM asignaturas WHERE nombre = 'Gestión de Sistemas'),
        (SELECT id_docente FROM docentes WHERE email = 'docente86@universidad.edu'),
        (SELECT id_aula FROM aulas WHERE nombre = 'Laboratorio L2'),
        2027, 1, 30, 'teorica');"""),
        ],
        tags=["INSERT", "subconsulta escalar", "error 1242"],
    ),
    dict(
        id="dml-n03",
        origen="Variante",
        titulo="Inscripción masiva con INSERT ... SELECT",
        dificultad=2,
        tipo="dml",
        enunciado="Se abrió la comisión **90201**, un curso de nivelación para 2027 (para este ejercicio la app ya la "
                  "creó). Inscribí en ella a **todos los alumnos que tienen la carrera 'Ingeniería en Sistemas' en "
                  "estado 'activa'**, con fecha de inscripción **'2027-03-01'** y estado **'Cursa'**.\n\n"
                  "Hacelo con una sola sentencia (sin escribir los alumnos uno por uno).",
        preparacion="""INSERT INTO comisiones (id_comision, id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo)
VALUES (90201, 7, 86, 9, 2027, 1, 30, 'practica');""",
        solucion="""INSERT INTO inscripcion_alumno_comision (id_alumno, id_comision, fecha_inscripcion, estado)
SELECT ac.id_alumno, 90201, '2027-03-01', 'Cursa'
FROM alumno_carrera ac
JOIN carreras c ON c.id_carrera = ac.id_carrera
WHERE c.nombre = 'Ingeniería en Sistemas'
  AND ac.estado = 'activa';""",
        alternativas=[
            dict(titulo="Con subconsulta para la carrera", sql="""INSERT INTO inscripcion_alumno_comision (id_alumno, id_comision, fecha_inscripcion, estado)
SELECT id_alumno, 90201, '2027-03-01', 'Cursa'
FROM alumno_carrera
WHERE estado = 'activa'
  AND id_carrera = (SELECT id_carrera FROM carreras WHERE nombre = 'Ingeniería en Sistemas');"""),
        ],
        verificacion="SELECT id_alumno, id_comision, fecha_inscripcion, estado FROM inscripcion_alumno_comision",
        pistas=[
            "Existe `INSERT INTO tabla (columnas) SELECT ...`: inserta todas las filas que devuelve el SELECT.",
            "Primero armá el SELECT que lista los `id_alumno` con carrera 'Ingeniería en Sistemas' activa (JOIN `alumno_carrera` con `carreras`).",
            "En el SELECT podés poner constantes como columnas: `SELECT ac.id_alumno, 90201, '2027-03-01', 'Cursa' FROM ...`.",
        ],
        explicacion="""`INSERT ... SELECT` inserta **el resultado de una consulta**:

```sql
INSERT INTO destino (c1, c2, c3)
SELECT x, constante, 'texto' FROM origen WHERE ...;
```

Las columnas del SELECT se asignan **por posición** a la lista del INSERT, y pueden ser constantes (`90201`, `'2027-03-01'`, `'Cursa'`), que se repiten en cada fila.

Acá el SELECT devuelve los 21 alumnos activos en Ingeniería en Sistemas.

Errores típicos:
- `VALUES ((SELECT id_alumno FROM ...), ...)` → la subconsulta devuelve 21 filas: error **1242**. `VALUES` es para valores sueltos; para muchas filas va `INSERT ... SELECT`.
- Filtrar `LIKE 'Ingeniería%'` toma las 5 ingenierías: hay alumnos en dos de ellas y la UNIQUE `(id_alumno, id_comision)` corta con **1062** (se arreglaría con `DISTINCT`, pero tampoco es lo pedido).

Dato: si omitís `estado`, MySQL pone `'Cursa'` porque en un ENUM NOT NULL sin DEFAULT el valor por defecto es el primero de la lista.""",
        errores_comunes=[
            "Usar `VALUES` con una subconsulta que devuelve varias filas → error 1242.",
            "Olvidar `estado = 'activa'` → se inscriben también graduados y abandonados.",
            "Filtrar la carrera con LIKE y traer otras carreras → filas de más o error 1062 por alumnos repetidos.",
        ],
        trampas=[
            dict(titulo="VALUES con subconsulta de varias filas", sql="""INSERT INTO inscripcion_alumno_comision (id_alumno, id_comision, fecha_inscripcion, estado)
VALUES ((SELECT id_alumno FROM alumno_carrera WHERE id_carrera = 1 AND estado = 'activa'), 90201, '2027-03-01', 'Cursa');"""),
            dict(titulo="Sin filtrar el estado de la carrera", sql="""INSERT INTO inscripcion_alumno_comision (id_alumno, id_comision, fecha_inscripcion, estado)
SELECT ac.id_alumno, 90201, '2027-03-01', 'Cursa'
FROM alumno_carrera ac JOIN carreras c ON c.id_carrera = ac.id_carrera
WHERE c.nombre = 'Ingeniería en Sistemas';"""),
            dict(titulo="Todas las ingenierías", sql="""INSERT INTO inscripcion_alumno_comision (id_alumno, id_comision, fecha_inscripcion, estado)
SELECT ac.id_alumno, 90201, '2027-03-01', 'Cursa'
FROM alumno_carrera ac JOIN carreras c ON c.id_carrera = ac.id_carrera
WHERE c.nombre LIKE 'Ingeniería%' AND ac.estado = 'activa';"""),
        ],
        tags=["INSERT ... SELECT", "JOIN"],
    ),
    dict(
        id="dml-n04",
        origen="Variante",
        titulo="Corregir «aprobado» según la nota (CASE)",
        dificultad=2,
        tipo="dml",
        enunciado="En la tabla `notas`, la columna `aprobado` quedó **incoherente** con la nota (hay 24.815 filas mal). "
                  "Corregila para **todas** las notas: `aprobado` debe valer **1** si la nota es **mayor o igual a 4** "
                  "y **0** en caso contrario.\n\n"
                  "(La primera verificación lista las notas incoherentes: después de tu UPDATE no tiene que quedar ninguna.)",
        solucion="""UPDATE notas
SET aprobado = CASE
                   WHEN nota >= 4 THEN 1
                   ELSE 0
               END;""",
        alternativas=[
            dict(titulo="Expresión booleana directa", sql="UPDATE notas SET aprobado = (nota >= 4);"),
        ],
        verificacion=[
            "SELECT id_nota, nota, aprobado FROM notas WHERE NOT (aprobado <=> (nota >= 4)) ORDER BY id_nota",
            "SELECT COUNT(*) AS filas, COUNT(aprobado) AS con_valor, SUM(aprobado) AS aprobados, SUM(nota) AS suma_notas FROM notas",
        ],
        pistas=[
            "Es un UPDATE sobre **todas** las filas: no lleva WHERE (pero en Workbench Safe Updates lo va a frenar).",
            "`CASE WHEN condición THEN valor ELSE otro_valor END` se puede usar como valor en el `SET`.",
            "`SET aprobado = CASE WHEN nota >= 4 THEN 1 ELSE 0 END`.",
        ],
        explicacion="""`CASE` permite calcular el valor nuevo según una condición, fila por fila:

```sql
UPDATE tabla
SET col = CASE
            WHEN condición1 THEN valor1
            WHEN condición2 THEN valor2
            ELSE valor_por_defecto
          END;
```

Detalles importantes:
- **El `ELSE` importa**: sin él, las filas que no cumplen ningún `WHEN` quedan en `NULL` (no en 0).
- **Los bordes**: aprobado es `>= 4`. Con `> 4`, las 62 notas exactamente 4 quedarían desaprobadas.
- En MySQL una comparación ya devuelve 1 o 0, así que `SET aprobado = (nota >= 4)` hace lo mismo (y también `IF(nota >= 4, 1, 0)`).

Este UPDATE no tiene `WHERE` a propósito (son todas las filas). En Workbench con *Safe Updates* da error **1175**: ejecutá antes `SET SQL_SAFE_UPDATES = 0;` (o agregá `WHERE id_nota > 0`).""",
        errores_comunes=[
            "Olvidar el ELSE del CASE → los desaprobados quedan con NULL.",
            "Usar `> 4` en vez de `>= 4` → los cuatros quedan desaprobados.",
            "Hacer dos UPDATE pero olvidarse del segundo (solo se marcan los aprobados y quedan 1 viejos en notas bajas).",
        ],
        trampas=[
            dict(titulo="CASE sin ELSE", sql="UPDATE notas SET aprobado = CASE WHEN nota >= 4 THEN 1 END;"),
            dict(titulo="Mayor estricto", sql="UPDATE notas SET aprobado = CASE WHEN nota > 4 THEN 1 ELSE 0 END;"),
            dict(titulo="Solo marcar los aprobados", sql="UPDATE notas SET aprobado = 1 WHERE nota >= 4;"),
        ],
        tags=["UPDATE", "CASE", "Safe Updates"],
    ),
]
