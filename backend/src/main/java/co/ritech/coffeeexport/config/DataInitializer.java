package co.ritech.coffeeexport.config;

import co.ritech.coffeeexport.clientes.Cliente;
import co.ritech.coffeeexport.clientes.ClienteRepository;
import co.ritech.coffeeexport.documentos.*;
import co.ritech.coffeeexport.exportaciones.*;
import co.ritech.coffeeexport.inventario.*;
import co.ritech.coffeeexport.pagos.*;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.ProductoRepository;
import co.ritech.coffeeexport.productos.TipoProducto;
import co.ritech.coffeeexport.usuarios.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * Crea roles y permisos (siempre) y, con app.seed.demo=true, datos de demostración equivalentes a los del prototipo web.
 * Las contraseñas de demostración se guardan con BCrypt; no deben usarse en producción.
 */
@Component
public class DataInitializer implements ApplicationRunner {
    static final String CLAVE_DEMO = "Demo2026*";
    private static final ZoneId ZONA = ZoneId.of("America/Bogota");

    private final RolRepository roles;
    private final PermisoRepository permisos;
    private final UsuarioRepository usuarios;
    private final ClienteRepository clientes;
    private final ProductoRepository productos;
    private final BodegaRepository bodegas;
    private final InventarioRepository inventario;
    private final ExportacionRepository exportaciones;
    private final DocumentoRepository documentos;
    private final PagoRepository pagos;
    private final PasswordEncoder encoder;
    private final boolean demo;

    public DataInitializer(RolRepository roles, PermisoRepository permisos, UsuarioRepository usuarios, ClienteRepository clientes,
                           ProductoRepository productos, BodegaRepository bodegas, InventarioRepository inventario,
                           ExportacionRepository exportaciones, DocumentoRepository documentos, PagoRepository pagos,
                           PasswordEncoder encoder, @Value("${app.seed.demo:false}") boolean demo) {
        this.roles = roles;
        this.permisos = permisos;
        this.usuarios = usuarios;
        this.clientes = clientes;
        this.productos = productos;
        this.bodegas = bodegas;
        this.inventario = inventario;
        this.exportaciones = exportaciones;
        this.documentos = documentos;
        this.pagos = pagos;
        this.encoder = encoder;
        this.demo = demo;
    }

    @Override
    @Transactional
    public void run(ApplicationArguments args) {
        sembrarRolesYPermisos();
        if (demo && usuarios.count() == 0) {
            sembrarDemo();
        }
    }

    private void sembrarRolesYPermisos() {
        Map<String, String> descripciones = Map.of(Acceso.ADMIN, "Administrador del sistema", Acceso.GERENTE, "Gerente / Ejecutivo",
                Acceso.OP_EXPORTACIONES, "Operador de exportaciones", Acceso.OP_BODEGA, "Operador de bodega", Acceso.CONTADOR, "Contador / Finanzas");
        for (String nombre : Acceso.ROLES) {
            roles.findByNombre(nombre).orElseGet(() -> roles.save(new Rol(nombre, descripciones.get(nombre))));
        }
        Acceso.MODULOS.forEach((modulo, acceso) -> {
            asignar(modulo.toUpperCase() + "_LEER", "Consultar " + modulo, acceso.leer());
            if (acceso.escribir().length > 0) {
                asignar(modulo.toUpperCase() + "_ESCRIBIR", "Modificar " + modulo, acceso.escribir());
            }
        });
    }

    private void asignar(String codigo, String descripcion, String[] nombresRol) {
        Permiso p = permisos.findByCodigo(codigo).orElseGet(() -> permisos.save(new Permiso(codigo, descripcion)));
        for (String n : nombresRol) {
            Rol r = roles.findByNombre(n).orElseThrow();
            if (r.getPermisos().add(p)) {
                roles.save(r);
            }
        }
    }

    private void sembrarDemo() {
        String hash = encoder.encode(CLAVE_DEMO);
        Map<String, Usuario> u = new LinkedHashMap<>();
        u.put("admin", usuario("Administrador RITECH", "admin@ritech.co", hash, Acceso.ADMIN));
        usuario("Gerente General", "gerente@ritech.co", hash, Acceso.GERENTE);
        u.put("exp", usuario("Operador Exportaciones", "exportaciones@ritech.co", hash, Acceso.OP_EXPORTACIONES));
        usuario("Operador Bodega", "bodega@ritech.co", hash, Acceso.OP_BODEGA);
        usuario("Contadora Finanzas", "contador@ritech.co", hash, Acceso.CONTADOR);

        List<Cliente> cs = List.of(
                cliente("Kaffee GmbH", "DE", "DE811234567", "Hans Becker", "contacto@kaffeegmbh.de", "+49 30 123456", true),
                cliente("EuroChoco Ltd", "NL", "NL820123456B01", "Sanne de Vries", "info@eurochoco.nl", "+31 20 987654", true),
                cliente("Baltic Foods", "BE", "BE0412345678", "Luc Peeters", "sales@balticfoods.be", "+32 2 123456", true),
                cliente("France Agro", "FR", "FR40303265045", "Camille Laurent", "contact@franceagro.fr", "+33 1 234567", true),
                cliente("Italian Trade", "IT", "IT01234567890", "Giulia Rossi", "info@italiantrade.it", "+39 02 345678", true),
                cliente("Iberia Cafés S.L.", "ES", "ESB12345678", "Carlos Mena", "compras@iberiacafes.es", "+34 91 555 0101", true),
                cliente("Nordic Beans AB", "SE", "SE556677889901", "Elin Karlsson", "order@nordicbeans.se", "+46 8 123 456", true),
                cliente("Lisboa Gourmet", "PT", "PT509876543", "Rita Santos", "geral@lisboagourmet.pt", "+351 21 123 4567", false));

        Bodega b1 = bodegas.save(new Bodega("Bodega Cartagena", "Cartagena"));
        Bodega b2 = bodegas.save(new Bodega("Bodega Bogotá", "Bogotá"));
        List<Producto> ps = List.of(
                producto("CAF-ARA-01", "Café Arábica", TipoProducto.CAFE, "Caturra", "4.50"),
                producto("CAF-ROB-01", "Café Robusta", TipoProducto.CAFE, "Robusta estándar", "3.20"),
                producto("CAF-CAS-01", "Café Castillo", TipoProducto.CAFE, "Castillo", "4.85"),
                producto("CAC-GRA-01", "Cacao en grano", TipoProducto.CACAO, "Criollo", "5.80"),
                producto("CAC-POL-01", "Cacao en polvo", TipoProducto.CACAO, "Trinitario", "4.10"),
                producto("CAC-NIB-01", "Nibs de cacao", TipoProducto.CACAO, "Criollo", "6.30"));
        stock(ps.get(0), b1, "1500", "800");
        stock(ps.get(0), b2, "1000", "0");
        stock(ps.get(1), b1, "4000", "1000");
        stock(ps.get(2), b2, "2200", "700");
        stock(ps.get(3), b1, "1200", "1000");
        stock(ps.get(4), b2, "800", "500");
        stock(ps.get(5), b1, "1750", "400");

        // Exportaciones de demostración repartidas en los últimos 80 días
        Random azar = new Random(7);
        List<Cliente> activos = cs.stream().filter(Cliente::isActivo).toList();
        LocalDate hoy = LocalDate.now(ZONA);
        for (int i = 0; i < 12; i++) {
            Cliente c = activos.get(azar.nextInt(activos.size()));
            int dias = 80 - i * 7;
            EstadoExportacion estado = dias > 45 ? EstadoExportacion.ENTREGADA : dias > 20 ? EstadoExportacion.EN_TRANSITO
                    : dias > 6 ? EstadoExportacion.EN_TRANSITO : (i % 2 == 0 ? EstadoExportacion.EN_PREPARACION : EstadoExportacion.BORRADOR);
            Exportacion ex = new Exportacion();
            ex.setCodigo("TMP-" + i);
            ex.setCliente(c);
            ex.setPaisDestino(c.getPais());
            ex.setPuertoSalida(i % 2 == 0 ? "Cartagena" : "Santa Marta");
            ex.setPuertoLlegada("Róterdam");
            ex.setFechaEnvio(hoy.minusDays(dias - 7));
            ex.setEstado(estado);
            ex.setUsuarioCreador(u.get("exp"));
            ex.setDescontado(estado != EstadoExportacion.BORRADOR);
            int lineas = 1 + azar.nextInt(2);
            Set<Integer> usados = new HashSet<>();
            while (usados.size() < lineas) {
                int k = azar.nextInt(ps.size());
                if (!usados.add(k)) {
                    continue;
                }
                DetalleExportacion d = new DetalleExportacion();
                d.setProducto(ps.get(k));
                d.setCantidadKg(BigDecimal.valueOf(200 + azar.nextInt(26) * 50L));
                d.setPrecioUnitario(ps.get(k).getPrecioUsdKg());
                ex.agregarDetalle(d);
            }
            Exportacion g = exportaciones.save(ex);
            g.setCodigo(String.format("EXP-%d-%04d", g.getFechaEnvio().getYear(), g.getId()));
            exportaciones.save(g);
            if (estado == EstadoExportacion.EN_TRANSITO || estado == EstadoExportacion.ENTREGADA) {
                for (TipoDocumento t : TipoDocumento.OBLIGATORIOS) {
                    documento(g, t, EstadoValidacion.VALIDADO, u.get("exp"));
                }
                pago(g, estado == EstadoExportacion.ENTREGADA ? EstadoPago.CONFIRMADO : EstadoPago.PENDIENTE, estado == EstadoExportacion.ENTREGADA ? 1.0 : 0.5, i % 3 == 0, u.get("admin"));
            } else if (estado == EstadoExportacion.EN_PREPARACION) {
                documento(g, TipoDocumento.FACTURA_COMERCIAL, EstadoValidacion.PENDIENTE, u.get("exp"));
            }
        }
    }

    private Usuario usuario(String nombre, String email, String hash, String rol) {
        Usuario x = new Usuario();
        x.setNombre(nombre);
        x.setEmail(email);
        x.setPasswordHash(hash);
        x.setRol(roles.findByNombre(rol).orElseThrow());
        return usuarios.save(x);
    }

    private Cliente cliente(String nombre, String pais, String nif, String contacto, String email, String tel, boolean activo) {
        Cliente c = new Cliente();
        c.setNombre(nombre);
        c.setPais(pais);
        c.setIdentificacionFiscal(nif);
        c.setContactoNombre(contacto);
        c.setContactoEmail(email);
        c.setContactoTelefono(tel);
        c.setConsentimientoDatos(true);
        c.setFechaConsentimiento(LocalDateTime.now());
        c.setActivo(activo);
        return clientes.save(c);
    }

    private Producto producto(String codigo, String nombre, TipoProducto tipo, String variedad, String precio) {
        Producto p = new Producto();
        p.setCodigo(codigo);
        p.setNombre(nombre);
        p.setTipo(tipo);
        p.setVariedad(variedad);
        p.setPrecioUsdKg(new BigDecimal(precio));
        return productos.save(p);
    }

    private void stock(Producto p, Bodega b, String kg, String minimo) {
        Inventario i = new Inventario();
        i.setProducto(p);
        i.setBodega(b);
        i.setCantidadKg(new BigDecimal(kg));
        i.setStockMinimoKg(new BigDecimal(minimo));
        inventario.save(i);
    }

    private void documento(Exportacion ex, TipoDocumento tipo, EstadoValidacion estado, Usuario por) {
        Documento d = new Documento();
        d.setExportacion(ex);
        d.setTipo(tipo);
        d.setNombreArchivo(tipo.name().toLowerCase() + "_" + ex.getCodigo() + ".pdf");
        d.setRutaArchivo("demo");   // documento de demostración sin archivo físico
        d.setTamanoBytes(180_000);
        d.setEstadoValidacion(estado);
        d.setSubidoPor(por);
        documentos.save(d);
    }

    private void pago(Exportacion ex, EstadoPago estado, double fraccion, boolean euros, Usuario por) {
        Pago p = new Pago();
        p.setExportacion(ex);
        BigDecimal usd = ex.getTotalUsd().multiply(BigDecimal.valueOf(fraccion));
        p.setMoneda(euros ? Moneda.EUR : Moneda.USD);
        p.setMonto((euros ? usd.divide(new BigDecimal("1.08"), 2, java.math.RoundingMode.HALF_UP) : usd).setScale(2, java.math.RoundingMode.HALF_UP));
        p.setMetodo(MetodoPago.TRANSFERENCIA);
        p.setReferencia("TRX-" + (100000 + ex.getId() * 37));
        p.setFechaPago(ex.getFechaEnvio().plusDays(12).isAfter(LocalDate.now(ZONA)) ? LocalDate.now(ZONA) : ex.getFechaEnvio().plusDays(12));
        p.setEstado(estado);
        p.setRegistradoPor(por);
        pagos.save(p);
    }
}
