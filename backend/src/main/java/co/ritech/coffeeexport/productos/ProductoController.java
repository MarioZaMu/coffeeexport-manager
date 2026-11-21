package co.ritech.coffeeexport.productos;

import co.ritech.coffeeexport.clientes.EstadoRequest;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/productos")
public class ProductoController {
    private final ProductoService service;

    public ProductoController(ProductoService service) {
        this.service = service;
    }

    @GetMapping
    public List<ProductoDto> listar(@RequestParam(required = false) String q, @RequestParam(required = false) String tipo,
                                    @RequestParam(required = false) Boolean activo) {
        return service.buscar(q, tipo, activo).stream().map(ProductoDto::de).toList();
    }

    @GetMapping("/{id}")
    public ProductoDto obtener(@PathVariable Long id) {
        return ProductoDto.de(service.obtener(id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ProductoDto crear(@Valid @RequestBody ProductoRequest r) {
        return ProductoDto.de(service.crearProducto(r));
    }

    @PutMapping("/{id}")
    public ProductoDto actualizar(@PathVariable Long id, @Valid @RequestBody ProductoRequest r) {
        return ProductoDto.de(service.actualizarProducto(id, r));
    }

    @PatchMapping("/{id}/estado")
    public ProductoDto estado(@PathVariable Long id, @RequestBody EstadoRequest r) {
        return ProductoDto.de(service.cambiarEstado(id, r.activo()));
    }
}
