package co.ritech.coffeeexport.repositorio;

import static org.assertj.core.api.Assertions.assertThat;

import co.ritech.coffeeexport.clientes.Cliente;
import co.ritech.coffeeexport.clientes.ClienteRepository;
import co.ritech.coffeeexport.inventario.Bodega;
import co.ritech.coffeeexport.inventario.Inventario;
import co.ritech.coffeeexport.inventario.InventarioRepository;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.ProductoRepository;
import co.ritech.coffeeexport.productos.TipoProducto;
import java.math.BigDecimal;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.test.context.ActiveProfiles;

/** Repositorios contra una base H2 real: consultas derivadas y consultas JPQL parametrizadas. */
@DataJpaTest
@ActiveProfiles("h2")   // fija H2 aunque se ejecute la suite con el perfil mysql
class RepositoriosTest {
    @Autowired TestEntityManager em;
    @Autowired ClienteRepository clientes;
    @Autowired ProductoRepository productos;
    @Autowired InventarioRepository inventarios;

    private Cliente cliente(String nombre, String pais, String nif, boolean activo) {
        Cliente c = new Cliente();
        c.setNombre(nombre);
        c.setPais(pais);
        c.setIdentificacionFiscal(nif);
        c.setContactoNombre("Contacto");
        c.setContactoEmail(nombre.replace(" ", "").toLowerCase() + "@cliente.eu");
        c.setConsentimientoDatos(true);
        c.setActivo(activo);
        return em.persist(c);
    }

    private Producto producto(String codigo, TipoProducto tipo) {
        Producto p = new Producto();
        p.setCodigo(codigo);
        p.setNombre("Producto " + codigo);
        p.setTipo(tipo);
        p.setPrecioUsdKg(new BigDecimal("4.50"));
        return em.persist(p);
    }

    @Test
    @DisplayName("QA008 [HU-02][RF-07] Consultar clientes filtrando por país")
    void qa008() {
        cliente("Kaffee GmbH", "DE", "DE1", true);
        cliente("France Agro", "FR", "FR1", true);
        cliente("Paris Cafe", "FR", "FR2", true);
        assertThat(clientes.findByPais("FR")).extracting(Cliente::getNombre).containsExactlyInAnyOrder("France Agro", "Paris Cafe");
        assertThat(clientes.findByPais("DE")).hasSize(1);
        assertThat(clientes.findByPais("IT")).isEmpty();
    }

    @Test
    @DisplayName("QA011 [HU-03][RF-10] Listar el catálogo filtrando por tipo")
    void qa011() {
        producto("CAF-1", TipoProducto.CAFE);
        producto("CAC-1", TipoProducto.CACAO);
        producto("CAC-2", TipoProducto.CACAO);
        assertThat(productos.findByTipo(TipoProducto.CACAO)).extracting(Producto::getCodigo).containsExactlyInAnyOrder("CAC-1", "CAC-2");
    }

    @Test
    @DisplayName("QA015 [HU-04][RF-12] Buscar inventario por producto y bodega")
    void qa015() {
        Producto p = producto("CAF-1", TipoProducto.CAFE);
        Bodega b1 = em.persist(new Bodega("Bodega 1", "Cartagena")), b2 = em.persist(new Bodega("Bodega 2", "Bogotá"));
        Inventario i = new Inventario();
        i.setProducto(p);
        i.setBodega(b1);
        i.setCantidadKg(new BigDecimal("100"));
        em.persist(i);
        assertThat(inventarios.findByProductoIdAndBodegaId(p.getId(), b1.getId())).isPresent();
        assertThat(inventarios.findByProductoIdAndBodegaId(p.getId(), b1.getId()).orElseThrow().getCantidadKg()).isEqualByComparingTo("100");
        assertThat(inventarios.findByProductoIdAndBodegaId(p.getId(), b2.getId())).isEmpty();
    }

    @Test
    @DisplayName("[HU-02][RNF-04] La búsqueda de clientes está parametrizada: una cadena de inyección SQL no devuelve ni borra nada")
    void busquedaParametrizada() {
        cliente("Kaffee GmbH", "DE", "DE1", true);
        em.flush();
        assertThat(clientes.buscar("'; DROP TABLE clientes; --", null, null)).isEmpty();
        assertThat(clientes.buscar("' OR '1'='1", null, null)).isEmpty();
        assertThat(clientes.count()).isEqualTo(1);
        assertThat(clientes.buscar("kaffee", null, true)).hasSize(1);
        assertThat(clientes.buscar(null, "DE", null)).hasSize(1);
        assertThat(clientes.buscar(null, null, false)).isEmpty();
    }

    @Test
    @DisplayName("[HU-04][RF-12] Un producto no puede repetirse en la misma bodega (restricción única)")
    void unicoPorBodega() {
        Producto p = producto("CAF-9", TipoProducto.CAFE);
        Bodega b = em.persist(new Bodega("Bodega U", "X"));
        Inventario primero = new Inventario();
        primero.setProducto(p);
        primero.setBodega(b);
        em.persistAndFlush(primero);
        Inventario repetido = new Inventario();
        repetido.setProducto(p);
        repetido.setBodega(b);
        org.junit.jupiter.api.Assertions.assertThrows(Exception.class, () -> em.persistAndFlush(repetido));
    }
}
