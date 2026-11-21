package co.ritech.coffeeexport.inventario;

import co.ritech.coffeeexport.exportaciones.DetalleExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.inventario.InventarioDtos.StockBodegaDto;
import co.ritech.coffeeexport.inventario.InventarioDtos.StockDto;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.ProductoRepository;
import co.ritech.coffeeexport.shared.Formato;
import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.shared.StockInsuficienteException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Inventario en tiempo real por producto y bodega (HU-04, RF-12 a RF-15, RF-19). */
@Service
public class InventarioService {
    private final InventarioRepository inventarios;
    private final MovimientoInventarioRepository movimientos;
    private final ProductoRepository productos;
    private final BodegaRepository bodegas;

    public InventarioService(InventarioRepository inventarios, MovimientoInventarioRepository movimientos,
                             ProductoRepository productos, BodegaRepository bodegas) {
        this.inventarios = inventarios;
        this.movimientos = movimientos;
        this.productos = productos;
        this.bodegas = bodegas;
    }

    /** RF-12: stock total del producto sumando todas sus bodegas, con el detalle por bodega. */
    @Transactional(readOnly = true)
    public StockDto consultarStock(Long productoId) {
        List<Inventario> filas = inventarios.findByProductoId(productoId);
        BigDecimal total = filas.stream().map(Inventario::getCantidadKg).reduce(BigDecimal.ZERO, BigDecimal::add);
        List<StockBodegaDto> detalle = filas.stream()
                .map(i -> new StockBodegaDto(i.getBodega().getId(), i.getBodega().getNombre(), i.getCantidadKg())).toList();
        return new StockDto(productoId, total, detalle);
    }

    @Transactional
    public MovimientoInventario registrarEntrada(Long productoId, Long bodegaId, BigDecimal kg, String motivo, Usuario usuario) {
        exigirPositiva(kg);
        Inventario inv = inventarios.findByProductoIdAndBodegaId(productoId, bodegaId).orElseGet(() -> nuevo(productoId, bodegaId));
        inv.setCantidadKg(inv.getCantidadKg().add(kg));
        inventarios.save(inv);
        return registrar(inv, TipoMovimiento.ENTRADA, kg, motivo, null, usuario);
    }

    /** RF-14: no se permite una salida mayor al stock disponible. */
    @Transactional
    public MovimientoInventario registrarSalida(Long productoId, Long bodegaId, BigDecimal kg, String motivo, Usuario usuario) {
        return salida(productoId, bodegaId, kg, motivo, null, usuario);
    }

    @Transactional
    public MovimientoInventario ajustar(Long productoId, Long bodegaId, BigDecimal nuevoStock, String motivo, Usuario usuario) {
        if (nuevoStock == null || nuevoStock.compareTo(BigDecimal.ZERO) < 0) {
            throw new ReglaNegocioException("El stock ajustado no puede ser negativo");
        }
        Inventario inv = inventarios.findByProductoIdAndBodegaId(productoId, bodegaId).orElseGet(() -> nuevo(productoId, bodegaId));
        inv.setCantidadKg(nuevoStock);
        inventarios.save(inv);
        return registrar(inv, TipoMovimiento.AJUSTE, nuevoStock, motivo, null, usuario);
    }

    @Transactional
    public MovimientoInventario registrarMovimiento(MovimientoRequest r, Usuario usuario) {
        TipoMovimiento tipo;
        try {
            tipo = TipoMovimiento.valueOf(r.tipo().trim().toUpperCase());
        } catch (IllegalArgumentException e) {
            throw new ReglaNegocioException("Tipo de movimiento no válido: ENTRADA, SALIDA o AJUSTE");
        }
        return switch (tipo) {
            case ENTRADA -> registrarEntrada(r.productoId(), r.bodegaId(), r.cantidadKg(), r.motivo(), usuario);
            case SALIDA -> registrarSalida(r.productoId(), r.bodegaId(), r.cantidadKg(), r.motivo(), usuario);
            case AJUSTE -> ajustar(r.productoId(), r.bodegaId(), r.cantidadKg(), r.motivo(), usuario);
        };
    }

    /** Comprueba que haya stock de todos los productos de la exportación antes de comprometerla (UC-08 3a). */
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
        for (Map.Entry<Long, BigDecimal> e : pedido.entrySet()) {
            BigDecimal falta = e.getValue();
            List<Inventario> filas = inventarios.findByProductoId(e.getKey()).stream()
                    .filter(i -> i.getCantidadKg().signum() > 0)
                    .sorted(Comparator.comparing(Inventario::getCantidadKg).reversed()).toList();
            for (Inventario inv : filas) {
                if (falta.signum() == 0) {
                    break;
                }
                BigDecimal t = falta.min(inv.getCantidadKg());
                inv.setCantidadKg(inv.getCantidadKg().subtract(t));
                inventarios.save(inv);
                registrar(inv, TipoMovimiento.SALIDA, t, "Exportación " + ex.getCodigo(), ex, usuario);
                falta = falta.subtract(t);
            }
        }
    }

    /** Devuelve al inventario lo descontado por una exportación cancelada. */
    @Transactional
    public void devolverStock(Exportacion ex, Usuario usuario) {
        for (MovimientoInventario m : movimientos.findByExportacionIdAndTipo(ex.getId(), TipoMovimiento.SALIDA)) {
            Inventario inv = m.getInventario();
            inv.setCantidadKg(inv.getCantidadKg().add(m.getCantidadKg()));
            inventarios.save(inv);
            registrar(inv, TipoMovimiento.ENTRADA, m.getCantidadKg(), "Cancelación " + ex.getCodigo(), ex, usuario);
        }
    }

    @Transactional
    public Inventario actualizarMinimo(Long inventarioId, BigDecimal minimo) {
        if (minimo == null || minimo.signum() < 0) {
            throw new ReglaNegocioException("Ingrese un valor válido (mayor o igual a 0)");
        }
        Inventario inv = inventarios.findById(inventarioId).orElseThrow(() -> new RecursoNoEncontradoException("Registro de inventario no encontrado"));
        inv.setStockMinimoKg(minimo);
        return inventarios.save(inv);
    }

    @Transactional(readOnly = true)
    public List<Inventario> listar(Long productoId) {
        return productoId == null ? inventarios.findAllByOrderByIdAsc() : inventarios.findByProductoId(productoId);
    }

    @Transactional(readOnly = true)
    public List<MovimientoInventario> listarMovimientos() {
        return movimientos.findAllByOrderByIdDesc();
    }

    @Transactional(readOnly = true)
    public List<Bodega> listarBodegas() {
        return bodegas.findAll();
    }

    private MovimientoInventario salida(Long productoId, Long bodegaId, BigDecimal kg, String motivo, Exportacion ex, Usuario usuario) {
        exigirPositiva(kg);
        Inventario inv = inventarios.findByProductoIdAndBodegaId(productoId, bodegaId)
                .orElseThrow(() -> new StockInsuficienteException("No hay existencias de ese producto en la bodega seleccionada."));
        if (kg.compareTo(inv.getCantidadKg()) > 0) {
            throw new StockInsuficienteException("Stock insuficiente: disponible " + Formato.kg(inv.getCantidadKg()) + " en esa bodega.");
        }
        inv.setCantidadKg(inv.getCantidadKg().subtract(kg));
        inventarios.save(inv);
        return registrar(inv, TipoMovimiento.SALIDA, kg, motivo, ex, usuario);
    }

    private MovimientoInventario registrar(Inventario inv, TipoMovimiento tipo, BigDecimal kg, String motivo, Exportacion ex, Usuario usuario) {
        MovimientoInventario m = new MovimientoInventario();
        m.setInventario(inv);
        m.setTipo(tipo);
        m.setCantidadKg(kg);
        m.setMotivo(motivo);
        m.setExportacion(ex);
        m.setUsuario(usuario);
        return movimientos.save(m);
    }

    private Inventario nuevo(Long productoId, Long bodegaId) {
        Inventario inv = new Inventario();
        inv.setProducto(productos.findById(productoId).orElseThrow(() -> new RecursoNoEncontradoException("Producto no encontrado")));
        inv.setBodega(bodegas.findById(bodegaId).orElseThrow(() -> new RecursoNoEncontradoException("Bodega no encontrada")));
        return inv;
    }

    private static void exigirPositiva(BigDecimal kg) {
        if (kg == null || kg.compareTo(BigDecimal.ZERO) <= 0) {
            throw new ReglaNegocioException("La cantidad debe ser mayor que cero.");
        }
    }
}
