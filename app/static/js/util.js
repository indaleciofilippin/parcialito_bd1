/* Utilidades globales: API, íconos, markdown, resaltado, estado compartido */
(function () {
  const { reactive } = Vue;

  // ---------------------------------------------------------------- API
  async function api(path, opts = {}) {
    const init = { method: opts.method || "GET", headers: {} };
    if (opts.body !== undefined) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(opts.body);
    }
    let r;
    try {
      r = await fetch("/api" + path, init);
    } catch (e) {
      throw new Error("No hay conexión con el servidor de la app. ¿Cerraste la terminal donde corre?");
    }
    let data = null;
    try { data = await r.json(); } catch (e) { /* vacío */ }
    if (r.status === 401 && data && data.login) {
      if (window.U && U.store) U.store.necesitaLogin = true;
    }
    if (!r.ok) throw new Error((data && data.error) || ("Error " + r.status));
    return data;
  }
  api.get = (p) => api(p);
  api.post = (p, body) => api(p, { method: "POST", body: body || {} });
  api.put = (p, body) => api(p, { method: "PUT", body: body || {} });

  // ---------------------------------------------------------------- Íconos (trazos estilo Lucide)
  const P = {
    home: '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/>',
    list: '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/>',
    timer: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2"/><path d="M9 2h6"/>',
    terminal: '<path d="m4 17 6-6-6-6"/><path d="M12 19h8"/>',
    database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    book: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    chart: '<path d="M3 3v18h18"/><path d="M7 16v-4M12 16V8M17 16v-7"/>',
    play: '<path d="M7 4v16l13-8z"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
    star: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z"/>',
    bulb: '<path d="M9 18h6M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2z"/>',
    eye: '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>',
    filter: '<path d="M22 3H2l8 9.46V19l4 2v-8.54z"/>',
    link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    layers: '<path d="M12 2 2 7l10 5 10-5z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    briefcase: '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
    moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9z"/>',
    right: '<path d="m9 18 6-6-6-6"/>',
    left: '<path d="m15 18-6-6 6-6"/>',
    down: '<path d="m6 9 6 6 6-6"/>',
    copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    sparkles: '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/>',
    undo: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
    alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3z"/><path d="M12 9v4M12 17h.01"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    lock: '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    flag: '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><path d="M4 22v-7"/>',
    target: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    trophy: '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0z"/>',
    history: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>',
    table: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/>',
    key: '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6M15.5 7.5l3 3L22 7l-3-3"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    zap: '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
    send: '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
    save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
    trash: '<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    graduation: '<path d="M22 10 12 5 2 10l10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>',
    columns: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 3v18"/>',
    code: '<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',
    clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    rocket: '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
    keyboard: '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M8 14h8"/>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    refresh: '<path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5M3 21v-5h5"/>',
    expand: '<path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>',
    dot: '<circle cx="12" cy="12" r="3"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5M21 12H9"/>',
  };
  function icon(name, cls) {
    return '<svg class="ico ' + (cls || "") + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + (P[name] || P.dot) + "</svg>";
  }

  // ---------------------------------------------------------------- Markdown + resaltado
  if (window.marked) {
    marked.setOptions({ gfm: true, breaks: false });
  }
  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function highlight(sql) {
    const out = [];
    if (!window.CodeMirror || !CodeMirror.runMode) return escapeHtml(sql);
    CodeMirror.runMode(sql, "text/x-mysql", function (text, style) {
      const t = escapeHtml(text);
      out.push(style ? '<span class="' + style.split(" ").map((s) => "cm-" + s).join(" ") + '">' + t + "</span>" : t);
    });
    return out.join("");
  }
  function md(texto) {
    if (!texto) return "";
    let html = window.marked ? marked.parse(texto) : escapeHtml(texto);
    // resaltar bloques ```sql
    html = html.replace(/<pre><code(?: class="language-(\w+)")?>([\s\S]*?)<\/code><\/pre>/g, function (_, lang, code) {
      const raw = code.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, "&");
      return "<pre><code>" + highlight(raw) + "</code></pre>";
    });
    return html;
  }
  function mdInline(texto) {
    if (!texto) return "";
    return window.marked ? marked.parseInline(texto) : escapeHtml(texto);
  }

  // ---------------------------------------------------------------- Estado global
  const store = reactive({
    tema: localStorage.getItem("parc-tema") || (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"),
    catalogo: null,
    esquema: null,
    estado: null,
    toasts: [],
    modal: null,
    safeUpdates: localStorage.getItem("parc-safe") === "1",
    consolaSql: null,
    necesitaLogin: false,
    derAbierto: localStorage.getItem("parc-der-abierto") === "1",
    multiusuario: false,
    usuario: null,
    admin: true,
  });

  function setTema(t) {
    store.tema = t;
    document.documentElement.setAttribute("data-theme", t);
    localStorage.setItem("parc-tema", t);
  }
  setTema(store.tema);

  function toast(msg, ms) {
    const t = { id: Math.random(), msg };
    store.toasts.push(t);
    setTimeout(() => { const i = store.toasts.indexOf(t); if (i >= 0) store.toasts.splice(i, 1); }, ms || 2600);
  }
  function confirmar(titulo, texto, ok, peligro) {
    return new Promise((resolve) => {
      store.modal = { titulo, texto, ok: ok || "Aceptar", peligro, resolve: (v) => { store.modal = null; resolve(v); } };
    });
  }

  async function cargarCatalogo() {
    store.catalogo = await api.get("/catalogo");
    return store.catalogo;
  }
  async function cargarEsquema(refrescar) {
    if (store.esquema && !refrescar) return store.esquema;
    store.esquema = await api.get("/esquema" + (refrescar ? "?refrescar=1" : ""));
    return store.esquema;
  }

  const SECC_ICON = { basicas: "filter", joins: "link", agrupacion: "layers", dominio: "briefcase", subconsultas: "search", vistas: "eye", dml: "edit", ddl: "database" };
  const TIPO_NOMBRE = { select: "SELECT", view: "VISTA", dml: "DML", ddl: "DDL" };
  function seccion(id) {
    return (store.catalogo && store.catalogo.secciones.find((s) => s.id === id)) || { id, nombre: id, corto: id };
  }
  function copiar(txt) {
    navigator.clipboard.writeText(txt).then(() => toast("Copiado al portapapeles"));
  }
  function irA(hash) { location.hash = hash; }

  // Inserta texto en el último editor SQL usado (lo usa el DER flotante)
  function insertarEnEditor(texto) {
    const cm = window.U && U.editorActivo;
    if (!cm || !document.body.contains(cm.getWrapperElement())) { toast("Abrí un ejercicio o la consola para insertar"); return false; }
    const cur = cm.getCursor();
    const antes = cm.getRange({ line: cur.line, ch: Math.max(0, cur.ch - 1) }, cur);
    const sep = antes && /[\w)]/.test(antes) && !cm.somethingSelected() ? " " : "";
    cm.replaceSelection(sep + texto);
    cm.focus();
    return true;
  }
  function fmtNum(n) { return (n || 0).toLocaleString("es-AR"); }

  window.U = { api, icon, md, mdInline, highlight, escapeHtml, store, setTema, toast, confirmar, cargarCatalogo, cargarEsquema,
               SECC_ICON, TIPO_NOMBRE, seccion, copiar, irA, fmtNum, insertarEnEditor };
})();
