# -*- coding: utf-8 -*-
"""Bloque 4: reportes, dashboard, instantánea para el frontend, datos iniciales. También parchea gen2 (validarDisponibilidad)."""
import os, re
AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(AQUI, "..", "src", "main", "java", "co", "ritech", "coffeeexport")

# ---- parche a InventarioService (validarDisponibilidad pública y reutilizable)
p2 = os.path.join(AQUI, "gen2.py")
g2 = open(p2, encoding="utf-8").read()
if "validarDisponibilidad" not in g2:
    ini = g2.index("    @Transactional\n    public void descontarParaExportacion")
    fin = g2.index("        for (Map.Entry<Long, BigDecimal> e : pedido.entrySet()) {\n            BigDecimal falta")
    nuevo = '''    /** Comprueba que haya stock de todos los productos de la exportación antes de comprometerla (UC-08 3a). */
    @Transactional(readOnly = true)
    public void validarDisponibilidad(Exportacion ex) {
        for (Map.Entry<Long, BigDecimal> e : pedidoPorProducto(ex).entrySet()) {
            BigDecimal disponible = consultarStock(e.getKey()).totalKg();
            if (e.getValue().compareTo(disponible) > 0) {
                String nombre = productos.findById(e.getKey()).map(Producto::getNombre).orElse("producto " + e.getKey());
                throw new StockInsuficienteException("Stock insuficiente de " + nombre + ": solicitado "
                        + Formato.kg(e.getValue()) + ", disponible " + Formato.kg(disponible));
            }
        }
    }

    private Map<Long, BigDecimal> pedidoPorProducto(Exportacion ex) {
        Map<Long, BigDecimal> pedido = new LinkedHashMap<>();
        for (DetalleExportacion d : ex.getDetalles()) {
            pedido.merge(d.getProducto().getId(), d.getCantidadKg(), BigDecimal::add);
        }
        return pedido;
    }

    /**
     * RF-19: descuenta el inventario de una exportación, de la bodega con más stock a la de menos.
     * Es atómica: primero valida todos los productos y solo entonces mueve existencias.
     */
    @Transactional
    public void descontarParaExportacion(Exportacion ex, Usuario usuario) {
        validarDisponibilidad(ex);
        Map<Long, BigDecimal> pedido = pedidoPorProducto(ex);
'''
    # quitar el javadoc previo del método viejo
    previo = g2.rfind("    /**\n     * RF-19", 0, ini)
    g2 = g2[:previo] + nuevo + g2[fin:]
    open(p2, "w", encoding="utf-8").write(g2)

F = {}

# ================================================================= reportes
F["reportes/ReporteDto.java"] = r'''package co.ritech.coffeeexport.reportes;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record ReporteDto(String titulo, String tipo, LocalDate desde, LocalDate hasta, long totalExportaciones, BigDecimal ventasUsd,
                         long clientesConEnvios, List<Par> porPais, List<ParMonto> productosTop, List<String> cabeceras,
                         List<List<Object>> filas) {
    public record Par(String clave, long valor) {
    }

    public record ParMonto(String clave, BigDecimal valor) {
    }
}
'''
F["reportes/ReporteService.java"] = r'''package co.ritech.coffeeexport.reportes;

import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.inventario.Inventario;
import co.ritech.coffeeexport.inventario.InventarioRepository;
import co.ritech.coffeeexport.reportes.ReporteDto.Par;
import co.ritech.coffeeexport.reportes.ReporteDto.ParMonto;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Reportes por rango de fechas (HU-18, RF-26, RF-28). La exportación a PDF y Excel se hace en la interfaz (RF-27). */
@Service
public class ReporteService {
    private static final Set<String> TIPOS = Set.of("exportaciones", "ventas", "existencias");
    private static final List<EstadoExportacion> EXCLUIDOS = List.of(EstadoExportacion.CANCELADA, EstadoExportacion.BORRADOR);

    private final ExportacionRepository exportaciones;
    private final InventarioRepository inventario;

    public ReporteService(ExportacionRepository exportaciones, InventarioRepository inventario) {
        this.exportaciones = exportaciones;
        this.inventario = inventario;
    }

    @Transactional(readOnly = true)
    public ReporteDto generarReporte(LocalDate desde, LocalDate hasta, String tipo) {
        if (desde == null || hasta == null) {
            throw new ReglaNegocioException("Seleccione el rango de fechas");
        }
        if (hasta.isBefore(desde)) {
            throw new ReglaNegocioException("La fecha final no puede ser anterior a la fecha inicial");
        }
        String t = tipo == null || tipo.isBlank() ? "exportaciones" : tipo.trim().toLowerCase();
        if (!TIPOS.contains(t)) {
            throw new ReglaNegocioException("Tipo de reporte no válido: exportaciones, ventas o existencias");
        }
        List<Exportacion> lista = exportaciones.enRango(desde, hasta, EXCLUIDOS);
        BigDecimal ventas = lista.stream().map(Exportacion::getTotalUsd).reduce(BigDecimal.ZERO, BigDecimal::add);
        long clientes = lista.stream().map(e -> e.getCliente().getId()).distinct().count();

        Map<String, Long> porPais = lista.stream().collect(Collectors.groupingBy(Exportacion::getPaisDestino, Collectors.counting()));
        Map<String, BigDecimal> porProducto = new HashMap<>();
        lista.forEach(e -> e.getDetalles().forEach(d -> porProducto.merge(d.getProducto().getNombre(), d.getSubtotal(), BigDecimal::add)));

        String titulo;
        List<String> cabeceras;
        List<List<Object>> filas = new ArrayList<>();
        switch (t) {
            case "ventas" -> {
                titulo = "Ventas por producto y país";
                cabeceras = List.of("Producto", "País", "Cantidad (kg)", "Ventas (USD)", "% del total");
                Map<String, BigDecimal[]> agg = new TreeMap<>();
                lista.forEach(e -> e.getDetalles().forEach(d -> {
                    BigDecimal[] a = agg.computeIfAbsent(d.getProducto().getNombre() + "|" + e.getPaisDestino(), k -> new BigDecimal[]{BigDecimal.ZERO, BigDecimal.ZERO});
                    a[0] = a[0].add(d.getCantidadKg());
                    a[1] = a[1].add(d.getSubtotal());
                }));
                agg.entrySet().stream().sorted((x, y) -> y.getValue()[1].compareTo(x.getValue()[1])).forEach(en -> {
                    String[] k = en.getKey().split("\\|");
                    BigDecimal pct = ventas.signum() == 0 ? BigDecimal.ZERO : en.getValue()[1].multiply(BigDecimal.valueOf(100)).divide(ventas, 1, RoundingMode.HALF_UP);
                    filas.add(List.of(k[0], k[1], en.getValue()[0], en.getValue()[1], pct + " %"));
                });
            }
            case "existencias" -> {
                titulo = "Existencias actuales";
                cabeceras = List.of("Producto", "Bodega", "Stock (kg)", "Mínimo (kg)", "Estado");
                for (Inventario i : inventario.findAllByOrderByIdAsc()) {
                    boolean bajo = i.getStockMinimoKg().signum() > 0 && i.getCantidadKg().compareTo(i.getStockMinimoKg()) < 0;
                    filas.add(List.of(i.getProducto().getNombre(), i.getBodega().getNombre(), i.getCantidadKg(), i.getStockMinimoKg(), bajo ? "Bajo mínimo" : "Normal"));
                }
            }
            default -> {
                titulo = "Detalle de exportaciones";
                cabeceras = List.of("Código", "Cliente", "País", "Cantidad (kg)", "Total (USD)", "Fecha de envío", "Estado");
                lista.forEach(e -> filas.add(List.of(e.getCodigo(), e.getCliente().getNombre(), e.getPaisDestino(), e.getTotalKg(), e.getTotalUsd(),
                        e.getFechaEnvio().toString(), e.getEstado().name())));
            }
        }
        List<Par> paises = porPais.entrySet().stream().sorted((a, b) -> Long.compare(b.getValue(), a.getValue())).map(e -> new Par(e.getKey(), e.getValue())).toList();
        List<ParMonto> top = porProducto.entrySet().stream().sorted((a, b) -> b.getValue().compareTo(a.getValue())).limit(5)
                .map(e -> new ParMonto(e.getKey(), e.getValue().setScale(2, RoundingMode.HALF_UP))).toList();
        return new ReporteDto(titulo, t, desde, hasta, lista.size(), ventas.setScale(2, RoundingMode.HALF_UP), clientes, paises, top, cabeceras, filas);
    }
}
'''
F["reportes/ReporteController.java"] = r'''package co.ritech.coffeeexport.reportes;

import java.time.LocalDate;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/reportes")
public class ReporteController {
    private final ReporteService service;

    public ReporteController(ReporteService service) {
        this.service = service;
    }

    @GetMapping
    public ReporteDto generar(@RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate desde,
                              @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate hasta,
                              @RequestParam(required = false) String tipo) {
        return service.generarReporte(desde, hasta, tipo);
    }
}
'''

# ================================================================= dashboard
F["dashboard/KpiDto.java"] = r'''package co.ritech.coffeeexport.dashboard;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record KpiDto(long totalExportaciones, long exportacionesMes, long exportacionesMesAnterior, long clientesActivos,
                     long clientesRegistrados, BigDecimal inventarioKg, long productosBajoMinimo, BigDecimal ventasMesUsd,
                     BigDecimal ventasMesAnteriorUsd, List<Par> exportacionesPorPais, List<ParKg> productosMasVendidos,
                     List<Ultima> ultimasExportaciones) {
    public record Par(String pais, long cantidad) {
    }

    public record ParKg(String producto, BigDecimal kg) {
    }

    public record Ultima(String codigo, String cliente, String pais, String producto, LocalDate fechaEnvio, String estado) {
    }
}
'''
F["dashboard/DashboardService.java"] = r'''package co.ritech.coffeeexport.dashboard;

import co.ritech.coffeeexport.clientes.ClienteRepository;
import co.ritech.coffeeexport.dashboard.KpiDto.Par;
import co.ritech.coffeeexport.dashboard.KpiDto.ParKg;
import co.ritech.coffeeexport.dashboard.KpiDto.Ultima;
import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.inventario.Inventario;
import co.ritech.coffeeexport.inventario.InventarioRepository;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.ZoneId;
import java.util.*;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Indicadores del dashboard ejecutivo (HU-20, HU-21, RF-29 a RF-31). */
@Service
public class DashboardService {
    private static final Set<EstadoExportacion> SIN_VENTA = Set.of(EstadoExportacion.CANCELADA, EstadoExportacion.BORRADOR);

    private final ExportacionRepository exportaciones;
    private final ClienteRepository clientes;
    private final InventarioRepository inventario;

    public DashboardService(ExportacionRepository exportaciones, ClienteRepository clientes, InventarioRepository inventario) {
        this.exportaciones = exportaciones;
        this.clientes = clientes;
        this.inventario = inventario;
    }

    @Transactional(readOnly = true)
    public KpiDto kpis() {
        List<Exportacion> todas = exportaciones.findAllByOrderByIdDesc();
        YearMonth mes = YearMonth.now(ZoneId.of("America/Bogota"));
        YearMonth anterior = mes.minusMonths(1);
        List<Exportacion> vendidas = todas.stream().filter(e -> !SIN_VENTA.contains(e.getEstado())).toList();

        BigDecimal ventasMes = suma(vendidas, mes), ventasAnt = suma(vendidas, anterior);
        long delMes = todas.stream().filter(e -> YearMonth.from(e.getFechaEnvio()).equals(mes)).count();
        long delAnterior = todas.stream().filter(e -> YearMonth.from(e.getFechaEnvio()).equals(anterior)).count();

        Map<String, Long> porPais = todas.stream().filter(e -> e.getEstado() != EstadoExportacion.CANCELADA)
                .collect(Collectors.groupingBy(Exportacion::getPaisDestino, Collectors.counting()));
        List<Par> paises = porPais.entrySet().stream().sorted((a, b) -> Long.compare(b.getValue(), a.getValue())).limit(6)
                .map(e -> new Par(e.getKey(), e.getValue())).toList();

        Map<String, BigDecimal> kgProducto = new HashMap<>();
        vendidas.forEach(e -> e.getDetalles().forEach(d -> kgProducto.merge(d.getProducto().getNombre(), d.getCantidadKg(), BigDecimal::add)));
        List<ParKg> masVendidos = kgProducto.entrySet().stream().sorted((a, b) -> b.getValue().compareTo(a.getValue())).limit(4)
                .map(e -> new ParKg(e.getKey(), e.getValue())).toList();

        List<Ultima> ultimas = todas.stream().sorted(Comparator.comparing(Exportacion::getFechaEnvio).reversed().thenComparing(Exportacion::getId, Comparator.reverseOrder()))
                .limit(5).map(e -> new Ultima(e.getCodigo(), e.getCliente().getNombre(), e.getPaisDestino(),
                        e.getDetalles().isEmpty() ? "" : e.getDetalles().get(0).getProducto().getNombre(), e.getFechaEnvio(), e.getEstado().name())).toList();

        return new KpiDto(todas.size(), delMes, delAnterior, clientes.countByActivoTrue(), clientes.count(), inventario.totalGeneral(),
                productosBajoMinimo(), ventasMes, ventasAnt, paises, masVendidos, ultimas);
    }

    private static BigDecimal suma(List<Exportacion> lista, YearMonth mes) {
        return lista.stream().filter(e -> YearMonth.from(e.getFechaEnvio()).equals(mes)).map(Exportacion::getTotalUsd).reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    private long productosBajoMinimo() {
        Map<Long, BigDecimal[]> p = new HashMap<>();   // [stock, mínimo]
        for (Inventario i : inventario.findAllByOrderByIdAsc()) {
            BigDecimal[] a = p.computeIfAbsent(i.getProducto().getId(), k -> new BigDecimal[]{BigDecimal.ZERO, BigDecimal.ZERO});
            a[0] = a[0].add(i.getCantidadKg());
            a[1] = a[1].add(i.getStockMinimoKg());
        }
        return p.values().stream().filter(a -> a[1].signum() > 0 && a[0].compareTo(a[1]) < 0).count();
    }
}
'''
F["dashboard/DashboardController.java"] = r'''package co.ritech.coffeeexport.dashboard;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {
    private final DashboardService service;

    public DashboardController(DashboardService service) {
        this.service = service;
    }

    @GetMapping("/kpis")
    public KpiDto kpis() {
        return service.kpis();
    }
}
'''

# ================================================================= snapshot (para el frontend)
F["snapshot/SnapshotController.java"] = r'''package co.ritech.coffeeexport.snapshot;

import co.ritech.coffeeexport.auth.AuthService;
import java.util.Map;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Instantánea de datos con la forma que usa la interfaz (la misma de su modo demostración).
 * Solo incluye lo que el rol del usuario puede leer (RNF-03) y minimiza datos personales (GDPR, RR-05).
 */
@RestController
@RequestMapping("/api/snapshot")
public class SnapshotController {
    private final SnapshotService service;
    private final AuthService auth;

    public SnapshotController(SnapshotService service, AuthService auth) {
        this.service = service;
        this.auth = auth;
    }

    @GetMapping
    public Map<String, Object> snapshot(Authentication a) {
        return service.generar(auth.actual(a));
    }
}
'''
F["snapshot/SnapshotService.java"] = r'''package co.ritech.coffeeexport.snapshot;

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
'''

# ================================================================= datos iniciales
F["config/DataInitializer.java"] = r'''package co.ritech.coffeeexport.config;

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
'''

for ruta, contenido in F.items():
    destino = os.path.normpath(os.path.join(BASE, ruta))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    open(destino, "w", encoding="utf-8", newline="\n").write(contenido)
print(len(F), "archivos")
