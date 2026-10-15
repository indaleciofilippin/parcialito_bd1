"""Punto de entrada para producción (Render): gunicorn app.wsgi:app"""
from .server import app, inicializar

inicializar()
