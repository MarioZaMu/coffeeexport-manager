package co.ritech.coffeeexport.integracion;

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
