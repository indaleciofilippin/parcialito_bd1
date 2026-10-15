window.Vistas = window.Vistas || {};

const MACHETE = [
  { id: "estrategia", grupo: "parcialito", titulo: "Cómo encarar un ejercicio", icono: "target",
    lead: "El método para no trabarte con los enunciados largos (sobre todo las «problemáticas de dominio»).",
    especial: "estrategia" },
  { id: "select", grupo: "parcialito", titulo: "SELECT básico", icono: "filter",
    lead: "Filtrar, ordenar y limitar sobre una tabla.",
    snips: [
      { t: "Plantilla completa", plantilla: true, md: "El orden en que se **escribe**. Solo SELECT y FROM son obligatorios.",
        sql: "SELECT DISTINCT columnas, expresiones AS alias\nFROM tabla t\nJOIN otra o ON o.id = t.id_otra\nWHERE condicion_sobre_filas\nGROUP BY columnas\nHAVING condicion_sobre_grupos\nORDER BY columna DESC\nLIMIT 10;" },
      { t: "Comparaciones y rangos", md: "`BETWEEN` es **inclusivo** en ambos extremos. Las fechas van entre comillas con formato `'AAAA-MM-DD'`.",
        sql: "SELECT nombre, apellido, fecha_nacimiento\nFROM alumnos\nWHERE fecha_nacimiento > '2000-01-01'\n  AND fecha_ingreso BETWEEN '2020-01-01' AND '2022-12-31';" },
      { t: "LIKE, IN y NULL", md: "`%` = cualquier cantidad de caracteres, `_` = uno solo. Nunca compares con `= NULL`: usá `IS NULL`.",
        sql: "SELECT nombre, apellido, email\nFROM docentes\nWHERE apellido LIKE 'G%'\n  AND id_departamento IN (1, 2)\n  AND email IS NOT NULL;" },
      { t: "AND / OR: ojo con los paréntesis", md: "`AND` se evalúa antes que `OR`. Sin paréntesis, la condición de capacidad solo aplica a los laboratorios.",
        sql: "SELECT nombre, tipo, capacidad\nFROM aulas\nWHERE (tipo = 'laboratorio' OR tipo = 'centro de computos')\n  AND capacidad >= 30;" },
      { t: "Ordenar, limitar y quitar repetidos", md: "`ORDER BY` acepta varias columnas y el alias del SELECT. `DISTINCT` aplica a la fila completa.",
        sql: "SELECT DISTINCT anio, cuatrimestre\nFROM comisiones\nORDER BY anio DESC, cuatrimestre;\n\nSELECT nombre, apellido, salario_base\nFROM docentes\nORDER BY salario_base DESC\nLIMIT 5;" },
      { t: "Funciones útiles", md: "`YEAR()`, `MONTH()`, `CURDATE()`, `DATEDIFF(a, b)` (días), `ROUND(x, 2)`, `CONCAT()`, `IFNULL(x, valor)`, `CASE WHEN … THEN … END`.",
        sql: "SELECT CONCAT(apellido, ', ', nombre) AS docente,\n       YEAR(fecha_ingreso) AS anio_ingreso,\n       ROUND(salario_base * 12, 2) AS sueldo_anual,\n       CASE WHEN salario_base > 350000 THEN 'Alto' ELSE 'Normal' END AS rango\nFROM docentes;" },
    ] },
  { id: "joins", grupo: "parcialito", titulo: "JOINs", icono: "link",
    lead: "Unir tablas siguiendo las claves foráneas. La condición del ON casi siempre es FK = PK.",
    snips: [
      { t: "INNER JOIN vs LEFT JOIN", md: "**INNER**: solo las filas que tienen pareja. **LEFT**: todas las de la izquierda; si no hay pareja, las columnas de la derecha vienen en `NULL`.",
        sql: "-- 1200 filas: una por comisión (solo asignaturas que tienen comisión)\nSELECT a.nombre, c.id_comision\nFROM asignaturas a\nJOIN comisiones c ON c.id_asignatura = a.id_asignatura;\n\n-- 1241 filas: suma las 41 asignaturas sin comisión (id_comision = NULL)\nSELECT a.nombre, c.id_comision\nFROM asignaturas a\nLEFT JOIN comisiones c ON c.id_asignatura = a.id_asignatura;" },
      { t: "Varias tablas en cadena", md: "Seguí el camino de FKs en el DER. Alumno → inscripción → comisión → asignatura (y docente).",
        sql: "SELECT al.apellido, al.nombre, asg.nombre AS asignatura,\n       d.apellido AS docente, i.estado\nFROM inscripcion_alumno_comision i\nJOIN alumnos al     ON al.id_alumno = i.id_alumno\nJOIN comisiones co  ON co.id_comision = i.id_comision\nJOIN asignaturas asg ON asg.id_asignatura = co.id_asignatura\nJOIN docentes d     ON d.id_docente = co.id_docente\nWHERE i.estado = 'Regular';" },
      { t: "N a N: alumnos y carreras", md: "No hay FK directa entre `alumnos` y `carreras`: la relación pasa por la tabla intermedia `alumno_carrera`.",
        sql: "SELECT a.nombre, a.apellido, c.nombre AS carrera, ac.estado\nFROM alumnos a\nJOIN alumno_carrera ac ON ac.id_alumno = a.id_alumno\nJOIN carreras c        ON c.id_carrera = ac.id_carrera;" },
      { t: "Auto-JOIN (correlatividades)", md: "La misma tabla dos veces, **con alias distintos**: una como «materia» y otra como «correlativa».",
        sql: "SELECT m.nombre AS materia, corr.nombre AS correlativa\nFROM correlatividades co\nJOIN asignaturas m    ON m.id_asignatura = co.id_asignatura\nJOIN asignaturas corr ON corr.id_asignatura = co.id_asignatura_correlativa;" },
      { t: "Caminos de JOIN más usados en esta base", md: "| Quiero… | Camino |\n|---|---|\n| notas por asignatura | notas → examenes → comisiones → asignaturas |\n| asistencias por alumno/comisión | asistencias → alumnos / comisiones |\n| inscriptos a una mesa | inscripciones_finales → mesas_finales → asignaturas |\n| carrera de un alumno | alumnos → alumno_carrera → carreras |\n| docentes de un depto | docentes → departamentos |\n| horas/monto de docentes | docente_asignatura → docentes / asignaturas |" },
    ] },
  { id: "agrupacion", grupo: "parcialito", titulo: "Agrupación", icono: "layers",
    lead: "GROUP BY arma grupos; las funciones de agregación resumen cada grupo; HAVING filtra grupos.",
    snips: [
      { t: "GROUP BY + HAVING", md: "Agrupá por el id **y** el nombre (dos asignaturas podrían llamarse igual). El umbral sobre un conteo va en `HAVING`.",
        sql: "SELECT a.id_asignatura, a.nombre, COUNT(*) AS cant_comisiones\nFROM asignaturas a\nJOIN comisiones c ON c.id_asignatura = a.id_asignatura\nGROUP BY a.id_asignatura, a.nombre\nHAVING COUNT(*) > 5\nORDER BY cant_comisiones DESC;" },
      { t: "WHERE vs HAVING", md: "**WHERE** filtra filas *antes* de agrupar (no puede usar COUNT/AVG). **HAVING** filtra los grupos *después*.",
        sql: "-- comisiones con más de 15 inscriptos activos\nSELECT i.id_comision, COUNT(*) AS activos\nFROM inscripcion_alumno_comision i\nWHERE i.estado <> 'Baja'          -- filtro de filas\nGROUP BY i.id_comision\nHAVING COUNT(*) > 15;             -- filtro de grupos" },
      { t: "COUNT(*) vs COUNT(col) vs COUNT(DISTINCT)", md: "`COUNT(*)` cuenta filas. `COUNT(col)` ignora NULL (clave con LEFT JOIN para contar 0). `COUNT(DISTINCT col)` cuenta valores distintos (¿alumnos o inscripciones?).",
        sql: "SELECT c.id_carrera, c.nombre,\n       COUNT(ac.id_alumno) AS alumnos   -- 0 si no tiene\nFROM carreras c\nLEFT JOIN alumno_carrera ac ON ac.id_carrera = c.id_carrera\nGROUP BY c.id_carrera, c.nombre;" },
      { t: "Contar con condición", md: "En MySQL una comparación vale 1 o 0, así que `SUM(condición)` cuenta cuántas filas la cumplen. Equivale a `SUM(CASE WHEN … THEN 1 ELSE 0 END)`.",
        sql: "SELECT id_comision,\n       SUM(presente = 1) AS presentes,\n       SUM(presente = 0) AS ausentes,\n       ROUND(100 * AVG(presente), 1) AS porcentaje_asistencia\nFROM asistencias\nGROUP BY id_comision;" },
      { t: "Promedios redondeados", md: "`AVG` devuelve muchos decimales: redondeá con `ROUND(AVG(x), 2)`. El corrector compara con 2 decimales.",
        sql: "SELECT e.id_examen, ROUND(AVG(n.nota), 2) AS promedio\nFROM examenes e\nJOIN notas n ON n.id_examen = e.id_examen\nGROUP BY e.id_examen;" },
      { t: "Error 1055 (ONLY_FULL_GROUP_BY)", md: "Si ponés en el SELECT una columna que no está en el GROUP BY ni dentro de una función de agregación, MySQL da error. Agregala al GROUP BY.",
        sql: "-- MAL: d.nombre no está en el GROUP BY\n-- SELECT d.nombre, COUNT(*) FROM docentes doc JOIN departamentos d ... GROUP BY d.id_departamento;\n\nSELECT d.id_departamento, d.nombre, COUNT(*) AS docentes\nFROM docentes doc\nJOIN departamentos d ON d.id_departamento = doc.id_departamento\nGROUP BY d.id_departamento, d.nombre;" },
    ] },
  { id: "ausencia", grupo: "parcialito", titulo: "Ausencia y presencia", icono: "search",
    lead: "«Los que tienen…» y «los que NO tienen…». Tres formas equivalentes; sabelas todas.",
    snips: [
      { t: "1) NOT EXISTS (la más segura)", md: "La subconsulta está **correlacionada**: se evalúa para cada docente `d`.",
        sql: "SELECT d.id_docente, d.nombre, d.apellido\nFROM docentes d\nWHERE NOT EXISTS (\n    SELECT 1 FROM comisiones c\n    WHERE c.id_docente = d.id_docente\n);" },
      { t: "2) NOT IN", md: "Simple, pero **si la subconsulta devuelve algún NULL el resultado queda vacío**. Acá `id_docente` es NOT NULL, así que funciona.",
        sql: "SELECT id_docente, nombre, apellido\nFROM docentes\nWHERE id_docente NOT IN (SELECT id_docente FROM comisiones);" },
      { t: "3) LEFT JOIN … IS NULL", md: "Conservás a todos con LEFT JOIN y te quedás con los que no encontraron pareja. Preguntá `IS NULL` sobre la **PK** de la tabla derecha.",
        sql: "SELECT d.id_docente, d.nombre, d.apellido\nFROM docentes d\nLEFT JOIN comisiones c ON c.id_docente = d.id_docente\nWHERE c.id_comision IS NULL;" },
      { t: "Presencia: «los que tienen al menos uno»", md: "`EXISTS`, `IN`, o `JOIN` + `DISTINCT` (sin DISTINCT, un alumno con 18 inscripciones aparece 18 veces).",
        sql: "SELECT a.id_alumno, a.nombre, a.apellido\nFROM alumnos a\nWHERE EXISTS (\n    SELECT 1 FROM inscripcion_alumno_comision i\n    WHERE i.id_alumno = a.id_alumno\n);\n\nSELECT DISTINCT a.id_alumno, a.nombre, a.apellido\nFROM alumnos a\nJOIN inscripcion_alumno_comision i ON i.id_alumno = a.id_alumno;" },
      { t: "Trampa clásica: INNER JOIN + IS NULL", md: "Nunca devuelve nada: el `INNER JOIN` ya descartó a los que no tienen relación. Para ausencia, **LEFT** JOIN.",
        sql: "-- MAL (siempre 0 filas)\nSELECT d.*\nFROM docentes d\nJOIN comisiones c ON c.id_docente = d.id_docente\nWHERE c.id_comision IS NULL;" },
      { t: "«Datos vacíos» (ej. 21 de la clase)", md: "Con los datos originales las consultas de ausencia dan 0 filas. Para probarlas, insertá registros sin relaciones (en la consulta con «Guardar cambios» apagado se deshacen solos).",
        sql: "INSERT INTO docentes (nombre, apellido, email, fecha_ingreso, salario_base, id_departamento)\nVALUES ('Ana', 'Prueba', 'ana.prueba@universidad.edu', '2026-03-01', 250000, 1);\n\nSELECT d.id_docente, d.apellido\nFROM docentes d\nWHERE NOT EXISTS (SELECT 1 FROM comisiones c WHERE c.id_docente = d.id_docente);" },
    ] },
  { id: "subconsultas", grupo: "parcialito", titulo: "Subconsultas", icono: "zap",
    lead: "Una consulta dentro de otra: como valor, como lista, como condición o como tabla.",
    snips: [
      { t: "Escalar: comparar contra un promedio", md: "La subconsulta devuelve **un solo valor**, entonces se puede usar con `>`, `=`, etc.",
        sql: "SELECT nombre, apellido, salario_base\nFROM docentes\nWHERE salario_base > (SELECT AVG(salario_base) FROM docentes);" },
      { t: "Promedio de conteos (tabla derivada)", md: "Ej. 10 de la clase: primero contás por grupo, después promediás esos conteos. **Toda tabla derivada lleva alias** (`AS t`).",
        sql: "SELECT a.nombre, COUNT(*) AS cant_comisiones\nFROM asignaturas a\nJOIN comisiones c ON c.id_asignatura = a.id_asignatura\nGROUP BY a.id_asignatura, a.nombre\nHAVING COUNT(*) > (\n    SELECT AVG(cant)\n    FROM (SELECT COUNT(*) AS cant\n          FROM comisiones\n          GROUP BY id_asignatura) AS t\n);" },
      { t: "IN con subconsulta", md: "Cuando la subconsulta devuelve **varios** valores, usá `IN` (con `=` da error 1242).",
        sql: "SELECT nombre\nFROM asignaturas\nWHERE id_asignatura IN (SELECT id_asignatura_correlativa FROM correlatividades);" },
      { t: "ANY / ALL", md: "`> ALL (…)`: mayor que todos. `> ANY (…)`: mayor que al menos uno.",
        sql: "SELECT nombre, apellido, salario_base\nFROM docentes\nWHERE salario_base > ALL (\n    SELECT salario_base FROM docentes\n    WHERE id_departamento = 3\n);" },
      { t: "Subconsulta en el SELECT", md: "Correlacionada, devuelve un valor por fila. Útil para «mostrar X junto con su cantidad de Y».",
        sql: "SELECT d.apellido, d.nombre,\n       (SELECT COUNT(*) FROM comisiones c WHERE c.id_docente = d.id_docente) AS comisiones\nFROM docentes d\nORDER BY comisiones DESC;" },
    ] },
  { id: "vistas", grupo: "parcialito", titulo: "Vistas", icono: "eye",
    lead: "Una vista es una consulta guardada con nombre: se usa como si fuera una tabla.",
    snips: [
      { t: "Crear, reemplazar y borrar", md: "Las columnas de la vista **no pueden repetir nombre**: usá alias (error 1060). Para probarla en la consola activá «Guardar cambios».",
        sql: "CREATE VIEW vw_comisiones_resumen AS\nSELECT co.id_comision, asg.nombre AS asignatura,\n       d.apellido AS docente, au.nombre AS aula\nFROM comisiones co\nJOIN asignaturas asg ON asg.id_asignatura = co.id_asignatura\nJOIN docentes d      ON d.id_docente = co.id_docente\nJOIN aulas au        ON au.id_aula = co.id_aula;\n\n-- para cambiarla: CREATE OR REPLACE VIEW ... AS ...\n-- para borrarla:  DROP VIEW IF EXISTS vw_comisiones_resumen;" },
      { t: "Usar una vista", md: "Se consulta como una tabla, con WHERE, JOIN, GROUP BY… Tu base ya trae `vw_inscriptos_por_comision`, `vw_alumnos_carreras`, `vw_comisiones_docentes` y `vw_notas_por_asignatura`.",
        sql: "SELECT id_comision, asignatura, cantidad_inscriptos\nFROM vw_inscriptos_por_comision\nWHERE cantidad_inscriptos > 30;" },
      { t: "¿Por qué reutilizar una vista? (ej. 14)", md: "- **Simplicidad**: la consulta final es corta y legible.\n- **Reutilización**: el JOIN/agrupación se escribe una sola vez y no se repiten errores.\n- **Consistencia**: todos calculan «inscriptos» de la misma forma.\n- **Mantenimiento**: si cambia la lógica, se cambia solo la vista.\n- **Seguridad**: se puede dar acceso a la vista sin exponer las tablas." },
    ] },
  { id: "enums", grupo: "parcialito", titulo: "Valores de los ENUM", icono: "list",
    lead: "Escribilos exactamente así (mayúsculas incluidas). Un valor que no existe da error o no encuentra nada.",
    especial: "enums" },
  { id: "errores", grupo: "parcialito", titulo: "Errores frecuentes", icono: "alert",
    lead: "Qué significan y cómo se arreglan.",
    snips: [
      { t: "1054 Unknown column", md: "Columna mal escrita, de una tabla que no está en el FROM, o un alias del SELECT usado en el WHERE." },
      { t: "1052 Column is ambiguous", md: "La columna existe en dos tablas del JOIN (`nombre`, `id_departamento`…). Prefijala: `a.nombre`." },
      { t: "1055 … not in GROUP BY", md: "Columna del SELECT que no está en el GROUP BY ni agregada. Sumala al GROUP BY." },
      { t: "1111 Invalid use of group function", md: "Usaste `COUNT/AVG/SUM` en el WHERE. Pasalo al `HAVING`." },
      { t: "1242 Subquery returns more than 1 row", md: "Comparaste con `=` una subconsulta que devuelve varias filas. Usá `IN`." },
      { t: "1248 Every derived table must have its own alias", md: "Subconsulta en el FROM sin alias: `FROM (SELECT …) AS t`." },
      { t: "1060 Duplicate column name (vistas)", md: "Dos columnas con el mismo nombre en la vista. Alias: `c.nombre AS carrera`." },
      { t: "1064 Syntax error", md: "Mirá el texto después de *near*: coma de más antes del FROM, comillas sin cerrar, falta un paréntesis, o espacio entre la función y el paréntesis (`COUNT (*)`)." },
    ] },
  { id: "dml", grupo: "extra", titulo: "DML: INSERT, UPDATE, DELETE", icono: "edit",
    lead: "No entra en el parcialito, pero conviene saberlo.",
    snips: [
      { t: "INSERT", md: "Listá siempre las columnas. La PK `AUTO_INCREMENT` se omite. Varias filas en una sola sentencia separadas por coma.",
        sql: "INSERT INTO aulas (nombre, capacidad, tipo)\nVALUES ('Aula B1', 45, 'normal'),\n       ('Laboratorio L4', 25, 'laboratorio');" },
      { t: "INSERT … SELECT", md: "Inserta el resultado de una consulta.",
        sql: "INSERT INTO inscripcion_alumno_comision (id_alumno, id_comision, fecha_inscripcion, estado)\nSELECT ac.id_alumno, 1, '2026-03-01', 'Cursa'\nFROM alumno_carrera ac\nWHERE ac.id_carrera = 17 AND ac.estado = 'activa'\n  AND ac.id_alumno NOT IN (SELECT id_alumno FROM inscripcion_alumno_comision WHERE id_comision = 1);" },
      { t: "UPDATE con subconsulta o JOIN", md: "**Siempre con WHERE.** En Workbench con *Safe Updates* el WHERE debe usar una columna con índice; si no, `SET SQL_SAFE_UPDATES = 0;` (error 1175).",
        sql: "UPDATE docentes\nSET salario_base = salario_base * 1.10\nWHERE id_departamento = (SELECT id_departamento FROM departamentos WHERE nombre = 'Ciencias Exactas');\n\nUPDATE docentes d\nJOIN departamentos dep ON dep.id_departamento = d.id_departamento\nSET d.salario_base = d.salario_base * 1.10\nWHERE dep.nombre = 'Ciencias Exactas';" },
      { t: "DELETE y claves foráneas", md: "No podés borrar un padre con hijos (error 1451): borrá primero los hijos.",
        sql: "DELETE FROM inscripciones_finales\nWHERE id_mesa IN (SELECT id_mesa FROM mesas_finales WHERE fecha < '2025-01-01');\n\nDELETE FROM mesas_finales\nWHERE fecha < '2025-01-01';" },
      { t: "Error 1093: misma tabla en la subconsulta", md: "MySQL no deja leer en una subconsulta la tabla que estás modificando. Envolvela en una tabla derivada.",
        sql: "DELETE FROM comisiones\nWHERE id_comision IN (\n    SELECT id FROM (\n        SELECT c.id_comision AS id\n        FROM comisiones c\n        LEFT JOIN inscripcion_alumno_comision i ON i.id_comision = c.id_comision\n        WHERE i.id_inscripcion IS NULL\n    ) AS t\n);" },
    ] },
  { id: "ddl", grupo: "extra", titulo: "DDL: CREATE y ALTER", icono: "database",
    lead: "No entra en el parcialito, pero conviene saberlo.",
    snips: [
      { t: "CREATE TABLE con restricciones", md: "PK con AUTO_INCREMENT, NOT NULL, DEFAULT, CHECK y FOREIGN KEY. Tipos: dinero/porcentajes `DECIMAL`, fechas `DATE`, teléfonos `VARCHAR`.",
        sql: "CREATE TABLE becas (\n    id_beca INT AUTO_INCREMENT PRIMARY KEY,\n    nombre VARCHAR(100) NOT NULL,\n    porcentaje DECIMAL(5,2) NOT NULL CHECK (porcentaje BETWEEN 0 AND 100),\n    fecha_inicio DATE NOT NULL,\n    fecha_fin DATE,\n    CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)\n);\n\nCREATE TABLE alumno_beca (\n    id_alumno INT NOT NULL,\n    id_beca INT NOT NULL,\n    fecha_otorgada DATE DEFAULT (CURDATE()),\n    PRIMARY KEY (id_alumno, id_beca),\n    FOREIGN KEY (id_alumno) REFERENCES alumnos(id_alumno),\n    FOREIGN KEY (id_beca) REFERENCES becas(id_beca)\n);" },
      { t: "ALTER TABLE", md: "Agregar, modificar, renombrar y borrar columnas o restricciones.",
        sql: "ALTER TABLE alumnos ADD COLUMN telefono_emergencia VARCHAR(50);\nALTER TABLE aulas MODIFY nombre VARCHAR(100) NOT NULL;\nALTER TABLE alumnos RENAME COLUMN telefono TO telefono_principal;\nALTER TABLE alumnos DROP COLUMN telefono_emergencia;\nALTER TABLE docentes ADD CONSTRAINT chk_salario CHECK (salario_base >= 0);\nALTER TABLE alumnos ADD CONSTRAINT uq_email UNIQUE (email);\nCREATE INDEX idx_apellido ON alumnos(apellido);" },
    ] },
];

Vistas.machete = {
  template: `
  <div class="page">
    <div class="page-head">
      <div><div class="page-title">Machete</div><div class="page-sub">Todo lo que necesitás para el parcialito, con ejemplos sobre esta misma base. Cada ejemplo se puede probar en la consola.</div></div>
    </div>
    <div class="cheat">
      <nav class="cheat-nav">
        <div class="sep">Para el parcialito</div>
        <a v-for="s in MACHETE.filter(s => s.grupo === 'parcialito')" :href="'#/machete'" @click.prevent="ir(s.id)">{{ s.titulo }}</a>
        <div class="sep">Práctica extra</div>
        <a v-for="s in MACHETE.filter(s => s.grupo === 'extra')" :href="'#/machete'" @click.prevent="ir(s.id)">{{ s.titulo }}</a>
      </nav>
      <div>
        <section v-for="s in MACHETE" :key="s.id" :id="'m-' + s.id" class="cheat-sec">
          <h2><ico :n="s.icono"/> {{ s.titulo }} <span v-if="s.grupo === 'extra'" class="badge warning">no entra</span></h2>
          <p class="lead">{{ s.lead }}</p>

          <template v-if="s.especial === 'estrategia'">
            <div class="grid" style="grid-template-columns: 1fr 1fr">
              <div class="card pad">
                <div class="card-title" style="margin-bottom:12px">Los 6 pasos</div>
                <div class="steps-guide">
                  <div><div><b>¿Qué devuelvo?</b> ¿Una fila por qué cosa? (por carrera, por docente, por comisión…). Eso define el GROUP BY.</div></div>
                  <div><div><b>¿Qué tablas necesito?</b> Ubicá en el DER dónde está cada dato y el camino de FKs que las une.</div></div>
                  <div><div><b>¿Qué filas filtro antes?</b> (estado distinto de 'Baja', un año, un tipo…) → <code>WHERE</code>.</div></div>
                  <div><div><b>¿Qué cuento / sumo / promedio?</b> ¿Filas o valores distintos? → <code>COUNT(*)</code> / <code>COUNT(DISTINCT …)</code> / <code>SUM</code> / <code>AVG</code>.</div></div>
                  <div><div><b>¿Hay un umbral sobre el resultado agregado?</b> («más de 90», «menor a 5») → <code>HAVING</code>. Ojo: «más de» es <code>&gt;</code>, «al menos» es <code>&gt;=</code>.</div></div>
                  <div><div><b>¿Qué muestro y cómo ordeno?</b> Nombre + valor calculado con alias claro; <code>ORDER BY</code> si ayuda.</div></div>
                </div>
              </div>
              <div class="grid" style="align-content:start">
                <div class="card pad">
                  <div class="card-title" style="margin-bottom:12px">Orden lógico de ejecución</div>
                  <div class="flow">
                    <template v-for="(p, i) in orden"><span class="st">{{ p[0] }}<small>{{ p[1] }}</small></span><span v-if="i < orden.length - 1" class="ar">→</span></template>
                  </div>
                  <p class="small muted" style="margin:12px 0 0">Por eso un alias del SELECT no existe todavía en el WHERE, pero sí en el ORDER BY.</p>
                </div>
                <div class="card pad">
                  <div class="card-title" style="margin-bottom:8px">Traducciones típicas del enunciado</div>
                  <table class="enum-table">
                    <tr><td>«cada / por cada X»</td><td>GROUP BY X</td></tr>
                    <tr><td>«cantidad de»</td><td>COUNT(*) o COUNT(DISTINCT …)</td></tr>
                    <tr><td>«más de N» (sobre un conteo)</td><td>HAVING COUNT(…) &gt; N</td></tr>
                    <tr><td>«que no tengan / nunca»</td><td>NOT EXISTS / LEFT JOIN … IS NULL</td></tr>
                    <tr><td>«al menos uno / alguna vez»</td><td>EXISTS / IN / JOIN + DISTINCT</td></tr>
                    <tr><td>«superior al promedio»</td><td>&gt; (SELECT AVG(…) …)</td></tr>
                    <tr><td>«activos / actualmente»</td><td>filtro por estado (ej. &lt;&gt; 'Baja', = 'activa')</td></tr>
                    <tr><td>«desaprobado»</td><td>nota &lt; 4</td></tr>
                  </table>
                </div>
              </div>
            </div>
          </template>

          <template v-else-if="s.especial === 'enums'">
            <div class="card pad">
              <table class="enum-table">
                <tr v-for="e in enums"><td>{{ e.tabla }}.{{ e.columna }}</td><td><span class="enum-vals" style="margin:0"><span v-for="v in e.valores">'{{ v }}'</span></span></td></tr>
                <tr><td>asignaturas.es_obligatoria · asistencias.presente · notas.aprobado</td><td class="small">TINYINT(1): 1 = sí / verdadero, 0 = no / falso (<code>TRUE</code> y <code>FALSE</code> equivalen a 1 y 0)</td></tr>
              </table>
            </div>
          </template>

          <div v-else class="cheat-grid">
            <div v-for="sn in s.snips" class="card snip">
              <h4>{{ sn.t }}</h4>
              <md-view v-if="sn.md" :texto="sn.md"/>
              <code-block v-if="sn.sql" :sql="sn.sql" :probar="!sn.plantilla"/>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>`,
  setup() {
    const { computed, onMounted } = Vue;
    onMounted(() => U.cargarEsquema().catch(() => {}));
    const orden = [["FROM", "tablas + JOIN"], ["WHERE", "filtra filas"], ["GROUP BY", "agrupa"], ["HAVING", "filtra grupos"], ["SELECT", "proyecta"], ["ORDER BY", "ordena"], ["LIMIT", "recorta"]];
    const enums = computed(() => {
      const e = U.store.esquema;
      if (!e) return [];
      const out = [];
      for (const [t, cols] of Object.entries(e.detalle)) {
        if (e.tipos[t] !== "tabla") continue;
        cols.forEach((c) => { if (c.valores) out.push({ tabla: t, columna: c.nombre, valores: c.valores }); });
      }
      return out;
    });
    function ir(id) { const el = document.getElementById("m-" + id); if (el) el.scrollIntoView({ behavior: "smooth", block: "start" }); }
    return { MACHETE, orden, enums, ir };
  },
};
