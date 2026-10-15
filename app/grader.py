"""Motor de ejecución y corrección de ejercicios SQL."""
import datetime
import decimal
import itertools
import re
import time
import unicodedata
import uuid
from collections import Counter

import pymysql

from . import db, errores, sqlutil

MAX_FILAS_UI = 500
MAX_FILAS_COMPARAR = 80000
MAX_FILAS_CONSOLA = 1000


# ---------------------------------------------------------------------------
# Esquema (para autocompletar y para explicar errores)
# ---------------------------------------------------------------------------
_ESQUEMA_CACHE = {}


def esquema(base=db.DB_SANDBOX, refrescar=False):
    if base in _ESQUEMA_CACHE and not refrescar:
        return _ESQUEMA_CACHE[base]
    conn = db.conectar()
    cur = conn.cursor()
    cur.execute("""SELECT c.TABLE_NAME, c.COLUMN_NAME, c.COLUMN_TYPE, c.DATA_TYPE, c.IS_NULLABLE,
                          c.COLUMN_KEY, c.EXTRA, c.COLUMN_DEFAULT, t.TABLE_TYPE
                   FROM information_schema.COLUMNS c
                   JOIN information_schema.TABLES t ON t.TABLE_SCHEMA=c.TABLE_SCHEMA AND t.TABLE_NAME=c.TABLE_NAME
                   WHERE c.TABLE_SCHEMA=%s ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION""", (base,))
    columnas, detalle, enums, tipos_tabla = {}, {}, {}, {}
    for t, c, ctype, dtype, nullable, key, extra, default, ttype in cur.fetchall():
        columnas.setdefault(t, []).append(c)
        tipos_tabla[t] = "vista" if ttype == "VIEW" else "tabla"
        info = {"nombre": c, "tipo": ctype, "nulo": nullable == "YES", "clave": key, "extra": extra,
                "default": db.a_json(default)}
        if dtype == "enum":
            vals = re.findall(r"'((?:[^']|'')*)'", ctype)
            enums[(t, c)] = vals
            info["valores"] = vals
        detalle.setdefault(t, []).append(info)
    cur.execute("""SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                   FROM information_schema.KEY_COLUMN_USAGE
                   WHERE TABLE_SCHEMA=%s AND REFERENCED_TABLE_NAME IS NOT NULL""", (base,))
    fks = [{"tabla": a, "columna": b, "ref_tabla": c, "ref_columna": d} for a, b, c, d in cur.fetchall()]
    conteos = {}
    for t, tipo in tipos_tabla.items():
        if tipo == "tabla":
            cur.execute("SELECT COUNT(*) FROM `%s`.`%s`" % (base, t))
            conteos[t] = cur.fetchone()[0]
    conn.close()
    r = {"columnas": columnas, "detalle": detalle, "enums": enums, "fks": fks, "conteos": conteos, "tipos": tipos_tabla}
    _ESQUEMA_CACHE[base] = r
    return r


def invalidar_esquema():
    _ESQUEMA_CACHE.clear()


# ---------------------------------------------------------------------------
# Ejecución básica
# ---------------------------------------------------------------------------
class ErrorSQL(Exception):
    def __init__(self, codigo, mensaje, sentencia=None, indice=None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.sentencia = sentencia
        self.indice = indice

    def a_dict(self):
        d = errores.explicar(self.codigo, self.mensaje, esquema())
        if self.sentencia is not None:
            d["sentencia"] = self.sentencia
            d["indice"] = self.indice
        return d


def _conexion(base, safe_updates=False):
    conn = db.conectar(base)
    cur = conn.cursor()
    cur.execute("SET SESSION MAX_EXECUTION_TIME=12000")
    cur.execute("SET SESSION innodb_lock_wait_timeout=8")
    cur.execute("SET SESSION sql_safe_updates=%d" % (1 if safe_updates else 0))
    try:   # Aiven exige PK en toda tabla: lo desactivamos para que los ejercicios de DDL se corrijan bien
        cur.execute("SET SESSION sql_require_primary_key=0")
    except Exception:
        pass
    return conn, cur


def _ejecutar(cur, sql, indice=None, limite=None):
    """Ejecuta una sentencia y devuelve dict con columnas/filas o filas afectadas."""
    limite = limite or MAX_FILAS_COMPARAR
    t0 = time.time()
    try:
        cur.execute(sql)
    except pymysql.err.MySQLError as e:
        codigo = e.args[0] if e.args else 0
        msg = e.args[1] if len(e.args) > 1 else str(e)
        if not isinstance(codigo, int):
            codigo, msg = 0, str(e)
        raise ErrorSQL(codigo, msg, sql, indice)
    ms = round((time.time() - t0) * 1000, 1)
    if cur.description:
        columnas = [d[0] for d in cur.description]
        filas = list(cur.fetchmany(limite + 1))
        mas = len(filas) > limite
        if mas:
            while cur.fetchmany(5000):   # descartar el resto
                pass
            if limite == MAX_FILAS_COMPARAR:
                raise ErrorSQL(0, "Tu consulta devuelve más de %s filas. ¿Te faltó una condición de JOIN (producto cartesiano) o un WHERE?" % format(limite, ",").replace(",", "."), sql, indice)
            filas = filas[:limite]
        return {"tipo": "resultado", "columnas": columnas, "filas": filas, "ms": ms, "sql": sql, "mas": mas}
    return {"tipo": "ok", "afectadas": cur.rowcount, "ms": ms, "sql": sql}


def para_ui(res, max_filas=MAX_FILAS_UI):
    """Convierte un resultado para mandarlo al frontend (recortado)."""
    if res is None:
        return None
    if res.get("tipo") != "resultado":
        return {k: v for k, v in res.items() if k != "filas"}
    filas = res["filas"]
    return {
        "tipo": "resultado",
        "columnas": res["columnas"],
        "filas": [[db.a_json(v) for v in f] for f in filas[:max_filas]],
        "total": len(filas),
        "truncado": len(filas) > max_filas,
        "ms": res.get("ms"),
        "sql": res.get("sql"),
    }


# ---------------------------------------------------------------------------
# Normalización y comparación de resultados
# ---------------------------------------------------------------------------
def _norm(v, prec=2):
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int):
        return v
    if isinstance(v, (float, decimal.Decimal)):
        # Redondeo "half up" exacto, igual que ROUND() de MySQL (Python redondea 6.475 -> 6.47)
        d = v if isinstance(v, decimal.Decimal) else decimal.Decimal(repr(v))
        if not d.is_finite():
            return float(d)
        f = float(d.quantize(decimal.Decimal(1).scaleb(-prec), rounding=decimal.ROUND_HALF_UP))
        if f == int(f):
            return int(f)
        return f
    if isinstance(v, datetime.datetime):
        if v.time() == datetime.time(0):
            return v.date().isoformat()
        return v.isoformat(sep=" ")
    if isinstance(v, datetime.date):
        return v.isoformat()
    if isinstance(v, datetime.timedelta):
        return str(v)
    if isinstance(v, (bytes, bytearray)):
        try:
            v = v.decode("utf-8")
        except Exception:
            return v.hex()
    if isinstance(v, str):
        s = v.strip()
        return s
    if isinstance(v, set):
        return ",".join(sorted(v))
    return v


def _normalizar(filas, prec):
    return [tuple(_norm(v, prec) for v in f) for f in filas]


def _indices(columnas, nombres):
    low = [c.lower() for c in columnas]
    idx = []
    for n in nombres:
        if n.lower() in low:
            idx.append(low.index(n.lower()))
        else:
            return None
    return idx


def _buscar_mapeo(alt, cand, E, U, ordenado):
    """Busca asignación inyectiva columna esperada -> columna del usuario."""
    objetivo = [tuple(f[j] for j in alt) for f in E]
    obj_counter = None if ordenado else Counter(objetivo)
    listas = [cand[j] for j in alt]
    # limitar explosión combinatoria
    total = 1
    for l in listas:
        total *= max(1, len(l))
    if total > 5000:
        listas = [l[:4] for l in listas]
    for combo in itertools.product(*listas):
        if len(set(combo)) != len(combo):
            continue
        proy = [tuple(f[k] for k in combo) for f in U]
        if ordenado:
            if proy == objetivo:
                return list(combo)
        elif Counter(proy) == obj_counter:
            return list(combo)
    return None


def _clave_texto(v):
    """Aproxima la collation utf8mb4_0900_ai_ci (sin acentos ni mayúsculas)."""
    if isinstance(v, str):
        return "".join(c for c in unicodedata.normalize("NFD", v) if unicodedata.category(c) != "Mn").casefold()
    return v


def _orden_valido(U, mapeo_cols, orden):
    """orden: lista de (indice_usuario, 'asc'|'desc')."""
    def clave(f):
        return tuple(_clave_texto(f[k]) for k, _ in orden)
    prev = None
    for f in U:
        actual = clave(f)
        if prev is not None:
            for (k, sentido), a, b in zip(orden, prev, actual):
                if a == b:
                    continue
                if a is None or b is None:
                    break
                try:
                    if sentido == "desc" and a < b:
                        return False
                    if sentido != "desc" and a > b:
                        return False
                except TypeError:
                    pass
                break
        prev = actual
    return True


def comparar(esp_cols, esp_filas, usr_cols, usr_filas, alternativas=None, ordenado=False, orden=None):
    """Compara resultados de forma flexible.

    alternativas: lista de listas de nombres de columnas esperadas que deben aparecer
                  (por valores, sin importar alias ni orden). None = todas las columnas.
    Devuelve dict(ok, motivo, mensajes, detalle)
    """
    alts = []
    for alt in (alternativas or [esp_cols]):
        idx = _indices(esp_cols, alt)
        if idx is not None:
            alts.append((alt, idx))
    if not alts:
        alts = [(esp_cols, list(range(len(esp_cols))))]

    ultimo_fallo = None
    prioridad = {"orden": 5, "filas": 4, "columnas": 3, "duplicados": 2, "cantidad": 1}

    def mejor(a, b):
        if a is None:
            return b
        return b if prioridad.get(b.get("motivo"), 0) > prioridad.get(a.get("motivo"), 0) else a

    for prec in (2, 1):
        E = _normalizar(esp_filas, prec)
        U = _normalizar(usr_filas, prec)
        if len(E) != len(U):
            if ultimo_fallo is None:
                ultimo_fallo = _diagnostico_cantidad(esp_cols, E, usr_cols, U, alts)
            continue
        ucount = [Counter(f[k] for f in U) for k in range(len(usr_cols))]
        ecount = [Counter(f[j] for f in E) for j in range(len(esp_cols))]
        for nombres, alt in alts:
            cand = {j: [k for k in range(len(usr_cols)) if ucount[k] == ecount[j]] for j in alt}
            faltan = [esp_cols[j] for j in alt if not cand[j]]
            if faltan:
                ultimo_fallo = mejor(ultimo_fallo, _diagnostico_columnas(esp_cols, E, usr_cols, U, alt, faltan))
                continue
            mapeo = _buscar_mapeo(alt, cand, E, U, ordenado and not orden)
            if mapeo is None:
                if ordenado and not orden and _buscar_mapeo(alt, cand, E, U, False):
                    ultimo_fallo = mejor(ultimo_fallo, {"ok": False, "motivo": "orden",
                                    "mensajes": ["Las filas son correctas pero el ORDEN no es el pedido. Revisá el ORDER BY."]})
                else:
                    ultimo_fallo = mejor(ultimo_fallo, _diagnostico_filas(esp_cols, E, usr_cols, U, alt))
                continue
            if orden:
                ordidx = []
                for col, sentido in orden:
                    j = esp_cols.index(col) if col in esp_cols else [c.lower() for c in esp_cols].index(col.lower())
                    if j in alt:
                        ordidx.append((mapeo[alt.index(j)], sentido))
                    else:
                        ks = [k for k in range(len(usr_cols)) if ucount[k] == ecount[j]]
                        if ks:
                            ordidx.append((ks[0], sentido))
                if not _orden_valido(U, mapeo, ordidx):
                    ultimo_fallo = mejor(ultimo_fallo, {"ok": False, "motivo": "orden",
                                    "mensajes": ["Las filas son correctas pero no están ordenadas como se pide (%s)." %
                                                 ", ".join("%s %s" % (c, s.upper()) for c, s in orden)]})
                    continue
            mensajes = []
            if prec == 1:
                mensajes.append("Coincide redondeando a 1 decimal (la solución usa 2 decimales).")
            extra = sum(1 for k in range(len(usr_cols))
                        if k not in mapeo and not any(ucount[k] == ecount[j] for j in range(len(esp_cols))))
            if extra > 0:
                mensajes.append("Tu resultado tiene %d columna(s) extra; no está mal, pero en el parcialito mostrá lo que se pide." % extra)
            return {"ok": True, "motivo": "ok", "mensajes": mensajes,
                    "mapeo": {esp_cols[j]: usr_cols[k] for j, k in zip(alt, mapeo)}}
    return ultimo_fallo or {"ok": False, "motivo": "desconocido", "mensajes": ["El resultado no coincide con el esperado."]}


def _mapeo_por_nombre_o_valores(esp_cols, E, usr_cols, U, alt):
    low = [c.lower() for c in usr_cols]
    mapeo = []
    usados = set()
    for j in alt:
        nombre = esp_cols[j].lower()
        k = None
        if nombre in low and low.index(nombre) not in usados:
            k = low.index(nombre)
        else:
            sj = set(f[j] for f in E)
            mejor, mejor_score = None, 0.0
            for kk in range(len(usr_cols)):
                if kk in usados:
                    continue
                sk = set(f[kk] for f in U)
                if not sj or not sk:
                    continue
                score = len(sj & sk) / float(len(sj | sk))
                if score > mejor_score:
                    mejor, mejor_score = kk, score
            if mejor is not None and mejor_score >= 0.3:
                k = mejor
        if k is None:
            return None
        usados.add(k)
        mapeo.append(k)
    return mapeo


def _muestras(esp_cols, E, usr_cols, U, alt):
    mapeo = _mapeo_por_nombre_o_valores(esp_cols, E, usr_cols, U, alt)
    if mapeo is None:
        return None
    pe = Counter(tuple(f[j] for j in alt) for f in E)
    pu = Counter(tuple(f[k] for k in mapeo) for f in U)
    faltan = list((pe - pu).elements())[:6]
    sobran = list((pu - pe).elements())[:6]
    return {
        "columnas": [esp_cols[j] for j in alt],
        "faltan": [[db.a_json(v) for v in f] for f in faltan],
        "sobran": [[db.a_json(v) for v in f] for f in sobran],
        "n_faltan": sum((pe - pu).values()),
        "n_sobran": sum((pu - pe).values()),
    }


def _diagnostico_cantidad(esp_cols, E, usr_cols, U, alts):
    ne, nu = len(E), len(U)
    mensajes = ["Se esperaban %d fila(s) y tu consulta devolvió %d." % (ne, nu)]
    motivo = "cantidad"
    nombres, alt = alts[0]
    # ¿filas repetidas?
    if nu > ne:
        for nombres, alt in alts:
            mapeo = _mapeo_por_nombre_o_valores(esp_cols, E, usr_cols, U, alt)
            if mapeo is None:
                continue
            se = set(tuple(f[j] for j in alt) for f in E)
            su = set(tuple(f[k] for k in mapeo) for f in U)
            if se == su and len(set(U)) < len(U):
                mensajes.append("¡Las filas correctas están todas! Pero aparecen repetidas: "
                                "probablemente te falta DISTINCT o agrupar (GROUP BY), o el JOIN multiplica filas.")
                motivo = "duplicados"
                break
    if nu == 0:
        mensajes.append("Tu consulta no devolvió filas: revisá las condiciones del WHERE / JOIN.")
    elif ne == 0:
        mensajes.append("Con estos datos la respuesta correcta no tiene filas.")
    d = {"ok": False, "motivo": motivo, "mensajes": mensajes}
    m = _muestras(esp_cols, E, usr_cols, U, alt)
    if m and motivo != "duplicados":
        d["muestras"] = m
    return d


def _diagnostico_columnas(esp_cols, E, usr_cols, U, alt, faltan):
    mensajes = []
    low = [c.lower() for c in usr_cols]
    con_nombre = [c for c in faltan if c.lower() in low]
    sin_nombre = [c for c in faltan if c.lower() not in low]
    if sin_nombre:
        mensajes.append("No encontramos en tu resultado la información de: %s." % ", ".join("«%s»" % c for c in sin_nombre))
    if con_nombre:
        mensajes.append("La(s) columna(s) %s está(n), pero sus valores no coinciden con lo esperado." %
                        ", ".join("«%s»" % c for c in con_nombre))
    d = {"ok": False, "motivo": "columnas", "mensajes": mensajes}
    m = _muestras(esp_cols, E, usr_cols, U, alt)
    if m and (m["faltan"] or m["sobran"]):
        d["muestras"] = m
    return d


def _diagnostico_filas(esp_cols, E, usr_cols, U, alt):
    d = {"ok": False, "motivo": "filas",
         "mensajes": ["Tenés la cantidad de filas correcta y las columnas parecen correctas, pero algunas filas no coinciden."]}
    m = _muestras(esp_cols, E, usr_cols, U, alt)
    if m:
        d["muestras"] = m
    return d


# ---------------------------------------------------------------------------
# Validaciones previas
# ---------------------------------------------------------------------------
def preparar_sentencias(sql, permitidos):
    """Separa y valida. permitidos: conjunto de tipos (select, dml, ddl, view)."""
    if not sql or not sqlutil.quitar_comentarios(sql).strip():
        raise ValueError("Escribí una consulta primero.")
    msg = sqlutil.verificar_prohibidos(sql)
    if msg:
        raise ValueError(msg)
    sentencias = sqlutil.separar_sentencias(sql)
    if not sentencias:
        raise ValueError("Escribí una consulta primero.")
    for s in sentencias:
        t = sqlutil.tipo_sentencia(s)
        if t == "transaccion":
            raise ValueError("No uses START TRANSACTION / COMMIT / ROLLBACK: la app maneja las transacciones por vos.")
        if t not in permitidos:
            nombres = {"select": "SELECT", "dml": "INSERT/UPDATE/DELETE", "ddl": "CREATE/ALTER/DROP TABLE",
                       "view": "CREATE VIEW", "otra": "esa sentencia"}
            if t == "otra" and sqlutil.set_permitido(s):
                continue  # SET SQL_SAFE_UPDATES = 0/1 (como en Workbench)
            raise ValueError("En este ejercicio no corresponde usar %s. Se espera: %s." % (
                nombres.get(t, t), " / ".join(nombres[p] for p in permitidos if p in nombres)))
    return sentencias


# ---------------------------------------------------------------------------
# Corrección por tipo de ejercicio
# ---------------------------------------------------------------------------
def _fixture_sql(ej):
    from .ejercicios.fixtures import CASOS_BORDE
    partes = []
    if ej.get("casos_borde"):
        partes.append(CASOS_BORDE)
    if ej.get("casos_borde_sql"):
        partes.append(ej["casos_borde_sql"])
    return "\n".join(partes)


def _correr_select_en_txn(cur, sql, preparacion="", limite=None):
    cur.execute("START TRANSACTION")
    try:
        for s in sqlutil.separar_sentencias(preparacion or ""):
            cur.execute(s)
        res = None
        for i, s in enumerate(sqlutil.separar_sentencias(sql)):
            r = _ejecutar(cur, s, i, limite=limite)
            if r["tipo"] == "resultado":
                res = r
        return res
    finally:
        try:
            cur.execute("ROLLBACK")
        except Exception:
            pass


def _consultas_aceptadas(ej):
    lista = [("Solución", ej["solucion"])]
    for a in ej.get("alternativas", []) or []:
        lista.append((a.get("titulo", "Alternativa"), a["sql"]))
    for v in ej.get("variantes", []) or []:
        lista.append((v.get("titulo", "Variante"), v["sql"]))
    return lista


def _verificar_contiene(ej, sql):
    for req in ej.get("debe_contener", []) or []:
        patron = req["patron"] if isinstance(req, dict) else req
        if not re.search(patron, sqlutil.sin_strings(sql), re.IGNORECASE):
            return req.get("mensaje") if isinstance(req, dict) else "Tu consulta debe usar: %s" % patron
    return None


def corregir_select(ej, sql, opciones=None):
    sentencias = preparar_sentencias(sql, {"select"})
    if len(sentencias) > 1:
        raise ValueError("Escribí una sola consulta SELECT (tenés %d sentencias)." % len(sentencias))
    conn, cur = _conexion(db.DB_SANDBOX)
    try:
        pasadas = [("datos", "")]
        fx = _fixture_sql(ej)
        if fx:
            pasadas.append(("casos_borde", fx))
        resultado_ui = None
        for nombre, prep in pasadas:
            usr = _correr_select_en_txn(cur, sentencias[0], prep)
            if resultado_ui is None:
                resultado_ui = para_ui(usr)
            comparaciones = []
            ok = None
            for titulo, q in _consultas_aceptadas(ej):
                esp = _correr_select_en_txn(cur, q, prep)
                c = comparar(esp["columnas"], esp["filas"], usr["columnas"], usr["filas"],
                             ej.get("columnas"), ej.get("ordenado", False), ej.get("orden"))
                comparaciones.append(c)
                if c["ok"]:
                    ok = (titulo, c)
                    break
            if not ok:
                fallo = comparaciones[0]
                if nombre == "casos_borde":
                    fallo = dict(fallo)
                    fallo["mensajes"] = [
                        "Con los datos originales tu consulta da bien, pero falla cuando agregamos casos borde "
                        "(por ejemplo alumnos sin inscripciones, docentes sin comisiones, aulas sin uso o carreras sin alumnos)."
                    ] + fallo["mensajes"]
                    fallo["pasada"] = "casos_borde"
                return {"ok": False, "resultado": resultado_ui, **fallo}
        aviso = _verificar_contiene(ej, sql)
        if aviso:
            return {"ok": False, "resultado": resultado_ui, "motivo": "requisito", "mensajes": [aviso]}
        titulo, c = ok
        mensajes = list(c.get("mensajes", []))
        if titulo != "Solución" and any(v.get("titulo") == titulo for v in ej.get("variantes", []) or []):
            mensajes.insert(0, "Coincide con la interpretación: %s." % titulo)
        if fx:
            mensajes.append("Verificado con los datos reales y con casos borde.")
        return {"ok": True, "resultado": resultado_ui, "mensajes": mensajes}
    finally:
        conn.close()


def _correr_dml(cur, sentencias, preparacion, verificaciones, safe_updates=False):
    """Ejecuta en transacción y devuelve (antes, despues, pasos). Siempre hace ROLLBACK."""
    cur.execute("START TRANSACTION")
    pasos = []
    try:
        for s in sqlutil.separar_sentencias(preparacion or ""):
            cur.execute(s)
        antes = [_ejecutar(cur, v) for v in verificaciones]
        if safe_updates:
            cur.execute("SET SESSION sql_safe_updates=1")
        for i, s in enumerate(sentencias):
            r = _ejecutar(cur, s, i)
            pasos.append(r)
        if safe_updates:
            cur.execute("SET SESSION sql_safe_updates=0")
        despues = [_ejecutar(cur, v) for v in verificaciones]
        return antes, despues, pasos
    finally:
        try:
            cur.execute("SET SESSION sql_safe_updates=0")
            cur.execute("ROLLBACK")
        except Exception:
            pass


def _lista(v):
    if not v:
        return []
    return v if isinstance(v, list) else [v]


def _diff(antes, despues):
    """Diferencias entre dos resultados. Si la 1ra columna es clave única, distingue modificadas."""
    fa = _normalizar(antes["filas"], 2)
    fd = _normalizar(despues["filas"], 2)
    base = {
        "columnas": despues["columnas"],
        "total_antes": len(fa),
        "total_despues": len(fd),
    }
    ka = [f[0] for f in fa]
    kd = [f[0] for f in fd]
    if fa and fd and len(despues["columnas"]) > 1 and len(set(ka)) == len(ka) and len(set(kd)) == len(kd):
        ma, md = {f[0]: f for f in fa}, {f[0]: f for f in fd}
        nuevas = [md[k] for k in kd if k not in ma]
        quitadas = [ma[k] for k in ka if k not in md]
        modificadas = [(ma[k], md[k]) for k in kd if k in ma and ma[k] != md[k]]
    else:
        a, d = Counter(fa), Counter(fd)
        nuevas = list((d - a).elements())
        quitadas = list((a - d).elements())
        modificadas = []
    conv = lambda f: [db.a_json(v) for v in f]
    base.update({
        "nuevas": [conv(f) for f in nuevas[:50]],
        "quitadas": [conv(f) for f in quitadas[:50]],
        "modificadas": [{"antes": conv(a), "despues": conv(d)} for a, d in modificadas[:50]],
        "n_nuevas": len(nuevas),
        "n_quitadas": len(quitadas),
        "n_modificadas": len(modificadas),
    })
    return base


def _n_cambios(c):
    return c["n_nuevas"] + c["n_quitadas"] + c.get("n_modificadas", 0)


def _desc_cambios(c):
    partes = []
    if c.get("n_modificadas"):
        partes.append("%d modificada(s)" % c["n_modificadas"])
    if c["n_nuevas"]:
        partes.append("%d nueva(s)" % c["n_nuevas"])
    if c["n_quitadas"]:
        partes.append("%d eliminada(s)" % c["n_quitadas"])
    return ", ".join(partes) or "ningún cambio"


def _evaluar_condiciones(cur, condiciones):
    res = []
    for cond in condiciones:
        try:
            cur.execute(cond["sql"])
            fila = cur.fetchone()
            ok = bool(fila and fila[0])
            res.append({"desc": cond.get("desc", cond["sql"]), "ok": ok,
                        "detalle": cond.get("ok_msg", "Cumple") if ok else cond.get("fallo_msg", "No se cumple")})
        except pymysql.err.MySQLError as e:
            res.append({"desc": cond.get("desc", ""), "ok": False, "detalle": "Error al verificar: %s" % e.args[1]})
    return res


def ejecutar_dml(ej, sql, opciones=None):
    opciones = opciones or {}
    sentencias = preparar_sentencias(sql, {"dml", "select"})
    conn, cur = _conexion(db.DB_SANDBOX)
    try:
        verifs = _lista(ej.get("verificacion"))
        antes, despues, pasos = _correr_dml(cur, sentencias, ej.get("preparacion"), verifs, opciones.get("safe_updates"))
        return {
            "pasos": [para_ui(p, 100) for p in pasos],
            "cambios": [_diff(a, d) for a, d in zip(antes, despues)],
            "verificacion_sql": verifs,
        }
    finally:
        conn.close()


def corregir_dml(ej, sql, opciones=None):
    opciones = opciones or {}
    sentencias = preparar_sentencias(sql, {"dml", "select"})
    if not any(sqlutil.tipo_sentencia(s) == "dml" for s in sentencias):
        raise ValueError("Este ejercicio se resuelve con INSERT, UPDATE o DELETE.")
    conn, cur = _conexion(db.DB_SANDBOX)
    try:
        verifs = _lista(ej.get("verificacion"))
        if ej.get("condiciones"):
            # Ejercicio abierto: se verifica que se cumplan condiciones (no se compara con la solución)
            cur.execute("START TRANSACTION")
            try:
                for s in sqlutil.separar_sentencias(ej.get("preparacion") or ""):
                    cur.execute(s)
                antes = [_ejecutar(cur, v) for v in verifs]
                if opciones.get("safe_updates"):
                    cur.execute("SET SESSION sql_safe_updates=1")
                pasos = [_ejecutar(cur, s, i) for i, s in enumerate(sentencias)]
                cur.execute("SET SESSION sql_safe_updates=0")
                despues = [_ejecutar(cur, v) for v in verifs]
                checks = _evaluar_condiciones(cur, ej["condiciones"])
            finally:
                cur.execute("SET SESSION sql_safe_updates=0")
                cur.execute("ROLLBACK")
            ok = all(c["ok"] for c in checks)
            return {"ok": ok, "motivo": "ok" if ok else "checks", "checks": checks,
                    "pasos": [para_ui(p, 100) for p in pasos],
                    "cambios": [_diff(a, d) for a, d in zip(antes, despues)],
                    "mensajes": ["Los cambios se deshicieron automáticamente (tu base de práctica quedó igual)."]}

        antes, desp_u, pasos = _correr_dml(cur, sentencias, ej.get("preparacion"), verifs, opciones.get("safe_updates"))
        cambios_u = [_diff(a, d) for a, d in zip(antes, desp_u)]
        info = {"pasos": [para_ui(p, 100) for p in pasos], "cambios": cambios_u}
        primer_fallo = None
        for titulo, q in _consultas_aceptadas(ej):
            _, desp_e, _ = _correr_dml(cur, sqlutil.separar_sentencias(q), ej.get("preparacion"), verifs)
            iguales = [Counter(_normalizar(e["filas"], 2)) == Counter(_normalizar(u["filas"], 2))
                       for e, u in zip(desp_e, desp_u)]
            if all(iguales):
                mensajes = ["Los cambios se deshicieron automáticamente (tu base de práctica quedó igual)."]
                if titulo != "Solución" and any(v.get("titulo") == titulo for v in ej.get("variantes", []) or []):
                    mensajes.insert(0, "Coincide con la interpretación: %s." % titulo)
                return {"ok": True, "mensajes": mensajes, **info}
            if primer_fallo is None:
                cambios_e = [_diff(a, e) for a, e in zip(antes, desp_e)]
                mensajes = []
                if sum(_n_cambios(c) for c in cambios_u) == 0:
                    mensajes.append("Tu sentencia no produjo ningún cambio en los datos. Revisá el WHERE (o los valores).")
                else:
                    mensajes.append("El estado final de los datos no coincide con el esperado.")
                for i, (ce, cu) in enumerate(zip(cambios_e, cambios_u)):
                    etiqueta = ("Verificación %d: " % (i + 1)) if len(verifs) > 1 else ""
                    if not iguales[i]:
                        mensajes.append("%sse esperaba %s; tu script dejó %s." % (etiqueta, _desc_cambios(ce), _desc_cambios(cu)))
                j = iguales.index(False)
                ce_c = Counter(_normalizar(desp_e[j]["filas"], 2))
                cu_c = Counter(_normalizar(desp_u[j]["filas"], 2))
                faltan = list((ce_c - cu_c).elements())
                sobran = list((cu_c - ce_c).elements())
                primer_fallo = {
                    "mensajes": mensajes,
                    "muestras": {
                        "columnas": desp_e[j]["columnas"],
                        "faltan": [[db.a_json(v) for v in f] for f in faltan[:6]],
                        "sobran": [[db.a_json(v) for v in f] for f in sobran[:6]],
                        "n_faltan": len(faltan), "n_sobran": len(sobran),
                    },
                }
        return {"ok": False, "motivo": "estado", **primer_fallo, **info}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# DDL: CREATE TABLE / ALTER TABLE en un espacio temporal
# ---------------------------------------------------------------------------
def nuevo_scratch():
    return "%s_%s" % (db.DB_SCRATCH, uuid.uuid4().hex[:10])


def borrar_scratch(nombre):
    try:
        conn = db.conectar()
        conn.cursor().execute("DROP DATABASE IF EXISTS `%s`" % nombre)
        conn.close()
    except Exception:
        pass


def limpiar_scratch_viejos():
    try:
        conn = db.conectar()
        cur = conn.cursor()
        cur.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME LIKE 'parcialito\\_scratch%%'")
        for (n,) in cur.fetchall():
            cur.execute("DROP DATABASE IF EXISTS `%s`" % n)
        conn.close()
    except Exception:
        pass


def preparar_scratch(ej, nombre):
    from .setup_db import clonar_esquema
    tablas = ej.get("tablas") or db.TABLAS
    clonar_esquema(nombre, con_datos=False, tablas=tablas, datos_de=db.TABLAS_CHICAS)
    if ej.get("preparacion"):
        conn, cur = _conexion(nombre)
        for s in sqlutil.separar_sentencias(ej["preparacion"]):
            cur.execute(s)
        conn.close()


def _snapshot(cur, base):
    snap = {"tablas": {}, "fks": [], "unicos": [], "indices": [], "checks": []}
    cur.execute("""SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, EXTRA,
                          CHARACTER_MAXIMUM_LENGTH
                   FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s ORDER BY TABLE_NAME, ORDINAL_POSITION""", (base,))
    for t, c, dt, ct, nul, dflt, key, extra, largo in cur.fetchall():
        snap["tablas"].setdefault(t, {})[c] = {"tipo": dt, "tipo_completo": ct, "nulo": nul == "YES",
                                              "default": dflt, "clave": key, "extra": extra, "largo": largo}
    cur.execute("""SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME, CONSTRAINT_NAME
                   FROM information_schema.KEY_COLUMN_USAGE
                   WHERE TABLE_SCHEMA=%s AND REFERENCED_TABLE_NAME IS NOT NULL""", (base,))
    snap["fks"] = [{"tabla": a, "columna": b, "ref_tabla": c, "ref_columna": d, "nombre": e} for a, b, c, d, e in cur.fetchall()]
    cur.execute("""SELECT TABLE_NAME, INDEX_NAME, NON_UNIQUE, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX)
                   FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=%s
                   GROUP BY TABLE_NAME, INDEX_NAME, NON_UNIQUE""", (base,))
    for t, idx, nonu, cols in cur.fetchall():
        item = {"tabla": t, "nombre": idx, "columnas": cols.split(","), "unico": not nonu}
        snap["indices"].append(item)
    cur.execute("""SELECT tc.TABLE_NAME, cc.CONSTRAINT_NAME, cc.CHECK_CLAUSE
                   FROM information_schema.TABLE_CONSTRAINTS tc
                   JOIN information_schema.CHECK_CONSTRAINTS cc
                     ON cc.CONSTRAINT_SCHEMA=tc.CONSTRAINT_SCHEMA AND cc.CONSTRAINT_NAME=tc.CONSTRAINT_NAME
                   WHERE tc.TABLE_SCHEMA=%s AND tc.CONSTRAINT_TYPE='CHECK'""", (base,))
    snap["checks"] = [{"tabla": a, "nombre": b, "expr": c} for a, b, c in cur.fetchall()]
    return snap


def _contiene(nombre, subcadenas):
    n = nombre.lower()
    return any(s.lower() in n for s in subcadenas)


def _resolver(texto, alias):
    def rep(m):
        clave = m.group(1)
        if clave in alias:
            return alias[clave]
        return m.group(0)
    return re.sub(r"\{([\w\.]+)\}", rep, texto)


def _evaluar_checks(ej, cur, antes, despues, scratch):
    resultados = []
    alias = {"scratch": scratch}
    tablas_nuevas = [t for t in despues["tablas"] if t not in antes["tablas"]]
    for chk in ej.get("checks", []):
        tipo = chk["tipo"]
        desc = chk.get("desc", tipo)
        ok, detalle = False, ""
        try:
            if tipo == "columna_nueva":
                tabla = _resolver(chk["tabla"], alias)
                nuevas = [c for c in despues["tablas"].get(tabla, {}) if c not in antes["tablas"].get(tabla, {})]
                if chk.get("nombre_contiene"):
                    candidatas = [c for c in nuevas if _contiene(c, chk["nombre_contiene"])] or nuevas
                else:
                    candidatas = nuevas
                if not candidatas:
                    detalle = "No se agregó ninguna columna nueva a «%s»." % tabla
                else:
                    col = candidatas[0]
                    info = despues["tablas"][tabla][col]
                    if chk.get("alias"):
                        alias[chk["alias"]] = col
                    if chk.get("tipos") and info["tipo"] not in chk["tipos"]:
                        detalle = "Agregaste «%s» como %s. %s" % (col, info["tipo_completo"].upper(),
                                                                  chk.get("msg_tipo", "Tipo esperado: %s." % "/".join(t.upper() for t in chk["tipos"])))
                    else:
                        ok = True
                        detalle = "Columna «%s» %s" % (col, info["tipo_completo"].upper())
            elif tipo == "tabla_nueva":
                cands = [t for t in tablas_nuevas if _contiene(t, chk.get("nombre_contiene", [""]))]
                if chk.get("excluir_contiene"):
                    cands = [t for t in cands if not _contiene(t, chk["excluir_contiene"])] or cands
                if not cands:
                    detalle = "No se creó la tabla (nombre esperado parecido a: %s)." % ", ".join(chk.get("nombre_contiene", []))
                else:
                    t = cands[0]
                    if chk.get("alias"):
                        alias[chk["alias"]] = t
                    cols = despues["tablas"][t]
                    faltantes, tipo_mal = [], []
                    for spec in chk.get("columnas", []):
                        match = [c for c in cols if _contiene(c, spec["contiene"])]
                        if not match:
                            faltantes.append(spec.get("desc", "/".join(spec["contiene"])))
                            continue
                        c = match[0]
                        if spec.get("alias") and chk.get("alias"):
                            alias[chk["alias"] + "." + spec["alias"]] = c
                        if spec.get("tipos") and cols[c]["tipo"] not in spec["tipos"]:
                            tipo_mal.append("«%s» es %s (conviene %s)" % (c, cols[c]["tipo_completo"].upper(),
                                                                         "/".join(x.upper() for x in spec["tipos"])))
                    tiene_pk = any(i["tabla"] == t and i["nombre"] == "PRIMARY" for i in despues["indices"])
                    problemas = []
                    if faltantes:
                        problemas.append("Faltan columnas para: " + ", ".join(faltantes))
                    if tipo_mal:
                        problemas.append("Tipos a revisar: " + "; ".join(tipo_mal))
                    if chk.get("pk", True) and not tiene_pk:
                        problemas.append("La tabla no tiene PRIMARY KEY")
                    ok = not problemas
                    detalle = ("Tabla «%s» con columnas: %s" % (t, ", ".join(cols))) if ok else ". ".join(problemas) + "."
            elif tipo == "fk":
                tabla = _resolver(chk.get("tabla", ""), alias)
                ref = _resolver(chk["referencia"], alias)
                cands = [f for f in despues["fks"] if f["ref_tabla"] == ref and
                         ((tabla and f["tabla"] == tabla) or
                          (not tabla and f["tabla"] in tablas_nuevas and _contiene(f["tabla"], chk.get("tabla_contiene", [""]))))]
                if cands:
                    ok = True
                    detalle = "FOREIGN KEY %s.%s → %s.%s" % (cands[0]["tabla"], cands[0]["columna"], ref, cands[0]["ref_columna"])
                else:
                    detalle = "No encontramos una FOREIGN KEY que referencie a «%s»." % ref
            elif tipo == "unique":
                tabla = _resolver(chk["tabla"], alias)
                col = _resolver(chk["columna"], alias)
                ok = any(i["tabla"] == tabla and i["unico"] and i["columnas"] == [col] for i in despues["indices"])
                detalle = "UNIQUE sobre %s.%s" % (tabla, col) if ok else "No hay una restricción UNIQUE sobre %s.%s." % (tabla, col)
            elif tipo == "indice":
                tabla = _resolver(chk["tabla"], alias)
                col = _resolver(chk["columna"], alias)
                ok = any(i["tabla"] == tabla and i["columnas"][0] == col for i in despues["indices"]
                         if i not in antes["indices"])
                detalle = "Índice sobre %s.%s" % (tabla, col) if ok else "No se creó un índice nuevo sobre %s.%s." % (tabla, col)
            elif tipo == "check_existe":
                tabla = _resolver(chk["tabla"], alias)
                nuevos = [c for c in despues["checks"] if c["tabla"] == tabla and c not in antes["checks"]]
                if chk.get("columna"):
                    col = _resolver(chk["columna"], alias)
                    nuevos = [c for c in nuevos if col.lower() in c["expr"].lower()]
                ok = bool(nuevos)
                detalle = ("CHECK %s" % nuevos[0]["expr"]) if ok else "No encontramos una restricción CHECK nueva en «%s»." % tabla
            elif tipo == "columna_tipo":
                tabla = _resolver(chk["tabla"], alias)
                col = _resolver(chk["columna"], alias)
                info = despues["tablas"].get(tabla, {}).get(col)
                if not info:
                    detalle = "La columna %s.%s no existe." % (tabla, col)
                else:
                    ok = info["tipo"] in chk["tipos"]
                    if ok and chk.get("largo_min") and (info["largo"] or 0) < chk["largo_min"]:
                        ok = False
                    if ok and chk.get("tipo_completo"):
                        ok = info["tipo_completo"].lower().replace(" ", "") == chk["tipo_completo"].lower().replace(" ", "")
                    if ok and "nulo" in chk:
                        ok = info["nulo"] == chk["nulo"]
                    detalle = "%s.%s es %s%s" % (tabla, col, info["tipo_completo"].upper(), "" if info["nulo"] else " NOT NULL")
            elif tipo == "columna_no_existe":
                tabla = _resolver(chk["tabla"], alias)
                col = _resolver(chk["columna"], alias)
                ok = col not in despues["tablas"].get(tabla, {})
                detalle = "La columna %s.%s ya no existe" % (tabla, col) if ok else "La columna %s.%s sigue existiendo." % (tabla, col)
            elif tipo == "tabla_existe":
                tabla = _resolver(chk["tabla"], alias)
                ok = tabla in despues["tablas"]
                detalle = "Existe «%s»" % tabla if ok else "No existe la tabla «%s»." % tabla
            elif tipo == "tabla_no_existe":
                tabla = _resolver(chk["tabla"], alias)
                ok = tabla not in despues["tablas"]
                detalle = "«%s» fue eliminada" % tabla if ok else "La tabla «%s» sigue existiendo." % tabla
            elif tipo in ("debe_fallar", "debe_funcionar"):
                sql = _resolver(chk["sql"], alias)
                if re.search(r"\{[\w\.]+\}", sql):
                    detalle = "No se pudo probar porque falta la estructura previa."
                else:
                    cur.execute("START TRANSACTION")
                    try:
                        for s in sqlutil.separar_sentencias(sql):
                            cur.execute(s)
                        if tipo == "debe_funcionar":
                            ok = True
                            detalle = chk.get("ok_msg", "Funciona correctamente.")
                        else:
                            detalle = chk.get("fallo_msg", "La base aceptó un dato que debería rechazar.")
                    except pymysql.err.MySQLError as e:
                        codigo = e.args[0]
                        if tipo == "debe_fallar":
                            esperados = chk.get("errores")
                            ok = (not esperados) or codigo in esperados
                            detalle = ("Rechazado correctamente (error %s)." % codigo) if ok else \
                                "Se rechazó pero por otro motivo (error %s: %s)." % (codigo, e.args[1])
                        else:
                            detalle = "Debería funcionar pero dio error %s: %s" % (codigo, e.args[1])
                    finally:
                        cur.execute("ROLLBACK")
            elif tipo == "consulta":
                cur.execute(_resolver(chk["sql"].replace("'parcialito_scratch'", "'{scratch}'"), alias))
                fila = cur.fetchone()
                ok = bool(fila and fila[0])
                detalle = chk.get("ok_msg", "OK") if ok else chk.get("fallo_msg", "No se cumple.")
        except pymysql.err.MySQLError as e:
            detalle = "No se pudo verificar: %s" % (e.args[1] if len(e.args) > 1 else e)
        resultados.append({"desc": desc, "ok": ok, "detalle": detalle, "opcional": bool(chk.get("opcional"))})
    return resultados


def _tablas_afectadas(antes, despues):
    afect = []
    for t, cols in despues["tablas"].items():
        if t not in antes["tablas"] or antes["tablas"][t] != cols:
            afect.append(t)
    for coleccion in ("indices", "checks", "fks"):
        for item in despues[coleccion]:
            if item not in antes[coleccion] and item["tabla"] not in afect:
                afect.append(item["tabla"])
    return afect


def _ddl_en_scratch(ej, sql, permitidos):
    sentencias = preparar_sentencias(sql, permitidos)
    scratch = nuevo_scratch()
    try:
        preparar_scratch(ej, scratch)
    except Exception:
        borrar_scratch(scratch)
        raise
    conn, cur = _conexion(scratch)
    try:
        antes = _snapshot(cur, scratch)
        pasos = []
        error = None
        for i, s in enumerate(sentencias):
            try:
                pasos.append(para_ui(_ejecutar(cur, s, i), 100))
            except ErrorSQL as e:
                error = e
                break
        despues = _snapshot(cur, scratch)
        estructuras = {}
        for t in _tablas_afectadas(antes, despues):
            try:
                cur.execute("SHOW CREATE TABLE `%s`" % t)
                ddl = cur.fetchone()[1]
                ddl = re.sub(r"\s*ENGINE=.*$", "", ddl, flags=re.S)
                estructuras[t] = ddl
            except Exception:
                pass
        return conn, cur, antes, despues, pasos, error, estructuras, scratch
    except Exception:
        conn.close()
        borrar_scratch(scratch)
        raise


def ejecutar_ddl(ej, sql, opciones=None):
    conn, cur, antes, despues, pasos, error, estructuras, scratch = _ddl_en_scratch(ej, sql, {"ddl", "dml", "select"})
    conn.close()
    borrar_scratch(scratch)
    r = {"pasos": pasos, "estructuras": estructuras}
    if error:
        r["error"] = error.a_dict()
    return r


def corregir_ddl(ej, sql, opciones=None):
    conn, cur, antes, despues, pasos, error, estructuras, scratch = _ddl_en_scratch(ej, sql, {"ddl", "dml", "select"})
    try:
        if error:
            return {"ok": False, "motivo": "error", "error": error.a_dict(), "pasos": pasos, "estructuras": estructuras,
                    "mensajes": ["La sentencia %d dio error, así que no se pudo terminar de verificar." % (error.indice + 1)]}
        checks = _evaluar_checks(ej, cur, antes, despues, scratch)
        ok = all(c["ok"] for c in checks if not c["opcional"])
        mensajes = ["Se probó en un espacio temporal (tu base de práctica no se modificó)."]
        return {"ok": ok, "checks": checks, "pasos": pasos, "estructuras": estructuras, "mensajes": mensajes,
                "motivo": "ok" if ok else "checks"}
    finally:
        conn.close()
        borrar_scratch(scratch)


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------
def _select_de_vista(sql_create):
    """Devuelve el SELECT equivalente a un CREATE VIEW (respetando la cabecera de columnas)."""
    s = sqlutil.quitar_comentarios(sql_create).strip().rstrip(";")
    m = re.search(r"\bVIEW\s+[`\w\.]+\s*(\([^)]*\))?\s*AS\s+(.*)$", s, re.IGNORECASE | re.S)
    if not m:
        return None
    cuerpo = m.group(2)
    if m.group(1):
        return "SELECT * FROM (%s) AS __vista %s" % (cuerpo, m.group(1))
    return cuerpo


def _crear_vista_usuario(sql):
    """Crea la vista del usuario en un espacio temporal. Devuelve (scratch, nombre, pasos)."""
    from .setup_db import clonar_esquema
    sentencias = preparar_sentencias(sql, {"view", "select", "ddl"})
    if not any(sqlutil.tipo_sentencia(s) == "view" for s in sentencias):
        raise ValueError("Este ejercicio se resuelve con CREATE VIEW nombre AS SELECT ...")
    for s in sentencias:
        if sqlutil.tipo_sentencia(s) == "ddl" and not re.match(r"\s*DROP\s+VIEW", sqlutil.sin_strings(s), re.I):
            raise ValueError("Acá solo hace falta CREATE VIEW (podés usar DROP VIEW IF EXISTS antes).")
    scratch = nuevo_scratch()
    clonar_esquema(scratch, vistas_base=True)
    conn = None
    try:
        conn, cur = _conexion(scratch)
        pasos = [_ejecutar(cur, s, i) for i, s in enumerate(sentencias)]
        cur.execute("SELECT TABLE_NAME FROM information_schema.VIEWS WHERE TABLE_SCHEMA=%s", (scratch,))
        vistas = [r[0] for r in cur.fetchall() if r[0] not in db.TABLAS]
        nombre = None
        for s in reversed(sentencias):
            if sqlutil.tipo_sentencia(s) == "view":
                nombre = sqlutil.nombre_vista(s)
                break
        if nombre not in vistas:
            nombre = vistas[0] if vistas else None
        if not nombre:
            raise ValueError("No se creó ninguna vista.")
        return scratch, nombre, pasos
    except Exception:
        borrar_scratch(scratch)
        raise
    finally:
        if conn:
            conn.close()


def ejecutar_vista(ej, sql, opciones=None):
    scratch, nombre, pasos = _crear_vista_usuario(sql)
    try:
        conn, cur = _conexion(db.DB_SANDBOX)
        try:
            res = _correr_select_en_txn(cur, "SELECT * FROM `%s`.`%s`" % (scratch, nombre))
        finally:
            conn.close()
    finally:
        borrar_scratch(scratch)
    return {"vista": nombre, "resultado": para_ui(res),
            "mensajes": ["Vista «%s» creada en un espacio temporal. Esto es lo que devuelve SELECT * FROM %s:" % (nombre, nombre)]}


def corregir_vista(ej, sql, opciones=None):
    scratch, nombre, pasos = _crear_vista_usuario(sql)
    conn, cur = _conexion(db.DB_SANDBOX)
    try:
        consulta_usr = "SELECT * FROM `%s`.`%s`" % (scratch, nombre)
        pasadas = [("datos", "")]
        fx = _fixture_sql(ej)
        if fx:
            pasadas.append(("casos_borde", fx))
        resultado_ui = None
        for pasada, prep in pasadas:
            usr = _correr_select_en_txn(cur, consulta_usr, prep)
            if resultado_ui is None:
                resultado_ui = para_ui(usr)
            comparaciones, ok = [], None
            for titulo, q in _consultas_aceptadas(ej):
                sel = _select_de_vista(q) if sqlutil.tipo_sentencia(q) == "view" else q
                esp = _correr_select_en_txn(cur, sel, prep)
                c = comparar(esp["columnas"], esp["filas"], usr["columnas"], usr["filas"], ej.get("columnas"),
                             ej.get("ordenado", False), ej.get("orden"))
                comparaciones.append(c)
                if c["ok"]:
                    ok = (titulo, c)
                    break
            if not ok:
                fallo = dict(comparaciones[0])
                if pasada == "casos_borde":
                    fallo["mensajes"] = ["Con los datos originales tu vista da bien, pero falla cuando agregamos casos borde "
                                         "(por ejemplo comisiones sin inscriptos)."] + fallo["mensajes"]
                return {"ok": False, "resultado": resultado_ui, "vista": nombre, **fallo}
        aviso = _verificar_contiene(ej, sql)
        if aviso:
            return {"ok": False, "resultado": resultado_ui, "vista": nombre, "motivo": "requisito", "mensajes": [aviso]}
        titulo, c = ok
        mensajes = ["Tu vista «%s» devuelve lo esperado." % nombre] + c.get("mensajes", [])
        if titulo != "Solución" and any(v.get("titulo") == titulo for v in ej.get("variantes", []) or []):
            mensajes.insert(0, "Coincide con la interpretación: %s." % titulo)
        if fx:
            mensajes.append("Verificado con los datos reales y con casos borde.")
        return {"ok": True, "resultado": resultado_ui, "vista": nombre, "mensajes": mensajes}
    finally:
        conn.close()
        borrar_scratch(scratch)


# ---------------------------------------------------------------------------
# Puntos de entrada
# ---------------------------------------------------------------------------
def ejecutar_ejercicio(ej, sql, opciones=None):
    t = ej["tipo"]
    try:
        if t == "select":
            sentencias = preparar_sentencias(sql, {"select"})
            conn, cur = _conexion(db.DB_SANDBOX)
            try:
                res = None
                for s in sentencias:
                    res = _correr_select_en_txn(cur, s, limite=MAX_FILAS_CONSOLA) or res
                u = para_ui(res)
                if res and res.get("mas"):
                    u["mas"] = True
                return {"resultado": u}
            finally:
                conn.close()
        if t == "dml":
            return ejecutar_dml(ej, sql, opciones)
        if t == "ddl":
            return ejecutar_ddl(ej, sql, opciones)
        if t == "view":
            return ejecutar_vista(ej, sql, opciones)
    except ErrorSQL as e:
        return {"error": e.a_dict()}
    except ValueError as e:
        return {"error": {"titulo": "Revisá la consulta", "explicacion": str(e), "mensaje": "", "sugerencias": []}}
    raise ValueError("Tipo de ejercicio desconocido")


def corregir_ejercicio(ej, sql, opciones=None):
    t = ej["tipo"]
    try:
        if t == "select":
            return corregir_select(ej, sql, opciones)
        if t == "dml":
            return corregir_dml(ej, sql, opciones)
        if t == "ddl":
            return corregir_ddl(ej, sql, opciones)
        if t == "view":
            return corregir_vista(ej, sql, opciones)
    except ErrorSQL as e:
        return {"ok": False, "motivo": "error", "error": e.a_dict(), "mensajes": []}
    except ValueError as e:
        return {"ok": False, "motivo": "validacion",
                "error": {"titulo": "Revisá la consulta", "explicacion": str(e), "mensaje": "", "sugerencias": []},
                "mensajes": []}
    raise ValueError("Tipo de ejercicio desconocido")


def resultado_esperado(ej):
    """Resultado de la solución oficial (para el botón 'Ver resultado esperado')."""
    conn, cur = _conexion(db.DB_SANDBOX)
    try:
        if ej["tipo"] == "select":
            return {"resultado": para_ui(_correr_select_en_txn(cur, ej["solucion"]), 200)}
        if ej["tipo"] == "view":
            return {"resultado": para_ui(_correr_select_en_txn(cur, _select_de_vista(ej["solucion"])), 200)}
        if ej["tipo"] == "dml":
            verifs = _lista(ej.get("verificacion"))
            antes, despues, pasos = _correr_dml(cur, sqlutil.separar_sentencias(ej["solucion"]), ej.get("preparacion"), verifs)
            return {"pasos": [para_ui(p, 50) for p in pasos], "cambios": [_diff(a, d) for a, d in zip(antes, despues)]}
        return {}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Consola libre
# ---------------------------------------------------------------------------
def consola(sql, guardar=False, safe_updates=False, permitir_guardar=True):
    try:
        sentencias = preparar_sentencias(sql, {"select", "dml", "ddl", "view"})
    except ValueError as e:
        return {"resultados": [], "error": {"titulo": "No se puede ejecutar", "explicacion": str(e), "mensaje": "", "sugerencias": []}}
    hay_ddl = any(sqlutil.tipo_sentencia(s) in ("ddl", "view") for s in sentencias)
    if not permitir_guardar:
        guardar = False
        if hay_ddl:
            return {"resultados": [], "error": {
                "titulo": "En la versión online la consola no modifica la estructura",
                "explicacion": "La base de práctica es compartida por todos, así que la consola deshace todo al terminar. "
                               "Para practicar CREATE / ALTER / CREATE VIEW usá los ejercicios de Vistas y DDL "
                               "(se ejecutan en un espacio temporal propio).",
                "mensaje": "", "sugerencias": []}}
    if hay_ddl and not guardar:
        return {"resultados": [], "error": {
            "titulo": "CREATE / ALTER / DROP no se pueden deshacer",
            "explicacion": "Activá «Guardar cambios» para ejecutar sentencias de estructura. "
                           "Si rompés algo, después podés usar «Restaurar base».",
            "mensaje": "", "sugerencias": []}}
    conn, cur = _conexion(db.DB_SANDBOX, safe_updates)
    resultados = []
    error = None
    try:
        if not guardar:
            cur.execute("START TRANSACTION")
        for i, s in enumerate(sentencias):
            try:
                r = _ejecutar(cur, s, i, limite=MAX_FILAS_CONSOLA)
                u = para_ui(r, MAX_FILAS_CONSOLA)
                if r.get("mas"):
                    u["truncado"] = True
                    u["mas"] = True
                resultados.append(u)
            except ErrorSQL as e:
                error = e.a_dict()
                break
        if not guardar:
            cur.execute("ROLLBACK")
        if hay_ddl:
            invalidar_esquema()
    finally:
        conn.close()
    return {"resultados": resultados, "error": error, "deshecho": not guardar and any(r.get("tipo") == "ok" for r in resultados)}
