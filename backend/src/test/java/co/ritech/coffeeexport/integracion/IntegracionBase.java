package co.ritech.coffeeexport.integracion;

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
