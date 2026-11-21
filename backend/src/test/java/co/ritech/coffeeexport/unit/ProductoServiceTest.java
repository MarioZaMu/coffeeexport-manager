package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.productos.*;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.math.BigDecimal;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ProductoServiceTest {
    @Mock ProductoRepository repo;
    ProductoService service;

    @BeforeEach
    void preparar() {
        service = new ProductoService(repo);
    }

    @Test
    @DisplayName("QA009 [HU-03][RF-09] Registrar un producto de café válido")
    void qa009() {
        when(repo.existsByCodigoIgnoreCase("CAF-CAS-01")).thenReturn(false);
        when(repo.save(any(Producto.class))).thenAnswer(i -> {
            Producto p = i.getArgument(0);
            p.setId(3L);
            return p;
        });
        Producto p = service.crearProducto(new ProductoRequest("CAF-CAS-01", "Café Castillo", "CAFE", "Castillo", new BigDecimal("4.5")));
        assertThat(p.getId()).isEqualTo(3L);
        assertThat(p.isActivo()).isTrue();
        assertThat(p.getTipo()).isEqualTo(TipoProducto.CAFE);
        assertThat(p.getPrecioUsdKg()).isEqualByComparingTo("4.50");
    }

    @Test
    @DisplayName("QA010 [HU-03][RF-09] Rechazar un producto con precio negativo o cero")
    void qa010() {
        assertThatThrownBy(() -> service.crearProducto(new ProductoRequest("X-1", "Malo", "CAFE", null, new BigDecimal("-5.00"))))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("precio debe ser mayor que cero");
        assertThatThrownBy(() -> service.crearProducto(new ProductoRequest("X-2", "Cero", "CAFE", null, BigDecimal.ZERO)))
                .isInstanceOf(ReglaNegocioException.class);
        verify(repo, never()).save(any());
    }

    @Test
    @DisplayName("[HU-03][RF-09] Tipo de producto inválido y código repetido se rechazan")
    void tipoYCodigo() {
        assertThatThrownBy(() -> service.crearProducto(new ProductoRequest("X-3", "Té", "TE", null, BigDecimal.ONE)))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("CAFE o CACAO");
        when(repo.existsByCodigoIgnoreCase("DUP-1")).thenReturn(true);
        assertThatThrownBy(() -> service.crearProducto(new ProductoRequest("DUP-1", "Dup", "CACAO", null, BigDecimal.ONE)))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("código");
    }
}
