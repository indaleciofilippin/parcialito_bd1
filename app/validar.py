"""Valida el banco de ejercicios contra la base real.

Uso:
  python -m app.validar                 # todos
  python -m app.validar dml ddl         # por sección
  python -m app.validar sub-02          # por id (o prefijo de id)
  python -m app.validar -v sub-02       # muestra detalles

Comprueba, para cada ejercicio:
  * que la solución se ejecute y que el corrector la acepte
  * que cada alternativa también sea aceptada (y dé el mismo resultado)
  * que cada "trampa" (consulta incorrecta típica) sea RECHAZADA
  * que el resultado no sea trivial (0 filas sin casos borde, DML que no cambia nada, etc.)
"""
import sys
import time
import json

from . import grader, db, sqlutil
from .ejercicios import EJERCICIOS, SECCIONES


def _r(texto, color):
    codigos = {"rojo": "31", "verde": "32", "amarillo": "33", "gris": "90", "azul": "34"}
    return "\033[%sm%s\033[0m" % (codigos[color], texto)


def validar(ej, verbose=False):
    problemas, avisos, info = [], [], []
    t0 = time.time()
    tipo = ej["tipo"]

    for campo in ("pistas", "explicacion"):
        if not ej.get(campo):
            avisos.append("falta '%s'" % campo)
    if ej.get("dificultad") not in (1, 2, 3):
        problemas.append("dificultad debe ser 1, 2 o 3")

    # 1) la solución debe ser aceptada
    r = grader.corregir_ejercicio(ej, ej["solucion"])
    if not r.get("ok"):
        problemas.append("la SOLUCIÓN no es aceptada: %s %s" % (
            r.get("error", {}).get("mensaje", "") if r.get("error") else "",
            " | ".join(r.get("mensajes", [])) or json.dumps(r.get("checks", ""), ensure_ascii=False)[:400]))
    else:
        if tipo in ("select", "view"):
            res = r.get("resultado") or {}
            info.append("%s filas" % res.get("total"))
            if res.get("total") == 0 and not ej.get("casos_borde") and not ej.get("casos_borde_sql"):
                avisos.append("la solución devuelve 0 filas con los datos reales y no hay casos borde")
        if tipo == "dml":
            cambios = r.get("cambios", [])
            n = sum(c["n_nuevas"] + c["n_quitadas"] + c.get("n_modificadas", 0) for c in cambios)
            info.append("cambios=%d" % n)
            if n == 0:
                problemas.append("la solución DML no produce cambios visibles en la verificación")
            # no hacer nada debe fallar
            vacio = grader.corregir_ejercicio(ej, "SELECT 1")
            if vacio.get("ok"):
                problemas.append("una respuesta vacía (SELECT 1) es aceptada")
        if tipo == "ddl":
            vacio = grader.corregir_ejercicio(ej, "SELECT 1")
            if vacio.get("ok"):
                problemas.append("una respuesta vacía (SELECT 1) es aceptada")
            info.append("%d checks" % len(r.get("checks", [])))

    # 2) alternativas
    for a in ej.get("alternativas", []) or []:
        ra = grader.corregir_ejercicio(ej, a["sql"])
        if not ra.get("ok"):
            problemas.append("alternativa '%s' NO es aceptada: %s %s" % (
                a.get("titulo"), (ra.get("error") or {}).get("mensaje", ""), " | ".join(ra.get("mensajes", []))))
        elif tipo == "select":
            # debe dar exactamente lo mismo que la solución (si no, es una 'variante')
            sub = dict(ej)
            sub["alternativas"], sub["variantes"] = [], []
            rs = grader.corregir_ejercicio(sub, a["sql"])
            if not rs.get("ok"):
                avisos.append("alternativa '%s' solo coincide con una variante, no con la solución" % a.get("titulo"))

    # 3) variantes (interpretaciones distintas aceptadas)
    for v in ej.get("variantes", []) or []:
        rv = grader.corregir_ejercicio(ej, v["sql"])
        if not rv.get("ok"):
            problemas.append("variante '%s' NO es aceptada: %s" % (v.get("titulo"), " | ".join(rv.get("mensajes", []))))

    # 4) trampas: deben ser rechazadas
    for t in ej.get("trampas", []) or []:
        rt = grader.corregir_ejercicio(ej, t["sql"])
        if rt.get("ok"):
            problemas.append("la trampa '%s' es ACEPTADA (debería fallar)" % t.get("titulo", t["sql"][:40]))
        elif verbose:
            info.append("trampa rechazada: " + (" | ".join(rt.get("mensajes", [])) or (rt.get("error") or {}).get("titulo", ""))[:120])

    # 5) columnas declaradas
    if tipo in ("select", "view") and ej.get("columnas") and r.get("ok"):
        pass

    ms = (time.time() - t0) * 1000
    if ms > 4000:
        avisos.append("lento: %.0f ms" % ms)
    return problemas, avisos, info, ms


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    verbose = "-v" in sys.argv
    secciones = {s["id"] for s in SECCIONES}
    lista = EJERCICIOS
    if args:
        lista = [e for e in EJERCICIOS if e["seccion"] in args or any(e["id"].startswith(a) for a in args)]
    total_p = 0
    por_seccion = {}
    for e in lista:
        try:
            p, a, i, ms = validar(e, verbose)
        except Exception as ex:  # error inesperado del motor
            p, a, i, ms = ["EXCEPCIÓN: %r" % ex], [], [], 0
        total_p += len(p)
        por_seccion.setdefault(e["seccion"], 0)
        por_seccion[e["seccion"]] += 1
        estado = _r("OK  ", "verde") if not p else _r("FALLA", "rojo")
        print("%s %-10s %-48s %s %s" % (estado, e["id"], e["titulo"][:48], _r("(%s)" % ", ".join(i), "gris"), _r("%.0fms" % ms, "gris")))
        for x in p:
            print("      " + _r("✗ " + x, "rojo"))
        for x in a:
            print("      " + _r("! " + x, "amarillo"))
    print()
    print("Ejercicios: %d  |  por sección: %s" % (len(lista), ", ".join("%s=%d" % kv for kv in por_seccion.items())))
    print(_r("Sin problemas.", "verde") if total_p == 0 else _r("%d problema(s)." % total_p, "rojo"))
    sys.exit(1 if total_p else 0)


if __name__ == "__main__":
    main()
