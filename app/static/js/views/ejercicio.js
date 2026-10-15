window.Vistas = window.Vistas || {};

Vistas.ejercicio = {
  props: { id: String },
  template: `
  <div class="ws" v-if="ej">
    <div class="ws-head">
      <button class="icon-btn" @click="U.irA('#/ejercicios/' + ej.seccion)" title="Volver"><ico n="left"/></button>
      <div style="min-width:0">
        <div class="crumbs"><a :href="'#/ejercicios/' + ej.seccion">{{ U.seccion(ej.seccion).nombre }}</a><ico n="right" c="xs"/><span class="mono">{{ ej.id }}</span></div>
        <div class="row" style="gap:10px">
          <h1>{{ ej.titulo }}</h1>
          <span v-if="ej.resuelto" class="badge success"><ico n="check" c="xs"/> Resuelto</span>
        </div>
      </div>
      <span class="spacer"></span>
      <span class="badge outline">{{ ej.origen }}</span>
      <span class="badge" :class="'dif-' + ej.dificultad" style="background:var(--surface-3)"><dif-dots :d="ej.dificultad"/> {{ ['', 'Fácil', 'Media', 'Difícil'][ej.dificultad] }}</span>
      <span class="badge primary">{{ U.TIPO_NOMBRE[ej.tipo] }}</span>
      <button class="icon-btn" :class="{on: ej.marcado}" @click="marcar" title="Marcar para repasar"><ico n="star"/></button>
      <button class="icon-btn" :disabled="!ej.anterior" @click="ej.anterior && U.irA('#/ej/' + ej.anterior)" title="Anterior"><ico n="left"/></button>
      <button class="icon-btn" :disabled="!ej.siguiente" @click="ej.siguiente && U.irA('#/ej/' + ej.siguiente)" title="Siguiente"><ico n="right"/></button>
    </div>

    <div class="ws-body">
      <!-- Izquierda: enunciado / pistas / solución / historial -->
      <div class="pane-left">
        <div class="tabs">
          <div class="tab" :class="{active: tabL === 'enunciado'}" @click="tabL = 'enunciado'"><ico n="book" c="sm"/> Enunciado</div>
          <div class="tab" :class="{active: tabL === 'pistas'}" @click="tabL = 'pistas'"><ico n="bulb" c="sm"/> Pistas <span class="badge warning" v-if="ej.pistas.length">{{ pistasVistas }}/{{ ej.pistas.length }}</span></div>
          <div class="tab" :class="{active: tabL === 'solucion'}" @click="tabL = 'solucion'"><ico n="eye" c="sm"/> Solución</div>
          <div class="tab" :class="{active: tabL === 'historial'}" @click="tabL = 'historial'"><ico n="history" c="sm"/> Mis intentos <span class="badge" v-if="ej.historial.length">{{ ej.historial.length }}</span></div>
        </div>
        <div class="pane-scroll">
          <!-- Enunciado -->
          <div v-show="tabL === 'enunciado'">
            <div class="enunciado"><md-view :texto="ej.enunciado"/></div>
            <div v-if="ej.tipo === 'view'" class="note info"><ico n="eye" c="sm"/><div>Escribí <code>CREATE VIEW nombre AS SELECT …;</code>. La vista se crea en un espacio temporal y se compara lo que devuelve con lo esperado. El nombre lo elegís vos.</div></div>
            <div v-if="ej.tipo === 'dml'" class="note info"><ico n="shield" c="sm"/><div>Tus sentencias se ejecutan dentro de una transacción y se <b>deshacen</b> al terminar: probá sin miedo. Podés escribir varias sentencias separadas por <code>;</code>.<template v-if="ej.tiene_preparacion"> Para este ejercicio la app agrega antes algunos datos de prueba (los menciona el enunciado).</template></div></div>
            <div v-if="ej.tipo === 'ddl'" class="note info"><ico n="shield" c="sm"/><div>Se ejecuta sobre una <b>copia temporal</b> de la estructura de la base: tu base de práctica no cambia. Al corregir se revisa la estructura y se prueba que las restricciones funcionen.</div></div>
            <div v-if="ej.es_abierto" class="note warn"><ico n="edit" c="sm"/><div>Ejercicio abierto: elegís vos los valores. Se verifica que se cumplan las condiciones pedidas.</div></div>
            <div v-if="ej.casos_borde" class="note warn"><ico n="flag" c="sm"/>
              <div>Ojo: con los datos originales este tipo de consulta puede dar <b>0 filas</b>. Al corregir, la app también prueba tu consulta con <b>casos borde</b> (datos extra que después se deshacen):
                <ul style="margin:6px 0 0;padding-left:18px"><li v-for="c in casosBorde" class="small">{{ c }}</li></ul>
              </div>
            </div>
            <div class="note" style="background:var(--surface-2)"><ico n="keyboard" c="sm"/><div class="small"><span class="kbd-hint">⌘ ↵</span> ejecutar · <span class="kbd-hint">⌘ ⇧ ↵</span> corregir · <span class="kbd-hint">Ctrl Espacio</span> autocompletar · <span class="kbd-hint">⌘ /</span> comentar</div></div>
          </div>

          <!-- Pistas -->
          <div v-show="tabL === 'pistas'">
            <div v-if="!ej.pistas.length" class="empty">Este ejercicio no tiene pistas.</div>
            <div v-for="(p, i) in ej.pistas" class="hint">
              <div class="hint-h" @click="verPista(i)">
                <span class="n">{{ i + 1 }}</span>
                <span>{{ ['Por dónde empezar', 'Una ayudita más', 'Casi la solución', 'Última pista'][Math.min(i, 3)] }}</span>
                <span class="spacer"></span>
                <span v-if="i >= pistasVistas" class="small muted">Mostrar</span>
                <ico v-else n="check" c="sm" style="color:var(--success)"/>
              </div>
              <div v-if="i < pistasVistas" class="hint-b"><md-view :texto="p"/></div>
            </div>
            <div v-if="ej.tipo === 'select' || ej.tipo === 'view'" class="note info" style="margin-top:16px"><ico n="table" c="sm"/><div>¿Querés ver qué tiene que devolver? Abajo, en la pestaña <b>Esperado</b>, está el resultado de la solución oficial (sin mostrar el SQL).</div></div>
          </div>

          <!-- Solución -->
          <div v-show="tabL === 'solucion'">
            <div v-if="!sol" class="locked">
              <div class="lk"><ico n="lock" c="lg"/></div>
              <h3 style="font-size:16px">{{ ej.resuelto ? '¡Ya lo resolviste!' : 'Intentalo primero' }}</h3>
              <p class="muted" style="max-width:340px;margin:6px auto 16px">{{ ej.resuelto ? 'Mirá la solución oficial, su explicación y otras formas de resolverlo.' : 'Se aprende mucho más peleándola un rato. Probá con las pistas antes de mirar.' }}</p>
              <button class="btn" :class="ej.resuelto ? 'primary' : ''" @click="verSolucion"><ico n="eye" c="sm"/> Ver solución</button>
            </div>
            <template v-else>
              <div class="sol-block"><h4><ico n="check" c="xs"/> Solución oficial</h4><code-block :sql="sol.solucion" cargable @cargar="cargar"/></div>
              <div class="sol-block" v-if="sol.explicacion"><h4><ico n="bulb" c="xs"/> Explicación</h4><md-view :texto="sol.explicacion"/></div>
              <div class="sol-block" v-if="sol.alternativas.length"><h4><ico n="layers" c="xs"/> Otras formas correctas</h4>
                <div v-for="a in sol.alternativas" style="margin-bottom:12px"><div class="small" style="font-weight:650;margin-bottom:6px">{{ a.titulo }}</div><code-block :sql="a.sql" cargable @cargar="cargar"/></div>
              </div>
              <div class="sol-block" v-if="sol.variantes.length"><h4><ico n="info" c="xs"/> Otras interpretaciones que también se aceptan</h4>
                <div v-for="a in sol.variantes" style="margin-bottom:12px"><div class="small" style="font-weight:650;margin-bottom:6px">{{ a.titulo }}</div><code-block :sql="a.sql" cargable @cargar="cargar"/></div>
              </div>
              <div class="sol-block" v-if="sol.errores_comunes.length"><h4><ico n="alert" c="xs"/> Errores comunes</h4>
                <ul class="err-list"><li v-for="e in sol.errores_comunes"><ico n="x" c="sm"/><md-view :texto="e" inline/></li></ul>
              </div>
              <div class="sol-block" v-if="sol.trampas.length"><h4><ico n="x" c="xs"/> Así NO (consultas que parecen bien pero están mal)</h4>
                <div v-for="t in sol.trampas" style="margin-bottom:12px"><div class="small" style="font-weight:650;margin-bottom:6px;color:var(--danger)">✗ {{ t.titulo }}</div><code-block :sql="t.sql" bad cargable @cargar="cargar"/></div>
              </div>
            </template>
          </div>

          <!-- Historial -->
          <div v-show="tabL === 'historial'">
            <div v-if="!ej.historial.length" class="empty">Todavía no corregiste ningún intento.</div>
            <div v-for="h in ej.historial" class="hist-item" @click="cargar(h.sql_texto)" title="Cargar en el editor">
              <span class="ex-status" :class="h.correcto ? 'ok' : 'try'" style="width:24px;height:24px"><ico :n="h.correcto ? 'check' : 'x'" c="xs"/></span>
              <code>{{ h.sql_texto.replace(/\\s+/g, ' ') }}</code>
              <span class="small faint tnum">{{ h.fecha.slice(5, 16) }}</span>
              <span v-if="h.modo === 'simulacro'" class="badge" style="height:18px;font-size:10.5px">simulacro</span>
            </div>
          </div>
        </div>
      </div>

      <div class="split" v-split="{var: '--left', eje: 'x', min: 25, max: 65}"></div>

      <!-- Derecha: editor + resultados -->
      <div class="pane-right" style="position:relative">
        <div class="toolbar">
          <button class="btn primary" @click="ejecutar" :disabled="cargando"><ico n="play" c="sm"/> Ejecutar <span class="kbd">⌘↵</span></button>
          <button class="btn success" @click="corregir" :disabled="cargando"><ico n="check" c="sm"/> Corregir <span class="kbd">⌘⇧↵</span></button>
          <button class="btn ghost sm" @click="$refs.ed.formatear()" title="Formatear SQL"><ico n="sparkles" c="sm"/> Formatear</button>
          <span class="spacer"></span>
          <label v-if="ej.tipo === 'dml'" class="toggle" :class="{on: U.store.safeUpdates}" @click="toggleSafe" title="Simula el modo Safe Updates de Workbench (error 1175 si el WHERE no usa una clave)"><span class="sw"></span> Safe updates</label>
          <span class="small faint" v-if="guardado">{{ guardado }}</span>
          <button class="btn sm" :class="{primary: drawer}" @click="drawer = !drawer"><ico n="database" c="sm"/> Esquema</button>
        </div>
        <sql-editor ref="ed" v-model="sql" :placeholder="placeholder" @run="ejecutar" @check="corregir" @save="guardar(true)"/>
        <div class="hsplit" v-split="{var: '--edh', eje: 'y', min: 18, max: 80, offset: 52}"></div>
        <div class="results">
          <div class="tabs">
            <div class="tab" :class="{active: tabR === 'resultado'}" @click="tabR = 'resultado'"><ico n="table" c="sm"/> Resultado</div>
            <div class="tab" :class="{active: tabR === 'correccion'}" @click="tabR = 'correccion'">
              <ico n="target" c="sm"/> Corrección
              <span v-if="veredicto" class="badge" :class="veredicto.ok ? 'success' : 'danger'">{{ veredicto.ok ? '✓' : '✗' }}</span>
            </div>
            <div class="tab" :class="{active: tabR === 'esperado'}" @click="verEsperado"><ico n="eye" c="sm"/> Esperado</div>
            <span class="spacer"></span>
            <span v-if="ms" class="small faint" style="align-self:center">{{ ms }} ms</span>
          </div>
          <div class="results-body" :class="{pad: tabR !== 'resultado' || !(resultado && resultado.resultado && resultado.resultado.tipo === 'resultado')}">
            <div v-if="cargando" class="loading-cover"><div class="spinner"></div></div>
            <template v-if="tabR === 'resultado'">
              <result-view v-if="resultado" :r="resultado"/>
              <div v-else class="placeholder"><div><ico n="play"/><div>Escribí tu consulta y apretá <b>Ejecutar</b> para ver el resultado.</div></div></div>
            </template>
            <template v-if="tabR === 'correccion'">
              <verdict-view v-if="veredicto" :r="veredicto" :siguiente="ej.siguiente" @solucion="tabL = 'solucion'; verSolucion(true)" @siguiente="U.irA('#/ej/' + ej.siguiente)"/>
              <div v-else class="placeholder"><div><ico n="target"/><div>Cuando tengas una respuesta, apretá <b>Corregir</b>.</div></div></div>
            </template>
            <template v-if="tabR === 'esperado'">
              <div v-if="ej.tipo === 'ddl'" class="placeholder"><div><ico n="database"/><div>En los ejercicios de estructura no hay un «resultado»: al corregir se revisa una lista de chequeos.</div></div></div>
              <template v-else-if="esperado">
                <div class="note info" style="margin:0 0 12px"><ico n="info" c="sm"/><div>Esto es lo que produce la <b>solución oficial</b>. No importan los alias ni el orden de las columnas; tu resultado tiene que contener la misma información.</div></div>
                <div v-if="esperado.resultado" style="height:calc(100% - 60px);min-height:200px;border:1px solid var(--border);border-radius:10px;overflow:hidden"><data-grid v-bind="esperado.resultado"/></div>
                <template v-if="esperado.cambios"><pasos-view :pasos="esperado.pasos"/><cambios-view :cambios="esperado.cambios"/></template>
              </template>
            </template>
          </div>
        </div>
        <div v-if="drawer" class="drawer">
          <div class="drawer-h"><ico n="database" c="sm"/> Esquema <span class="spacer"></span><button class="icon-btn" @click="drawer = false"><ico n="x" c="sm"/></button></div>
          <div style="padding:8px 10px;border-bottom:1px solid var(--border)"><input class="input" style="width:100%;height:32px" v-model="filtroEsq" placeholder="Filtrar tablas o columnas"></div>
          <schema-tree :filtro="filtroEsq" @insertar="t => $refs.ed.insertar(t)" @abrir="t => $refs.ed.insertar('SELECT * FROM ' + t + ';')"/>
          <div class="small muted" style="padding:8px 12px;border-top:1px solid var(--border)">Clic en un nombre lo inserta en el editor.</div>
        </div>
      </div>
    </div>
  </div>
  <div v-else-if="errorCarga" class="placeholder" style="height:100vh"><div><ico n="alert"/><div style="margin-bottom:12px">{{ errorCarga }}</div><button class="btn" @click="U.irA('#/ejercicios')">Volver a los ejercicios</button></div></div>
  <div v-else class="placeholder" style="height:100vh"><div class="spinner"></div></div>`,
  setup(props) {
    const { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } = Vue;
    const ej = ref(null);
    const sql = ref("");
    const tabL = ref("enunciado");
    const tabR = ref("resultado");
    const resultado = ref(null);
    const veredicto = ref(null);
    const esperado = ref(null);
    const sol = ref(null);
    const cargando = ref(false);
    const ms = ref(null);
    const drawer = ref(false);
    const filtroEsq = ref("");
    const pistasVistas = ref(0);
    const guardado = ref("");
    const errorCarga = ref("");
    let timer = null;
    let ultimoGuardado = "";

    const casosBorde = computed(() => (U.store.catalogo ? U.store.catalogo.casos_borde : []));
    const placeholder = computed(() => {
      if (!ej.value) return "";
      return { select: "-- Escribí tu consulta SELECT acá", view: "-- CREATE VIEW nombre AS\n-- SELECT ...", dml: "-- INSERT / UPDATE / DELETE ...", ddl: "-- CREATE TABLE / ALTER TABLE ..." }[ej.value.tipo];
    });

    async function cargarEj() {
      ej.value = null; errorCarga.value = ""; resultado.value = null; veredicto.value = null; esperado.value = null; sol.value = null;
      tabL.value = "enunciado"; tabR.value = "resultado"; ms.value = null;
      try {
        const d = await U.api.get("/ejercicios/" + props.id);
        ej.value = d;
        sql.value = d.borrador || "";
        ultimoGuardado = sql.value;
        pistasVistas.value = parseInt(localStorage.getItem("parc-pistas-" + d.id) || "0", 10);
        if (!U.store.catalogo) U.cargarCatalogo().catch(() => {});
      } catch (e) { errorCarga.value = e.message; }
    }
    watch(() => props.id, cargarEj);
    onMounted(cargarEj);

    watch(sql, (v) => {
      clearTimeout(timer);
      timer = setTimeout(() => guardar(false), 900);
    });
    async function guardar(manual) {
      if (!ej.value || sql.value === ultimoGuardado) { if (manual) U.toast("Guardado"); return; }
      try {
        await U.api.put("/borradores/" + ej.value.id, { sql: sql.value });
        ultimoGuardado = sql.value;
        guardado.value = "Borrador guardado";
        setTimeout(() => (guardado.value = ""), 1500);
        if (manual) U.toast("Guardado");
      } catch (e) {}
    }
    onBeforeUnmount(() => { clearTimeout(timer); guardar(false); });

    async function ejecutar() {
      if (!sql.value.trim()) return U.toast("Escribí una consulta primero");
      cargando.value = true; tabR.value = "resultado";
      try {
        const r = await U.api.post("/ejercicios/" + ej.value.id + "/ejecutar", { sql: sql.value, safe_updates: U.store.safeUpdates });
        resultado.value = r;
        ms.value = r.ms_total;
      } catch (e) { U.toast(e.message); }
      cargando.value = false;
    }
    async function corregir() {
      if (!sql.value.trim()) return U.toast("Escribí una consulta primero");
      cargando.value = true; tabR.value = "correccion";
      try {
        const r = await U.api.post("/ejercicios/" + ej.value.id + "/corregir", { sql: sql.value, safe_updates: U.store.safeUpdates });
        veredicto.value = r;
        ms.value = r.ms_total;
        if (r.resultado) resultado.value = { resultado: r.resultado };
        else if (r.pasos || r.cambios || r.estructuras) resultado.value = { pasos: r.pasos, cambios: r.cambios, estructuras: r.estructuras, error: r.error };
        else if (r.error) resultado.value = { error: r.error };
        ej.value.historial.unshift({ sql_texto: sql.value, correcto: r.ok ? 1 : 0, modo: "practica", fecha: new Date().toISOString().replace("T", " ") });
        if (r.ok) {
          const primera = !ej.value.resuelto;
          ej.value.resuelto = true;
          if (window.confetti) confetti({ particleCount: primera ? 140 : 60, spread: 75, origin: { x: 0.72, y: 0.75 }, scalar: 0.9 });
          if (U.store.catalogo) {
            const e = U.store.catalogo.ejercicios.find((x) => x.id === ej.value.id);
            if (e && !e.resuelto) {
              e.resuelto = true;
              const s = U.store.catalogo.secciones.find((x) => x.id === e.seccion);
              if (s) s.resueltos++;
            }
            if (e) e.intentos++;
          }
        } else if (U.store.catalogo) {
          const e = U.store.catalogo.ejercicios.find((x) => x.id === ej.value.id);
          if (e) e.intentos++;
        }
      } catch (e) { U.toast(e.message); }
      cargando.value = false;
    }
    async function verEsperado() {
      tabR.value = "esperado";
      if (esperado.value || ej.value.tipo === "ddl") return;
      cargando.value = true;
      try { esperado.value = await U.api.get("/ejercicios/" + ej.value.id + "/esperado"); } catch (e) { U.toast(e.message); }
      cargando.value = false;
    }
    async function verSolucion(sinPreguntar) {
      if (sol.value) return;
      if (sinPreguntar !== true && !ej.value.resuelto && !ej.value.vio_solucion && ej.value.historial.length < 2) {
        const ok = await U.confirmar("¿Ver la solución?", "Todavía no lo resolviste. Probá al menos una vez y usá las pistas: en el parcialito no vas a tener la solución a mano.", "Ver igual");
        if (!ok) return;
      }
      try { sol.value = await U.api.get("/ejercicios/" + ej.value.id + "/solucion"); ej.value.vio_solucion = true; } catch (e) { U.toast(e.message); }
    }
    function verPista(i) {
      if (i < pistasVistas.value) return;
      pistasVistas.value = i + 1;
      localStorage.setItem("parc-pistas-" + ej.value.id, String(pistasVistas.value));
    }
    async function marcar() {
      const r = await U.api.post("/marcados/" + ej.value.id);
      ej.value.marcado = r.marcado;
      if (U.store.catalogo) { const e = U.store.catalogo.ejercicios.find((x) => x.id === ej.value.id); if (e) e.marcado = r.marcado; }
      U.toast(r.marcado ? "Marcado para repasar ★" : "Desmarcado");
    }
    function cargar(texto) { sql.value = texto; U.toast("Cargado en el editor"); }
    function toggleSafe() {
      U.store.safeUpdates = !U.store.safeUpdates;
      localStorage.setItem("parc-safe", U.store.safeUpdates ? "1" : "0");
    }
    return { U, ej, errorCarga, sql, tabL, tabR, resultado, veredicto, esperado, sol, cargando, ms, drawer, filtroEsq, pistasVistas, guardado,
             casosBorde, placeholder, ejecutar, corregir, verEsperado, verSolucion, verPista, marcar, cargar, toggleSafe, guardar };
  },
};
