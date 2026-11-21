package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.*;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class UsuarioServiceTest {
    @Mock UsuarioRepository usuarios;
    @Mock RolRepository roles;
    final PasswordEncoder encoder = new BCryptPasswordEncoder(4);
    UsuarioService service;

    @BeforeEach
    void preparar() {
        service = new UsuarioService(usuarios, roles, encoder);
    }

    @Test
    @DisplayName("QA002 [HU-01][RNF-01] La contraseña se guarda cifrada con BCrypt y no en texto plano")
    void qa002() {
        when(usuarios.existsByEmailIgnoreCase("ana@ritech.co")).thenReturn(false);
        when(roles.findByNombre("OP_BODEGA")).thenReturn(Optional.of(new Rol("OP_BODEGA", "Bodega")));
        when(usuarios.save(any(Usuario.class))).thenAnswer(i -> i.getArgument(0));

        service.crearUsuario(new UsuarioRequest("Ana", "ana@ritech.co", "Cafe2026*", "OP_BODEGA", true));

        ArgumentCaptor<Usuario> guardado = ArgumentCaptor.forClass(Usuario.class);
        verify(usuarios).save(guardado.capture());
        String hash = guardado.getValue().getPasswordHash();
        assertThat(hash).isNotEqualTo("Cafe2026*").matches("^\\$2[aby]\\$.{56}$");
        assertThat(encoder.matches("Cafe2026*", hash)).isTrue();
    }

    @Test
    @DisplayName("[HU-05][RF-03] No se crean usuarios con correo repetido ni contraseña corta")
    void validaciones() {
        when(usuarios.existsByEmailIgnoreCase("repetido@ritech.co")).thenReturn(true);
        assertThatThrownBy(() -> service.crearUsuario(new UsuarioRequest("X", "repetido@ritech.co", "Cafe2026*", "ADMIN", true)))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("Ya existe un usuario con ese correo");
        assertThatThrownBy(() -> service.crearUsuario(new UsuarioRequest("X", "nuevo@ritech.co", "corta", "ADMIN", true)))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("al menos 8 caracteres");
        verify(usuarios, never()).save(any());
    }

    @Test
    @DisplayName("[HU-05][RF-03] Un administrador no puede desactivarse a sí mismo")
    void noAutoDesactivar() {
        Usuario admin = new Usuario();
        admin.setId(1L);
        admin.setRol(new Rol("ADMIN", "x"));
        when(usuarios.findById(1L)).thenReturn(Optional.of(admin));
        when(usuarios.findByEmailIgnoreCase("admin@ritech.co")).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.actualizarUsuario(1L, new UsuarioRequest("Admin", "admin@ritech.co", null, "ADMIN", false), 1L))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("a sí mismo");
    }
}
