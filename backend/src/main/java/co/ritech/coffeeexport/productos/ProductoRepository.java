package co.ritech.coffeeexport.productos;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ProductoRepository extends JpaRepository<Producto, Long> {

    List<Producto> findByTipo(TipoProducto tipo);

    boolean existsByCodigoIgnoreCase(String codigo);

    @Query("""
            select p from Producto p
            where (:q is null or lower(p.nombre) like lower(concat('%', :q, '%')) or lower(p.codigo) like lower(concat('%', :q, '%')))
              and (:tipo is null or p.tipo = :tipo)
              and (:activo is null or p.activo = :activo)
            order by p.id
            """)
    List<Producto> buscar(@Param("q") String q, @Param("tipo") TipoProducto tipo, @Param("activo") Boolean activo);
}
