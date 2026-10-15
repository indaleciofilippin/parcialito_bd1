"""Configuración inicial: genera config.json y el script para crear el usuario de MySQL.

  python -m app.configurar           crea config.json (si no existe) y setup/crear_usuario.sql
  python -m app.configurar --probar  sale con código 0 si la app ya se conecta a MySQL
"""
import json
import os
import secrets
import sys

from . import db

SQL_USUARIO = """-- Crea un usuario de MySQL exclusivo para la app Parcialito BD.
-- Solo tiene permisos sobre las bases parcialito_* (no toca tu base 'universidad').
CREATE USER IF NOT EXISTS 'parcialito'@'localhost' IDENTIFIED BY '{pw}';
CREATE USER IF NOT EXISTS 'parcialito'@'127.0.0.1' IDENTIFIED BY '{pw}';
ALTER USER 'parcialito'@'localhost' IDENTIFIED BY '{pw}';
ALTER USER 'parcialito'@'127.0.0.1' IDENTIFIED BY '{pw}';
GRANT ALL PRIVILEGES ON `parcialito\\_%`.* TO 'parcialito'@'localhost';
GRANT ALL PRIVILEGES ON `parcialito\\_%`.* TO 'parcialito'@'127.0.0.1';
FLUSH PRIVILEGES;
SELECT 'Usuario parcialito creado OK' AS resultado;
"""


def crear_config():
    if not os.path.exists(db.CONFIG_PATH):
        pw = "Parc_" + secrets.token_urlsafe(14).replace("-", "x").replace("_", "y") + "9!"
        cfg = {"host": "127.0.0.1", "port": 3306, "user": "parcialito", "password": pw, "app_port": 5050}
        with open(db.CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
        os.chmod(db.CONFIG_PATH, 0o600)
    cfg = db.cargar_config()
    ruta = os.path.join(db.RAIZ, "setup", "crear_usuario.sql")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w") as f:
        f.write(SQL_USUARIO.format(pw=cfg["password"]))
    os.chmod(ruta, 0o600)


def probar():
    try:
        conn = db.conectar()
        conn.close()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    if "--probar" in sys.argv:
        sys.exit(0 if probar() else 1)
    crear_config()
