"""Sección: DDL — CREATE y ALTER (Clase Semana 10 · Sección 4)."""

# ddl-26: la tabla intermedia la nombra el usuario (y sus columnas también: id_alumno_beca, id_alumno, ...).
# Para probar el comportamiento sin depender de los nombres, se buscan las columnas que son FK a alumnos y a
# becas en information_schema y se arma el INSERT con PREPARE. Además se desactiva el modo estricto para que
# columnas extra NOT NULL sin DEFAULT (p. ej. fecha_otorgamiento) no hagan fallar la prueba.
_INSERT_ALUMNO_BECA = """SET SESSION sql_mode = 'NO_ENGINE_SUBSTITUTION';
SET @c_alu = COALESCE((SELECT MIN(COLUMN_NAME) FROM information_schema.KEY_COLUMN_USAGE
              WHERE TABLE_SCHEMA = '{scratch}' AND TABLE_NAME = '{ab}' AND REFERENCED_TABLE_NAME = 'alumnos'),
              'sin_fk_hacia_alumnos');
SET @c_bec = COALESCE((SELECT MIN(COLUMN_NAME) FROM information_schema.KEY_COLUMN_USAGE
              WHERE TABLE_SCHEMA = '{scratch}' AND TABLE_NAME = '{ab}' AND REFERENCED_TABLE_NAME = 'becas'),
              'sin_fk_hacia_becas');
SET @q = CONCAT('INSERT INTO `{ab}` (`', @c_alu, '`, `', @c_bec, '`) VALUES %s');
PREPARE st FROM @q;
EXECUTE st;
DEALLOCATE PREPARE st;"""

EJERCICIOS = [
    # ------------------------------------------------------------------ 22
    dict(
        id="ddl-22",
        origen="Semana 10 · Ej. 22",
        titulo="Teléfono de emergencia de los alumnos",
        dificultad=1,
        tipo="ddl",
        enunciado="La universidad desea comenzar a registrar **teléfonos de emergencia** de los alumnos. "
                  "Modificar la estructura correspondiente para almacenar esta información.",
        solucion="""ALTER TABLE alumnos
ADD COLUMN telefono_emergencia VARCHAR(50);""",
        checks=[
            dict(tipo="columna_nueva", tabla="alumnos", nombre_contiene=["emerg", "tel", "contacto"],
                 tipos=["varchar", "char"], alias="col",
                 msg_tipo="Los teléfonos se guardan como texto (VARCHAR): pueden tener +, guiones o ceros adelante.",
                 desc="Nueva columna en alumnos para el teléfono de emergencia (tipo texto)"),
            dict(tipo="debe_funcionar",
                 sql="UPDATE alumnos SET {col} = '+54 9 351 555-1234' WHERE id_alumno = 1;",
                 desc="Se puede guardar un teléfono con prefijo internacional (+54 9 351 555-1234)"),
        ],
        pistas=[
            "No hace falta una tabla nueva: alcanza con agregar una columna a `alumnos`.",
            "Sintaxis: `ALTER TABLE tabla ADD COLUMN nombre TIPO;`",
            "Un teléfono no es un número para hacer cuentas: usá `VARCHAR`, igual que la columna `telefono` existente.",
        ],
        explicacion="""`ALTER TABLE ... ADD COLUMN` agrega una columna a una tabla existente. Las filas que ya estaban quedan con `NULL` en la columna nueva (salvo que pongas un `DEFAULT`).

El tipo correcto es `VARCHAR` con un largo razonable (la columna `telefono` usa `VARCHAR(50)`): un teléfono puede empezar con 0, tener `+54`, guiones o espacios, y nunca se suma ni se promedia.

Si se quisieran guardar **varios** contactos de emergencia por alumno, lo correcto sería una tabla aparte `contactos_emergencia (id, id_alumno FK, nombre, telefono)`. Para este enunciado (un teléfono por alumno) alcanza con la columna, y es lo que espera el corrector.""",
        errores_comunes=[
            "Guardar el teléfono como INT: se pierden ceros iniciales, no entran `+` ni guiones y los números largos desbordan.",
            "Usar un VARCHAR demasiado corto (por ejemplo `VARCHAR(8)`): no entra un número con característica.",
            "Escribir `ALTER TABLE alumnos ADD telefono_emergencia;` sin tipo de dato.",
        ],
        trampas=[
            dict(titulo="Como INT", sql="ALTER TABLE alumnos ADD COLUMN telefono_emergencia INT;"),
            dict(titulo="VARCHAR muy corto", sql="ALTER TABLE alumnos ADD COLUMN telefono_emergencia VARCHAR(8);"),
        ],
        tags=["ALTER TABLE", "ADD COLUMN"],
    ),
    # ------------------------------------------------------------------ 23
    dict(
        id="ddl-23",
        origen="Semana 10 · Ej. 23",
        titulo="Tabla de becas académicas",
        dificultad=2,
        tipo="ddl",
        enunciado="La institución incorporará un sistema de **becas académicas**. Crear una estructura que permita "
                  "almacenar:\n\n"
                  "- nombre de la beca,\n"
                  "- porcentaje de descuento,\n"
                  "- fecha de inicio,\n"
                  "- fecha de finalización.\n\n"
                  "(Usá un identificador autoincremental como clave primaria.)",
        solucion="""CREATE TABLE becas (
    id_beca      INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    porcentaje   DECIMAL(5,2) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin    DATE,
    CONSTRAINT chk_becas_porcentaje CHECK (porcentaje BETWEEN 0 AND 100),
    CONSTRAINT chk_becas_fechas CHECK (fecha_fin >= fecha_inicio)
);""",
        checks=[
            dict(tipo="tabla_nueva", nombre_contiene=["beca"], alias="becas", pk=True,
                 columnas=[
                     dict(contiene=["nombre"], tipos=["varchar", "char"], desc="nombre de la beca", alias="nombre"),
                     dict(contiene=["porc", "descuento"],
                          tipos=["decimal", "int", "tinyint", "smallint", "float", "double"],
                          desc="porcentaje de descuento (numérico)", alias="porcentaje"),
                     dict(contiene=["inicio", "desde", "comienzo"], tipos=["date", "datetime"],
                          desc="fecha de inicio (DATE)", alias="inicio"),
                     dict(contiene=["fin", "hasta"], tipos=["date", "datetime"],
                          desc="fecha de finalización (DATE)", alias="fin"),
                 ],
                 desc="Tabla de becas con nombre, porcentaje, fecha de inicio y de fin, y PRIMARY KEY"),
            dict(tipo="debe_funcionar",
                 sql="INSERT INTO {becas} ({becas.nombre}, {becas.porcentaje}, {becas.inicio}, {becas.fin}) "
                     "VALUES ('Beca al Mérito', 50, '2026-03-01', '2026-12-31');",
                 desc="Se puede registrar una beca (50%, de marzo a diciembre de 2026) sin indicar el id"),
            dict(tipo="debe_funcionar", opcional=True,
                 sql="INSERT INTO {becas} ({becas.nombre}, {becas.porcentaje}, {becas.inicio}, {becas.fin}) VALUES "
                     "('Beca Completa', 100, '2026-03-01', '2026-12-31'), ('Beca Simbólica', 0, '2026-03-01', '2026-12-31');",
                 desc="Acepta los límites 0% y 100%"),
            dict(tipo="debe_fallar", opcional=True,
                 sql="INSERT INTO {becas} ({becas.nombre}, {becas.porcentaje}, {becas.inicio}, {becas.fin}) "
                     "VALUES ('Beca Imposible', 101, '2026-03-01', '2026-12-31');",
                 errores=[3819], desc="Sugerencia: CHECK que impida un porcentaje mayor a 100"),
            dict(tipo="debe_fallar", opcional=True,
                 sql="INSERT INTO {becas} ({becas.nombre}, {becas.porcentaje}, {becas.inicio}, {becas.fin}) "
                     "VALUES ('Beca Negativa', -5, '2026-03-01', '2026-12-31');",
                 errores=[3819, 1264], desc="Sugerencia: impedir porcentajes negativos"),
            dict(tipo="debe_fallar", opcional=True,
                 sql="INSERT INTO {becas} ({becas.nombre}, {becas.porcentaje}, {becas.inicio}, {becas.fin}) "
                     "VALUES ('Beca al Revés', 30, '2026-12-31', '2026-03-01');",
                 errores=[3819], desc="Sugerencia: CHECK para que la fecha de fin no sea anterior a la de inicio"),
        ],
        pistas=[
            "Es una tabla nueva: `CREATE TABLE becas ( columna TIPO, ..., PRIMARY KEY (...) );`",
            "Tipos: nombre → `VARCHAR`, porcentaje → `DECIMAL(5,2)` (entra hasta 100.00), fechas → `DATE`. El id: `INT AUTO_INCREMENT PRIMARY KEY`.",
            "Buena práctica (opcional): `CHECK (porcentaje BETWEEN 0 AND 100)` y `CHECK (fecha_fin >= fecha_inicio)`.",
        ],
        explicacion="""Sintaxis general:

```sql
CREATE TABLE nombre (
    columna TIPO [NOT NULL] [DEFAULT valor],
    ...,
    PRIMARY KEY (columna),
    CHECK (condición)
);
```

Decisiones de diseño:
- **Clave primaria** `id_beca INT AUTO_INCREMENT`: identifica cada beca y es lo que después van a referenciar otras tablas (ejercicio 26).
- **Porcentaje**: `DECIMAL(5,2)` guarda hasta `999.99` con 2 decimales exactos (con `DECIMAL(4,2)` no entraría 100). `INT` también sirve si no hacen falta decimales. Nunca `VARCHAR('50%')`: no se podría calcular un descuento.
- **Fechas**: `DATE`, no texto. Así se pueden comparar y ordenar.
- `fecha_fin` admite `NULL` (beca sin fecha de cierre definida).

Los `CHECK` no los pide el enunciado, pero son la forma de que la base rechace datos absurdos (error **3819**): un 150% o una beca que termina antes de empezar.""",
        errores_comunes=[
            "Guardar el porcentaje como texto (`'50%'`) o las fechas como VARCHAR: no se pueden comparar ni calcular.",
            "Olvidar la PRIMARY KEY: después no se puede referenciar la beca desde otra tabla.",
            "Usar `DECIMAL(4,2)` para el porcentaje: el máximo es 99.99, no entra 100.",
        ],
        trampas=[
            dict(titulo="Porcentaje como texto", sql="""CREATE TABLE becas (
    id_beca INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    porcentaje VARCHAR(5),
    fecha_inicio DATE,
    fecha_fin DATE
);"""),
            dict(titulo="Fechas como texto", sql="""CREATE TABLE becas (
    id_beca INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    porcentaje DECIMAL(5,2),
    fecha_inicio VARCHAR(10),
    fecha_fin VARCHAR(10)
);"""),
            dict(titulo="Sin PRIMARY KEY", sql="""CREATE TABLE becas (
    nombre VARCHAR(100),
    porcentaje DECIMAL(5,2),
    fecha_inicio DATE,
    fecha_fin DATE
);"""),
        ],
        tags=["CREATE TABLE", "PRIMARY KEY", "DECIMAL", "DATE", "CHECK"],
    ),
    # ------------------------------------------------------------------ 24
    dict(
        id="ddl-24",
        origen="Semana 10 · Ej. 24",
        titulo="Impedir salarios negativos",
        dificultad=2,
        tipo="ddl",
        enunciado="Modificar la estructura de `docentes` para **impedir salarios negativos**.",
        solucion="""ALTER TABLE docentes
ADD CONSTRAINT chk_salario_no_negativo CHECK (salario_base >= 0);""",
        checks=[
            dict(tipo="check_existe", tabla="docentes", columna="salario_base",
                 desc="Existe una restricción CHECK sobre salario_base"),
            dict(tipo="debe_fallar",
                 sql="INSERT INTO docentes (nombre, apellido, salario_base) VALUES ('Test', 'Negativo', -100);",
                 errores=[3819], desc="Rechaza un docente con salario negativo"),
            dict(tipo="debe_funcionar",
                 sql="INSERT INTO docentes (nombre, apellido, salario_base) VALUES ('Test', 'Cero', 0);",
                 desc="Acepta salario 0 (no negativo)"),
            dict(tipo="debe_fallar",
                 sql="UPDATE docentes SET salario_base = -1 WHERE id_docente = 1;",
                 errores=[3819], desc="Rechaza un UPDATE que deja un salario negativo"),
        ],
        pistas=[
            "La restricción que valida una condición sobre los valores de una columna es `CHECK`.",
            "Se agrega con `ALTER TABLE docentes ADD CONSTRAINT nombre CHECK (condición);`",
            "«No negativo» incluye el cero: `>= 0`.",
        ],
        explicacion="""`CHECK (condición)` hace que MySQL rechace (error **3819**) cualquier `INSERT` o `UPDATE` que deje una fila sin cumplir la condición.

Darle nombre (`CONSTRAINT chk_salario_no_negativo`) es buena práctica: después la podés borrar con `ALTER TABLE docentes DROP CHECK chk_salario_no_negativo;`.

Al agregarla, MySQL verifica las filas existentes: si ya hubiera algún salario negativo, el `ALTER` fallaría.

Ojo: un `CHECK` con `NULL` no falla (la condición da «desconocido», no falso). Si además querés que el salario sea obligatorio, eso es `NOT NULL`.""",
        errores_comunes=[
            "Usar `> 0` cuando se pide «no negativo» (el 0 es válido).",
            "Poner el CHECK sobre otra columna o escribir `CHECK salario_base >= 0` sin paréntesis.",
        ],
        trampas=[
            dict(titulo="Mayor estricto", sql="ALTER TABLE docentes ADD CHECK (salario_base > 0);"),
            dict(titulo="CHECK sobre otra columna", sql="ALTER TABLE docentes ADD CHECK (id_departamento >= 0);"),
        ],
        tags=["ALTER TABLE", "CHECK", "CONSTRAINT"],
    ),
    # ------------------------------------------------------------------ 25
    dict(
        id="ddl-25",
        origen="Semana 10 · Ej. 25",
        titulo="Emails únicos en alumnos",
        dificultad=1,
        tipo="ddl",
        enunciado="Agregar una restricción que impida registrar **emails repetidos** en `alumnos`.\n\n"
                  "> En la base real `alumnos.email` ya es UNIQUE. Para este ejercicio la app le **quitó** esa "
                  "restricción en el espacio temporal, así que tenés que volver a agregarla.",
        preparacion="ALTER TABLE alumnos DROP INDEX email;",
        solucion="""ALTER TABLE alumnos
ADD CONSTRAINT uq_alumnos_email UNIQUE (email);""",
        checks=[
            dict(tipo="unique", tabla="alumnos", columna="email",
                 desc="Existe una restricción UNIQUE sobre alumnos.email (sola)"),
            dict(tipo="debe_fallar",
                 sql="INSERT INTO alumnos (nombre, apellido, dni, email) "
                     "VALUES ('Test', 'Duplicado', '99999999', 'alumno1@mail.com');",
                 errores=[1062], desc="Rechaza un alumno nuevo con un email que ya existe"),
            dict(tipo="debe_funcionar",
                 sql="INSERT INTO alumnos (nombre, apellido, dni, email) "
                     "VALUES ('Test', 'Nuevo', '99999998', 'test.nuevo@mail.com');",
                 desc="Acepta un alumno con email nuevo"),
        ],
        pistas=[
            "La restricción que impide valores repetidos en una columna es `UNIQUE`.",
            "`ALTER TABLE alumnos ADD CONSTRAINT nombre UNIQUE (columna);`",
            "Tiene que ser UNIQUE sobre `email` **solo**: un UNIQUE compuesto `(email, dni)` permitiría el mismo email con otro DNI.",
        ],
        explicacion="""`UNIQUE` garantiza que no haya dos filas con el mismo valor en esa columna; si se intenta, MySQL responde **1062 (Duplicate entry)**.

```sql
ALTER TABLE alumnos ADD CONSTRAINT uq_alumnos_email UNIQUE (email);
-- equivalente: ALTER TABLE alumnos ADD UNIQUE (email);
--              CREATE UNIQUE INDEX uq_alumnos_email ON alumnos (email);
```

Detalles:
- `UNIQUE` crea un **índice** por debajo, así que además acelera las búsquedas por email.
- Admite varios `NULL` (NULL no es igual a NULL). Si el email fuera obligatorio, sumá `NOT NULL`.
- Si ya hubiera emails repetidos en la tabla, el `ALTER` fallaría con 1062 y habría que limpiarlos antes.
- Un UNIQUE **compuesto** `(email, dni)` solo impide repetir el **par**: el mismo email con otro DNI pasaría.""",
        errores_comunes=[
            "Crear un índice común (`ADD INDEX (email)`): acelera búsquedas pero no impide repetidos.",
            "Hacer un UNIQUE compuesto `(email, dni)`: impide repetir la combinación, no el email.",
            "Confundir UNIQUE con PRIMARY KEY: la tabla ya tiene PK (`id_alumno`) y solo puede haber una.",
        ],
        trampas=[
            dict(titulo="Índice común", sql="ALTER TABLE alumnos ADD INDEX idx_email (email);"),
            dict(titulo="UNIQUE compuesto", sql="ALTER TABLE alumnos ADD UNIQUE (email, dni);"),
        ],
        tags=["ALTER TABLE", "UNIQUE", "CONSTRAINT"],
    ),
    # ------------------------------------------------------------------ 26
    dict(
        id="ddl-26",
        origen="Semana 10 · Ej. 26",
        titulo="Asociar alumnos con becas",
        dificultad=3,
        tipo="ddl",
        enunciado="Crear una estructura que permita **asociar alumnos con becas**.\n\n"
                  "> Para este ejercicio, en el espacio temporal ya existe la tabla `becas` (la del ejercicio 23): "
                  "`becas(id_beca INT AUTO_INCREMENT PK, nombre, porcentaje, fecha_inicio, fecha_fin)`, "
                  "con las becas 1 y 2 cargadas.",
        preparacion="""CREATE TABLE becas (
    id_beca INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    porcentaje DECIMAL(5,2) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE
);
INSERT INTO becas (id_beca, nombre, porcentaje, fecha_inicio, fecha_fin) VALUES
    (1, 'Beca al Mérito Académico', 50.00, '2026-03-01', '2026-12-31'),
    (2, 'Beca Deportiva', 25.00, '2026-03-01', NULL);""",
        solucion="""CREATE TABLE alumno_beca (
    id_alumno          INT NOT NULL,
    id_beca            INT NOT NULL,
    fecha_otorgamiento DATE,
    PRIMARY KEY (id_alumno, id_beca),
    FOREIGN KEY (id_alumno) REFERENCES alumnos (id_alumno),
    FOREIGN KEY (id_beca) REFERENCES becas (id_beca)
);""",
        alternativas=[
            dict(titulo="Con id propio + UNIQUE", sql="""CREATE TABLE alumno_beca (
    id_alumno_beca INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno      INT NOT NULL,
    id_beca        INT NOT NULL,
    fecha_otorgamiento DATE NOT NULL,
    UNIQUE (id_alumno, id_beca),
    CONSTRAINT fk_ab_alumno FOREIGN KEY (id_alumno) REFERENCES alumnos (id_alumno),
    CONSTRAINT fk_ab_beca FOREIGN KEY (id_beca) REFERENCES becas (id_beca)
);"""),
        ],
        checks=[
            dict(tipo="tabla_nueva", nombre_contiene=["beca", "alumno"], alias="ab", pk=True,
                 desc="Tabla nueva para asociar alumnos y becas, con PRIMARY KEY"),
            dict(tipo="fk", tabla="{ab}", referencia="alumnos", desc="FOREIGN KEY hacia alumnos"),
            dict(tipo="fk", tabla="{ab}", referencia="becas", desc="FOREIGN KEY hacia becas"),
            dict(tipo="debe_funcionar", sql=_INSERT_ALUMNO_BECA % "(1, 1), (1, 2), (2, 1)",
                 desc="Un alumno puede tener varias becas y una beca varios alumnos (relación N a N)"),
            dict(tipo="debe_fallar", sql=_INSERT_ALUMNO_BECA % "(999999, 1)",
                 errores=[1452], desc="Rechaza asociar un alumno inexistente"),
            dict(tipo="debe_fallar", sql=_INSERT_ALUMNO_BECA % "(1, 999)",
                 errores=[1452], desc="Rechaza asociar una beca inexistente"),
            dict(tipo="debe_fallar", opcional=True, sql=_INSERT_ALUMNO_BECA % "(1, 1), (1, 1)",
                 errores=[1062], desc="Sugerencia: PK compuesta (o UNIQUE) para no repetir la misma beca al mismo alumno"),
        ],
        pistas=[
            "Un alumno puede tener varias becas y una beca la pueden tener muchos alumnos: es una relación **N a N**.",
            "Las relaciones N a N se resuelven con una **tabla intermedia** con dos FOREIGN KEY: una a `alumnos` y otra a `becas`.",
            "`CREATE TABLE alumno_beca (id_alumno INT, id_beca INT, PRIMARY KEY (id_alumno, id_beca), FOREIGN KEY (id_alumno) REFERENCES alumnos(id_alumno), FOREIGN KEY (id_beca) REFERENCES becas(id_beca));`",
        ],
        explicacion="""Un alumno puede recibir varias becas (a lo largo del tiempo) y una beca la reciben muchos alumnos: relación **N a N**. En el modelo relacional se resuelve con una **tabla intermedia**, igual que `alumno_carrera` o `inscripcion_alumno_comision`:

```sql
CREATE TABLE alumno_beca (
    id_alumno INT NOT NULL,
    id_beca   INT NOT NULL,
    PRIMARY KEY (id_alumno, id_beca),
    FOREIGN KEY (id_alumno) REFERENCES alumnos (id_alumno),
    FOREIGN KEY (id_beca)   REFERENCES becas (id_beca)
);
```

- Las **FOREIGN KEY** garantizan que no se asocie un alumno o una beca inexistente (error **1452**). La columna tiene que ser del mismo tipo que la referenciada (`INT`).
- La **PK compuesta** `(id_alumno, id_beca)` impide repetir la misma asociación (error **1062**). Otra opción válida: un id propio + `UNIQUE (id_alumno, id_beca)`.
- Podés agregar datos de la relación (fecha de otorgamiento).

Agregar `id_beca` a `alumnos` solo permitiría **una** beca por alumno.""",
        errores_comunes=[
            "Agregar `id_beca` como columna de `alumnos`: cada alumno podría tener una sola beca (relación 1 a N, no N a N).",
            "Crear la tabla sin FOREIGN KEY: se podrían cargar alumnos o becas que no existen.",
            "Poner la PRIMARY KEY solo en `id_alumno`: un alumno no podría tener dos becas.",
        ],
        trampas=[
            dict(titulo="Columna en alumnos (1 a N)", sql="""ALTER TABLE alumnos
ADD COLUMN id_beca INT,
ADD FOREIGN KEY (id_beca) REFERENCES becas (id_beca);"""),
            dict(titulo="Sin claves foráneas", sql="""CREATE TABLE alumno_beca (
    id_alumno INT NOT NULL,
    id_beca INT NOT NULL,
    PRIMARY KEY (id_alumno, id_beca)
);"""),
            dict(titulo="PK solo en el alumno", sql="""CREATE TABLE alumno_beca (
    id_alumno INT NOT NULL PRIMARY KEY,
    id_beca INT NOT NULL,
    FOREIGN KEY (id_alumno) REFERENCES alumnos (id_alumno),
    FOREIGN KEY (id_beca) REFERENCES becas (id_beca)
);"""),
        ],
        tags=["CREATE TABLE", "FOREIGN KEY", "N a N", "PRIMARY KEY compuesta"],
    ),
    # ================================================================== Variantes
    dict(
        id="ddl-n01",
        origen="Variante",
        titulo="Ampliar el nombre de las aulas (MODIFY)",
        dificultad=1,
        tipo="ddl",
        enunciado="Los nombres de las aulas ya no entran en `VARCHAR(50)`. Modificá la columna `aulas.nombre` para que "
                  "sea **VARCHAR(100)** y además **obligatoria** (NOT NULL), sin cambiarle el nombre.",
        solucion="""ALTER TABLE aulas
MODIFY nombre VARCHAR(100) NOT NULL;""",
        alternativas=[
            dict(titulo="Con CHANGE (repitiendo el nombre)", sql="ALTER TABLE aulas CHANGE nombre nombre VARCHAR(100) NOT NULL;"),
        ],
        checks=[
            dict(tipo="columna_tipo", tabla="aulas", columna="nombre", tipos=["varchar"], largo_min=100, nulo=False,
                 desc="aulas.nombre es VARCHAR(100) (o más) y NOT NULL"),
            dict(tipo="debe_funcionar",
                 sql="INSERT INTO aulas (nombre, capacidad, tipo) VALUES (REPEAT('x', 100), 30, 'normal');",
                 desc="Acepta un nombre de 100 caracteres"),
            dict(tipo="debe_fallar",
                 sql="INSERT INTO aulas (nombre, capacidad, tipo) VALUES (NULL, 30, 'normal');",
                 errores=[1048], desc="Rechaza un aula sin nombre"),
        ],
        pistas=[
            "Para cambiar el tipo de una columna existente se usa `ALTER TABLE ... MODIFY`.",
            "`MODIFY` redefine la columna **completa**: tipo y también `NOT NULL`, `DEFAULT`, etc.",
            "`ALTER TABLE aulas MODIFY nombre VARCHAR(100) NOT NULL;`",
        ],
        explicacion="""Para cambiar la definición de una columna existente:

```sql
ALTER TABLE tabla MODIFY columna NUEVO_TIPO [NOT NULL] [DEFAULT ...];
ALTER TABLE tabla CHANGE columna nombre_nuevo NUEVO_TIPO ...;  -- además renombra
ALTER TABLE tabla RENAME COLUMN viejo TO nuevo;              -- solo renombra
```

Clave: `MODIFY` **reemplaza la definición entera**. Si escribís `MODIFY nombre VARCHAR(100)` sin `NOT NULL`, la columna queda (o sigue) admitiendo NULL. Lo mismo con un `DEFAULT` que tuviera: si no lo repetís, se pierde.

Al ampliar un `VARCHAR` los datos se conservan. Al **achicarlo** o pasar a `NOT NULL`, MySQL verifica las filas existentes: si algún valor no entra o es `NULL`, el `ALTER` falla.

`ADD COLUMN nombre ...` no sirve: la columna ya existe (error **1060**).""",
        errores_comunes=[
            "Olvidar repetir `NOT NULL` en el MODIFY: MODIFY redefine la columna completa.",
            "Usar `CHANGE` con otro nombre: la columna queda renombrada y las consultas que usan `nombre` dejan de andar.",
            "Usar `ADD COLUMN` para una columna que ya existe → error 1060.",
        ],
        trampas=[
            dict(titulo="Sin NOT NULL", sql="ALTER TABLE aulas MODIFY nombre VARCHAR(100);"),
            dict(titulo="CHANGE renombrando", sql="ALTER TABLE aulas CHANGE nombre nombre_aula VARCHAR(100) NOT NULL;"),
            dict(titulo="ADD COLUMN de una columna existente", sql="ALTER TABLE aulas ADD COLUMN nombre VARCHAR(100) NOT NULL;"),
        ],
        tags=["ALTER TABLE", "MODIFY", "NOT NULL"],
    ),
    dict(
        id="ddl-n02",
        origen="Variante",
        titulo="Docentes activos por defecto",
        dificultad=1,
        tipo="ddl",
        enunciado="Agregá a `docentes` una columna que indique si el docente está **activo (1)** o **inactivo (0)**. "
                  "Todos los docentes que ya existen, y los que se registren de ahora en más sin indicar ese dato, "
                  "tienen que quedar **activos**.",
        solucion="""ALTER TABLE docentes
ADD COLUMN activo TINYINT(1) NOT NULL DEFAULT 1;""",
        checks=[
            dict(tipo="columna_nueva", tabla="docentes", nombre_contiene=["activ", "habil", "vigen", "estado"],
                 tipos=["tinyint", "bit", "smallint", "int"], alias="act",
                 msg_tipo="Para un sí/no se usa TINYINT(1) (BOOLEAN es un alias de TINYINT(1)).",
                 desc="Nueva columna en docentes para indicar si está activo (tipo numérico / booleano)"),
            dict(tipo="consulta", sql="SELECT COUNT(*) > 0 AND SUM({act} = 1) = COUNT(*) FROM docentes",
                 desc="Los docentes que ya existían quedaron activos (= 1)",
                 fallo_msg="Los docentes existentes no quedaron en 1: al agregar la columna faltó el DEFAULT 1."),
            dict(tipo="consulta",
                 sql="SELECT COLUMN_DEFAULT IN ('1', \"b'1'\") FROM information_schema.COLUMNS "
                     "WHERE TABLE_SCHEMA = '{scratch}' AND TABLE_NAME = 'docentes' AND COLUMN_NAME = '{act}'",
                 desc="Los docentes nuevos quedan activos por defecto (DEFAULT 1)",
                 fallo_msg="La columna no tiene DEFAULT 1."),
            dict(tipo="debe_fallar", opcional=True, sql="UPDATE docentes SET {act} = NULL WHERE id_docente = 1;",
                 errores=[1048], desc="Sugerencia: NOT NULL (que no pueda quedar sin valor)"),
        ],
        pistas=[
            "Es un `ALTER TABLE docentes ADD COLUMN ...`.",
            "Para un sí/no se usa `TINYINT(1)` (o `BOOLEAN`, que es lo mismo).",
            "`DEFAULT 1` hace que las filas existentes y las nuevas tomen ese valor si no se indica otro.",
        ],
        explicacion="""```sql
ALTER TABLE docentes ADD COLUMN activo TINYINT(1) NOT NULL DEFAULT 1;
```

- `TINYINT(1)` es el tipo habitual para valores sí/no en MySQL (`BOOLEAN` es un alias; `es_obligatoria` de `asignaturas` usa el mismo tipo).
- `DEFAULT 1` cumple **las dos** partes del pedido: al agregar la columna, MySQL completa las 200 filas existentes con el valor por defecto, y en los `INSERT` futuros que no mencionen `activo` también se usa 1.
- Sin `DEFAULT`, las filas existentes quedarían en `NULL` (o en 0 si la columna es `NOT NULL`).
- `NOT NULL` es recomendable: un docente tiene que estar activo o no, no «desconocido».

Diferencia clave: `DEFAULT` actúa cuando **no se indica** el valor; no impide que alguien cargue 0 a propósito.""",
        errores_comunes=[
            "Olvidar el DEFAULT: los docentes existentes quedan en NULL.",
            "Poner `DEFAULT 0`: quedan todos inactivos.",
            "Usar `VARCHAR` con 'si'/'no': ocupa más y permite cualquier texto.",
        ],
        trampas=[
            dict(titulo="Sin DEFAULT", sql="ALTER TABLE docentes ADD COLUMN activo TINYINT(1);"),
            dict(titulo="DEFAULT 0", sql="ALTER TABLE docentes ADD COLUMN activo BOOLEAN NOT NULL DEFAULT 0;"),
            dict(titulo="Como texto", sql="ALTER TABLE docentes ADD COLUMN activo VARCHAR(2) DEFAULT 'si';"),
        ],
        tags=["ALTER TABLE", "ADD COLUMN", "DEFAULT"],
    ),
    dict(
        id="ddl-n03",
        origen="Variante",
        titulo="Agregar una FOREIGN KEY que falta",
        dificultad=2,
        tipo="ddl",
        enunciado="En esta práctica la tabla `examenes` **perdió** su clave foránea hacia `comisiones` (la app la "
                  "borró en el espacio temporal): hoy se podría cargar un examen de una comisión que no existe. "
                  "Agregá la restricción que lo impida.",
        preparacion="ALTER TABLE examenes DROP FOREIGN KEY examenes_ibfk_1;",
        solucion="""ALTER TABLE examenes
ADD CONSTRAINT fk_examenes_comision
    FOREIGN KEY (id_comision) REFERENCES comisiones (id_comision);""",
        checks=[
            dict(tipo="fk", tabla="examenes", referencia="comisiones",
                 desc="examenes tiene una FOREIGN KEY hacia comisiones"),
            dict(tipo="debe_fallar",
                 sql="INSERT INTO examenes (id_comision, fecha, tipo) VALUES (999999, '2026-06-01', 'parcial');",
                 errores=[1452], desc="Rechaza un examen de una comisión inexistente"),
            dict(tipo="debe_funcionar",
                 sql="INSERT INTO examenes (id_comision, fecha, tipo) VALUES (1, '2026-06-01', 'parcial');",
                 desc="Acepta un examen de una comisión existente"),
        ],
        pistas=[
            "La restricción que exige que un valor exista en otra tabla es `FOREIGN KEY`.",
            "Sintaxis: `ALTER TABLE hija ADD CONSTRAINT nombre FOREIGN KEY (columna) REFERENCES padre (columna);`",
            "La columna de `examenes` que apunta a la comisión es `id_comision`, y referencia a `comisiones(id_comision)`.",
        ],
        explicacion="""Una **FOREIGN KEY** obliga a que cada valor de la columna exista en la tabla referenciada:

```sql
ALTER TABLE examenes
ADD CONSTRAINT fk_examenes_comision
    FOREIGN KEY (id_comision) REFERENCES comisiones (id_comision);
```

Efectos:
- `INSERT`/`UPDATE` en `examenes` con una comisión inexistente → error **1452**.
- `DELETE` de una comisión que tiene exámenes → error **1451** (salvo que definas `ON DELETE CASCADE`, que borraría los exámenes en cascada).

Requisitos: las dos columnas tienen que ser del **mismo tipo** (`INT`) y la referenciada tiene que ser PK o tener índice. Si la tabla ya tuviera exámenes de comisiones inexistentes, el `ALTER` fallaría hasta limpiarlos (acá, en el espacio temporal, `examenes` está vacía).

Ojo con la dirección: la FK se define en la tabla **hija** (`examenes`) y apunta a la **padre** (`comisiones`).""",
        errores_comunes=[
            "Referenciar la tabla equivocada (por ejemplo `asignaturas`): la restricción existe pero valida otra cosa.",
            "Crear solo un índice (`ADD INDEX (id_comision)`): acelera pero no valida nada.",
            "Definir la FK sobre la columna equivocada (`id_examen`).",
        ],
        trampas=[
            dict(titulo="Referencia a la tabla equivocada", sql="""ALTER TABLE examenes
ADD FOREIGN KEY (id_comision) REFERENCES asignaturas (id_asignatura);"""),
            dict(titulo="Solo un índice", sql="ALTER TABLE examenes ADD INDEX idx_comision (id_comision);"),
            dict(titulo="FK sobre la columna equivocada", sql="""ALTER TABLE examenes
ADD FOREIGN KEY (id_examen) REFERENCES comisiones (id_comision);"""),
        ],
        tags=["ALTER TABLE", "FOREIGN KEY", "CONSTRAINT"],
    ),
    dict(
        id="ddl-n04",
        origen="Variante",
        titulo="Tabla de cuotas con FK, ENUM y DEFAULT",
        dificultad=3,
        tipo="ddl",
        enunciado="Crear la tabla **`cuotas`** para registrar las cuotas que deben pagar los alumnos, con:\n\n"
                  "- un identificador **autoincremental** (clave primaria),\n"
                  "- el **alumno** (tiene que existir en `alumnos`),\n"
                  "- el **monto**, con 2 decimales, obligatorio,\n"
                  "- la **fecha de vencimiento**, obligatoria,\n"
                  "- el **estado**, que solo puede ser `'pendiente'`, `'pagada'` o `'vencida'`, y por defecto `'pendiente'`.",
        solucion="""CREATE TABLE cuotas (
    id_cuota          INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno         INT NOT NULL,
    monto             DECIMAL(10,2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    estado            ENUM('pendiente', 'pagada', 'vencida') NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (id_alumno) REFERENCES alumnos (id_alumno)
);""",
        checks=[
            dict(tipo="tabla_nueva", nombre_contiene=["cuota", "pago"], alias="c", pk=True,
                 columnas=[
                     dict(contiene=["alumno"], tipos=["int"], desc="alumno (INT)", alias="alumno"),
                     dict(contiene=["monto", "importe", "valor"], tipos=["decimal"],
                          desc="monto (DECIMAL)", alias="monto"),
                     dict(contiene=["venc", "fecha"], tipos=["date", "datetime"],
                          desc="fecha de vencimiento (DATE)", alias="venc"),
                     dict(contiene=["estado"], tipos=["enum"], desc="estado (ENUM)", alias="estado"),
                 ],
                 desc="Tabla cuotas con alumno, monto DECIMAL, vencimiento DATE, estado ENUM y PRIMARY KEY"),
            dict(tipo="fk", tabla="{c}", referencia="alumnos", desc="El alumno es FOREIGN KEY a alumnos"),
            dict(tipo="debe_funcionar",
                 sql="INSERT INTO {c} ({c.alumno}, {c.monto}, {c.venc}) VALUES (1, 45000.50, '2026-11-10');",
                 desc="Se puede registrar una cuota indicando solo alumno, monto y vencimiento"),
            dict(tipo="consulta",
                 sql="SELECT COLUMN_DEFAULT = 'pendiente' FROM information_schema.COLUMNS "
                     "WHERE TABLE_SCHEMA = '{scratch}' AND TABLE_NAME = '{c}' AND COLUMN_NAME = '{c.estado}'",
                 desc="El estado por defecto es 'pendiente'", fallo_msg="Falta `DEFAULT 'pendiente'` en el estado."),
            dict(tipo="consulta",
                 sql="SELECT NUMERIC_SCALE = 2 FROM information_schema.COLUMNS "
                     "WHERE TABLE_SCHEMA = '{scratch}' AND TABLE_NAME = '{c}' AND COLUMN_NAME = '{c.monto}'",
                 desc="El monto tiene 2 decimales", fallo_msg="El monto tiene que ser DECIMAL(x,2)."),
            dict(tipo="debe_funcionar",
                 sql="INSERT INTO {c} ({c.alumno}, {c.monto}, {c.venc}, {c.estado}) VALUES "
                     "(1, 45000, '2026-11-10', 'pagada'), (2, 45000, '2026-11-10', 'vencida');",
                 desc="Acepta los estados 'pagada' y 'vencida'"),
            dict(tipo="debe_fallar",
                 sql="INSERT INTO {c} ({c.alumno}, {c.monto}, {c.venc}, {c.estado}) VALUES (1, 45000, '2026-11-10', 'cancelada');",
                 errores=[1265], desc="Rechaza un estado que no está en la lista"),
            dict(tipo="debe_fallar",
                 sql="INSERT INTO {c} ({c.alumno}, {c.monto}, {c.venc}) VALUES (999999, 45000, '2026-11-10');",
                 errores=[1452], desc="Rechaza una cuota de un alumno inexistente"),
            dict(tipo="debe_fallar",
                 sql="INSERT INTO {c} ({c.alumno}, {c.monto}, {c.venc}) VALUES (1, NULL, '2026-11-10');",
                 errores=[1048], desc="El monto es obligatorio (NOT NULL)"),
            dict(tipo="debe_fallar",
                 sql="INSERT INTO {c} ({c.alumno}, {c.monto}, {c.venc}) VALUES (1, 45000, NULL);",
                 errores=[1048], desc="La fecha de vencimiento es obligatoria (NOT NULL)"),
        ],
        pistas=[
            "Estructura: `CREATE TABLE cuotas ( ..., PRIMARY KEY ..., FOREIGN KEY (id_alumno) REFERENCES alumnos (id_alumno) );`",
            "Tipos: monto → `DECIMAL(10,2)`, vencimiento → `DATE`, estado → `ENUM('pendiente','pagada','vencida')`.",
            "El valor por defecto se escribe en la definición de la columna: `estado ENUM(...) NOT NULL DEFAULT 'pendiente'`.",
        ],
        explicacion="""Este ejercicio junta casi todo lo de DDL:

```sql
CREATE TABLE cuotas (
    id_cuota INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    estado ENUM('pendiente','pagada','vencida') NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (id_alumno) REFERENCES alumnos (id_alumno)
);
```

- **Dinero → `DECIMAL`**, nunca `FLOAT`: `FLOAT` es aproximado y `0.1 + 0.2` no da exacto. `DECIMAL(10,2)` = hasta 10 dígitos, 2 decimales.
- **`ENUM`** restringe los valores posibles: otro valor da **1265**. Un `VARCHAR` aceptaría cualquier texto.
- **`DEFAULT 'pendiente'`**: si el `INSERT` no menciona el estado, se usa ese.
- **`NOT NULL`** en monto y vencimiento: «obligatorio» (si no, error **1048**).
- **FOREIGN KEY**: la cuota tiene que ser de un alumno existente (**1452**). El tipo de `id_alumno` tiene que coincidir con `alumnos.id_alumno` (`INT`).""",
        errores_comunes=[
            "Guardar el monto como FLOAT: los montos de dinero se guardan con DECIMAL (exacto).",
            "Usar VARCHAR para el estado: acepta cualquier texto, no solo los tres permitidos.",
            "Olvidar el DEFAULT o escribirlo con un valor que no está en el ENUM.",
        ],
        trampas=[
            dict(titulo="Monto FLOAT", sql="""CREATE TABLE cuotas (
    id_cuota INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno INT NOT NULL,
    monto FLOAT NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    estado ENUM('pendiente', 'pagada', 'vencida') NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (id_alumno) REFERENCES alumnos (id_alumno)
);"""),
            dict(titulo="Estado VARCHAR", sql="""CREATE TABLE cuotas (
    id_cuota INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (id_alumno) REFERENCES alumnos (id_alumno)
);"""),
            dict(titulo="Sin PRIMARY KEY", sql="""CREATE TABLE cuotas (
    id_alumno INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    estado ENUM('pendiente', 'pagada', 'vencida') NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (id_alumno) REFERENCES alumnos (id_alumno)
);"""),
        ],
        tags=["CREATE TABLE", "FOREIGN KEY", "ENUM", "DEFAULT", "DECIMAL"],
    ),
]
