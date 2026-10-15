"""Conexión a MySQL y utilidades comunes.

Configuración:
  - Local: config.json (lo genera app/configurar.py).
  - Producción (Render): variables de entorno.
      DATABASE_URL      mysql://usuario:clave@host:puerto/db?ssl-mode=REQUIRED  (la "Service URI" de Aiven)
      DB_CA_PEM         (opcional) certificado CA de Aiven, para verificar el servidor
      GOOGLE_CLIENT_ID  activa el modo multiusuario con login de Google
      SECRET_KEY        clave para firmar las sesiones
      MAX_USUARIOS      cupo de cuentas (por defecto 20)
      ADMIN_EMAILS      mails de administradores separados por coma
"""
import datetime
import decimal
import hashlib
import hmac
import json
import os
import queue
import tempfile
import threading
from urllib.parse import urlparse, unquote, parse_qs

import pymysql
import pymysql.cursors

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(RAIZ, "config.json")

# Bases que usa la app (todas con prefijo parcialito_)
DB_PRISTINA = "parcialito_uni"        # copia intacta del dump (fuente para restaurar)
DB_SANDBOX = "parcialito_sandbox"     # donde corren tus consultas
DB_SCRATCH = "parcialito_scratch"     # espacio temporal para CREATE / ALTER / VIEW
DB_APP = "parcialito_app"             # usuarios, progreso, intentos, simulacros

TABLAS = [
    "departamentos", "aulas", "carreras", "docentes", "asignaturas", "alumnos",
    "alumno_carrera", "correlatividades", "docente_asignatura", "comisiones",
    "inscripcion_alumno_comision", "asistencias", "examenes", "notas",
    "mesas_finales", "inscripciones_finales",
]
TABLAS_CHICAS = ["departamentos", "aulas", "carreras", "docentes", "asignaturas", "alumnos", "comisiones"]

USUARIO_RUNNER = "parcialito_run"     # usuario restringido que crea la app en producción

_CFG = None
_CFG_LOCK = threading.Lock()


def _cfg_desde_url(url):
    u = urlparse(url)
    q = parse_qs(u.query)
    modo_ssl = (q.get("ssl-mode") or q.get("sslmode") or [""])[0].upper()
    return {
        "host": u.hostname or "127.0.0.1",
        "port": u.port or 3306,
        "user": unquote(u.username or ""),
        "password": unquote(u.password or ""),
        "ssl": modo_ssl in ("REQUIRED", "VERIFY_CA", "VERIFY_IDENTITY", "REQUIRE") or "aivencloud.com" in (u.hostname or ""),
    }


def cargar_config():
    global _CFG
    if _CFG is not None:
        return _CFG
    with _CFG_LOCK:
        if _CFG is not None:
            return _CFG
        cfg = {"host": "127.0.0.1", "port": 3306, "user": "parcialito", "password": "", "app_port": 5050, "ssl": False}
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                cfg.update(json.load(f))
        if os.environ.get("DATABASE_URL"):
            cfg.update(_cfg_desde_url(os.environ["DATABASE_URL"]))
        if os.environ.get("PARCIALITO_DB_PORT"):
            cfg["port"] = int(os.environ["PARCIALITO_DB_PORT"])
        for clave, env in (("google_client_id", "GOOGLE_CLIENT_ID"), ("secret_key", "SECRET_KEY"),
                           ("max_usuarios", "MAX_USUARIOS"), ("admin_emails", "ADMIN_EMAILS")):
            if os.environ.get(env):
                cfg[clave] = os.environ[env]
        cfg["max_usuarios"] = int(cfg.get("max_usuarios") or 20)
        admins = cfg.get("admin_emails") or "indafilippin@gmail.com"
        if isinstance(admins, str):
            admins = [a.strip().lower() for a in admins.split(",") if a.strip()]
        cfg["admin_emails"] = admins
        if os.environ.get("DB_CA_PEM"):
            ruta = os.path.join(tempfile.gettempdir(), "parcialito_ca.pem")
            with open(ruta, "w") as f:
                f.write(os.environ["DB_CA_PEM"])
            cfg["ssl_ca"] = ruta
        _CFG = cfg
        return cfg


def multiusuario():
    return bool(cargar_config().get("google_client_id"))


def _ssl_args(cfg):
    if not cfg.get("ssl"):
        return {}
    if cfg.get("ssl_ca"):
        return {"ssl": {"ca": cfg["ssl_ca"], "check_hostname": True}}
    return {"ssl": {"check_hostname": False}}   # cifrado sin verificar certificado (como ssl-mode=REQUIRED)


# ---------------------------------------------------------------------------
# Credenciales: admin (config) y runner (restringido, solo producción)
# ---------------------------------------------------------------------------
_RUNNER_OK = None


def clave_runner():
    cfg = cargar_config()
    base = (cfg.get("secret_key") or cfg.get("password") or "parcialito").encode()
    return "Pr_" + hmac.new(base, b"runner-mysql", hashlib.sha256).hexdigest()[:28] + "9!"


def usar_runner(valor):
    global _RUNNER_OK
    _RUNNER_OK = bool(valor)


def _credenciales(admin):
    cfg = cargar_config()
    if not admin and _RUNNER_OK:
        return USUARIO_RUNNER, clave_runner()
    return cfg["user"], cfg["password"]


class _ConexionPool(pymysql.connections.Connection):
    """Conexión que al cerrarse vuelve al pool (si está sana)."""
    _clave_pool = None

    def close(self):
        clave = self._clave_pool
        if clave and self.open:
            try:
                self.rollback()   # por si quedó una transacción abierta
                cola = _POOLS.setdefault(clave, queue.LifoQueue(maxsize=10))
                cola.put_nowait(self)
                return
            except Exception:
                pass
        try:
            super().close()
        except Exception:
            pass


_POOLS = {}


def conectar(database=None, autocommit=True, admin=False):
    """Conexión a MySQL. Reutiliza conexiones (pool) para las bases fijas de la app."""
    cfg = cargar_config()
    user, password = _credenciales(admin)
    usa_pool = database in (DB_SANDBOX, DB_APP) and autocommit
    clave = (database, user) if usa_pool else None
    if clave:
        cola = _POOLS.get(clave)
        while cola is not None:
            try:
                conn = cola.get_nowait()
            except queue.Empty:
                break
            try:
                conn.ping(reconnect=True)
                if database:
                    conn.select_db(database)
                return conn
            except Exception:
                try:
                    pymysql.connections.Connection.close(conn)
                except Exception:
                    pass
    conn = _ConexionPool(
        host=cfg["host"],
        port=int(cfg["port"]),
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        autocommit=autocommit,
        cursorclass=pymysql.cursors.Cursor,
        connect_timeout=10,
        read_timeout=90,
        write_timeout=90,
        local_infile=False,
        **_ssl_args(cfg)
    )
    conn._clave_pool = clave
    return conn


def a_json(v):
    """Convierte un valor de MySQL en algo serializable y legible."""
    if v is None:
        return None
    if isinstance(v, decimal.Decimal):
        if v == v.to_integral_value() and abs(v) < 10**15 and v.as_tuple().exponent >= 0:
            return int(v)
        return float(v)
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
            return v.decode("utf-8")
        except Exception:
            return v.hex()
    if isinstance(v, set):
        return ",".join(sorted(v))
    return v
