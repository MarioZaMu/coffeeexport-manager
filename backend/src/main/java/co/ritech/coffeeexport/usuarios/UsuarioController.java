package co.ritech.coffeeexport.usuarios;

import co.ritech.coffeeexport.auth.AuthService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

/** Solo el administrador (matriz de permisos en SecurityConfig). */
@RestController
@RequestMapping("/api/usuarios")
public class UsuarioController {
    private final UsuarioService service;
    private final AuthService auth;

    public UsuarioController(UsuarioService service, AuthService auth) {
        this.service = service;
        this.auth = auth;
    }

    @GetMapping
    public List<UsuarioDto> listar() {
        return service.listar().stream().map(UsuarioDto::de).toList();
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UsuarioDto crear(@Valid @RequestBody UsuarioRequest r) {
        return UsuarioDto.de(service.crearUsuario(r));
    }

    @PutMapping("/{id}")
    public UsuarioDto actualizar(@PathVariable Long id, @Valid @RequestBody UsuarioRequest r, Authentication a) {
        return UsuarioDto.de(service.actualizarUsuario(id, r, auth.actual(a).getId()));
    }
}
