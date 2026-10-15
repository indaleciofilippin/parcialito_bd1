"""Banco de ejercicios del parcialito.

Cada módulo define una lista EJERCICIOS. Ver .dev/FORMATO_EJERCICIOS.md para el formato.
"""
import importlib

SECCIONES = [
    {"id": "basicas", "grupo": "parcialito", "nombre": "Consultas básicas", "corto": "Básicas",
     "descripcion": "SELECT, WHERE, ORDER BY, LIKE, BETWEEN, IN, DISTINCT y LIMIT sobre una sola tabla.",
     "icono": "filter", "origen": "TP1 · Parte A"},
    {"id": "joins", "grupo": "parcialito", "nombre": "Consultas con varias tablas", "corto": "JOINs",
     "descripcion": "INNER JOIN, LEFT JOIN y auto-JOIN siguiendo las claves foráneas del modelo.",
     "icono": "link", "origen": "TP1 · Parte B"},
    {"id": "agrupacion", "grupo": "parcialito", "nombre": "Agrupación", "corto": "GROUP BY",
     "descripcion": "COUNT, SUM, AVG, MIN, MAX con GROUP BY y filtros de grupo con HAVING.",
     "icono": "layers", "origen": "TP1 · Parte C"},
    {"id": "dominio", "grupo": "parcialito", "nombre": "Problemáticas de dominio", "corto": "Dominio",
     "descripcion": "Pedidos «de la vida real» del área académica: traducir el problema a una consulta con umbrales.",
     "icono": "briefcase", "origen": "TP1 · Sección 2"},
    {"id": "subconsultas", "grupo": "parcialito", "nombre": "Subconsultas y ausencia/presencia", "corto": "Subconsultas",
     "descripcion": "IN / NOT IN, EXISTS / NOT EXISTS, LEFT JOIN … IS NULL y comparaciones contra promedios.",
     "icono": "search", "origen": "Semana 10 · Sección 1"},
    {"id": "vistas", "grupo": "parcialito", "nombre": "Vistas", "corto": "Vistas",
     "descripcion": "CREATE VIEW para simplificar consultas y reutilizarlas.",
     "icono": "eye", "origen": "Semana 10 · Sección 2"},
    {"id": "dml", "grupo": "extra", "nombre": "DML: INSERT, UPDATE, DELETE", "corto": "DML",
     "descripcion": "Registrar, modificar y eliminar datos respetando las claves foráneas.",
     "icono": "edit", "origen": "Semana 10 · Sección 3"},
    {"id": "ddl", "grupo": "extra", "nombre": "DDL: CREATE y ALTER", "corto": "DDL",
     "descripcion": "Crear tablas, agregar columnas y restricciones (PK, FK, UNIQUE, CHECK).",
     "icono": "database", "origen": "Semana 10 · Sección 4"},
]

GRUPOS = [
    {"id": "parcialito", "nombre": "Para el parcialito", "descripcion": "Lo que entra: consultas SELECT, subconsultas y vistas."},
    {"id": "extra", "nombre": "Práctica extra", "descripcion": "No entra en el parcialito: DML y DDL para practicar aparte."},
]

MODULOS = ["basicas", "joins", "agrupacion", "dominio", "subconsultas", "vistas", "dml", "ddl"]

CAMPOS_OBLIGATORIOS = ["id", "seccion", "titulo", "enunciado", "tipo", "solucion", "dificultad"]
TIPOS = {"select", "dml", "ddl", "view"}


def cargar():
    ejercicios = []
    for m in MODULOS:
        try:
            mod = importlib.import_module("." + m, __name__)
        except ModuleNotFoundError as e:
            if e.name and e.name.endswith("." + m):
                continue
            raise
        for i, e in enumerate(getattr(mod, "EJERCICIOS", [])):
            e = dict(e)
            e.setdefault("seccion", m)
            e["pos"] = i
            ejercicios.append(e)
    ids = set()
    secciones = {s["id"] for s in SECCIONES}
    for e in ejercicios:
        for c in CAMPOS_OBLIGATORIOS:
            if c not in e:
                raise ValueError("Ejercicio %s: falta el campo %s" % (e.get("id"), c))
        if e["id"] in ids:
            raise ValueError("Id repetido: %s" % e["id"])
        if e["tipo"] not in TIPOS:
            raise ValueError("Ejercicio %s: tipo inválido %s" % (e["id"], e["tipo"]))
        if e["seccion"] not in secciones:
            raise ValueError("Ejercicio %s: sección inválida %s" % (e["id"], e["seccion"]))
        ids.add(e["id"])
    return ejercicios


EJERCICIOS = cargar()
POR_ID = {e["id"]: e for e in EJERCICIOS}


# ---------------------------------------------------------------------------
# Recarga en caliente: si se edita un archivo de ejercicios, se recarga solo.
# ---------------------------------------------------------------------------
import os as _os
import sys as _sys

_DIR = _os.path.dirname(_os.path.abspath(__file__))


def _firma():
    return max(_os.path.getmtime(_os.path.join(_DIR, f)) for f in _os.listdir(_DIR) if f.endswith(".py"))


_FIRMA = _firma()


def recargar_si_cambio():
    global EJERCICIOS, POR_ID, _FIRMA
    try:
        f = _firma()
        if f == _FIRMA:
            return False
        for m in MODULOS + ["fixtures"]:
            nombre = __name__ + "." + m
            if nombre in _sys.modules:
                importlib.reload(_sys.modules[nombre])
        nuevos = cargar()
        EJERCICIOS, POR_ID, _FIRMA = nuevos, {e["id"]: e for e in nuevos}, f
        print("  (banco de ejercicios recargado: %d ejercicios)" % len(nuevos))
        return True
    except Exception as e:  # archivo a medio escribir: se reintenta en el próximo pedido
        print("  (no se pudo recargar el banco de ejercicios: %s)" % e)
        return False
