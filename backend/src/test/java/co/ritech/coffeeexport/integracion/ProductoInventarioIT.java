package co.ritech.coffeeexport.integracion;

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
