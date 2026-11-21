/* CoffeeExport Manager | capa de datos.
   Modo conectado: habla con la API Spring Boot (cookie de sesión HttpOnly, CORS con credenciales).
   Modo demostración: igual que antes, con los datos en localStorage.
   Se activa con ?api=http://localhost:8080 (se recuerda) y se desactiva con ?api=off.
   Las vistas llaman a Data.*; solo este archivo sabe en qué modo se está. */
"use strict";

const CLAVE_API = "cem_api", CLAVE_META_API = "cem_meta_api";
const COLECCIONES = ["clientes", "productos", "bodegas", "inventario", "movimientos", "exportaciones", "documentos", "pagos", "usuarios"];

const Api = {
  base: null,
  get on() { return !!this.base; },

  init() {
    let base = null;
    try {
      const p = new URLSearchParams(location.search).get("api");
      if (p === "off") localStorage.removeItem(CLAVE_API);
      else if (p) localStorage.setItem(CLAVE_API, p.replace(/\/+$/, ""));
      base = window.CEM_API || localStorage.getItem(CLAVE_API);
    } catch (e) { base = window.CEM_API || null; }
    this.base = base ? base.replace(/\/+$/, "") : null;
    if (!this.on) return;

    // En modo conectado el servidor es la fuente de verdad: la base local solo es una copia de lectura.
    const guardado = (() => { try { return JSON.parse(localStorage.getItem(CLAVE_META_API)) || {}; } catch (e) { return {}; } })();
    Store.load = () => {
      Store.db = {meta:{nextId:{}, tasaEurUsd:1.08, empresa:guardado.empresa || {nombre:"RITECH SAS", nit:"900.123.456-7", direccion:"Cra 45 # 12-34, Bogotá, Colombia", email:"info@ritech.co", telefono:"+57 300 123 4567"},
                       notif:guardado.notif || {stock:true, docs:true, pagos:true}}};
      COLECCIONES.forEach(k => Store.db[k] = []);
      return Store.db;
    };
    Store.save = () => { try { localStorage.setItem(CLAVE_META_API, JSON.stringify({empresa:Store.db.meta.empresa, notif:Store.db.meta.notif})); } catch (e) { /* sin almacenamiento */ } };
    Store.reset = () => {};
  },

  async req(metodo, ruta, cuerpo, formulario) {
    const opciones = {method:metodo, credentials:"include", headers:{}};
    if (formulario) opciones.body = formulario;
    else if (cuerpo !== undefined) { opciones.headers["Content-Type"] = "application/json"; opciones.body = JSON.stringify(cuerpo); }
    let r;
    try { r = await fetch(this.base + ruta, opciones); }
    catch (e) { throw new Error(`No se pudo conectar con el servidor (${this.base}).`); }
    if (r.status === 204) return null;
    const datos = await r.json().catch(() => ({}));
    if (!r.ok) {
      const err = new Error(datos.error || `Error ${r.status}`);
      err.status = r.status; err.campos = datos.campos;
      if (r.status === 401 && ruta !== "/api/auth/login" && !ruta.endsWith("/me") && Session.user) logout("Su sesión expiró. Inicie sesión de nuevo.");
      throw err;
    }
    return datos;
  },

  async login(email, password) { return this.req("POST", "/api/auth/login", {email, password}); },
  async me() { return this.req("GET", "/api/auth/me"); },

  /** Descarga la instantánea de datos permitidos al rol y la copia en el mismo objeto (las vistas conservan su referencia). */
  async refresh() {
    const s = await this.req("GET", "/api/snapshot");
    COLECCIONES.forEach(k => { Store.db[k] = s[k] || []; });
    if (s.meta) Store.db.meta.tasaEurUsd = s.meta.tasaEurUsd;
  },

  async subir(exportacionId, tipo, archivo) {
    const f = new FormData(); f.append("tipo", tipo); f.append("archivo", archivo, archivo.name);
    return this.req("POST", `/api/exportaciones/${exportacionId}/documentos`, undefined, f);
  },
};

/* Cuentas de demostración que ofrece el login en modo conectado (coinciden con los datos iniciales del backend) */
const DEMO_CUENTAS = [["admin@ritech.co", "ADMIN"], ["gerente@ritech.co", "GERENTE"], ["exportaciones@ritech.co", "OP_EXPORTACIONES"],
                      ["bodega@ritech.co", "OP_BODEGA"], ["contador@ritech.co", "CONTADOR"]];

/* Operaciones de datos de las vistas. Cada una resuelve en la API o, en modo demostración, sobre localStorage. */
const Data = {
  async clienteGuardar(c, f) {
    if (Api.on) {
      const cuerpo = {nombre:f.nombre, pais:f.pais, identificacionFiscal:f.nif, contactoNombre:f.contacto, contactoEmail:f.email, contactoTelefono:f.telefono || null, direccion:f.direccion || null, consentimientoDatos:true};
      await Api.req(c ? "PUT" : "POST", c ? `/api/clientes/${c.id}` : "/api/clientes", cuerpo); return Api.refresh();
    }
    if (c) Object.assign(c, {nombre:f.nombre, pais:f.pais, nif:f.nif, contacto:f.contacto, email:f.email, telefono:f.telefono, direccion:f.direccion, consent:true, consentFecha:c.consentFecha || todayISO()});
    else DBx().clientes.push({id:Store.nextId("clientes"), nombre:f.nombre, pais:f.pais, nif:f.nif, contacto:f.contacto, email:f.email, telefono:f.telefono, direccion:f.direccion, consent:true, consentFecha:todayISO(), activo:true});
    Store.save();
  },
  async clienteEstado(c) {
    if (Api.on) { const nuevo = !c.activo; await Api.req("PATCH", `/api/clientes/${c.id}/estado`, {activo:nuevo}); await Api.refresh(); return nuevo; }
    c.activo = !c.activo; Store.save(); return c.activo;
  },

  async productoGuardar(p, d) {
    if (Api.on) {
      await Api.req(p ? "PUT" : "POST", p ? `/api/productos/${p.id}` : "/api/productos", {codigo:d.codigo, nombre:d.nombre, tipo:d.tipo, variedad:d.variedad || null, precioUsdKg:d.precio}); return Api.refresh();
    }
    if (p) Object.assign(p, d); else DBx().productos.push({id:Store.nextId("productos"), ...d, activo:true});
    Store.save();
  },
  async productoEstado(p) {
    if (Api.on) { await Api.req("PATCH", `/api/productos/${p.id}/estado`, {activo:!p.activo}); return Api.refresh(); }
    p.activo = !p.activo; Store.save();
  },

  async minimoGuardar(i, v) {
    if (Api.on) { await Api.req("PATCH", `/api/inventario/${i.id}/minimo`, {stockMinimoKg:v}); return Api.refresh(); }
    i.min = v; Store.save();
  },
  async movimiento(f, cant) {
    if (Api.on) {
      await Api.req("POST", "/api/inventario/movimientos", {productoId:+f.producto, bodegaId:+f.bodega, tipo:f.tipo, cantidadKg:cant, motivo:f.motivo || null}); return Api.refresh();
    }
    const d = DBx(); let inv = d.inventario.find(i => i.producto_id === +f.producto && i.bodega_id === +f.bodega);
    if (!inv) { if (f.tipo === "SALIDA") throw new Error("No hay existencias de ese producto en la bodega seleccionada."); inv = {id:Store.nextId("inventario"), producto_id:+f.producto, bodega_id:+f.bodega, kg:0, min:0}; d.inventario.push(inv); }
    moverInventario({inv_id:inv.id, tipo:f.tipo, kg:cant, motivo:f.motivo, usuario:Session.user.nombre});
    Store.save();
  },

  async exportacionEstado(e, to) {
    if (Api.on) { await Api.req("PATCH", `/api/exportaciones/${e.id}/estado`, {estado:to}); return Api.refresh(); }
    const u = Session.user.nombre;
    if (to === "EN_PREPARACION") {
      for (const l of e.lineas) if (stockProducto(l.producto_id) < e.lineas.filter(x => x.producto_id === l.producto_id).reduce((a, x) => a + x.kg, 0)) throw new Error(`Stock insuficiente de ${prodName(l.producto_id)}.`);
      descontarStock(e, u);
    }
    if (to === "EN_TRANSITO") { const f = docsFaltantes(e.id); if (f.length) throw new Error("Faltan documentos obligatorios: " + f.map(t => TIPOS_DOC[t]).join(", ") + "."); }
    if (to === "CANCELADA" && e.descontado) devolverStock(e, u);
    e.estado = to; Store.save();
  },
  async exportacionCrear(f, estado) {
    if (Api.on) {
      const ex = await Api.req("POST", "/api/exportaciones", {clienteId:+f.cliente, paisDestino:f.pais, puertoSalida:f.salida, puertoLlegada:f.llegada, fechaEnvio:f.fecha,
        estadoInicial:estado === "BORRADOR" ? "BORRADOR" : "EN_PREPARACION", observaciones:f.obs || null,
        lineas:f.lineas.map(l => ({productoId:+l.producto, cantidadKg:parseFloat(l.kg), precioUnitario:parseFloat(l.precio)}))});
      const fallos = [];
      for (const [tipo, dd] of Object.entries(f.docs)) { try { await Api.subir(ex.id, tipo, dd.file); } catch (er) { fallos.push(`${TIPOS_DOC[tipo]}: ${er.message}`); } }
      await Api.refresh();
      if (fallos.length) toast("La exportación se creó, pero no se pudieron adjuntar: " + fallos.join("; "), "warning");
      return ex;
    }
    const ex = {id:Store.nextId("exportaciones"), cliente_id:+f.cliente, pais:f.pais, puerto_salida:f.salida, puerto_llegada:f.llegada, fecha_envio:f.fecha, estado:"BORRADOR", creador:Session.user.id, obs:f.obs,
      lineas:f.lineas.map(l => ({producto_id:+l.producto, kg:parseFloat(l.kg) || 0, precio:parseFloat(l.precio) || 0})), descontado:false, creado:todayISO()};
    ex.codigo = `EXP-${new Date().getFullYear()}-${String(ex.id).padStart(4, "0")}`;
    if (estado !== "BORRADOR") { descontarStock(ex, Session.user.nombre); ex.estado = "EN_PREPARACION"; }
    DBx().exportaciones.push(ex);
    Object.entries(f.docs).forEach(([t, dd]) => DBx().documentos.push({id:Store.nextId("documentos"), exportacion_id:ex.id, tipo:t, archivo:dd.nombre, kb:dd.kb, estado:"PENDIENTE", fecha:todayISO(), por:Session.user.id}));
    Store.save();
    return ex;
  },

  async documentoEstado(id, estado) {
    if (Api.on) { await Api.req("PATCH", `/api/documentos/${id}/validacion`, {estado}); return Api.refresh(); }
    byId(DBx().documentos, id).estado = estado; Store.save();
  },
  async documentoSubir(exportacionId, tipo, archivo) {
    if (Api.on) { await Api.subir(exportacionId, tipo, archivo); return Api.refresh(); }
    DBx().documentos.push({id:Store.nextId("documentos"), exportacion_id:exportacionId, tipo, archivo:archivo.name, kb:Math.max(1, Math.round(archivo.size / 1024)), estado:"PENDIENTE", fecha:todayISO(), por:Session.user.id});
    Store.save();
  },

  async pagoRegistrar(f, monto) {
    if (Api.on) {
      await Api.req("POST", "/api/pagos", {exportacionId:+f.exp, monto, moneda:f.moneda, metodo:f.metodo, referencia:f.ref || null, fechaPago:f.fecha}); return Api.refresh();
    }
    DBx().pagos.push({id:Store.nextId("pagos"), exportacion_id:+f.exp, monto:Math.round(monto * 100) / 100, moneda:f.moneda, metodo:f.metodo, ref:f.ref, fecha:f.fecha, estado:"PENDIENTE", por:Session.user.id});
    Store.save();
  },
  async pagoEstado(id, estado) {
    if (Api.on) { await Api.req("PATCH", `/api/pagos/${id}/estado`, {estado}); return Api.refresh(); }
    byId(DBx().pagos, id).estado = estado; Store.save();
  },

  async usuarioGuardar(u, f) {
    if (Api.on) {
      await Api.req(u ? "PUT" : "POST", u ? `/api/usuarios/${u.id}` : "/api/usuarios", {nombre:f.nombre, email:f.email, password:f.password || null, rol:f.rol, activo:f.activo}); return Api.refresh();
    }
    const d = DBx();
    if (u) { Object.assign(u, {nombre:f.nombre, email:f.email, rol:f.rol, activo:f.activo}); if (f.password) u.password = f.password; }
    else d.usuarios.push({id:Store.nextId("usuarios"), nombre:f.nombre, email:f.email, rol:f.rol, password:f.password, activo:f.activo});
    Store.save();
  },
};
