/* App principal: layout, router, login y pantalla de configuración */
(function () {
  const { createApp, ref, computed, onMounted, onBeforeUnmount, nextTick, watch } = Vue;

  function parsear() {
    const h = (location.hash || "#/").replace(/^#\/?/, "");
    const [a, b] = h.split("/");
    switch (a) {
      case "": case "inicio": return { nombre: "inicio", comp: "inicio", props: {} };
      case "ejercicios": return { nombre: "ejercicios", comp: "catalogo", props: { seccion: b || "" } };
      case "ej": return { nombre: "ejercicios", comp: "ejercicio", props: { id: b } };
      case "simulacro": return b ? { nombre: "simulacro", comp: "simulacro", props: { id: b } } : { nombre: "simulacro", comp: "simulacroInicio", props: {} };
      case "consola": return { nombre: "consola", comp: "consola", props: {} };
      case "esquema": return { nombre: "esquema", comp: "esquema", props: {} };
      case "machete": return { nombre: "machete", comp: "machete", props: {} };
      case "progreso": return { nombre: "progreso", comp: "progreso", props: {} };
      case "admin": return { nombre: "admin", comp: "admin", props: {} };
      default: return { nombre: "inicio", comp: "inicio", props: {} };
    }
  }

  // ------------------------------------------------------------------ Panel de administración
  window.Vistas.admin = {
    template: `
    <div class="page">
      <div class="page-head">
        <div><div class="page-title">Usuarios</div><div class="page-sub">Quiénes están usando la app. Si alguien que no conocés ocupó un lugar, borralo y se libera el cupo.</div></div>
        <button class="btn sm" @click="cargar"><ico n="refresh" c="sm"/> Actualizar</button>
      </div>
      <div v-if="!d" class="empty"><div class="spinner" style="margin:auto"></div></div>
      <template v-else>
        <div class="card pad" v-if="d.cupo" style="margin-bottom:16px">
          <div class="row"><b>Cupo</b><span class="spacer"></span><span class="tnum">{{ d.cupo.usados }} / {{ d.cupo.max }} cuentas</span></div>
          <div class="progress" style="margin-top:8px"><i :style="{width: (100 * d.cupo.usados / d.cupo.max) + '%', background: d.cupo.usados >= d.cupo.max ? 'var(--danger)' : 'var(--primary)'}"></i></div>
        </div>
        <div class="card" style="overflow-x:auto">
          <table class="dg" style="width:100%">
            <thead><tr><th>Usuario</th><th>Mail</th><th>Alta</th><th>Último acceso</th><th>Intentos</th><th>Resueltos</th><th></th></tr></thead>
            <tbody>
              <tr v-for="u in d.usuarios" :key="u.id">
                <td style="font-family:var(--font)"><div class="row" style="gap:8px">
                  <img v-if="u.foto" :src="u.foto" referrerpolicy="no-referrer" style="width:26px;height:26px;border-radius:50%">
                  <b>{{ u.nombre }}</b><span v-if="u.es_admin" class="badge primary" style="height:18px;font-size:10.5px">admin</span></div></td>
                <td>{{ u.email }}</td>
                <td>{{ (u.creado || '').slice(0, 16) }}</td>
                <td>{{ (u.ultimo_acceso || '').slice(0, 16) }}</td>
                <td class="num">{{ u.intentos }}</td>
                <td class="num">{{ u.resueltos }} / {{ d.total_ejercicios }}</td>
                <td><button v-if="!u.es_admin" class="btn sm danger" @click="borrar(u)"><ico n="trash" c="xs"/> Borrar</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="card pad" style="margin-top:16px">
          <div class="card-title"><ico n="undo" c="sm"/> Base de práctica compartida</div>
          <p class="muted small" style="margin:6px 0 12px">Los ejercicios y la consola deshacen sus cambios solos, así que normalmente no hace falta. Si algo quedara raro, la podés volver a los datos originales.</p>
          <button class="btn sm danger" @click="restaurar" :disabled="restaurando"><ico n="undo" c="sm"/> {{ restaurando ? 'Restaurando…' : 'Restaurar base de práctica' }}</button>
        </div>
      </template>
    </div>`,
    setup() {
      const d = ref(null);
      const restaurando = ref(false);
      async function cargar() { try { d.value = await U.api.get("/admin/usuarios"); } catch (e) { U.toast(e.message); } }
      onMounted(cargar);
      async function borrar(u) {
        const ok = await U.confirmar("Borrar a " + u.nombre, "Se borra su cuenta y todo su progreso (" + u.email + "), y se libera un lugar del cupo.", "Borrar", true);
        if (!ok) return;
        try { await U.api(`/admin/usuarios/${u.id}`, { method: "DELETE" }); U.toast("Usuario borrado"); cargar(); } catch (e) { U.toast(e.message); }
      }
      async function restaurar() {
        const ok = await U.confirmar("Restaurar la base de práctica", "Vuelve los datos originales del dump. Tarda unos segundos.", "Restaurar", true);
        if (!ok) return;
        restaurando.value = true;
        try { const r = await U.api.post("/restaurar"); U.toast("Base restaurada (" + r.segundos + " s)"); } catch (e) { U.toast(e.message); }
        restaurando.value = false;
      }
      return { d, cargar, borrar, restaurar, restaurando };
    },
  };

  // ------------------------------------------------------------------ Raíz
  const Root = {
    template: `
    <div v-if="estado === null" class="placeholder" style="height:100vh"><div class="spinner"></div></div>

    <!-- ============ Login con Google (versión online) ============ -->
    <div v-else-if="estado.multiusuario && (!U.store.usuario || U.store.necesitaLogin)" class="login-wrap">
      <div class="login-card">
        <div class="brand" style="padding:0 0 18px;justify-content:center"><div class="brand-logo"><ico n="database"/></div><div style="text-align:left"><div class="brand-name" style="color:var(--text)">Parcialito BD</div><div class="brand-sub">Práctica de SQL · UCC</div></div></div>
        <h1 class="login-title">Practicá SQL para el parcialito</h1>
        <p class="muted" style="margin:8px 0 22px">Ejercicios del TP1 y de la Clase Semana 10 corregidos al instante, simulacros con reloj, machete y el DER interactivo. Tu progreso queda guardado en tu cuenta.</p>
        <div ref="botonGoogle" class="google-btn"></div>
        <div v-if="errorLogin" class="note warn" style="text-align:left"><ico n="alert" c="sm"/><div>{{ errorLogin }}</div></div>
        <div v-if="estado.cupo" class="small muted" style="margin-top:18px">
          <div class="progress" style="max-width:240px;margin:0 auto 6px"><i :style="{width: (100 * estado.cupo.usados / estado.cupo.max) + '%'}"></i></div>
          {{ estado.cupo.usados }} de {{ estado.cupo.max }} lugares ocupados
        </div>
        <div v-if="!estado.listo" class="note warn" style="text-align:left"><ico n="alert" c="sm"/><div>La base de datos no está disponible en este momento. Probá en un ratito.</div></div>
      </div>
    </div>

    <!-- ============ Configuración inicial (versión local) ============ -->
    <div v-else-if="!estado.conectado || !estado.listo" class="setup">
      <div class="brand" style="padding:0 0 20px"><div class="brand-logo"><ico n="database"/></div><div><div class="brand-name" style="color:var(--text)">Parcialito BD</div><div class="brand-sub">Configuración inicial</div></div></div>
      <div class="card pad" v-if="!estado.conectado">
        <h2 style="font-size:20px;margin-bottom:8px">No me puedo conectar a MySQL</h2>
        <p class="muted">La app usa un usuario propio de MySQL llamado <code>parcialito</code> (solo puede tocar las bases <code>parcialito_*</code>; tu base <code>universidad</code> queda intacta). Para crearlo, abrí la Terminal en la carpeta del proyecto y ejecutá (te va a pedir la contraseña de <b>root</b> de MySQL):</p>
        <pre>/usr/local/mysql/bin/mysql -u root -p &lt; setup/crear_usuario.sql</pre>
        <p class="muted small">O directamente <code>./iniciar.command</code>, que hace todo. Detalle del error: <code>{{ estado.error }}</code></p>
        <button class="btn primary" @click="cargarEstado"><ico n="refresh" c="sm"/> Reintentar</button>
      </div>
      <div class="card pad" v-else>
        <h2 style="font-size:20px;margin-bottom:8px">Falta preparar la base de práctica</h2>
        <p class="muted">Voy a importar <code>BD-Universidad.sql</code> en una base propia de la app (<code>parcialito_uni</code>) y crear tu base de práctica. Tarda unos segundos.</p>
        <button class="btn primary" @click="instalar" :disabled="instalando"><ico n="database" c="sm"/> {{ instalando ? 'Preparando…' : 'Preparar base' }}</button>
        <pre v-if="log.length" style="margin-top:14px">{{ log.join('\\n') }}</pre>
      </div>
    </div>

    <!-- ============ App ============ -->
    <div v-else class="app">
      <aside class="sidebar">
        <div class="brand"><div class="brand-logo"><ico n="database"/></div><div><div class="brand-name">Parcialito BD</div><div class="brand-sub">Práctica de SQL · UCC</div></div></div>
        <div class="nav-item" :class="{active: ruta.nombre === 'inicio'}" @click="U.irA('#/')"><ico n="home"/> Inicio</div>
        <div class="nav-item" :class="{active: ruta.nombre === 'ejercicios'}" @click="U.irA('#/ejercicios')"><ico n="list"/> Ejercicios <span class="count">{{ resueltos }}/{{ total }}</span></div>
        <div class="nav-item" :class="{active: ruta.nombre === 'simulacro'}" @click="U.irA('#/simulacro')"><ico n="timer"/> Simulacro</div>
        <div class="nav-label">Herramientas</div>
        <div class="nav-item" :class="{active: ruta.nombre === 'consola'}" @click="U.irA('#/consola')"><ico n="terminal"/> Consola SQL</div>
        <div class="nav-item" :class="{active: ruta.nombre === 'esquema'}" @click="U.irA('#/esquema')"><ico n="database"/> Esquema (DER)</div>
        <div class="nav-item" :class="{active: ruta.nombre === 'machete'}" @click="U.irA('#/machete')"><ico n="book"/> Machete</div>
        <div class="nav-item" :class="{active: ruta.nombre === 'progreso'}" @click="U.irA('#/progreso')"><ico n="chart"/> Mi progreso</div>
        <div v-if="estado.multiusuario && U.store.admin" class="nav-item" :class="{active: ruta.nombre === 'admin'}" @click="U.irA('#/admin')"><ico n="users"/> Usuarios <span class="count" v-if="estado.cupo">{{ estado.cupo.usados }}/{{ estado.cupo.max }}</span></div>
        <div class="sidebar-foot">
          <div class="countdown" @click="cambiarFecha" style="cursor:pointer" title="Clic para cambiar la fecha">
            <div class="t">Parcialito</div>
            <div class="v">{{ cuenta.titulo }}</div>
            <div class="s">{{ cuenta.sub }}</div>
          </div>
          <div v-if="estado.multiusuario && U.store.usuario" class="user-chip">
            <img v-if="U.store.usuario.foto" :src="U.store.usuario.foto" referrerpolicy="no-referrer">
            <span v-else class="avatar">{{ (U.store.usuario.nombre || '?').slice(0, 1).toUpperCase() }}</span>
            <div style="min-width:0;flex:1"><div class="un">{{ U.store.usuario.nombre }}</div><div class="ue">{{ U.store.usuario.email }}</div></div>
            <button class="icon-btn-dark" @click="salir" title="Cerrar sesión"><ico n="logout" c="sm"/></button>
          </div>
          <div class="sidebar-row">
            <span class="status-dot" :class="{off: !estado.conectado}"><i></i> {{ estado.multiusuario ? 'En línea' : 'MySQL conectado' }}</span>
            <button class="icon-btn-dark" @click="U.setTema(U.store.tema === 'dark' ? 'light' : 'dark')" title="Cambiar tema"><ico :n="U.store.tema === 'dark' ? 'sun' : 'moon'" c="sm"/></button>
          </div>
        </div>
      </aside>
      <main class="main">
        <component :is="ruta.comp" v-bind="ruta.props"/>
      </main>
    </div>

    <div class="toasts"><div v-for="t in U.store.toasts" :key="t.id" class="toast"><ico n="check" c="sm"/> {{ t.msg }}</div></div>
    <div v-if="U.store.modal" class="modal-bg" @click.self="U.store.modal.resolve(false)">
      <div class="modal">
        <h3>{{ U.store.modal.titulo }}</h3>
        <p>{{ U.store.modal.texto }}</p>
        <div class="acts">
          <button class="btn" @click="U.store.modal.resolve(false)">Cancelar</button>
          <button class="btn" :class="U.store.modal.peligro ? 'danger' : 'primary'" @click="U.store.modal.resolve(true)">{{ U.store.modal.ok }}</button>
        </div>
      </div>
    </div>`,
    setup() {
      const ruta = ref(parsear());
      const estado = ref(null);
      const instalando = ref(false);
      const log = ref([]);
      const errorLogin = ref("");
      const botonGoogle = ref(null);
      const fecha = ref(localStorage.getItem("parc-fecha") || "2026-10-16");
      const ahora = ref(new Date());
      const onHash = () => { ruta.value = parsear(); };
      let reloj;
      onMounted(() => {
        window.addEventListener("hashchange", onHash);
        cargarEstado();
        reloj = setInterval(() => (ahora.value = new Date()), 30000);
      });
      onBeforeUnmount(() => { window.removeEventListener("hashchange", onHash); clearInterval(reloj); });

      async function cargarEstado() {
        try {
          const e = await U.api.get("/estado");
          estado.value = e;
          U.store.multiusuario = !!e.multiusuario;
          U.store.usuario = e.usuario || null;
          U.store.admin = !e.multiusuario || !!e.admin;
          U.store.necesitaLogin = false;
          if (e.listo && (!e.multiusuario || e.usuario)) { U.cargarCatalogo().catch(() => {}); U.cargarEsquema().catch(() => {}); }
          if (e.multiusuario && !e.usuario) mostrarBotonGoogle();
        } catch (err) {
          estado.value = { conectado: false, listo: false, error: err.message };
        }
      }
      // si una llamada a la API devuelve 401 (sesión vencida), volver al login
      watch(() => U.store.necesitaLogin, (v) => { if (v && estado.value && estado.value.multiusuario) { U.store.usuario = null; mostrarBotonGoogle(); } });

      function cargarScriptGoogle() {
        return new Promise((resolve, reject) => {
          if (window.google && google.accounts && google.accounts.id) return resolve();
          const s = document.createElement("script");
          s.src = "https://accounts.google.com/gsi/client";
          s.async = true;
          s.onload = () => resolve();
          s.onerror = () => reject(new Error("No se pudo cargar el inicio de sesión de Google. ¿Hay internet?"));
          document.head.appendChild(s);
        });
      }
      async function mostrarBotonGoogle() {
        try {
          await cargarScriptGoogle();
          await nextTick();
          google.accounts.id.initialize({ client_id: estado.value.google_client_id, callback: alIngresar, ux_mode: "popup", auto_select: false });
          if (botonGoogle.value) {
            botonGoogle.value.innerHTML = "";
            google.accounts.id.renderButton(botonGoogle.value, { theme: U.store.tema === "dark" ? "filled_black" : "filled_blue", size: "large", shape: "pill", text: "signin_with", locale: "es", width: 300 });
          }
        } catch (e) { errorLogin.value = e.message; }
      }
      async function alIngresar(resp) {
        errorLogin.value = "";
        try {
          const r = await U.api.post("/login", { credential: resp.credential });
          U.store.usuario = r.usuario;
          U.toast("¡Hola, " + (r.usuario.nombre || "").split(" ")[0] + "!");
          await cargarEstado();
        } catch (e) { errorLogin.value = e.message; }
      }
      async function salir() {
        try { await U.api.post("/logout"); } catch (e) {}
        try { google.accounts.id.disableAutoSelect(); } catch (e) {}
        U.store.usuario = null;
        U.store.catalogo = null;
        location.hash = "#/";
        location.reload();
      }
      async function instalar() {
        instalando.value = true;
        try { const r = await U.api.post("/instalar"); log.value = r.log; await cargarEstado(); } catch (e) { log.value = [e.message]; }
        instalando.value = false;
      }
      const total = computed(() => (U.store.catalogo ? U.store.catalogo.ejercicios.length : 0));
      const resueltos = computed(() => (U.store.catalogo ? U.store.catalogo.ejercicios.filter((e) => e.resuelto).length : 0));
      const cuenta = computed(() => {
        const [y, m, d] = fecha.value.split("-").map(Number);
        const objetivo = new Date(y, m - 1, d);
        const hoy = new Date(ahora.value.getFullYear(), ahora.value.getMonth(), ahora.value.getDate());
        const dias = Math.round((objetivo - hoy) / 86400000);
        const dia = objetivo.toLocaleDateString("es-AR", { weekday: "long", day: "numeric", month: "numeric" });
        if (dias < 0) return { titulo: "¡Ya pasó!", sub: "Ojalá te haya ido bárbaro 🎉" };
        if (dias === 0) return { titulo: "¡Es hoy!", sub: "Respirá hondo, vos sabés." };
        if (dias === 1) {
          const h = Math.max(0, Math.round((objetivo - ahora.value) / 3600000));
          return { titulo: "Mañana", sub: dia + " · faltan ~" + h + " h" };
        }
        return { titulo: "En " + dias + " días", sub: dia };
      });
      function cambiarFecha() {
        const v = prompt("Fecha del parcialito (AAAA-MM-DD):", fecha.value);
        if (v && /^\d{4}-\d{2}-\d{2}$/.test(v)) { fecha.value = v; localStorage.setItem("parc-fecha", v); }
      }
      return { U, ruta, estado, instalando, log, errorLogin, botonGoogle, total, resueltos, cuenta, cargarEstado, instalar, cambiarFecha, salir };
    },
  };

  const app = createApp(Root);
  registrarComponentes(app);
  for (const [nombre, comp] of Object.entries(window.Vistas)) app.component(nombre, comp);
  app.config.errorHandler = (err) => { console.error(err); U.toast("Error en la interfaz: " + err.message, 5000); };
  app.mount("#app");
})();
