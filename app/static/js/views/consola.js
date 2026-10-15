window.Vistas = window.Vistas || {};

const CONSOLA_INICIAL = `-- Consola libre: probá lo que quieras sobre la base de la universidad.
-- ⌘↵ ejecuta todo (o solo lo seleccionado). Varias sentencias separadas por ;

SELECT c.nombre AS carrera, COUNT(*) AS alumnos
FROM alumno_carrera ac
JOIN carreras c ON c.id_carrera = ac.id_carrera
WHERE ac.estado = 'activa'
GROUP BY c.id_carrera, c.nombre
ORDER BY alumnos DESC;
`;

Vistas.consola = {
  template: `
  <div class="console">
    <div class="console-side">
      <div class="drawer-h"><ico n="database" c="sm"/> Tablas <span class="spacer"></span>
        <button class="icon-btn" title="Recargar esquema" @click="U.cargarEsquema(true)"><ico n="refresh" c="sm"/></button></div>
      <div style="padding:8px 10px;border-bottom:1px solid var(--border)"><input class="input" style="width:100%;height:32px" v-model="filtro" placeholder="Filtrar"></div>
      <schema-tree :filtro="filtro" @insertar="t => $refs.ed.insertar(t)" @abrir="abrir"/>
      <div class="small muted" style="padding:10px 12px;border-top:1px solid var(--border);line-height:1.45">Clic: inserta el nombre · Doble clic en una tabla: <code>SELECT *</code></div>
    </div>
    <div class="console-main">
      <div class="toolbar">
        <button class="btn primary" @click="ejecutar" :disabled="cargando"><ico n="play" c="sm"/> {{ haySel ? 'Ejecutar selección' : 'Ejecutar' }} <span class="kbd">⌘↵</span></button>
        <button class="btn ghost sm" @click="$refs.ed.formatear()"><ico n="sparkles" c="sm"/> Formatear</button>
        <span class="spacer"></span>
        <label v-if="!U.store.multiusuario" class="toggle" :class="{on: guardar}" @click="guardar = !guardar" title="Apagado: INSERT/UPDATE/DELETE se deshacen al terminar. Encendido: los cambios quedan guardados en tu base de práctica.">
          <span class="sw"></span> Guardar cambios
        </label>
        <span v-else class="badge outline" title="La base es compartida: INSERT/UPDATE/DELETE se ejecutan y se deshacen al terminar."><ico n="shield" c="xs"/> Los cambios se deshacen solos</span>
        <label class="toggle" :class="{on: U.store.safeUpdates}" @click="toggleSafe" title="Simula Safe Updates de Workbench"><span class="sw"></span> Safe updates</label>
        <button v-if="!U.store.multiusuario" class="btn sm danger" @click="restaurar" title="Vuelve la base de práctica a los datos originales"><ico n="undo" c="sm"/> Restaurar base</button>
      </div>
      <sql-editor ref="ed" v-model="sql" @run="ejecutar" @save="() => U.toast('La consola se guarda sola')"/>
      <div class="hsplit" v-split="{var: '--edh', eje: 'y', min: 18, max: 80, offset: 52}"></div>
      <div class="results">
        <div class="tabs">
          <div v-for="(r, i) in conFilas" class="tab" :class="{active: tab === i}" @click="tab = i"><ico n="table" c="sm"/> Resultado {{ conFilas.length > 1 ? i + 1 : '' }}</div>
          <div class="tab" :class="{active: tab === 'log'}" @click="tab = 'log'"><ico n="terminal" c="sm"/> Salida <span v-if="res && res.error" class="badge danger">error</span></div>
          <span class="spacer"></span>
          <span v-if="res" class="small faint" style="align-self:center">{{ res.ms_total }} ms</span>
        </div>
        <div class="results-body" :class="{pad: tab === 'log' && res && res.error}">
          <div v-if="cargando" class="loading-cover"><div class="spinner"></div></div>
          <div v-if="!res" class="placeholder"><div><ico n="terminal"/><div>Los resultados aparecen acá.</div></div></div>
          <template v-else-if="tab !== 'log' && conFilas[tab]">
            <data-grid v-bind="conFilas[tab]"/>
          </template>
          <template v-else>
            <div v-if="res.deshecho" class="note info" style="margin:12px"><ico n="shield" c="sm"/><div>Los cambios se <b>deshicieron</b> al terminar{{ U.store.multiusuario ? ' (la base es compartida por todos)' : ' (está apagado «Guardar cambios»)' }}.</div></div>
            <div class="out-log">
              <div v-for="(r, i) in res.resultados" class="out-row">
                <span class="ex-status ok" style="width:20px;height:20px"><ico n="check" c="xs"/></span>
                <code>{{ (r.sql || '').replace(/\\s+/g, ' ') }}</code>
                <span class="muted tnum">{{ r.tipo === 'resultado' ? r.total + ' fila(s)' : r.afectadas + ' afectada(s)' }}</span>
                <span class="faint tnum">{{ r.ms }} ms</span>
              </div>
            </div>
            <error-card v-if="res.error" :error="res.error" style="margin:12px"/>
          </template>
        </div>
      </div>
    </div>
  </div>`,
  setup() {
    const { ref, computed, onMounted, watch } = Vue;
    const sql = ref(U.store.consolaSql || localStorage.getItem("parc-consola") || CONSOLA_INICIAL);
    if (U.store.consolaSql) U.store.consolaSql = null;
    const res = ref(null);
    const tab = ref("log");
    const cargando = ref(false);
    const guardar = ref(false);
    const filtro = ref("");
    const haySel = ref(false);
    const ed = ref(null);
    watch(sql, (v) => localStorage.setItem("parc-consola", v));
    const conFilas = computed(() => (res.value ? res.value.resultados.filter((r) => r.tipo === "resultado") : []));
    onMounted(() => {
      setInterval(() => { haySel.value = !!(ed.value && ed.value.seleccion()); }, 400);
    });
    async function ejecutar() {
      const texto = (ed.value && ed.value.seleccion()) || sql.value;
      if (!texto.trim()) return;
      cargando.value = true;
      try {
        const r = await U.api.post("/consola", { sql: texto, guardar: guardar.value, safe_updates: U.store.safeUpdates });
        res.value = r;
        const n = r.resultados.filter((x) => x.tipo === "resultado").length;
        tab.value = r.error || !n ? "log" : n - 1;
        if (guardar.value && r.resultados.some((x) => x.tipo === "ok")) U.cargarEsquema(true);
      } catch (e) { U.toast(e.message); }
      cargando.value = false;
    }
    function abrir(t) { sql.value = "SELECT *\nFROM " + t + "\nLIMIT 100;"; setTimeout(ejecutar, 50); }
    async function restaurar() {
      const ok = await U.confirmar("Restaurar la base de práctica", "Se borran todos los cambios que hiciste con «Guardar cambios» y vuelven los datos originales del dump. Tu progreso de ejercicios no se toca.", "Restaurar", true);
      if (!ok) return;
      cargando.value = true;
      try { const r = await U.api.post("/restaurar"); U.toast("Base restaurada (" + r.segundos + " s)"); U.cargarEsquema(true); } catch (e) { U.toast(e.message); }
      cargando.value = false;
    }
    function toggleSafe() {
      U.store.safeUpdates = !U.store.safeUpdates;
      localStorage.setItem("parc-safe", U.store.safeUpdates ? "1" : "0");
    }
    return { U, sql, res, tab, cargando, guardar, filtro, conFilas, ejecutar, abrir, restaurar, toggleSafe, haySel, ed };
  },
};
