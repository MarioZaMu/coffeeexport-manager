package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyCollection;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.inventario.InventarioRepository;
import co.ritech.coffeeexport.reportes.ReporteDto;
import co.ritech.coffeeexport.reportes.ReporteService;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ReporteServiceTest {
    @Mock ExportacionRepository exportaciones;
    @Mock InventarioRepository inventario;
    ReporteService service;

    @BeforeEach
    void preparar() {
        service = new ReporteService(exportaciones, inventario);
    }

    @Test
    @DisplayName("QA018 [HU-18][RF-26] Rechazar un reporte cuya fecha final es anterior a la inicial")
    void qa018() {
        assertThatThrownBy(() -> service.generarReporte(LocalDate.of(2026, 9, 30), LocalDate.of(2026, 9, 1), "exportaciones"))
                .isInstanceOf(IllegalArgumentException.class).hasMessage("La fecha final no puede ser anterior a la fecha inicial");
        verifyNoInteractions(exportaciones);
    }

    @Test
    @DisplayName("[HU-18][RF-26] Un rango sin exportaciones devuelve un reporte vacío con ceros")
    void rangoVacio() {
        when(exportaciones.enRango(any(), any(), anyCollection())).thenReturn(List.of());
        ReporteDto r = service.generarReporte(LocalDate.of(2026, 1, 1), LocalDate.of(2026, 1, 31), null);
        assertThat(r.totalExportaciones()).isZero();
        assertThat(r.ventasUsd()).isEqualByComparingTo("0");
        assertThat(r.filas()).isEmpty();
        assertThat(r.tipo()).isEqualTo("exportaciones");
    }

    @Test
    @DisplayName("[HU-18][RF-26] Fechas ausentes o tipo de reporte inválido se rechazan")
    void parametrosInvalidos() {
        assertThatThrownBy(() -> service.generarReporte(null, LocalDate.now(), "ventas")).hasMessageContaining("rango de fechas");
        assertThatThrownBy(() -> service.generarReporte(LocalDate.now(), LocalDate.now(), "otro")).hasMessageContaining("Tipo de reporte no válido");
    }
}
