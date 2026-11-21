package co.ritech.coffeeexport.inventario;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface InventarioRepository extends JpaRepository<Inventario, Long> {

    Optional<Inventario> findByProductoIdAndBodegaId(Long productoId, Long bodegaId);

    List<Inventario> findByProductoId(Long productoId);

    List<Inventario> findAllByOrderByIdAsc();

    @Query("select coalesce(sum(i.cantidadKg), 0) from Inventario i")
    BigDecimal totalGeneral();
}
