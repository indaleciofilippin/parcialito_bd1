/* Componentes reutilizables */
window.registrarComponentes = function (app) {
  const { h, ref, computed, watch, onMounted, onBeforeUnmount, nextTick } = Vue;
  const { store } = U;

  // ------------------------------------------------------------ Ícono
  app.component("ico", {
    props: { n: String, c: String },
    setup(props) {
      return () => h("span", { style: "display:contents", innerHTML: U.icon(props.n, props.c) });
    },
  });

  // ------------------------------------------------------------ Markdown
  app.component("md-view", {
    props: { texto: String, inline: Boolean },
    template: `<span v-if="inline" class="md" v-html="html"></span><div v-else class="md" v-html="html"></div>`,
    computed: { html() { return this.inline ? U.mdInline(this.texto) : U.md(this.texto); } },
  });

  // ------------------------------------------------------------ Dificultad
  app.component("dif-dots", {
    props: { d: Number },
    template: `<span class="dots" :class="'dif-' + d" :title="['', 'Fácil', 'Media', 'Difícil'][d]"><i v-for="i in 3" :class="{on: i <= d}"></i></span>`,
  });

  // ------------------------------------------------------------ Bloque de código
  app.component("code-block", {
    props: { sql: String, bad: Boolean, cargable: Boolean, probar: Boolean },
    emits: ["cargar"],
    template: `
      <div class="code" :class="{bad}">
        <div class="code-acts">
          <button class="btn sm" @click="copiar"><ico n="copy" c="xs"/> Copiar</button>
          <button v-if="cargable" class="btn sm" @click="$emit('cargar', sql)"><ico n="edit" c="xs"/> Al editor</button>
          <button v-if="probar" class="btn sm" @click="probarEnConsola"><ico n="play" c="xs"/> Probar</button>
        </div>
        <pre v-html="html"></pre>
      </div>`,
    computed: { html() { return U.highlight(this.sql || ""); } },
    methods: {
      copiar() { U.copiar(this.sql); },
      probarEnConsola() { store.consolaSql = this.sql; U.irA("#/consola"); },
    },
  });

  // ------------------------------------------------------------ Anillo de progreso
  app.component("progress-ring", {
    props: { value: Number, size: { type: Number, default: 120 }, stroke: { type: Number, default: 10 },
             color: { type: String, default: "#fff" }, track: { type: String, default: "rgba(255,255,255,.18)" } },
    template: `
      <div class="ring" :style="{width: size + 'px', height: size + 'px'}">
        <svg :width="size" :height="size">
          <circle :cx="size/2" :cy="size/2" :r="r" :stroke="track" :stroke-width="stroke" fill="none"/>
          <circle :cx="size/2" :cy="size/2" :r="r" :stroke="color" :stroke-width="stroke" fill="none" stroke-linecap="round"
                  :stroke-dasharray="c" :stroke-dashoffset="c * (1 - Math.min(1, value || 0))" style="transition: stroke-dashoffset 1s cubic-bezier(.2,.8,.2,1)"/>
        </svg>
        <div class="ring-txt"><slot/></div>
      </div>`,
    computed: { r() { return (this.size - this.stroke) / 2; }, c() { return 2 * Math.PI * this.r; } },
  });

  // ------------------------------------------------------------ Editor SQL (CodeMirror 5)
  app.component("sql-editor", {
    props: { modelValue: String, placeholder: String, readonly: Boolean },
    emits: ["update:modelValue", "run", "check", "save"],
    setup(props, { emit, expose }) {
      const el = ref(null);
      let cm = null;
      function tablasHint() {
        const t = {};
        if (store.esquema) for (const [k, v] of Object.entries(store.esquema.columnas)) t[k] = v;
        return t;
      }
      onMounted(async () => {
        if (!store.esquema) { try { await U.cargarEsquema(); } catch (e) {} }
        cm = CodeMirror(el.value, {
          value: props.modelValue || "",
          mode: "text/x-mysql",
          theme: "parc",
          lineNumbers: true,
          matchBrackets: true,
          autoCloseBrackets: true,
          styleActiveLine: true,
          indentUnit: 4,
          tabSize: 4,
          lineWrapping: false,
          readOnly: props.readonly,
          placeholder: props.placeholder || "",
          hintOptions: { tables: tablasHint(), completeSingle: false },
          extraKeys: {
            "Cmd-Enter": () => emit("run"),
            "Ctrl-Enter": () => emit("run"),
            "Shift-Cmd-Enter": () => emit("check"),
            "Shift-Ctrl-Enter": () => emit("check"),
            "Cmd-S": () => emit("save"),
            "Ctrl-S": () => emit("save"),
            "Ctrl-Space": "autocomplete",
            "Cmd-/": "toggleComment",
            "Ctrl-/": "toggleComment",
            Tab: (c) => (c.somethingSelected() ? c.indentSelection("add") : c.replaceSelection("    ")),
          },
        });
        cm.on("change", () => {
          const v = cm.getValue();
          if (v !== props.modelValue) emit("update:modelValue", v);
        });
        cm.on("inputRead", (c, ch) => {
          if (ch.origin !== "+input") return;
          const txt = ch.text[0];
          if (/^[\w.]$/.test(txt)) {
            const tok = c.getTokenAt(c.getCursor());
            if (tok.string.length >= 2 || txt === ".") c.showHint({ completeSingle: false });
          }
        });
        setTimeout(() => cm.refresh(), 30);
      });
      watch(() => props.modelValue, (v) => {
        if (cm && v !== cm.getValue()) {
          const cur = cm.getCursor();
          cm.setValue(v || "");
          cm.setCursor(cur);
        }
      });
      watch(() => store.esquema, () => { if (cm) cm.setOption("hintOptions", { tables: tablasHint(), completeSingle: false }); });
      onBeforeUnmount(() => { cm = null; });
      expose({
        insertar(texto) { if (!cm) return; cm.replaceSelection(texto); cm.focus(); },
        foco() { cm && cm.focus(); },
        seleccion() { return cm ? cm.getSelection() : ""; },
        refrescar() { cm && cm.refresh(); },
        formatear() {
          if (!cm || !window.sqlFormatter) return;
          try {
            const f = sqlFormatter.format(cm.getValue(), { language: "mysql", keywordCase: "upper", tabWidth: 4 });
            cm.setValue(f);
          } catch (e) { U.toast("No pude formatear: revisá la sintaxis"); }
        },
      });
      return () => h("div", { class: "editor", ref: el });
    },
  });

  // ------------------------------------------------------------ Grilla de datos
  app.component("data-grid", {
    props: { columnas: Array, filas: Array, total: Number, truncado: Boolean, ms: Number, clases: Array, cambios: Array, compacto: Boolean },
    template: `
      <div style="display:flex;flex-direction:column;height:100%;min-height:0">
        <div class="grid-wrap" style="flex:1">
          <table class="dg">
            <thead><tr><th class="rn">#</th><th v-for="c in columnas">{{ c }}</th></tr></thead>
            <tbody>
              <tr v-for="(f, i) in filas" :class="clases && clases[i]">
                <td class="rn">{{ i + 1 }}</td>
                <td v-for="(v, j) in f" :class="celda(v, i, j)" :title="v === null ? 'NULL' : String(v)">{{ v === null ? 'NULL' : v }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="!filas || !filas.length" class="empty small">La consulta no devolvió filas (0 resultados).</div>
        </div>
        <div v-if="!compacto" class="grid-foot">
          <span><b class="tnum">{{ U.fmtNum(total ?? (filas ? filas.length : 0)) }}</b> fila(s)</span>
          <span v-if="truncado">· mostrando las primeras {{ filas.length }}</span>
          <span v-if="ms != null">· {{ ms }} ms</span>
          <span class="spacer"></span>
          <slot/>
        </div>
      </div>`,
    setup() { return { U }; },
    methods: {
      celda(v, i, j) {
        const c = [];
        if (v === null) c.push("null");
        else if (typeof v === "number") c.push("num");
        if (this.cambios && this.cambios[i] && this.cambios[i].includes(j)) c.push("chg");
        return c;
      },
    },
  });

  // ------------------------------------------------------------ Error de MySQL explicado
  app.component("error-card", {
    props: { error: Object },
    template: `
      <div class="err-card">
        <h4><ico n="alert" c="sm"/> {{ error.titulo }}<span v-if="error.codigo" class="badge danger" style="margin-left:4px">Error {{ error.codigo }}</span></h4>
        <div v-if="error.mensaje" class="msg">{{ error.mensaje }}</div>
        <p v-if="error.explicacion" :style="{marginTop: error.mensaje ? 0 : '8px'}">{{ error.explicacion }}</p>
        <div v-if="error.sugerencias && error.sugerencias.length" class="sug">
          <div v-for="s in error.sugerencias"><ico n="bulb" c="sm"/> {{ s }}</div>
        </div>
        <div v-if="error.sentencia && error.indice != null" class="small muted" style="margin-top:8px">En la sentencia {{ error.indice + 1 }}.</div>
      </div>`,
  });

  // ------------------------------------------------------------ Tabla chica (muestras)
  app.component("mini-table", {
    props: { columnas: Array, filas: Array, clase: String },
    template: `
      <div class="mini-table"><table class="dg">
        <thead><tr><th v-for="c in columnas">{{ c }}</th></tr></thead>
        <tbody><tr v-for="f in filas" :class="clase"><td v-for="v in f" :class="{null: v === null, num: typeof v === 'number'}">{{ v === null ? 'NULL' : v }}</td></tr></tbody>
      </table></div>`,
  });

  // ------------------------------------------------------------ Cambios de DML (antes/después)
  app.component("cambios-view", {
    props: { cambios: Array, verificacion: Array },
    template: `
      <div>
        <div v-for="(c, k) in cambios" :key="k" style="margin-bottom:16px">
          <div class="row small" style="margin-bottom:6px">
            <b>{{ cambios.length > 1 ? 'Verificación ' + (k + 1) : 'Cambios en los datos' }}</b>
            <span class="muted">· {{ c.total_antes }} → {{ c.total_despues }} filas</span>
            <span class="spacer"></span>
            <span v-if="c.n_modificadas" class="badge warning">{{ c.n_modificadas }} modificada(s)</span>
            <span v-if="c.n_nuevas" class="badge success">+{{ c.n_nuevas }} nueva(s)</span>
            <span v-if="c.n_quitadas" class="badge danger">−{{ c.n_quitadas }} eliminada(s)</span>
            <span v-if="!c.n_modificadas && !c.n_nuevas && !c.n_quitadas" class="badge">sin cambios</span>
          </div>
          <div v-if="filas(c).length" class="mini-table" style="max-height:260px">
            <table class="dg">
              <thead><tr><th class="rn"></th><th v-for="col in c.columnas">{{ col }}</th></tr></thead>
              <tbody>
                <tr v-for="f in filas(c)" :class="f.cls">
                  <td class="rn">{{ f.signo }}</td>
                  <td v-for="(v, j) in f.vals" :class="{null: v === null, num: typeof v === 'number', chg: f.chg && f.chg.includes(j)}" :title="f.antes ? 'Antes: ' + f.antes[j] : ''">
                    {{ v === null ? 'NULL' : v }}<span v-if="f.chg && f.chg.includes(j)" class="faint" style="font-size:10.5px"> (antes {{ f.antes[j] === null ? 'NULL' : f.antes[j] }})</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="tot(c) > 50" class="small muted" style="margin-top:4px">Se muestran hasta 50 de cada tipo.</div>
        </div>
      </div>`,
    methods: {
      tot(c) { return Math.max(c.n_nuevas, c.n_quitadas, c.n_modificadas || 0); },
      filas(c) {
        const out = [];
        (c.modificadas || []).forEach((m) => out.push({ vals: m.despues, antes: m.antes, cls: "", signo: "~", chg: m.despues.map((v, j) => (v !== m.antes[j] ? j : -1)).filter((j) => j >= 0) }));
        (c.nuevas || []).forEach((v) => out.push({ vals: v, cls: "add", signo: "+" }));
        (c.quitadas || []).forEach((v) => out.push({ vals: v, cls: "del", signo: "−" }));
        return out;
      },
    },
  });

  // ------------------------------------------------------------ Pasos ejecutados
  app.component("pasos-view", {
    props: { pasos: Array, error: Object },
    template: `
      <div class="card" style="overflow:hidden;margin-bottom:12px" v-if="(pasos && pasos.length) || error">
        <div v-for="(p, i) in pasos" class="step">
          <span class="si"><ico n="check" c="xs"/></span>
          <code>{{ (p.sql || '').replace(/\\s+/g, ' ') }}</code>
          <span class="muted tnum" v-if="p.tipo === 'ok'">{{ p.afectadas }} fila(s) afectada(s)</span>
          <span class="muted tnum" v-else>{{ p.total }} fila(s)</span>
          <span class="faint tnum small">{{ p.ms }} ms</span>
        </div>
        <div v-if="error" class="step err">
          <span class="si"><ico n="x" c="xs"/></span>
          <code>{{ (error.sentencia || '').replace(/\\s+/g, ' ') }}</code>
          <span style="color:var(--danger)">Error {{ error.codigo }}</span>
        </div>
      </div>`,
  });

  // ------------------------------------------------------------ Resultado de "Ejecutar"
  app.component("result-view", {
    props: { r: Object },
    template: `
      <div style="height:100%;display:flex;flex-direction:column;min-height:0">
        <div v-if="r.error && !r.resultado" class="results-body pad">
          <pasos-view v-if="r.pasos" :pasos="r.pasos" :error="r.error"/>
          <error-card :error="r.error"/>
        </div>
        <template v-else-if="r.resultado && r.resultado.tipo === 'resultado'">
          <div v-if="r.mensajes && r.mensajes.length" class="note info" style="margin:10px 12px 4px"><ico n="info" c="sm"/><div>{{ r.mensajes[0] }}</div></div>
          <div style="flex:1;min-height:0"><data-grid v-bind="r.resultado"/></div>
        </template>
        <div v-else class="results-body pad">
          <div class="note info" style="margin-top:0;margin-bottom:12px" v-if="r.cambios || r.estructuras">
            <ico n="shield" c="sm"/>
            <div v-if="r.cambios">Ejecutado dentro de una transacción y <b>deshecho</b> al terminar: tu base de práctica no cambió.</div>
            <div v-else>Ejecutado en un <b>espacio temporal</b>: tu base de práctica no cambió.</div>
          </div>
          <pasos-view :pasos="r.pasos" :error="r.error"/>
          <error-card v-if="r.error" :error="r.error" style="margin-bottom:12px"/>
          <cambios-view v-if="r.cambios && r.cambios.length" :cambios="r.cambios"/>
          <template v-if="r.estructuras && Object.keys(r.estructuras).length">
            <div class="sol-block" v-for="(ddl, t) in r.estructuras">
              <h4><ico n="table" c="xs"/> Estructura resultante de {{ t }}</h4>
              <code-block :sql="ddl"/>
            </div>
          </template>
          <div v-if="r.pasos && r.pasos.some(p => p.tipo === 'resultado')">
            <div v-for="p in r.pasos.filter(p => p.tipo === 'resultado')" style="height:260px;border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-bottom:12px">
              <data-grid v-bind="p"/>
            </div>
          </div>
        </div>
      </div>`,
  });

  // ------------------------------------------------------------ Veredicto de "Corregir"
  app.component("verdict-view", {
    props: { r: Object, siguiente: String },
    emits: ["solucion", "siguiente"],
    template: `
      <div>
        <div class="verdict" :class="r.ok ? 'ok' : 'bad'">
          <div class="vi"><ico :n="r.ok ? 'check' : 'x'"/></div>
          <div style="flex:1;min-width:0">
            <h3>{{ r.ok ? titulos[Math.floor(Math.random() * titulos.length)] : 'Todavía no' }}</h3>
            <ul v-if="r.mensajes && r.mensajes.length"><li v-for="m in r.mensajes">{{ m }}</li></ul>
            <div class="row" style="margin-top:12px" v-if="r.ok">
              <button class="btn sm" @click="$emit('solucion')"><ico n="eye" c="xs"/> Ver solución oficial y otras formas</button>
              <button v-if="siguiente" class="btn sm success" @click="$emit('siguiente')">Siguiente ejercicio <ico n="right" c="xs"/></button>
            </div>
          </div>
        </div>
        <error-card v-if="r.error" :error="r.error" style="margin-top:12px"/>
        <div v-if="r.checks" class="checks">
          <div v-for="c in r.checks" class="check" :class="c.ok ? 'ok' : (c.opcional ? 'opt' : 'bad')">
            <span class="ci"><ico :n="c.ok ? 'check' : (c.opcional ? 'info' : 'x')" c="xs"/></span>
            <div><div class="cd">{{ c.desc }} <span v-if="c.opcional" class="badge outline" style="height:18px;font-size:10.5px">opcional</span></div><div class="cx">{{ c.detalle }}</div></div>
          </div>
        </div>
        <template v-if="r.muestras">
          <div v-if="r.muestras.faltan && r.muestras.faltan.length">
            <div class="mini-label del"><ico n="minus" c="xs"/> Filas que faltan en tu resultado ({{ r.muestras.n_faltan }}){{ r.muestras.n_faltan > r.muestras.faltan.length ? ' · algunas:' : '' }}</div>
            <mini-table :columnas="r.muestras.columnas" :filas="r.muestras.faltan"/>
          </div>
          <div v-if="r.muestras.sobran && r.muestras.sobran.length">
            <div class="mini-label add" style="color:var(--warning)"><ico n="plus" c="xs"/> Filas que sobran en tu resultado ({{ r.muestras.n_sobran }}){{ r.muestras.n_sobran > r.muestras.sobran.length ? ' · algunas:' : '' }}</div>
            <mini-table :columnas="r.muestras.columnas" :filas="r.muestras.sobran"/>
          </div>
        </template>
        <div v-if="r.cambios && r.cambios.length" style="margin-top:16px">
          <cambios-view :cambios="r.cambios"/>
        </div>
        <template v-if="r.estructuras && Object.keys(r.estructuras).length">
          <div class="sol-block" style="margin-top:16px" v-for="(ddl, t) in r.estructuras">
            <h4><ico n="table" c="xs"/> Tu estructura de {{ t }}</h4>
            <code-block :sql="ddl"/>
          </div>
        </template>
      </div>`,
    data() { return { titulos: ["¡Correcto!", "¡Perfecto!", "¡Excelente!", "¡Bien ahí!", "¡Impecable!"] }; },
  });

  // ------------------------------------------------------------ Panel de esquema (árbol)
  app.component("schema-tree", {
    props: { filtro: String },
    emits: ["insertar", "abrir"],
    template: `
      <div class="tree">
        <div v-if="!store.esquema" class="empty small">Cargando…</div>
        <template v-else v-for="t in tablas" :key="t">
          <div class="tree-t" @click="toggle(t)" @dblclick="$emit('abrir', t)" :title="'Doble clic: SELECT * FROM ' + t">
            <ico :n="abiertas[t] ? 'down' : 'right'" c="xs"/>
            <ico :n="store.esquema.tipos[t] === 'vista' ? 'eye' : 'table'" c="sm"/>
            <span @click.stop="$emit('insertar', t)" style="cursor:copy">{{ t }}</span>
            <span class="n">{{ store.esquema.tipos[t] === 'vista' ? 'vista' : U.fmtNum(store.esquema.conteos[t]) }}</span>
          </div>
          <template v-if="abiertas[t]">
            <div v-for="c in store.esquema.detalle[t]" class="tree-c" @click="$emit('insertar', c.nombre)" :title="c.valores ? 'Valores: ' + c.valores.join(', ') : c.tipo">
              <ico :n="c.clave === 'PRI' ? 'key' : (esFk(t, c.nombre) ? 'link' : 'dot')" :c="'xs ' + (c.clave === 'PRI' ? 'k-pk' : (esFk(t, c.nombre) ? 'k-fk' : 'k-col'))"/>
              {{ c.nombre }}<span class="ty">{{ c.tipo }}</span>
            </div>
          </template>
        </template>
      </div>`,
    setup() {
      U.cargarEsquema().catch(() => {});
      return { store, U };
    },
    data() { return { abiertas: {} }; },
    computed: {
      tablas() {
        const todas = Object.keys(store.esquema.detalle);
        const f = (this.filtro || "").toLowerCase();
        const lista = f ? todas.filter((t) => t.includes(f) || store.esquema.detalle[t].some((c) => c.nombre.includes(f))) : todas;
        return lista.sort((a, b) => (store.esquema.tipos[a] === "vista") - (store.esquema.tipos[b] === "vista") || a.localeCompare(b));
      },
    },
    methods: {
      toggle(t) { this.abiertas[t] = !this.abiertas[t]; },
      esFk(t, c) { return store.esquema.fks.some((f) => f.tabla === t && f.columna === c); },
    },
  });

  // ------------------------------------------------------------ Divisores redimensionables
  app.directive("split", {
    mounted(el, binding) {
      // binding.value = { contenedor: selector o elemento padre, var: '--left', eje: 'x'|'y', min, max }
      const cfg = binding.value;
      el.addEventListener("mousedown", (ev) => {
        ev.preventDefault();
        const cont = el.parentElement;
        const rect = cont.getBoundingClientRect();
        el.classList.add("drag");
        document.body.style.cursor = cfg.eje === "y" ? "row-resize" : "col-resize";
        const mover = (e) => {
          let pct;
          if (cfg.eje === "y") pct = ((e.clientY - rect.top - (cfg.offset || 0)) / (rect.height - (cfg.offset || 0))) * 100;
          else pct = ((e.clientX - rect.left) / rect.width) * 100;
          pct = Math.max(cfg.min || 15, Math.min(cfg.max || 85, pct));
          cont.style.setProperty(cfg.var, pct + "%");
          window.dispatchEvent(new Event("resize"));
        };
        const soltar = () => {
          el.classList.remove("drag");
          document.body.style.cursor = "";
          window.removeEventListener("mousemove", mover);
          window.removeEventListener("mouseup", soltar);
          try { localStorage.setItem("parc" + cfg.var, cont.style.getPropertyValue(cfg.var)); } catch (e) {}
          document.querySelectorAll(".CodeMirror").forEach((c) => c.CodeMirror && c.CodeMirror.refresh());
        };
        window.addEventListener("mousemove", mover);
        window.addEventListener("mouseup", soltar);
      });
      try {
        const v = localStorage.getItem("parc" + cfg.var);
        if (v) el.parentElement.style.setProperty(cfg.var, v);
      } catch (e) {}
    },
  });
};
