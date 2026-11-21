# -*- coding: utf-8 -*-
"""Conecta las vistas del frontend a la capa Data (api.js). Cada reemplazo verifica que el texto original exista."""
import os
RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend"))
os.chdir(RAIZ)

def sub(s, old, new):
    assert s.count(old) == 1, f"debe aparecer exactamente una vez ({s.count(old)}): {old[:80]!r}"
    return s.replace(old, new)

def entre(s, ini, fin, nuevo):
    a = s.index(ini)
    b = s.index(fin, a) + len(fin)
    assert a < b
    return s[:a] + nuevo + s[b:]

# ======================================================================= views.js
p = "js/views.js"; s = open(p, encoding="utf-8").read()
assert "Data." not in s, "views.js ya fue parchado"

# --- clientes
s = sub(s, '{ c.activo = !c.activo; Store.save(); toast(`Cliente ${c.activo ? "activado" : "desactivado"}`); draw(); } });',
           '{ let nuevo; try { nuevo = await Data.clienteEstado(c); } catch (e) { return toast(e.message, "danger"); } toast(`Cliente ${nuevo ? "activado" : "desactivado"}`); draw(); } });')
s = entre(s, '        if (c) Object.assign(c, {nombre:f.nombre, pais:f.pais, nif:f.nif', 'redraw(); }});',
          '        try { await Data.clienteGuardar(c, f); } catch (e) { return formErrors(root, [e.message]); }\n        toast(c ? "Cliente actualizado" : "Cliente registrado"); redraw(); }});')
# --- productos
s = sub(s, '{ p.activo = !p.activo; Store.save(); toast("Producto actualizado"); draw(); } });',
           '{ try { await Data.productoEstado(p); } catch (e) { return toast(e.message, "danger"); } toast("Producto actualizado"); draw(); } });')
s = entre(s, '        const data = {nombre:f.nombre, codigo:f.codigo, tipo:f.tipo, variedad:f.variedad, precio:Math.round(pr * 100) / 100};', 'draw(); }});',
          '        try { await Data.productoGuardar(p, {nombre:f.nombre, codigo:f.codigo, tipo:f.tipo, variedad:f.variedad, precio:Math.round(pr * 100) / 100}); } catch (e) { return formErrors(root, [e.message]); }\n        toast(p ? "Producto actualizado" : "Producto registrado"); draw(); }});')
# --- inventario
s = sub(s, 'i.min = v; Store.save(); toast("Stock mínimo actualizado");',
           'try { await Data.minimoGuardar(i, v); } catch (e) { return formErrors(root, [e.message]); } toast("Stock mínimo actualizado");')
s = entre(s, 'onSave:root => { const f = formData(root), cant = parseFloat(f.cant);', 'Views.inventario(); }});',
          'onSave:root => { const f = formData(root), cant = parseFloat(f.cant);\n        try { await Data.movimiento(f, cant); } catch (e) { return formErrors(root, [e.message]); }\n        toast("Movimiento registrado"); Views.inventario(); }});')
# --- exportaciones: cambio de estado
s = entre(s, '  $$("[data-to]", $("#modal")).forEach(b => b.onclick = async () => {', 'redraw && redraw(); refreshBell();\n  });',
          '''  $$("[data-to]", $("#modal")).forEach(b => b.onclick = async () => {
    const to = b.dataset.to;
    if (to === "CANCELADA" && !(await confirmDlg(`¿Cancelar la exportación <b>${esc(e.codigo)}</b>? ${e.descontado ? "Se devolverá el stock descontado." : ""}`, {danger:true, label:"Cancelar exportación"}))) return;
    try { await Data.exportacionEstado(e, to); } catch (err) { toast(err.message, "danger"); return; }
    closeModal(); toast(`Exportación ${ESTADOS_EXP[to][0].toLowerCase()}`); redraw && redraw(); refreshBell();
  });''')
# --- asistente de exportación
s = sub(s, 'f.docs[inp.dataset.doc] = {nombre:file.name, kb:Math.max(1, Math.round(file.size / 1024))}; wizDraw(); });',
           'f.docs[inp.dataset.doc] = {nombre:file.name, kb:Math.max(1, Math.round(file.size / 1024)), file}; wizDraw(); });')
s = entre(s, '      const ex = {id:Store.nextId("exportaciones"), cliente_id:+f.cliente,', 'location.hash = "#exportaciones";\n    };',
          '      let ex;\n      try { ex = await Data.exportacionCrear(f, estado); } catch (err) { return showErr([err.message]); }\n      toast(`Exportación ${ex.codigo} creada`); location.hash = "#exportaciones";\n    };')
# --- documentos
s = sub(s, '$$("[data-dl]").forEach(b => b.onclick = () => toast("Demostración: el archivo PDF se almacenará en el servidor cuando exista el backend.", "info"));',
           '$$("[data-dl]").forEach(b => b.onclick = () => Api.on ? window.open(`${Api.base}/api/documentos/${b.dataset.dl}/archivo`, "_blank") : toast("Modo demostración: el archivo PDF no se guarda. Conecte el backend para descargarlo.", "info"));')
s = sub(s, '$$("[data-val]").forEach(b => b.onclick = () => { byId(DBx().documentos, b.dataset.val).estado = "VALIDADO"; Store.save(); toast("Documento validado"); draw(); refreshBell(); });',
           '$$("[data-val]").forEach(b => b.onclick = async () => { try { await Data.documentoEstado(+b.dataset.val, "VALIDADO"); } catch (e) { return toast(e.message, "danger"); } toast("Documento validado"); draw(); refreshBell(); });')
s = sub(s, '$$("[data-rej]").forEach(b => b.onclick = () => { byId(DBx().documentos, b.dataset.rej).estado = "RECHAZADO"; Store.save(); toast("Documento rechazado", "warning"); draw(); refreshBell(); });',
           '$$("[data-rej]").forEach(b => b.onclick = async () => { try { await Data.documentoEstado(+b.dataset.rej, "RECHAZADO"); } catch (e) { return toast(e.message, "danger"); } toast("Documento rechazado", "warning"); draw(); refreshBell(); });')
s = entre(s, '      DBx().documentos.push({id:Store.nextId("documentos"), exportacion_id:+f.exp,', 'refreshBell(); }});',
          '      try { await Data.documentoSubir(+f.exp, f.tipo, file); } catch (e) { return formErrors(root, [e.message]); }\n      toast("Documento cargado"); draw(); refreshBell(); }});')
# --- pagos
s = sub(s, '$$("[data-ok]").forEach(b => b.onclick = () => { byId(d.pagos, b.dataset.ok).estado = "CONFIRMADO"; Store.save(); toast("Pago confirmado"); Views.pagos(); refreshBell(); });',
           '$$("[data-ok]").forEach(b => b.onclick = async () => { try { await Data.pagoEstado(+b.dataset.ok, "CONFIRMADO"); } catch (e) { return toast(e.message, "danger"); } toast("Pago confirmado"); Views.pagos(); refreshBell(); });')
s = sub(s, '$$("[data-no]").forEach(b => b.onclick = () => { byId(d.pagos, b.dataset.no).estado = "RECHAZADO"; Store.save(); toast("Pago rechazado", "warning"); Views.pagos(); refreshBell(); });',
           '$$("[data-no]").forEach(b => b.onclick = async () => { try { await Data.pagoEstado(+b.dataset.no, "RECHAZADO"); } catch (e) { return toast(e.message, "danger"); } toast("Pago rechazado", "warning"); Views.pagos(); refreshBell(); });')
s = entre(s, '        d.pagos.push({id:Store.nextId("pagos"), exportacion_id:+f.exp,', 'refreshBell(); }});',
          '        try { await Data.pagoRegistrar(f, m); } catch (e) { return formErrors(root, [e.message]); }\n        toast("Pago registrado como pendiente"); Views.pagos(); refreshBell(); }});')
# --- configuración
s = sub(s, '''attrs:'step="0.0001" min="0.1"', help:"Se usa para consolidar pagos en EUR a USD."''',
           '''attrs:(Api.on ? 'disabled ' : '') + 'step="0.0001" min="0.1"', help:Api.on ? "Definida en el servidor (app.tasa-eur-usd)." : "Se usa para consolidar pagos en EUR a USD."''')
s = sub(s, 'm.tasaEurUsd = t; Store.save(); toast("Configuración guardada"); };', 'if (!Api.on) m.tasaEurUsd = t; Store.save(); toast("Configuración guardada"); };')
s = sub(s, '    $("#reset-demo").onclick = async () => {', '    if (Api.on) $("#reset-demo").closest(".card-cem").remove(); else $("#reset-demo").onclick = async () => {')
s = entre(s, '        if (u) { Object.assign(u, {nombre:f.nombre, email:f.email, rol:f.rol, activo:f.activo});', 'Views.config(); }});',
          '        try { await Data.usuarioGuardar(u, f); } catch (e) { return formErrors(root, [e.message]); }\n        toast(u ? "Usuario actualizado" : "Usuario creado"); Views.config(); }});')
# --- todos los guardados pasan a ser asíncronos
s = s.replace("onSave:root =>", "onSave:async root =>")
open(p, "w", encoding="utf-8", newline="\n").write(s)

# ======================================================================= app.js
p = "js/app.js"; s = open(p, encoding="utf-8").read()
s = sub(s, '''  $("#demo-users").innerHTML = Store.db.usuarios.filter(u => u.activo).map(u => `<button type="button" data-u="${esc(u.email)}">${esc(ROLES[u.rol].nombre)}</button>`).join("");''',
           '''  const cuentas = Api.on ? DEMO_CUENTAS : Store.db.usuarios.filter(u => u.activo).map(u => [u.email, u.rol]);
  $("#demo-users").innerHTML = cuentas.map(([email, rol]) => `<button type="button" data-u="${esc(email)}">${esc(ROLES[rol].nombre)}</button>`).join("");''')
s = entre(s, 'function doLogin(e) {', 'startApp(true);\n}',
'''async function doLogin(e) {
  e.preventDefault();
  const email = $("#login-email").value.trim().toLowerCase(), pass = $("#login-pass").value, err = $("#login-error");
  const fail = m => { err.hidden = false; err.textContent = m; };
  if (!email || !pass) return fail("Ingrese su correo y contraseña.");
  if (Api.on) {   // modo conectado: la validación (BCrypt, usuario activo) la hace el servidor
    try { Session.user = await Api.login(email, pass); await Api.refresh(); } catch (er) { Session.user = null; return fail(er.message); }
    Session.last = Date.now(); $("#login-pass").value = ""; err.hidden = true; return startApp(true);
  }
  const u = Store.db.usuarios.find(x => x.email.toLowerCase() === email);
  if (!u || u.password !== pass) return fail("Credenciales incorrectas");            // mensaje genérico (UC-01 3a)
  if (!u.activo) return fail("Su usuario está inactivo. Contacte al administrador.");
  Session.user = u; Session.last = Date.now(); saveSession($("#login-remember").checked);
  $("#login-pass").value = ""; err.hidden = true; startApp(true);
}''')
s = sub(s, '''  refreshBell();
  if (fresh || !location.hash)''', '''  $(".side-foot").innerHTML = Api.on ? `Conectado al servidor<br>${esc(new URL(Api.base).host)}` : "Modo demostración<br>Datos en este navegador";
  refreshBell();
  if (fresh || !location.hash)''')
s = sub(s, 'function logout(msg) { clearSession(); showLogin(msg); }',
           'function logout(msg) { if (Api.on && Session.user) Api.req("POST", "/api/auth/logout").catch(() => {}); clearSession(); showLogin(msg); }')
s = sub(s, '  Store.load();\n  $("#login-form")', '  Api.init(); Store.load();\n  $("#login-form")')
s = sub(s, '  if (restoreSession()) { Session.last = Date.now(); startApp(false); } else showLogin();\n});',
'''  if (Api.on) {   // ¿sigue viva la sesión del servidor?
    Api.me().then(async u => { Session.user = u; Session.last = Date.now(); await Api.refresh(); startApp(false); })
      .catch(er => showLogin(er.status === 401 ? "" : er.message));
  } else if (restoreSession()) { Session.last = Date.now(); startApp(false); } else showLogin();
});''')
open(p, "w", encoding="utf-8", newline="\n").write(s)

# ======================================================================= app.html
p = "app.html"; s = open(p, encoding="utf-8").read()
s = sub(s, '<script src="js/views.js"></script>', '<script src="js/api.js"></script>\n<script src="js/views.js"></script>')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("frontend conectado a la capa Data")
