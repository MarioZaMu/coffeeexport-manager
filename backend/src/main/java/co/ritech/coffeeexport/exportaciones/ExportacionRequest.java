package co.ritech.coffeeexport.exportaciones;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

/** Datos del asistente de 4 pasos (RF-16): básica, cliente y destino, productos y documentos. */
public record ExportacionRequest(
        @NotNull(message = "Seleccione un cliente") Long clienteId,
        @NotBlank(message = "Seleccione el país destino") String paisDestino,
        @NotBlank(message = "Seleccione el puerto de salida") String puertoSalida,
        @NotBlank(message = "Seleccione el puerto de llegada") String puertoLlegada,
        @NotNull(message = "La fecha de envío es obligatoria") LocalDate fechaEnvio,
        String estadoInicial,
        String observaciones,
        @NotEmpty(message = "Agregue al menos un producto") @Valid List<Linea> lineas) {

    public record Linea(
            @NotNull(message = "Seleccione un producto") Long productoId,
            @NotNull(message = "Ingrese la cantidad") BigDecimal cantidadKg,
            @NotNull(message = "Ingrese el precio") BigDecimal precioUnitario) {
    }
}
