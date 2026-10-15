"""Explicaciones en castellano de los errores típicos de MySQL."""
import difflib
import re

EXPLICACIONES = {
    1064: ("Error de sintaxis",
           "MySQL no entiende la sentencia a partir del fragmento que muestra después de «near». "
           "Causas típicas: una coma de más antes del FROM, falta una coma entre columnas, "
           "un string sin comillas simples, paréntesis sin cerrar, o una palabra reservada mal escrita."),
    1054: ("Columna inexistente",
           "Estás usando una columna que no existe en las tablas del FROM (o un alias definido en el SELECT "
           "dentro del WHERE, cosa que no se puede: el WHERE se evalúa antes que el SELECT)."),
    1146: ("Tabla inexistente", "La tabla que nombraste no existe. Revisá el nombre (todas van en minúscula y en plural)."),
    1052: ("Columna ambigua",
           "Esa columna existe en más de una de las tablas que uniste. Prefijala con la tabla o su alias, "
           "por ejemplo a.nombre o d.id_departamento."),
    1055: ("Falta columna en el GROUP BY (ONLY_FULL_GROUP_BY)",
           "Toda columna del SELECT que no esté dentro de una función de agregación (COUNT, SUM, AVG, MIN, MAX) "
           "tiene que aparecer en el GROUP BY."),
    1111: ("Uso inválido de función de agregación",
           "Usaste COUNT/SUM/AVG/... dentro del WHERE. El WHERE filtra filas ANTES de agrupar: "
           "para filtrar por un resultado agregado usá HAVING."),
    1140: ("Mezcla de agregados sin GROUP BY",
           "Pusiste columnas comunes junto con funciones de agregación pero sin GROUP BY. Agregá GROUP BY con esas columnas."),
    1242: ("La subconsulta devuelve más de una fila",
           "Comparaste con = (o <, >) contra una subconsulta que devuelve varias filas. Usá IN, o asegurate de que devuelva un único valor."),
    1241: ("La subconsulta devuelve más de una columna",
           "Una subconsulta usada con IN o = tiene que devolver una sola columna."),
    1248: ("La tabla derivada necesita alias",
           "Toda subconsulta en el FROM necesita un alias: FROM (SELECT ...) AS t"),
    1222: ("UNION con distinta cantidad de columnas", "Los SELECT unidos con UNION deben tener la misma cantidad de columnas."),
    1093: ("No se puede usar la misma tabla en la subconsulta (error 1093)",
           "MySQL no permite modificar (UPDATE/DELETE) una tabla y a la vez leerla en una subconsulta del WHERE. "
           "Truco: envolvé la subconsulta en otra: WHERE id IN (SELECT id FROM (SELECT ... ) AS t)."),
    1175: ("Safe Updates activado (Workbench)",
           "Con el modo seguro, UPDATE/DELETE exigen un WHERE sobre una columna con índice (PK/FK). "
           "En Workbench podés ejecutar SET SQL_SAFE_UPDATES = 0; antes de la sentencia."),
    1451: ("Restricción de clave foránea (hay filas hijas)",
           "No se puede borrar/actualizar esa fila porque otras tablas la referencian con una FOREIGN KEY. "
           "Primero borrá (o reasigná) las filas hijas y después la fila padre."),
    1452: ("Clave foránea inválida",
           "Estás insertando/actualizando un valor de FK que no existe en la tabla referenciada "
           "(por ejemplo un id_docente que no está en docentes)."),
    1062: ("Valor duplicado", "Violaste una restricción PRIMARY KEY o UNIQUE: ese valor ya existe."),
    1048: ("Columna NOT NULL", "Esa columna no admite NULL y no le diste un valor."),
    1364: ("Falta un valor obligatorio", "Esa columna es NOT NULL y no tiene DEFAULT: tenés que incluirla en el INSERT."),
    1136: ("Cantidad de valores incorrecta",
           "La cantidad de valores del VALUES no coincide con la cantidad de columnas. "
           "Tip: listá siempre las columnas: INSERT INTO t (c1, c2) VALUES (...)."),
    1265: ("Valor no permitido / truncado",
           "El valor no entra en la columna. Si es un ENUM, solo acepta los valores definidos (respetá mayúsculas/acentos)."),
    1366: ("Valor de tipo incorrecto", "El valor no corresponde al tipo de la columna (por ejemplo texto en un INT)."),
    1292: ("Fecha o valor incorrecto", "Formato de fecha inválido. En MySQL las fechas van como 'AAAA-MM-DD'."),
    1406: ("Dato demasiado largo", "El texto supera el largo máximo de la columna (VARCHAR(n))."),
    3819: ("Violación de CHECK", "El valor no cumple una restricción CHECK de la tabla."),
    1050: ("La tabla/vista ya existe", "Ya existe un objeto con ese nombre. Usá otro nombre, DROP ... IF EXISTS antes, o CREATE OR REPLACE VIEW para vistas."),
    1060: ("Nombre de columna duplicado",
           "Hay dos columnas con el mismo nombre. En una VISTA pasa mucho al unir tablas con columnas homónimas "
           "(nombre, id...): poneles alias distintos, ej. c.nombre AS carrera."),
    1061: ("Nombre de índice duplicado", "Ya existe un índice/constraint con ese nombre en la tabla."),
    1068: ("Más de una PRIMARY KEY", "Una tabla solo puede tener una PRIMARY KEY (puede ser compuesta: PRIMARY KEY (a, b))."),
    1075: ("AUTO_INCREMENT sin clave", "Una columna AUTO_INCREMENT tiene que ser PRIMARY KEY (o tener un índice)."),
    1091: ("No existe para borrar", "La columna, índice o constraint que querés eliminar no existe."),
    1215: ("No se pudo crear la FK", "Revisá que la columna referenciada sea PK/UNIQUE y que los tipos coincidan exactamente (INT con INT)."),
    1822: ("No se pudo crear la FK (falta índice)", "La columna referenciada debe ser PRIMARY KEY o tener un índice."),
    3780: ("FK con tipos incompatibles", "La columna FK y la referenciada deben tener exactamente el mismo tipo (ej. INT y INT)."),
    1824: ("Tabla referenciada inexistente", "La FOREIGN KEY apunta a una tabla que no existe (¿creaste antes la tabla padre?)."),
    3813: ("CHECK mal definido", "La expresión del CHECK no es válida o referencia otra columna con AUTO_INCREMENT."),
    3024: ("Consulta demasiado lenta", "La consulta tardó más de lo permitido. ¿Te olvidaste una condición de JOIN (producto cartesiano)?"),
    1205: ("Tiempo de espera agotado", "La sentencia esperó demasiado por un bloqueo. Probá de nuevo."),
    1142: ("Sin permiso", "La app solo puede tocar la base de práctica. No uses prefijos de base (ej. universidad.alumnos), usá solo el nombre de la tabla."),
    1044: ("Sin permiso", "La app solo puede tocar la base de práctica."),
    1049: ("Base inexistente", "No uses nombres de base: trabajá con las tablas directamente."),
    1347: ("No es una vista/tabla del tipo esperado", "El objeto existe pero no es del tipo que indicaste (¿DROP VIEW sobre una tabla?)."),
    1356: ("Vista inválida", "La vista referencia columnas o tablas que ya no existen."),
    1109: ("Tabla desconocida", "Usás un alias o tabla que no está en el FROM (o en un DELETE con JOIN, no nombraste la tabla a borrar)."),
    1066: ("Alias repetido", "Usaste la misma tabla dos veces sin alias distinto, o repetiste un alias. Ej: FROM asignaturas a JOIN asignaturas c ..."),
    3750: ("Falta la PRIMARY KEY", "Este servidor exige que toda tabla tenga PRIMARY KEY. Agregá una (por ejemplo id INT AUTO_INCREMENT PRIMARY KEY)."),
    0: ("Consulta demasiado grande", "La consulta devuelve demasiadas filas para compararla."),
    1353: ("Cabecera de la vista incorrecta", "La cantidad de columnas que nombraste en CREATE VIEW v (col1, col2, …) no coincide con la cantidad de columnas del SELECT."),
    1330: ("Vista: columnas duplicadas", "La vista tiene columnas repetidas: usá alias."),
    1393: ("Vista con JOIN no actualizable", "No se puede modificar una vista multitabla de esa forma."),
    1288: ("Vista no actualizable", "Esa vista no se puede usar como destino de INSERT/UPDATE/DELETE."),
    1305: ("Función inexistente", "Esa función no existe. Ojo: entre el nombre de la función y el paréntesis no puede haber espacio (COUNT(*), no COUNT (*))."),
    1630: ("Función inexistente", "Esa función no existe en MySQL. Ojo: no dejes espacio entre el nombre y el paréntesis: COUNT(*), AVG(nota)."),
    1584: ("Parámetros incorrectos", "Llamaste a una función con parámetros incorrectos."),
    1583: ("Parámetros incorrectos", "Llamaste a una función con parámetros incorrectos."),
    1582: ("Cantidad de parámetros incorrecta", "Esa función recibe otra cantidad de parámetros."),
    1235: ("No soportado por MySQL", "Esa construcción no está soportada (ej. LIMIT dentro de una subconsulta con IN). Envolvé la subconsulta en una tabla derivada."),
    4031: ("Conexión cerrada", "Se perdió la conexión. Probá de nuevo."),
}


def _cercanos(nombre, opciones, n=3):
    return difflib.get_close_matches(nombre.lower(), [o.lower() for o in opciones], n=n, cutoff=0.6)


def explicar(codigo, mensaje, esquema=None):
    """Devuelve dict con titulo, explicacion y sugerencias extra."""
    titulo, texto = EXPLICACIONES.get(codigo, ("Error de MySQL", "Revisá el mensaje del servidor."))
    sugerencias = []
    esquema = esquema or {}
    columnas = sorted({c for cols in esquema.get("columnas", {}).values() for c in cols})
    tablas = list(esquema.get("columnas", {}).keys())

    if codigo == 1054:
        m = re.search(r"Unknown column '([^']+)'", mensaje)
        if m:
            col = m.group(1).split(".")[-1]
            cerc = _cercanos(col, columnas)
            if cerc:
                sugerencias.append("¿Quisiste decir " + ", ".join("«%s»" % c for c in cerc) + "?")
            dueños = [t for t, cols in esquema.get("columnas", {}).items() if col.lower() in [x.lower() for x in cols]]
            if dueños:
                sugerencias.append("La columna «%s» está en: %s. ¿Incluiste esa tabla en el FROM/JOIN?" % (col, ", ".join(dueños)))
            if "where clause" in mensaje and not dueños:
                sugerencias.append("Si es un alias del SELECT, recordá que no se puede usar en el WHERE (sí en HAVING y ORDER BY).")
    elif codigo == 1146:
        m = re.search(r"Table '[^.]+\.([^']+)' doesn't exist", mensaje)
        if m:
            cerc = _cercanos(m.group(1), tablas)
            if cerc:
                sugerencias.append("¿Quisiste decir " + ", ".join("«%s»" % c for c in cerc) + "?")
    elif codigo == 1265 or codigo == 1366:
        m = re.search(r"column '([^']+)'", mensaje)
        if m:
            col = m.group(1)
            for (t, c), vals in esquema.get("enums", {}).items():
                if c == col:
                    sugerencias.append("Valores válidos de %s.%s: %s" % (t, c, ", ".join("'%s'" % v for v in vals)))
    elif codigo == 1064:
        m = re.search(r"near '(.{0,80})", mensaje, re.S)
        if m:
            frag = m.group(1).strip().rstrip("'")
            if frag:
                sugerencias.append("El problema está justo antes de: «%s»" % frag[:60])
            if frag.upper().startswith("FROM"):
                sugerencias.append("¿Dejaste una coma después de la última columna del SELECT?")
    elif codigo == 1055:
        m = re.search(r"#(\d+) of SELECT list .*?column '([^']+)'", mensaje)
        if m:
            sugerencias.append("La columna «%s» tiene que ir en el GROUP BY (o dentro de una función de agregación)." % m.group(2).split(".")[-1])
    return {"codigo": codigo, "mensaje": mensaje, "titulo": titulo, "explicacion": texto, "sugerencias": sugerencias}
