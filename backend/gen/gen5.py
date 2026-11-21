# -*- coding: utf-8 -*-
"""Pruebas del backend, parte 1: apoyo, unitarias (Mockito) y de repositorio (@DataJpaTest)."""
import os
AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(AQUI, "..", "src", "test", "java", "co", "ritech", "coffeeexport")
F = {}

F["Fixtures.java"] = r'''package co.ritech.coffeeexport;

import co.ritech.coffeeexport.clientes.Cliente;
import co.ritech.coffeeexport.exportaciones.DetalleExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.inventario.Bodega;
import co.ritech.coffeeexport.inventario.Inventario;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.TipoProducto;
import co.ritech.coffeeexport.usuarios.Rol;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.time.LocalDate;

/** Constructores de datos de prueba compartidos por las pruebas unitarias. */
public final class Fixtures {
    private Fixtures() {
    }

    public static Usuario usuario(Long id, String email, String hash, String rol, boolean activo) {
        Usuario u = new Usuario();
        u.setId(id);
        u.setNombre("Usuario " + id);
        u.setEmail(email);
        u.setPasswordHash(hash);
        u.setRol(new Rol(rol, rol));
        u.setActivo(activo);
        return u;
    }

    public static Cliente cliente(Long id, String pais, boolean activo) {
        Cliente c = new Cliente();
        c.setId(id);
        c.setNombre("Cliente " + id);
        c.setPais(pais);
        c.setIdentificacionFiscal("NIF-" + id);
        c.setContactoNombre("Contacto");
        c.setContactoEmail("c" + id + "@cliente.eu");
        c.setConsentimientoDatos(true);
        c.setActivo(activo);
        return c;
    }

    public static Producto producto(Long id, String nombre, String precio) {
        Producto p = new Producto();
        p.setId(id);
        p.setCodigo("P-" + id);
        p.setNombre(nombre);
        p.setTipo(TipoProducto.CAFE);
        p.setPrecioUsdKg(new BigDecimal(precio));
        return p;
    }

    public static Bodega bodega(Long id, String nombre) {
        Bodega b = new Bodega(nombre, "Ciudad");
        b.setId(id);
        return b;
    }

    public static Inventario inventario(Long id, Producto p, Bodega b, String kg) {
        Inventario i = new Inventario();
        i.setId(id);
        i.setProducto(p);
        i.setBodega(b);
        i.setCantidadKg(new BigDecimal(kg));
        return i;
    }

    public static Exportacion exportacion(Long id, Cliente c, Usuario creador, LocalDate fecha) {
        Exportacion e = new Exportacion();
        e.setId(id);
        e.setCodigo("EXP-2026-" + String.format("%04d", id));
        e.setCliente(c);
        e.setPaisDestino(c.getPais());
        e.setPuertoSalida("Cartagena");
        e.setPuertoLlegada("Róterdam");
        e.setFechaEnvio(fecha);
        e.setUsuarioCreador(creador);
        return e;
    }

    public static DetalleExportacion detalle(Producto p, String kg, String precio) {
        DetalleExportacion d = new DetalleExportacion();
        d.setProducto(p);
        d.setCantidadKg(new BigDecimal(kg));
        d.setPrecioUnitario(new BigDecimal(precio));
        return d;
    }
}
'''

# ================================================================= unitarias
F["unit/AuthServiceTest.java"] = r'''package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import co.ritech.coffeeexport.Fixtures;
import co.ritech.coffeeexport.auth.AuthService;
import co.ritech.coffeeexport.usuarios.Usuario;
import co.ritech.coffeeexport.usuarios.UsuarioRepository;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {
    @Mock UsuarioRepository usuarios;
    final PasswordEncoder encoder = new BCryptPasswordEncoder(4);
    AuthService service;

    @BeforeEach
    void preparar() {
        service = new AuthService(usuarios, encoder);
    }

    @Test
    @DisplayName("QA001 [HU-01][RF-01] Autenticar a un usuario activo con credenciales válidas")
    void qa001() {
        Usuario u = Fixtures.usuario(1L, "admin@ritech.co", encoder.encode("Demo2026*"), "ADMIN", true);
        when(usuarios.findByEmailIgnoreCase("admin@ritech.co")).thenReturn(Optional.of(u));
        Usuario r = service.autenticar("admin@ritech.co", "Demo2026*");
        assertThat(r.getRol().getNombre()).isEqualTo("ADMIN");
        assertThat(r.getUltimoAcceso()).isNotNull();
    }

    @Test
    @DisplayName("QA003 [HU-01][RF-01] Rechazar la autenticación con contraseña incorrecta")
    void qa003() {
        Usuario u = Fixtures.usuario(1L, "admin@ritech.co", encoder.encode("Demo2026*"), "ADMIN", true);
        when(usuarios.findByEmailIgnoreCase("admin@ritech.co")).thenReturn(Optional.of(u));
        assertThatThrownBy(() -> service.autenticar("admin@ritech.co", "incorrecta"))
                .isInstanceOf(BadCredentialsException.class).hasMessage("Credenciales incorrectas");
        assertThat(u.getUltimoAcceso()).isNull();
    }

    @Test
    @DisplayName("QA004 [HU-01][RF-01] Rechazar la autenticación de un usuario inactivo")
    void qa004() {
        Usuario u = Fixtures.usuario(2L, "baja@ritech.co", encoder.encode("Demo2026*"), "OP_BODEGA", false);
        when(usuarios.findByEmailIgnoreCase("baja@ritech.co")).thenReturn(Optional.of(u));
        assertThatThrownBy(() -> service.autenticar("baja@ritech.co", "Demo2026*")).isInstanceOf(DisabledException.class);
        assertThat(u.getUltimoAcceso()).isNull();
    }

    @Test
    @DisplayName("[HU-01][RNF-04] Un correo inexistente da el mismo mensaje genérico que una contraseña mala")
    void correoInexistente() {
        when(usuarios.findByEmailIgnoreCase("nadie@ritech.co")).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.autenticar("nadie@ritech.co", "x")).isInstanceOf(BadCredentialsException.class).hasMessage("Credenciales incorrectas");
    }
}
'''
F["unit/UsuarioServiceTest.java"] = r'''package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.*;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class UsuarioServiceTest {
    @Mock UsuarioRepository usuarios;
    @Mock RolRepository roles;
    final PasswordEncoder encoder = new BCryptPasswordEncoder(4);
    UsuarioService service;

    @BeforeEach
    void preparar() {
        service = new UsuarioService(usuarios, roles, encoder);
    }

    @Test
    @DisplayName("QA002 [HU-01][RNF-01] La contraseña se guarda cifrada con BCrypt y no en texto plano")
    void qa002() {
        when(usuarios.existsByEmailIgnoreCase("ana@ritech.co")).thenReturn(false);
        when(roles.findByNombre("OP_BODEGA")).thenReturn(Optional.of(new Rol("OP_BODEGA", "Bodega")));
        when(usuarios.save(any(Usuario.class))).thenAnswer(i -> i.getArgument(0));

        service.crearUsuario(new UsuarioRequest("Ana", "ana@ritech.co", "Cafe2026*", "OP_BODEGA", true));

        ArgumentCaptor<Usuario> guardado = ArgumentCaptor.forClass(Usuario.class);
        verify(usuarios).save(guardado.capture());
        String hash = guardado.getValue().getPasswordHash();
        assertThat(hash).isNotEqualTo("Cafe2026*").matches("^\\$2[aby]\\$.{56}$");
        assertThat(encoder.matches("Cafe2026*", hash)).isTrue();
    }

    @Test
    @DisplayName("[HU-05][RF-03] No se crean usuarios con correo repetido ni contraseña corta")
    void validaciones() {
        when(usuarios.existsByEmailIgnoreCase("repetido@ritech.co")).thenReturn(true);
        assertThatThrownBy(() -> service.crearUsuario(new UsuarioRequest("X", "repetido@ritech.co", "Cafe2026*", "ADMIN", true)))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("Ya existe un usuario con ese correo");
        assertThatThrownBy(() -> service.crearUsuario(new UsuarioRequest("X", "nuevo@ritech.co", "corta", "ADMIN", true)))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("al menos 8 caracteres");
        verify(usuarios, never()).save(any());
    }

    @Test
    @DisplayName("[HU-05][RF-03] Un administrador no puede desactivarse a sí mismo")
    void noAutoDesactivar() {
        Usuario admin = new Usuario();
        admin.setId(1L);
        admin.setRol(new Rol("ADMIN", "x"));
        when(usuarios.findById(1L)).thenReturn(Optional.of(admin));
        when(usuarios.findByEmailIgnoreCase("admin@ritech.co")).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.actualizarUsuario(1L, new UsuarioRequest("Admin", "admin@ritech.co", null, "ADMIN", false), 1L))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("a sí mismo");
    }
}
'''
F["unit/ClienteServiceTest.java"] = r'''package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.clientes.*;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ClienteServiceTest {
    @Mock ClienteRepository repo;
    ClienteService service;

    @BeforeEach
    void preparar() {
        service = new ClienteService(repo);
    }

    static ClienteRequest peticion(String pais, String nif, Boolean consentimiento) {
        return new ClienteRequest("Kaffeehaus GmbH", pais, nif, "Hans Becker", "hans@kaffeehaus.de", "+49 30 1", "Berlín", consentimiento);
    }

    @Test
    @DisplayName("QA005 [HU-02][RF-05] Registrar un cliente válido de la UE")
    void qa005() {
        when(repo.existsByIdentificacionFiscalIgnoreCase("DE811234567")).thenReturn(false);
        when(repo.save(any(Cliente.class))).thenAnswer(i -> {
            Cliente c = i.getArgument(0);
            c.setId(10L);
            return c;
        });
        Cliente c = service.registrarCliente(peticion("DE", "DE811234567", true));
        verify(repo, times(1)).save(any(Cliente.class));
        assertThat(c.getId()).isEqualTo(10L);
        assertThat(c.isActivo()).isTrue();
        assertThat(c.getFechaConsentimiento()).isNotNull();
    }

    @Test
    @DisplayName("QA006 [HU-02][RF-05] Rechazar un cliente con identificación fiscal duplicada")
    void qa006() {
        when(repo.existsByIdentificacionFiscalIgnoreCase("DE811234567")).thenReturn(true);
        assertThatThrownBy(() -> service.registrarCliente(peticion("DE", "DE811234567", true)))
                .isInstanceOf(ClienteDuplicadoException.class).hasMessageContaining("identificación fiscal");
        verify(repo, never()).save(any());
    }

    @Test
    @DisplayName("QA007 [HU-02][RF-05] Rechazar un cliente cuyo país no pertenece a la UE")
    void qa007() {
        assertThatThrownBy(() -> service.registrarCliente(peticion("US", "US123", true)))
                .isInstanceOf(IllegalArgumentException.class).isInstanceOf(ReglaNegocioException.class)
                .hasMessageContaining("Unión Europea");
        verify(repo, never()).save(any());
    }

    @Test
    @DisplayName("[HU-02][RF-08][RR-05] Sin consentimiento GDPR no se registra el cliente")
    void sinConsentimiento() {
        assertThatThrownBy(() -> service.registrarCliente(peticion("FR", "FR1", false)))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("consentimiento");
        assertThatThrownBy(() -> service.registrarCliente(peticion("FR", "FR1", null))).isInstanceOf(ReglaNegocioException.class);
        verify(repo, never()).save(any());
    }

    @Test
    @DisplayName("[HU-02][RF-06] Desactivar un cliente conserva el registro (baja lógica)")
    void bajaLogica() {
        Cliente c = new Cliente();
        c.setId(5L);
        c.setActivo(true);
        when(repo.findById(5L)).thenReturn(Optional.of(c));
        when(repo.save(any(Cliente.class))).thenAnswer(i -> i.getArgument(0));
        assertThat(service.cambiarEstado(5L, false).isActivo()).isFalse();
        verify(repo, never()).delete(any());
        verify(repo, never()).deleteById(any());
    }

    @Test
    @DisplayName("[HU-02][RF-05] Al actualizar, el NIF solo choca con OTRO cliente")
    void actualizarMismoNif() {
        Cliente actual = Fixtures_clienteConId(7L);
        when(repo.findById(7L)).thenReturn(Optional.of(actual));
        when(repo.findByIdentificacionFiscalIgnoreCase("DE811234567")).thenReturn(Optional.of(actual));
        when(repo.save(any(Cliente.class))).thenAnswer(i -> i.getArgument(0));
        assertThat(service.actualizarCliente(7L, peticion("DE", "DE811234567", true)).getNombre()).isEqualTo("Kaffeehaus GmbH");
    }

    private static Cliente Fixtures_clienteConId(Long id) {
        return co.ritech.coffeeexport.Fixtures.cliente(id, "DE", true);
    }
}
'''
F["unit/ProductoServiceTest.java"] = r'''package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.productos.*;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.math.BigDecimal;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ProductoServiceTest {
    @Mock ProductoRepository repo;
    ProductoService service;

    @BeforeEach
    void preparar() {
        service = new ProductoService(repo);
    }

    @Test
    @DisplayName("QA009 [HU-03][RF-09] Registrar un producto de café válido")
    void qa009() {
        when(repo.existsByCodigoIgnoreCase("CAF-CAS-01")).thenReturn(false);
        when(repo.save(any(Producto.class))).thenAnswer(i -> {
            Producto p = i.getArgument(0);
            p.setId(3L);
            return p;
        });
        Producto p = service.crearProducto(new ProductoRequest("CAF-CAS-01", "Café Castillo", "CAFE", "Castillo", new BigDecimal("4.5")));
        assertThat(p.getId()).isEqualTo(3L);
        assertThat(p.isActivo()).isTrue();
        assertThat(p.getTipo()).isEqualTo(TipoProducto.CAFE);
        assertThat(p.getPrecioUsdKg()).isEqualByComparingTo("4.50");
    }

    @Test
    @DisplayName("QA010 [HU-03][RF-09] Rechazar un producto con precio negativo o cero")
    void qa010() {
        assertThatThrownBy(() -> service.crearProducto(new ProductoRequest("X-1", "Malo", "CAFE", null, new BigDecimal("-5.00"))))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("precio debe ser mayor que cero");
        assertThatThrownBy(() -> service.crearProducto(new ProductoRequest("X-2", "Cero", "CAFE", null, BigDecimal.ZERO)))
                .isInstanceOf(ReglaNegocioException.class);
        verify(repo, never()).save(any());
    }

    @Test
    @DisplayName("[HU-03][RF-09] Tipo de producto inválido y código repetido se rechazan")
    void tipoYCodigo() {
        assertThatThrownBy(() -> service.crearProducto(new ProductoRequest("X-3", "Té", "TE", null, BigDecimal.ONE)))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("CAFE o CACAO");
        when(repo.existsByCodigoIgnoreCase("DUP-1")).thenReturn(true);
        assertThatThrownBy(() -> service.crearProducto(new ProductoRequest("DUP-1", "Dup", "CACAO", null, BigDecimal.ONE)))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("código");
    }
}
'''
F["unit/InventarioServiceTest.java"] = r'''package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.Fixtures;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.inventario.*;
import co.ritech.coffeeexport.inventario.InventarioDtos.StockDto;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.ProductoRepository;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.shared.StockInsuficienteException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class InventarioServiceTest {
    @Mock InventarioRepository inventarios;
    @Mock MovimientoInventarioRepository movimientos;
    @Mock ProductoRepository productos;
    @Mock BodegaRepository bodegas;
    InventarioService service;
    final Usuario usuario = Fixtures.usuario(1L, "bodega@ritech.co", "x", "OP_BODEGA", true);
    final Producto cafe = Fixtures.producto(1L, "Café Arábica", "4.50");
    final Bodega b1 = Fixtures.bodega(1L, "Bodega Cartagena"), b2 = Fixtures.bodega(2L, "Bodega Bogotá");

    @BeforeEach
    void preparar() {
        service = new InventarioService(inventarios, movimientos, productos, bodegas);
    }

    @Test
    @DisplayName("QA012 [HU-04][RF-12] Consultar el stock total de un producto sumando sus bodegas")
    void qa012() {
        when(inventarios.findByProductoId(1L)).thenReturn(List.of(Fixtures.inventario(1L, cafe, b1, "100"), Fixtures.inventario(2L, cafe, b2, "50")));
        StockDto s = service.consultarStock(1L);
        assertThat(s.totalKg()).isEqualByComparingTo("150");
        assertThat(s.bodegas()).hasSize(2);
    }

    @Test
    @DisplayName("QA013 [HU-04][RF-13] Registrar una entrada de inventario")
    void qa013() {
        Inventario inv = Fixtures.inventario(1L, cafe, b1, "100");
        when(inventarios.findByProductoIdAndBodegaId(1L, 1L)).thenReturn(Optional.of(inv));
        when(movimientos.save(any(MovimientoInventario.class))).thenAnswer(i -> i.getArgument(0));

        service.registrarEntrada(1L, 1L, new BigDecimal("50"), "Compra", usuario);

        assertThat(inv.getCantidadKg()).isEqualByComparingTo("150");
        ArgumentCaptor<MovimientoInventario> m = ArgumentCaptor.forClass(MovimientoInventario.class);
        verify(movimientos).save(m.capture());
        assertThat(m.getValue().getTipo()).isEqualTo(TipoMovimiento.ENTRADA);
        assertThat(m.getValue().getCantidadKg()).isEqualByComparingTo("50");
        assertThat(m.getValue().getUsuario()).isSameAs(usuario);
    }

    @Test
    @DisplayName("QA014 [HU-04][RF-14] Rechazar una salida mayor al stock disponible")
    void qa014() {
        Inventario inv = Fixtures.inventario(1L, cafe, b1, "100");
        when(inventarios.findByProductoIdAndBodegaId(1L, 1L)).thenReturn(Optional.of(inv));
        assertThatThrownBy(() -> service.registrarSalida(1L, 1L, new BigDecimal("150"), "x", usuario))
                .isInstanceOf(StockInsuficienteException.class).hasMessage("Stock insuficiente: disponible 100 kg en esa bodega.");
        assertThat(inv.getCantidadKg()).isEqualByComparingTo("100");
        verify(movimientos, never()).save(any());
    }

    @Test
    @DisplayName("[HU-04][RF-13] Cantidades cero, negativas o nulas se rechazan en entradas y salidas")
    void cantidadesInvalidas() {
        for (BigDecimal kg : new BigDecimal[]{BigDecimal.ZERO, new BigDecimal("-5"), null}) {
            assertThatThrownBy(() -> service.registrarEntrada(1L, 1L, kg, "x", usuario)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("mayor que cero");
            assertThatThrownBy(() -> service.registrarSalida(1L, 1L, kg, "x", usuario)).isInstanceOf(ReglaNegocioException.class);
        }
        verify(movimientos, never()).save(any());
    }

    @Test
    @DisplayName("[HU-04][RF-13] Un ajuste fija el stock al valor indicado")
    void ajuste() {
        Inventario inv = Fixtures.inventario(1L, cafe, b1, "100");
        when(inventarios.findByProductoIdAndBodegaId(1L, 1L)).thenReturn(Optional.of(inv));
        when(movimientos.save(any(MovimientoInventario.class))).thenAnswer(i -> i.getArgument(0));
        service.ajustar(1L, 1L, new BigDecimal("80"), "Conteo físico", usuario);
        assertThat(inv.getCantidadKg()).isEqualByComparingTo("80");
    }

    @Test
    @DisplayName("[HU-11][RF-19] Descontar una exportación reparte entre bodegas, de la de mayor stock a la menor")
    void descuentoRepartido() {
        Inventario i1 = Fixtures.inventario(1L, cafe, b1, "1500"), i2 = Fixtures.inventario(2L, cafe, b2, "1000");
        when(inventarios.findByProductoId(1L)).thenReturn(List.of(i1, i2));
        when(movimientos.save(any(MovimientoInventario.class))).thenAnswer(i -> i.getArgument(0));
        Exportacion ex = unaExportacion("1800");

        service.descontarParaExportacion(ex, usuario);

        assertThat(i1.getCantidadKg()).isEqualByComparingTo("0");       // primero la bodega con más stock
        assertThat(i2.getCantidadKg()).isEqualByComparingTo("700");
        verify(movimientos, times(2)).save(any(MovimientoInventario.class));
    }

    @Test
    @DisplayName("[HU-11][RF-19] Con stock insuficiente el descuento falla y NO mueve nada (atómico)")
    void descuentoAtomico() {
        Inventario i1 = Fixtures.inventario(1L, cafe, b1, "1500"), i2 = Fixtures.inventario(2L, cafe, b2, "1000");
        when(inventarios.findByProductoId(1L)).thenReturn(List.of(i1, i2));
        when(productos.findById(1L)).thenReturn(Optional.of(cafe));
        Exportacion ex = unaExportacion("3000");

        assertThatThrownBy(() -> service.descontarParaExportacion(ex, usuario))
                .isInstanceOf(StockInsuficienteException.class)
                .hasMessage("Stock insuficiente de Café Arábica: solicitado 3.000 kg, disponible 2.500 kg");
        assertThat(i1.getCantidadKg()).isEqualByComparingTo("1500");
        assertThat(i2.getCantidadKg()).isEqualByComparingTo("1000");
        verify(inventarios, never()).save(any());
        verify(movimientos, never()).save(any());
    }

    private Exportacion unaExportacion(String kg) {
        Exportacion ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), usuario, LocalDate.now());
        ex.agregarDetalle(Fixtures.detalle(cafe, kg, "4.50"));
        return ex;
    }
}
'''
F["unit/ExportacionServiceTest.java"] = r'''package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.Fixtures;
import co.ritech.coffeeexport.clientes.ClienteRepository;
import co.ritech.coffeeexport.documentos.DocumentoService;
import co.ritech.coffeeexport.documentos.TipoDocumento;
import co.ritech.coffeeexport.exportaciones.*;
import co.ritech.coffeeexport.inventario.InventarioService;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.ProductoRepository;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ExportacionServiceTest {
    @Mock ExportacionRepository exportaciones;
    @Mock ClienteRepository clientes;
    @Mock ProductoRepository productos;
    @Mock InventarioService inventario;
    @Mock DocumentoService documentos;
    ExportacionService service;
    final Usuario operador = Fixtures.usuario(3L, "exportaciones@ritech.co", "x", "OP_EXPORTACIONES", true);
    final Producto arabica = Fixtures.producto(1L, "Café Arábica", "4.50"), cacao = Fixtures.producto(2L, "Cacao en grano", "8.00");
    final LocalDate manana = LocalDate.now(ZoneId.of("America/Bogota")).plusDays(1);

    @BeforeEach
    void preparar() {
        service = new ExportacionService(exportaciones, clientes, productos, inventario, documentos);
    }

    private ExportacionRequest peticion(String estadoInicial) {
        return new ExportacionRequest(1L, "DE", "Cartagena", "Hamburgo", manana, estadoInicial, null,
                List.of(new ExportacionRequest.Linea(1L, new BigDecimal("100"), new BigDecimal("4.50")),
                        new ExportacionRequest.Linea(2L, new BigDecimal("50"), new BigDecimal("8.00"))));
    }

    private void preparar2Productos() {
        when(clientes.findById(1L)).thenReturn(Optional.of(Fixtures.cliente(1L, "DE", true)));
        when(productos.findById(1L)).thenReturn(Optional.of(arabica));
        when(productos.findById(2L)).thenReturn(Optional.of(cacao));
        when(exportaciones.save(any(Exportacion.class))).thenAnswer(i -> {
            Exportacion e = i.getArgument(0);
            if (e.getId() == null) {
                e.setId(1L);
            }
            return e;
        });
    }

    @Test
    @DisplayName("QA016 [HU-11][RF-17] Crear una exportación con varios productos y calcular su total")
    void qa016() {
        preparar2Productos();
        Exportacion ex = service.crearExportacion(peticion(null), operador);
        assertThat(ex.getEstado()).isEqualTo(EstadoExportacion.BORRADOR);
        assertThat(ex.getTotalUsd()).isEqualByComparingTo("850.00");   // 100 × 4,50 + 50 × 8,00
        assertThat(ex.getDetalles()).hasSize(2);
        assertThat(ex.getCodigo()).matches("EXP-\\d{4}-0001");
        verify(inventario).validarDisponibilidad(ex);
        verify(inventario, never()).descontarParaExportacion(any(), any());
    }

    @Test
    @DisplayName("[HU-11][RF-19] Crear con estado inicial EN_PREPARACION confirma y descuenta el inventario")
    void confirmaAlCrear() {
        preparar2Productos();
        Exportacion ex = service.crearExportacion(peticion("EN_PREPARACION"), operador);
        assertThat(ex.getEstado()).isEqualTo(EstadoExportacion.EN_PREPARACION);
        assertThat(ex.isDescontado()).isTrue();
        verify(inventario).descontarParaExportacion(ex, operador);
    }

    @Test
    @DisplayName("[HU-11][RF-16] Un cliente inactivo o una fecha pasada impiden crear la exportación")
    void validacionesBasicas() {
        when(clientes.findById(1L)).thenReturn(Optional.of(Fixtures.cliente(1L, "DE", false)));
        assertThatThrownBy(() -> service.crearExportacion(peticion(null), operador)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("no está activo");
        when(clientes.findById(1L)).thenReturn(Optional.of(Fixtures.cliente(1L, "DE", true)));
        ExportacionRequest pasada = new ExportacionRequest(1L, "DE", "Cartagena", "Hamburgo", LocalDate.now().minusDays(3), null, null,
                List.of(new ExportacionRequest.Linea(1L, BigDecimal.ONE, BigDecimal.ONE)));
        assertThatThrownBy(() -> service.crearExportacion(pasada, operador)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("pasado");
        verify(exportaciones, never()).save(any());
    }

    @Test
    @DisplayName("[HU-15][RF-21] No se pasa a EN_TRANSITO si faltan documentos obligatorios")
    void tránsitoSinDocumentos() {
        Exportacion ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), operador, manana);
        ex.setEstado(EstadoExportacion.EN_PREPARACION);
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        when(documentos.faltantes(1L)).thenReturn(List.of(TipoDocumento.CERTIFICADO_ORIGEN, TipoDocumento.FITOSANITARIO));
        assertThatThrownBy(() -> service.cambiarEstado(1L, EstadoExportacion.EN_TRANSITO, operador))
                .isInstanceOf(ReglaNegocioException.class).hasMessage("Faltan documentos obligatorios: Certificado de origen, Certificado fitosanitario.");
        assertThat(ex.getEstado()).isEqualTo(EstadoExportacion.EN_PREPARACION);
    }

    @Test
    @DisplayName("[HU-12][RF-18] Solo se permiten las transiciones de estado del flujo")
    void transicionesInvalidas() {
        Exportacion ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), operador, manana);
        ex.setEstado(EstadoExportacion.ENTREGADA);
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        assertThatThrownBy(() -> service.cambiarEstado(1L, EstadoExportacion.CANCELADA, operador)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("Transición");
        assertThatThrownBy(() -> service.cambiarEstado(1L, EstadoExportacion.BORRADOR, operador)).isInstanceOf(ReglaNegocioException.class);
    }

    @Test
    @DisplayName("[HU-12][RF-19] Cancelar una exportación con inventario descontado lo devuelve")
    void cancelarDevuelveStock() {
        Exportacion ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), operador, manana);
        ex.setEstado(EstadoExportacion.EN_PREPARACION);
        ex.setDescontado(true);
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        when(exportaciones.save(any(Exportacion.class))).thenAnswer(i -> i.getArgument(0));
        Exportacion r = service.cambiarEstado(1L, EstadoExportacion.CANCELADA, operador);
        assertThat(r.getEstado()).isEqualTo(EstadoExportacion.CANCELADA);
        assertThat(r.isDescontado()).isFalse();
        verify(inventario).devolverStock(ex, operador);
    }
}
'''
F["unit/PagoServiceTest.java"] = r'''package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.Fixtures;
import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.pagos.*;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class PagoServiceTest {
    @Mock PagoRepository pagos;
    @Mock ExportacionRepository exportaciones;
    PagoService service;
    final Usuario contador = Fixtures.usuario(5L, "contador@ritech.co", "x", "CONTADOR", true);
    Exportacion ex;

    @BeforeEach
    void preparar() {
        service = new PagoService(pagos, exportaciones, new BigDecimal("1.08"));
        ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), contador, LocalDate.now());
        ex.setEstado(EstadoExportacion.EN_TRANSITO);
        ex.agregarDetalle(Fixtures.detalle(Fixtures.producto(1L, "Café", "5"), "200", "5.00"));   // total 1.000 USD
    }

    private PagoRequest peticion(String moneda, String monto) {
        return new PagoRequest(1L, monto == null ? null : new BigDecimal(monto), moneda, "TRANSFERENCIA", "TRX-1", LocalDate.now());
    }

    @Test
    @DisplayName("QA017 [HU-16][RR-07] Rechazar un pago en una moneda no soportada")
    void qa017() {
        assertThatThrownBy(() -> service.registrarPago(peticion("COP", "1000"), contador))
                .isInstanceOf(ReglaNegocioException.class).hasMessage("Moneda no soportada: solo USD o EUR");
        verify(pagos, never()).save(any());
    }

    @Test
    @DisplayName("[HU-16][RF-23] Un pago válido en USD queda PENDIENTE; un monto cero se rechaza")
    void pagoValido() {
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        when(pagos.save(any(Pago.class))).thenAnswer(i -> i.getArgument(0));
        Pago p = service.registrarPago(peticion("usd", "5000"), contador);
        assertThat(p.getEstado()).isEqualTo(EstadoPago.PENDIENTE);
        assertThat(p.getMoneda()).isEqualTo(Moneda.USD);
        assertThat(p.getMonto()).isEqualByComparingTo("5000.00");
        assertThatThrownBy(() -> service.registrarPago(peticion("USD", "0"), contador)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("mayor que cero");
    }

    @Test
    @DisplayName("[HU-16][RF-23] No se registran pagos de una exportación en borrador")
    void soloConfirmadas() {
        ex.setEstado(EstadoExportacion.BORRADOR);
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        assertThatThrownBy(() -> service.registrarPago(peticion("USD", "10"), contador)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("confirmadas");
    }

    @Test
    @DisplayName("[HU-17][RF-24][RF-25] El saldo descuenta solo pagos confirmados y convierte EUR con la tasa")
    void saldo() {
        Pago confirmado = pago(EstadoPago.CONFIRMADO, Moneda.EUR, "500");     // 500 EUR × 1,08 = 540 USD
        Pago pendiente = pago(EstadoPago.PENDIENTE, Moneda.USD, "300");       // no cuenta
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        when(pagos.findByExportacionId(1L)).thenReturn(List.of(confirmado, pendiente));
        assertThat(service.saldoPendiente(1L)).isEqualByComparingTo("460.00");
    }

    @Test
    @DisplayName("[HU-17][RF-25] Solo se confirman o rechazan pagos pendientes")
    void confirmarSoloPendientes() {
        Pago p = pago(EstadoPago.PENDIENTE, Moneda.USD, "100");
        when(pagos.findById(9L)).thenReturn(Optional.of(p));
        when(pagos.save(any(Pago.class))).thenAnswer(i -> i.getArgument(0));
        assertThat(service.confirmar(9L).getEstado()).isEqualTo(EstadoPago.CONFIRMADO);
        assertThatThrownBy(() -> service.rechazar(9L)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("pendientes");
    }

    private Pago pago(EstadoPago estado, Moneda moneda, String monto) {
        Pago p = new Pago();
        p.setExportacion(ex);
        p.setEstado(estado);
        p.setMoneda(moneda);
        p.setMonto(new BigDecimal(monto));
        return p;
    }
}
'''
F["unit/ReporteServiceTest.java"] = r'''package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyCollection;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.inventario.InventarioRepository;
import co.ritech.coffeeexport.reportes.ReporteDto;
import co.ritech.coffeeexport.reportes.ReporteService;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ReporteServiceTest {
    @Mock ExportacionRepository exportaciones;
    @Mock InventarioRepository inventario;
    ReporteService service;

    @BeforeEach
    void preparar() {
        service = new ReporteService(exportaciones, inventario);
    }

    @Test
    @DisplayName("QA018 [HU-18][RF-26] Rechazar un reporte cuya fecha final es anterior a la inicial")
    void qa018() {
        assertThatThrownBy(() -> service.generarReporte(LocalDate.of(2026, 9, 30), LocalDate.of(2026, 9, 1), "exportaciones"))
                .isInstanceOf(IllegalArgumentException.class).hasMessage("La fecha final no puede ser anterior a la fecha inicial");
        verifyNoInteractions(exportaciones);
    }

    @Test
    @DisplayName("[HU-18][RF-26] Un rango sin exportaciones devuelve un reporte vacío con ceros")
    void rangoVacio() {
        when(exportaciones.enRango(any(), any(), anyCollection())).thenReturn(List.of());
        ReporteDto r = service.generarReporte(LocalDate.of(2026, 1, 1), LocalDate.of(2026, 1, 31), null);
        assertThat(r.totalExportaciones()).isZero();
        assertThat(r.ventasUsd()).isEqualByComparingTo("0");
        assertThat(r.filas()).isEmpty();
        assertThat(r.tipo()).isEqualTo("exportaciones");
    }

    @Test
    @DisplayName("[HU-18][RF-26] Fechas ausentes o tipo de reporte inválido se rechazan")
    void parametrosInvalidos() {
        assertThatThrownBy(() -> service.generarReporte(null, LocalDate.now(), "ventas")).hasMessageContaining("rango de fechas");
        assertThatThrownBy(() -> service.generarReporte(LocalDate.now(), LocalDate.now(), "otro")).hasMessageContaining("Tipo de reporte no válido");
    }
}
'''
F["unit/DocumentoServiceTest.java"] = r'''package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.Fixtures;
import co.ritech.coffeeexport.documentos.*;
import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;

@ExtendWith(MockitoExtension.class)
class DocumentoServiceTest {
    @Mock DocumentoRepository documentos;
    @Mock ExportacionRepository exportaciones;
    @TempDir Path carpeta;
    DocumentoService service;
    final Usuario operador = Fixtures.usuario(3L, "exportaciones@ritech.co", "x", "OP_EXPORTACIONES", true);
    Exportacion ex;

    @BeforeEach
    void preparar() {
        service = new DocumentoService(documentos, exportaciones, carpeta.toString());
        ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), operador, LocalDate.now().plusDays(3));
        ex.setEstado(EstadoExportacion.EN_PREPARACION);
        lenient().when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
    }

    private static MockMultipartFile pdf(String nombre, String mime, byte[] contenido) {
        return new MockMultipartFile("archivo", nombre, mime, contenido);
    }

    @Test
    @DisplayName("[HU-14][RF-20] Un PDF válido se guarda y queda PENDIENTE de validación")
    void pdfValido() throws Exception {
        when(documentos.save(any(Documento.class))).thenAnswer(i -> i.getArgument(0));
        Documento d = service.subir(1L, "fitosanitario", pdf("fito.pdf", "application/pdf", "%PDF-1.4 contenido".getBytes()), operador);
        assertThat(d.getTipo()).isEqualTo(TipoDocumento.FITOSANITARIO);
        assertThat(d.getEstadoValidacion()).isEqualTo(EstadoValidacion.PENDIENTE);
        assertThat(Files.exists(Path.of(d.getRutaArchivo()))).isTrue();
    }

    @Test
    @DisplayName("[HU-14][RF-20] Se rechazan archivos que no son PDF, aunque cambien la extensión")
    void noPdf() {
        assertThatThrownBy(() -> service.subir(1L, "OTRO", pdf("virus.exe", "application/octet-stream", "MZ".getBytes()), operador))
                .isInstanceOf(ReglaNegocioException.class).hasMessage("Solo se permiten archivos PDF");
        assertThatThrownBy(() -> service.subir(1L, "OTRO", pdf("falso.pdf", "application/pdf", "MZ-no-soy-pdf".getBytes()), operador))
                .isInstanceOf(ReglaNegocioException.class).hasMessage("Solo se permiten archivos PDF");
        verify(documentos, never()).save(any());
    }

    @Test
    @DisplayName("[HU-14][RF-20] Un archivo de más de 5 MB se rechaza")
    void demasiadoGrande() {
        byte[] grande = new byte[5 * 1024 * 1024 + 1];
        System.arraycopy("%PDF".getBytes(), 0, grande, 0, 4);
        assertThatThrownBy(() -> service.subir(1L, "OTRO", pdf("grande.pdf", "application/pdf", grande), operador))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("5 MB");
    }

    @Test
    @DisplayName("[HU-15][RF-21] faltantes() lista los obligatorios sin cargar e ignora los rechazados")
    void faltantes() {
        Documento ok = doc(TipoDocumento.CERTIFICADO_ORIGEN, EstadoValidacion.VALIDADO);
        Documento rechazado = doc(TipoDocumento.FITOSANITARIO, EstadoValidacion.RECHAZADO);
        when(documentos.findByExportacionIdOrderByIdDesc(1L)).thenReturn(List.of(ok, rechazado));
        assertThat(service.faltantes(1L)).containsExactly(TipoDocumento.FITOSANITARIO, TipoDocumento.FACTURA_COMERCIAL, TipoDocumento.DECLARACION_ADUANERA);
    }

    @Test
    @DisplayName("[HU-14][RF-22] En una exportación cancelada no se cargan documentos")
    void exportacionCancelada() {
        ex.setEstado(EstadoExportacion.CANCELADA);
        assertThatThrownBy(() -> service.subir(1L, "OTRO", pdf("a.pdf", "application/pdf", "%PDF".getBytes()), operador))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("cancelada o entregada");
    }

    private Documento doc(TipoDocumento tipo, EstadoValidacion estado) {
        Documento d = new Documento();
        d.setTipo(tipo);
        d.setEstadoValidacion(estado);
        return d;
    }
}
'''

# ================================================================= repositorios (@DataJpaTest)
F["repositorio/RepositoriosTest.java"] = r'''package co.ritech.coffeeexport.repositorio;

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
'''

for ruta, contenido in F.items():
    destino = os.path.normpath(os.path.join(BASE, ruta))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    open(destino, "w", encoding="utf-8", newline="\n").write(contenido)
print(len(F), "archivos")
