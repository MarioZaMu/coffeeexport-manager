package co.ritech.coffeeexport.clientes;

import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/clientes")
public class ClienteController {
    private final ClienteService service;

    public ClienteController(ClienteService service) {
        this.service = service;
    }

    @GetMapping
    public List<ClienteDto> listar(@RequestParam(required = false) String q, @RequestParam(required = false) String pais,
                                   @RequestParam(required = false) Boolean activo) {
        return service.buscar(q, pais, activo).stream().map(ClienteDto::de).toList();
    }

    @GetMapping("/{id}")
    public ClienteDto obtener(@PathVariable Long id) {
        return ClienteDto.de(service.obtener(id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ClienteDto crear(@Valid @RequestBody ClienteRequest r) {
        return ClienteDto.de(service.registrarCliente(r));
    }

    @PutMapping("/{id}")
    public ClienteDto actualizar(@PathVariable Long id, @Valid @RequestBody ClienteRequest r) {
        return ClienteDto.de(service.actualizarCliente(id, r));
    }

    @PatchMapping("/{id}/estado")
    public ClienteDto estado(@PathVariable Long id, @RequestBody EstadoRequest r) {
        return ClienteDto.de(service.cambiarEstado(id, r.activo()));
    }
}
