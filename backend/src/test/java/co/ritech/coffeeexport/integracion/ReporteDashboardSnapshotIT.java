package co.ritech.coffeeexport.integracion;

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
