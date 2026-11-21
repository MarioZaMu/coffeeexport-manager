package co.ritech.coffeeexport.snapshot;

import co.ritech.coffeeexport.auth.AuthService;
import java.util.Map;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Instantánea de datos con la forma que usa la interfaz (la misma de su modo demostración).
 * Solo incluye lo que el rol del usuario puede leer (RNF-03) y minimiza datos personales (GDPR, RR-05).
 */
@RestController
@RequestMapping("/api/snapshot")
public class SnapshotController {
    private final SnapshotService service;
    private final AuthService auth;

    public SnapshotController(SnapshotService service, AuthService auth) {
        this.service = service;
        this.auth = auth;
    }

    @GetMapping
    public Map<String, Object> snapshot(Authentication a) {
        return service.generar(auth.actual(a));
    }
}
