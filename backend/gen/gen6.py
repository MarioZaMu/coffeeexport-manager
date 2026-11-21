# -*- coding: utf-8 -*-
"""Pruebas del backend, parte 2: integración con MockMvc + H2 (API REST, seguridad, flujos)."""
import os
AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(AQUI, "..", "src", "test", "java", "co", "ritech", "coffeeexport", "integracion")
F = {}

F["IntegracionBase.java"] = r'''package co.ritech.coffeeexport.integracion;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import co.ritech.coffeeexport.clientes.ClienteRepository;
import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.inventario.BodegaRepository;
import co.ritech.coffeeexport.productos.ProductoRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

/**
 * Base de las pruebas de integración: la aplicación completa (seguridad, controladores, servicios, JPA, H2 en modo MySQL)
 * con los datos de demostración. Cada prueba se revierte al terminar (@Transactional), así no se contaminan entre sí.
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
@TestPropertySource(properties = {"app.seed.demo=true", "app.storage.dir=${java.io.tmpdir}/coffeeexport-pruebas"})
public abstract class IntegracionBase {
    protected static final String CLAVE = "Demo2026*";
    protected static final byte[] PDF = "%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF".getBytes();

    @Autowired protected MockMvc mvc;
    @Autowired protected ObjectMapper json;
    @Autowired protected ClienteRepository clientes;
    @Autowired protected ProductoRepository productos;
    @Autowired protected BodegaRepository bodegas;
    @Autowired protected ExportacionRepository exportaciones;

    protected MockHttpSession login(String email) throws Exception {
        MvcResult r = mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON).content(cuerpo("email", email, "password", CLAVE)))
                .andExpect(status().isOk()).andReturn();
        return (MockHttpSession) r.getRequest().getSession(false);
    }

    protected MockHttpSession admin() throws Exception {
        return login("admin@ritech.co");
    }

    protected String cuerpo(Object... pares) throws Exception {
        Map<String, Object> m = new LinkedHashMap<>();
        for (int i = 0; i < pares.length; i += 2) {
            m.put((String) pares[i], pares[i + 1]);
        }
        return json.writeValueAsString(m);
    }

    protected JsonNode leer(MvcResult r) throws Exception {
        return json.readTree(r.getResponse().getContentAsString());
    }

    protected Long productoId(String codigo) {
        return productos.findAll().stream().filter(p -> p.getCodigo().equals(codigo)).findFirst().orElseThrow().getId();
    }

    protected Long bodegaId(String nombre) {
        return bodegas.findAll().stream().filter(b -> b.getNombre().equals(nombre)).findFirst().orElseThrow().getId();
    }

    protected Long clienteId(String nif) {
        return clientes.findByIdentificacionFiscalIgnoreCase(nif).orElseThrow().getId();
    }

    protected Exportacion exportacionEn(EstadoExportacion estado) {
        return exportaciones.findAll().stream().filter(e -> e.getEstado() == estado).findFirst().orElseThrow();
    }

    protected static LocalDate enDias(int dias) {
        return LocalDate.now(ZoneId.of("America/Bogota")).plusDays(dias);
    }
}
'''

F["AutenticacionIT.java"] = r'''package co.ritech.coffeeexport.integracion;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpSession;

class AutenticacionIT extends IntegracionBase {

    @Test
    @DisplayName("QC001 [HU-01][RF-01] Iniciar sesión por la API con credenciales válidas")
    void qc001() throws Exception {
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON).content(cuerpo("email", "admin@ritech.co", "password", CLAVE)))
                .andExpect(status().isOk()).andExpect(jsonPath("$.rol").value("ADMIN")).andExpect(jsonPath("$.email").value("admin@ritech.co"))
                .andExpect(jsonPath("$.passwordHash").doesNotExist()).andExpect(jsonPath("$.permisos").isArray());
    }

    @Test
    @DisplayName("QC002 [HU-01][RF-01] Rechazar el inicio de sesión con contraseña incorrecta (mensaje genérico)")
    void qc002() throws Exception {
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON).content(cuerpo("email", "admin@ritech.co", "password", "incorrecta")))
                .andExpect(status().isUnauthorized()).andExpect(jsonPath("$.error").value("Credenciales incorrectas"));
        mvc.perform(get("/api/auth/me")).andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("QC010 [HU-01][RNF-03] Un recurso protegido sin sesión responde 401 y no devuelve datos")
    void qc010() throws Exception {
        for (String ruta : new String[]{"/api/clientes", "/api/productos", "/api/inventario", "/api/exportaciones", "/api/pagos", "/api/dashboard/kpis"}) {
            mvc.perform(get(ruta)).andExpect(status().isUnauthorized()).andExpect(jsonPath("$.error").value("Debe iniciar sesión"));
        }
    }

    @Test
    @DisplayName("QC011 [HU-01][RNF-03] Acceder a una función sin el rol requerido responde 403 y no ejecuta la acción")
    void qc011() throws Exception {
        MockHttpSession bodega = login("bodega@ritech.co");
        long antes = clientes.count();
        mvc.perform(post("/api/clientes").session(bodega).contentType(MediaType.APPLICATION_JSON).content(cuerpo(
                        "nombre", "Intruso", "pais", "DE", "identificacionFiscal", "DE000", "contactoNombre", "X", "contactoEmail", "x@x.de", "consentimientoDatos", true)))
                .andExpect(status().isForbidden()).andExpect(jsonPath("$.error").value(containsString("rol no tiene permiso")));
        org.assertj.core.api.Assertions.assertThat(clientes.count()).isEqualTo(antes);
    }

    @Test
    @DisplayName("QC012 [HU-01][RNF-04] Intento básico de inyección SQL en el login: no inicia sesión y no hay error SQL")
    void qc012() throws Exception {
        for (String ataque : new String[]{"' OR '1'='1' --", "admin@ritech.co' --", "\" OR \"\"=\"", "'; DROP TABLE usuarios; --"}) {
            mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON).content(cuerpo("email", ataque, "password", "x")))
                    .andExpect(status().isUnauthorized()).andExpect(jsonPath("$.error").value("Credenciales incorrectas"));
        }
        login("admin@ritech.co");   // la tabla usuarios sigue intacta
    }

    @Test
    @DisplayName("QC014 [HU-01][RF-02] Cerrar sesión invalida la sesión: la misma cookie ya no sirve")
    void qc014() throws Exception {
        MockHttpSession s = admin();
        mvc.perform(get("/api/auth/me").session(s)).andExpect(status().isOk());
        mvc.perform(post("/api/auth/logout").session(s)).andExpect(status().isNoContent());
        mvc.perform(get("/api/clientes").session(s)).andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("QC015 [HU-01][RF-01] Flujo: iniciar sesión, ver el dashboard y cerrar sesión")
    void qc015() throws Exception {
        MockHttpSession s = admin();
        mvc.perform(get("/api/dashboard/kpis").session(s)).andExpect(status().isOk());
        mvc.perform(post("/api/auth/logout").session(s)).andExpect(status().isNoContent());
        mvc.perform(get("/api/dashboard/kpis").session(s)).andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("[HU-01][RF-01] Un usuario inactivo no puede iniciar sesión (403 con mensaje claro)")
    void usuarioInactivo() throws Exception {
        MockHttpSession a = admin();
        mvc.perform(post("/api/usuarios").session(a).contentType(MediaType.APPLICATION_JSON).content(cuerpo(
                "nombre", "Baja", "email", "baja@ritech.co", "password", "Clave2026*", "rol", "OP_BODEGA", "activo", false))).andExpect(status().isCreated());
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON).content(cuerpo("email", "baja@ritech.co", "password", "Clave2026*")))
                .andExpect(status().isForbidden()).andExpect(jsonPath("$.error").value(containsString("inactivo")));
    }

    @Test
    @DisplayName("[HU-01][RF-01] Faltan datos de login: se valida por campo (400)")
    void loginIncompleto() throws Exception {
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.campos.email").exists()).andExpect(jsonPath("$.campos.password").exists());
    }
}
'''

F["CorsIT.java"] = r'''package co.ritech.coffeeexport.integracion;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.options;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;

/** CORS: el sitio web (otro puerto) debe poder llamar a la API con cookies, y ningún otro origen. */
class CorsIT extends IntegracionBase {

    @Test
    @DisplayName("[HU-01][RNF-05] Un origen local permitido recibe las cabeceras CORS con credenciales (preflight y petición real)")
    void origenPermitido() throws Exception {
        mvc.perform(options("/api/auth/login").header(HttpHeaders.ORIGIN, "http://127.0.0.1:5500")
                        .header(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD, "POST").header(HttpHeaders.ACCESS_CONTROL_REQUEST_HEADERS, "content-type"))
                .andExpect(status().isOk()).andExpect(header().string(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN, "http://127.0.0.1:5500"))
                .andExpect(header().string(HttpHeaders.ACCESS_CONTROL_ALLOW_CREDENTIALS, "true"));
        mvc.perform(post("/api/auth/login").header(HttpHeaders.ORIGIN, "http://localhost:8000").contentType(MediaType.APPLICATION_JSON)
                        .content(cuerpo("email", "admin@ritech.co", "password", CLAVE)))
                .andExpect(status().isOk()).andExpect(header().string(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN, "http://localhost:8000"));
    }

    @Test
    @DisplayName("[HU-01][RNF-05] Un origen desconocido es rechazado por CORS (403) y no recibe cabeceras de permiso")
    void origenNoPermitido() throws Exception {
        mvc.perform(post("/api/auth/login").header(HttpHeaders.ORIGIN, "https://sitio-malicioso.example").contentType(MediaType.APPLICATION_JSON)
                        .content(cuerpo("email", "admin@ritech.co", "password", CLAVE)))
                .andExpect(status().isForbidden()).andExpect(header().doesNotExist(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN));
    }
}
'''

F["MatrizPermisosIT.java"] = r'''package co.ritech.coffeeexport.integracion;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpSession;

/** Matriz de permisos por rol (RF-04, RNF-03): lectura y escritura de cada módulo contra el backend real. */
class MatrizPermisosIT extends IntegracionBase {

    @ParameterizedTest(name = "[HU-06][RNF-03] {0} lee {1} → {2}")
    @DisplayName("Lectura por rol")
    @CsvSource({
            "admin@ritech.co,/api/clientes,200", "gerente@ritech.co,/api/clientes,200", "exportaciones@ritech.co,/api/clientes,200",
            "bodega@ritech.co,/api/clientes,403", "contador@ritech.co,/api/clientes,403",
            "bodega@ritech.co,/api/productos,200", "contador@ritech.co,/api/productos,403",
            "bodega@ritech.co,/api/inventario,200", "contador@ritech.co,/api/inventario,403",
            "contador@ritech.co,/api/exportaciones,200", "bodega@ritech.co,/api/exportaciones,403",
            "contador@ritech.co,/api/pagos,200", "exportaciones@ritech.co,/api/pagos,403", "bodega@ritech.co,/api/pagos,403",
            "gerente@ritech.co,/api/dashboard/kpis,200", "exportaciones@ritech.co,/api/dashboard/kpis,403", "contador@ritech.co,/api/dashboard/kpis,403",
            "contador@ritech.co,/api/reportes,400", "bodega@ritech.co,/api/reportes,403",
            "admin@ritech.co,/api/usuarios,200", "gerente@ritech.co,/api/usuarios,403", "contador@ritech.co,/api/usuarios,403",
            "exportaciones@ritech.co,/api/documentos,200", "bodega@ritech.co,/api/documentos,403"})
    void lectura(String usuario, String ruta, int esperado) throws Exception {
        MockHttpSession s = login(usuario);
        int real = mvc.perform(get(ruta).session(s)).andReturn().getResponse().getStatus();
        assertThat(real).as("%s GET %s", usuario, ruta).isEqualTo(esperado);   // 400 = autorizado pero faltan parámetros del reporte
    }

    @ParameterizedTest(name = "[HU-06][RNF-03] {0} escribe en {1} → {2}")
    @DisplayName("Escritura por rol (se envía un cuerpo vacío: 403 = sin permiso, 400 = autorizado pero inválido)")
    @CsvSource({
            "admin@ritech.co,/api/clientes,400", "exportaciones@ritech.co,/api/clientes,400", "gerente@ritech.co,/api/clientes,403",
            "bodega@ritech.co,/api/clientes,403", "contador@ritech.co,/api/clientes,403",
            "admin@ritech.co,/api/productos,400", "exportaciones@ritech.co,/api/productos,403", "bodega@ritech.co,/api/productos,403",
            "bodega@ritech.co,/api/inventario/movimientos,400", "admin@ritech.co,/api/inventario/movimientos,400",
            "exportaciones@ritech.co,/api/inventario/movimientos,403", "gerente@ritech.co,/api/inventario/movimientos,403",
            "exportaciones@ritech.co,/api/exportaciones,400", "gerente@ritech.co,/api/exportaciones,403", "contador@ritech.co,/api/exportaciones,403",
            "contador@ritech.co,/api/pagos,400", "admin@ritech.co,/api/pagos,400", "exportaciones@ritech.co,/api/pagos,403", "gerente@ritech.co,/api/pagos,403",
            "admin@ritech.co,/api/usuarios,400", "exportaciones@ritech.co,/api/usuarios,403"})
    void escritura(String usuario, String ruta, int esperado) throws Exception {
        MockHttpSession s = login(usuario);
        int real = mvc.perform(post(ruta).session(s).contentType(MediaType.APPLICATION_JSON).content("{}")).andReturn().getResponse().getStatus();
        assertThat(real).as("%s POST %s", usuario, ruta).isEqualTo(esperado);
    }
}
'''

F["ClienteIT.java"] = r'''package co.ritech.coffeeexport.integracion;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpSession;

class ClienteIT extends IntegracionBase {

    private String nuevo(String nombre, String pais, String nif, boolean consentimiento) throws Exception {
        return cuerpo("nombre", nombre, "pais", pais, "identificacionFiscal", nif, "contactoNombre", "Eva Smit", "contactoEmail", "eva@cliente.nl",
                "contactoTelefono", "+31 20 1", "direccion", "Ámsterdam", "consentimientoDatos", consentimiento);
    }

    @Test
    @DisplayName("QC003 [HU-02][RF-05] Registrar un cliente por la API y verificar su persistencia")
    void qc003() throws Exception {
        MockHttpSession s = login("exportaciones@ritech.co");
        mvc.perform(post("/api/clientes").session(s).contentType(MediaType.APPLICATION_JSON).content(nuevo("Café del Norte BV", "NL", "NL999999999B01", true)))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.activo").value(true)).andExpect(jsonPath("$.consentimientoDatos").value(true))
                .andExpect(jsonPath("$.fechaConsentimiento").exists());
        assertThat(clientes.existsByIdentificacionFiscalIgnoreCase("NL999999999B01")).isTrue();
    }

    @Test
    @DisplayName("QC004 [HU-02][RF-07] Filtrar clientes por país mediante la API")
    void qc004() throws Exception {
        MvcResult_ r = new MvcResult_();
        mvc.perform(get("/api/clientes").param("pais", "FR").session(admin())).andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].pais").value("FR")).andExpect(jsonPath("$[0].nombre").value("France Agro"));
        mvc.perform(get("/api/clientes").param("pais", "dk").session(admin())).andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    @DisplayName("QC005 [HU-02][RF-06] Editar un cliente existente")
    void qc005() throws Exception {
        Long id = clienteId("DE811234567");
        mvc.perform(put("/api/clientes/{id}", id).session(admin()).contentType(MediaType.APPLICATION_JSON)
                        .content(cuerpo("nombre", "Kaffee GmbH", "pais", "DE", "identificacionFiscal", "DE811234567", "contactoNombre", "Hans Becker",
                                "contactoEmail", "nuevo@kaffeegmbh.de", "consentimientoDatos", true)))
                .andExpect(status().isOk()).andExpect(jsonPath("$.contactoEmail").value("nuevo@kaffeegmbh.de"));
        assertThat(clientes.findById(id).orElseThrow().getContactoEmail()).isEqualTo("nuevo@kaffeegmbh.de");
    }

    @Test
    @DisplayName("QC013 [HU-02][RNF-04] Inyección SQL en la búsqueda de clientes: lista vacía y la tabla intacta")
    void qc013() throws Exception {
        long antes = clientes.count();
        for (String ataque : new String[]{"'; DROP TABLE clientes; --", "' OR '1'='1", "x%' UNION SELECT * FROM usuarios --"}) {
            mvc.perform(get("/api/clientes").param("q", ataque).session(admin())).andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(0)));
        }
        assertThat(clientes.count()).isEqualTo(antes);
    }

    @Test
    @DisplayName("QC016 [HU-02][RF-05] Flujo: registrar un cliente y verlo en el listado")
    void qc016() throws Exception {
        MockHttpSession s = admin();
        mvc.perform(post("/api/clientes").session(s).contentType(MediaType.APPLICATION_JSON).content(nuevo("Tulip Trading", "NL", "NL123", true))).andExpect(status().isCreated());
        mvc.perform(get("/api/clientes").param("q", "tulip").session(s)).andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].nombre").value("Tulip Trading"));
    }

    @Test
    @DisplayName("QC020 [HU-02][RF-05][RF-08] Validaciones: campos obligatorios, país fuera de la UE, NIF duplicado y consentimiento")
    void qc020() throws Exception {
        MockHttpSession s = admin();
        mvc.perform(post("/api/clientes").session(s).contentType(MediaType.APPLICATION_JSON).content("{}")).andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.campos.nombre").exists()).andExpect(jsonPath("$.campos.pais").exists()).andExpect(jsonPath("$.campos.identificacionFiscal").exists());
        mvc.perform(post("/api/clientes").session(s).contentType(MediaType.APPLICATION_JSON).content(nuevo("Yankee Inc", "US", "US1", true)))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value(containsString("Unión Europea")));
        mvc.perform(post("/api/clientes").session(s).contentType(MediaType.APPLICATION_JSON).content(nuevo("Duplicado SA", "DE", "DE811234567", true)))
                .andExpect(status().isConflict()).andExpect(jsonPath("$.error").value(containsString("identificación fiscal")));
        mvc.perform(post("/api/clientes").session(s).contentType(MediaType.APPLICATION_JSON).content(nuevo("Sin Consent", "FR", "FR9", false)))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value(containsString("consentimiento")));
    }

    @Test
    @DisplayName("[HU-02][RF-06] Desactivar un cliente lo conserva (baja lógica) y se puede filtrar por estado")
    void bajaLogica() throws Exception {
        MockHttpSession s = admin();
        Long id = clienteId("FR40303265045");
        mvc.perform(patch("/api/clientes/{id}/estado", id).session(s).contentType(MediaType.APPLICATION_JSON).content("{\"activo\":false}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.activo").value(false));
        assertThat(clientes.existsById(id)).isTrue();
        mvc.perform(get("/api/clientes").param("activo", "false").session(s)).andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(2)));
    }

    @Test
    @DisplayName("[HU-02][RF-07] Un cliente inexistente responde 404")
    void noEncontrado() throws Exception {
        mvc.perform(get("/api/clientes/{id}", 999999).session(admin())).andExpect(status().isNotFound());
    }

    /** Marcador sin uso para mantener el estilo de las pruebas (no se necesita el resultado intermedio). */
    private static final class MvcResult_ {
    }
}
'''

F["ProductoInventarioIT.java"] = r'''package co.ritech.coffeeexport.integracion;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpSession;

class ProductoInventarioIT extends IntegracionBase {

    private String nuevoProducto(String codigo, Object precio) throws Exception {
        return cuerpo("codigo", codigo, "nombre", "Café Geisha", "tipo", "CAFE", "variedad", "Geisha", "precioUsdKg", precio);
    }

    private String movimiento(String producto, String bodega, String tipo, Object kg) throws Exception {
        return cuerpo("productoId", productoId(producto), "bodegaId", bodegaId(bodega), "tipo", tipo, "cantidadKg", kg, "motivo", "Prueba");
    }

    // ------------------------------------------------------------------ productos
    @Test
    @DisplayName("QC006 [HU-03][RF-09] Registrar un producto por la API como administrador")
    void qc006() throws Exception {
        mvc.perform(post("/api/productos").session(admin()).contentType(MediaType.APPLICATION_JSON).content(nuevoProducto("CAF-GEI-01", 18.5)))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.activo").value(true)).andExpect(jsonPath("$.precioUsdKg").value(18.5));
        assertThat(productos.findAll()).extracting(p -> p.getCodigo()).contains("CAF-GEI-01");
    }

    @Test
    @DisplayName("QC007 [HU-03][RF-10] Consultar el catálogo por la API filtrando por tipo")
    void qc007() throws Exception {
        mvc.perform(get("/api/productos").param("tipo", "CAFE").session(login("exportaciones@ritech.co"))).andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(3))).andExpect(jsonPath("$[*].tipo", everyItem(is("CAFE"))));
        mvc.perform(get("/api/productos").param("tipo", "CACAO").session(admin())).andExpect(jsonPath("$", hasSize(3)));
    }

    @Test
    @DisplayName("QC017 [HU-03][RF-09] Flujo: crear un producto y verlo en el catálogo")
    void qc017() throws Exception {
        MockHttpSession s = admin();
        mvc.perform(post("/api/productos").session(s).contentType(MediaType.APPLICATION_JSON).content(nuevoProducto("CAC-NEW-01", 6.2))).andExpect(status().isCreated());
        mvc.perform(get("/api/productos").param("q", "CAC-NEW").session(s)).andExpect(jsonPath("$", hasSize(1)));
    }

    @Test
    @DisplayName("[HU-03][RF-09] Un precio negativo o un código repetido se rechazan")
    void validacionesProducto() throws Exception {
        MockHttpSession s = admin();
        mvc.perform(post("/api/productos").session(s).contentType(MediaType.APPLICATION_JSON).content(nuevoProducto("X-1", -5)))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value(containsString("precio debe ser mayor que cero")));
        mvc.perform(post("/api/productos").session(s).contentType(MediaType.APPLICATION_JSON).content(nuevoProducto("CAF-ARA-01", 5)))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value(containsString("código")));
    }

    @Test
    @DisplayName("[HU-08][RF-11] Desactivar un producto lo conserva y lo marca inactivo")
    void bajaProducto() throws Exception {
        Long id = productoId("CAF-ROB-01");
        mvc.perform(patch("/api/productos/{id}/estado", id).session(admin()).contentType(MediaType.APPLICATION_JSON).content("{\"activo\":false}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.activo").value(false));
        assertThat(productos.findById(id)).isPresent();
    }

    // ------------------------------------------------------------------ inventario
    @Test
    @DisplayName("QC008 [HU-04][RF-12] Consultar el stock de un producto con existencias en dos bodegas")
    void qc008() throws Exception {
        mvc.perform(get("/api/inventario/stock/{id}", productoId("CAF-ARA-01")).session(login("bodega@ritech.co"))).andExpect(status().isOk())
                .andExpect(jsonPath("$.totalKg").value(2500.0)).andExpect(jsonPath("$.bodegas", hasSize(2)));
    }

    @Test
    @DisplayName("QC009 [HU-04][RF-14] Rechazar un movimiento de salida mayor al stock (409) sin cambiar el inventario")
    void qc009() throws Exception {
        MockHttpSession s = login("bodega@ritech.co");
        mvc.perform(post("/api/inventario/movimientos").session(s).contentType(MediaType.APPLICATION_JSON).content(movimiento("CAF-CAS-01", "Bodega Bogotá", "SALIDA", 999999)))
                .andExpect(status().isConflict()).andExpect(jsonPath("$.error").value("Stock insuficiente: disponible 2.200 kg en esa bodega."));
        mvc.perform(get("/api/inventario/stock/{id}", productoId("CAF-CAS-01")).session(s)).andExpect(jsonPath("$.totalKg").value(2200.0));
    }

    @Test
    @DisplayName("QC018 [HU-04][RF-13] Flujo: consultar inventario, registrar una entrada y ver el stock actualizado y el historial")
    void qc018() throws Exception {
        MockHttpSession s = login("bodega@ritech.co");
        mvc.perform(post("/api/inventario/movimientos").session(s).contentType(MediaType.APPLICATION_JSON).content(movimiento("CAF-CAS-01", "Bodega Bogotá", "ENTRADA", 100)))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.tipo").value("ENTRADA")).andExpect(jsonPath("$.usuario").value("Operador Bodega"));
        mvc.perform(get("/api/inventario/stock/{id}", productoId("CAF-CAS-01")).session(s)).andExpect(jsonPath("$.totalKg").value(2300.0));
        mvc.perform(get("/api/inventario/movimientos").session(s)).andExpect(status().isOk()).andExpect(jsonPath("$[0].motivo").value("Prueba"));
    }

    @Test
    @DisplayName("[HU-04][RF-13] Cantidades inválidas y tipos de movimiento desconocidos se rechazan; un ajuste fija el stock")
    void validacionesMovimiento() throws Exception {
        MockHttpSession s = login("bodega@ritech.co");
        mvc.perform(post("/api/inventario/movimientos").session(s).contentType(MediaType.APPLICATION_JSON).content(movimiento("CAF-CAS-01", "Bodega Bogotá", "ENTRADA", 0)))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value(containsString("mayor que cero")));
        mvc.perform(post("/api/inventario/movimientos").session(s).contentType(MediaType.APPLICATION_JSON).content(movimiento("CAF-CAS-01", "Bodega Bogotá", "ROBO", 5)))
                .andExpect(status().isBadRequest());
        mvc.perform(post("/api/inventario/movimientos").session(s).contentType(MediaType.APPLICATION_JSON).content(movimiento("CAF-CAS-01", "Bodega Bogotá", "AJUSTE", 1800)))
                .andExpect(status().isCreated());
        mvc.perform(get("/api/inventario/stock/{id}", productoId("CAF-CAS-01")).session(s)).andExpect(jsonPath("$.totalKg").value(1800.0));
    }

    @Test
    @DisplayName("[HU-09][RF-15] El stock mínimo se puede actualizar y no admite valores negativos")
    void stockMinimo() throws Exception {
        MockHttpSession s = login("bodega@ritech.co");
        Long invId = new BigDecimal(1).longValue();
        mvc.perform(patch("/api/inventario/{id}/minimo", invId).session(s).contentType(MediaType.APPLICATION_JSON).content("{\"stockMinimoKg\":900}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.stockMinimoKg").value(900.0));
        mvc.perform(patch("/api/inventario/{id}/minimo", invId).session(s).contentType(MediaType.APPLICATION_JSON).content("{\"stockMinimoKg\":-1}"))
                .andExpect(status().isBadRequest());
    }
}
'''

F["ExportacionDocumentoPagoIT.java"] = r'''package co.ritech.coffeeexport.integracion;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MvcResult;

class ExportacionDocumentoPagoIT extends IntegracionBase {

    private String exportacion(String estadoInicial, Object kg, String pais) throws Exception {
        return json.writeValueAsString(Map.of("clienteId", clienteId("DE811234567"), "paisDestino", pais, "puertoSalida", "Cartagena", "puertoLlegada", "Hamburgo",
                "fechaEnvio", enDias(10).toString(), "estadoInicial", estadoInicial, "observaciones", "Prueba",
                "lineas", List.of(Map.of("productoId", productoId("CAF-ARA-01"), "cantidadKg", kg, "precioUnitario", 4.5))));
    }

    private JsonNode crear(MockHttpSession s, String estadoInicial, Object kg) throws Exception {
        MvcResult r = mvc.perform(post("/api/exportaciones").session(s).contentType(MediaType.APPLICATION_JSON).content(exportacion(estadoInicial, kg, "DE")))
                .andExpect(status().isCreated()).andReturn();
        return leer(r);
    }

    private void subirPdf(MockHttpSession s, long exportacionId, String tipo) throws Exception {
        mvc.perform(multipart("/api/exportaciones/{id}/documentos", exportacionId).file(new MockMultipartFile("archivo", tipo.toLowerCase() + ".pdf", "application/pdf", PDF))
                .param("tipo", tipo).session(s)).andExpect(status().isCreated());
    }

    private double stockArabica(MockHttpSession s) throws Exception {
        return leer(mvc.perform(get("/api/inventario/stock/{id}", productoId("CAF-ARA-01")).session(s)).andReturn()).get("totalKg").asDouble();
    }

    // ------------------------------------------------------------------ exportaciones
    @Test
    @DisplayName("QC022 [HU-11][RF-16][RF-19] Crear una exportación por la API con productos, calcular el total y descontar el inventario")
    void qc022() throws Exception {
        MockHttpSession s = login("exportaciones@ritech.co");
        JsonNode ex = crear(s, "EN_PREPARACION", 300);
        assertThat(ex.get("estado").asText()).isEqualTo("EN_PREPARACION");
        assertThat(ex.get("descontado").asBoolean()).isTrue();
        assertThat(ex.get("totalUsd").asDouble()).isEqualTo(1350.0);
        assertThat(ex.get("lineas")).hasSize(1);
        assertThat(ex.get("codigo").asText()).matches("EXP-\\d{4}-\\d{4}");
        assertThat(stockArabica(s)).isEqualTo(2200.0);
    }

    @Test
    @DisplayName("[HU-11][RF-16] Una exportación en borrador no descuenta inventario hasta confirmarse")
    void borradorNoDescuenta() throws Exception {
        MockHttpSession s = login("exportaciones@ritech.co");
        JsonNode ex = crear(s, "BORRADOR", 300);
        assertThat(ex.get("estado").asText()).isEqualTo("BORRADOR");
        assertThat(stockArabica(s)).isEqualTo(2500.0);
        mvc.perform(patch("/api/exportaciones/{id}/estado", ex.get("id").asLong()).session(s).contentType(MediaType.APPLICATION_JSON).content("{\"estado\":\"EN_PREPARACION\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.estado").value("EN_PREPARACION"));
        assertThat(stockArabica(s)).isEqualTo(2200.0);
    }

    @Test
    @DisplayName("[HU-11][RF-17] Una cantidad mayor al stock se rechaza (409) con el detalle y sin crear la exportación")
    void stockInsuficiente() throws Exception {
        MockHttpSession s = login("exportaciones@ritech.co");
        long antes = exportaciones.count();
        mvc.perform(post("/api/exportaciones").session(s).contentType(MediaType.APPLICATION_JSON).content(exportacion("EN_PREPARACION", 99999, "DE")))
                .andExpect(status().isConflict()).andExpect(jsonPath("$.error").value("Stock insuficiente de Café Arábica: solicitado 99.999 kg, disponible 2.500 kg"));
        assertThat(exportaciones.count()).isEqualTo(antes);
    }

    @Test
    @DisplayName("[HU-11][RF-16] País destino fuera de la UE, fecha pasada y cliente inactivo se rechazan")
    void validacionesExportacion() throws Exception {
        MockHttpSession s = login("exportaciones@ritech.co");
        mvc.perform(post("/api/exportaciones").session(s).contentType(MediaType.APPLICATION_JSON).content(exportacion("BORRADOR", 100, "US")))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value(containsString("Unión Europea")));
        String pasada = json.writeValueAsString(Map.of("clienteId", clienteId("DE811234567"), "paisDestino", "DE", "puertoSalida", "Cartagena", "puertoLlegada", "Hamburgo",
                "fechaEnvio", enDias(-2).toString(), "lineas", List.of(Map.of("productoId", productoId("CAF-ARA-01"), "cantidadKg", 100, "precioUnitario", 4.5))));
        mvc.perform(post("/api/exportaciones").session(s).contentType(MediaType.APPLICATION_JSON).content(pasada))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value(containsString("pasado")));
        mvc.perform(post("/api/exportaciones").session(s).contentType(MediaType.APPLICATION_JSON).content("{}")).andExpect(status().isBadRequest()).andExpect(jsonPath("$.campos").exists());
    }

    @Test
    @DisplayName("[HU-12][RF-19] Cancelar una exportación en preparación devuelve el stock descontado")
    void cancelarDevuelveStock() throws Exception {
        MockHttpSession s = login("exportaciones@ritech.co");
        JsonNode ex = crear(s, "EN_PREPARACION", 400);
        assertThat(stockArabica(s)).isEqualTo(2100.0);
        mvc.perform(patch("/api/exportaciones/{id}/estado", ex.get("id").asLong()).session(s).contentType(MediaType.APPLICATION_JSON).content("{\"estado\":\"CANCELADA\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.estado").value("CANCELADA")).andExpect(jsonPath("$.descontado").value(false));
        assertThat(stockArabica(s)).isEqualTo(2500.0);
    }

    @Test
    @DisplayName("[HU-12][RF-18] Una transición fuera del flujo se rechaza (una exportación entregada no se cancela)")
    void transicionInvalida() throws Exception {
        MockHttpSession s = login("exportaciones@ritech.co");
        Long entregada = exportacionEn(EstadoExportacion.ENTREGADA).getId();
        mvc.perform(patch("/api/exportaciones/{id}/estado", entregada).session(s).contentType(MediaType.APPLICATION_JSON).content("{\"estado\":\"CANCELADA\"}"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value(containsString("Transición")));
    }

    @Test
    @DisplayName("QC021 [HU-11][HU-15][HU-16][RF-16][RF-21][RF-25] Flujo completo: crear, documentar, enviar, cobrar y entregar")
    void qc021() throws Exception {
        MockHttpSession exp = login("exportaciones@ritech.co"), conta = login("contador@ritech.co");
        JsonNode ex = crear(exp, "EN_PREPARACION", 100);
        long id = ex.get("id").asLong();

        mvc.perform(patch("/api/exportaciones/{id}/estado", id).session(exp).contentType(MediaType.APPLICATION_JSON).content("{\"estado\":\"EN_TRANSITO\"}"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value(containsString("Faltan documentos obligatorios")));
        for (String tipo : new String[]{"CERTIFICADO_ORIGEN", "FITOSANITARIO", "FACTURA_COMERCIAL", "DECLARACION_ADUANERA"}) {
            subirPdf(exp, id, tipo);
        }
        mvc.perform(patch("/api/exportaciones/{id}/estado", id).session(exp).contentType(MediaType.APPLICATION_JSON).content("{\"estado\":\"EN_TRANSITO\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.estado").value("EN_TRANSITO"));

        MvcResult pago = mvc.perform(post("/api/pagos").session(conta).contentType(MediaType.APPLICATION_JSON)
                .content(cuerpo("exportacionId", id, "monto", 450, "moneda", "USD", "metodo", "TRANSFERENCIA", "referencia", "TRX-1", "fechaPago", enDias(0).toString())))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.estado").value("PENDIENTE")).andReturn();
        long pagoId = leer(pago).get("id").asLong();
        mvc.perform(get("/api/pagos/saldo/{id}", id).session(conta)).andExpect(jsonPath("$.saldoPendienteUsd").value(450.0));   // sin confirmar no descuenta
        mvc.perform(patch("/api/pagos/{id}/estado", pagoId).session(conta).contentType(MediaType.APPLICATION_JSON).content("{\"estado\":\"CONFIRMADO\"}")).andExpect(status().isOk());
        mvc.perform(get("/api/pagos/saldo/{id}", id).session(conta)).andExpect(jsonPath("$.saldoPendienteUsd").value(0.0));
        mvc.perform(patch("/api/exportaciones/{id}/estado", id).session(exp).contentType(MediaType.APPLICATION_JSON).content("{\"estado\":\"ENTREGADA\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.estado").value("ENTREGADA"));
    }

    // ------------------------------------------------------------------ documentos
    @Test
    @DisplayName("QC023 [HU-14][RF-20][RF-22] Adjuntar un PDF a una exportación, listarlo y descargarlo")
    void qc023() throws Exception {
        MockHttpSession s = login("exportaciones@ritech.co");
        long id = crear(s, "EN_PREPARACION", 100).get("id").asLong();
        MvcResult r = mvc.perform(multipart("/api/exportaciones/{id}/documentos", id).file(new MockMultipartFile("archivo", "fito.pdf", "application/pdf", PDF))
                .param("tipo", "FITOSANITARIO").session(s)).andExpect(status().isCreated()).andExpect(jsonPath("$.estadoValidacion").value("PENDIENTE"))
                .andExpect(jsonPath("$.tipo").value("FITOSANITARIO")).andReturn();
        long docId = leer(r).get("id").asLong();
        mvc.perform(get("/api/exportaciones/{id}/documentos", id).session(s)).andExpect(jsonPath("$", hasSize(1)));
        mvc.perform(get("/api/documentos/{id}/archivo", docId).session(s)).andExpect(status().isOk()).andExpect(content().contentType(MediaType.APPLICATION_PDF));
    }

    @Test
    @DisplayName("[HU-14][RF-20] Un archivo que no es PDF se rechaza (400) aunque tenga extensión .pdf")
    void noPdf() throws Exception {
        MockHttpSession s = login("exportaciones@ritech.co");
        long id = crear(s, "BORRADOR", 100).get("id").asLong();
        mvc.perform(multipart("/api/exportaciones/{id}/documentos", id).file(new MockMultipartFile("archivo", "virus.exe", "application/octet-stream", "MZ".getBytes()))
                .param("tipo", "OTRO").session(s)).andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value("Solo se permiten archivos PDF"));
        mvc.perform(multipart("/api/exportaciones/{id}/documentos", id).file(new MockMultipartFile("archivo", "falso.pdf", "application/pdf", "no soy pdf".getBytes()))
                .param("tipo", "OTRO").session(s)).andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("[HU-15][RF-21] Validar y rechazar documentos: solo desde el estado pendiente")
    void validacionDocumentos() throws Exception {
        MockHttpSession s = login("exportaciones@ritech.co");
        long id = crear(s, "EN_PREPARACION", 100).get("id").asLong();
        MvcResult r = mvc.perform(multipart("/api/exportaciones/{id}/documentos", id).file(new MockMultipartFile("archivo", "f.pdf", "application/pdf", PDF)).param("tipo", "OTRO").session(s))
                .andExpect(status().isCreated()).andReturn();
        long docId = leer(r).get("id").asLong();
        mvc.perform(patch("/api/documentos/{id}/validacion", docId).session(s).contentType(MediaType.APPLICATION_JSON).content("{\"estado\":\"VALIDADO\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.estadoValidacion").value("VALIDADO"));
        mvc.perform(patch("/api/documentos/{id}/validacion", docId).session(s).contentType(MediaType.APPLICATION_JSON).content("{\"estado\":\"RECHAZADO\"}"))
                .andExpect(status().isBadRequest());
    }

    // ------------------------------------------------------------------ pagos
    @Test
    @DisplayName("QC024 [HU-16][RF-23][RR-07] Registrar un pago en USD asociado a una exportación (queda pendiente)")
    void qc024() throws Exception {
        Long id = exportacionEn(EstadoExportacion.EN_TRANSITO).getId();
        mvc.perform(post("/api/pagos").session(login("contador@ritech.co")).contentType(MediaType.APPLICATION_JSON)
                        .content(cuerpo("exportacionId", id, "monto", 5000, "moneda", "USD", "metodo", "CARTA_CREDITO", "referencia", "LC-77", "fechaPago", enDias(0).toString())))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.estado").value("PENDIENTE")).andExpect(jsonPath("$.moneda").value("USD"))
                .andExpect(jsonPath("$.monto").value(5000.0)).andExpect(jsonPath("$.metodo").value("CARTA_CREDITO"));
    }

    @Test
    @DisplayName("[HU-16][RR-07] Una moneda no soportada (COP) o un monto cero se rechazan; EUR se acepta")
    void monedas() throws Exception {
        MockHttpSession s = login("contador@ritech.co");
        Long id = exportacionEn(EstadoExportacion.EN_TRANSITO).getId();
        mvc.perform(post("/api/pagos").session(s).contentType(MediaType.APPLICATION_JSON).content(cuerpo("exportacionId", id, "monto", 100, "moneda", "COP", "fechaPago", enDias(0).toString())))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value("Moneda no soportada: solo USD o EUR"));
        mvc.perform(post("/api/pagos").session(s).contentType(MediaType.APPLICATION_JSON).content(cuerpo("exportacionId", id, "monto", 0, "moneda", "USD", "fechaPago", enDias(0).toString())))
                .andExpect(status().isBadRequest());
        mvc.perform(post("/api/pagos").session(s).contentType(MediaType.APPLICATION_JSON).content(cuerpo("exportacionId", id, "monto", 1000, "moneda", "EUR", "fechaPago", enDias(0).toString())))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.moneda").value("EUR"));
    }

    @Test
    @DisplayName("[HU-17][RF-25] Un pago solo se confirma o rechaza una vez")
    void resolverUnaVez() throws Exception {
        MockHttpSession s = login("contador@ritech.co");
        Long id = exportacionEn(EstadoExportacion.EN_TRANSITO).getId();
        long pagoId = leer(mvc.perform(post("/api/pagos").session(s).contentType(MediaType.APPLICATION_JSON)
                .content(cuerpo("exportacionId", id, "monto", 10, "moneda", "USD", "fechaPago", enDias(0).toString()))).andReturn()).get("id").asLong();
        mvc.perform(patch("/api/pagos/{id}/estado", pagoId).session(s).contentType(MediaType.APPLICATION_JSON).content("{\"estado\":\"RECHAZADO\"}")).andExpect(status().isOk());
        mvc.perform(patch("/api/pagos/{id}/estado", pagoId).session(s).contentType(MediaType.APPLICATION_JSON).content("{\"estado\":\"CONFIRMADO\"}")).andExpect(status().isBadRequest());
    }
}
'''

F["ReporteDashboardSnapshotIT.java"] = r'''package co.ritech.coffeeexport.integracion;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpSession;

class ReporteDashboardSnapshotIT extends IntegracionBase {

    @Test
    @DisplayName("QC025 [HU-18][RF-26] Generar un reporte por rango de fechas con KPI, distribución y detalle")
    void qc025() throws Exception {
        mvc.perform(get("/api/reportes").param("desde", enDias(-120).toString()).param("hasta", enDias(30).toString()).session(login("gerente@ritech.co")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.titulo").value("Detalle de exportaciones")).andExpect(jsonPath("$.totalExportaciones", greaterThan(0)))
                .andExpect(jsonPath("$.ventasUsd", greaterThan(0.0))).andExpect(jsonPath("$.porPais").isArray()).andExpect(jsonPath("$.productosTop").isArray())
                .andExpect(jsonPath("$.cabeceras", hasSize(7))).andExpect(jsonPath("$.filas").isArray());
        mvc.perform(get("/api/reportes").param("desde", enDias(-120).toString()).param("hasta", enDias(30).toString()).param("tipo", "ventas").session(admin()))
                .andExpect(jsonPath("$.titulo").value("Ventas por producto y país")).andExpect(jsonPath("$.cabeceras", hasSize(5)));
        mvc.perform(get("/api/reportes").param("desde", enDias(-1).toString()).param("hasta", enDias(0).toString()).param("tipo", "existencias").session(admin()))
                .andExpect(jsonPath("$.filas", hasSize(7)));
    }

    @Test
    @DisplayName("[HU-18][RF-26] Un rango con fecha final anterior a la inicial responde 400 con el mensaje de la regla")
    void rangoInvalido() throws Exception {
        mvc.perform(get("/api/reportes").param("desde", "2026-10-30").param("hasta", "2026-10-01").session(admin()))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").value("La fecha final no puede ser anterior a la fecha inicial"));
        mvc.perform(get("/api/reportes").param("desde", "2026-10-01").param("hasta", "2026-10-30").param("tipo", "secreto").session(admin()))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("QC026 [HU-20][HU-21][RF-29][RF-30][RF-31] Consultar los KPI del dashboard por la API")
    void qc026() throws Exception {
        mvc.perform(get("/api/dashboard/kpis").session(login("gerente@ritech.co"))).andExpect(status().isOk())
                .andExpect(jsonPath("$.totalExportaciones").value(12)).andExpect(jsonPath("$.clientesActivos").value(7)).andExpect(jsonPath("$.clientesRegistrados").value(8))
                .andExpect(jsonPath("$.inventarioKg").value(12450.0)).andExpect(jsonPath("$.ventasMesUsd").exists())
                .andExpect(jsonPath("$.exportacionesPorPais").isArray()).andExpect(jsonPath("$.productosMasVendidos", hasSize(lessThanOrEqualTo(4))))
                .andExpect(jsonPath("$.ultimasExportaciones", hasSize(5)));
    }

    @Test
    @DisplayName("[HU-06][RF-04][RR-05] La instantánea del frontend incluye solo lo que el rol puede leer y minimiza datos personales")
    void instantanea() throws Exception {
        JsonNode admin = leer(mvc.perform(get("/api/snapshot").session(admin())).andExpect(status().isOk()).andReturn());
        assertThat(admin.get("clientes").get(0).has("nif")).isTrue();
        assertThat(admin.get("usuarios")).hasSize(5);
        assertThat(admin.get("usuarios").toString()).doesNotContain("passwordHash").doesNotContain("password");

        JsonNode contador = leer(mvc.perform(get("/api/snapshot").session(login("contador@ritech.co"))).andReturn());
        assertThat(contador.get("clientes").get(0).has("nif")).as("el contador no ve datos personales del cliente").isFalse();
        assertThat(contador.get("clientes").get(0).has("nombre")).isTrue();
        assertThat(contador.get("pagos")).isNotEmpty();
        assertThat(contador.get("usuarios")).isEmpty();
        assertThat(contador.get("movimientos")).isEmpty();

        JsonNode bodega = leer(mvc.perform(get("/api/snapshot").session(login("bodega@ritech.co"))).andReturn());
        assertThat(bodega.get("exportaciones")).isEmpty();
        assertThat(bodega.get("pagos")).isEmpty();
        assertThat(bodega.get("inventario")).isNotEmpty();
    }

    @Test
    @DisplayName("[HU-05][RF-03][RNF-01] El administrador crea usuarios sin exponer el hash; solo él puede hacerlo")
    void usuarios() throws Exception {
        MockHttpSession a = admin();
        mvc.perform(post("/api/usuarios").session(a).contentType(MediaType.APPLICATION_JSON).content(cuerpo(
                "nombre", "Nuevo", "email", "nuevo@ritech.co", "password", "Clave2026*", "rol", "CONTADOR", "activo", true)))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.rol").value("CONTADOR")).andExpect(jsonPath("$.passwordHash").doesNotExist());
        mvc.perform(post("/api/usuarios").session(a).contentType(MediaType.APPLICATION_JSON).content(cuerpo(
                "nombre", "Dup", "email", "NUEVO@ritech.co", "password", "Clave2026*", "rol", "CONTADOR"))).andExpect(status().isBadRequest());
        mvc.perform(post("/api/usuarios").session(a).contentType(MediaType.APPLICATION_JSON).content(cuerpo(
                "nombre", "Corta", "email", "corta@ritech.co", "password", "123", "rol", "CONTADOR"))).andExpect(status().isBadRequest());
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON).content(cuerpo("email", "nuevo@ritech.co", "password", "Clave2026*")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.rol").value("CONTADOR"));   // su contraseña quedó guardada con BCrypt
    }
}
'''

for ruta, contenido in F.items():
    destino = os.path.normpath(os.path.join(BASE, ruta))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    open(destino, "w", encoding="utf-8", newline="\n").write(contenido)
print(len(F), "archivos")
