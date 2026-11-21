package co.ritech.coffeeexport.inventario;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

public record MovimientoRequest(
        @NotNull(message = "Seleccione un producto") Long productoId,
        @NotNull(message = "Seleccione una bodega") Long bodegaId,
        @NotBlank(message = "Seleccione el tipo de movimiento") String tipo,
        @NotNull(message = "Ingrese la cantidad") BigDecimal cantidadKg,
        String motivo) {
}
