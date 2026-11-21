package co.ritech.coffeeexport.productos;

import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Catálogo de café y cacao (HU-03, RF-09 a RF-11). */
@Service
public class ProductoService {
    private final ProductoRepository repo;

    public ProductoService(ProductoRepository repo) {
        this.repo = repo;
    }

    @Transactional
    public Producto crearProducto(ProductoRequest r) {
        validar(r, null);
        Producto p = new Producto();
        copiar(r, p);
        p.setActivo(true);
        return repo.save(p);
    }

    @Transactional
    public Producto actualizarProducto(Long id, ProductoRequest r) {
        Producto p = obtener(id);
        validar(r, p);
        copiar(r, p);
        return repo.save(p);
    }

    /** RF-11: se desactiva sin eliminar físicamente. */
    @Transactional
    public Producto cambiarEstado(Long id, boolean activo) {
        Producto p = obtener(id);
        p.setActivo(activo);
        return repo.save(p);
    }

    @Transactional(readOnly = true)
    public List<Producto> buscar(String q, String tipo, Boolean activo) {
        String texto = q == null || q.isBlank() ? null : q.trim();
        return repo.buscar(texto, tipo == null || tipo.isBlank() ? null : parsearTipo(tipo), activo);
    }

    @Transactional(readOnly = true)
    public Producto obtener(Long id) {
        return repo.findById(id).orElseThrow(() -> new RecursoNoEncontradoException("Producto no encontrado"));
    }

    private void validar(ProductoRequest r, Producto actual) {
        if (r.precioUsdKg() == null || r.precioUsdKg().compareTo(BigDecimal.ZERO) <= 0) {
            throw new ReglaNegocioException("El precio debe ser mayor que cero");
        }
        parsearTipo(r.tipo());
        boolean cambiaCodigo = actual == null || !actual.getCodigo().equalsIgnoreCase(r.codigo().trim());
        if (cambiaCodigo && repo.existsByCodigoIgnoreCase(r.codigo().trim())) {
            throw new ReglaNegocioException("Ya existe un producto con ese código");
        }
    }

    private static TipoProducto parsearTipo(String tipo) {
        try {
            return TipoProducto.valueOf(tipo.trim().toUpperCase());
        } catch (IllegalArgumentException | NullPointerException e) {
            throw new ReglaNegocioException("Tipo de producto no válido: use CAFE o CACAO");
        }
    }

    private void copiar(ProductoRequest r, Producto p) {
        p.setCodigo(r.codigo().trim());
        p.setNombre(r.nombre().trim());
        p.setTipo(parsearTipo(r.tipo()));
        p.setVariedad(r.variedad());
        p.setPrecioUsdKg(r.precioUsdKg().setScale(2, RoundingMode.HALF_UP));
    }
}
