package co.ritech.coffeeexport.auth;

import jakarta.validation.constraints.NotBlank;

public record LoginRequest(
        @NotBlank(message = "Ingrese su correo") String email,
        @NotBlank(message = "Ingrese su contraseña") String password) {
}
