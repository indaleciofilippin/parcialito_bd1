/* ==========================================================================
   Autocompletado SQL inteligente para el editor (CodeMirror 5)

   - Parsea la sentencia actual (texto entre ';' alrededor del cursor, ignorando
     strings y comentarios) y detecta tablas, vistas, alias, subconsultas,
     tablas derivadas y CTEs.
   - Según el contexto sugiere: tablas/vistas, columnas (calificadas cuando hace
     falta), condiciones de JOIN por clave foránea, valores de ENUM, funciones y
     palabras clave.

   API (funciones puras, se pueden probar sin UI):
     Autocompletar.analizar(texto, pos)          -> { contexto, prefijo, tablas, ... }
     Autocompletar.sugerencias(texto, pos, opt)  -> { contexto, from, to, list: [...] }
     Autocompletar.probar("SELECT a.| FROM alumnos a")  (la barra marca el cursor)
   Integración con CodeMirror:
     Autocompletar.hint(cm, options)   (para hintOptions.hint)
     Autocompletar.instalar(cm)        (disparo automático mientras se escribe)
   ========================================================================== */
(function () {
  "use strict";

  // ---------------------------------------------------------------- Léxico
  const WCH = /[A-Za-z0-9_$À-￿]/;
  const ID_OK = /^[A-Za-z_$À-￿][A-Za-z0-9_$À-￿]*$/;
  const RE_NUM = /[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?[A-Za-z0-9_$]*/y;
  const RE_PAL = /[A-Za-z_$À-￿][A-Za-z0-9_$À-￿]*/y;
  const RE_VAR = /@@?(?:`[^`]*`|'[^']*'|"[^"]*"|[A-Za-z0-9_$.]*)/y;
  const OPS3 = ["<=>", "->>"];
  const OPS2 = ["<>", "<=", ">=", "!=", ":=", "||", "&&", "->", "<<", ">>"];

  function conjunto(s) { return new Set(s.trim().split(/\s+/)); }

  // Palabras que NO pueden ser alias sin comillas (y que no "terminan" un valor)
  const RESERVADAS = conjunto(`
    SELECT FROM WHERE JOIN INNER LEFT RIGHT OUTER CROSS NATURAL FULL STRAIGHT_JOIN ON USING
    GROUP ORDER BY HAVING LIMIT OFFSET SET UNION EXCEPT INTERSECT ALL DISTINCT DISTINCTROW AS
    AND OR NOT XOR IN IS LIKE BETWEEN EXISTS CASE WHEN THEN ELSE END INTO VALUES INSERT UPDATE
    DELETE REPLACE CREATE DROP ALTER TABLE VIEW WITH WINDOW PARTITION OVER FOR LOCK FORCE IGNORE
    USE INDEX KEY PRIMARY FOREIGN REFERENCES DEFAULT NULL TRUE FALSE ASC DESC ANY SOME DIV MOD
    REGEXP RLIKE INTERVAL ROLLUP LATERAL RECURSIVE`);
  const VALOR_KW = conjunto("NULL TRUE FALSE END");
  const CLAUSULAS = conjunto(`SELECT FROM JOIN STRAIGHT_JOIN ON USING WHERE BY HAVING LIMIT OFFSET SET
    INTO UPDATE VALUES TABLE VIEW REFERENCES UNION EXCEPT INTERSECT DELETE INSERT REPLACE WITH`);
  const UNIONES = conjunto("UNION EXCEPT INTERSECT");
  const MODIF_JOIN = conjunto("LEFT RIGHT INNER OUTER CROSS NATURAL FULL");
  const FUNC_CON_FROM = conjunto("EXTRACT TRIM SUBSTRING SUBSTR POSITION");

  // ---------------------------------------------------------------- Vocabulario
  const KW_GENERAL = [
    "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "NOT IN", "EXISTS", "NOT EXISTS",
    "IS NULL", "IS NOT NULL", "BETWEEN", "LIKE", "NOT LIKE", "AS", "DISTINCT",
    "GROUP BY", "HAVING", "ORDER BY", "ASC", "DESC", "LIMIT",
    "JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN", "ON", "USING",
    "UNION", "UNION ALL", "WHEN", "THEN", "ELSE", "END", "NULL", "TRUE", "FALSE",
    "ALL", "ANY", "INTERVAL", "DIV", "MOD", "REGEXP", "WITH",
    "CREATE VIEW", "CREATE OR REPLACE VIEW", "INSERT INTO", "VALUES", "UPDATE", "SET", "DELETE FROM",
  ];
  const KW_INICIO = [
    "SELECT", "SELECT DISTINCT", "INSERT INTO", "UPDATE", "DELETE FROM", "CREATE VIEW",
    "CREATE OR REPLACE VIEW", "DROP VIEW", "WITH", "CREATE TABLE", "ALTER TABLE", "DROP TABLE",
    "SHOW TABLES", "DESCRIBE", "START TRANSACTION", "COMMIT", "ROLLBACK",
  ];
  const KW_TRAS_TABLA = {
    FROM: ["JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN", "NATURAL JOIN", "WHERE",
           "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "UNION", "UNION ALL"],
    JOIN: ["ON", "USING", "JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN", "WHERE",
           "GROUP BY", "ORDER BY", "HAVING", "LIMIT"],
    UPDATE: ["SET", "JOIN", "INNER JOIN", "LEFT JOIN"],
  };
  const SIN_ESPACIO = new Set(["ASC", "DESC", "NULL", "TRUE", "FALSE", "END", "IS NULL", "IS NOT NULL",
    "COMMIT", "ROLLBACK", "SHOW TABLES", "START TRANSACTION", "NOT NULL"]);
  const REDISPARA = new Set(["FROM", "JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN",
    "NATURAL JOIN", "OUTER JOIN", "ON", "INSERT INTO", "INTO", "UPDATE", "DELETE FROM", "DROP VIEW"]);

  // [nombre, firma, descripción, sinArgumentos]
  const FUNCIONES = [
    ["COUNT", "COUNT(expr)", "agregación · cuenta"],
    ["SUM", "SUM(expr)", "agregación · suma"],
    ["AVG", "AVG(expr)", "agregación · promedio"],
    ["MIN", "MIN(expr)", "agregación · mínimo"],
    ["MAX", "MAX(expr)", "agregación · máximo"],
    ["ROUND", "ROUND(x, d)", "redondea"],
    ["CONCAT", "CONCAT(a, b, …)", "concatena texto"],
    ["CONCAT_WS", "CONCAT_WS(sep, a, …)", "concatena con separador"],
    ["GROUP_CONCAT", "GROUP_CONCAT(expr)", "agregación · une textos"],
    ["IFNULL", "IFNULL(x, valor)", "reemplaza NULL"],
    ["COALESCE", "COALESCE(a, b, …)", "primer no NULL"],
    ["NULLIF", "NULLIF(a, b)", "NULL si son iguales"],
    ["IF", "IF(cond, si, no)", "condicional"],
    ["YEAR", "YEAR(fecha)", "fecha · año"],
    ["MONTH", "MONTH(fecha)", "fecha · mes"],
    ["DAY", "DAY(fecha)", "fecha · día"],
    ["CURDATE", "CURDATE()", "fecha de hoy", true],
    ["NOW", "NOW()", "fecha y hora actual", true],
    ["DATEDIFF", "DATEDIFF(f1, f2)", "fecha · días entre"],
    ["TIMESTAMPDIFF", "TIMESTAMPDIFF(YEAR, f1, f2)", "fecha · diferencia"],
    ["DATE_FORMAT", "DATE_FORMAT(f, '%d/%m/%Y')", "fecha · formato"],
    ["DATE_ADD", "DATE_ADD(f, INTERVAL n DAY)", "fecha · sumar"],
    ["DATE_SUB", "DATE_SUB(f, INTERVAL n DAY)", "fecha · restar"],
    ["UPPER", "UPPER(s)", "texto · mayúsculas"],
    ["LOWER", "LOWER(s)", "texto · minúsculas"],
    ["LENGTH", "LENGTH(s)", "texto · largo"],
    ["CHAR_LENGTH", "CHAR_LENGTH(s)", "texto · caracteres"],
    ["SUBSTRING", "SUBSTRING(s, ini, n)", "texto · subcadena"],
    ["TRIM", "TRIM(s)", "texto · quita espacios"],
    ["ABS", "ABS(x)", "valor absoluto"],
    ["CEIL", "CEIL(x)", "redondea hacia arriba"],
    ["FLOOR", "FLOOR(x)", "redondea hacia abajo"],
    ["CAST", "CAST(x AS tipo)", "convierte tipo"],
  ];
  const SNIPPET_CASE = { nombre: "CASE", display: "CASE WHEN … END", texto: "CASE WHEN  THEN  ELSE  END", cursor: 10 };

  // ---------------------------------------------------------------- Utilidades
  const esP = (t, v) => !!t && t.t === "p" && t.v === v;
  const esPal = (t, u) => !!t && t.t === "w" && t.u === u;
  const esId = (t) => !!t && (t.t === "q" || (t.t === "w" && !RESERVADAS.has(t.u)));
  const esIdCualquiera = (t) => !!t && (t.t === "q" || t.t === "w");
  const eqi = (a, b) => !!a && !!b && String(a).toLowerCase() === String(b).toLowerCase();
  function quoteId(s) {
    s = String(s);
    return ID_OK.test(s) && !RESERVADAS.has(s.toUpperCase()) ? s : "`" + s.replace(/`/g, "``") + "`";
  }
  function fmtNum(n) { return (Number(n) || 0).toLocaleString("es-AR"); }
  function tipoCorto(t) {
    t = String(t || "");
    const m = /^\s*(enum|set)\s*\(/i.exec(t);
    if (m) { const v = valoresDeTipo(t); return m[1].toLowerCase() + "(" + (v ? v.length : "…") + ")"; }
    return t.toLowerCase();
  }
  function valoresDeTipo(tipo) {
    const m = /^\s*(?:enum|set)\s*\(([\s\S]*)\)\s*$/i.exec(tipo || "");
    if (!m) return null;
    const out = [], re = /'((?:[^'\\]|''|\\.)*)'/g;
    let x;
    while ((x = re.exec(m[1]))) out.push(x[1].replace(/''/g, "'"));
    return out.length ? out : null;
  }
  function tipoDeFuncion(fn) {
    if (!fn) return "";
    if (fn === "COUNT") return "bigint";
    if (fn === "SUM" || fn === "AVG" || fn === "ROUND") return "decimal";
    if (/^(CONCAT|CONCAT_WS|GROUP_CONCAT|UPPER|LOWER|SUBSTRING|TRIM|DATE_FORMAT)$/.test(fn)) return "varchar";
    if (/^(YEAR|MONTH|DAY|DATEDIFF|TIMESTAMPDIFF|LENGTH|CHAR_LENGTH)$/.test(fn)) return "int";
    return "";
  }

  // ---------------------------------------------------------------- Esquema
  let esquemaForzado = null, cacheSrc = null, cacheIdx = null;
  const IDX_VACIO = { tablas: {}, lista: [], fks: [] };
  function usarEsquema(e) { esquemaForzado = e || null; cacheSrc = null; cacheIdx = null; }

  function indice() {
    let e = esquemaForzado || (window.U && window.U.store ? window.U.store.esquema : null);
    if (!e) return IDX_VACIO;
    if (window.Vue && typeof window.Vue.toRaw === "function") e = window.Vue.toRaw(e);
    if (e === cacheSrc && cacheIdx) return cacheIdx;
    const det = e.detalle || {}, tipos = e.tipos || {}, conteos = e.conteos || {}, simples = e.columnas || {};
    const fks = (e.fks || []).filter((f) => f && f.tabla && f.ref_tabla && f.columna && f.ref_columna);
    const fkDe = {};
    fks.forEach((f) => { fkDe[(f.tabla + "." + f.columna).toLowerCase()] = f.ref_tabla; });
    const tablas = {}, lista = [];
    const nombres = Object.keys(det).length ? Object.keys(det) : Object.keys(simples);
    nombres.forEach((nombre) => {
      const crudas = det[nombre] || (simples[nombre] || []).map((n) => ({ nombre: n }));
      const tipo = tipos[nombre] === "vista" ? "vista" : "tabla";
      const cols = crudas.map((c) => ({
        nombre: String(c.nombre),
        tipo: c.tipo || "",
        pk: c.clave === "PRI",
        fk: fkDe[(nombre + "." + c.nombre).toLowerCase()] || null,
        valores: c.valores && c.valores.length ? c.valores.slice() : valoresDeTipo(c.tipo),
        tabla: nombre,
      }));
      const t = { nombre, tipo, filas: conteos[nombre], cols, orden: lista.length };
      tablas[nombre.toLowerCase()] = t;
      lista.push(t);
    });
    lista.sort((a, b) => (a.tipo === b.tipo ? a.orden - b.orden : a.tipo === "tabla" ? -1 : 1));
    cacheSrc = e;
    cacheIdx = { tablas, lista, fks };
    return cacheIdx;
  }

  // ---------------------------------------------------------------- Tokenizador
  function tokenizar(src) {
    const toks = [], n = src.length;
    let i = 0;
    while (i < n) {
      const c = src[i];
      if (c === " " || c === "\n" || c === "\t" || c === "\r" || c === "\f" || c === "\v" || c === " ") { i++; continue; }
      const s = i;
      // comentarios
      if (c === "#" || (c === "-" && src[i + 1] === "-" && (i + 2 >= n || /\s/.test(src[i + 2])))) {
        let j = src.indexOf("\n", i);
        if (j < 0) j = n;
        toks.push({ t: "c", s, e: j, linea: true });
        i = j;
        continue;
      }
      if (c === "/" && src[i + 1] === "*") {
        const j = src.indexOf("*/", i + 2);
        const e = j < 0 ? n : j + 2;
        toks.push({ t: "c", s, e, abierto: j < 0 });
        i = e;
        continue;
      }
      // strings e identificadores entre backticks
      if (c === "'" || c === '"' || c === "`") {
        let j = i + 1, v = "", abierto = true;
        while (j < n) {
          const d = src[j];
          if (d === "\\" && c !== "`" && j + 1 < n) { v += src[j + 1]; j += 2; continue; }
          if (d === c) {
            if (src[j + 1] === c) { v += c; j += 2; continue; }
            abierto = false;
            j++;
            break;
          }
          v += d;
          j++;
        }
        if (j > n) j = n;
        toks.push({ t: c === "`" ? "q" : "s", s, e: j, v, q: c, abierto });
        i = j;
        continue;
      }
      if (c >= "0" && c <= "9") {
        RE_NUM.lastIndex = i;
        const m = RE_NUM.exec(src);
        const j = i + (m ? m[0].length : 1);
        toks.push({ t: "n", s, e: j, v: src.slice(s, j) });
        i = j;
        continue;
      }
      if (c === "@") {
        RE_VAR.lastIndex = i;
        const m = RE_VAR.exec(src);
        const j = i + Math.max(1, m ? m[0].length : 1);
        toks.push({ t: "v", s, e: j, v: src.slice(s, j) });
        i = j;
        continue;
      }
      RE_PAL.lastIndex = i;
      const m = RE_PAL.exec(src);
      if (m) {
        const j = i + m[0].length;
        toks.push({ t: "w", s, e: j, v: m[0], u: m[0].toUpperCase() });
        i = j;
        continue;
      }
      if ("(),.;".indexOf(c) >= 0) { toks.push({ t: "p", s, e: i + 1, v: c }); i++; continue; }
      let op = c;
      if (OPS3.indexOf(src.substr(i, 3)) >= 0) op = src.substr(i, 3);
      else if (OPS2.indexOf(src.substr(i, 2)) >= 0) op = src.substr(i, 2);
      toks.push({ t: "o", s, e: i + op.length, v: op });
      i += op.length;
    }
    return toks;
  }

  // Asigna a cada token su grupo de paréntesis (g) y su segmento de UNION (sg).
  // '(' y ')' pertenecen al grupo de afuera; lo de adentro, al grupo hijo.
  function estructurar(toks) {
    const grupos = [{ id: 0, padre: -1, segPadre: 0, seg: 0, abre: -1, cierra: -1 }];
    const pila = [0];
    toks.forEach((t, i) => {
      t.i = i;
      const g = pila[pila.length - 1];
      if (esP(t, "(")) {
        t.g = g; t.sg = grupos[g].seg;
        const ng = { id: grupos.length, padre: g, segPadre: grupos[g].seg, seg: 0, abre: i, cierra: -1 };
        grupos.push(ng);
        pila.push(ng.id);
        t.hijo = ng.id;
      } else if (esP(t, ")")) {
        if (pila.length > 1) { const cg = pila.pop(); grupos[cg].cierra = i; t.cierraGrupo = cg; }
        const g2 = pila[pila.length - 1];
        t.g = g2; t.sg = grupos[g2].seg;
      } else {
        t.g = g; t.sg = grupos[g].seg;
        if (t.t === "w" && UNIONES.has(t.u)) grupos[g].seg++;
      }
    });
    return grupos;
  }

  // Grupo/segmento en una posición y la cadena de grupos que la contienen.
  function grupoEn(A, off) {
    let cg = 0;
    for (const t of A.toks) {
      if (t.e > off) break;
      if (t.hijo != null) cg = t.hijo;
      else if (t.cierraGrupo != null) cg = A.grupos[t.cierraGrupo].padre;
    }
    let csg = 0;
    for (const t of A.toks) {
      if (t.e > off) break;
      if (t.g === cg && t.t === "w" && UNIONES.has(t.u)) csg++;
    }
    const cadena = [];
    let g = cg, s = csg;
    while (g >= 0) {
      cadena.push([g, s]);
      const gr = A.grupos[g];
      s = gr.segPadre;
      g = gr.padre;
    }
    return { cg, csg, cadena };
  }
  function esDescendiente(grupos, g, anc) {
    while (g >= 0) { if (g === anc) return true; g = grupos[g].padre; }
    return false;
  }
  function dentroDeFuncionEspecial(A, t) {
    const gr = A.grupos[t.g];
    if (!gr || gr.abre < 1) return false;
    const prev = A.toks[gr.abre - 1];
    return !!prev && prev.t === "w" && FUNC_CON_FROM.has(prev.u);
  }
  function terminaValor(t, prev) {
    if (!t) return false;
    if (t.t === "w") return !RESERVADAS.has(t.u) || VALOR_KW.has(t.u);
    if (t.t === "q" || t.t === "s" || t.t === "n" || t.t === "v") return true;
    if (esP(t, ")")) return true;
    if (t.t === "o" && t.v === "*") return !terminaValor(prev, null); // SELECT * / a.*  (no multiplicación)
    return false;
  }

  // ---------------------------------------------------------------- Tablas en la sentencia
  function extraerTablas(A) {
    const { toks, grupos, idx } = A;
    const refs = [], ctes = {};

    // WITH nombre [(cols)] AS ( ... ) [, ...]
    for (let i = 0; i < toks.length; i++) {
      if (!esPal(toks[i], "WITH") || esPal(toks[i + 1], "ROLLUP")) continue;
      let j = i + 1;
      if (esPal(toks[j], "RECURSIVE")) j++;
      while (j < toks.length) {
        const nt = toks[j];
        if (!esIdCualquiera(nt)) break;
        j++;
        let cols = null;
        if (esP(toks[j], "(")) {
          const g = toks[j].hijo, cierra = grupos[g].cierra;
          cols = [];
          for (let k = j + 1; k < (cierra < 0 ? toks.length : cierra); k++) if (toks[k].g === g && esIdCualquiera(toks[k])) cols.push(toks[k].v);
          if (cierra < 0) break;
          j = cierra + 1;
        }
        if (!esPal(toks[j], "AS")) break;
        j++;
        if (!esP(toks[j], "(")) break;
        const g = toks[j].hijo, cierra = grupos[g].cierra;
        ctes[nt.v.toLowerCase()] = { nombre: nt.v, cols, sub: { g, a: j + 1, b: cierra < 0 ? toks.length : cierra } };
        if (cierra < 0) break;
        j = cierra + 1;
        if (esP(toks[j], ",")) { j++; continue; }
        break;
      }
    }

    // FROM / JOIN / UPDATE / INTO
    for (let i = 0; i < toks.length; i++) {
      const t = toks[i];
      if (t.t !== "w") continue;
      let coma;
      if (t.u === "FROM") { if (dentroDeFuncionEspecial(A, t)) continue; coma = true; }
      else if (t.u === "JOIN" || t.u === "STRAIGHT_JOIN") coma = false;
      else if (t.u === "UPDATE") { if (esPal(toks[i - 1], "KEY")) continue; coma = true; }
      else if (t.u === "INTO") coma = false;
      else continue;
      let j = i + 1;
      while (j < toks.length) {
        const a = toks[j];
        if (!a || a.g !== t.g) break;
        const ref = { kw: t.u, g: t.g, sg: t.sg, i: j, nombre: null, alias: null, tipo: null };
        if (esP(a, "(")) {
          const g = a.hijo, cierra = grupos[g].cierra;
          ref.tipo = "derivada";
          ref.sub = { g, a: j + 1, b: cierra < 0 ? toks.length : cierra };
          if (cierra < 0) { refs.push(ref); break; }
          j = cierra + 1;
        } else if (esId(a)) {
          ref.nombre = a.v;
          j++;
          if (esP(toks[j], ".") && esIdCualquiera(toks[j + 1])) { ref.base = a.v; ref.nombre = toks[j + 1].v; j += 2; }
        } else break;
        const b = toks[j];
        if (b && b.g === t.g) {
          if (esPal(b, "AS")) {
            if (esId(toks[j + 1]) && toks[j + 1].g === t.g) { ref.alias = toks[j + 1].v; j += 2; } else j++;
          } else if (esId(b)) { ref.alias = b.v; j++; }
        }
        if (ref.tipo !== "derivada") {
          const k = String(ref.nombre).toLowerCase();
          if (!ref.base && ctes[k]) { ref.tipo = "cte"; ref.cte = ctes[k]; }
          else if (idx.tablas[k]) { ref.tabla = idx.tablas[k]; ref.tipo = ref.tabla.tipo; }
          else ref.tipo = "desconocida";
        }
        refs.push(ref);
        if (coma && esP(toks[j], ",") && toks[j].g === t.g) { j++; continue; }
        break;
      }
    }
    return { refs, ctes };
  }

  function columnasDe(A, ref) {
    if (!ref) return [];
    if (ref._cols) return ref._cols;
    ref._cols = []; // evita recursión infinita
    let cols = [];
    if (ref.tabla) cols = ref.tabla.cols;
    else if (ref.tipo === "derivada") cols = columnasSelect(A, ref.sub, ref.alias ? "subconsulta " + ref.alias : "subconsulta");
    else if (ref.tipo === "cte" && ref.cte) {
      const c = ref.cte;
      if (!c._cols) {
        c._cols = [];
        c._cols = c.cols && c.cols.length
          ? c.cols.map((n) => ({ nombre: n, tipo: "", tabla: "CTE " + c.nombre }))
          : columnasSelect(A, c.sub, "CTE " + c.nombre);
      }
      cols = c._cols;
    }
    ref._cols = cols;
    return cols;
  }

  // Ítems (listas de tokens) de la lista del SELECT que está en toks[iSel]
  function itemsSelectDesde(A, iSel, b) {
    const toks = A.toks, g = toks[iSel].g;
    let i = iSel + 1;
    while (i < b && toks[i].g === g && toks[i].t === "w" && /^(DISTINCT|ALL|DISTINCTROW|STRAIGHT_JOIN|HIGH_PRIORITY|SQL_[A-Z_]+)$/.test(toks[i].u)) i++;
    const items = [];
    let cur = [];
    for (; i < b; i++) {
      const t = toks[i];
      if (t.g === g && t.t === "w" && /^(FROM|INTO|WHERE|GROUP|ORDER|HAVING|LIMIT|UNION|EXCEPT|INTERSECT|WINDOW)$/.test(t.u)) break;
      if (t.g === g && esP(t, ",")) { if (cur.length) items.push(cur); cur = []; continue; }
      cur.push(t);
    }
    if (cur.length) items.push(cur);
    return items;
  }
  function analizarItemSelect(A, item, g) {
    const nivel = item.filter((t) => t.g === g);
    const n = nivel.length, u = nivel[n - 1], p = nivel[n - 2];
    let alias = null, expr = item;
    if (n >= 2 && (esId(u) || u.t === "s") && esPal(p, "AS")) { alias = u.v; expr = item.slice(0, item.indexOf(p)); }
    else if (n >= 2 && esId(u) && terminaValor(p, nivel[n - 3]) && !esP(p, ".")) { alias = u.v; expr = item.slice(0, item.indexOf(u)); }
    let col = null, calif = null, estrella = false;
    if (expr.length === 1 && esIdCualquiera(expr[0])) col = expr[0].v;
    else if (expr.length === 3 && esIdCualquiera(expr[0]) && esP(expr[1], ".") && esIdCualquiera(expr[2])) { calif = expr[0].v; col = expr[2].v; }
    else if (expr.length === 1 && expr[0].t === "o" && expr[0].v === "*") estrella = true;
    else if (expr.length === 3 && esIdCualquiera(expr[0]) && esP(expr[1], ".") && expr[2].t === "o" && expr[2].v === "*") { estrella = true; calif = expr[0].v; }
    const texto = expr.length ? A.texto.slice(expr[0].s, expr[expr.length - 1].e).replace(/\s+/g, " ") : "";
    const fn = expr[0] && expr[0].t === "w" && esP(expr[1], "(") ? expr[0].u : null;
    return { alias, col, calif, estrella, texto, fn };
  }
  // Columnas que devuelve una subconsulta (tabla derivada / CTE)
  function columnasSelect(A, sub, etiqueta) {
    const toks = A.toks;
    let iSel = -1;
    for (let i = sub.a; i < sub.b; i++) if (toks[i].g === sub.g && esPal(toks[i], "SELECT")) { iSel = i; break; }
    if (iSel < 0) return [];
    const sel = toks[iSel];
    const internas = A.refs.filter((r) => r.g === sub.g && r.sg === sel.sg && r.i > iSel && r.i < sub.b && r.kw !== "INTO");
    const coincide = (r, q) => eqi(r.alias, q) || eqi(r.nombre, q);
    const out = [];
    itemsSelectDesde(A, iSel, sub.b).forEach((item) => {
      const x = analizarItemSelect(A, item, sub.g);
      if (x.estrella) {
        internas.forEach((r) => {
          if (x.calif && !coincide(r, x.calif)) return;
          columnasDe(A, r).forEach((c) => out.push({ nombre: c.nombre, tipo: c.tipo, valores: c.valores, pk: false, fk: null, tabla: etiqueta }));
        });
        return;
      }
      let origen = null;
      if (x.col) {
        const cands = x.calif ? internas.filter((r) => coincide(r, x.calif)) : internas;
        for (const r of cands) {
          const c = columnasDe(A, r).find((c) => eqi(c.nombre, x.col));
          if (c) { origen = c; break; }
        }
      }
      const nombre = x.alias || x.col || x.texto;
      if (!nombre) return;
      out.push({
        nombre, tipo: origen ? origen.tipo : tipoDeFuncion(x.fn), valores: origen ? origen.valores : null,
        pk: false, fk: null, tabla: etiqueta,
      });
    });
    return out;
  }
  // Alias definidos en la lista del SELECT de la consulta donde está el cursor
  function aliasDelSelect(A, gi) {
    for (const par of gi.cadena) {
      const g = par[0], s = par[1];
      let iSel = -1;
      for (let i = 0; i < A.toks.length; i++) { const t = A.toks[i]; if (t.g === g && t.sg === s && esPal(t, "SELECT")) { iSel = i; break; } }
      if (iSel < 0) continue;
      const cierra = g === 0 ? -1 : A.grupos[g].cierra;
      const fin = cierra < 0 ? A.toks.length : cierra;
      return itemsSelectDesde(A, iSel, fin).map((it) => analizarItemSelect(A, it, g)).filter((x) => x.alias).map((x) => x.alias);
    }
    return [];
  }

  // Tablas visibles desde el cursor: las de su consulta y las de las consultas que la contienen
  function visibles(A, gi) {
    const out = [];
    gi.cadena.forEach((par) => {
      A.refs.forEach((r) => {
        if (r.g === par[0] && r.sg === par[1] && r.kw !== "INTO" && !(r.sub && esDescendiente(A.grupos, gi.cg, r.sub.g))) out.push(r);
      });
    });
    return out;
  }
  function resolverCalif(A, q, vis) {
    const busca = (lista, f) => { for (const r of lista) if (f(r)) return r; return null; };
    const ql = String(q).toLowerCase();
    return busca(vis, (r) => eqi(r.alias, q)) || busca(A.refs, (r) => eqi(r.alias, q))
      || busca(vis, (r) => !r.alias && eqi(r.nombre, q)) || busca(A.refs, (r) => !r.alias && eqi(r.nombre, q))
      || busca(A.refs, (r) => eqi(r.nombre, q))
      || (A.ctes[ql] ? { tipo: "cte", cte: A.ctes[ql], nombre: q } : null)
      || (A.idx.tablas[ql] ? { tipo: A.idx.tablas[ql].tipo, tabla: A.idx.tablas[ql], nombre: q } : null);
  }

  // ---------------------------------------------------------------- Contexto
  function esAsDeVista(nivel, k) {
    let j = k - 1;
    if (esP(nivel[j], ")") && esP(nivel[j - 1], "(")) j -= 2;
    if (!esIdCualquiera(nivel[j])) return false;
    j--;
    if (esP(nivel[j], ".") && esIdCualquiera(nivel[j - 1])) j -= 2;
    return esPal(nivel[j], "VIEW");
  }

  function expresion(nivel, cl) {
    const u = nivel[nivel.length - 1], p = nivel[nivel.length - 2];
    if (u && esPal(u, "AS")) return { contexto: "alias", clausula: cl };
    if (u && u.t === "w" && (u.u === "GROUP" || u.u === "ORDER" || u.u === "PARTITION")) return { contexto: "palabras", lista: ["BY"], clausula: cl };
    if (u && u.t === "w" && MODIF_JOIN.has(u.u)) return { contexto: "palabras", lista: ["JOIN", "OUTER JOIN"], clausula: cl };
    if (u && esPal(u, "IS")) return { contexto: "palabras", lista: ["NULL", "NOT NULL", "TRUE", "FALSE"], min: 0, clausula: cl };
    if (u && terminaValor(u, p)) return { contexto: "palabras", lista: KW_GENERAL, despuesValor: true, clausula: cl };
    return { contexto: "columna", clausula: cl };
  }

  function contextoFrom(cl, seg) {
    let s = seg;
    if (cl === "FROM" || cl === "UPDATE") {
      let lc = -1;
      s.forEach((t, k) => { if (esP(t, ",")) lc = k; });
      if (lc >= 0) s = s.slice(lc + 1);
    }
    const unidades = [];
    for (let i = 0; i < s.length; i++) {
      const t = s[i];
      if (esP(t, "(")) {
        let j = i + 1;
        while (j < s.length && !esP(s[j], ")")) j++;
        unidades.push({ t: "grp" });
        i = j;
        continue;
      }
      if (esIdCualquiera(t) && esP(s[i + 1], ".") && esIdCualquiera(s[i + 2])) { unidades.push(s[i + 2]); i += 2; continue; }
      unidades.push(t);
    }
    const n = unidades.length, ult = unidades[n - 1];
    const lista = KW_TRAS_TABLA[cl === "STRAIGHT_JOIN" ? "JOIN" : cl] || KW_TRAS_TABLA.FROM;
    if (n === 0) return { contexto: "tabla", clausula: cl };
    if (ult.t === "w" && MODIF_JOIN.has(ult.u)) return { contexto: "palabras", lista: ["JOIN", "OUTER JOIN"], clausula: cl };
    if (n === 1) return { contexto: "palabras", lista: ["AS"].concat(lista), min: 3, clausula: cl };
    if (esPal(ult, "AS")) return { contexto: "alias", clausula: cl };
    return { contexto: "palabras", lista, min: 3, clausula: cl };
  }

  function apertura(A, gi, nivel) {
    const gr = A.grupos[gi.cg];
    const abre = A.toks[gr.abre];
    const previos = A.toks.filter((t) => t.g === abre.g && t.e <= abre.s);
    const p1 = previos[previos.length - 1];
    const u1 = p1 && p1.t === "w" ? p1.u : null;
    const ult = nivel[nivel.length - 1];
    let base = "expr", tabla = null;
    if (u1 && /^(EXISTS|FROM|JOIN|STRAIGHT_JOIN|ANY|SOME|ALL|AS|UNION|EXCEPT|INTERSECT|LATERAL)$/.test(u1)) base = "sub";
    else if (u1 === "VALUES" || u1 === "VALUE") base = "valores";
    else if (u1 === "USING") base = "using";
    else if (esId(p1)) {
      let j = previos.length - 2;
      if (esP(previos[j], ".")) j -= 2;
      if (esPal(previos[j], "INTO")) { base = "insert"; tabla = p1.v; }
      else if (esPal(previos[j], "VIEW") || esPal(previos[j], "TABLE") || esPal(previos[j], "WITH")) base = "nada";
    }
    if (base === "nada") return { contexto: "nada" };
    if (base === "sub") return nivel.length ? expresion(nivel, null) : { contexto: "palabras", lista: ["SELECT", "WITH"], min: 0 };
    const tras = !nivel.length || esP(ult, ",");
    if (base === "valores") return tras || !terminaValor(ult, nivel[nivel.length - 2]) ? { contexto: "valores" } : { contexto: "nada" };
    if (base === "insert") return tras ? { contexto: "insert_cols", tabla } : { contexto: "nada" };
    if (base === "using") return tras ? { contexto: "using", usingTok: p1 } : { contexto: "nada" };
    if (!nivel.length) return { contexto: "columna", funcion: u1 };
    return expresion(nivel, null);
  }

  function determinarContexto(A, gi, antes) {
    const nivel = antes.filter((t) => t.g === gi.cg);
    let k = nivel.length - 1, cl = null;
    for (; k >= 0; k--) {
      const t = nivel[k];
      if (t.t !== "w") continue;
      if (t.u === "AS") { if (esAsDeVista(nivel, k)) { cl = "VIEW_AS"; break; } continue; }
      if (!CLAUSULAS.has(t.u)) continue;
      if ((t.u === "REPLACE" || t.u === "INSERT") && esP(nivel[k + 1], "(")) continue; // funciones REPLACE()/INSERT()
      if (t.u === "REPLACE" && esPal(nivel[k - 1], "OR")) continue; // CREATE OR REPLACE
      if (t.u === "FROM" && dentroDeFuncionEspecial(A, t)) continue;
      if (t.u === "UPDATE" && esPal(nivel[k - 1], "KEY")) continue;
      if (t.u === "ON" && esPal(nivel[k + 1], "DUPLICATE")) continue;
      cl = t.u;
      break;
    }
    const seg = cl ? nivel.slice(k + 1) : nivel;
    const ult = nivel[nivel.length - 1];
    const primera = nivel[0] && nivel[0].t === "w" ? nivel[0].u : null;
    const soloIfExists = (s) => s.every((t) => esPal(t, "IF") || esPal(t, "EXISTS"));

    if (!cl) {
      if (gi.cg !== 0) return apertura(A, gi, nivel);
      if (!nivel.length) return { contexto: "palabras", lista: KW_INICIO, inicio: true };
      if (primera === "CREATE") return { contexto: "palabras", lista: ["VIEW", "OR REPLACE VIEW", "REPLACE VIEW", "TABLE"] };
      if (primera === "DROP" || primera === "ALTER") return { contexto: "palabras", lista: ["VIEW", "TABLE", "IF EXISTS"] };
      return expresion(nivel, null);
    }
    switch (cl) {
      case "FROM": case "JOIN": case "STRAIGHT_JOIN": case "UPDATE":
        return contextoFrom(cl, seg);
      case "INTO":
        return seg.length ? { contexto: "palabras", lista: ["VALUES", "SELECT", "SET"], clausula: cl } : { contexto: "tabla", clausula: cl };
      case "TABLE":
        if (primera === "CREATE") return { contexto: "nada" };
        return soloIfExists(seg) ? { contexto: "tabla", solo: "tabla", clausula: cl } : { contexto: "nada" };
      case "REFERENCES":
        return seg.length ? { contexto: "nada" } : { contexto: "tabla", solo: "tabla", clausula: cl };
      case "VIEW":
        if (primera === "CREATE") return seg.length === 1 ? { contexto: "palabras", lista: ["AS"] } : { contexto: "nada" };
        if (soloIfExists(seg)) return { contexto: "tabla", solo: "vista", clausula: cl };
        return seg.length === 1 ? { contexto: "palabras", lista: ["AS"] } : { contexto: "nada" };
      case "VIEW_AS":
        return seg.length ? expresion(nivel, null) : { contexto: "palabras", lista: ["SELECT", "WITH"], min: 0 };
      case "ON":
        if (!seg.length) return { contexto: "join_on", on: nivel[k], clausula: cl };
        return expresion(nivel, cl);
      case "USING": case "LIMIT": case "OFFSET": case "VALUES":
        return { contexto: "nada" };
      case "DELETE":
        return { contexto: "palabras", lista: ["FROM"] };
      case "INSERT": case "REPLACE":
        return { contexto: "palabras", lista: ["INTO"] };
      case "UNION": case "EXCEPT": case "INTERSECT":
        return { contexto: "palabras", lista: ["SELECT", "ALL", "DISTINCT"] };
      case "WITH":
        if (ult && esP(ult, ")")) return { contexto: "palabras", lista: ["SELECT"] };
        return seg.length === 1 ? { contexto: "palabras", lista: ["AS"] } : { contexto: "nada" };
      default: // SELECT, WHERE, BY, HAVING, SET
        return expresion(nivel, cl);
    }
  }

  // Dentro de un string: ¿es la comparación de una columna ENUM?
  function contextoEnum(A, str, gi) {
    const g = str.g;
    const nivel = A.toks.filter((t) => t.g === g && t.e <= str.s);
    const esComp = (t) => !!t && ((t.t === "o" && /^(=|<>|!=|<=>)$/.test(t.v)) || esPal(t, "LIKE"));
    const refCol = (arr, k) => {
      const a = arr[k - 1];
      if (!esId(a)) return null;
      if (esP(arr[k - 2], ".") && esIdCualquiera(arr[k - 3])) return { calif: arr[k - 3].v, col: a.v };
      return { calif: null, col: a.v };
    };
    let k = nivel.length - 1, cref = null;
    const ult = nivel[k];
    if (esComp(ult)) {
      cref = refCol(nivel, k);
      if (!cref && esPal(ult, "LIKE") && esPal(nivel[k - 1], "NOT")) cref = refCol(nivel, k - 1);
    } else {
      // col IN ('a', 'b', '|
      if (ult && !esP(ult, ",")) return null;
      while (k >= 0 && (esP(nivel[k], ",") || nivel[k].t === "s" || nivel[k].t === "n")) k--;
      if (k >= 0) return null;
      const gr = A.grupos[g];
      if (!gr || gr.abre < 0) return null;
      const abre = A.toks[gr.abre];
      const prev = A.toks.filter((t) => t.g === abre.g && t.e <= abre.s);
      let pk = prev.length - 1;
      if (!esPal(prev[pk], "IN")) return null;
      if (esPal(prev[pk - 1], "NOT")) pk--;
      cref = refCol(prev, pk);
    }
    if (!cref) return null;
    const vis = visibles(A, gi);
    const fuentes = [];
    const agregar = (cols) => cols.forEach((c) => { if (eqi(c.nombre, cref.col) && c.valores && c.valores.length) fuentes.push(c); });
    if (cref.calif) {
      const r = resolverCalif(A, cref.calif, vis);
      if (r) agregar(columnasDe(A, r));
    } else {
      vis.forEach((r) => agregar(columnasDe(A, r)));
      if (!fuentes.length) A.refs.forEach((r) => agregar(columnasDe(A, r)));
      if (!fuentes.length) A.idx.lista.forEach((t) => agregar(t.cols));
    }
    if (!fuentes.length) return null;
    const valores = [], vistos = new Set();
    fuentes.forEach((c) => c.valores.forEach((v) => {
      if (vistos.has(v)) return;
      vistos.add(v);
      valores.push({ v, origen: c.tabla + "." + c.nombre });
    }));
    return {
      contexto: "enum",
      columna: (cref.calif ? cref.calif + "." : "") + cref.col,
      valores,
      comilla: str.q,
      prefijo: A.texto.slice(str.s + 1, A.pos),
      palabra: str.abierto ? A.texto.slice(str.s + 1, A.pos) : str.v,
      desde: str.s + 1,
      hasta: str.abierto ? A.pos : str.e,
    };
  }

  // ---------------------------------------------------------------- Análisis principal
  function analizarInterno(texto, pos) {
    texto = texto == null ? "" : String(texto);
    pos = pos == null ? texto.length : Math.max(0, Math.min(texto.length, Math.floor(pos)));
    const nada = (motivo, A, gi) => ({ an: { contexto: "nada", motivo, prefijo: "", palabra: "", desde: pos, hasta: pos }, A: A || null, gi: gi || null });
    const idx = indice();
    const todos = tokenizar(texto);

    // ¿el cursor está dentro de un comentario, string o `identificador`?
    let dentro = null;
    for (const t of todos) {
      if (t.s >= pos) break;
      if ((t.t === "c" || t.t === "s" || t.t === "q") && (pos < t.e || (pos === t.e && (t.linea || t.abierto)))) { dentro = t; break; }
    }
    if (dentro && dentro.t === "c") return nada("comentario");

    // sentencia actual (entre ';')
    const sents = [];
    let ini = 0, cur = [];
    for (const t of todos) {
      if (esP(t, ";")) { sents.push({ s: ini, e: t.s, toks: cur }); ini = t.e; cur = []; }
      else if (t.t !== "c") cur.push(t);
    }
    sents.push({ s: ini, e: texto.length, toks: cur });
    let st = sents[sents.length - 1];
    for (const x of sents) if (pos >= x.s && pos <= x.e) { st = x; break; }

    const A = { texto, pos, toks: st.toks, idx, sentencia: { desde: st.s, hasta: st.e } };
    A.grupos = estructurar(A.toks);
    const ex = extraerTablas(A);
    A.refs = ex.refs;
    A.ctes = ex.ctes;

    if (dentro && dentro.t === "q") return nada("identificador", A);
    if (dentro && dentro.t === "s") {
      const gi = grupoEn(A, dentro.s);
      const en = contextoEnum(A, dentro, gi);
      return en ? { an: en, A, gi } : nada("string", A, gi);
    }

    // palabra bajo el cursor
    let ws = pos, we = pos;
    while (ws > st.s && WCH.test(texto.charAt(ws - 1))) ws--;
    while (we < st.e && WCH.test(texto.charAt(we))) we++;
    const prefijo = texto.slice(ws, pos), palabra = texto.slice(ws, we);
    if (/^[0-9]/.test(prefijo) || texto.charAt(ws - 1) === "@") return nada("número", A);

    // ¿alias.columna?
    let calif = null, cIni = ws;
    if (texto.charAt(ws - 1) === ".") {
      let tq = null;
      for (const t of A.toks) { if (t.s >= ws) break; if (t.e === ws - 1) tq = t; }
      if (!tq || (tq.t !== "w" && tq.t !== "q")) return nada("punto", A);
      calif = tq.v;
      cIni = tq.s;
    }
    const gi = grupoEn(A, cIni);
    const antes = A.toks.filter((t) => t.e <= cIni);
    const base = determinarContexto(A, gi, antes);
    let an;
    if (calif) {
      if (base.contexto === "tabla") an = Object.assign({}, base, { base: calif });
      else an = { contexto: "calificada", calificador: calif, trasOn: base.contexto === "join_on" ? base.on : null, clausula: base.clausula };
    } else an = base;
    an.prefijo = prefijo;
    an.palabra = palabra;
    an.desde = ws;
    an.hasta = we;
    an.calIni = cIni;
    return { an, A, gi };
  }

  // Versión "limpia" para inspección/pruebas
  function analizar(texto, pos) {
    const r = analizarInterno(texto, pos);
    const an = r.an, out = {};
    Object.keys(an).forEach((k) => {
      const v = an[k];
      if (k === "on" || k === "trasOn" || k === "usingTok") return;
      if (k === "valores") { out.valores = v.map((x) => x.v); return; }
      if (k === "lista") { out.lista = v.slice(0, 8); return; }
      out[k] = v;
    });
    if (r.A) {
      const vis = r.gi ? visibles(r.A, r.gi) : [];
      out.tablas = r.A.refs.map((x) => ({
        nombre: x.tabla ? x.tabla.nombre : x.nombre, alias: x.alias, tipo: x.tipo, clausula: x.kw,
        visible: vis.indexOf(x) >= 0, columnas: columnasDe(r.A, x).map((c) => c.nombre),
      }));
      out.ctes = Object.keys(r.A.ctes);
    }
    return out;
  }

  // ---------------------------------------------------------------- Candidatos
  function itemColumna(c, text, display, tablasTxt) {
    const kind = c.pk ? "pk" : c.fk ? "fk" : "col";
    let det = tablasTxt || c.tabla || "";
    const tipo = tipoCorto(c.tipo);
    if (tipo) det += (det ? " · " : "") + tipo;
    if (c.fk) det += " → " + c.fk;
    return {
      kind, etiqueta: kind === "pk" ? "PK" : kind === "fk" ? "FK" : "COL",
      text, display: display || text, claves: [c.nombre], detalle: det, rango: 1,
      titulo: c.valores ? "Valores: " + c.valores.join(", ") : "",
    };
  }
  function palabras(lista, rango) {
    return lista.map((k) => ({
      kind: "kw", etiqueta: "KW", text: k, display: k, claves: [k], detalle: "", rango: rango == null ? 3 : rango,
      espacio: !SIN_ESPACIO.has(k), redisparar: REDISPARA.has(k),
    }));
  }
  function funciones() {
    const out = FUNCIONES.map((f) => ({
      kind: "func", etiqueta: "FN", text: f[0], display: f[1], claves: [f[0]], detalle: f[2], rango: 2, sinArgs: !!f[3],
    }));
    out.push({ kind: "func", etiqueta: "FN", text: SNIPPET_CASE.nombre, display: SNIPPET_CASE.display, claves: ["CASE"],
      detalle: "condicional", rango: 2, snippet: SNIPPET_CASE.texto, cursor: SNIPPET_CASE.cursor });
    return out;
  }
  function resumenTablas(ts) {
    if (ts.length <= 2) return ts.join(", ");
    return ts.slice(0, 2).join(", ") + " +" + (ts.length - 2);
  }

  function tablasRelacionadas(A, gi) {
    const out = new Set();
    const par = gi.cadena[0];
    const presentes = A.refs.filter((r) => r.g === par[0] && r.sg === par[1] && r.tabla && r.tipo === "tabla" && r.kw !== "INTO" && r.i < A.pos);
    presentes.forEach((r) => {
      const t = r.tabla.nombre.toLowerCase();
      A.idx.fks.forEach((fk) => {
        if (String(fk.tabla).toLowerCase() === t) out.add(String(fk.ref_tabla).toLowerCase());
        if (String(fk.ref_tabla).toLowerCase() === t) out.add(String(fk.tabla).toLowerCase());
      });
    });
    return out;
  }
  function candTablas(A, gi, an) {
    const items = [];
    Object.keys(A.ctes).forEach((k) => {
      const c = A.ctes[k];
      items.push({ kind: "cte", etiqueta: "CTE", text: quoteId(c.nombre), display: c.nombre, claves: [c.nombre], detalle: "consulta WITH", rango: 0 });
    });
    const rel = an.clausula === "JOIN" || an.clausula === "STRAIGHT_JOIN" || an.clausula === "FROM" ? tablasRelacionadas(A, gi) : new Set();
    A.idx.lista.forEach((t) => {
      if (an.solo && an.solo !== t.tipo) return;
      const vista = t.tipo === "vista", esRel = rel.has(t.nombre.toLowerCase());
      items.push({
        kind: vista ? "vista" : "tabla", etiqueta: vista ? "VW" : "TAB", text: quoteId(t.nombre), display: t.nombre, claves: [t.nombre],
        detalle: vista ? "vista" : "tabla · " + fmtNum(t.filas) + " filas" + (esRel ? " · FK" : ""),
        rango: esRel ? 0.5 : vista ? 1.5 : 1,
      });
    });
    return items;
  }

  function candColumnas(A, gi, an, manual) {
    const p = an.prefijo || "";
    const vis = visibles(A, gi).filter((r) => columnasDe(A, r).length);
    const items = [];
    if (vis.length) {
      const usaAlias = vis.some((r) => r.alias);
      const cuenta = {};
      vis.forEach((r) => columnasDe(A, r).forEach((c) => { const k = c.nombre.toLowerCase(); cuenta[k] = (cuenta[k] || 0) + 1; }));
      vis.forEach((r) => {
        const q = r.alias || r.nombre;
        columnasDe(A, r).forEach((c) => {
          const calificar = !!q && (usaAlias || cuenta[c.nombre.toLowerCase()] > 1);
          const text = (calificar ? quoteId(q) + "." : "") + quoteId(c.nombre);
          items.push(itemColumna(c, text, text));
        });
      });
    } else if (p.length >= 2) {
      // todavía no hay tablas: columnas de todas las tablas (agrupadas por nombre)
      const porNombre = new Map();
      A.idx.lista.forEach((t) => t.cols.forEach((c) => {
        const k = c.nombre.toLowerCase();
        if (!porNombre.has(k)) porNombre.set(k, { c, tablas: [] });
        porNombre.get(k).tablas.push(t.nombre);
      }));
      porNombre.forEach((x) => items.push(itemColumna(x.c, quoteId(x.c.nombre), x.c.nombre, resumenTablas(x.tablas))));
    }
    if (an.clausula === "BY" || an.clausula === "HAVING") {
      aliasDelSelect(A, gi).forEach((al) => items.push({ kind: "alias", etiqueta: "AS", text: quoteId(al), display: al, claves: [al], detalle: "alias del SELECT", rango: 0.5 }));
    }
    if (p.length >= 1 || (manual && !items.length)) {
      funciones().forEach((f) => items.push(f));
      palabras(KW_GENERAL).forEach((k) => items.push(k));
    }
    return items;
  }

  function fkEntre(A, o, n) {
    const qo = o.alias || o.nombre, qn = n.alias || n.nombre;
    if (!qo || !qn) return [];
    const to = o.tabla && o.tipo === "tabla" ? o.tabla.nombre.toLowerCase() : null;
    const tn = n.tabla && n.tipo === "tabla" ? n.tabla.nombre.toLowerCase() : null;
    const out = [];
    if (to && tn) {
      A.idx.fks.forEach((fk) => {
        const ft = String(fk.tabla).toLowerCase(), fr = String(fk.ref_tabla).toLowerCase();
        const det = "FK · " + fk.tabla + "." + fk.columna + " → " + fk.ref_tabla;
        if (ft === tn && fr === to) out.push({ izq: [qo, fk.ref_columna], der: [qn, fk.columna], det });
        if (ft === to && fr === tn) out.push({ izq: [qo, fk.columna], der: [qn, fk.ref_columna], det });
      });
    } else {
      // vistas / subconsultas: no tienen FK, se emparejan columnas id_* con el mismo nombre
      const cn = columnasDe(A, n);
      columnasDe(A, o).forEach((a) => {
        if (!/^id_/i.test(a.nombre)) return;
        const b = cn.find((b) => eqi(b.nombre, a.nombre));
        if (b) out.push({ izq: [qo, a.nombre], der: [qn, b.nombre], det: "mismo nombre de columna" });
      });
    }
    return out;
  }
  function condicionesJoin(A, onTok) {
    if (!onTok) return [];
    let nueva = null;
    A.refs.forEach((r) => {
      if ((r.kw === "JOIN" || r.kw === "STRAIGHT_JOIN") && r.g === onTok.g && r.sg === onTok.sg && r.i < onTok.i && (!nueva || r.i > nueva.i)) nueva = r;
    });
    if (!nueva) return [];
    const otras = A.refs.filter((r) => r !== nueva && r.g === nueva.g && r.sg === nueva.sg && r.i < nueva.i && r.kw !== "INTO").reverse();
    const out = [], vistos = new Set();
    otras.forEach((o) => fkEntre(A, o, nueva).forEach((cd) => {
      const k = (cd.izq.join(".") + "=" + cd.der.join(".")).toLowerCase();
      if (!vistos.has(k)) { vistos.add(k); out.push(cd); }
    }));
    return out;
  }
  const textoCond = (izq, der) => quoteId(izq[0]) + "." + quoteId(izq[1]) + " = " + quoteId(der[0]) + "." + quoteId(der[1]);
  function candJoin(A, onTok) {
    return condicionesJoin(A, onTok).map((cd) => {
      const text = textoCond(cd.izq, cd.der);
      return { kind: "join", etiqueta: "JOIN", text, display: text, claves: [text, cd.izq[1], cd.der[1]], detalle: cd.det, rango: 0 };
    });
  }
  function candCalificada(A, gi, an) {
    const vis = visibles(A, gi);
    const ref = resolverCalif(A, an.calificador, vis);
    if (!ref) return [];
    const items = columnasDe(A, ref).map((c) => itemColumna(c, quoteId(c.nombre), c.nombre));
    if (an.trasOn) {
      condicionesJoin(A, an.trasOn).forEach((cd) => {
        let izq = cd.izq, der = cd.der;
        if (eqi(der[0], an.calificador) && !eqi(izq[0], an.calificador)) { const t = izq; izq = der; der = t; }
        else if (!eqi(izq[0], an.calificador)) return;
        const text = textoCond(izq, der);
        items.push({ kind: "join", etiqueta: "JOIN", text, display: text, claves: [izq[1]], detalle: cd.det, rango: 0, from: an.calIni, to: an.hasta });
      });
    }
    return items;
  }
  function candInsert(A, gi, an) {
    const t = A.idx.tablas[String(an.tabla || "").toLowerCase()];
    if (!t) return [];
    const ya = new Set(A.toks.filter((x) => x.g === gi.cg && esIdCualquiera(x) && x.s !== an.desde).map((x) => x.v.toLowerCase()));
    return t.cols.filter((c) => !ya.has(c.nombre.toLowerCase())).map((c) => itemColumna(c, quoteId(c.nombre)));
  }
  function candUsing(A, an) {
    const tok = an.usingTok;
    let nueva = null;
    A.refs.forEach((r) => { if ((r.kw === "JOIN" || r.kw === "STRAIGHT_JOIN") && tok && r.g === tok.g && r.i < tok.i && (!nueva || r.i > nueva.i)) nueva = r; });
    if (!nueva) return [];
    const otras = A.refs.filter((r) => r !== nueva && r.g === nueva.g && r.sg === nueva.sg && r.i < nueva.i);
    const nombres = new Set();
    otras.forEach((o) => columnasDe(A, o).forEach((c) => nombres.add(c.nombre.toLowerCase())));
    const cols = columnasDe(A, nueva);
    const comunes = cols.filter((c) => nombres.has(c.nombre.toLowerCase()));
    return (comunes.length ? comunes : cols).map((c) => itemColumna(c, quoteId(c.nombre)));
  }

  function candidatos(r, manual) {
    const an = r.an, A = r.A, gi = r.gi;
    if (!A) return [];
    switch (an.contexto) {
      case "tabla": return candTablas(A, gi, an);
      case "columna": return candColumnas(A, gi, an, manual);
      case "join_on": return candJoin(A, an.on).concat(candColumnas(A, gi, an, manual));
      case "calificada": return candCalificada(A, gi, an);
      case "palabras": return palabras(an.lista, 0);
      case "enum":
        return an.valores.map((x) => ({
          kind: "enum", etiqueta: "VAL", text: x.v + an.comilla, display: x.v, claves: [x.v], detalle: x.origen, rango: 0,
        }));
      case "insert_cols": return candInsert(A, gi, an);
      case "using": return candUsing(A, an);
      case "valores": return an.prefijo || manual ? funciones().concat(palabras(["NULL", "DEFAULT", "TRUE", "FALSE"])) : [];
      default: return [];
    }
  }

  // ---------------------------------------------------------------- Filtrado y orden
  const CONTIENE = new Set(["col", "pk", "fk", "tabla", "vista", "cte", "enum", "join", "alias"]);
  function puntuar(clave, q, contiene) {
    if (!q) return 1;
    const k = String(clave).toLowerCase();
    if (k === q) return 0;
    if (k.indexOf(q) === 0) return 1;
    if (k.indexOf("_" + q) >= 0 || k.indexOf(" " + q) >= 0 || k.indexOf("." + q) >= 0) return 2;
    if (contiene && k.indexOf(q) >= 0) return 3;
    return -1;
  }
  function marcar(display, clave, q) {
    if (!q) return null;
    const d = display.toLowerCase(), k = String(clave).toLowerCase();
    const base = d.indexOf(k);
    if (base >= 0) {
      let off = k.indexOf(q) === 0 ? 0 : -1;
      if (off < 0) for (const sep of ["_", " ", "."]) { const j = k.indexOf(sep + q); if (j >= 0) { off = j + 1; break; } }
      if (off < 0) off = k.indexOf(q);
      if (off >= 0) return [base + off, base + off + q.length];
    }
    const j = d.indexOf(q);
    return j >= 0 ? [j, j + q.length] : null;
  }
  const MIN_AUTO = { tabla: 0, calificada: 0, enum: 0, join_on: 0 };

  function sugerencias(texto, pos, opts) {
    opts = opts || {};
    const r = analizarInterno(texto, pos);
    const an = r.an;
    const out = { contexto: an.contexto, prefijo: an.prefijo || "", from: an.desde, to: an.hasta, list: [] };
    const items = candidatos(r, !opts.auto);
    if (!items.length) return out;
    const q = (an.prefijo || "").toLowerCase();
    const lista = [];
    items.forEach((it, n) => {
      let tier = -1, clave = null;
      (it.claves || [it.text]).forEach((k) => {
        const t = puntuar(k, q, CONTIENE.has(it.kind));
        if (t >= 0 && (tier < 0 || t < tier)) { tier = t; clave = k; }
      });
      if (tier < 0) return;
      it.tier = tier;
      it.orden = n;
      it.marca = marcar(it.display, clave, q);
      lista.push(it);
    });
    lista.sort((a, b) => a.tier - b.tier || a.rango - b.rango || a.orden - b.orden);
    const vistos = new Set(), final = [];
    lista.forEach((it) => {
      const k = it.text.toLowerCase();
      if (vistos.has(k)) return;
      vistos.add(k);
      final.push(it);
    });
    if (opts.auto) {
      const min = an.contexto === "palabras" ? (an.min != null ? an.min : 2) : (MIN_AUTO[an.contexto] != null ? MIN_AUTO[an.contexto] : 2);
      if ((an.prefijo || "").length < min) return out;
      // si lo escrito ya es exactamente una sugerencia, no molestar (Enter = nueva línea)
      const pal = (an.palabra || "").toLowerCase();
      if (pal && final.some((it) => (it.claves || []).some((k) => String(k).toLowerCase() === pal))) return out;
    }
    out.list = final.slice(0, 200);
    return out;
  }

  // ---------------------------------------------------------------- CodeMirror
  function renderItem(el, data, comp) {
    const it = comp._it || {};
    const doc = el.ownerDocument || document;
    const ico = doc.createElement("span");
    ico.className = "ac-ico";
    ico.textContent = it.etiqueta || "";
    el.appendChild(ico);
    const txt = doc.createElement("span");
    txt.className = "ac-txt";
    const d = it.display || comp.text, m = it.marca;
    if (m && m[1] > m[0]) {
      txt.appendChild(doc.createTextNode(d.slice(0, m[0])));
      const b = doc.createElement("b");
      b.textContent = d.slice(m[0], m[1]);
      txt.appendChild(b);
      txt.appendChild(doc.createTextNode(d.slice(m[1])));
    } else txt.textContent = d;
    el.appendChild(txt);
    if (it.detalle) {
      const det = doc.createElement("span");
      det.className = "ac-det";
      det.textContent = it.detalle;
      el.appendChild(det);
    }
    if (it.titulo) el.title = it.titulo;
  }

  function aplicar(cm, data, comp) {
    const it = comp._it || {};
    const from = comp.from || data.from, to = comp.to || data.to;
    const sig = cm.getRange(to, { line: to.line, ch: to.ch + 1 });
    let texto = comp.text, cursor = null;
    if (it.kind === "func") {
      if (it.snippet) { texto = it.snippet; cursor = it.cursor; }
      else if (sig === "(") { texto = it.text; cursor = texto.length + 1; }
      else { texto = it.text + "()"; cursor = it.sinArgs ? texto.length : texto.length - 1; }
    } else if (it.kind === "kw" && it.espacio && !/\s/.test(sig)) {
      texto += " ";
    }
    cm.replaceRange(texto, from, to, "complete");
    if (cursor != null) cm.setCursor(cm.posFromIndex(cm.indexFromPos(from) + cursor));
    if (it.redisparar) setTimeout(() => { try { abrirSiHay(cm, ["tabla", "join_on"]); } catch (e) { /* nada */ } }, 0);
  }

  function hint(cm, options) {
    try {
      const r = sugerencias(cm.getValue(), cm.indexFromPos(cm.getCursor()), { auto: !!(options && options.auto) });
      if (!r.list.length) return null;
      const P = (o) => cm.posFromIndex(o);
      return {
        from: P(r.from),
        to: P(r.to),
        list: r.list.map((it) => ({
          text: it.text,
          displayText: it.display,
          className: "ac-item ac-k-" + it.kind,
          render: renderItem,
          hint: aplicar,
          from: it.from != null ? P(it.from) : undefined,
          to: it.to != null ? P(it.to) : undefined,
          _it: it,
        })),
      };
    } catch (e) {
      if (window.console) console.warn("[autocompletar]", e);
      return null;
    }
  }

  function abrir(cm, auto) {
    cm.showHint({ hint, completeSingle: false, auto: !!auto });
  }
  // Abre la lista (en modo automático) solo si hay algo para mostrar en alguno de los contextos pedidos
  function abrirSiHay(cm, contextos) {
    if (!cm || cm.somethingSelected()) return false;
    const r = sugerencias(cm.getValue(), cm.indexFromPos(cm.getCursor()), { auto: true });
    if (!r.list.length) return false;
    if (contextos && contextos.indexOf(r.contexto) < 0) return false;
    abrir(cm, true);
    return true;
  }

  function alEscribir(cm, ch) {
    if (ch.origin !== "+input" || cm.getOption("readOnly")) return;
    if (ch.text.length !== 1 || ch.text[0].length !== 1) return;
    if (cm.somethingSelected() || cm.listSelections().length > 1) return;
    const c = ch.text[0];
    if (WCH.test(c)) {
      if (cm.state.completionActive) return; // la lista abierta se actualiza sola
      const cur = cm.getCursor(), antes = cm.getLine(cur.line).slice(0, cur.ch);
      const m = /[A-Za-z0-9_$À-￿]+$/.exec(antes);
      if (!m || /^[0-9]/.test(m[0])) return;
      const trasPunto = antes.charAt(m.index - 1) === ".";
      if (m[0].length >= (trasPunto ? 1 : 2)) abrirSiHay(cm, null);
    } else if (c === ".") {
      abrirSiHay(cm, ["calificada", "tabla"]);
    } else if (c === " ") {
      abrirSiHay(cm, ["tabla", "join_on"]);
    } else if (c === "'" || c === '"') {
      abrirSiHay(cm, ["enum"]);
    }
  }

  function instalar(cm) {
    if (!cm || cm.state.acInstalado) return;
    cm.state.acInstalado = true;
    cm.on("inputRead", (c, ch) => {
      try { alEscribir(c, ch); } catch (e) { if (window.console) console.warn("[autocompletar]", e); }
    });
    // closebrackets inserta '' sin pasar por inputRead: detectar la comilla de apertura acá
    cm.on("change", (c, ch) => {
      try {
        if (ch.origin == null && ch.text.length === 1 && (ch.text[0] === "''" || ch.text[0] === '""') && !ch.removed.join("")) {
          abrirSiHay(c, ["enum"]);
        }
      } catch (e) { if (window.console) console.warn("[autocompletar]", e); }
    });
  }

  // ---------------------------------------------------------------- Pruebas rápidas
  function probar(conBarra, opts) {
    const i = conBarra.indexOf("|");
    const texto = i < 0 ? conBarra : conBarra.slice(0, i) + conBarra.slice(i + 1);
    const r = sugerencias(texto, i < 0 ? texto.length : i, opts);
    const max = (opts && opts.max) || 12;
    return {
      contexto: r.contexto,
      n: r.list.length,
      items: r.list.slice(0, max).map((it) => it.text + (it.display !== it.text ? "  {" + it.display + "}" : "") + "  [" + it.kind + "] " + (it.detalle || "")),
    };
  }

  window.Autocompletar = { hint, analizar, sugerencias, instalar, abrir, abrirSiHay, probar, tokenizar, usarEsquema };
})();
