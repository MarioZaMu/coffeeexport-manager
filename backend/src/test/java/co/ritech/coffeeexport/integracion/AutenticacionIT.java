package co.ritech.coffeeexport.integracion;

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
