package co.ritech.coffeeexport.integracion;

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
