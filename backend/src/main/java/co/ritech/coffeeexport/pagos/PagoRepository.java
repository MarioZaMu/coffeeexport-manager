package co.ritech.coffeeexport.pagos;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PagoRepository extends JpaRepository<Pago, Long> {
    List<Pago> findAllByOrderByIdDesc();

    List<Pago> findByExportacionId(Long exportacionId);
}
