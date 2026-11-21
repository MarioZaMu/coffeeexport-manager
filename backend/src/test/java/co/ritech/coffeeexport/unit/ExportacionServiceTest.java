package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.Fixtures;
import co.ritech.coffeeexport.clientes.ClienteRepository;
import co.ritech.coffeeexport.documentos.DocumentoService;
import co.ritech.coffeeexport.documentos.TipoDocumento;
import co.ritech.coffeeexport.exportaciones.*;
import co.ritech.coffeeexport.inventario.InventarioService;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.ProductoRepository;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ExportacionServiceTest {
    @Mock ExportacionRepository exportaciones;
    @Mock ClienteRepository clientes;
    @Mock ProductoRepository productos;
    @Mock InventarioService inventario;
    @Mock DocumentoService documentos;
    ExportacionService service;
    final Usuario operador = Fixtures.usuario(3L, "exportaciones@ritech.co", "x", "OP_EXPORTACIONES", true);
    final Producto arabica = Fixtures.producto(1L, "Café Arábica", "4.50"), cacao = Fixtures.producto(2L, "Cacao en grano", "8.00");
    final LocalDate manana = LocalDate.now(ZoneId.of("America/Bogota")).plusDays(1);

    @BeforeEach
    void preparar() {
        service = new ExportacionService(exportaciones, clientes, productos, inventario, documentos);
    }

    private ExportacionRequest peticion(String estadoInicial) {
        return new ExportacionRequest(1L, "DE", "Cartagena", "Hamburgo", manana, estadoInicial, null,
                List.of(new ExportacionRequest.Linea(1L, new BigDecimal("100"), new BigDecimal("4.50")),
                        new ExportacionRequest.Linea(2L, new BigDecimal("50"), new BigDecimal("8.00"))));
    }

    private void preparar2Productos() {
        when(clientes.findById(1L)).thenReturn(Optional.of(Fixtures.cliente(1L, "DE", true)));
        when(productos.findById(1L)).thenReturn(Optional.of(arabica));
        when(productos.findById(2L)).thenReturn(Optional.of(cacao));
        when(exportaciones.save(any(Exportacion.class))).thenAnswer(i -> {
            Exportacion e = i.getArgument(0);
            if (e.getId() == null) {
                e.setId(1L);
            }
            return e;
        });
    }

    @Test
    @DisplayName("QA016 [HU-11][RF-17] Crear una exportación con varios productos y calcular su total")
    void qa016() {
        preparar2Productos();
        Exportacion ex = service.crearExportacion(peticion(null), operador);
        assertThat(ex.getEstado()).isEqualTo(EstadoExportacion.BORRADOR);
        assertThat(ex.getTotalUsd()).isEqualByComparingTo("850.00");   // 100 × 4,50 + 50 × 8,00
        assertThat(ex.getDetalles()).hasSize(2);
        assertThat(ex.getCodigo()).matches("EXP-\\d{4}-0001");
        verify(inventario).validarDisponibilidad(ex);
        verify(inventario, never()).descontarParaExportacion(any(), any());
    }

    @Test
    @DisplayName("[HU-11][RF-19] Crear con estado inicial EN_PREPARACION confirma y descuenta el inventario")
    void confirmaAlCrear() {
        preparar2Productos();
        Exportacion ex = service.crearExportacion(peticion("EN_PREPARACION"), operador);
        assertThat(ex.getEstado()).isEqualTo(EstadoExportacion.EN_PREPARACION);
        assertThat(ex.isDescontado()).isTrue();
        verify(inventario).descontarParaExportacion(ex, operador);
    }

    @Test
    @DisplayName("[HU-11][RF-16] Un cliente inactivo o una fecha pasada impiden crear la exportación")
    void validacionesBasicas() {
        when(clientes.findById(1L)).thenReturn(Optional.of(Fixtures.cliente(1L, "DE", false)));
        assertThatThrownBy(() -> service.crearExportacion(peticion(null), operador)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("no está activo");
        when(clientes.findById(1L)).thenReturn(Optional.of(Fixtures.cliente(1L, "DE", true)));
        ExportacionRequest pasada = new ExportacionRequest(1L, "DE", "Cartagena", "Hamburgo", LocalDate.now().minusDays(3), null, null,
                List.of(new ExportacionRequest.Linea(1L, BigDecimal.ONE, BigDecimal.ONE)));
        assertThatThrownBy(() -> service.crearExportacion(pasada, operador)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("pasado");
        verify(exportaciones, never()).save(any());
    }

    @Test
    @DisplayName("[HU-15][RF-21] No se pasa a EN_TRANSITO si faltan documentos obligatorios")
    void tránsitoSinDocumentos() {
        Exportacion ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), operador, manana);
        ex.setEstado(EstadoExportacion.EN_PREPARACION);
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        when(documentos.faltantes(1L)).thenReturn(List.of(TipoDocumento.CERTIFICADO_ORIGEN, TipoDocumento.FITOSANITARIO));
        assertThatThrownBy(() -> service.cambiarEstado(1L, EstadoExportacion.EN_TRANSITO, operador))
                .isInstanceOf(ReglaNegocioException.class).hasMessage("Faltan documentos obligatorios: Certificado de origen, Certificado fitosanitario.");
        assertThat(ex.getEstado()).isEqualTo(EstadoExportacion.EN_PREPARACION);
    }

    @Test
    @DisplayName("[HU-12][RF-18] Solo se permiten las transiciones de estado del flujo")
    void transicionesInvalidas() {
        Exportacion ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), operador, manana);
        ex.setEstado(EstadoExportacion.ENTREGADA);
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        assertThatThrownBy(() -> service.cambiarEstado(1L, EstadoExportacion.CANCELADA, operador)).isInstanceOf(ReglaNegocioException.class).hasMessageContaining("Transición");
        assertThatThrownBy(() -> service.cambiarEstado(1L, EstadoExportacion.BORRADOR, operador)).isInstanceOf(ReglaNegocioException.class);
    }

    @Test
    @DisplayName("[HU-12][RF-19] Cancelar una exportación con inventario descontado lo devuelve")
    void cancelarDevuelveStock() {
        Exportacion ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), operador, manana);
        ex.setEstado(EstadoExportacion.EN_PREPARACION);
        ex.setDescontado(true);
        when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
        when(exportaciones.save(any(Exportacion.class))).thenAnswer(i -> i.getArgument(0));
        Exportacion r = service.cambiarEstado(1L, EstadoExportacion.CANCELADA, operador);
        assertThat(r.getEstado()).isEqualTo(EstadoExportacion.CANCELADA);
        assertThat(r.isDescontado()).isFalse();
        verify(inventario).devolverStock(ex, operador);
    }
}
