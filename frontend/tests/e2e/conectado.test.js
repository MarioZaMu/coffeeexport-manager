/* Pruebas de sistema (E2E): la interfaz web en Chrome hablando con el backend Spring Boot REAL.
   Requiere el JAR: en backend/ ejecutar `mvn verify` (o `mvn package`). Ejecutar: node --test "tests/e2e/*.test.js"
   El backend arranca con H2 en memoria y los datos de demostración, en el puerto 8099. */
"use strict";
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");
const { chromium } = require("playwright-core");
const servidor = require("../helpers/servidor");

const EVIDENCIA = path.join(__dirname, "..", "evidence");
fs.mkdirSync(EVIDENCIA, { recursive: true });
const PUERTO_API = 8099, API = `http://127.0.0.1:${PUERTO_API}`;
const PDF = Buffer.from("%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF");

let browser, web, base, backend;
const salida = [];

function encontrarJar() {
  const dir = path.join(__dirname, "..", "..", "..", "backend", "target");
  const jar = fs.existsSync(dir) && fs.readdirSync(dir).find(f => /^coffeeexport-backend-.*\.jar$/.test(f) && !f.endsWith(".original"));
  if (!jar) throw new Error("No existe el JAR del backend. Ejecute `mvn verify` en backend/ antes de estas pruebas.");
  return path.join(dir, jar);
}

async function esperarBackend() {
  for (let i = 0; i < 120; i++) {
    try { const r = await fetch(API + "/api/auth/me"); if (r.status === 401) return; } catch (e) { /* aún arrancando */ }
    await new Promise(r => setTimeout(r, 500));
  }
  throw new Error("El backend no arrancó a tiempo:\n" + salida.slice(-30).join(""));
}

before(async () => {
  const java = process.env.JAVA_HOME ? path.join(process.env.JAVA_HOME, "bin", "java") : "java";
  backend = spawn(java, ["-jar", encontrarJar(), `--server.port=${PUERTO_API}`, `--app.storage.dir=${path.join(os.tmpdir(), "coffeeexport-e2e")}`, "--app.seed.demo=true"], { stdio: ["ignore", "pipe", "pipe"] });
  backend.stdout.on("data", d => salida.push(String(d))); backend.stderr.on("data", d => salida.push(String(d)));
  await esperarBackend();
  web = await servidor.iniciar(); base = web.base;
  browser = await chromium.launch({ headless: true, channel: process.env.PW_CHANNEL || undefined });
});
after(async () => {
  if (browser) await browser.close();
  if (web) await web.cerrar();
  if (backend) backend.kill();
});

async function abrir(viewport = { width: 1366, height: 860 }) {
  const ctx = await browser.newContext({ viewport, locale: "es-CO", timezoneId: "America/Bogota" });
  const page = await ctx.newPage();
  const errores = []; page.on("pageerror", e => errores.push(e.message));
  return { ctx, page, errores };
}
async function entrar(page, usuario = "admin@ritech.co") {
  await page.goto(`${base}/app.html?api=${encodeURIComponent(API)}`);
  await page.click(`#demo-users [data-u="${usuario}"]`);
  await page.click("#login-form button[type=submit]");
  await page.waitForSelector("#app:not([hidden])");
  await page.waitForSelector("#view > *");
}
const ir = async (page, hash) => { await page.evaluate(h => { location.hash = "#" + h; }, hash); await page.waitForTimeout(500); };
const api = (page, ruta) => page.evaluate(async r => (await fetch(Api.base + r, { credentials: "include" })).json(), ruta);
const foto = async (page, nombre) => { await page.waitForTimeout(1300); await page.screenshot({ path: path.join(EVIDENCIA, nombre + ".png") }); };

describe("Sistema completo: interfaz web + API Spring Boot", () => {
  test("PS-01 [QC015][HU-01][RF-01] iniciar sesión contra el servidor, ver el dashboard con datos reales y cerrar sesión", async () => {
    const { ctx, page, errores } = await abrir(); await entrar(page);
    assert.match(await page.locator(".side-foot").innerText(), /Conectado al servidor/);
    assert.equal(await page.locator(".kpi").count(), 4);
    assert.equal(await page.evaluate(() => Store.db.exportaciones.length), 12, "las 12 exportaciones vienen del backend");
    await foto(page, "PS-01-dashboard-conectado");
    await page.click('[aria-label="Menú de usuario"]'); await page.click("#logout"); await page.waitForSelector("#login-view:not([hidden])");
    await page.reload(); await page.waitForSelector("#login-view:not([hidden])");   // la cookie de sesión ya no es válida
    assert.deepEqual(errores, []); await ctx.close();
  });

  test("PS-02 [HU-01][RF-01] credenciales incorrectas: el servidor responde y la interfaz muestra el mensaje genérico", async () => {
    const { ctx, page } = await abrir(); await page.goto(`${base}/app.html?api=${encodeURIComponent(API)}`);
    await page.fill("#login-email", "admin@ritech.co"); await page.fill("#login-pass", "mala"); await page.click("#login-form button[type=submit]");
    await page.waitForFunction(() => document.querySelector("#login-error") && !document.querySelector("#login-error").hidden);
    assert.equal((await page.locator("#login-error").innerText()).trim(), "Credenciales incorrectas");
    assert.equal(await page.locator("#app").isHidden(), true); await ctx.close();
  });

  test("PS-03 [QC016][HU-02][RF-05] registrar un cliente desde el formulario: queda guardado en el servidor y en el listado", async () => {
    const { ctx, page } = await abrir(); await entrar(page); await ir(page, "clientes");
    await page.click("#new-cli"); await page.waitForSelector("#modal.show");
    await page.fill("[name=nombre]", "Tulip Trading BV"); await page.selectOption("[name=pais]", "NL"); await page.fill("[name=nif]", "NL777000111B01");
    await page.fill("[name=contacto]", "Eva Smit"); await page.fill("[name=email]", "eva@tulip.nl"); await page.check("[name=consent]");
    await page.click("#modal-save"); await page.waitForSelector("#modal", { state: "hidden" });
    const enServidor = await api(page, "/api/clientes?q=tulip");
    assert.equal(enServidor.length, 1); assert.equal(enServidor[0].identificacionFiscal, "NL777000111B01");
    await page.fill("#f-q", "Tulip"); await page.waitForTimeout(300);
    assert.equal(await page.locator("#tbl tbody tr").count(), 1);
    await foto(page, "PS-03-cliente-guardado"); await ctx.close();
  });

  test("PS-04 [HU-02][RF-05] un NIF duplicado lo rechaza el servidor y la interfaz muestra su mensaje", async () => {
    const { ctx, page } = await abrir(); await entrar(page); await ir(page, "clientes");
    await page.click("#new-cli"); await page.waitForSelector("#modal.show");
    await page.fill("[name=nombre]", "Duplicado SA"); await page.selectOption("[name=pais]", "DE"); await page.fill("[name=nif]", "DE811234567");
    await page.fill("[name=contacto]", "X"); await page.fill("[name=email]", "x@dup.de"); await page.check("[name=consent]");
    await page.click("#modal-save");
    await page.waitForSelector(".form-errors:not([hidden])");
    assert.match(await page.locator(".form-errors").innerText(), /identificación fiscal/);
    await ctx.close();
  });

  test("PS-05 [QC017][HU-03][RF-09] crear un producto y verlo en el catálogo con su foto", async () => {
    const { ctx, page } = await abrir(); await entrar(page); await ir(page, "productos");
    await page.click("#new-prod"); await page.waitForSelector("#modal.show");
    await page.fill("[name=nombre]", "Café Geisha"); await page.fill("[name=codigo]", "CAF-GEI-01"); await page.fill("[name=variedad]", "Geisha"); await page.fill("[name=precio]", "18.50");
    await page.click("#modal-save"); await page.waitForSelector("#modal", { state: "hidden" });
    await page.fill("#f-q", "Geisha"); await page.waitForTimeout(300);
    assert.equal(await page.locator("#tbl tbody tr").count(), 1);
    assert.equal((await api(page, "/api/productos?q=GEI")).length, 1); await ctx.close();
  });

  test("PS-06 [QC018][HU-04][RF-13][RF-14] inventario: una entrada actualiza el stock del servidor y una salida excesiva se rechaza", async () => {
    const { ctx, page } = await abrir(); await entrar(page, "bodega@ritech.co"); await ir(page, "inventario");
    const antes = (await api(page, "/api/inventario/stock/3")).totalKg;
    await page.click("#new-mov"); await page.waitForSelector("#modal.show");
    await page.selectOption("[name=producto]", "3"); await page.selectOption("[name=bodega]", "2"); await page.selectOption("[name=tipo]", "ENTRADA"); await page.fill("[name=cant]", "100");
    await page.click("#modal-save"); await page.waitForSelector("#modal", { state: "hidden" });
    assert.equal((await api(page, "/api/inventario/stock/3")).totalKg, antes + 100);
    await page.click("#new-mov"); await page.waitForSelector("#modal.show");
    await page.selectOption("[name=producto]", "3"); await page.selectOption("[name=bodega]", "2"); await page.selectOption("[name=tipo]", "SALIDA"); await page.fill("[name=cant]", "999999");
    await page.click("#modal-save"); await page.waitForSelector(".form-errors:not([hidden])");
    assert.match(await page.locator(".form-errors").innerText(), /Stock insuficiente: disponible/);
    await foto(page, "PS-06-salida-rechazada-servidor"); await ctx.close();
  });

  test("PS-07 [QC021][HU-11][HU-14][RF-16][RF-19][RF-20] el asistente de 4 pasos crea la exportación, adjunta los PDF y descuenta el inventario del servidor", async () => {
    const { ctx, page } = await abrir(); await entrar(page, "exportaciones@ritech.co");
    const antes = (await api(page, "/api/inventario/stock/1")).totalKg;
    await ir(page, "exportaciones/nueva"); await page.click("#w-next");
    await page.selectOption("[name=cliente]", "1"); await page.selectOption("[name=llegada]", "Hamburgo"); await page.click("#w-next");
    await page.selectOption("[data-k=producto]", "1"); await page.fill("[data-k=kg]", "300"); await page.click("#w-next");
    for (const tipo of ["CERTIFICADO_ORIGEN", "FITOSANITARIO"]) await page.setInputFiles(`[data-doc="${tipo}"]`, { name: tipo + ".pdf", mimeType: "application/pdf", buffer: PDF });
    await foto(page, "PS-07-asistente-documentos");
    await page.click("#w-finish"); await page.waitForFunction(() => location.hash === "#exportaciones"); await page.waitForTimeout(500);
    const lista = await api(page, "/api/exportaciones");
    const nueva = lista.find(e => e.estado === "EN_PREPARACION" && e.totalUsd === 1350);
    assert.ok(nueva, "la exportación existe en el servidor"); assert.match(nueva.codigo, /^EXP-\d{4}-\d{4}$/);
    assert.equal((await api(page, "/api/inventario/stock/1")).totalKg, antes - 300);
    assert.equal((await api(page, `/api/exportaciones/${nueva.id}/documentos`)).length, 2);
    await foto(page, "PS-07-exportacion-creada-servidor"); await ctx.close();
  });

  test("PS-08 [QC011][HU-06][RNF-03] el operador de bodega no ve Clientes: ni en el menú ni forzando la ruta ni llamando a la API", async () => {
    const { ctx, page } = await abrir(); await entrar(page, "bodega@ritech.co");
    assert.deepEqual(await page.$$eval("#nav a", a => a.map(x => x.dataset.m)), ["productos", "inventario"]);
    await ir(page, "clientes"); assert.equal(await page.evaluate(() => location.hash), "#inventario");
    const r = await page.evaluate(async () => (await fetch(Api.base + "/api/clientes", { credentials: "include" })).status);
    assert.equal(r, 403, "el servidor también lo rechaza (no solo la interfaz)"); await ctx.close();
  });

  test("PS-09 [HU-16][HU-17][RF-23][RF-25] el contador registra un pago en euros y lo confirma; el saldo del servidor baja", async () => {
    const { ctx, page } = await abrir(); await entrar(page, "contador@ritech.co"); await ir(page, "pagos");
    const exp = (await api(page, "/api/exportaciones")).find(e => e.estado === "EN_TRANSITO");
    const saldoAntes = (await api(page, `/api/pagos/saldo/${exp.id}`)).saldoPendienteUsd;
    await page.click("#new-pay"); await page.waitForSelector("#modal.show");
    await page.selectOption("[name=exp]", String(exp.id)); await page.fill("[name=monto]", "100"); await page.selectOption("[name=moneda]", "EUR"); await page.fill("[name=ref]", "TRX-E2E");
    await page.click("#modal-save"); await page.waitForSelector("#modal", { state: "hidden" });
    const pago = (await api(page, "/api/pagos")).find(p => p.referencia === "TRX-E2E");
    assert.equal(pago.estado, "PENDIENTE"); assert.equal(pago.moneda, "EUR");
    await page.click(`[data-ok="${pago.id}"]`); await page.waitForTimeout(700);
    const saldoDespues = (await api(page, `/api/pagos/saldo/${exp.id}`)).saldoPendienteUsd;
    assert.ok(Math.abs((saldoAntes - saldoDespues) - 108) < 0.01, `el saldo baja 108 USD (100 EUR a 1,08): ${saldoAntes} -> ${saldoDespues}`);
    await ctx.close();
  });

  test("PS-10 [QC019][RNF-12][RNF-08] usabilidad móvil (375 × 812): login y dashboard sin desplazamiento horizontal, controles operables y menú lateral", async () => {
    const { ctx, page } = await abrir({ width: 375, height: 812 });
    await page.goto(`${base}/app.html?api=${encodeURIComponent(API)}`);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), "el login no desborda horizontalmente");
    for (const sel of ["#login-email", "#login-pass", "#login-form button[type=submit]"]) {
      const b = await page.locator(sel).boundingBox(); assert.ok(b && b.width >= 120 && b.height >= 36, `${sel} es visible y de tamaño táctil`);
    }
    await foto(page, "PS-10-login-movil");
    await page.click('#demo-users [data-u="admin@ritech.co"]'); await page.click("#login-form button[type=submit]");
    await page.waitForSelector("#app:not([hidden])"); await page.waitForSelector(".kpi");
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), "el dashboard no desborda horizontalmente");
    assert.equal(await page.locator("#sidebar").evaluate(el => el.getBoundingClientRect().right <= 0), true, "el menú lateral está oculto");
    await page.click("#menu-toggle"); await page.waitForTimeout(500);
    assert.ok(await page.locator("#sidebar.open").count() === 1, "el botón de menú abre la barra lateral");
    await foto(page, "PS-10-menu-movil"); await ctx.close();
  });
});
