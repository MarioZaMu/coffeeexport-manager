package co.ritech.coffeeexport.clientes;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record ClienteRequest(
        @NotBlank(message = "El nombre es obligatorio") String nombre,
        @NotBlank(message = "Seleccione un país perteneciente a la Unión Europea") String pais,
        @NotBlank(message = "La identificación fiscal es obligatoria") String identificacionFiscal,
        @NotBlank(message = "La persona de contacto es obligatoria") String contactoNombre,
        @NotBlank(message = "El correo de contacto es obligatorio") @Email(message = "Ingrese un correo de contacto válido") String contactoEmail,
        String contactoTelefono,
        String direccion,
        Boolean consentimientoDatos) {
}
