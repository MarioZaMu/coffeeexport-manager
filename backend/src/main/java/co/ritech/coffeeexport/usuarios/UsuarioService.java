package co.ritech.coffeeexport.usuarios;

import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.util.List;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Gestión de usuarios y roles (HU-05, RF-03, RF-04). */
@Service
public class UsuarioService {
    static final int LARGO_MINIMO_CLAVE = 8;

    private final UsuarioRepository usuarios;
    private final RolRepository roles;
    private final PasswordEncoder encoder;

    public UsuarioService(UsuarioRepository usuarios, RolRepository roles, PasswordEncoder encoder) {
        this.usuarios = usuarios;
        this.roles = roles;
        this.encoder = encoder;
    }

    /** RNF-01: la contraseña se guarda únicamente como hash BCrypt. */
    @Transactional
    public Usuario crearUsuario(UsuarioRequest r) {
        if (r.password() == null || r.password().length() < LARGO_MINIMO_CLAVE) {
            throw new ReglaNegocioException("La contraseña debe tener al menos " + LARGO_MINIMO_CLAVE + " caracteres");
        }
        if (usuarios.existsByEmailIgnoreCase(r.email())) {
            throw new ReglaNegocioException("Ya existe un usuario con ese correo");
        }
        Usuario u = new Usuario();
        u.setNombre(r.nombre().trim());
        u.setEmail(r.email().trim().toLowerCase());
        u.setPasswordHash(encoder.encode(r.password()));
        u.setRol(rolDe(r.rol()));
        u.setActivo(r.activo() == null || r.activo());
        return usuarios.save(u);
    }

    @Transactional
    public Usuario actualizarUsuario(Long id, UsuarioRequest r, Long idActor) {
        Usuario u = obtener(id);
        usuarios.findByEmailIgnoreCase(r.email()).filter(o -> !o.getId().equals(id)).ifPresent(o -> {
            throw new ReglaNegocioException("Ya existe un usuario con ese correo");
        });
        boolean activo = r.activo() == null || r.activo();
        if (id.equals(idActor) && (!activo || !"ADMIN".equals(r.rol()))) {
            throw new ReglaNegocioException("No puede desactivarse ni quitarse el rol de administrador a sí mismo");
        }
        u.setNombre(r.nombre().trim());
        u.setEmail(r.email().trim().toLowerCase());
        u.setRol(rolDe(r.rol()));
        u.setActivo(activo);
        if (r.password() != null && !r.password().isBlank()) {
            if (r.password().length() < LARGO_MINIMO_CLAVE) {
                throw new ReglaNegocioException("La contraseña debe tener al menos " + LARGO_MINIMO_CLAVE + " caracteres");
            }
            u.setPasswordHash(encoder.encode(r.password()));
        }
        return usuarios.save(u);
    }

    @Transactional(readOnly = true)
    public List<Usuario> listar() {
        return usuarios.findAll();
    }

    @Transactional(readOnly = true)
    public Usuario obtener(Long id) {
        return usuarios.findById(id).orElseThrow(() -> new RecursoNoEncontradoException("Usuario no encontrado"));
    }

    private Rol rolDe(String nombre) {
        return roles.findByNombre(nombre).orElseThrow(() -> new ReglaNegocioException("Rol no válido: " + nombre));
    }
}
