window.Vistas = window.Vistas || {};

const TIPS = [
  "**WHERE filtra filas, HAVING filtra grupos.** Si la condición usa COUNT, SUM o AVG, va en el HAVING.",
  "Para «los que **no** tienen…» usá `NOT EXISTS` o `LEFT JOIN … WHERE x.id IS NULL`. Con `INNER JOIN` nunca vas a ver a los que no tienen relación.",
  "Con `ONLY_FULL_GROUP_BY`, toda columna del SELECT que no esté en una función de agregación tiene que ir en el GROUP BY.",
  "`COUNT(*)` cuenta filas; `COUNT(col)` no cuenta NULLs; `COUNT(DISTINCT col)` cuenta valores distintos. Elegí bien qué estás contando.",
  "Si un JOIN te multiplica filas, preguntate: ¿estoy contando alumnos o inscripciones? A veces la respuesta es `COUNT(DISTINCT id_alumno)`.",
  "El alias de una columna del SELECT **no** se puede usar en el WHERE (se evalúa antes), pero sí en HAVING y ORDER BY.",
  "Para comparar contra un promedio de conteos: `HAVING COUNT(*) > (SELECT AVG(c) FROM (SELECT COUNT(*) c FROM … GROUP BY …) t)`. Toda tabla derivada necesita alias.",
  "En una vista no puede haber dos columnas con el mismo nombre: si unís alumnos y carreras, poné `c.nombre AS carrera`.",
  "Los valores de los ENUM respetan mayúsculas: `'Baja'`, `'Regular'`, `'Febrero'`… pero `'activa'`, `'teorica'`, `'parcial'` van en minúscula. Están todos en el Machete.",
  "`NOT IN (subconsulta)` falla si la subconsulta devuelve algún NULL (no devuelve nada). `NOT EXISTS` no tiene ese problema.",
  "Antes de escribir, preguntate: ¿qué devuelvo (una fila por qué)?, ¿qué tablas necesito?, ¿qué filtro antes de agrupar?, ¿qué filtro después?",
];

Vistas.inicio = {
  template: `
  <div class="page">
    <div class="hero">
      <div style="position:relative;z-index:1">
        <div class="badge" style="background:rgba(255,255,255,.16);color:#fff;margin-bottom:12px"><ico n="graduation" c="xs"/> Base de Datos · UCC</div>
        <h1>{{ saludo }}</h1>
        <p>Ejercicios al estilo del TP1 y de la Clase Semana 10, corregidos al instante contra la base real de la universidad. Practicá, equivocate acá y aprobá mañana.</p>
        <div class="row wrap">
          <button class="btn lg white" @click="continuar"><ico n="play" c="sm"/> {{ resueltosP ? 'Seguir practicando' : 'Empezar a practicar' }}</button>
          <button class="btn lg glass" @click="U.irA('#/simulacro')"><ico n="timer" c="sm"/> Simulacro</button>
          <button class="btn lg glass" @click="U.irA('#/machete')"><ico n="book" c="sm"/> Machete</button>
        </div>
      </div>
      <progress-ring :value="totalP ? resueltosP / totalP : 0" :size="148" :stroke="12" style="position:relative;z-index:1">
        <b>{{ totalP ? Math.round(100 * resueltosP / totalP) : 0 }}%</b><span>{{ resueltosP }}/{{ totalP }} del parcialito</span>
      </progress-ring>
    </div>

    <div class="stats">
      <div class="card stat"><div class="k"><ico n="check" c="xs"/> Resueltos (parcialito)</div><div class="v">{{ resueltosP }} <small>/ {{ totalP }}</small></div></div>
      <div class="card stat"><div class="k"><ico n="zap" c="xs"/> Intentos</div><div class="v">{{ prog ? prog.intentos_totales : 0 }}</div></div>
      <div class="card stat"><div class="k"><ico n="target" c="xs"/> Precisión</div><div class="v">{{ precision }}<small>%</small></div></div>
      <div class="card stat"><div class="k"><ico n="trophy" c="xs"/> Último simulacro</div><div class="v">{{ ultimaNota }}</div></div>
    </div>

    <div class="section-h"><h2>Plan de estudio</h2><span class="muted small">en el orden recomendado · lo que entra en el parcialito</span></div>
    <div class="plan" v-if="cat">
      <div v-for="(s, i) in seccionesP" :key="s.id" class="card sec-card" :style="{'--sc': 'var(--c-' + s.id + ')'}" @click="U.irA('#/ejercicios/' + s.id)">
        <span class="num">{{ i + 1 }}</span>
        <div class="top"><div class="sec-ico"><ico :n="U.SECC_ICON[s.id]"/></div><div><h3>{{ s.nombre }}</h3><div class="small muted">{{ s.origen }}</div></div></div>
        <div class="desc">{{ s.descripcion }}</div>
        <div class="foot"><div class="progress"><i :style="{width: (s.total ? 100 * s.resueltos / s.total : 0) + '%'}"></i></div><span class="tnum">{{ s.resueltos }}/{{ s.total }}</span></div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns: 1.3fr 1fr; margin-top: 26px; align-items: start">
      <div>
        <div class="section-h"><h2>Cómo usar la app</h2></div>
        <div class="card pad">
          <div class="steps-guide">
            <div><div><b>Elegí un ejercicio</b> y leé el enunciado. Abajo a la derecha tenés el esquema de tablas a mano (botón <span class="kbd-hint">Esquema</span>).</div></div>
            <div><div><b>Escribí tu SQL</b> y probalo con <span class="kbd-hint">⌘ ↵</span> (Ejecutar). Ves el resultado como en Workbench.</div></div>
            <div><div><b>Corregí</b> con <span class="kbd-hint">⌘ ⇧ ↵</span>: la app compara tu resultado con el de la solución (sin importar alias ni orden de columnas) y te dice qué falta o sobra.</div></div>
            <div><div>Si te trabás, usá las <b>pistas</b> de a una. Al final mirá la <b>solución explicada</b> y las otras formas de resolverlo.</div></div>
            <div><div>Cuando te sientas listo, hacé un <b>simulacro</b> con tiempo y sin ayudas.</div></div>
          </div>
        </div>
      </div>
      <div>
        <div class="section-h"><h2>Tip</h2><span class="spacer"></span><button class="btn ghost sm" @click="tip = (tip + 1) % TIPS.length"><ico n="refresh" c="xs"/> otro</button></div>
        <div class="card tip"><div class="ti"><ico n="bulb"/></div><md-view :texto="TIPS[tip]"/></div>
        <div class="section-h" style="margin-top:22px"><h2>Práctica extra</h2><span class="badge outline">no entra</span></div>
        <div class="grid" style="gap:10px">
          <div v-for="s in seccionesX" :key="s.id" class="card ex-card" :style="{'--sc': 'var(--c-' + s.id + ')'}" @click="U.irA('#/ejercicios/' + s.id)">
            <div class="sec-ico" style="width:34px;height:34px"><ico :n="U.SECC_ICON[s.id]" c="sm"/></div>
            <div class="body"><div class="t">{{ s.nombre }}</div><div class="m">{{ s.resueltos }}/{{ s.total }} resueltos · {{ s.origen }}</div></div>
            <ico n="right" c="sm"/>
          </div>
        </div>
      </div>
    </div>
  </div>`,
  setup() {
    const { ref, computed, onMounted } = Vue;
    const cat = computed(() => U.store.catalogo);
    const prog = ref(null);
    const tip = ref(Math.floor(Math.random() * TIPS.length));
    onMounted(async () => {
      U.cargarCatalogo().catch((e) => U.toast(e.message));
      try { prog.value = await U.api.get("/progreso"); } catch (e) {}
    });
    const seccionesP = computed(() => (cat.value ? cat.value.secciones.filter((s) => s.grupo === "parcialito") : []));
    const seccionesX = computed(() => (cat.value ? cat.value.secciones.filter((s) => s.grupo === "extra") : []));
    const totalP = computed(() => seccionesP.value.reduce((a, s) => a + s.total, 0));
    const resueltosP = computed(() => seccionesP.value.reduce((a, s) => a + s.resueltos, 0));
    const precision = computed(() => {
      const p = prog.value;
      return p && p.intentos_totales ? Math.round((100 * p.intentos_correctos) / p.intentos_totales) : 0;
    });
    const ultimaNota = computed(() => {
      const p = prog.value;
      return p && p.simulacros.length ? p.simulacros[0].nota.toFixed(1).replace(".0", "") + "/10" : "—";
    });
    const saludo = computed(() => {
      const h = new Date().getHours();
      const m = h < 6 ? "Última repasada antes de dormir" : h < 13 ? "Buen día, a preparar el parcialito" : h < 20 ? "Buenas tardes, a meterle al SQL" : "Buenas noches, repaso final";
      return m;
    });
    function continuar() {
      const c = cat.value;
      if (!c) return;
      const orden = c.secciones.filter((s) => s.grupo === "parcialito").map((s) => s.id);
      const pend = c.ejercicios.filter((e) => orden.includes(e.seccion) && !e.resuelto)
        .sort((a, b) => orden.indexOf(a.seccion) - orden.indexOf(b.seccion));
      if (pend.length) U.irA("#/ej/" + pend[0].id);
      else U.irA("#/simulacro");
    }
    return { U, cat, prog, tip, TIPS, seccionesP, seccionesX, totalP, resueltosP, precision, ultimaNota, saludo, continuar };
  },
};

// ======================================================================= Catálogo
Vistas.catalogo = {
  props: { seccion: String },
  template: `
  <div class="page">
    <div class="page-head">
      <div><div class="page-title">Ejercicios</div><div class="page-sub">{{ cat ? cat.ejercicios.length : '…' }} ejercicios corregidos automáticamente · elegí uno y a practicar.</div></div>
      <div class="search"><ico n="search" c="sm"/><input class="input" v-model="q" placeholder="Buscar (ej. HAVING, vista, docentes)"></div>
    </div>
    <div class="filters">
      <span class="chip" :class="{active: !sec}" @click="U.irA('#/ejercicios')">Todas <span class="n">{{ cat ? cat.ejercicios.length : '' }}</span></span>
      <span v-for="s in (cat ? cat.secciones : [])" class="chip" :class="{active: sec === s.id}" @click="U.irA('#/ejercicios/' + s.id)">
        {{ s.corto }} <span class="n">{{ s.resueltos }}/{{ s.total }}</span>
      </span>
    </div>
    <div class="filters" style="margin-top:-8px">
      <span v-for="e in estados" class="chip" :class="{active: estado === e.id}" @click="estado = e.id" style="height:28px;font-size:12.5px">{{ e.nombre }}</span>
      <span class="spacer"></span>
      <span class="small muted">Dificultad</span>
      <span v-for="d in [0,1,2,3]" class="chip" :class="{active: dif === d}" @click="dif = d" style="height:28px;font-size:12.5px">
        <template v-if="d === 0">Todas</template><dif-dots v-else :d="d"/>
      </span>
    </div>

    <div v-if="!cat" class="empty"><div class="spinner" style="margin:auto"></div></div>
    <template v-else>
      <div v-for="g in grupos" :key="g.s.id" class="cat-group">
        <div class="cat-head" :style="{'--sc': 'var(--c-' + g.s.id + ')'}">
          <div class="sec-ico" style="width:30px;height:30px;border-radius:9px"><ico :n="U.SECC_ICON[g.s.id]" c="sm"/></div>
          <h3>{{ g.s.nombre }}</h3><span class="badge outline">{{ g.s.origen }}</span>
          <span v-if="g.s.grupo === 'extra'" class="badge warning">no entra en el parcialito</span>
          <span class="spacer"></span><span class="small muted tnum">{{ g.s.resueltos }}/{{ g.s.total }} resueltos</span>
        </div>
        <div v-if="g.s.grupo === 'extra' && sec === g.s.id" class="extra-banner"><ico n="info"/> Esta sección es práctica extra: DML y DDL no se toman en el parcialito, pero sirven para entender cómo se modifican los datos y la estructura.</div>
        <div class="ex-list">
          <div v-for="e in g.items" :key="e.id" class="card ex-card" @click="U.irA('#/ej/' + e.id)">
            <div class="ex-status" :class="e.resuelto ? 'ok' : (e.intentos ? 'try' : '')">
              <ico v-if="e.resuelto" n="check" c="sm"/><ico v-else-if="e.intentos" n="edit" c="xs"/><span v-else class="small faint" style="font-weight:700">{{ num(e) }}</span>
            </div>
            <div class="body">
              <div class="t">{{ e.titulo }}</div>
              <div class="m"><dif-dots :d="e.dificultad"/><span>{{ e.origen }}</span><span v-if="e.tipo !== 'select'" class="badge" style="height:18px;font-size:10.5px">{{ U.TIPO_NOMBRE[e.tipo] }}</span><span v-if="e.intentos && !e.resuelto">· {{ e.intentos }} intento(s)</span></div>
            </div>
            <ico v-if="e.marcado" n="star" c="sm" style="color:#f59e0b"/>
          </div>
        </div>
      </div>
      <div v-if="!grupos.length" class="empty">No hay ejercicios con esos filtros.</div>
    </template>
  </div>`,
  setup(props) {
    const { ref, computed, onMounted } = Vue;
    const cat = computed(() => U.store.catalogo);
    const q = ref("");
    const estado = ref("todos");
    const dif = ref(0);
    const sec = computed(() => props.seccion || "");
    onMounted(() => U.cargarCatalogo().catch((e) => U.toast(e.message)));
    const estados = [{ id: "todos", nombre: "Todos" }, { id: "pendientes", nombre: "Pendientes" }, { id: "resueltos", nombre: "Resueltos" }, { id: "marcados", nombre: "★ Marcados" }];
    const grupos = computed(() => {
      if (!cat.value) return [];
      const qq = q.value.trim().toLowerCase();
      return cat.value.secciones
        .filter((s) => !sec.value || s.id === sec.value)
        .map((s) => ({
          s,
          items: cat.value.ejercicios.filter((e) => e.seccion === s.id)
            .filter((e) => estado.value === "todos" || (estado.value === "pendientes" && !e.resuelto) || (estado.value === "resueltos" && e.resuelto) || (estado.value === "marcados" && e.marcado))
            .filter((e) => !dif.value || e.dificultad === dif.value)
            .filter((e) => !qq || (e.titulo + " " + e.tags.join(" ") + " " + e.origen + " " + e.id).toLowerCase().includes(qq)),
        }))
        .filter((g) => g.items.length);
    });
    function num(e) {
      const lista = cat.value.ejercicios.filter((x) => x.seccion === e.seccion);
      return lista.indexOf(e) + 1;
    }
    return { U, cat, q, estado, dif, sec, estados, grupos, num };
  },
};
