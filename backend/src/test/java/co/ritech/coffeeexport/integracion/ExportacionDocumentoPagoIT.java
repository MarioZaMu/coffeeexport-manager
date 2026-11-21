package co.ritech.coffeeexport.integracion;

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
