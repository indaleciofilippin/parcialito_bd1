"""Utilidades para separar sentencias SQL y clasificarlas."""
import re


def separar_sentencias(sql):
    """Separa un script en sentencias respetando strings y comentarios.

    Devuelve una lista de strings (sin el ';' final, sin vacías).
    """
    sentencias = []
    actual = []
    i = 0
    n = len(sql)
    while i < n:
        c = sql[i]
        sig = sql[i + 1] if i + 1 < n else ""
        # Comentario de línea: -- (con espacio) o #
        if (c == "-" and sig == "-" and (i + 2 >= n or sql[i + 2] in " \t\r\n")) or c == "#":
            fin = sql.find("\n", i)
            if fin == -1:
                fin = n
            actual.append(sql[i:fin])
            i = fin
            continue
        # Comentario de bloque
        if c == "/" and sig == "*":
            fin = sql.find("*/", i + 2)
            fin = n if fin == -1 else fin + 2
            actual.append(sql[i:fin])
            i = fin
            continue
        # Strings y identificadores entre comillas
        if c in ("'", '"', "`"):
            j = i + 1
            while j < n:
                if sql[j] == "\\" and c != "`":
                    j += 2
                    continue
                if sql[j] == c:
                    if j + 1 < n and sql[j + 1] == c:  # comilla escapada duplicada
                        j += 2
                        continue
                    break
                j += 1
            actual.append(sql[i:j + 1])
            i = j + 1
            continue
        if c == ";":
            s = "".join(actual).strip()
            if quitar_comentarios(s).strip():
                sentencias.append(s)
            actual = []
            i += 1
            continue
        actual.append(c)
        i += 1
    s = "".join(actual).strip()
    if quitar_comentarios(s).strip():
        sentencias.append(s)
    return sentencias


def quitar_comentarios(sql):
    """Quita comentarios (no toca el contenido de strings)."""
    out = []
    i = 0
    n = len(sql)
    while i < n:
        c = sql[i]
        sig = sql[i + 1] if i + 1 < n else ""
        if (c == "-" and sig == "-" and (i + 2 >= n or sql[i + 2] in " \t\r\n")) or c == "#":
            fin = sql.find("\n", i)
            if fin == -1:
                break
            i = fin
            continue
        if c == "/" and sig == "*":
            fin = sql.find("*/", i + 2)
            if fin == -1:
                break
            i = fin + 2
            out.append(" ")
            continue
        if c in ("'", '"', "`"):
            j = i + 1
            while j < n:
                if sql[j] == "\\" and c != "`":
                    j += 2
                    continue
                if sql[j] == c:
                    if j + 1 < n and sql[j + 1] == c:
                        j += 2
                        continue
                    break
                j += 1
            out.append(sql[i:j + 1])
            i = j + 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def sin_strings(sql):
    """Reemplaza el contenido de strings por '' para analizar palabras clave."""
    sql = quitar_comentarios(sql)
    return re.sub(r"'(?:[^'\\]|\\.|'')*'|\"(?:[^\"\\]|\\.|\"\")*\"", "''", sql)


def primera_palabra(sql):
    s = sin_strings(sql).strip().lstrip("(").strip()
    m = re.match(r"([A-Za-z_]+)", s)
    return m.group(1).upper() if m else ""


def tipo_sentencia(sql):
    """Clasifica: select, dml, ddl, transaccion, otra."""
    p = primera_palabra(sql)
    s = sin_strings(sql).upper()
    if p in ("SELECT", "WITH", "TABLE", "VALUES"):
        return "select"
    if p in ("SHOW", "DESCRIBE", "DESC", "EXPLAIN"):
        return "select"
    if p in ("INSERT", "UPDATE", "DELETE", "REPLACE"):
        return "dml"
    if p in ("CREATE", "ALTER", "DROP", "RENAME", "TRUNCATE"):
        if re.match(r"\s*CREATE\s+(OR\s+REPLACE\s+)?(ALGORITHM\s*=\s*\w+\s+)?(DEFINER\s*=\s*\S+\s+)?(SQL\s+SECURITY\s+\w+\s+)?VIEW\b", s):
            return "view"
        return "ddl"
    if p in ("START", "BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE"):
        return "transaccion"
    return "otra"


PROHIBIDOS = [
    (r"\bDROP\s+(DATABASE|SCHEMA)\b", "No se permite DROP DATABASE en la app (protegemos tu base de práctica)."),
    (r"\bCREATE\s+(DATABASE|SCHEMA)\b", "No hace falta crear bases: ya estás trabajando sobre la base de la universidad."),
    (r"^\s*USE\b", "No hace falta USE: la app ya está posicionada en la base de la universidad."),
    (r"\b(GRANT|REVOKE)\b", "GRANT/REVOKE no están permitidos en la app."),
    (r"\bSET\s+(GLOBAL|PERSIST)\b", "No se pueden cambiar variables globales del servidor desde la app."),
    (r"\bparcialito_\w+", "No uses nombres de base de datos: trabajá con las tablas directamente (alumnos, docentes, …)."),
    (r"\b(mysql|performance_schema|sys)\s*\.", "Esa base del sistema no está disponible en la app."),
    (r"\b(SLEEP|BENCHMARK|GET_LOCK)\s*\(", "Esa función no está permitida en la app."),
    (r"\b(INTO\s+OUTFILE|INTO\s+DUMPFILE|LOAD\s+DATA|LOAD_FILE)\b", "Lectura/escritura de archivos no permitida."),
    (r"\b(CREATE|DROP|ALTER)\s+(USER|ROLE)\b", "No se pueden administrar usuarios desde la app."),
    (r"\b(SHUTDOWN|KILL)\b", "Comando no permitido."),
    (r"\b(CREATE|DROP)\s+(PROCEDURE|FUNCTION|TRIGGER|EVENT)\b", "Procedimientos/triggers no forman parte del parcialito; no están habilitados."),
]


def verificar_prohibidos(sql):
    s = sin_strings(sql)
    for patron, msg in PROHIBIDOS:
        if re.search(patron, s, re.IGNORECASE | re.MULTILINE):
            return msg
    return None


def nombre_vista(sql):
    s = sin_strings(sql)
    m = re.search(r"\bVIEW\s+(?:`?(\w+)`?\.)?`?(\w+)`?", s, re.IGNORECASE)
    return m.group(2) if m else None


def set_permitido(sql):
    """Solo se permite SET SQL_SAFE_UPDATES = 0/1 (como en Workbench)."""
    s = sin_strings(sql).strip().rstrip(";").strip()
    return re.match(r"^SET\s+(SESSION\s+|@@SESSION\.|@@)?SQL_SAFE_UPDATES\s*=\s*(0|1|ON|OFF|TRUE|FALSE)$", s, re.IGNORECASE) is not None
