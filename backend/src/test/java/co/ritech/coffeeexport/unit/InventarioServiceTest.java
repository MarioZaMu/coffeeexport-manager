package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.Fixtures;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.inventario.*;
import co.ritech.coffeeexport.inventario.InventarioDtos.StockDto;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.ProductoRepository;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.shared.StockInsuficienteException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class InventarioServiceTest {
    @Mock InventarioRepository inventarios;
    @Mock MovimientoInventarioRepository movimientos;
    @Mock ProductoRepository productos;
    @Mock BodegaRepository bodegas;
    InventarioService service;
    final Usuario usuario = Fixtures.usuario(1L, "bodega@ritech.co", "x", "OP_BODEGA", true);
    final Producto cafe = Fixtures.producto(1L, "Café Arábica", "4.50");
    final Bodega b1 = Fixtures.bodega(1L, "Bodega Cartagena"), b2 = Fixtures.bodega(2L, "Bodega Bogotá");

    @BeforeEach
    void preparar() {
        service = new InventarioService(inventarios, movimientos, productos, bodegas);
    }

    @Test
    @DisplayName("QA012 [HU-04][RF-12] Consultar el stock total de un producto sumando sus bodegas")
    void qa012() {
        when(inventarios.findByProductoId(1L)).thenReturn(List.of(Fixtures.inventario(1L, cafe, b1, "100"), Fixtures.inventario(2L, cafe, b2, "50")));
        StockDto s = service.consultarStock(1L);
        assertThat(s.totalKg()).isEqualByComparingTo("150");
        assertThat(s.bodegas()).hasSize(2);
    }

    @Test
    @DisplayName("QA013 [HU-04][RF-13] Registrar una entrada de inventario")
    void qa013() {
        Inventario inv = Fixtures.inventario(1L, cafe, b1, "100");
        when(inventarios.findByProductoIdAndBodegaId(1L, 1L)).thenReturn(Optional.of(inv));
        when(movimientos.save(any(MovimientoInventario.class))).thenAnswer(i -> i.getArgument(0));

        service.registrarEntrada(1L, 1L, new BigDecimal("50"), "Compra", usuario);

        assertThat(inv.getCantidadKg()).isEqualByComparingTo("150");
        ArgumentCaptor<MovimientoInventario> m = ArgumentCaptor.forClass(MovimientoInventario.class);
        verify(movimientos).save(m.capture());
        assertThat(m.getValue().getTipo()).isEqualTo(TipoMovimiento.ENTRADA);
        assertThat(m.getValue().getCantidadKg()).isEqualByComparingTo("50");
        assertThat(m.getValue().getUsuario()).isSameAs(usuario);
    }

    @Test
    @DisplayName("QA014 [HU-04][RF-14] Rechazar una salida mayor al stock disponible")
    void qa014() {
        Inventario inv = Fixtures.inventario(1L, cafe, b1, "100");
        when(inventarios.findByProductoIdAndBodegaId(1L, 1L)).thenReturn(Optional.of(inv));
        assertThatThrownBy(() -> service.registrarSalida(1L, 1L, new BigDecimal("150"), "x", usuario))
                .isInstanceOf(StockInsuficienteException.class).hasMessage("Stock insuficiente: disponible 100 kg en esa bodega.");
        assertThat(inv.getCantidadKg()).isEqualByComparingTo("100");
        verify(movimientos, never()).save(any());
    }

    @Test
    @DisplayName("[HU-04][RF-13] Cantidades cero, negativas o nulas se rechazan en entradas y salidas")
    void cantidadesInvalidas() {
        for (BigDecimal kg : new BigDecimal[]{BigDecimal.ZERO, new BigDecimal("-5"), null}) {
            assertThatThrownBy(() -> service.registrarEntrada(1L, 1L, kg, "x", usuario)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("mayor que cero");
            assertThatThrownBy(() -> service.registrarSalida(1L, 1L, kg, "x", usuario)).isInstanceOf(ReglaNegocioException.class);
        }
        verify(movimientos, never()).save(any());
    }

    @Test
    @DisplayName("[HU-04][RF-13] Un ajuste fija el stock al valor indicado")
    void ajuste() {
        Inventario inv = Fixtures.inventario(1L, cafe, b1, "100");
        when(inventarios.findByProductoIdAndBodegaId(1L, 1L)).thenReturn(Optional.of(inv));
        when(movimientos.save(any(MovimientoInventario.class))).thenAnswer(i -> i.getArgument(0));
        service.ajustar(1L, 1L, new BigDecimal("80"), "Conteo físico", usuario);
        assertThat(inv.getCantidadKg()).isEqualByComparingTo("80");
    }

    @Test
    @DisplayName("[HU-11][RF-19] Descontar una exportación reparte entre bodegas, de la de mayor stock a la menor")
    void descuentoRepartido() {
        Inventario i1 = Fixtures.inventario(1L, cafe, b1, "1500"), i2 = Fixtures.inventario(2L, cafe, b2, "1000");
        when(inventarios.findByProductoId(1L)).thenReturn(List.of(i1, i2));
        when(movimientos.save(any(MovimientoInventario.class))).thenAnswer(i -> i.getArgument(0));
        Exportacion ex = unaExportacion("1800");

        service.descontarParaExportacion(ex, usuario);

        assertThat(i1.getCantidadKg()).isEqualByComparingTo("0");       // primero la bodega con más stock
        assertThat(i2.getCantidadKg()).isEqualByComparingTo("700");
        verify(movimientos, times(2)).save(any(MovimientoInventario.class));
    }

    @Test
    @DisplayName("[HU-11][RF-19] Con stock insuficiente el descuento falla y NO mueve nada (atómico)")
    void descuentoAtomico() {
        Inventario i1 = Fixtures.inventario(1L, cafe, b1, "1500"), i2 = Fixtures.inventario(2L, cafe, b2, "1000");
        when(inventarios.findByProductoId(1L)).thenReturn(List.of(i1, i2));
        when(productos.findById(1L)).thenReturn(Optional.of(cafe));
        Exportacion ex = unaExportacion("3000");

        assertThatThrownBy(() -> service.descontarParaExportacion(ex, usuario))
                .isInstanceOf(StockInsuficienteException.class)
                .hasMessage("Stock insuficiente de Café Arábica: solicitado 3.000 kg, disponible 2.500 kg");
        assertThat(i1.getCantidadKg()).isEqualByComparingTo("1500");
        assertThat(i2.getCantidadKg()).isEqualByComparingTo("1000");
        verify(inventarios, never()).save(any());
        verify(movimientos, never()).save(any());
    }

    private Exportacion unaExportacion(String kg) {
        Exportacion ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), usuario, LocalDate.now());
        ex.agregarDetalle(Fixtures.detalle(cafe, kg, "4.50"));
        return ex;
    }
}
