package co.ritech.coffeeexport.snapshot;

import co.ritech.coffeeexport.clientes.Cliente;
import co.ritech.coffeeexport.clientes.ClienteRepository;
import co.ritech.coffeeexport.config.Acceso;
import co.ritech.coffeeexport.documentos.Documento;
import co.ritech.coffeeexport.documentos.DocumentoRepository;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.inventario.*;
import co.ritech.coffeeexport.pagos.Pago;
import co.ritech.coffeeexport.pagos.PagoRepository;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.ProductoRepository;
import co.ritech.coffeeexport.usuarios.Usuario;
import co.ritech.coffeeexport.usuarios.UsuarioRepository;
import java.math.BigDecimal;
import java.util.*;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class SnapshotService {
    private final ClienteRepository clientes;
    private final ProductoRepository productos;
    private final BodegaRepository bodegas;
    private final InventarioRepository inventario;
    private final MovimientoInventarioRepository movimientos;
    private final ExportacionRepository exportaciones;
    private final DocumentoRepository documentos;
    private final PagoRepository pagos;
    private final UsuarioRepository usuarios;
    private final BigDecimal tasa;

    public SnapshotService(ClienteRepository clientes, ProductoRepository productos, BodegaRepository bodegas, InventarioRepository inventario,
                           MovimientoInventarioRepository movimientos, ExportacionRepository exportaciones, DocumentoRepository documentos,
                           PagoRepository pagos, UsuarioRepository usuarios, @Value("${app.tasa-eur-usd}") BigDecimal tasa) {
        this.clientes = clientes;
        this.productos = productos;
        this.bodegas = bodegas;
        this.inventario = inventario;
        this.movimientos = movimientos;
        this.exportaciones = exportaciones;
        this.documentos = documentos;
        this.pagos = pagos;
        this.usuarios = usuarios;
        this.tasa = tasa;
    }

    @Transactional(readOnly = true)
    public Map<String, Object> generar(Usuario u) {
        String rol = u.getRol().getNombre();
        boolean verClientes = puede(rol, "clientes"), verProductos = puede(rol, "productos"), verInventario = puede(rol, "inventario"),
                verExportaciones = puede(rol, "exportaciones"), verDocumentos = puede(rol, "documentos"), verPagos = puede(rol, "pagos");
        Map<String, Object> s = new LinkedHashMap<>();
        // Los clientes se incluyen siempre con datos mínimos (nombre y país) para rotular exportaciones y pagos; el detalle solo con permiso.
        s.put("clientes", clientes.findAll().stream().sorted(Comparator.comparing(Cliente::getId)).map(c -> cliente(c, verClientes)).toList());
        s.put("productos", productos.findAll().stream().sorted(Comparator.comparing(Producto::getId)).map(this::producto).toList());
        s.put("bodegas", bodegas.findAll().stream().map(b -> Map.of("id", b.getId(), "nombre", b.getNombre(), "ciudad", String.valueOf(b.getCiudad()))).toList());
        s.put("inventario", verInventario || verExportaciones ? inventario.findAllByOrderByIdAsc().stream().map(this::inventario).toList() : List.of());
        s.put("movimientos", verInventario ? movimientos.findAllByOrderByIdDesc().stream().map(this::movimiento).toList() : List.of());
        s.put("exportaciones", verExportaciones || verPagos ? exportaciones.findAllByOrderByIdDesc().stream().sorted(Comparator.comparing(Exportacion::getId)).map(this::exportacion).toList() : List.of());
        s.put("documentos", verDocumentos || verExportaciones ? documentos.findAllByOrderByIdDesc().stream().sorted(Comparator.comparing(Documento::getId)).map(this::documento).toList() : List.of());
        s.put("pagos", verPagos ? pagos.findAllByOrderByIdDesc().stream().sorted(Comparator.comparing(Pago::getId)).map(this::pago).toList() : List.of());
        s.put("usuarios", "ADMIN".equals(rol) ? usuarios.findAll().stream().sorted(Comparator.comparing(Usuario::getId)).map(x -> Map.<String, Object>of(
                "id", x.getId(), "nombre", x.getNombre(), "email", x.getEmail(), "rol", x.getRol().getNombre(), "activo", x.isActivo())).toList() : List.of());
        s.put("meta", Map.of("tasaEurUsd", tasa));
        return s;
    }

    private static boolean puede(String rol, String modulo) {
        return Arrays.asList(Acceso.MODULOS.get(modulo).leer()).contains(rol);
    }

    private Map<String, Object> cliente(Cliente c, boolean completo) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", c.getId());
        m.put("nombre", c.getNombre());
        m.put("pais", c.getPais());
        m.put("activo", c.isActivo());
        if (completo) {
            m.put("nif", c.getIdentificacionFiscal());
            m.put("contacto", c.getContactoNombre());
            m.put("email", c.getContactoEmail());
            m.put("telefono", nvl(c.getContactoTelefono()));
            m.put("direccion", nvl(c.getDireccion()));
            m.put("consent", c.isConsentimientoDatos());
            m.put("consentFecha", c.getFechaConsentimiento() == null ? null : c.getFechaConsentimiento().toLocalDate().toString());
        }
        return m;
    }

    private Map<String, Object> producto(Producto p) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", p.getId());
        m.put("codigo", p.getCodigo());
        m.put("nombre", p.getNombre());
        m.put("tipo", p.getTipo().name());
        m.put("variedad", nvl(p.getVariedad()));
        m.put("precio", p.getPrecioUsdKg());
        m.put("activo", p.isActivo());
        return m;
    }

    private Map<String, Object> inventario(Inventario i) {
        return Map.of("id", i.getId(), "producto_id", i.getProducto().getId(), "bodega_id", i.getBodega().getId(), "kg", i.getCantidadKg(), "min", i.getStockMinimoKg());
    }

    private Map<String, Object> movimiento(MovimientoInventario m) {
        Map<String, Object> r = new LinkedHashMap<>();
        r.put("id", m.getId());
        r.put("inv_id", m.getInventario().getId());
        r.put("tipo", m.getTipo().name());
        r.put("kg", m.getCantidadKg());
        r.put("motivo", nvl(m.getMotivo()));
        r.put("exportacion_id", m.getExportacion() == null ? null : m.getExportacion().getId());
        r.put("usuario", m.getUsuario().getNombre());
        r.put("fecha", m.getCreatedAt().toString());
        return r;
    }

    private Map<String, Object> exportacion(Exportacion e) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", e.getId());
        m.put("codigo", e.getCodigo());
        m.put("cliente_id", e.getCliente().getId());
        m.put("pais", e.getPaisDestino());
        m.put("puerto_salida", e.getPuertoSalida());
        m.put("puerto_llegada", e.getPuertoLlegada());
        m.put("fecha_envio", e.getFechaEnvio().toString());
        m.put("estado", e.getEstado().name());
        m.put("creador", e.getUsuarioCreador().getId());
        m.put("obs", nvl(e.getObservaciones()));
        m.put("descontado", e.isDescontado());
        m.put("creado", e.getCreatedAt().toLocalDate().toString());
        m.put("lineas", e.getDetalles().stream().map(d -> Map.of("producto_id", d.getProducto().getId(), "kg", d.getCantidadKg(), "precio", d.getPrecioUnitario())).toList());
        return m;
    }

    private Map<String, Object> documento(Documento d) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", d.getId());
        m.put("exportacion_id", d.getExportacion().getId());
        m.put("tipo", d.getTipo().name());
        m.put("archivo", d.getNombreArchivo());
        m.put("kb", Math.max(1, d.getTamanoBytes() / 1024));
        m.put("estado", d.getEstadoValidacion().name());
        m.put("fecha", d.getCreatedAt().toLocalDate().toString());
        m.put("por", d.getSubidoPor().getId());
        return m;
    }

    private Map<String, Object> pago(Pago p) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", p.getId());
        m.put("exportacion_id", p.getExportacion().getId());
        m.put("monto", p.getMonto());
        m.put("moneda", p.getMoneda().name());
        m.put("metodo", p.getMetodo().name());
        m.put("ref", nvl(p.getReferencia()));
        m.put("fecha", p.getFechaPago().toString());
        m.put("estado", p.getEstado().name());
        m.put("por", p.getRegistradoPor().getId());
        return m;
    }

    private static String nvl(String s) {
        return s == null ? "" : s;
    }
}
