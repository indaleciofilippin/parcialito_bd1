window.Vistas = window.Vistas || {};

Vistas.simulacroInicio = {
  template: `
  <div class="page">
    <div class="page-head">
      <div><div class="page-title">Simulacro de parcialito</div><div class="page-sub">Ejercicios al azar, con tiempo, sin pistas ni corrección hasta que entregues. Como el día del examen.</div></div>
    </div>
    <div class="sim-options">
      <div v-for="p in plantillas" class="card sim-opt" :class="{sel: plantilla === p.id}" @click="plantilla = p.id">
        <div class="row"><div class="sec-ico" :style="{'--sc': p.color}"><ico :n="p.icono"/></div><span class="spacer"></span><span v-if="p.extra" class="badge warning">no entra</span><span class="badge outline"><ico n="clock" c="xs"/> {{ p.min }} min</span></div>
        <h3>{{ p.nombre }}</h3>
        <div class="small muted">{{ p.desc }}</div>
      </div>
    </div>
    <div class="card pad row wrap" style="margin-top:16px;gap:18px">
      <label class="toggle" :class="{on: noResueltos}" @click="noResueltos = !noResueltos"><span class="sw"></span> Priorizar ejercicios que todavía no resolví</label>
      <span class="spacer"></span>
      <span class="small muted">Podés <b>Ejecutar</b> para ver resultados (como en Workbench), pero la corrección llega al entregar.</span>
      <button class="btn primary lg" @click="empezar" :disabled="creando"><ico n="play" c="sm"/> Empezar simulacro</button>
    </div>

    <div class="section-h" style="margin-top:30px"><h2>Simulacros anteriores</h2></div>
    <div v-if="!historial.length" class="card empty">Todavía no hiciste ninguno. ¡Animate!</div>
    <div v-else class="grid" style="gap:8px">
      <div v-for="h in historial" class="card ex-card" @click="U.irA('#/simulacro/' + h.id)">
        <div class="ex-status" :class="h.nota == null ? 'try' : (h.nota >= 6 ? 'ok' : '')" :style="h.nota != null && h.nota < 6 ? 'background:var(--danger);border:0;color:#fff' : ''">
          <ico v-if="h.nota == null" n="clock" c="xs"/><b v-else class="small">{{ Math.round(h.nota) }}</b>
        </div>
        <div class="body"><div class="t">Simulacro #{{ h.id }} · {{ h.n }} ejercicios</div><div class="m">{{ h.inicio.slice(0, 16) }} · {{ h.duracion_min }} min · {{ h.nota == null ? 'sin entregar' : 'nota ' + h.nota + '/10' }}</div></div>
        <ico n="right" c="sm"/>
      </div>
    </div>
  </div>`,
  setup() {
    const { ref, onMounted } = Vue;
    const plantillas = [
      { id: "corto", nombre: "Parcialito corto", min: 45, icono: "zap", color: "var(--c-joins)", desc: "5 ejercicios: JOIN/básica, agrupación, dominio y subconsultas/vistas." },
      { id: "completo", nombre: "Parcialito completo", min: 80, icono: "graduation", color: "var(--c-agrupacion)", desc: "8 ejercicios cubriendo todos los temas que entran." },
      { id: "extra", nombre: "DML + DDL", min: 40, icono: "edit", color: "var(--c-dml)", desc: "4 ejercicios de práctica extra (no entran en el parcialito).", extra: true },
    ];
    const plantilla = ref("corto");
    const noResueltos = ref(true);
    const historial = ref([]);
    const creando = ref(false);
    onMounted(async () => { try { historial.value = await U.api.get("/simulacros"); } catch (e) {} });
    async function empezar() {
      creando.value = true;
      try {
        const s = await U.api.post("/simulacro", { plantilla: plantilla.value, no_resueltos: noResueltos.value });
        U.irA("#/simulacro/" + s.id);
      } catch (e) { U.toast(e.message); }
      creando.value = false;
    }
    return { U, plantillas, plantilla, noResueltos, historial, creando, empezar };
  },
};

Vistas.simulacro = {
  props: { id: String },
  template: `
  <div v-if="!s" class="placeholder" style="height:100vh"><div class="spinner"></div></div>

  <!-- ===================== Examen en curso ===================== -->
  <div v-else-if="!s.terminado" class="ws" style="grid-template-rows:auto auto 1fr">
    <div class="ws-head">
      <div class="sec-ico" style="--sc: var(--primary)"><ico n="timer"/></div>
      <div><div class="crumbs">Simulacro #{{ s.id }}</div><h1>Ejercicio {{ actual + 1 }} de {{ s.ejercicios.length }}</h1></div>
      <span class="spacer"></span>
      <span class="timer" :class="{warn: restante < 300}">{{ reloj }}</span>
      <button class="btn success" @click="entregar(false)" :disabled="entregando"><ico n="send" c="sm"/> Entregar</button>
    </div>
    <div class="qtabs">
      <div v-for="(e, i) in s.ejercicios" class="qtab" :class="{active: actual === i}" @click="ir(i)">
        <span class="dot" :class="{on: (resp[e.id] || '').trim()}"></span> {{ i + 1 }} <span class="small muted" style="font-weight:500">{{ U.seccion(e.seccion).corto }}</span>
      </div>
    </div>
    <div class="ws-body">
      <div class="pane-left">
        <div class="pane-scroll">
          <div class="row" style="margin-bottom:12px"><span class="badge outline">{{ ej.origen }}</span><span class="badge primary">{{ U.TIPO_NOMBRE[ej.tipo] }}</span><dif-dots :d="ej.dificultad"/></div>
          <h2 style="font-size:19px;margin-bottom:12px">{{ ej.titulo }}</h2>
          <div class="enunciado"><md-view :texto="ej.enunciado"/></div>
          <div v-if="ej.tipo === 'view'" class="note info"><ico n="eye" c="sm"/><div>Respondé con <code>CREATE VIEW nombre AS SELECT …</code></div></div>
          <div class="note" style="background:var(--surface-2);margin-top:20px"><ico n="info" c="sm"/><div class="small">Sin pistas ni corrección hasta entregar. Tus respuestas se guardan solas. Si se termina el tiempo, se entrega automáticamente.</div></div>
        </div>
      </div>
      <div class="split" v-split="{var: '--left', eje: 'x', min: 25, max: 65}"></div>
      <div class="pane-right" style="position:relative">
        <div class="toolbar">
          <button class="btn primary" @click="ejecutar" :disabled="cargando"><ico n="play" c="sm"/> Ejecutar <span class="kbd">⌘↵</span></button>
          <button class="btn ghost sm" @click="$refs.ed.formatear()"><ico n="sparkles" c="sm"/> Formatear</button>
          <span class="spacer"></span>
          <button class="btn sm" :disabled="actual === 0" @click="ir(actual - 1)"><ico n="left" c="sm"/></button>
          <button class="btn sm" :disabled="actual === s.ejercicios.length - 1" @click="ir(actual + 1)">Siguiente <ico n="right" c="sm"/></button>
          <button class="btn sm" :class="{primary: U.store.derAbierto}" @click="U.toggleDer()" title="Ver el diagrama entidad-relación mientras resolvés"><ico n="layers" c="sm"/> DER</button>
          <button class="btn sm" :class="{primary: drawer}" @click="drawer = !drawer"><ico n="database" c="sm"/> Tablas</button>
        </div>
        <sql-editor ref="ed" v-model="resp[ej.id]" placeholder="-- Tu respuesta" @run="ejecutar"/>
        <div class="hsplit" v-split="{var: '--edh', eje: 'y', min: 18, max: 80, offset: 52}"></div>
        <div class="results">
          <div class="tabs"><div class="tab active"><ico n="table" c="sm"/> Resultado</div></div>
          <div class="results-body" :class="{pad: !(res && res.resultado)}">
            <div v-if="cargando" class="loading-cover"><div class="spinner"></div></div>
            <result-view v-if="res" :r="res"/>
            <div v-else class="placeholder"><div><ico n="play"/><div>Ejecutá para ver el resultado.</div></div></div>
          </div>
        </div>
        <div v-if="drawer" class="drawer">
          <div class="drawer-h"><ico n="database" c="sm"/> Esquema <span class="spacer"></span><button class="icon-btn" @click="drawer = false"><ico n="x" c="sm"/></button></div>
          <schema-tree @insertar="t => $refs.ed.insertar(t)" @abrir="t => $refs.ed.insertar('SELECT * FROM ' + t + ';')"/>
        </div>
      </div>
    </div>
  </div>

  <!-- ===================== Resultado ===================== -->
  <div v-else class="page">
    <div class="hero" :style="{background: s.nota >= 6 ? 'linear-gradient(120deg,#065f46,#059669 50%,#10b981)' : 'linear-gradient(120deg,#7f1d1d,#dc2626 55%,#f97316)'}">
      <div style="position:relative;z-index:1">
        <div class="badge" style="background:rgba(255,255,255,.16);color:#fff;margin-bottom:10px">Simulacro #{{ s.id }} · {{ s.inicio.slice(0, 16) }}</div>
        <h1>{{ s.nota >= 9 ? '¡Excelente! Estás listo.' : s.nota >= 6 ? '¡Aprobado! Bien ahí.' : 'Todavía no, pero vas a llegar.' }}</h1>
        <p>{{ correctos }} de {{ s.ejercicios.length }} ejercicios correctos. {{ s.nota >= 6 ? 'Repasá los que fallaste y hacé otro para afianzar.' : 'Mirá abajo qué falló en cada uno, practicá esas secciones y volvé a intentar.' }}</p>
        <div class="row"><button class="btn lg white" @click="U.irA('#/simulacro')"><ico n="refresh" c="sm"/> Otro simulacro</button><button class="btn lg glass" @click="U.irA('#/progreso')"><ico n="chart" c="sm"/> Mi progreso</button></div>
      </div>
      <progress-ring :value="s.nota / 10" :size="150" :stroke="12" style="position:relative;z-index:1"><b style="font-size:38px">{{ fmtNota }}</b><span>sobre 10</span></progress-ring>
    </div>
    <div class="section-h" style="margin-top:26px"><h2>Detalle por ejercicio</h2></div>
    <div v-for="(e, i) in s.ejercicios" class="card res-item">
      <div class="res-head" @click="abierto[e.id] = !abierto[e.id]">
        <span class="ex-status" :class="s.resultado[e.id] && s.resultado[e.id].ok ? 'ok' : ''" :style="!(s.resultado[e.id] && s.resultado[e.id].ok) ? 'background:var(--danger);border:0;color:#fff' : ''"><ico :n="s.resultado[e.id] && s.resultado[e.id].ok ? 'check' : 'x'" c="sm"/></span>
        <div style="flex:1;min-width:0"><div style="font-weight:650">{{ i + 1 }}. {{ e.titulo }}</div><div class="small muted">{{ U.seccion(e.seccion).nombre }} · {{ e.origen }}</div></div>
        <button class="btn sm ghost" @click.stop="U.irA('#/ej/' + e.id)">Practicar <ico n="right" c="xs"/></button>
        <ico :n="abierto[e.id] ? 'down' : 'right'" c="sm"/>
      </div>
      <div v-if="abierto[e.id]" class="res-body">
        <div class="enunciado small"><md-view :texto="e.enunciado"/></div>
        <div class="sol-block" style="margin:0"><h4>Tu respuesta</h4>
          <code-block v-if="(s.respuestas[e.id] || '').trim()" :sql="s.respuestas[e.id]" :bad="!(s.resultado[e.id] && s.resultado[e.id].ok)"/>
          <div v-else class="small muted">Sin responder.</div>
        </div>
        <verdict-view v-if="s.resultado[e.id] && !s.resultado[e.id].vacio" :r="s.resultado[e.id]"/>
        <div class="sol-block" style="margin:0"><h4>Solución oficial</h4><code-block :sql="e.solucion"/></div>
        <div v-if="e.explicacion" class="sol-block" style="margin:0"><h4>Explicación</h4><md-view :texto="e.explicacion"/></div>
      </div>
    </div>
  </div>`,
  setup(props) {
    const { ref, reactive, computed, watch, onMounted, onBeforeUnmount } = Vue;
    const s = ref(null);
    const actual = ref(0);
    const resp = reactive({});
    const res = ref(null);
    const cargando = ref(false);
    const entregando = ref(false);
    const drawer = ref(false);
    const restante = ref(0);
    const abierto = reactive({});
    let tick = null, autosave = null, finMs = 0;

    async function cargar() {
      const d = await U.api.get("/simulacro/" + props.id);
      s.value = d;
      Object.keys(resp).forEach((k) => delete resp[k]);
      d.ejercicios.forEach((e) => { resp[e.id] = (d.respuestas && d.respuestas[e.id]) || ""; });
      if (d.terminado) {
        d.ejercicios.forEach((e) => { abierto[e.id] = !(d.resultado[e.id] && d.resultado[e.id].ok); });
        return;
      }
      finMs = Date.now() + (d.duracion_min * 60 - d.segundos_transcurridos) * 1000;
      clearInterval(tick);
      tick = setInterval(() => {
        restante.value = Math.max(0, Math.round((finMs - Date.now()) / 1000));
        if (restante.value <= 0) { clearInterval(tick); entregar(true); }
      }, 500);
      clearInterval(autosave);
      autosave = setInterval(guardarRespuestas, 5000);
    }
    onMounted(() => cargar().catch((e) => U.toast(e.message)));
    watch(() => props.id, () => cargar().catch((e) => U.toast(e.message)));
    onBeforeUnmount(() => { clearInterval(tick); clearInterval(autosave); if (s.value && !s.value.terminado) guardarRespuestas(); });

    const ej = computed(() => s.value.ejercicios[actual.value]);
    const reloj = computed(() => {
      const m = Math.floor(restante.value / 60), sec = restante.value % 60;
      return String(m).padStart(2, "0") + ":" + String(sec).padStart(2, "0");
    });
    const correctos = computed(() => (s.value && s.value.resultado ? Object.values(s.value.resultado).filter((r) => r.ok).length : 0));
    const fmtNota = computed(() => (s.value && s.value.nota != null ? (Math.round(s.value.nota * 10) / 10).toString().replace(".", ",") : ""));

    function guardarRespuestas() {
      if (!s.value || s.value.terminado) return;
      U.api.put("/simulacro/" + s.value.id + "/respuestas", { respuestas: { ...resp } }).catch(() => {});
    }
    function ir(i) { actual.value = i; res.value = null; }
    async function ejecutar() {
      const sql = resp[ej.value.id] || "";
      if (!sql.trim()) return U.toast("Escribí una consulta primero");
      cargando.value = true;
      try { res.value = await U.api.post("/ejercicios/" + ej.value.id + "/ejecutar", { sql }); } catch (e) { U.toast(e.message); }
      cargando.value = false;
    }
    async function entregar(auto) {
      if (!auto) {
        const vacios = s.value.ejercicios.filter((e) => !(resp[e.id] || "").trim()).length;
        const ok = await U.confirmar("¿Entregar el simulacro?", vacios ? "Te quedan " + vacios + " ejercicio(s) sin responder." : "Se corrigen todos los ejercicios y ves tu nota.", "Entregar");
        if (!ok) return;
      } else U.toast("¡Tiempo! Entregando…");
      entregando.value = true;
      clearInterval(tick); clearInterval(autosave);
      try {
        const d = await U.api.post("/simulacro/" + s.value.id + "/entregar", { respuestas: { ...resp } });
        d.ejercicios.forEach((e) => { abierto[e.id] = !(d.resultado[e.id] && d.resultado[e.id].ok); });
        s.value = d;
        U.cargarCatalogo().catch(() => {});
        if (d.nota >= 6 && window.confetti) confetti({ particleCount: 180, spread: 90, origin: { y: 0.4 } });
        document.querySelector(".main").scrollTop = 0;
      } catch (e) { U.toast(e.message); }
      entregando.value = false;
    }
    return { U, s, actual, resp, res, cargando, entregando, drawer, restante, abierto, ej, reloj, correctos, fmtNota, ir, ejecutar, entregar };
  },
};
