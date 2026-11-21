package co.ritech.coffeeexport.productos;

import java.math.BigDecimal;

public record ProductoDto(Long id, String codigo, String nombre, String tipo, String variedad, BigDecimal precioUsdKg, boolean activo) {
    public static ProductoDto de(Producto p) {
        return new ProductoDto(p.getId(), p.getCodigo(), p.getNombre(), p.getTipo().name(), p.getVariedad(), p.getPrecioUsdKg(), p.isActivo());
    }
}
