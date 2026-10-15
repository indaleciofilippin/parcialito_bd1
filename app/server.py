"""Servidor web de Parcialito BD.

Local:       .venv/bin/python -m app.server [--no-abrir]      (un solo usuario, sin login)
Producción:  gunicorn app.wsgi:app                             (multiusuario con login de Google)
"""
import collections
import datetime
import hashlib
import json
import logging
import os
import random
import secrets
import sys
import threading
import time
import traceback
import webbrowser
from contextlib import contextmanager

import pymysql
from flask import Flask, g, jsonify, request, send_from_directory, session
from werkzeug.exceptions import HTTPException

from . import db, grader, setup_db
from . import ejercicios as EJ
from .ejercicios import SECCIONES, GRUPOS
from .ejercicios.fixtures import DESCRIPCION as CASOS_BORDE_DESC

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app = Flask(__name__, static_folder=STATIC, static_url_path="/static")
app.json.ensure_ascii = False
app.json.sort_keys = False

_cfg = db.cargar_config()
MULTI = db.multiusuario()
app.secret_key = _cfg.get("secret_key") or hashlib.sha256(("parcialito-local-" + str(_cfg.get("password"))).encode()).hexdigest()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=MULTI and os.environ.get("RENDER") is not None,
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(days=30),
)

SECCION_GRUPO = {s["id"]: s.get("grupo", "parcialito") for s in SECCIONES}

# Límites (solo en modo multiusuario)
LIMITE_POR_MINUTO = 40
LIMITE_POR_DIA = 1500
CORRECCIONES_SIMULTANEAS = 6


# ---------------------------------------------------------------------------
# Utilidades de base de la app
# ---------------------------------------------------------------------------
def consulta_app(sql, params=None, uno=False):
    conn = db.conectar(db.DB_APP)
    try:
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql, params or ())
        return cur.fetchone() if uno else cur.fetchall()
    finally:
        conn.close()


def exec_app(sql, params=None):
    conn = db.conectar(db.DB_APP)
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        return cur.lastrowid
    finally:
        conn.close()


@app.errorhandler(pymysql.err.OperationalError)
def error_mysql(e):
    return jsonify({"error": "No me puedo conectar a MySQL: %s" % (e.args[1] if len(e.args) > 1 else e)}), 503


@app.errorhandler(Exception)
def error_general(e):
    if isinstance(e, HTTPException):
        return e
    traceback.print_exc()
    return jsonify({"error": "Error interno: %s" % e}), 500


# ---------------------------------------------------------------------------
# Autenticación (Google) y límites
# ---------------------------------------------------------------------------
PUBLICAS = {"/api/estado", "/api/login", "/api/logout"}
_cache_usuarios = {}
_lock_registro = threading.Lock()


def _usuario(uid):
    ahora = time.time()
    c = _cache_usuarios.get(uid)
    if c and ahora - c[1] < 60:
        return c[0]
    u = consulta_app("SELECT id, email, nombre, foto, es_admin FROM usuarios WHERE id=%s", (uid,), uno=True)
    _cache_usuarios[uid] = (u, ahora)
    return u


@app.before_request
def autenticar():
    if not request.path.startswith("/api/"):
        return None
    EJ.recargar_si_cambio()
    g.usuario = None
    if not MULTI and os.environ.get("RENDER"):
        # En internet nunca se abre sin login: falta configurar GOOGLE_CLIENT_ID en Render
        return jsonify({"error": "Falta configurar GOOGLE_CLIENT_ID en Render (Environment).", "configuracion": True}), 503
    if not MULTI:
        g.uid, g.admin = 1, True
        return None
    uid = session.get("uid")
    u = _usuario(uid) if uid else None
    if u:
        g.usuario, g.uid, g.admin = u, u["id"], bool(u["es_admin"])
        return None
    g.uid, g.admin = None, False
    if request.path not in PUBLICAS:
        return jsonify({"error": "Tenés que iniciar sesión.", "login": True}), 401
    return None


_actividad = collections.defaultdict(collections.deque)
_lock_actividad = threading.Lock()


def limitar(costo=1):
    """Devuelve una respuesta 429 si el usuario se pasó del límite; si no, None."""
    if not MULTI:
        return None
    ahora = time.time()
    with _lock_actividad:
        dq = _actividad[g.uid]
        while dq and ahora - dq[0] > 86400:
            dq.popleft()
        ultimo_minuto = sum(1 for t in dq if ahora - t < 60)
        if ultimo_minuto + costo > LIMITE_POR_MINUTO:
            return jsonify({"error": "Muchas consultas seguidas: esperá unos segundos y probá de nuevo.", "limite": True}), 429
        if len(dq) + costo > LIMITE_POR_DIA:
            return jsonify({"error": "Llegaste al límite de consultas por hoy. ¡Mañana seguís!", "limite": True}), 429
        for _ in range(costo):
            dq.append(ahora)
    return None


_semaforo = threading.BoundedSemaphore(CORRECCIONES_SIMULTANEAS)


@contextmanager
def ocupado():
    if not _semaforo.acquire(timeout=45):
        raise RuntimeError("El servidor está muy ocupado: probá de nuevo en unos segundos.")
    try:
        yield
    finally:
        _semaforo.release()


def requiere_admin():
    if MULTI and not g.admin:
        return jsonify({"error": "Solo la administradora puede hacer esto."}), 403
    return None


def cupo():
    total = consulta_app("SELECT COUNT(*) AS n FROM usuarios", uno=True)["n"]
    return {"usados": int(total), "max": _cfg["max_usuarios"]}


@app.route("/api/login", methods=["POST"])
def api_login():
    if not MULTI:
        return jsonify({"ok": True})
    cred = (request.json or {}).get("credential", "")
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as greq
        info = id_token.verify_oauth2_token(cred, greq.Request(), _cfg["google_client_id"])
    except Exception as e:
        return jsonify({"error": "No se pudo validar el inicio de sesión con Google (%s)." % e}), 401
    if not info.get("email_verified"):
        return jsonify({"error": "Tu cuenta de Google no tiene el mail verificado."}), 401
    return _registrar(info["sub"], info["email"].lower(), info.get("name"), info.get("picture"))


def _registrar(sub, email, nombre, foto):
    nombre = nombre or email.split("@")[0]
    with _lock_registro:
        u = consulta_app("SELECT id FROM usuarios WHERE google_sub=%s OR email=%s", (sub, email), uno=True)
        if u:
            exec_app("UPDATE usuarios SET google_sub=%s, nombre=%s, foto=%s, ultimo_acceso=NOW() WHERE id=%s",
                     (sub, nombre, foto, u["id"]))
            uid = u["id"]
        else:
            es_admin = email in _cfg["admin_emails"]
            registrados = {r["email"] for r in consulta_app("SELECT email FROM usuarios")}
            reservados = len([a for a in _cfg["admin_emails"] if a not in registrados and a != email])
            if not es_admin and len(registrados) + reservados >= _cfg["max_usuarios"]:
                return jsonify({"error": "Ya se completó el cupo de %d usuarios. Pedile a la administradora que te libere un lugar."
                                         % _cfg["max_usuarios"], "cupo": True}), 403
            uid = exec_app("""INSERT INTO usuarios (google_sub, email, nombre, foto, es_admin, ultimo_acceso)
                              VALUES (%s,%s,%s,%s,%s,NOW())""", (sub, email, nombre, foto, 1 if es_admin else 0))
    _cache_usuarios.pop(uid, None)
    session.clear()
    session.permanent = True
    session["uid"] = uid
    return jsonify({"ok": True, "usuario": _usuario(uid)})


# Login de prueba SOLO para testear en la compu (nunca en Render)
if os.environ.get("PARCIALITO_LOGIN_PRUEBA") == "1" and not os.environ.get("RENDER"):
    PUBLICAS.add("/api/login_prueba")

    @app.route("/api/login_prueba", methods=["POST"])
    def api_login_prueba():
        email = (request.json or {}).get("email", "").lower()
        return _registrar("prueba-" + email, email, email.split("@")[0].title(), None)


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    resp = send_from_directory(STATIC, "index.html")
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.after_request
def cabeceras(resp):
    if request.path.startswith("/static/js") or request.path.startswith("/static/css"):
        resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp


# ---------------------------------------------------------------------------
# Estado e instalación
# ---------------------------------------------------------------------------
@app.route("/api/estado")
def api_estado():
    base = {"multiusuario": MULTI, "google_client_id": _cfg.get("google_client_id") if MULTI else None,
            "usuario": g.usuario, "admin": bool(g.admin), "ejercicios": len(EJ.EJERCICIOS)}
    try:
        est = setup_db.estado()
        ok = est[db.DB_PRISTINA] and est[db.DB_SANDBOX] and est[db.DB_APP]
        base.update({"conectado": True, "listo": bool(ok), "puerto_mysql": _cfg["port"]})
        if MULTI and ok:
            base["cupo"] = cupo()
        if not MULTI or g.admin:
            base["detalle"] = est
        return jsonify(base)
    except pymysql.err.MySQLError as e:
        base.update({"conectado": False, "listo": False, "error": str(e.args[1] if len(e.args) > 1 else e)})
        return jsonify(base)


@app.route("/api/instalar", methods=["POST"])
def api_instalar():
    r = requiere_admin()
    if r:
        return r
    log = []
    setup_db.instalar(forzar=bool((request.json or {}).get("forzar")), log=log.append)
    grader.invalidar_esquema()
    return jsonify({"ok": True, "log": log})


@app.route("/api/restaurar", methods=["POST"])
def api_restaurar():
    r = requiere_admin()
    if r:
        return r
    t0 = time.time()
    setup_db.restaurar_sandbox(log=lambda *_: None)
    grader.invalidar_esquema()
    return jsonify({"ok": True, "segundos": round(time.time() - t0, 1)})


# ---------------------------------------------------------------------------
# Catálogo de ejercicios
# ---------------------------------------------------------------------------
def estados_ejercicios():
    filas = consulta_app("""SELECT ejercicio_id, COUNT(*) AS intentos, MAX(correcto) AS resuelto, MAX(fecha) AS ultimo
                            FROM intentos WHERE usuario_id=%s GROUP BY ejercicio_id""", (g.uid,))
    return {f["ejercicio_id"]: f for f in filas}


def marcados_usuario():
    return {f["ejercicio_id"] for f in consulta_app("SELECT ejercicio_id FROM marcados WHERE usuario_id=%s", (g.uid,))}


def resumen_ejercicio(e, estados=None, marcados=None):
    est = (estados or {}).get(e["id"], {})
    return {
        "id": e["id"], "seccion": e["seccion"], "grupo": SECCION_GRUPO.get(e["seccion"]), "titulo": e["titulo"],
        "dificultad": e["dificultad"], "tipo": e["tipo"], "origen": e.get("origen", ""), "tags": e.get("tags", []),
        "intentos": int(est.get("intentos") or 0), "resuelto": bool(est.get("resuelto")),
        "marcado": e["id"] in (marcados or set()),
    }


@app.route("/api/catalogo")
def api_catalogo():
    estados = estados_ejercicios()
    marcados = marcados_usuario()
    ejercicios = [resumen_ejercicio(e, estados, marcados) for e in EJ.EJERCICIOS]
    secciones = []
    for s in SECCIONES:
        de_s = [e for e in ejercicios if e["seccion"] == s["id"]]
        secciones.append(dict(s, total=len(de_s), resueltos=sum(e["resuelto"] for e in de_s),
                              intentados=sum(1 for e in de_s if e["intentos"])))
    return jsonify({"secciones": secciones, "grupos": GRUPOS, "ejercicios": ejercicios,
                    "casos_borde": CASOS_BORDE_DESC})


@app.route("/api/ejercicios/<eid>")
def api_ejercicio(eid):
    e = EJ.POR_ID.get(eid)
    if not e:
        return jsonify({"error": "No existe el ejercicio"}), 404
    estados = estados_ejercicios()
    marcados = marcados_usuario()
    borrador = consulta_app("SELECT sql_texto FROM borradores WHERE usuario_id=%s AND ejercicio_id=%s", (g.uid, eid), uno=True)
    vio = consulta_app("SELECT 1 AS v FROM vistos_solucion WHERE usuario_id=%s AND ejercicio_id=%s", (g.uid, eid), uno=True)
    intentos = consulta_app("""SELECT id, sql_texto, correcto, modo, fecha FROM intentos
                               WHERE usuario_id=%s AND ejercicio_id=%s ORDER BY id DESC LIMIT 20""", (g.uid, eid))
    for i in intentos:
        i["fecha"] = i["fecha"].isoformat(sep=" ")
    d = resumen_ejercicio(e, estados, marcados)
    d.update({
        "enunciado": e["enunciado"],
        "pistas": e.get("pistas", []),
        "borrador": borrador["sql_texto"] if borrador else "",
        "vio_solucion": bool(vio),
        "historial": intentos,
        "casos_borde": bool(e.get("casos_borde") or e.get("casos_borde_sql")),
        "tiene_preparacion": bool(e.get("preparacion")),
        "es_abierto": bool(e.get("condiciones")),
    })
    misma = [x for x in EJ.EJERCICIOS if x["seccion"] == e["seccion"]]
    idx = [x["id"] for x in misma].index(e["id"])
    d["anterior"] = misma[idx - 1]["id"] if idx > 0 else None
    d["siguiente"] = misma[idx + 1]["id"] if idx + 1 < len(misma) else None
    return jsonify(d)


@app.route("/api/ejercicios/<eid>/solucion")
def api_solucion(eid):
    e = EJ.POR_ID.get(eid)
    if not e:
        return jsonify({"error": "No existe"}), 404
    exec_app("INSERT IGNORE INTO vistos_solucion (usuario_id, ejercicio_id) VALUES (%s,%s)", (g.uid, eid))
    return jsonify({
        "solucion": e["solucion"],
        "alternativas": e.get("alternativas", []),
        "variantes": e.get("variantes", []),
        "explicacion": e.get("explicacion", ""),
        "errores_comunes": e.get("errores_comunes", []),
        "trampas": e.get("trampas", []),
    })


@app.route("/api/ejercicios/<eid>/esperado")
def api_esperado(eid):
    e = EJ.POR_ID.get(eid)
    if not e:
        return jsonify({"error": "No existe"}), 404
    r = limitar()
    if r:
        return r
    with ocupado():
        return jsonify(grader.resultado_esperado(e))


@app.route("/api/ejercicios/<eid>/ejecutar", methods=["POST"])
def api_ejecutar(eid):
    e = EJ.POR_ID.get(eid)
    if not e:
        return jsonify({"error": "No existe"}), 404
    r = limitar()
    if r:
        return r
    body = request.json or {}
    t0 = time.time()
    with ocupado():
        res = grader.ejecutar_ejercicio(e, body.get("sql", ""), {"safe_updates": body.get("safe_updates")})
    res["ms_total"] = round((time.time() - t0) * 1000)
    return jsonify(res)


@app.route("/api/ejercicios/<eid>/corregir", methods=["POST"])
def api_corregir(eid):
    e = EJ.POR_ID.get(eid)
    if not e:
        return jsonify({"error": "No existe"}), 404
    r = limitar()
    if r:
        return r
    body = request.json or {}
    sql = body.get("sql", "")
    t0 = time.time()
    with ocupado():
        res = grader.corregir_ejercicio(e, sql, {"safe_updates": body.get("safe_updates")})
    res["ms_total"] = round((time.time() - t0) * 1000)
    if sql.strip():
        exec_app("INSERT INTO intentos (usuario_id, ejercicio_id, sql_texto, correcto, modo) VALUES (%s,%s,%s,%s,'practica')",
                 (g.uid, eid, sql[:60000], 1 if res.get("ok") else 0))
    return jsonify(res)


@app.route("/api/borradores/<eid>", methods=["PUT"])
def api_borrador(eid):
    if eid not in EJ.POR_ID:
        return jsonify({"error": "No existe"}), 404
    sql = (request.json or {}).get("sql", "")[:60000]
    exec_app("""INSERT INTO borradores (usuario_id, ejercicio_id, sql_texto) VALUES (%s,%s,%s)
                ON DUPLICATE KEY UPDATE sql_texto=VALUES(sql_texto)""", (g.uid, eid, sql))
    return jsonify({"ok": True})


@app.route("/api/marcados/<eid>", methods=["POST"])
def api_marcar(eid):
    existe = consulta_app("SELECT 1 AS x FROM marcados WHERE usuario_id=%s AND ejercicio_id=%s", (g.uid, eid), uno=True)
    if existe:
        exec_app("DELETE FROM marcados WHERE usuario_id=%s AND ejercicio_id=%s", (g.uid, eid))
    else:
        exec_app("INSERT INTO marcados (usuario_id, ejercicio_id) VALUES (%s,%s)", (g.uid, eid))
    return jsonify({"marcado": not existe})


# ---------------------------------------------------------------------------
# Consola y esquema
# ---------------------------------------------------------------------------
@app.route("/api/consola", methods=["POST"])
def api_consola():
    r = limitar()
    if r:
        return r
    body = request.json or {}
    t0 = time.time()
    with ocupado():
        res = grader.consola(body.get("sql", ""), bool(body.get("guardar")), bool(body.get("safe_updates")),
                             permitir_guardar=not MULTI)
    res["ms_total"] = round((time.time() - t0) * 1000)
    return jsonify(res)


@app.route("/api/esquema")
def api_esquema():
    esq = grader.esquema(refrescar=request.args.get("refrescar") == "1" and (not MULTI or g.admin))
    return jsonify({
        "detalle": esq["detalle"], "fks": esq["fks"], "conteos": esq["conteos"], "tipos": esq["tipos"],
        "columnas": esq["columnas"],
    })


@app.route("/api/tabla/<nombre>")
def api_tabla(nombre):
    esq = grader.esquema()
    if nombre not in esq["columnas"]:
        return jsonify({"error": "No existe la tabla"}), 404
    conn = db.conectar(db.DB_SANDBOX)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM `%s` LIMIT 15" % nombre)
        cols = [d[0] for d in cur.description]
        filas = [[db.a_json(v) for v in f] for f in cur.fetchall()]
    finally:
        conn.close()
    return jsonify({"columnas": cols, "filas": filas})


# ---------------------------------------------------------------------------
# Progreso
# ---------------------------------------------------------------------------
@app.route("/api/progreso")
def api_progreso():
    estados = estados_ejercicios()
    por_seccion = []
    for s in SECCIONES:
        de_s = [e for e in EJ.EJERCICIOS if e["seccion"] == s["id"]]
        res = sum(1 for e in de_s if estados.get(e["id"], {}).get("resuelto"))
        intentos = sum(int(estados.get(e["id"], {}).get("intentos") or 0) for e in de_s)
        por_seccion.append({"id": s["id"], "nombre": s["nombre"], "corto": s["corto"], "grupo": s.get("grupo"),
                            "total": len(de_s), "resueltos": res, "intentos": intentos})
    dias = consulta_app("""SELECT DATE(fecha) AS dia, COUNT(*) AS intentos, SUM(correcto) AS correctos
                           FROM intentos WHERE usuario_id=%s GROUP BY DATE(fecha) ORDER BY dia DESC LIMIT 14""", (g.uid,))
    for d in dias:
        d["dia"] = d["dia"].isoformat()
        d["correctos"] = int(d["correctos"] or 0)
    recientes = consulta_app("""SELECT ejercicio_id, correcto, fecha, modo FROM intentos
                                WHERE usuario_id=%s ORDER BY id DESC LIMIT 15""", (g.uid,))
    for r in recientes:
        r["fecha"] = r["fecha"].isoformat(sep=" ")
        e = EJ.POR_ID.get(r["ejercicio_id"])
        r["titulo"] = e["titulo"] if e else r["ejercicio_id"]
        r["seccion"] = e["seccion"] if e else ""
    tot = consulta_app("SELECT COUNT(*) AS n, COALESCE(SUM(correcto),0) AS ok FROM intentos WHERE usuario_id=%s", (g.uid,), uno=True)
    simus = consulta_app("""SELECT id, inicio, fin, nota, duracion_min, JSON_LENGTH(ejercicios) AS n FROM simulacros
                            WHERE usuario_id=%s AND nota IS NOT NULL ORDER BY id DESC LIMIT 10""", (g.uid,))
    for s in simus:
        s["inicio"] = s["inicio"].isoformat(sep=" ")
        s["fin"] = s["fin"].isoformat(sep=" ") if s["fin"] else None
        s["nota"] = float(s["nota"]) if s["nota"] is not None else None
    return jsonify({"secciones": por_seccion, "dias": dias, "recientes": recientes,
                    "intentos_totales": int(tot["n"]), "intentos_correctos": int(tot["ok"]), "simulacros": simus})


@app.route("/api/progreso/reiniciar", methods=["POST"])
def api_reiniciar():
    for t in ("intentos", "borradores", "marcados", "vistos_solucion", "simulacros"):
        exec_app("DELETE FROM %s WHERE usuario_id=%%s" % t, (g.uid,))
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Administración (solo admin en modo multiusuario)
# ---------------------------------------------------------------------------
@app.route("/api/admin/usuarios")
def api_admin_usuarios():
    r = requiere_admin()
    if r:
        return r
    filas = consulta_app("""SELECT u.id, u.email, u.nombre, u.foto, u.es_admin, u.creado, u.ultimo_acceso,
                                   (SELECT COUNT(*) FROM intentos i WHERE i.usuario_id = u.id) AS intentos,
                                   (SELECT COUNT(DISTINCT ejercicio_id) FROM intentos i
                                     WHERE i.usuario_id = u.id AND i.correcto = 1) AS resueltos
                            FROM usuarios u ORDER BY u.creado""")
    for f in filas:
        f["creado"] = f["creado"].isoformat(sep=" ") if f["creado"] else None
        f["ultimo_acceso"] = f["ultimo_acceso"].isoformat(sep=" ") if f["ultimo_acceso"] else None
    return jsonify({"usuarios": filas, "cupo": cupo() if MULTI else None, "total_ejercicios": len(EJ.EJERCICIOS)})


@app.route("/api/admin/usuarios/<int:uid>", methods=["DELETE"])
def api_admin_borrar(uid):
    r = requiere_admin()
    if r:
        return r
    if uid == g.uid:
        return jsonify({"error": "No podés borrarte a vos misma."}), 400
    for t in ("intentos", "borradores", "marcados", "vistos_solucion", "simulacros"):
        exec_app("DELETE FROM %s WHERE usuario_id=%%s" % t, (uid,))
    exec_app("DELETE FROM usuarios WHERE id=%s", (uid,))
    _cache_usuarios.pop(uid, None)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Simulacro
# ---------------------------------------------------------------------------
PLANTILLAS = {
    "corto": {"nombre": "Parcialito corto", "minutos": 45,
              "slots": [["joins", "basicas"], ["agrupacion"], ["dominio"], ["subconsultas"], ["subconsultas", "vistas"]]},
    "completo": {"nombre": "Parcialito completo", "minutos": 80,
                 "slots": [["joins"], ["agrupacion"], ["dominio"], ["dominio"], ["subconsultas"], ["subconsultas"], ["vistas"], ["subconsultas", "agrupacion"]]},
    "extra": {"nombre": "Práctica DML + DDL", "minutos": 40,
              "slots": [["dml"], ["dml"], ["ddl"], ["ddl"]]},
}


@app.route("/api/simulacro", methods=["POST"])
def api_simulacro_crear():
    body = request.json or {}
    plantilla = PLANTILLAS.get(body.get("plantilla", "corto"), PLANTILLAS["corto"])
    minutos = int(body.get("minutos") or plantilla["minutos"])
    estados = estados_ejercicios()
    preferir_no_resueltos = body.get("no_resueltos", True)
    elegidos = []
    for slot in plantilla["slots"]:
        cands = [e for e in EJ.EJERCICIOS if e["seccion"] in slot and e["id"] not in elegidos]
        if not cands:
            continue

        def peso(e):
            w = {1: 1, 2: 3, 3: 3}[e["dificultad"]]
            if preferir_no_resueltos and not estados.get(e["id"], {}).get("resuelto"):
                w *= 3
            return w
        elegido = random.choices(cands, weights=[peso(e) for e in cands], k=1)[0]
        elegidos.append(elegido["id"])
    sid = exec_app("INSERT INTO simulacros (usuario_id, duracion_min, ejercicios) VALUES (%s,%s,%s)",
                   (g.uid, minutos, json.dumps(elegidos)))
    return jsonify({"id": sid, **_simulacro(sid)})


def _simulacro(sid):
    s = consulta_app("SELECT * FROM simulacros WHERE id=%s AND usuario_id=%s", (sid, g.uid), uno=True)
    if not s:
        return None
    ids = json.loads(s["ejercicios"])
    terminado = s["nota"] is not None
    ejercicios = []
    for eid in ids:
        e = EJ.POR_ID.get(eid)
        if not e:
            continue
        item = {"id": e["id"], "titulo": e["titulo"], "seccion": e["seccion"], "tipo": e["tipo"],
                "dificultad": e["dificultad"], "enunciado": e["enunciado"], "origen": e.get("origen", ""),
                "tiene_preparacion": bool(e.get("preparacion"))}
        if terminado:
            item["solucion"] = e["solucion"]
            item["explicacion"] = e.get("explicacion", "")
        ejercicios.append(item)
    ahora = consulta_app("SELECT NOW() AS n", uno=True)["n"]
    return {
        "id": s["id"], "inicio": s["inicio"].isoformat(sep=" "), "duracion_min": s["duracion_min"],
        "fin": s["fin"].isoformat(sep=" ") if s["fin"] else None,
        "ejercicios": ejercicios, "terminado": terminado,
        "respuestas": json.loads(s["respuestas"]) if s["respuestas"] else {},
        "resultado": json.loads(s["resultado"]) if s["resultado"] else None,
        "nota": float(s["nota"]) if s["nota"] is not None else None,
        "segundos_transcurridos": int((ahora - s["inicio"]).total_seconds()),
    }


@app.route("/api/simulacro/<int:sid>")
def api_simulacro(sid):
    s = _simulacro(sid)
    if not s:
        return jsonify({"error": "No existe"}), 404
    return jsonify(s)


@app.route("/api/simulacro/<int:sid>/respuestas", methods=["PUT"])
def api_simulacro_guardar(sid):
    respuestas = (request.json or {}).get("respuestas", {})
    exec_app("UPDATE simulacros SET respuestas=%s WHERE id=%s AND usuario_id=%s AND nota IS NULL",
             (json.dumps(respuestas)[:200000], sid, g.uid))
    return jsonify({"ok": True})


@app.route("/api/simulacro/<int:sid>/entregar", methods=["POST"])
def api_simulacro_entregar(sid):
    s = consulta_app("SELECT * FROM simulacros WHERE id=%s AND usuario_id=%s", (sid, g.uid), uno=True)
    if not s:
        return jsonify({"error": "No existe"}), 404
    if s["nota"] is not None:
        return jsonify(_simulacro(sid))
    respuestas = (request.json or {}).get("respuestas", {})
    ids = json.loads(s["ejercicios"])
    r = limitar(costo=1)
    if r:
        return r
    resultado = {}
    correctos = 0
    for eid in ids:
        e = EJ.POR_ID.get(eid)
        sql = (respuestas.get(eid) or "").strip()
        if not sql or not e:
            resultado[eid] = {"ok": False, "vacio": True, "mensajes": ["Sin responder."]}
            continue
        with ocupado():
            res = grader.corregir_ejercicio(e, sql)
        for k in ("resultado", "pasos", "cambios", "estructuras"):
            res.pop(k, None)
        resultado[eid] = res
        if res.get("ok"):
            correctos += 1
        exec_app("INSERT INTO intentos (usuario_id, ejercicio_id, sql_texto, correcto, modo) VALUES (%s,%s,%s,%s,'simulacro')",
                 (g.uid, eid, sql[:60000], 1 if res.get("ok") else 0))
    nota = round(10.0 * correctos / max(1, len(ids)), 2)
    exec_app("UPDATE simulacros SET respuestas=%s, resultado=%s, nota=%s, fin=NOW() WHERE id=%s AND usuario_id=%s",
             (json.dumps(respuestas), json.dumps(resultado, default=str), nota, sid, g.uid))
    return jsonify(_simulacro(sid))


@app.route("/api/simulacros")
def api_simulacros():
    filas = consulta_app("""SELECT id, inicio, nota, duracion_min, JSON_LENGTH(ejercicios) AS n FROM simulacros
                            WHERE usuario_id=%s ORDER BY id DESC LIMIT 20""", (g.uid,))
    for f in filas:
        f["inicio"] = f["inicio"].isoformat(sep=" ")
        f["nota"] = float(f["nota"]) if f["nota"] is not None else None
    return jsonify(filas)


@app.errorhandler(RuntimeError)
def error_ocupado(e):
    return jsonify({"error": str(e)}), 503


# ---------------------------------------------------------------------------
def inicializar(log=print):
    """Prepara las bases (importa el dump si hace falta) y el usuario restringido."""
    setup_db.instalar(log=lambda m: log("  " + m))
    setup_db.asegurar_runner(log=log)
    grader.limpiar_scratch_viejos()


def main():
    puerto = int(os.environ.get("PARCIALITO_PORT", _cfg.get("app_port", 5050)))
    try:
        inicializar()
    except pymysql.err.MySQLError as e:
        print("\n  ⚠  No pude conectar/preparar MySQL: %s" % (e.args[1] if len(e.args) > 1 else e))
        print("     La app abre igual y te muestra cómo solucionarlo.\n")
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    url = "http://127.0.0.1:%d" % puerto
    print("\n  Parcialito BD listo en %s  (Ctrl+C para cerrar)\n" % url)
    if "--no-abrir" not in sys.argv:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=puerto, threaded=True, debug=False)


if __name__ == "__main__":
    main()
