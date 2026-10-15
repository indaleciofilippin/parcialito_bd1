window.Vistas = window.Vistas || {};

// Disposición calculada para minimizar cruces de líneas: tablas "padre" a la izquierda,
// las que dependen de ellas a la derecha (las FK van de derecha a izquierda).
const ER_POS = {
  correlatividades: [20, 140], docente_asignatura: [20, 280], departamentos: [20, 510],
  asignaturas: [300, 180], docentes: [300, 380], aulas: [300, 600], carreras: [300, 750],
  comisiones: [580, 210], mesas_finales: [580, 450],
  examenes: [860, 20], asistencias: [860, 180], inscripcion_alumno_comision: [860, 350], inscripciones_finales: [860, 520], alumno_carrera: [860, 720],
  notas: [1140, 30], alumnos: [1140, 370],
};
const ER_COLOR = {
  alumnos: "#2563eb", docentes: "#2563eb",
  asignaturas: "#7c3aed", correlatividades: "#7c3aed", comisiones: "#7c3aed", docente_asignatura: "#7c3aed",
  inscripcion_alumno_comision: "#0d9488", alumno_carrera: "#0d9488", inscripciones_finales: "#0d9488",
  examenes: "#e11d48", notas: "#e11d48", asistencias: "#e11d48", mesas_finales: "#d97706",
  aulas: "#475569", departamentos: "#475569", carreras: "#059669",
};
const ER_DESC = {
  departamentos: "Departamentos académicos (Ingeniería, Ciencias Exactas, …) con su presupuesto.",
  aulas: "Aulas físicas: capacidad y tipo (normal, laboratorio, centro de cómputos).",
  carreras: "Carreras que ofrece cada departamento (nivel, modalidad, duración).",
  docentes: "Plantel docente: salario base y departamento al que pertenecen.",
  asignaturas: "Materias: créditos, carga horaria, si son obligatorias y su departamento.",
  alumnos: "Datos personales de los alumnos.",
  alumno_carrera: "Tabla intermedia N a N: en qué carrera(s) está cada alumno y en qué estado.",
  correlatividades: "Auto-relación de asignaturas: id_asignatura tiene como correlativa a id_asignatura_correlativa.",
  docente_asignatura: "Asignación de docentes a asignaturas por año/cuatrimestre, con horas asignadas y monto pagado.",
  comisiones: "Cada dictado de una asignatura: docente a cargo, aula, año, cuatrimestre, cupo y tipo.",
  inscripcion_alumno_comision: "Inscripciones de alumnos a comisiones, con su estado de cursado.",
  asistencias: "Asistencia de cada alumno a cada clase de una comisión (presente = 1 / 0).",
  examenes: "Parciales y recuperatorios tomados en cada comisión.",
  notas: "Nota de cada alumno en cada examen.",
  mesas_finales: "Mesas de examen final: asignatura, docente, aula, fecha, turno y llamado.",
  inscripciones_finales: "Inscripciones de alumnos a mesas finales, con estado y nota.",
};
const ER_W = 196, ER_HEAD = 31, ER_ROW = 21;

const ER_ANCHO = 1356, ER_ALTO = 990;

// ======================================================================= Diagrama (reutilizable)
// Lo usan la página "Esquema" y la ventana flotante del DER.
Vistas.derDiagrama = {
  props: { zoom: { type: Number, default: 0.8 }, seleccion: String },
  emits: ["tabla", "columna", "doble", "fondo"],
  template: `
  <div v-if="esq" :style="{width: ER_ANCHO * zoom + 'px', height: ER_ALTO * zoom + 'px', position: 'relative'}" @click.self="$emit('fondo')">
    <div class="er-canvas" :style="{transform: 'scale(' + zoom + ')', width: ER_ANCHO + 'px', height: ER_ALTO + 'px'}" @click.self="$emit('fondo')">
      <svg class="er-svg" :width="ER_ANCHO" :height="ER_ALTO">
        <g v-for="(l, i) in lineas" :key="i">
          <path :d="l.d" :class="clsLinea(l)"/>
          <circle :cx="l.x2" :cy="l.y2" r="3.5" :class="{hi: activa(l)}"/>
        </g>
      </svg>
      <div v-for="t in tablas" :key="t" class="er-table" :class="{sel: seleccion === t, dim: foco && !relacionadas.has(t)}"
           :style="{left: ER_POS[t][0] + 'px', top: ER_POS[t][1] + 'px', '--tc': ER_COLOR[t]}"
           @mouseenter="hover = t" @mouseleave="hover = null" @click.stop="$emit('tabla', t)" @dblclick.stop="$emit('doble', t)">
        <div class="er-th" :title="ER_DESC[t]"><ico n="table" c="xs"/> {{ t }}<span class="n">{{ U.fmtNum(esq.conteos[t]) }}</span></div>
        <div v-for="c in esq.detalle[t]" class="er-col" :class="{pk: c.clave === 'PRI'}" :title="tituloCol(t, c)"
             @click.stop="$emit('columna', {tabla: t, columna: c.nombre})" @dblclick.stop="$emit('doble', c.nombre)">
          <ico :n="c.clave === 'PRI' ? 'key' : (esFk(t, c.nombre) ? 'link' : 'dot')" :c="'xs ' + (c.clave === 'PRI' ? 'k-pk' : (esFk(t, c.nombre) ? 'k-fk' : 'k-col'))"/>
          {{ c.nombre }}<span class="ty">{{ tipoCorto(c.tipo) }}</span>
        </div>
      </div>
    </div>
  </div>`,
  setup(props) {
    const { ref, computed, onMounted } = Vue;
    const esq = computed(() => U.store.esquema);
    const hover = ref(null);
    onMounted(() => { U.cargarEsquema().catch(() => {}); });
    const tablas = computed(() => Object.keys(ER_POS).filter((t) => esq.value && esq.value.detalle[t]));
    function esFk(t, c) { return esq.value.fks.some((f) => f.tabla === t && f.columna === c); }
    function fk(t, c) { return esq.value.fks.find((f) => f.tabla === t && f.columna === c); }
    function tipoCorto(t) { return t.startsWith("enum") ? "enum" : t.replace(/\(.*\)/, ""); }
    function tituloCol(t, c) {
      const partes = [t + "." + c.nombre + " · " + c.tipo];
      const f = fk(t, c.nombre);
      if (f) partes.push("FK → " + f.ref_tabla + "." + f.ref_columna);
      if (c.valores) partes.push("Valores: " + c.valores.map((v) => "'" + v + "'").join(", "));
      return partes.join("\n");
    }
    function filaY(t, col) {
      const cols = esq.value.detalle[t];
      const i = Math.max(0, cols.findIndex((c) => c.nombre === col));
      return ER_POS[t][1] + ER_HEAD + i * ER_ROW + ER_ROW / 2 + 1;
    }
    const lineas = computed(() => {
      if (!esq.value) return [];
      return esq.value.fks.filter((f) => ER_POS[f.tabla] && ER_POS[f.ref_tabla]).map((f) => {
        const [ax] = ER_POS[f.tabla], [bx] = ER_POS[f.ref_tabla];
        const y1 = filaY(f.tabla, f.columna), y2 = filaY(f.ref_tabla, f.ref_columna);
        let x1, x2, d1, d2;
        if (f.tabla === f.ref_tabla) { x1 = ax + ER_W; x2 = ax + ER_W; d1 = 50; d2 = 50; }
        else if (ax + ER_W < bx) { x1 = ax + ER_W; x2 = bx; d1 = 1; d2 = -1; }
        else if (bx + ER_W < ax) { x1 = ax; x2 = bx + ER_W; d1 = -1; d2 = 1; }
        else { x1 = ax; x2 = bx; d1 = -1; d2 = -1; }
        const k = f.tabla === f.ref_tabla ? 1 : Math.max(40, Math.abs(x2 - x1) / 2);
        return { d: `M${x1},${y1} C${x1 + d1 * k},${y1} ${x2 + d2 * k},${y2} ${x2},${y2}`, x2, y2, a: f.tabla, b: f.ref_tabla };
      });
    });
    const foco = computed(() => hover.value || props.seleccion);
    const relacionadas = computed(() => {
      const s = new Set();
      if (!foco.value || !esq.value) return s;
      s.add(foco.value);
      esq.value.fks.forEach((f) => { if (f.tabla === foco.value) s.add(f.ref_tabla); if (f.ref_tabla === foco.value) s.add(f.tabla); });
      return s;
    });
    function activa(l) { return foco.value && (l.a === foco.value || l.b === foco.value); }
    function clsLinea(l) { return foco.value ? (activa(l) ? "hi" : "dim") : ""; }
    return { U, esq, hover, tablas, lineas, foco, relacionadas, esFk, tipoCorto, tituloCol, activa, clsLinea,
             ER_POS, ER_COLOR, ER_DESC, ER_ANCHO, ER_ALTO };
  },
};

Vistas.esquema = {
  template: `
  <div class="er-wrap">
    <div class="er-canvas-wrap" ref="wrap" @click.self="sel = null">
      <div class="er-zoom">
        <button class="icon-btn" @click="zoom = Math.max(.4, zoom - .1)" title="Alejar"><ico n="minus" c="sm"/></button>
        <span class="small tnum" style="align-self:center;width:40px;text-align:center">{{ Math.round(zoom * 100) }}%</span>
        <button class="icon-btn" @click="zoom = Math.min(1.4, zoom + .1)" title="Acercar"><ico n="plus" c="sm"/></button>
        <button class="icon-btn" @click="ajustar" title="Ajustar"><ico n="expand" c="sm"/></button>
      </div>
      <div style="padding:0 20px;margin-top:-40px">
        <der-diagrama :zoom="zoom" :seleccion="sel" @tabla="seleccionar" @columna="c => seleccionar(c.tabla)" @fondo="sel = null"/>
      </div>
    </div>

    <div class="er-panel">
      <template v-if="!sel">
        <div class="page-title" style="font-size:20px">Esquema de la base</div>
        <p class="muted" style="margin:6px 0 16px">Es el mismo modelo del DER de la cátedra. Pasá el mouse por una tabla para ver con quién se relaciona; hacé clic para ver sus columnas, valores posibles y datos de ejemplo.</p>
        <div class="card pad" style="margin-bottom:16px">
          <div class="card-title" style="font-size:13.5px;margin-bottom:8px">Referencias</div>
          <div class="small" style="display:grid;gap:6px">
            <div class="row"><ico n="key" c="sm k-pk"/> Clave primaria (PK)</div>
            <div class="row"><ico n="link" c="sm k-fk"/> Clave foránea (FK): apunta a otra tabla</div>
            <div class="row"><svg width="40" height="10"><path d="M2 5 H36" stroke="var(--border-strong)" stroke-width="1.6"/><circle cx="36" cy="5" r="3.5" fill="var(--surface)" stroke="var(--border-strong)" stroke-width="1.6"/></svg> la línea termina en la tabla referenciada (lado «1»)</div>
          </div>
        </div>
        <div class="sol-block"><h4>Tablas</h4>
          <div v-for="t in tablas" class="rel" @click="seleccionar(t)"><span style="width:10px;height:10px;border-radius:3px" :style="{background: ER_COLOR[t]}"></span><b>{{ t }}</b><span class="spacer"></span><code>{{ U.fmtNum(esq ? esq.conteos[t] : 0) }}</code></div>
        </div>
        <div class="sol-block" v-if="vistas.length"><h4><ico n="eye" c="xs"/> Vistas ya creadas en tu base</h4>
          <div v-for="v in vistas" class="rel" @click="seleccionar(v)"><ico n="eye" c="sm"/><b>{{ v }}</b><span class="spacer"></span><code>{{ esq.detalle[v].length }} col.</code></div>
        </div>
      </template>
      <template v-else-if="esq">
        <div class="row" style="margin-bottom:6px">
          <button class="icon-btn" @click="sel = null"><ico n="left"/></button>
          <div class="page-title" style="font-size:19px">{{ sel }}</div>
          <span class="badge" v-if="esq.tipos[sel] === 'vista'">vista</span>
        </div>
        <p class="muted small" style="margin:0 0 12px">{{ ER_DESC[sel] || 'Vista precargada en tu base de práctica.' }} <span v-if="esq.conteos[sel] != null">· <b>{{ U.fmtNum(esq.conteos[sel]) }}</b> filas</span></p>
        <div class="row" style="margin-bottom:16px">
          <button class="btn sm primary" @click="abrirConsola"><ico n="terminal" c="xs"/> Abrir en consola</button>
          <button class="btn sm" @click="U.copiar(sel)"><ico n="copy" c="xs"/> Copiar nombre</button>
        </div>
        <div class="sol-block"><h4>Columnas</h4>
          <div v-for="c in esq.detalle[sel]" class="col-row">
            <ico :n="c.clave === 'PRI' ? 'key' : (esFk(sel, c.nombre) ? 'link' : 'dot')" :c="'sm ' + (c.clave === 'PRI' ? 'k-pk' : (esFk(sel, c.nombre) ? 'k-fk' : 'k-col'))"/>
            <span class="nm">{{ c.nombre }} <span v-if="!c.nulo" class="badge outline" style="height:17px;font-size:10px;padding:0 5px">NOT NULL</span> <span v-if="c.clave === 'UNI'" class="badge outline" style="height:17px;font-size:10px;padding:0 5px">UNIQUE</span></span>
            <span class="ty">{{ c.valores ? 'ENUM' : c.tipo }}</span>
            <div v-if="c.valores" class="enum-vals"><span v-for="v in c.valores">'{{ v }}'</span></div>
            <div v-if="fkDe(sel, c.nombre)" class="enum-vals" style="color:var(--muted);font-size:11.5px">→ {{ fkDe(sel, c.nombre).ref_tabla }}.{{ fkDe(sel, c.nombre).ref_columna }}</div>
          </div>
        </div>
        <div class="sol-block" v-if="salientes.length || entrantes.length"><h4>Relaciones</h4>
          <div v-for="f in salientes" class="rel" @click="seleccionar(f.ref_tabla)"><ico n="right" c="sm"/> <span><code>{{ f.columna }}</code> → <b>{{ f.ref_tabla }}</b></span></div>
          <div v-for="f in entrantes" class="rel" @click="seleccionar(f.tabla)"><ico n="left" c="sm"/> <span><b>{{ f.tabla }}</b>.<code>{{ f.columna }}</code> la referencia</span></div>
          <div class="small muted" style="margin-top:6px">JOIN típico: <code v-if="salientes[0]">{{ joinEjemplo }}</code></div>
        </div>
        <div class="sol-block"><h4>Primeras filas</h4>
          <div v-if="!muestra" class="spinner"></div>
          <div v-else class="mini-table" style="max-height:320px"><table class="dg"><thead><tr><th v-for="c in muestra.columnas">{{ c }}</th></tr></thead>
            <tbody><tr v-for="f in muestra.filas"><td v-for="v in f" :class="{num: typeof v === 'number', null: v === null}">{{ v === null ? 'NULL' : v }}</td></tr></tbody></table></div>
        </div>
      </template>
    </div>
  </div>`,
  setup() {
    const { ref, computed, onMounted, watch } = Vue;
    const esq = computed(() => U.store.esquema);
    const sel = ref(null);
    const hover = ref(null);
    const zoom = ref(0.8);
    const muestra = ref(null);
    const wrap = ref(null);
    onMounted(async () => { await U.cargarEsquema(); ajustar(); });
    function ajustar() {
      const w = wrap.value ? wrap.value.clientWidth : 1000;
      zoom.value = Math.max(0.45, Math.min(1, (w - 30) / ER_ANCHO));
    }
    const tablas = computed(() => Object.keys(ER_POS).filter((t) => esq.value && esq.value.detalle[t]));
    const vistas = computed(() => (esq.value ? Object.keys(esq.value.tipos).filter((t) => esq.value.tipos[t] === "vista") : []));
    function esFk(t, c) { return esq.value.fks.some((f) => f.tabla === t && f.columna === c); }
    function fkDe(t, c) { return esq.value.fks.find((f) => f.tabla === t && f.columna === c); }
    function tipoCorto(t) { return t.startsWith("enum") ? "enum" : t.replace(/\(.*\)/, "").replace("tinyint", "tinyint"); }
    function filaY(t, col) {
      const cols = esq.value.detalle[t];
      const i = Math.max(0, cols.findIndex((c) => c.nombre === col));
      return ER_POS[t][1] + ER_HEAD + i * ER_ROW + ER_ROW / 2 + 1;
    }
    const lineas = computed(() => {
      if (!esq.value) return [];
      return esq.value.fks.filter((f) => ER_POS[f.tabla] && ER_POS[f.ref_tabla]).map((f) => {
        const [ax] = ER_POS[f.tabla], [bx] = ER_POS[f.ref_tabla];
        const y1 = filaY(f.tabla, f.columna), y2 = filaY(f.ref_tabla, f.ref_columna);
        let x1, x2, d1, d2;
        if (f.tabla === f.ref_tabla) {
          x1 = ax + ER_W; x2 = ax + ER_W; d1 = 50; d2 = 50;
        } else if (ax + ER_W < bx) { x1 = ax + ER_W; x2 = bx; d1 = 1; d2 = -1; }
        else if (bx + ER_W < ax) { x1 = ax; x2 = bx + ER_W; d1 = -1; d2 = 1; }
        else { x1 = ax; x2 = bx; d1 = -1; d2 = -1; }
        const k = f.tabla === f.ref_tabla ? 1 : Math.max(40, Math.abs(x2 - x1) / 2);
        const c1 = x1 + d1 * k, c2 = x2 + d2 * k;
        return { d: `M${x1},${y1} C${c1},${y1} ${c2},${y2} ${x2},${y2}`, x2, y2, a: f.tabla, b: f.ref_tabla };
      });
    });
    const foco = computed(() => hover.value || sel.value);
    const relacionadas = computed(() => {
      const s = new Set();
      if (!foco.value || !esq.value) return s;
      s.add(foco.value);
      esq.value.fks.forEach((f) => { if (f.tabla === foco.value) s.add(f.ref_tabla); if (f.ref_tabla === foco.value) s.add(f.tabla); });
      return s;
    });
    function activa(l) { return foco.value && (l.a === foco.value || l.b === foco.value); }
    function clsLinea(l) { return foco.value ? (activa(l) ? "hi" : "dim") : ""; }
    const salientes = computed(() => (sel.value && esq.value ? esq.value.fks.filter((f) => f.tabla === sel.value) : []));
    const entrantes = computed(() => (sel.value && esq.value ? esq.value.fks.filter((f) => f.ref_tabla === sel.value) : []));
    const joinEjemplo = computed(() => {
      const f = salientes.value[0];
      if (!f) return "";
      return `${f.tabla} JOIN ${f.ref_tabla} ON ${f.ref_tabla}.${f.ref_columna} = ${f.tabla}.${f.columna}`;
    });
    async function seleccionar(t) {
      sel.value = t; muestra.value = null;
      try { muestra.value = await U.api.get("/tabla/" + t); } catch (e) { U.toast(e.message); }
    }
    function abrirConsola() { U.store.consolaSql = "SELECT *\nFROM " + sel.value + "\nLIMIT 100;"; U.irA("#/consola"); }
    return { U, esq, sel, hover, zoom, muestra, wrap, tablas, vistas, lineas, foco, relacionadas, salientes, entrantes, joinEjemplo,
             ER_POS, ER_COLOR, ER_DESC, esFk, fkDe, tipoCorto, activa, clsLinea, seleccionar, abrirConsola, ajustar };
  },
};


// ======================================================================= DER flotante
// Ventana que se puede mover, agrandar y hacer zoom, para ver el diagrama mientras resolvés.
U.toggleDer = function () {
  U.store.derAbierto = !U.store.derAbierto;
  try { localStorage.setItem("parc-der-abierto", U.store.derAbierto ? "1" : "0"); } catch (e) {}
};

Vistas.derFlotante = {
  template: `
  <div v-if="U.store.derAbierto" class="der-float" :style="{left: pos.x + 'px', top: pos.y + 'px', width: pos.w + 'px', height: pos.h + 'px'}">
    <div class="der-float-h" @mousedown="mover">
      <ico n="database" c="sm"/><b>DER</b>
      <span class="small muted der-ayuda">Clic: resalta relaciones · Doble clic: inserta en el editor</span>
      <span class="spacer"></span>
      <button class="icon-btn" @mousedown.stop @click="setZoom(zoom - .1)" title="Alejar"><ico n="minus" c="sm"/></button>
      <span class="small tnum" style="width:38px;text-align:center">{{ Math.round(zoom * 100) }}%</span>
      <button class="icon-btn" @mousedown.stop @click="setZoom(zoom + .1)" title="Acercar"><ico n="plus" c="sm"/></button>
      <button class="icon-btn" @mousedown.stop @click="verTodo" title="Ver todo el diagrama"><ico n="expand" c="sm"/></button>
      <button class="icon-btn" @mousedown.stop @click="U.toggleDer()" title="Cerrar"><ico n="x" c="sm"/></button>
    </div>
    <div class="der-float-b" ref="lienzo" @mousedown="panear" @wheel="rueda">
      <der-diagrama :zoom="zoom" :seleccion="sel" @tabla="clic" @columna="c => clic(c.tabla)" @doble="insertar" @fondo="fondo"/>
    </div>
    <div class="der-float-r" @mousedown.stop="redimensionar" title="Arrastrá para cambiar el tamaño"></div>
  </div>`,
  setup() {
    const { ref, reactive, watch, onMounted, onBeforeUnmount } = Vue;
    const guardado = (() => { try { return JSON.parse(localStorage.getItem("parc-der-pos") || "null"); } catch (e) { return null; } })();
    const pos = reactive(guardado && guardado.w ? guardado : { x: 250, y: Math.max(70, window.innerHeight - 500), w: 720, h: 470 });
    const zoom = ref((guardado && guardado.zoom) || 0.5);
    const sel = ref(null);
    const lienzo = ref(null);
    let movido = false;

    function persistir() { try { localStorage.setItem("parc-der-pos", JSON.stringify({ ...pos, zoom: zoom.value })); } catch (e) {} }
    function acomodar() {
      pos.w = Math.min(pos.w, window.innerWidth - 20);
      pos.h = Math.min(pos.h, window.innerHeight - 20);
      pos.x = Math.min(Math.max(0, pos.x), window.innerWidth - 120);
      pos.y = Math.min(Math.max(0, pos.y), window.innerHeight - 50);
    }
    onMounted(() => { acomodar(); window.addEventListener("resize", acomodar); });
    onBeforeUnmount(() => window.removeEventListener("resize", acomodar));

    function arrastre(ev, alMover) {
      ev.preventDefault();
      const x0 = ev.clientX, y0 = ev.clientY;
      const mov = (e) => alMover(e.clientX - x0, e.clientY - y0);
      const fin = () => { window.removeEventListener("mousemove", mov); window.removeEventListener("mouseup", fin); persistir(); };
      window.addEventListener("mousemove", mov);
      window.addEventListener("mouseup", fin);
    }
    function mover(ev) {
      const px = pos.x, py = pos.y;
      arrastre(ev, (dx, dy) => { pos.x = px + dx; pos.y = py + dy; acomodar(); });
    }
    function redimensionar(ev) {
      const w0 = pos.w, h0 = pos.h;
      arrastre(ev, (dx, dy) => { pos.w = Math.max(320, w0 + dx); pos.h = Math.max(220, h0 + dy); acomodar(); });
    }
    function panear(ev) {
      if (ev.button !== 0 || !lienzo.value) return;
      const el = lienzo.value, sl = el.scrollLeft, st = el.scrollTop;
      movido = false;
      const x0 = ev.clientX, y0 = ev.clientY;
      const mov = (e) => {
        const dx = e.clientX - x0, dy = e.clientY - y0;
        if (Math.abs(dx) + Math.abs(dy) > 4) { movido = true; el.classList.add("paneando"); }
        if (movido) { el.scrollLeft = sl - dx; el.scrollTop = st - dy; }
      };
      const fin = () => {
        el.classList.remove("paneando");
        window.removeEventListener("mousemove", mov);
        window.removeEventListener("mouseup", fin);
        setTimeout(() => { movido = false; }, 0);
      };
      window.addEventListener("mousemove", mov);
      window.addEventListener("mouseup", fin);
    }
    function setZoom(z, cx, cy) {
      const el = lienzo.value;
      const viejo = zoom.value;
      const nuevo = Math.round(Math.min(1.4, Math.max(0.2, z)) * 100) / 100;
      if (!el || nuevo === viejo) { zoom.value = nuevo; return; }
      cx = cx == null ? el.clientWidth / 2 : cx;
      cy = cy == null ? el.clientHeight / 2 : cy;
      const px = (el.scrollLeft + cx) / viejo, py = (el.scrollTop + cy) / viejo;
      zoom.value = nuevo;
      Vue.nextTick(() => { el.scrollLeft = px * nuevo - cx; el.scrollTop = py * nuevo - cy; });
      persistir();
    }
    function rueda(ev) {
      if (!(ev.ctrlKey || ev.metaKey)) return;
      ev.preventDefault();
      const r = lienzo.value.getBoundingClientRect();
      setZoom(zoom.value * (ev.deltaY < 0 ? 1.1 : 0.9), ev.clientX - r.left, ev.clientY - r.top);
    }
    function verTodo() {
      const el = lienzo.value;
      if (!el) return;
      setZoom(Math.min((el.clientWidth - 10) / ER_ANCHO, (el.clientHeight - 10) / ER_ALTO));
      Vue.nextTick(() => { el.scrollLeft = 0; el.scrollTop = 0; });
    }
    function clic(t) { if (movido) return; sel.value = sel.value === t ? null : t; }
    function fondo() { if (!movido) sel.value = null; }
    function insertar(texto) { if (movido) return; if (U.insertarEnEditor(texto)) U.toast("Insertado: " + texto, 1200); }
    watch(() => U.store.derAbierto, (v) => { if (v) Vue.nextTick(acomodar); });
    return { U, pos, zoom, sel, lienzo, mover, redimensionar, panear, setZoom, rueda, verTodo, clic, fondo, insertar };
  },
};
