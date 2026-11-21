package co.ritech.coffeeexport.shared;

import java.util.Map;

/** Cuerpo estándar de error de la API. {@code campos} se llena en errores de validación por campo. */
public record ApiError(String error, Map<String, String> campos) {
    public static ApiError de(String mensaje) {
        return new ApiError(mensaje, Map.of());
    }
}
