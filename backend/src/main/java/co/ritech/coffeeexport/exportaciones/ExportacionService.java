package co.ritech.coffeeexport.exportaciones;

import co.ritech.coffeeexport.clientes.Cliente;
import co.ritech.coffeeexport.clientes.ClienteRepository;
import co.ritech.coffeeexport.documentos.DocumentoService;
import co.ritech.coffeeexport.documentos.TipoDocumento;
import co.ritech.coffeeexport.inventario.InventarioService;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.ProductoRepository;
import co.ritech.coffeeexport.shared.Paises;
import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Pedidos y envíos de exportación (HU-11, HU-12, RF-16 a RF-19). */
@Service
public class ExportacionService {
    static final ZoneId ZONA = ZoneId.of("America/Bogota");

    private final ExportacionRepository exportaciones;
    private final ClienteRepository clientes;
    private final ProductoRepository productos;
    private final InventarioService inventario;
    private final DocumentoService documentos;

    public ExportacionService(ExportacionRepository exportaciones, ClienteRepository clientes, ProductoRepository productos,
                              InventarioService inventario, DocumentoService documentos) {
        this.exportaciones = exportaciones;
        this.clientes = clientes;
        this.productos = productos;
        this.inventario = inventario;
        this.documentos = documentos;
    }

    /** Crea la exportación en BORRADOR o la confirma de inmediato (descontando inventario) según el estado inicial. */
    @Transactional
    public Exportacion crearExportacion(ExportacionRequest r, Usuario creador) {
        Cliente cliente = clientes.findById(r.clienteId()).orElseThrow(() -> new ReglaNegocioException("El cliente seleccionado no existe"));
        if (!cliente.isActivo()) {
            throw new ReglaNegocioException("El cliente seleccionado no está activo");
        }
        if (!Paises.esUe(r.paisDestino())) {
            throw new ReglaNegocioException("Seleccione el país destino dentro de la Unión Europea");
        }
        if (r.fechaEnvio().isBefore(LocalDate.now(ZONA))) {
            throw new ReglaNegocioException("La fecha de envío no puede estar en el pasado");
        }
        boolean confirmar = r.estadoInicial() != null && r.estadoInicial().equalsIgnoreCase("EN_PREPARACION");
        if (r.estadoInicial() != null && !r.estadoInicial().isBlank() && !confirmar && !r.estadoInicial().equalsIgnoreCase("BORRADOR")) {
            throw new ReglaNegocioException("El estado inicial debe ser BORRADOR o EN_PREPARACION");
        }

        Exportacion ex = new Exportacion();
        ex.setCodigo("TMP-" + UUID.randomUUID().toString().replace("-", "").substring(0, 16));   // provisional (20 caracteres como máximo)
        ex.setCliente(cliente);
        ex.setPaisDestino(r.paisDestino().trim().toUpperCase());
        ex.setPuertoSalida(r.puertoSalida().trim());
        ex.setPuertoLlegada(r.puertoLlegada().trim());
        ex.setFechaEnvio(r.fechaEnvio());
        ex.setObservaciones(r.observaciones());
        ex.setUsuarioCreador(creador);
        ex.setEstado(EstadoExportacion.BORRADOR);
        for (ExportacionRequest.Linea l : r.lineas()) {
            if (l.cantidadKg().compareTo(BigDecimal.ZERO) <= 0) {
                throw new ReglaNegocioException("La cantidad debe ser mayor que cero");
            }
            if (l.precioUnitario().compareTo(BigDecimal.ZERO) <= 0) {
                throw new ReglaNegocioException("El precio debe ser mayor que cero");
            }
            Producto p = productos.findById(l.productoId()).orElseThrow(() -> new ReglaNegocioException("Producto no encontrado"));
            if (!p.isActivo()) {
                throw new ReglaNegocioException("El producto " + p.getNombre() + " no está activo");
            }
            DetalleExportacion d = new DetalleExportacion();
            d.setProducto(p);
            d.setCantidadKg(l.cantidadKg());
            d.setPrecioUnitario(l.precioUnitario());
            ex.agregarDetalle(d);
        }
        inventario.validarDisponibilidad(ex);   // UC-08 3a: el stock insuficiente bloquea el avance
        Exportacion guardada = exportaciones.save(ex);
        guardada.setCodigo(String.format("EXP-%d-%04d", LocalDate.now(ZONA).getYear(), guardada.getId()));
        if (confirmar) {
            confirmarInterno(guardada, creador);
        }
        return exportaciones.save(guardada);
    }

    /** Transiciones válidas: BORRADOR → EN_PREPARACION → EN_TRANSITO → ENTREGADA; cancelar desde BORRADOR o EN_PREPARACION. */
    @Transactional
    public Exportacion cambiarEstado(Long id, EstadoExportacion nuevo, Usuario usuario) {
        Exportacion ex = obtener(id);
        EstadoExportacion actual = ex.getEstado();
        switch (nuevo) {
            case EN_PREPARACION -> {
                exigir(actual == EstadoExportacion.BORRADOR, actual, nuevo);
                confirmarInterno(ex, usuario);
            }
            case EN_TRANSITO -> {
                exigir(actual == EstadoExportacion.EN_PREPARACION, actual, nuevo);
                List<TipoDocumento> faltan = documentos.faltantes(id);   // RF-21
                if (!faltan.isEmpty()) {
                    throw new ReglaNegocioException("Faltan documentos obligatorios: "
                            + faltan.stream().map(TipoDocumento::getEtiqueta).collect(Collectors.joining(", ")) + ".");
                }
                ex.setEstado(nuevo);
            }
            case ENTREGADA -> {
                exigir(actual == EstadoExportacion.EN_TRANSITO, actual, nuevo);
                ex.setEstado(nuevo);
            }
            case CANCELADA -> {
                exigir(actual == EstadoExportacion.BORRADOR || actual == EstadoExportacion.EN_PREPARACION, actual, nuevo);
                if (ex.isDescontado()) {
                    inventario.devolverStock(ex, usuario);
                    ex.setDescontado(false);
                }
                ex.setEstado(nuevo);
            }
            default -> throw new ReglaNegocioException("Transición de estado no permitida: " + actual + " a " + nuevo);
        }
        return exportaciones.save(ex);
    }

    @Transactional(readOnly = true)
    public Exportacion obtener(Long id) {
        return exportaciones.findById(id).orElseThrow(() -> new RecursoNoEncontradoException("Exportación no encontrada"));
    }

    @Transactional(readOnly = true)
    public List<Exportacion> listar(String q, String estado) {
        EstadoExportacion filtro = estado == null || estado.isBlank() ? null : parsear(estado);
        String texto = q == null ? "" : q.trim().toLowerCase();
        return exportaciones.findAllByOrderByIdDesc().stream()
                .filter(e -> filtro == null || e.getEstado() == filtro)
                .filter(e -> texto.isEmpty() || e.getCodigo().toLowerCase().contains(texto)
                        || e.getCliente().getNombre().toLowerCase().contains(texto))
                .toList();
    }

    public static EstadoExportacion parsear(String estado) {
        try {
            return EstadoExportacion.valueOf(estado.trim().toUpperCase());
        } catch (IllegalArgumentException | NullPointerException e) {
            throw new ReglaNegocioException("Estado de exportación no válido");
        }
    }

    private void confirmarInterno(Exportacion ex, Usuario usuario) {
        inventario.descontarParaExportacion(ex, usuario);   // RF-19
        ex.setDescontado(true);
        ex.setEstado(EstadoExportacion.EN_PREPARACION);
    }

    private static void exigir(boolean condicion, EstadoExportacion actual, EstadoExportacion nuevo) {
        if (!condicion) {
            throw new ReglaNegocioException("Transición de estado no permitida: " + actual + " a " + nuevo);
        }
    }
}
