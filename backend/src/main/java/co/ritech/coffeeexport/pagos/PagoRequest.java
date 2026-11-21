package co.ritech.coffeeexport.pagos;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDate;

public record PagoRequest(
        @NotNull(message = "Seleccione una exportación") Long exportacionId,
        @NotNull(message = "Ingrese el monto") BigDecimal monto,
        @NotBlank(message = "Seleccione la moneda") String moneda,
        String metodo,
        String referencia,
        @NotNull(message = "Ingrese la fecha de pago") LocalDate fechaPago) {
}
