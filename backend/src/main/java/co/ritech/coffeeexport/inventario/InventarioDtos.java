package co.ritech.coffeeexport.inventario;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

public final class InventarioDtos {
    private InventarioDtos() {
    }

    public record InventarioDto(Long id, Long productoId, String productoNombre, Long bodegaId, String bodegaNombre,
                                BigDecimal cantidadKg, BigDecimal stockMinimoKg) {
        public static InventarioDto de(Inventario i) {
            return new InventarioDto(i.getId(), i.getProducto().getId(), i.getProducto().getNombre(), i.getBodega().getId(),
                    i.getBodega().getNombre(), i.getCantidadKg(), i.getStockMinimoKg());
        }
    }

    public record StockBodegaDto(Long bodegaId, String bodega, BigDecimal cantidadKg) {
    }

    public record StockDto(Long productoId, BigDecimal totalKg, List<StockBodegaDto> bodegas) {
    }

    public record MovimientoDto(Long id, Long inventarioId, String tipo, BigDecimal cantidadKg, String motivo, Long exportacionId,
                                String usuario, LocalDateTime fecha) {
        public static MovimientoDto de(MovimientoInventario m) {
            return new MovimientoDto(m.getId(), m.getInventario().getId(), m.getTipo().name(), m.getCantidadKg(), m.getMotivo(),
                    m.getExportacion() == null ? null : m.getExportacion().getId(), m.getUsuario().getNombre(), m.getCreatedAt());
        }
    }

    public record MinimoRequest(BigDecimal stockMinimoKg) {
    }
}
