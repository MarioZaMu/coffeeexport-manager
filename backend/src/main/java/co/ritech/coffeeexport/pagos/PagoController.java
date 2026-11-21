package co.ritech.coffeeexport.pagos;

import co.ritech.coffeeexport.auth.AuthService;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/pagos")
public class PagoController {
    private final PagoService service;
    private final AuthService auth;

    public PagoController(PagoService service, AuthService auth) {
        this.service = service;
        this.auth = auth;
    }

    @GetMapping
    public List<PagoDto> listar() {
        return service.listar().stream().map(PagoDto::de).toList();
    }

    @GetMapping("/saldo/{exportacionId}")
    public Map<String, BigDecimal> saldo(@PathVariable Long exportacionId) {
        return Map.of("saldoPendienteUsd", service.saldoPendiente(exportacionId));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public PagoDto registrar(@Valid @RequestBody PagoRequest r, Authentication a) {
        return PagoDto.de(service.registrarPago(r, auth.actual(a)));
    }

    @PatchMapping("/{id}/estado")
    public PagoDto estado(@PathVariable Long id, @RequestBody Map<String, String> cuerpo) {
        String estado = String.valueOf(cuerpo.get("estado")).toUpperCase();
        return switch (estado) {
            case "CONFIRMADO" -> PagoDto.de(service.confirmar(id));
            case "RECHAZADO" -> PagoDto.de(service.rechazar(id));
            default -> throw new ReglaNegocioException("Estado de pago no válido: CONFIRMADO o RECHAZADO");
        };
    }
}
