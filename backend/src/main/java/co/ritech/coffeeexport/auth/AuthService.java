package co.ritech.coffeeexport.auth;

import co.ritech.coffeeexport.usuarios.Usuario;
import co.ritech.coffeeexport.usuarios.UsuarioRepository;
import java.time.LocalDateTime;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Autenticación de usuarios (HU-01, RF-01). */
@Service
public class AuthService {
    private final UsuarioRepository usuarios;
    private final PasswordEncoder encoder;

    public AuthService(UsuarioRepository usuarios, PasswordEncoder encoder) {
        this.usuarios = usuarios;
        this.encoder = encoder;
    }

    /**
     * Valida correo y contraseña contra el hash BCrypt.
     * El mensaje de error es genérico a propósito: no revela si falló el correo o la contraseña (UC-01 3a).
     */
    @Transactional
    public Usuario autenticar(String email, String password) {
        Usuario u = usuarios.findByEmailIgnoreCase(email == null ? "" : email.trim())
                .orElseThrow(() -> new BadCredentialsException("Credenciales incorrectas"));
        if (password == null || !encoder.matches(password, u.getPasswordHash())) {
            throw new BadCredentialsException("Credenciales incorrectas");
        }
        if (!u.isActivo()) {
            throw new DisabledException("Usuario inactivo");
        }
        u.setUltimoAcceso(LocalDateTime.now());
        return u;
    }

    /** Usuario de la sesión actual. */
    @Transactional(readOnly = true)
    public Usuario actual(Authentication authentication) {
        return usuarios.findByEmailIgnoreCase(authentication.getName())
                .orElseThrow(() -> new BadCredentialsException("Sesión no válida"));
    }
}
