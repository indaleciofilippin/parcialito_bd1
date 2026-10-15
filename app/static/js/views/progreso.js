window.Vistas = window.Vistas || {};

Vistas.progreso = {
  template: `
  <div class="page">
    <div class="page-head">
      <div><div class="page-title">Mi progreso</div><div class="page-sub">Qué dominás y qué te conviene repasar antes del parcialito.</div></div>
      <button class="btn sm danger" @click="reiniciar"><ico n="trash" c="sm"/> Reiniciar progreso</button>
    </div>
    <div v-if="!p" class="empty"><div class="spinner" style="margin:auto"></div></div>
    <template v-else>
      <div class="stats" style="margin-top:0">
        <div class="card stat"><div class="k"><ico n="check" c="xs"/> Resueltos (parcialito)</div><div class="v">{{ resP }} <small>/ {{ totP }}</small></div></div>
        <div class="card stat"><div class="k"><ico n="zap" c="xs"/> Intentos corregidos</div><div class="v">{{ p.intentos_totales }}</div></div>
        <div class="card stat"><div class="k"><ico n="target" c="xs"/> Precisión</div><div class="v">{{ p.intentos_totales ? Math.round(100 * p.intentos_correctos / p.intentos_totales) : 0 }}<small>%</small></div></div>
        <div class="card stat"><div class="k"><ico n="trophy" c="xs"/> Mejor simulacro</div><div class="v">{{ mejor }}</div></div>
      </div>
      <div class="grid" style="grid-template-columns: 1.2fr 1fr; align-items:start">
        <div class="card pad">
          <div class="card-title" style="margin-bottom:10px"><ico n="layers" c="sm"/> Por sección</div>
          <div v-for="s in p.secciones" class="sec-prog" :style="{'--sc': 'var(--c-' + s.id + ')'}">
            <a :href="'#/ejercicios/' + s.id" style="color:var(--text);font-weight:600">{{ s.corto }} <span v-if="s.grupo === 'extra'" class="badge outline" style="height:17px;font-size:10px">extra</span></a>
            <div class="progress"><i :style="{width: (s.total ? 100 * s.resueltos / s.total : 0) + '%', background: 'var(--sc)'}"></i></div>
            <span class="small muted tnum" style="text-align:right">{{ s.resueltos }}/{{ s.total }}</span>
          </div>
          <div v-if="debiles.length" class="note warn" style="margin-top:14px"><ico n="flag" c="sm"/>
            <div>Te conviene repasar: <b>{{ debiles.map(s => s.corto).join(', ') }}</b>.
              <a :href="'#/ejercicios/' + debiles[0].id">Ir a practicar →</a></div>
          </div>
        </div>
        <div class="card pad">
          <div class="card-title" style="margin-bottom:4px"><ico n="chart" c="sm"/> Actividad por día</div>
          <div class="small muted">Intentos corregidos (verde = correctos)</div>
          <div v-if="!dias.length" class="empty small">Sin actividad todavía.</div>
          <div v-else class="bars">
            <div v-for="d in dias" class="b" :title="d.dia + ': ' + d.correctos + '/' + d.intentos + ' correctos'">
              <span class="tnum" style="color:var(--text-2);font-size:11px">{{ d.intentos }}</span>
              <div class="col" :style="{height: (100 * d.intentos / maxDia) + '%'}"><i :style="{height: (d.intentos ? 100 * d.correctos / d.intentos : 0) + '%'}"></i></div>
              <span>{{ d.dia.slice(8, 10) }}/{{ d.dia.slice(5, 7) }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="grid" style="grid-template-columns: 1fr 1fr; margin-top:16px; align-items:start">
        <div class="card pad">
          <div class="card-title" style="margin-bottom:10px"><ico n="history" c="sm"/> Últimos intentos</div>
          <div v-if="!p.recientes.length" class="empty small">Todavía nada.</div>
          <div v-for="r in p.recientes" class="hist-item" @click="U.irA('#/ej/' + r.ejercicio_id)">
            <span class="ex-status" :class="r.correcto ? 'ok' : 'try'" style="width:24px;height:24px"><ico :n="r.correcto ? 'check' : 'x'" c="xs"/></span>
            <span style="flex:1;font-weight:560;font-size:13px">{{ r.titulo }}</span>
            <span v-if="r.modo === 'simulacro'" class="badge" style="height:18px;font-size:10.5px">simulacro</span>
            <span class="small faint tnum">{{ r.fecha.slice(5, 16) }}</span>
          </div>
        </div>
        <div class="card pad">
          <div class="card-title" style="margin-bottom:10px"><ico n="timer" c="sm"/> Simulacros</div>
          <div v-if="!p.simulacros.length" class="empty small">Todavía no hiciste ninguno. <a href="#/simulacro">Hacer uno →</a></div>
          <div v-for="s in p.simulacros" class="hist-item" @click="U.irA('#/simulacro/' + s.id)">
            <span class="badge" :class="s.nota >= 6 ? 'success' : 'danger'" style="min-width:52px;justify-content:center">{{ s.nota }}/10</span>
            <span style="flex:1;font-size:13px">#{{ s.id }} · {{ s.n }} ejercicios</span>
            <span class="small faint tnum">{{ s.inicio.slice(5, 16) }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>`,
  setup() {
    const { ref, computed, onMounted } = Vue;
    const p = ref(null);
    async function cargar() { p.value = await U.api.get("/progreso"); }
    onMounted(() => cargar().catch((e) => U.toast(e.message)));
    const parc = computed(() => (p.value ? p.value.secciones.filter((s) => s.grupo === "parcialito") : []));
    const totP = computed(() => parc.value.reduce((a, s) => a + s.total, 0));
    const resP = computed(() => parc.value.reduce((a, s) => a + s.resueltos, 0));
    const dias = computed(() => (p.value ? p.value.dias.slice().reverse() : []));
    const maxDia = computed(() => Math.max(1, ...dias.value.map((d) => d.intentos)));
    const mejor = computed(() => (p.value && p.value.simulacros.length ? Math.max(...p.value.simulacros.map((s) => s.nota)) + "/10" : "—"));
    const debiles = computed(() => parc.value.filter((s) => s.total && s.resueltos / s.total < 0.6).sort((a, b) => a.resueltos / a.total - b.resueltos / b.total).slice(0, 3));
    async function reiniciar() {
      const ok = await U.confirmar("Reiniciar progreso", "Se borran tus intentos, borradores, marcados y simulacros. Los ejercicios y la base no se tocan.", "Reiniciar", true);
      if (!ok) return;
      await U.api.post("/progreso/reiniciar");
      U.toast("Progreso reiniciado");
      await cargar();
      U.cargarCatalogo().catch(() => {});
    }
    return { U, p, totP, resP, dias, maxDia, mejor, debiles, reiniciar };
  },
};
