package co.ritech.coffeeexport.usuarios;

import java.util.List;

/** Vista pública del usuario: sin hash de contraseña. */
public record UsuarioDto(Long id, String nombre, String email, String rol, boolean activo, List<String> permisos) {
    public static UsuarioDto de(Usuario u) {
        return new UsuarioDto(u.getId(), u.getNombre(), u.getEmail(), u.getRol().getNombre(), u.isActivo(),
                u.getRol().getPermisos().stream().map(Permiso::getCodigo).sorted().toList());
    }
}
