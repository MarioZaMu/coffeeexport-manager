package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.Fixtures;
import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.pagos.*;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class PagoServiceTest {
    @Mock PagoRepository pagos;
    @Mock ExportacionRepository exportaciones;
    PagoService service;
    final Usuario contador = Fixtures.usuario(5L, "contador@ritech.co", "x", "CONTADOR", true);
    Exportacion ex;

    @BeforeEach
    void preparar() {
        service = new PagoService(pagos, exportaciones, new BigDecimal("1.08"));
        ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), contador, LocalDate.now());
        ex.setEstado(EstadoExportacion.EN_TRANSITO);
        ex.agregarDetalle(Fixtures.detalle(Fixtures.producto(1L, "Café", "5"), "200", "5.00"));   // total 1.000 USD
    }

    private PagoRequest peticion(String moneda, String monto) {
        return new PagoRequest(1L, monto == null ? null : new BigDecimal(monto), moneda, "TRANSFERENCIA", "TRX-1", LocalDate.now());
    }

    @Test
    @DisplayName("QA017 [HU-16][RR-07] Rechazar un pago en una moneda no soportada")
    void qa017() {
        assertThatThrownBy(() -> service.registrarPago(peticion("COP", "1000"), contador))
                .isInstanceOf(ReglaNegocioException.class).hasMessage("Moneda no soportada: solo USD o EUR");
        verify(pagos, never()).save(any());
    }

    @Test
    @DisplayName("[HU-16][RF-23] Un pago válido en USD queda PENDIENTE; un monto cero se rechaza")
    void pagoValido() {
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        when(pagos.save(any(Pago.class))).thenAnswer(i -> i.getArgument(0));
        Pago p = service.registrarPago(peticion("usd", "5000"), contador);
        assertThat(p.getEstado()).isEqualTo(EstadoPago.PENDIENTE);
        assertThat(p.getMoneda()).isEqualTo(Moneda.USD);
        assertThat(p.getMonto()).isEqualByComparingTo("5000.00");
        assertThatThrownBy(() -> service.registrarPago(peticion("USD", "0"), contador)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("mayor que cero");
    }

    @Test
    @DisplayName("[HU-16][RF-23] No se registran pagos de una exportación en borrador")
    void soloConfirmadas() {
        ex.setEstado(EstadoExportacion.BORRADOR);
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        assertThatThrownBy(() -> service.registrarPago(peticion("USD", "10"), contador)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("confirmadas");
    }

    @Test
    @DisplayName("[HU-17][RF-24][RF-25] El saldo descuenta solo pagos confirmados y convierte EUR con la tasa")
    void saldo() {
        Pago confirmado = pago(EstadoPago.CONFIRMADO, Moneda.EUR, "500");     // 500 EUR × 1,08 = 540 USD
        Pago pendiente = pago(EstadoPago.PENDIENTE, Moneda.USD, "300");       // no cuenta
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        when(pagos.findByExportacionId(1L)).thenReturn(List.of(confirmado, pendiente));
        assertThat(service.saldoPendiente(1L)).isEqualByComparingTo("460.00");
    }

    @Test
    @DisplayName("[HU-17][RF-25] Solo se confirman o rechazan pagos pendientes")
    void confirmarSoloPendientes() {
        Pago p = pago(EstadoPago.PENDIENTE, Moneda.USD, "100");
        when(pagos.findById(9L)).thenReturn(Optional.of(p));
        when(pagos.save(any(Pago.class))).thenAnswer(i -> i.getArgument(0));
        assertThat(service.confirmar(9L).getEstado()).isEqualTo(EstadoPago.CONFIRMADO);
        assertThatThrownBy(() -> service.rechazar(9L)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("pendientes");
    }

    private Pago pago(EstadoPago estado, Moneda moneda, String monto) {
        Pago p = new Pago();
        p.setExportacion(ex);
        p.setEstado(estado);
        p.setMoneda(moneda);
        p.setMonto(new BigDecimal(monto));
        return p;
    }
}
