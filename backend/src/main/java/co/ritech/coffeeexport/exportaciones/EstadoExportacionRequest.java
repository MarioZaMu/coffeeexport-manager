package co.ritech.coffeeexport.exportaciones;

import jakarta.validation.constraints.NotBlank;

public record EstadoExportacionRequest(@NotBlank(message = "Indique el nuevo estado") String estado) {
}
