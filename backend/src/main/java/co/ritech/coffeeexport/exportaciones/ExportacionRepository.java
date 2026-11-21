package co.ritech.coffeeexport.exportaciones;

import java.time.LocalDate;
import java.util.Collection;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ExportacionRepository extends JpaRepository<Exportacion, Long> {

    List<Exportacion> findAllByOrderByIdDesc();

    @Query("""
            select e from Exportacion e
            where e.fechaEnvio between :desde and :hasta and e.estado not in :excluidos
            order by e.fechaEnvio, e.id
            """)
    List<Exportacion> enRango(@Param("desde") LocalDate desde, @Param("hasta") LocalDate hasta,
                              @Param("excluidos") Collection<EstadoExportacion> excluidos);
}
