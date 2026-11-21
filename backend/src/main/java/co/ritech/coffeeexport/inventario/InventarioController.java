package co.ritech.coffeeexport.inventario;

import co.ritech.coffeeexport.auth.AuthService;
import co.ritech.coffeeexport.inventario.InventarioDtos.*;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/inventario")
public class InventarioController {
    private final InventarioService service;
    private final AuthService auth;

    public InventarioController(InventarioService service, AuthService auth) {
        this.service = service;
        this.auth = auth;
    }

    @GetMapping
    public List<InventarioDto> consultar(@RequestParam(required = false) Long productoId) {
        return service.listar(productoId).stream().map(InventarioDto::de).toList();
    }

    @GetMapping("/stock/{productoId}")
    public StockDto stock(@PathVariable Long productoId) {
        return service.consultarStock(productoId);
    }

    @GetMapping("/bodegas")
    public List<Bodega> bodegas() {
        return service.listarBodegas();
    }

    @GetMapping("/movimientos")
    public List<MovimientoDto> movimientos() {
        return service.listarMovimientos().stream().map(MovimientoDto::de).toList();
    }

    @PostMapping("/movimientos")
    @ResponseStatus(HttpStatus.CREATED)
    public MovimientoDto registrarMovimiento(@Valid @RequestBody MovimientoRequest r, Authentication a) {
        return MovimientoDto.de(service.registrarMovimiento(r, auth.actual(a)));
    }

    @PatchMapping("/{id}/minimo")
    public InventarioDto minimo(@PathVariable Long id, @RequestBody MinimoRequest r) {
        return InventarioDto.de(service.actualizarMinimo(id, r.stockMinimoKg()));
    }
}
