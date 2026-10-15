"""Crea/restaura las bases de la app a partir del dump BD-Universidad.sql.

Uso:  python -m app.setup_db            (instala si hace falta)
      python -m app.setup_db --forzar   (reimporta todo desde cero)
"""
import os
import sys
import time

from . import db

DUMP_CANDIDATOS = [
    os.path.join(db.RAIZ, "BD-Universidad.sql"),
    os.path.join(db.RAIZ, "material", "BD-Universidad.sql"),
]

# Vistas que la cátedra suele dar "ya creadas" para ejercicios de uso de vistas.
VISTAS_PRECARGADAS = {
    "vw_alumnos_carreras": """
        SELECT a.id_alumno, a.nombre, a.apellido, a.dni, c.id_carrera,
               c.nombre AS carrera, ac.estado AS estado_carrera, ac.fecha_inscripcion
        FROM alumnos a
        JOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno
        JOIN carreras c ON c.id_carrera = ac.id_carrera""",
    "vw_comisiones_docentes": """
        SELECT co.id_comision, co.anio, co.cuatrimestre, co.tipo, co.cupo,
               asg.id_asignatura, asg.nombre AS asignatura,
               d.id_docente, d.nombre AS nombre_docente, d.apellido AS apellido_docente,
               au.id_aula, au.nombre AS aula
        FROM comisiones co
        JOIN asignaturas asg ON asg.id_asignatura = co.id_asignatura
        JOIN docentes d ON d.id_docente = co.id_docente
        JOIN aulas au ON au.id_aula = co.id_aula""",
    "vw_inscriptos_por_comision": """
        SELECT co.id_comision, asg.nombre AS asignatura, co.anio, co.cuatrimestre, co.cupo,
               COUNT(i.id_inscripcion) AS cantidad_inscriptos
        FROM comisiones co
        JOIN asignaturas asg ON asg.id_asignatura = co.id_asignatura
        LEFT JOIN inscripcion_alumno_comision i ON i.id_comision = co.id_comision
        GROUP BY co.id_comision, asg.nombre, co.anio, co.cuatrimestre, co.cupo""",
    "vw_notas_por_asignatura": """
        SELECT asg.id_asignatura, asg.nombre AS asignatura,
               COUNT(n.id_nota) AS cantidad_notas,
               ROUND(AVG(n.nota), 2) AS promedio,
               SUM(n.nota < 4) AS desaprobados
        FROM asignaturas asg
        JOIN comisiones co ON co.id_asignatura = asg.id_asignatura
        JOIN examenes e ON e.id_comision = co.id_comision
        JOIN notas n ON n.id_examen = e.id_examen
        GROUP BY asg.id_asignatura, asg.nombre""",
}

TABLAS_APP = [
    """CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        google_sub VARCHAR(64) NULL UNIQUE,
        email VARCHAR(190) NOT NULL UNIQUE,
        nombre VARCHAR(190) NULL,
        foto VARCHAR(500) NULL,
        es_admin TINYINT(1) NOT NULL DEFAULT 0,
        creado DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ultimo_acceso DATETIME NULL
    )""",
    """CREATE TABLE IF NOT EXISTS intentos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id INT NOT NULL DEFAULT 1,
        ejercicio_id VARCHAR(40) NOT NULL,
        sql_texto MEDIUMTEXT,
        correcto TINYINT(1) NOT NULL DEFAULT 0,
        modo VARCHAR(20) NOT NULL DEFAULT 'practica',
        fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_intentos_usuario (usuario_id, ejercicio_id)
    )""",
    """CREATE TABLE IF NOT EXISTS borradores (
        usuario_id INT NOT NULL DEFAULT 1,
        ejercicio_id VARCHAR(40) NOT NULL,
        sql_texto MEDIUMTEXT,
        actualizado DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (usuario_id, ejercicio_id)
    )""",
    """CREATE TABLE IF NOT EXISTS marcados (
        usuario_id INT NOT NULL DEFAULT 1,
        ejercicio_id VARCHAR(40) NOT NULL,
        fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (usuario_id, ejercicio_id)
    )""",
    """CREATE TABLE IF NOT EXISTS vistos_solucion (
        usuario_id INT NOT NULL DEFAULT 1,
        ejercicio_id VARCHAR(40) NOT NULL,
        fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (usuario_id, ejercicio_id)
    )""",
    """CREATE TABLE IF NOT EXISTS simulacros (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id INT NOT NULL DEFAULT 1,
        inicio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        fin DATETIME NULL,
        duracion_min INT NOT NULL,
        ejercicios JSON NOT NULL,
        respuestas JSON NULL,
        resultado JSON NULL,
        nota DECIMAL(4,2) NULL,
        INDEX idx_simulacros_usuario (usuario_id)
    )""",
]

# Migración de instalaciones viejas (un solo usuario, sin usuario_id)
MIGRACIONES = [
    ("intentos", "ALTER TABLE intentos ADD COLUMN usuario_id INT NOT NULL DEFAULT 1 AFTER id, ADD INDEX idx_intentos_usuario (usuario_id, ejercicio_id)"),
    ("borradores", "ALTER TABLE borradores ADD COLUMN usuario_id INT NOT NULL DEFAULT 1 FIRST, DROP PRIMARY KEY, ADD PRIMARY KEY (usuario_id, ejercicio_id)"),
    ("marcados", "ALTER TABLE marcados ADD COLUMN usuario_id INT NOT NULL DEFAULT 1 FIRST, DROP PRIMARY KEY, ADD PRIMARY KEY (usuario_id, ejercicio_id)"),
    ("vistos_solucion", "ALTER TABLE vistos_solucion ADD COLUMN usuario_id INT NOT NULL DEFAULT 1 FIRST, DROP PRIMARY KEY, ADD PRIMARY KEY (usuario_id, ejercicio_id)"),
    ("simulacros", "ALTER TABLE simulacros ADD COLUMN usuario_id INT NOT NULL DEFAULT 1 AFTER id, ADD INDEX idx_simulacros_usuario (usuario_id)"),
]


def _dump_path():
    for p in DUMP_CANDIDATOS:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("No encuentro BD-Universidad.sql en la carpeta del proyecto.")


def _sentencias_dump(path):
    """El dump de mysqldump termina cada sentencia con ';' al final de línea."""
    buf = []
    with open(path, encoding="utf-8") as f:
        for linea in f:
            l = linea.rstrip("\n")
            if not buf:
                ls = l.strip()
                if not ls or ls.startswith("--"):
                    continue
                up = ls.upper()
                if up.startswith("CREATE DATABASE") or up.startswith("USE "):
                    continue
            buf.append(l)
            if l.rstrip().endswith(";"):
                yield "\n".join(buf)
                buf = []
    if buf and "".join(buf).strip():
        yield "\n".join(buf)


def existe_base(cur, nombre):
    cur.execute("SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s", (nombre,))
    return cur.fetchone()[0] > 0


def importar_pristina(log=print):
    conn = db.conectar(admin=True)
    cur = conn.cursor()
    cur.execute("DROP DATABASE IF EXISTS %s" % db.DB_PRISTINA)
    cur.execute("CREATE DATABASE %s CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci" % db.DB_PRISTINA)
    cur.execute("USE %s" % db.DB_PRISTINA)
    t0 = time.time()
    n = 0
    for s in _sentencias_dump(_dump_path()):
        cur.execute(s)
        n += 1
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.close()
    log("  dump importado (%d sentencias, %.1fs)" % (n, time.time() - t0))


def clonar_esquema(destino, con_datos=True, tablas=None, datos_de=None, vistas_base=False, origen=None, admin=False):
    """Recrea `destino` copiando estructura (con FKs) desde la base prístina.

    - con_datos: copia todas las filas.
    - datos_de: lista de tablas a las que se copian datos (si con_datos=False).
    - vistas_base: en vez de tablas, crea VISTAS que apuntan al sandbox (para ejercicios de vistas).
    """
    origen = origen or db.DB_PRISTINA
    tablas = tablas or db.TABLAS
    conn = db.conectar(admin=admin)
    cur = conn.cursor()
    cur.execute("DROP DATABASE IF EXISTS %s" % destino)
    cur.execute("CREATE DATABASE %s CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci" % destino)
    cur.execute("USE %s" % destino)
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    if vistas_base:
        for t in tablas:
            cur.execute("CREATE VIEW `%s` AS SELECT * FROM %s.`%s`" % (t, db.DB_SANDBOX, t))
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.close()
        return
    for t in tablas:
        cur.execute("SHOW CREATE TABLE %s.`%s`" % (origen, t))
        ddl = cur.fetchone()[1]
        cur.execute(ddl)
    for t in tablas:
        if con_datos or (datos_de and t in datos_de):
            cur.execute("INSERT INTO `%s` SELECT * FROM %s.`%s`" % (t, origen, t))
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.close()


def crear_vistas_precargadas(base):
    conn = db.conectar(base, admin=True)
    cur = conn.cursor()
    for nombre, cuerpo in VISTAS_PRECARGADAS.items():
        cur.execute("CREATE OR REPLACE VIEW `%s` AS %s" % (nombre, cuerpo))
    conn.close()


def restaurar_sandbox(log=print):
    t0 = time.time()
    clonar_esquema(db.DB_SANDBOX, con_datos=True, admin=True)
    crear_vistas_precargadas(db.DB_SANDBOX)
    log("  base de práctica lista (%.1fs)" % (time.time() - t0))


def crear_app_db():
    conn = db.conectar(admin=True)
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS %s CHARACTER SET utf8mb4" % db.DB_APP)
    cur.execute("USE %s" % db.DB_APP)
    for t in TABLAS_APP:
        cur.execute(t)
    for tabla, alter in MIGRACIONES:
        cur.execute("""SELECT COUNT(*) FROM information_schema.COLUMNS
                       WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME='usuario_id'""", (db.DB_APP, tabla))
        if cur.fetchone()[0] == 0:
            cur.execute(alter)
    conn.close()


def asegurar_runner(log=print):
    """En producción crea un usuario de MySQL restringido a parcialito_* para ejecutar el SQL de los alumnos."""
    if not db.multiusuario():
        return False
    clave = db.clave_runner()
    u = db.USUARIO_RUNNER
    try:
        conn = db.conectar(admin=True)
        cur = conn.cursor()
        cur.execute("CREATE USER IF NOT EXISTS '%s'@'%%%%' IDENTIFIED BY %%s" % u, (clave,))
        cur.execute("ALTER USER '%s'@'%%%%' IDENTIFIED BY %%s" % u, (clave,))
        cur.execute("GRANT ALL PRIVILEGES ON `parcialito\\_%%`.* TO '%s'@'%%'" % u)
        try:
            cur.execute("GRANT SESSION_VARIABLES_ADMIN ON *.* TO '%s'@'%%'" % u)
        except Exception:
            pass
        conn.close()
        db.usar_runner(True)
        prueba = db.conectar(db.DB_APP)
        prueba.cursor().execute("SELECT 1")
        prueba.close()
        log("  usuario restringido '%s' listo" % u)
        return True
    except Exception as e:
        db.usar_runner(False)
        log("  (no pude crear el usuario restringido, uso el principial: %s)" % e)
        return False


def estado():
    conn = db.conectar(admin=True)
    cur = conn.cursor()
    r = {}
    for b in (db.DB_PRISTINA, db.DB_SANDBOX, db.DB_APP):
        r[b] = existe_base(cur, b)
    if r[db.DB_PRISTINA]:
        cur.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE'", (db.DB_PRISTINA,))
        r["tablas_pristina"] = cur.fetchone()[0]
    conn.close()
    return r


def instalar(forzar=False, log=print):
    est = estado()
    if forzar or not est[db.DB_PRISTINA] or est.get("tablas_pristina", 0) < len(db.TABLAS):
        log("Importando BD-Universidad.sql ...")
        importar_pristina(log)
        est[db.DB_SANDBOX] = False
    if forzar or not est[db.DB_SANDBOX]:
        log("Creando base de práctica ...")
        restaurar_sandbox(log)
    crear_app_db()
    log("Todo listo.")


if __name__ == "__main__":
    instalar(forzar="--forzar" in sys.argv)
