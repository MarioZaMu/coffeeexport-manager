package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import co.ritech.coffeeexport.Fixtures;
import co.ritech.coffeeexport.auth.AuthService;
import co.ritech.coffeeexport.usuarios.Usuario;
import co.ritech.coffeeexport.usuarios.UsuarioRepository;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {
    @Mock UsuarioRepository usuarios;
    final PasswordEncoder encoder = new BCryptPasswordEncoder(4);
    AuthService service;

    @BeforeEach
    void preparar() {
        service = new AuthService(usuarios, encoder);
    }

    @Test
    @DisplayName("QA001 [HU-01][RF-01] Autenticar a un usuario activo con credenciales válidas")
    void qa001() {
        Usuario u = Fixtures.usuario(1L, "admin@ritech.co", encoder.encode("Demo2026*"), "ADMIN", true);
        when(usuarios.findByEmailIgnoreCase("admin@ritech.co")).thenReturn(Optional.of(u));
        Usuario r = service.autenticar("admin@ritech.co", "Demo2026*");
        assertThat(r.getRol().getNombre()).isEqualTo("ADMIN");
        assertThat(r.getUltimoAcceso()).isNotNull();
    }

    @Test
    @DisplayName("QA003 [HU-01][RF-01] Rechazar la autenticación con contraseña incorrecta")
    void qa003() {
        Usuario u = Fixtures.usuario(1L, "admin@ritech.co", encoder.encode("Demo2026*"), "ADMIN", true);
        when(usuarios.findByEmailIgnoreCase("admin@ritech.co")).thenReturn(Optional.of(u));
        assertThatThrownBy(() -> service.autenticar("admin@ritech.co", "incorrecta"))
                .isInstanceOf(BadCredentialsException.class).hasMessage("Credenciales incorrectas");
        assertThat(u.getUltimoAcceso()).isNull();
    }

    @Test
    @DisplayName("QA004 [HU-01][RF-01] Rechazar la autenticación de un usuario inactivo")
    void qa004() {
        Usuario u = Fixtures.usuario(2L, "baja@ritech.co", encoder.encode("Demo2026*"), "OP_BODEGA", false);
        when(usuarios.findByEmailIgnoreCase("baja@ritech.co")).thenReturn(Optional.of(u));
        assertThatThrownBy(() -> service.autenticar("baja@ritech.co", "Demo2026*")).isInstanceOf(DisabledException.class);
        assertThat(u.getUltimoAcceso()).isNull();
    }

    @Test
    @DisplayName("[HU-01][RNF-04] Un correo inexistente da el mismo mensaje genérico que una contraseña mala")
    void correoInexistente() {
        when(usuarios.findByEmailIgnoreCase("nadie@ritech.co")).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.autenticar("nadie@ritech.co", "x")).isInstanceOf(BadCredentialsException.class).hasMessage("Credenciales incorrectas");
    }
}
