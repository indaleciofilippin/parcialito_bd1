"""Sección: Consultas básicas sobre una sola tabla (TP1 · Parte A + variantes)."""

EJERCICIOS = [
    # ------------------------------------------------------------------
    # Originales del TP1 · Parte A
    # ------------------------------------------------------------------
    dict(
        id="bas-01",
        origen="TP1 · Parte A · Ej. 1",
        titulo="Alumnos nacidos después del 2000",
        dificultad=1,
        tipo="select",
        enunciado="Obtener el nombre, apellido y fecha de nacimiento de todos los alumnos nacidos después del "
                  "1 de enero del año 2000.",
        solucion="""SELECT nombre, apellido, fecha_nacimiento
FROM alumnos
WHERE fecha_nacimiento > '2000-01-01';""",
        pistas=[
            "Es una sola tabla: `alumnos`. Elegí las tres columnas que pide y filtrá con `WHERE`.",
            "Las fechas en MySQL se escriben como texto con formato `'AAAA-MM-DD'`.",
            "`WHERE fecha_nacimiento > '2000-01-01'`.",
        ],
        explicacion="""Una consulta básica tiene tres partes: **qué columnas** (`SELECT`), **de qué tabla** (`FROM`) y **qué filas** (`WHERE`).

Las fechas se comparan como fechas si las escribís entre comillas con el formato `'AAAA-MM-DD'`: MySQL convierte `'2000-01-01'` a `DATE` y compara cronológicamente.

«Después del 1 de enero» es estrictamente mayor (`>`). Con estos datos nadie nació justo ese día, así que `>=` da lo mismo, pero en el parcialito respetá lo que dice el enunciado.

Ojo con `YEAR(fecha_nacimiento) > 2000`: eso deja afuera a todo el año 2000 (los nacidos entre el 2 de enero y el 31 de diciembre de 2000 sí cumplen la condición).""",
        errores_comunes=[
            "Usar `YEAR(fecha_nacimiento) > 2000`: excluye a los nacidos durante el 2000 (después del 1/1), que sí van.",
            "Comparar con un número (`fecha_nacimiento > 2000`): MySQL compara la fecha como número (20050314 > 2000) y devuelve TODOS los alumnos.",
            "Escribir la fecha en formato argentino (`'01/01/2000'`): MySQL no la interpreta como fecha.",
        ],
        trampas=[
            dict(titulo="Comparar el año con YEAR() > 2000", sql="""SELECT nombre, apellido, fecha_nacimiento
FROM alumnos
WHERE YEAR(fecha_nacimiento) > 2000;"""),
            dict(titulo="Comparar la fecha con el número 2000", sql="""SELECT nombre, apellido, fecha_nacimiento
FROM alumnos
WHERE fecha_nacimiento > 2000;"""),
            dict(titulo="Condición al revés", sql="""SELECT nombre, apellido, fecha_nacimiento
FROM alumnos
WHERE fecha_nacimiento < '2000-01-01';"""),
        ],
        tags=["SELECT", "WHERE", "fechas"],
    ),
    dict(
        id="bas-02",
        origen="TP1 · Parte A · Ej. 2",
        titulo="Asignaturas obligatorias",
        dificultad=1,
        tipo="select",
        enunciado="Listar todas las asignaturas que sean obligatorias (`es_obligatoria = TRUE`).",
        solucion="""SELECT *
FROM asignaturas
WHERE es_obligatoria = TRUE;""",
        alternativas=[
            dict(titulo="Comparando con 1", sql="""SELECT *
FROM asignaturas
WHERE es_obligatoria = 1;"""),
            dict(titulo="Usando la columna como condición", sql="""SELECT *
FROM asignaturas
WHERE es_obligatoria;"""),
        ],
        columnas=[
            ["id_asignatura", "nombre", "creditos", "carga_horaria", "es_obligatoria", "id_departamento"],
            ["id_asignatura", "nombre"],
            ["id_asignatura"],
            ["nombre"],
        ],
        pistas=[
            "«Listar todas las asignaturas» sin decir qué columnas: podés usar `SELECT *` o, al menos, id y nombre.",
            "`es_obligatoria` es `TINYINT(1)`: MySQL guarda los booleanos como 1 (verdadero) y 0 (falso).",
            "`WHERE es_obligatoria = TRUE` (o `= 1`).",
        ],
        explicacion="""MySQL no tiene un tipo booleano «de verdad»: `BOOLEAN` es un alias de `TINYINT(1)`, y `TRUE`/`FALSE` son simplemente `1` y `0`. Por eso estas tres condiciones son equivalentes:

```sql
WHERE es_obligatoria = TRUE
WHERE es_obligatoria = 1
WHERE es_obligatoria        -- cualquier valor distinto de 0 es verdadero
```

Lo que **no** funciona es `= 'TRUE'` entre comillas: es un texto, MySQL lo convierte a número, le da `0` y termina devolviendo las asignaturas **optativas**.

Como el enunciado no fija columnas, `SELECT *` es válido; el corrector también acepta si mostrás solo id y/o nombre.""",
        errores_comunes=[
            "Escribir `es_obligatoria = 'TRUE'` (con comillas): el texto se convierte a 0 y te devuelve las NO obligatorias.",
            "Confundir 1 y 0: `es_obligatoria = 0` son las optativas.",
        ],
        trampas=[
            dict(titulo="TRUE entre comillas", sql="""SELECT *
FROM asignaturas
WHERE es_obligatoria = 'TRUE';"""),
            dict(titulo="Las optativas (= 0)", sql="""SELECT *
FROM asignaturas
WHERE es_obligatoria = 0;"""),
        ],
        tags=["SELECT", "WHERE", "booleanos"],
    ),
    dict(
        id="bas-03",
        origen="TP1 · Parte A · Ej. 3",
        titulo="Aulas con capacidad mayor a 40",
        dificultad=1,
        tipo="select",
        enunciado="Mostrar todas las aulas cuya capacidad sea mayor a 40 alumnos.",
        solucion="""SELECT *
FROM aulas
WHERE capacidad > 40;""",
        columnas=[
            ["id_aula", "nombre", "capacidad", "tipo"],
            ["id_aula", "nombre", "capacidad"],
            ["nombre", "capacidad"],
            ["id_aula", "nombre"],
            ["id_aula"],
            ["nombre"],
        ],
        pistas=[
            "Tabla `aulas`, columna `capacidad`.",
            "«Mayor a 40» no incluye al 40.",
            "`WHERE capacidad > 40`.",
        ],
        explicacion="""Un filtro numérico simple. La clave está en leer bien el operador:

| enunciado | operador |
|---|---|
| mayor a 40 | `> 40` |
| 40 o más / al menos 40 | `>= 40` |
| menor a 40 | `< 40` |
| distinto de 40 | `<>` o `!=` |

Hay dos aulas con capacidad **exactamente 40** (Aula A1 y Centro Cómputos C1): con `>=` aparecerían y el resultado estaría mal. Los números van **sin comillas**.""",
        errores_comunes=[
            "Usar `>= 40`: incluye las aulas de capacidad exactamente 40, que no son «mayores a 40».",
            "Poner el número entre comillas (`'40'`): funciona por conversión implícita, pero es un mal hábito con columnas numéricas.",
        ],
        trampas=[
            dict(titulo="Mayor o igual (>=)", sql="""SELECT *
FROM aulas
WHERE capacidad >= 40;"""),
        ],
        tags=["SELECT", "WHERE", "comparación"],
    ),
    dict(
        id="bas-04",
        origen="TP1 · Parte A · Ej. 4",
        titulo="Docentes con salario mayor a $350000",
        dificultad=1,
        tipo="select",
        enunciado="Obtener todos los docentes cuyo salario base sea superior a $350000.",
        solucion="""SELECT *
FROM docentes
WHERE salario_base > 350000;""",
        columnas=[
            ["id_docente", "nombre", "apellido", "email", "fecha_ingreso", "salario_base", "id_departamento"],
            ["id_docente", "nombre", "apellido", "salario_base"],
            ["nombre", "apellido", "salario_base"],
            ["id_docente", "nombre", "apellido"],
            ["id_docente"],
            ["nombre", "apellido"],
        ],
        pistas=[
            "Tabla `docentes`, columna `salario_base`.",
            "El número va sin `$` y sin separadores de miles.",
            "`WHERE salario_base > 350000`.",
        ],
        explicacion="""El filtro es directo: `salario_base > 350000`.

Lo importante es **cómo escribir el número**:

- Sin signo `$`: `'$350000'` es un texto; MySQL lo convierte a número, le da `0` y devuelve **todos** los docentes.
- Sin punto de miles: en SQL el punto es el separador **decimal**, así que `350.000` es 350 (trescientos cincuenta) y también devuelve a todos.

`salario_base` es `DECIMAL(10,2)`, así que la comparación es exacta. Como el enunciado dice «todos los docentes», `SELECT *` es válido; también alcanza con id o nombre y apellido.""",
        errores_comunes=[
            "Escribir `350.000` con punto de miles: en SQL eso es 350 con decimales, no trescientos cincuenta mil.",
            "Copiar el `$` del enunciado (`> '$350000'`): el texto se convierte a 0 y pasan todos.",
        ],
        trampas=[
            dict(titulo="Punto como separador de miles", sql="""SELECT *
FROM docentes
WHERE salario_base > 350.000;"""),
            dict(titulo="Con el signo $", sql="""SELECT *
FROM docentes
WHERE salario_base > '$350000';"""),
        ],
        tags=["SELECT", "WHERE", "DECIMAL"],
    ),
    dict(
        id="bas-05",
        origen="TP1 · Parte A · Ej. 5",
        titulo="Carreras de modalidad virtual",
        dificultad=1,
        tipo="select",
        enunciado="Listar todas las carreras cuya modalidad sea `'virtual'`.",
        solucion="""SELECT *
FROM carreras
WHERE modalidad = 'virtual';""",
        columnas=[
            ["id_carrera", "nombre", "titulo_otorgado", "nivel", "modalidad", "duracion_anios",
             "carga_horaria_total", "id_departamento"],
            ["id_carrera", "nombre", "modalidad"],
            ["nombre", "modalidad"],
            ["id_carrera", "nombre"],
            ["id_carrera"],
            ["nombre"],
        ],
        pistas=[
            "Tabla `carreras`, columna `modalidad`.",
            "`modalidad` es un `ENUM('presencial','virtual','mixta')`: se compara como texto, entre comillas.",
            "`WHERE modalidad = 'virtual'`.",
        ],
        explicacion="""Los valores de texto (y de `ENUM`) van **entre comillas simples**. Sin comillas, MySQL interpreta la palabra como un identificador (nombre de columna): con `presencial` daría *Unknown column*, y con `virtual` directamente da **error de sintaxis**, porque `VIRTUAL` es palabra reservada.

`ENUM` limita los valores posibles a una lista fija; para filtrar se usa igual que un `VARCHAR`. La comparación no distingue mayúsculas (`'Virtual'` también funciona) por la *collation* de la base.

«Mixta» es otra modalidad distinta: no hay que incluirla. Con estos datos hay solo 2 carreras virtuales (Tecnicatura en Programación y Licenciatura en Administración).""",
        errores_comunes=[
            "Olvidar las comillas: `WHERE modalidad = virtual` da error (MySQL lo toma como identificador, y además `VIRTUAL` es palabra reservada).",
            "Incluir las carreras mixtas: el enunciado pide solo `'virtual'`.",
        ],
        trampas=[
            dict(titulo="Sin comillas", sql="""SELECT *
FROM carreras
WHERE modalidad = virtual;"""),
            dict(titulo="Virtual o mixta", sql="""SELECT *
FROM carreras
WHERE modalidad IN ('virtual', 'mixta');"""),
        ],
        tags=["SELECT", "WHERE", "ENUM"],
    ),

    # ------------------------------------------------------------------
    # Variantes nuevas (de menor a mayor dificultad)
    # ------------------------------------------------------------------
    dict(
        id="bas-n01",
        origen="Variante",
        titulo="Asignaturas de Programación (LIKE)",
        dificultad=1,
        tipo="select",
        enunciado="Mostrá el id y el nombre de las asignaturas cuyo nombre **contenga** la palabra "
                  "'Programación' (por ejemplo «Taller de Programación 135»).",
        solucion="""SELECT id_asignatura, nombre
FROM asignaturas
WHERE nombre LIKE '%Programación%';""",
        columnas=[["id_asignatura", "nombre"], ["nombre"]],
        pistas=[
            "Para buscar un pedazo de texto se usa `LIKE` con comodines.",
            "`%` reemplaza a cualquier cantidad de caracteres (incluso ninguno).",
            "«Contiene» = `%` adelante y atrás: `LIKE '%Programación%'`.",
        ],
        explicacion="""`LIKE` compara contra un **patrón**:

- `%` = cualquier secuencia de caracteres (cero o más).
- `_` = exactamente un carácter.

| patrón | significa |
|---|---|
| `'Prog%'` | empieza con «Prog» |
| `'%135'` | termina en «135» |
| `'%Programación%'` | contiene «Programación» en cualquier lugar |

Acá los nombres tienen la forma «Taller de Programación 135», así que la palabra está **en el medio**: hacen falta los dos `%`.

Con la *collation* de esta base (`utf8mb4_0900_ai_ci`) la comparación no distingue mayúsculas ni tildes: `'%programacion%'` da el mismo resultado.""",
        errores_comunes=[
            "Usar `=` en lugar de `LIKE`: `nombre = 'Programación'` busca un nombre idéntico y no encuentra nada.",
            "Poner `%` de un solo lado: `'Programación%'` exige que el nombre EMPIECE con esa palabra.",
        ],
        trampas=[
            dict(titulo="Igualdad en vez de LIKE", sql="""SELECT id_asignatura, nombre
FROM asignaturas
WHERE nombre = 'Programación';"""),
            dict(titulo="Comodín solo al final", sql="""SELECT id_asignatura, nombre
FROM asignaturas
WHERE nombre LIKE 'Programación%';"""),
        ],
        tags=["LIKE", "WHERE"],
    ),
    dict(
        id="bas-n02",
        origen="Variante",
        titulo="Alumnos que ingresaron en 2022 (BETWEEN)",
        dificultad=1,
        tipo="select",
        enunciado="Mostrá nombre, apellido y fecha de ingreso de los alumnos que ingresaron a la universidad "
                  "durante el año **2022** (del 1 de enero al 31 de diciembre, inclusive).",
        solucion="""SELECT nombre, apellido, fecha_ingreso
FROM alumnos
WHERE fecha_ingreso BETWEEN '2022-01-01' AND '2022-12-31';""",
        alternativas=[
            dict(titulo="Con YEAR()", sql="""SELECT nombre, apellido, fecha_ingreso
FROM alumnos
WHERE YEAR(fecha_ingreso) = 2022;"""),
            dict(titulo="Con >= y <", sql="""SELECT nombre, apellido, fecha_ingreso
FROM alumnos
WHERE fecha_ingreso >= '2022-01-01'
  AND fecha_ingreso < '2023-01-01';"""),
        ],
        pistas=[
            "Es un rango de fechas sobre `fecha_ingreso`.",
            "`BETWEEN a AND b` incluye los dos extremos.",
            "`WHERE fecha_ingreso BETWEEN '2022-01-01' AND '2022-12-31'` (o `YEAR(fecha_ingreso) = 2022`).",
        ],
        explicacion="""`BETWEEN a AND b` equivale a `>= a AND <= b`: **incluye los dos extremos**. Por eso el rango correcto termina en `'2022-12-31'`.

Hay tres formas equivalentes:

```sql
WHERE fecha_ingreso BETWEEN '2022-01-01' AND '2022-12-31'
WHERE YEAR(fecha_ingreso) = 2022
WHERE fecha_ingreso >= '2022-01-01' AND fecha_ingreso < '2023-01-01'
```

`YEAR()` es la más legible. La primera y la tercera, en cambio, pueden aprovechar un índice sobre la columna.

Hay un alumno que ingresó justo el **2022-12-31**: si usás `< '2022-12-31'` lo perdés.

> Cuidado: si la columna fuera `DATETIME`, `BETWEEN ... AND '2022-12-31'` cortaría a las 00:00 del 31. Acá es `DATE`, no hay problema.""",
        errores_comunes=[
            "Usar `>` y `<` estrictos: se pierden los extremos (acá, el alumno que ingresó el 31/12/2022).",
            "Comparar la fecha con el número 2022 (`fecha_ingreso = 2022`): no devuelve nada. Para el año usá `YEAR()`.",
        ],
        trampas=[
            dict(titulo="Desigualdades estrictas", sql="""SELECT nombre, apellido, fecha_ingreso
FROM alumnos
WHERE fecha_ingreso > '2022-01-01' AND fecha_ingreso < '2022-12-31';"""),
            dict(titulo="Fecha igual al número 2022", sql="""SELECT nombre, apellido, fecha_ingreso
FROM alumnos
WHERE fecha_ingreso = 2022;"""),
        ],
        tags=["BETWEEN", "fechas", "YEAR"],
    ),
    dict(
        id="bas-n03",
        origen="Variante",
        titulo="Períodos con comisiones (DISTINCT)",
        dificultad=1,
        tipo="select",
        enunciado="Listá **sin repetir** los años y cuatrimestres en los que se dictaron comisiones, "
                  "ordenados por año y luego por cuatrimestre (de menor a mayor).",
        solucion="""SELECT DISTINCT anio, cuatrimestre
FROM comisiones
ORDER BY anio, cuatrimestre;""",
        orden=[("anio", "asc"), ("cuatrimestre", "asc")],
        pistas=[
            "Los datos están en `comisiones` (columnas `anio` y `cuatrimestre`).",
            "Hay 1200 comisiones pero muy pocas combinaciones distintas de año + cuatrimestre.",
            "`SELECT DISTINCT anio, cuatrimestre ... ORDER BY anio, cuatrimestre`.",
        ],
        explicacion="""`DISTINCT` elimina las filas **repetidas del resultado**, mirando **todas** las columnas del `SELECT` juntas. Acá cada combinación (año, cuatrimestre) aparece una sola vez: de 1200 filas pasamos a 6.

`DISTINCT` va una sola vez, justo después de `SELECT`, y afecta a la fila completa (no a una columna). `SELECT DISTINCT anio, DISTINCT cuatrimestre` es un error de sintaxis.

`ORDER BY anio, cuatrimestre` ordena primero por año y, dentro del mismo año, por cuatrimestre. Si no ponés `ASC`/`DESC`, el orden es ascendente.""",
        errores_comunes=[
            "Olvidar `DISTINCT`: aparece cada combinación cientos de veces (una por comisión).",
            "Poner `DISTINCT` solo sobre `anio`: perdés la información del cuatrimestre.",
            "Creer que `DISTINCT` se aplica a una sola columna: siempre mira la fila entera del SELECT.",
        ],
        trampas=[
            dict(titulo="Sin DISTINCT", sql="""SELECT anio, cuatrimestre
FROM comisiones
ORDER BY anio, cuatrimestre;"""),
            dict(titulo="Orden descendente", sql="""SELECT DISTINCT anio, cuatrimestre
FROM comisiones
ORDER BY anio DESC, cuatrimestre DESC;"""),
        ],
        tags=["DISTINCT", "ORDER BY"],
    ),
    dict(
        id="bas-n04",
        origen="Variante",
        titulo="Nombre con 'Ma' y apellido de 4 letras",
        dificultad=2,
        tipo="select",
        enunciado="Mostrá nombre y apellido de los alumnos cuyo nombre **empiece con 'Ma'** y cuyo apellido "
                  "tenga **exactamente 4 letras** (como «Ruiz»).",
        solucion="""SELECT nombre, apellido
FROM alumnos
WHERE nombre LIKE 'Ma%'
  AND apellido LIKE '____';""",
        alternativas=[
            dict(titulo="Con CHAR_LENGTH()", sql="""SELECT nombre, apellido
FROM alumnos
WHERE nombre LIKE 'Ma%'
  AND CHAR_LENGTH(apellido) = 4;"""),
        ],
        pistas=[
            "Son dos condiciones unidas con `AND`, las dos con `LIKE`.",
            "«Empieza con» = `'Ma%'`. Para contar caracteres exactos usá `_` (cada `_` es UN carácter).",
            "`apellido LIKE '____'` (cuatro guiones bajos, sin `%`).",
        ],
        explicacion="""Los dos comodines de `LIKE` cumplen roles distintos:

- `'Ma%'`: empieza con «Ma» y después **cualquier cosa** (María, Mateo, Martín, Martina).
- `'____'`: **exactamente cuatro** caracteres, ni uno más ni uno menos (Ruiz, Díaz).

Si agregás un `%` al patrón de 4 (`'____%'` o `'%____%'`) pasa a significar «4 **o más**» y entran casi todos.

La alternativa es `CHAR_LENGTH(apellido) = 4`, que cuenta **caracteres**. No la confundas con `LENGTH()`, que cuenta **bytes**: en UTF-8 la «í» de Díaz ocupa 2 bytes, así que `LENGTH('Díaz')` da 5 y ese apellido quedaría afuera.""",
        errores_comunes=[
            "Usar `LENGTH()` en vez de `CHAR_LENGTH()`: cuenta bytes y las letras con tilde ocupan 2 (Díaz «mide» 5).",
            "Agregar `%` al patrón de 4 letras: `'____%'` significa «al menos 4».",
            "Usar `'%Ma%'`: eso es «contiene Ma» y trae también a Tomás o Emma.",
        ],
        trampas=[
            dict(titulo="LENGTH cuenta bytes", sql="""SELECT nombre, apellido
FROM alumnos
WHERE nombre LIKE 'Ma%' AND LENGTH(apellido) = 4;"""),
            dict(titulo="Cuatro o más letras", sql="""SELECT nombre, apellido
FROM alumnos
WHERE nombre LIKE 'Ma%' AND apellido LIKE '____%';"""),
            dict(titulo="Contiene 'Ma' en vez de empieza", sql="""SELECT nombre, apellido
FROM alumnos
WHERE nombre LIKE '%Ma%' AND apellido LIKE '____';"""),
        ],
        tags=["LIKE", "comodines", "CHAR_LENGTH"],
    ),
    dict(
        id="bas-n05",
        origen="Variante",
        titulo="Asignaturas de 60 a 70 horas, ordenadas",
        dificultad=2,
        tipo="select",
        enunciado="Mostrá nombre, créditos y carga horaria de las asignaturas que tengan **entre 60 y 70 horas** "
                  "de carga horaria (inclusive). Ordená de **mayor a menor** carga horaria y, a igual carga "
                  "horaria, **alfabéticamente** por nombre.",
        solucion="""SELECT nombre, creditos, carga_horaria
FROM asignaturas
WHERE carga_horaria BETWEEN 60 AND 70
ORDER BY carga_horaria DESC, nombre ASC;""",
        alternativas=[
            dict(titulo="Con >= y <=", sql="""SELECT nombre, creditos, carga_horaria
FROM asignaturas
WHERE carga_horaria >= 60 AND carga_horaria <= 70
ORDER BY carga_horaria DESC, nombre;"""),
        ],
        orden=[("carga_horaria", "desc"), ("nombre", "asc")],
        pistas=[
            "Filtro con `BETWEEN` (incluye los extremos 60 y 70).",
            "`ORDER BY` acepta varias columnas separadas por coma, cada una con su `ASC`/`DESC`.",
            "`ORDER BY carga_horaria DESC, nombre ASC`.",
        ],
        explicacion="""Dos conceptos:

**1. Rango numérico.** `carga_horaria BETWEEN 60 AND 70` incluye 60 y 70 (hay asignaturas con exactamente esas cargas). Con `> 60 AND < 70` se pierden.

**2. Orden con desempate.** En `ORDER BY carga_horaria DESC, nombre ASC`:
- Primero ordena por carga horaria de mayor a menor.
- **Solo cuando dos filas empatan** en carga horaria, usa el nombre (A→Z).

Cada columna lleva su propio sentido: `ORDER BY carga_horaria, nombre DESC` ordenaría la carga ascendente (el `DESC` afecta solo a `nombre`). Y el orden de las columnas importa: `ORDER BY nombre, carga_horaria DESC` ordenaría casi todo por nombre.""",
        errores_comunes=[
            "Usar `> 60 AND < 70`: excluye las asignaturas de exactamente 60 y 70 horas.",
            "Creer que un solo `DESC` al final afecta a todas las columnas: cada columna tiene su propio sentido.",
            "Invertir la prioridad (`ORDER BY nombre, carga_horaria DESC`).",
        ],
        trampas=[
            dict(titulo="Extremos excluidos", sql="""SELECT nombre, creditos, carga_horaria
FROM asignaturas
WHERE carga_horaria > 60 AND carga_horaria < 70
ORDER BY carga_horaria DESC, nombre ASC;"""),
            dict(titulo="DESC solo en la última columna", sql="""SELECT nombre, creditos, carga_horaria
FROM asignaturas
WHERE carga_horaria BETWEEN 60 AND 70
ORDER BY carga_horaria, nombre DESC;"""),
            dict(titulo="Prioridad invertida", sql="""SELECT nombre, creditos, carga_horaria
FROM asignaturas
WHERE carga_horaria BETWEEN 60 AND 70
ORDER BY nombre ASC, carga_horaria DESC;"""),
        ],
        tags=["BETWEEN", "ORDER BY"],
    ),
    dict(
        id="bas-n06",
        origen="Variante",
        titulo="Optativas de los departamentos 1 o 2",
        dificultad=2,
        tipo="select",
        enunciado="Listá id, nombre y créditos de las asignaturas **optativas** (no obligatorias) que pertenezcan "
                  "al departamento **1 o al 2**.",
        solucion="""SELECT id_asignatura, nombre, creditos
FROM asignaturas
WHERE id_departamento IN (1, 2)
  AND es_obligatoria = 0;""",
        alternativas=[
            dict(titulo="OR entre paréntesis", sql="""SELECT id_asignatura, nombre, creditos
FROM asignaturas
WHERE (id_departamento = 1 OR id_departamento = 2)
  AND es_obligatoria = FALSE;"""),
        ],
        columnas=[["id_asignatura", "nombre", "creditos"], ["id_asignatura", "creditos"], ["nombre", "creditos"]],
        pistas=[
            "Hay dos condiciones: el departamento (1 o 2) **y** que sea optativa (`es_obligatoria = 0`).",
            "`AND` se evalúa antes que `OR` (como la multiplicación antes que la suma).",
            "Usá `id_departamento IN (1, 2) AND es_obligatoria = 0`, o poné el `OR` entre paréntesis.",
        ],
        explicacion="""Esta es **la** trampa clásica de precedencia. `AND` tiene más prioridad que `OR`, así que:

```sql
WHERE id_departamento = 1 OR id_departamento = 2 AND es_obligatoria = 0
```

se interpreta como

```sql
WHERE id_departamento = 1 OR (id_departamento = 2 AND es_obligatoria = 0)
```

y trae **todas** las asignaturas del departamento 1 (obligatorias incluidas). Hay que agrupar el `OR` con paréntesis:

```sql
WHERE (id_departamento = 1 OR id_departamento = 2) AND es_obligatoria = 0
```

`IN (1, 2)` evita el problema: es una sola condición que equivale a los `OR` agrupados, y además es más corta y legible.""",
        errores_comunes=[
            "Mezclar `AND` y `OR` sin paréntesis: el `AND` se aplica solo a la condición que tiene al lado.",
            "Escribir `id_departamento = 1 AND id_departamento = 2`: una asignatura no puede tener dos departamentos a la vez, da vacío.",
        ],
        trampas=[
            dict(titulo="AND/OR sin paréntesis", sql="""SELECT id_asignatura, nombre, creditos
FROM asignaturas
WHERE id_departamento = 1 OR id_departamento = 2 AND es_obligatoria = 0;"""),
            dict(titulo="AND en vez de OR entre departamentos", sql="""SELECT id_asignatura, nombre, creditos
FROM asignaturas
WHERE id_departamento = 1 AND id_departamento = 2 AND es_obligatoria = 0;"""),
        ],
        tags=["IN", "AND/OR", "precedencia"],
    ),
    dict(
        id="bas-n07",
        origen="Variante",
        titulo="Carreras fuera de Ingeniería y Salud",
        dificultad=2,
        tipo="select",
        enunciado="Listá nombre, nivel y modalidad de las carreras que **no** pertenezcan ni al departamento 1 "
                  "(Ingeniería) ni al departamento 5 (Salud).",
        solucion="""SELECT nombre, nivel, modalidad
FROM carreras
WHERE id_departamento NOT IN (1, 5);""",
        alternativas=[
            dict(titulo="Con <> y AND", sql="""SELECT nombre, nivel, modalidad
FROM carreras
WHERE id_departamento <> 1
  AND id_departamento <> 5;"""),
            dict(titulo="NOT sobre el IN", sql="""SELECT nombre, nivel, modalidad
FROM carreras
WHERE NOT (id_departamento = 1 OR id_departamento = 5);"""),
        ],
        pistas=[
            "Querés excluir dos valores de `id_departamento`.",
            "`NOT IN (lista)` deja afuera todos los valores de la lista.",
            "Si lo escribís con `<>`, las dos condiciones se unen con `AND`, no con `OR`.",
        ],
        explicacion="""`NOT IN (1, 5)` significa «distinto de 1 **y** distinto de 5».

El error típico es traducirlo literalmente como «no es 1 **o** no es 5»:

```sql
WHERE id_departamento <> 1 OR id_departamento <> 5   -- ¡siempre verdadero!
```

Una carrera del departamento 1 cumple `<> 5`, y una del 5 cumple `<> 1`: pasan **todas**. Es la ley de De Morgan:

`NOT (A OR B)` = `NOT A AND NOT B`

Por eso las formas correctas son `NOT IN (1, 5)`, `<> 1 AND <> 5`, o `NOT (= 1 OR = 5)`.

> Recordá: `NOT IN` con una **lista fija** es seguro. Con una **subconsulta** que devuelva algún `NULL`, el resultado queda vacío (eso se ve en la sección de subconsultas).""",
        errores_comunes=[
            "Usar `<> 1 OR <> 5`: la condición es siempre verdadera y devuelve todas las carreras.",
            "Usar `NOT IN` pero olvidar uno de los valores de la lista.",
        ],
        trampas=[
            dict(titulo="<> con OR (siempre verdadero)", sql="""SELECT nombre, nivel, modalidad
FROM carreras
WHERE id_departamento <> 1 OR id_departamento <> 5;"""),
            dict(titulo="IN en vez de NOT IN", sql="""SELECT nombre, nivel, modalidad
FROM carreras
WHERE id_departamento IN (1, 5);"""),
        ],
        tags=["NOT IN", "De Morgan", "AND/OR"],
    ),
    dict(
        id="bas-n08",
        origen="Variante",
        titulo="Cumpleaños de octubre (MONTH, DAY)",
        dificultad=2,
        tipo="select",
        enunciado="El centro de estudiantes quiere saludar a los cumpleañeros del mes. Mostrá nombre, apellido y "
                  "el **día del mes** en que cumplen años (por ejemplo 14) los alumnos que cumplen en **octubre**, "
                  "ordenados por ese día de menor a mayor.",
        solucion="""SELECT nombre, apellido, DAY(fecha_nacimiento) AS dia
FROM alumnos
WHERE MONTH(fecha_nacimiento) = 10
ORDER BY dia;""",
        alternativas=[
            dict(titulo="Ordenando por la expresión", sql="""SELECT nombre, apellido, DAY(fecha_nacimiento) AS dia
FROM alumnos
WHERE MONTH(fecha_nacimiento) = 10
ORDER BY DAY(fecha_nacimiento) ASC;"""),
        ],
        orden=[("dia", "asc")],
        pistas=[
            "MySQL tiene funciones para extraer partes de una fecha: `YEAR()`, `MONTH()`, `DAY()`.",
            "Octubre es el mes `10`. El día lo calculás en el `SELECT` con `DAY(fecha_nacimiento)`.",
            "Ponele un alias a la columna calculada (`AS dia`) y usalo en el `ORDER BY`.",
        ],
        explicacion="""Las funciones de fecha extraen una parte de un `DATE`:

| función | `'2003-10-14'` |
|---|---|
| `YEAR(f)` | 2003 |
| `MONTH(f)` | 10 |
| `DAY(f)` | 14 |

El filtro es `MONTH(fecha_nacimiento) = 10` (el mes es un **número**, no `'octubre'`).

El orden es importante: si ordenás por `fecha_nacimiento`, MySQL ordena primero por **año** de nacimiento, y un alumno nacido el 2/10/2010 quedaría después de uno del 25/10/1995. Para «por día del mes» hay que ordenar por `DAY(...)`.

Los **alias** del `SELECT` (`dia`) se pueden usar en `ORDER BY`, pero **no** en `WHERE` (el `WHERE` se evalúa antes que el `SELECT`).""",
        errores_comunes=[
            "Comparar con el nombre del mes: `MONTH(fecha_nacimiento) = 'octubre'` no devuelve nada.",
            "Ordenar por `fecha_nacimiento`: ordena por año primero, no por día de cumpleaños.",
            "Confundir `DAY()` con `MONTH()` en el filtro (`DAY(fecha_nacimiento) = 10` son los nacidos un día 10).",
        ],
        trampas=[
            dict(titulo="Ordenar por la fecha completa", sql="""SELECT nombre, apellido, DAY(fecha_nacimiento) AS dia
FROM alumnos
WHERE MONTH(fecha_nacimiento) = 10
ORDER BY fecha_nacimiento;"""),
            dict(titulo="DAY en vez de MONTH en el filtro", sql="""SELECT nombre, apellido, DAY(fecha_nacimiento) AS dia
FROM alumnos
WHERE DAY(fecha_nacimiento) = 10
ORDER BY dia;"""),
            dict(titulo="Mes como texto", sql="""SELECT nombre, apellido, DAY(fecha_nacimiento) AS dia
FROM alumnos
WHERE MONTH(fecha_nacimiento) = 'octubre'
ORDER BY dia;"""),
        ],
        tags=["MONTH", "DAY", "funciones de fecha", "alias", "ORDER BY"],
    ),
    dict(
        id="bas-n09",
        origen="Variante",
        titulo="Salario anual calculado (aritmética y alias)",
        dificultad=2,
        tipo="select",
        enunciado="Mostrá apellido, nombre, salario base y el **salario anual** (12 sueldos) de los docentes cuyo "
                  "salario anual supere los **$4800000**. Llamá `salario_anual` a la columna calculada y ordená de "
                  "mayor a menor salario anual.",
        solucion="""SELECT apellido, nombre, salario_base, salario_base * 12 AS salario_anual
FROM docentes
WHERE salario_base * 12 > 4800000
ORDER BY salario_anual DESC;""",
        alternativas=[
            dict(titulo="Despejando el salario mensual", sql="""SELECT apellido, nombre, salario_base, salario_base * 12 AS salario_anual
FROM docentes
WHERE salario_base > 400000
ORDER BY salario_base DESC;"""),
        ],
        orden=[("salario_anual", "desc")],
        pistas=[
            "En el `SELECT` podés poner expresiones: `salario_base * 12`. Con `AS` le das nombre.",
            "En el `WHERE` no podés usar el alias `salario_anual`: repetí la expresión.",
            "`WHERE salario_base * 12 > 4800000 ORDER BY salario_anual DESC`.",
        ],
        explicacion="""En el `SELECT` se pueden calcular columnas con `+ - * /` y ponerles un nombre con `AS`:

```sql
SELECT salario_base * 12 AS salario_anual
```

El **orden lógico de evaluación** explica dónde se puede usar ese alias:

`FROM` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `ORDER BY`

Cuando se evalúa el `WHERE`, el alias todavía **no existe** → error *Unknown column 'salario_anual' in 'where clause'*. En el `ORDER BY` sí existe, porque se evalúa después del `SELECT`.

Por eso en el `WHERE` se repite la expresión (o se despeja: `salario_base > 400000` es lo mismo). Y el número va sin puntos de miles: `4.800.000` es un error de sintaxis.""",
        errores_comunes=[
            "Usar el alias en el `WHERE`: da error 1054 porque el `WHERE` se evalúa antes que el `SELECT`.",
            "Ordenar ascendente (el `ORDER BY` por defecto es `ASC`).",
            "Escribir el número con puntos de miles.",
        ],
        trampas=[
            dict(titulo="Alias en el WHERE", sql="""SELECT apellido, nombre, salario_base, salario_base * 12 AS salario_anual
FROM docentes
WHERE salario_anual > 4800000
ORDER BY salario_anual DESC;"""),
            dict(titulo="Comparar el sueldo mensual con el monto anual", sql="""SELECT apellido, nombre, salario_base, salario_base * 12 AS salario_anual
FROM docentes
WHERE salario_base > 4800000
ORDER BY salario_anual DESC;"""),
            dict(titulo="Orden ascendente", sql="""SELECT apellido, nombre, salario_base, salario_base * 12 AS salario_anual
FROM docentes
WHERE salario_base * 12 > 4800000
ORDER BY salario_anual;"""),
        ],
        tags=["aritmética", "alias", "ORDER BY", "orden de evaluación"],
    ),
    dict(
        id="bas-n10",
        origen="Variante",
        titulo="Los 5 docentes mejor pagos (LIMIT)",
        dificultad=2,
        tipo="select",
        enunciado="Mostrá nombre, apellido y salario base de los **5 docentes con mayor salario base**, "
                  "de mayor a menor.",
        solucion="""SELECT nombre, apellido, salario_base
FROM docentes
ORDER BY salario_base DESC
LIMIT 5;""",
        orden=[("salario_base", "desc")],
        pistas=[
            "Primero hay que ordenar por salario de mayor a menor.",
            "`LIMIT n` se queda con las primeras `n` filas del resultado **ya ordenado**.",
            "`ORDER BY salario_base DESC LIMIT 5`.",
        ],
        explicacion="""Para un «top N» se combinan dos cláusulas, en este orden:

1. `ORDER BY salario_base DESC`: los más altos quedan arriba.
2. `LIMIT 5`: corta después de la quinta fila.

`LIMIT` sin `ORDER BY` devuelve 5 filas **cualesquiera** (en la práctica, las primeras por id), que no tienen nada que ver con el salario.

`LIMIT` siempre va **al final** de la consulta.

> Ojo con los empates: si el 5.° y el 6.° cobraran lo mismo, `LIMIT 5` dejaría a uno afuera de manera arbitraria. Con estos datos no pasa (el 5.° cobra $416.032,45 y el 6.° $415.393,24).""",
        errores_comunes=[
            "Usar `LIMIT` sin `ORDER BY`: el «top» queda librado al azar.",
            "Ordenar ascendente: obtenés los 5 que MENOS cobran.",
            "Poner `LIMIT` antes del `ORDER BY`: es un error de sintaxis.",
        ],
        trampas=[
            dict(titulo="LIMIT sin ORDER BY", sql="""SELECT nombre, apellido, salario_base
FROM docentes
LIMIT 5;"""),
            dict(titulo="Orden ascendente", sql="""SELECT nombre, apellido, salario_base
FROM docentes
ORDER BY salario_base
LIMIT 5;"""),
            dict(titulo="Sin LIMIT", sql="""SELECT nombre, apellido, salario_base
FROM docentes
ORDER BY salario_base DESC;"""),
        ],
        tags=["LIMIT", "ORDER BY", "top N"],
    ),
]
