package co.ritech.coffeeexport.exportaciones;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

public record ExportacionDto(Long id, String codigo, Long clienteId, String clienteNombre, String paisDestino, String puertoSalida,
                             String puertoLlegada, LocalDate fechaEnvio, String estado, Long creadorId, String observaciones,
                             boolean descontado, LocalDateTime createdAt, BigDecimal totalUsd, BigDecimal totalKg, List<LineaDto> lineas) {

    public record LineaDto(Long productoId, String productoNombre, BigDecimal cantidadKg, BigDecimal precioUnitario, BigDecimal subtotal) {
    }

    public static ExportacionDto de(Exportacion e) {
        List<LineaDto> lineas = e.getDetalles().stream().map(d -> new LineaDto(d.getProducto().getId(), d.getProducto().getNombre(),
                d.getCantidadKg(), d.getPrecioUnitario(), d.getSubtotal())).toList();
        return new ExportacionDto(e.getId(), e.getCodigo(), e.getCliente().getId(), e.getCliente().getNombre(), e.getPaisDestino(),
                e.getPuertoSalida(), e.getPuertoLlegada(), e.getFechaEnvio(), e.getEstado().name(), e.getUsuarioCreador().getId(),
                e.getObservaciones(), e.isDescontado(), e.getCreatedAt(), e.getTotalUsd(), e.getTotalKg(), lineas);
    }
}
