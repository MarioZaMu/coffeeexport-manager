/* CoffeeExport Manager – sesión, navegación y arranque */
"use strict";

const SESSION_KEY = "cem_session", IDLE_MS = 30 * 60 * 1000;   // RF-02: expira a los 30 min de inactividad
const Session = {user:null, last:Date.now()};
const can = (mod, lvl = "r") => { const p = (PERMISOS[Session.user?.rol] || {})[mod]; return lvl === "w" ? p === "w" : !!p; };

function saveSession(remember) {
  try { const v = JSON.stringify({id:Session.user.id}); (remember ? localStorage : sessionStorage).setItem(SESSION_KEY, v); (remember ? sessionStorage : localStorage).removeItem(SESSION_KEY); } catch (e) { /* sin almacenamiento */ }
}
function clearSession() { try { sessionStorage.removeItem(SESSION_KEY); localStorage.removeItem(SESSION_KEY); } catch (e) {} }
function restoreSession() {
  try { const raw = sessionStorage.getItem(SESSION_KEY) || localStorage.getItem(SESSION_KEY); if (!raw) return false;
    const u = byId(Store.db.usuarios, JSON.parse(raw).id); if (!u || !u.activo) return false; Session.user = u; return true; } catch (e) { return false; }
}

/* ---------------- Login ---------------- */
/* Tarjetas del acceso de demostración: ícono, color y una línea de lo que puede hacer cada rol (RF-04) */
const ROL_UI = {ADMIN:["bi-shield-lock", 1, "Acceso total y usuarios"], GERENTE:["bi-graph-up-arrow", 3, "Dashboard y reportes"],
  OP_EXPORTACIONES:["bi-truck", 2, "Clientes, envíos y documentos"], OP_BODEGA:["bi-box-seam", 4, "Inventario y movimientos"], CONTADOR:["bi-cash-coin", 1, "Pagos y finanzas"]};
const LAST_DEMO = "cem_last_demo";
function showLogin(msg) {
  killCharts(); Session.user = null; $("#app").hidden = true; const lv = $("#login-view"); lv.classList.remove("leaving"); lv.hidden = false;
  $("#hero-logo").innerHTML = logoSVG(30, "#f5b041", "#14523f");
  $("#lh-stats").innerHTML = [[Object.keys(EU).length, "países de la UE"], [PUERTOS_SALIDA.length, "puertos de salida"], [DOCS_OBLIGATORIOS.length, "documentos por envío"]]
    .map(([n, t]) => `<li><b>${n}</b><span>${t}</span></li>`).join("");
  const cuentas = Api.on ? DEMO_CUENTAS : Store.db.usuarios.filter(u => u.activo).map(u => [u.email, u.rol]);
  let ultimo = ""; try { ultimo = localStorage.getItem(LAST_DEMO) || ""; } catch (e) { /* sin almacenamiento */ }
  $("#demo-users").innerHTML = cuentas.map(([email, rol]) => { const [ic, c, d] = ROL_UI[rol] || ["bi-person", 1, ""];
    return `<button type="button" data-u="${esc(email)}" class="${email === ultimo ? "sel" : ""}"><span class="ic" style="background:var(--ico-${c});color:var(--ico-${c}c)"><i class="bi ${ic}"></i></span><span><span class="t">${esc(ROLES[rol].nombre)}</span><span class="d">${esc(d)}</span></span></button>`; }).join("");
  $$("#demo-users [data-u]").forEach(b => b.onclick = () => {
    $$("#demo-users .sel").forEach(x => x.classList.remove("sel")); b.classList.add("sel");
    $("#login-email").value = b.dataset.u; $("#login-pass").value = "Demo2026*"; $("#login-pass").focus();
    try { localStorage.setItem(LAST_DEMO, b.dataset.u); } catch (e) { /* sin almacenamiento */ }
  });
  const err = $("#login-error"); err.hidden = !msg; err.textContent = msg || "";
  history.replaceState(null, "", location.pathname);
}
/* Transición corta del login al sistema (se omite con movimiento reducido) */
function entrar() {
  const lv = $("#login-view"); if (reducedMotion()) return startApp(true);
  lv.classList.add("leaving"); setTimeout(() => { lv.classList.remove("leaving"); startApp(true); }, 340);
}
async function doLogin(e) {
  e.preventDefault();
  const email = $("#login-email").value.trim().toLowerCase(), pass = $("#login-pass").value, err = $("#login-error");
  const fail = m => { err.hidden = false; err.textContent = m; const f = $("#login-form"); f.classList.remove("shake"); void f.offsetWidth; f.classList.add("shake"); };
  if (!email || !pass) return fail("Ingrese su correo y contraseña.");
  if (Api.on) {   // modo conectado: la validación (BCrypt, usuario activo) la hace el servidor
    const btn = $("#login-form [type=submit]"), txt = btn.innerHTML; btn.disabled = true; btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Ingresando…`;
    try { Session.user = await Api.login(email, pass); await Api.refresh(); } catch (er) { Session.user = null; return fail(er.message); }
    finally { btn.disabled = false; btn.innerHTML = txt; }
    Session.last = Date.now(); $("#login-pass").value = ""; err.hidden = true; return entrar();
  }
  const u = Store.db.usuarios.find(x => x.email.toLowerCase() === email);
  if (!u || u.password !== pass) return fail("Credenciales incorrectas");            // mensaje genérico (UC-01 3a)
  if (!u.activo) return fail("Su usuario está inactivo. Contacte al administrador.");
  Session.user = u; Session.last = Date.now(); saveSession($("#login-remember").checked);
  $("#login-pass").value = ""; err.hidden = true; entrar();
}

/* ---------------- App ---------------- */
function startApp(fresh) {
  const u = Session.user; $("#login-view").hidden = true; $("#app").hidden = false;
  $("#side-logo").innerHTML = logoSVG(36, "#f5b041", "#14523f");
  $("#u-name").textContent = u.nombre.split(" ")[0] === "Administrador" ? "Admin" : u.nombre; $("#u-role").textContent = ROLES[u.rol].nombre; $("#u-mail").textContent = u.email;
  $("#u-avatar").textContent = u.nombre.split(" ").map(x => x[0]).slice(0, 2).join("").toUpperCase();
  $("#nav").innerHTML = MODULOS.filter(m => can(m.id)).map(m => `<li><a href="#${m.id}" data-m="${m.id}"><i class="bi ${m.icon}"></i><span>${m.label}</span></a></li>`).join("");
  $(".side-foot").innerHTML = Api.on ? `Conectado al servidor<br>${esc(new URL(Api.base).host)}` : "Modo demostración<br>Datos en este navegador";
  refreshBell();
  if (fresh || !location.hash) location.hash = "#" + HOME[u.rol]; else route();
}
function route() {
  if (!Session.user) return;
  const hash = (location.hash || "").slice(1) || HOME[Session.user.rol], mod = hash.split("/")[0];
  closeSidebar(); killCharts();
  const m = MODULOS.find(x => x.id === mod);
  if (!m || !Views[hash]) { location.hash = "#" + HOME[Session.user.rol]; return; }
  if (!can(mod)) { toast("Acceso denegado: su rol no tiene permiso para este módulo.", "danger"); location.hash = "#" + HOME[Session.user.rol]; return; }   // RNF-03
  $$("#nav a").forEach(a => { const on = a.dataset.m === mod; a.classList.toggle("active", on); if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  document.title = `${m.label} · CoffeeExport Manager`;
  const v = $("#view");
  try { Views[hash](); }
  catch (er) { console.warn("Error al dibujar la vista", hash, er); v.innerHTML = pageHead(m.label, "") + errorState(er.message || "Error inesperado"); $("#retry").onclick = () => route(); }
  window.scrollTo(0, 0); v.focus({preventScroll:true}); stackTables(v);
  v.classList.add("enter"); countUp(v); clearTimeout(route._t); route._t = setTimeout(() => v.classList.remove("enter"), 1200);   // la entrada solo anima al cambiar de vista
}
/* En pantallas pequeñas las tablas pasan a tarjetas: cada celda toma como etiqueta el encabezado de su columna (CSS en styles.css) */
function stackTables(root = document) {
  $$("table.table-cem", root).forEach(t => {
    const h = $$("thead th", t).map(x => x.textContent.trim());
    $$("tbody tr", t).forEach(tr => [...tr.children].forEach((td, i) => { if (h[i] && !td.dataset.label) td.dataset.label = h[i]; }));
    t.classList.add("stack");
  });
}
function watchTables() {
  const v = $("#view"); let pend = false;
  new MutationObserver(() => { if (pend) return; pend = true; requestAnimationFrame(() => { pend = false; stackTables(v); }); }).observe(v, {childList:true, subtree:true});
}
/* Estado de conexión (solo modo conectado): avisa cuando el navegador pierde la red */
function watchNet() {
  const b = $("#net-banner"); if (!b) return;
  const paint = () => { b.hidden = !(Api.on && navigator.onLine === false); };
  addEventListener("offline", paint); addEventListener("online", () => { paint(); if (Api.on && Session.user) toast("Conexión restablecida", "success"); });
}
function logout(msg) { if (Api.on && Session.user) Api.req("POST", "/api/auth/logout").catch(() => {}); clearSession(); showLogin(msg); }

/* ---------------- Sidebar móvil ---------------- */
const closeSidebar = () => { $("#sidebar").classList.remove("open"); $("#backdrop").classList.remove("show"); };

/* ---------------- Notificaciones ---------------- */
function refreshBell() {
  if (!Session.user) return; const d = DBx(), n = d.meta.notif, items = [];
  if (n.stock && can("inventario")) alertasStock().forEach(a => items.push({ic:"bi-exclamation-triangle text-warning", t:`Stock bajo: ${a.p.nombre}`, s:`${nf(a.stock)} kg disponibles (mínimo ${nf(a.min)} kg)`, h:"#inventario"}));
  if (n.docs && can("documentos")) { const p = d.documentos.filter(x => x.estado === "PENDIENTE").length; if (p) items.push({ic:"bi-file-earmark-text text-primary", t:`${p} documento(s) por validar`, s:"Revise la sección de documentos", h:"#documentos"});
    d.exportaciones.filter(e => e.estado === "EN_PREPARACION" && docsFaltantes(e.id).length).slice(0, 3).forEach(e => items.push({ic:"bi-exclamation-circle text-danger", t:`${e.codigo}: documentación incompleta`, s:`Faltan ${docsFaltantes(e.id).length} documento(s) obligatorio(s)`, h:"#documentos"})); }
  if (n.pagos && can("pagos")) { const p = d.pagos.filter(x => x.estado === "PENDIENTE").length; if (p) items.push({ic:"bi-credit-card text-success", t:`${p} pago(s) por confirmar`, s:"Concilie los pagos pendientes", h:"#pagos"}); }
  $("#bell-n").hidden = !items.length; $("#bell-n").textContent = items.length;
  $("#bell-menu").innerHTML = `<div class="px-3 py-2 fw-semibold border-bottom">Notificaciones</div>` + (items.length ? items.map(i => `<a class="dropdown-item d-flex gap-2 py-2" href="${i.h}" style="white-space:normal"><i class="bi ${i.ic} mt-1"></i><span><span class="d-block small fw-semibold">${esc(i.t)}</span><span class="small text-muted">${esc(i.s)}</span></span></a>`).join("") : `<div class="p-3 small text-muted">Sin notificaciones pendientes.</div>`);
}

/* ---------------- Búsqueda global ---------------- */
function initSearch() {
  const inp = $("#gsearch"), box = $("#gsearch-res");
  const run = () => { const q = nrm(inp.value); if (q.length < 2) { box.hidden = true; return; } const d = DBx(), out = [];
    if (can("clientes")) d.clientes.filter(c => nrm(c.nombre + c.nif + c.email).includes(q)).slice(0, 3).forEach(c => out.push({t:c.nombre, s:`Cliente · ${EU[c.pais]}`, h:"clientes", key:"clientes", q:c.nombre}));
    if (can("productos")) d.productos.filter(p => nrm(p.nombre + p.codigo).includes(q)).slice(0, 3).forEach(p => out.push({t:p.nombre, s:`Producto · ${p.codigo}`, h:"productos", key:"productos", q:p.nombre}));
    if (can("exportaciones")) d.exportaciones.filter(e => nrm(e.codigo + cliName(e.cliente_id)).includes(q)).slice(0, 4).forEach(e => out.push({t:e.codigo, s:`Exportación · ${cliName(e.cliente_id)}`, h:"exportaciones", key:"exportaciones", q:e.codigo}));
    box.innerHTML = out.length ? out.map((o, i) => `<a href="#${o.h}" data-i="${i}"><b>${esc(o.t)}</b><small>${esc(o.s)}</small></a>`).join("") : `<div class="p-3 small text-muted">Sin resultados</div>`; box.hidden = false;
    $$("a", box).forEach(a => a.onclick = () => { const o = out[+a.dataset.i]; UI[o.key].q = o.q; UI[o.key].page = 1; box.hidden = true; inp.value = ""; if (location.hash === "#" + o.h) route(); }); };
  inp.oninput = run; inp.onfocus = run; document.addEventListener("click", e => { if (!e.target.closest(".search")) box.hidden = true; });
  inp.onkeydown = e => { if (e.key === "Escape") { box.hidden = true; inp.blur(); } };
}

/* ---------------- Arranque ---------------- */
document.addEventListener("DOMContentLoaded", () => {
  Api.init(); Store.load();
  $("#login-form").addEventListener("submit", doLogin);
  $("#toggle-pass").onclick = () => { const p = $("#login-pass"), show = p.type === "password"; p.type = show ? "text" : "password"; $("#toggle-pass i").className = `bi bi-eye${show ? "-slash" : ""}`; };
  $("#login-form").addEventListener("animationend", e => { if (e.animationName === "shake") e.currentTarget.classList.remove("shake"); });
  const caps = e => { if (e.getModifierState) $("#caps-warn").hidden = !e.getModifierState("CapsLock"); };
  $("#login-pass").addEventListener("keydown", caps); $("#login-pass").addEventListener("keyup", caps);
  $("#login-pass").addEventListener("blur", () => { $("#caps-warn").hidden = true; });
  $("#forgot").onclick = e => { e.preventDefault(); openModal({title:"Recuperar contraseña", hideFoot:true, body:`
    <p class="mb-3">Por seguridad, las contraseñas solo las restablece el <b>administrador</b> del sistema (RF-01). Escríbale indicando su correo corporativo y él le asignará una contraseña temporal.</p>
    <div class="alert alert-light small mb-0"><i class="bi bi-info-circle me-1"></i>En <b>modo demostración</b> no necesita contraseña propia: elija un rol en <b>Acceso de demostración</b> y se completan los datos.</div>`}); };
  $("#logout").onclick = e => { e.preventDefault(); logout(); };
  $("#menu-toggle").onclick = () => { $("#sidebar").classList.add("open"); $("#backdrop").classList.add("show"); };
  $("#backdrop").onclick = closeSidebar;
  initSearch(); watchTables(); watchNet();
  const paintTheme = () => { const c = "bi " + (isDark() ? "bi-sun" : "bi-moon-stars"); $("#theme-ic").className = c; $("#login-theme i").className = c; };
  paintTheme();
  $("#login-theme").onclick = () => $("#theme").onclick();
  $("#theme").onclick = () => { const t = isDark() ? "light" : "dark"; document.documentElement.dataset.theme = t; document.documentElement.dataset.bsTheme = t;
    try { localStorage.setItem("cem_theme", t); } catch (e) { /* sin almacenamiento */ } paintTheme(); if (Session.user) route(); };
  window.addEventListener("hashchange", route);
  ["click", "keydown", "mousemove", "touchstart"].forEach(ev => document.addEventListener(ev, () => { Session.last = Date.now(); }, {passive:true}));
  setInterval(() => { if (Session.user && Date.now() - Session.last > IDLE_MS) logout("Su sesión expiró por inactividad. Inicie sesión de nuevo."); }, 30000);
  if (Api.on) {   // ¿sigue viva la sesión del servidor?
    Api.me().then(async u => { Session.user = u; Session.last = Date.now(); await Api.refresh(); startApp(false); })
      .catch(er => showLogin(er.status === 401 ? "" : er.message));
  } else if (restoreSession()) { Session.last = Date.now(); startApp(false); } else showLogin();
});
