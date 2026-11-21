package co.ritech.coffeeexport.clientes;

import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ClienteRepository extends JpaRepository<Cliente, Long> {

    List<Cliente> findByPais(String pais);

    Optional<Cliente> findByIdentificacionFiscalIgnoreCase(String identificacionFiscal);

    boolean existsByIdentificacionFiscalIgnoreCase(String identificacionFiscal);

    long countByActivoTrue();

    /** Búsqueda parametrizada (RNF-04): ningún valor se concatena en la consulta. */
    @Query("""
            select c from Cliente c
            where (:q is null or lower(c.nombre) like lower(concat('%', :q, '%'))
                   or lower(c.identificacionFiscal) like lower(concat('%', :q, '%'))
                   or lower(c.contactoEmail) like lower(concat('%', :q, '%'))
                   or lower(c.contactoNombre) like lower(concat('%', :q, '%')))
              and (:pais is null or c.pais = :pais)
              and (:activo is null or c.activo = :activo)
            order by c.id
            """)
    List<Cliente> buscar(@Param("q") String q, @Param("pais") String pais, @Param("activo") Boolean activo);
}
