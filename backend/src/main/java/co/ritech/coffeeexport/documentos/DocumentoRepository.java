package co.ritech.coffeeexport.documentos;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DocumentoRepository extends JpaRepository<Documento, Long> {
    List<Documento> findAllByOrderByIdDesc();

    List<Documento> findByExportacionIdOrderByIdDesc(Long exportacionId);
}
