"""Punto de entrada para producción (Render):
    gunicorn app.wsgi:app --workers 1 --threads 8 --timeout 180 --bind 0.0.0.0:$PORT

La primera vez importa los datos en la base (puede tardar ~1 minuto); se hace en segundo plano
para que el servidor responda enseguida mientras tanto.
"""
import threading
import traceback

from .server import app, inicializar


def _inicializar():
    try:
        inicializar()
        print("  Parcialito BD: base lista.", flush=True)
    except Exception:
        print("  Parcialito BD: ERROR preparando la base de datos:", flush=True)
        traceback.print_exc()


threading.Thread(target=_inicializar, daemon=True).start()
