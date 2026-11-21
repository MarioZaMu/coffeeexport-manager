package co.ritech.coffeeexport.exportaciones;

import co.ritech.coffeeexport.auth.AuthService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/exportaciones")
public class ExportacionController {
    private final ExportacionService service;
    private final AuthService auth;

    public ExportacionController(ExportacionService service, AuthService auth) {
        this.service = service;
        this.auth = auth;
    }

    @GetMapping
    public List<ExportacionDto> listar(@RequestParam(required = false) String q, @RequestParam(required = false) String estado) {
        return service.listar(q, estado).stream().map(ExportacionDto::de).toList();
    }

    @GetMapping("/{id}")
    public ExportacionDto obtener(@PathVariable Long id) {
        return ExportacionDto.de(service.obtener(id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ExportacionDto crear(@Valid @RequestBody ExportacionRequest r, Authentication a) {
        return ExportacionDto.de(service.crearExportacion(r, auth.actual(a)));
    }

    @PatchMapping("/{id}/estado")
    public ExportacionDto estado(@PathVariable Long id, @Valid @RequestBody EstadoExportacionRequest r, Authentication a) {
        return ExportacionDto.de(service.cambiarEstado(id, ExportacionService.parsear(r.estado()), auth.actual(a)));
    }
}
