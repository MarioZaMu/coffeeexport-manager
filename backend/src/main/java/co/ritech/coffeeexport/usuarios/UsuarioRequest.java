package co.ritech.coffeeexport.usuarios;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record UsuarioRequest(
        @NotBlank(message = "El nombre es obligatorio") String nombre,
        @NotBlank(message = "El correo es obligatorio") @Email(message = "Ingrese un correo válido") String email,
        String password,
        @NotBlank(message = "El rol es obligatorio") String rol,
        Boolean activo) {
}
