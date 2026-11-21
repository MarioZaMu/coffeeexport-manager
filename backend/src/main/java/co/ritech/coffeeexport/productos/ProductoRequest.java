package co.ritech.coffeeexport.productos;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

public record ProductoRequest(
        @NotBlank(message = "El código es obligatorio") String codigo,
        @NotBlank(message = "El nombre es obligatorio") String nombre,
        @NotBlank(message = "El tipo es obligatorio") String tipo,
        String variedad,
        @NotNull(message = "El precio es obligatorio") BigDecimal precioUsdKg) {
}
