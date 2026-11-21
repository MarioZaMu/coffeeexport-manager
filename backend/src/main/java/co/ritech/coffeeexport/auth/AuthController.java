package co.ritech.coffeeexport.auth;

import co.ritech.coffeeexport.usuarios.Usuario;
import co.ritech.coffeeexport.usuarios.UsuarioDto;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.web.bind.annotation.*;

/** Inicio y cierre de sesión por cookie de sesión HttpOnly (RF-01, RF-02, RNF-02). */
@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthService service;

    public AuthController(AuthService service) {
        this.service = service;
    }

    @PostMapping("/login")
    public UsuarioDto login(@Valid @RequestBody LoginRequest r, HttpServletRequest request, HttpServletResponse response) {
        Usuario u = service.autenticar(r.email(), r.password());
        request.getSession(true);
        request.changeSessionId();   // evita fijación de sesión
        Authentication auth = new UsernamePasswordAuthenticationToken(u.getEmail(), null,
                List.of(new SimpleGrantedAuthority("ROLE_" + u.getRol().getNombre())));
        SecurityContext contexto = SecurityContextHolder.createEmptyContext();
        contexto.setAuthentication(auth);
        SecurityContextHolder.setContext(contexto);
        new HttpSessionSecurityContextRepository().saveContext(contexto, request, response);
        return UsuarioDto.de(u);
    }

    @PostMapping("/logout")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void logout(HttpServletRequest request) {
        HttpSession sesion = request.getSession(false);
        if (sesion != null) {
            sesion.invalidate();
        }
        SecurityContextHolder.clearContext();
    }

    @GetMapping("/me")
    public UsuarioDto me(Authentication authentication) {
        return UsuarioDto.de(service.actual(authentication));
    }
}
