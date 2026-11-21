package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.clientes.*;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ClienteServiceTest {
    @Mock ClienteRepository repo;
    ClienteService service;

    @BeforeEach
    void preparar() {
        service = new ClienteService(repo);
    }

    static ClienteRequest peticion(String pais, String nif, Boolean consentimiento) {
        return new ClienteRequest("Kaffeehaus GmbH", pais, nif, "Hans Becker", "hans@kaffeehaus.de", "+49 30 1", "Berlín", consentimiento);
    }

    @Test
    @DisplayName("QA005 [HU-02][RF-05] Registrar un cliente válido de la UE")
    void qa005() {
        when(repo.existsByIdentificacionFiscalIgnoreCase("DE811234567")).thenReturn(false);
        when(repo.save(any(Cliente.class))).thenAnswer(i -> {
            Cliente c = i.getArgument(0);
            c.setId(10L);
            return c;
        });
        Cliente c = service.registrarCliente(peticion("DE", "DE811234567", true));
        verify(repo, times(1)).save(any(Cliente.class));
        assertThat(c.getId()).isEqualTo(10L);
        assertThat(c.isActivo()).isTrue();
        assertThat(c.getFechaConsentimiento()).isNotNull();
    }

    @Test
    @DisplayName("QA006 [HU-02][RF-05] Rechazar un cliente con identificación fiscal duplicada")
    void qa006() {
        when(repo.existsByIdentificacionFiscalIgnoreCase("DE811234567")).thenReturn(true);
        assertThatThrownBy(() -> service.registrarCliente(peticion("DE", "DE811234567", true)))
                .isInstanceOf(ClienteDuplicadoException.class).hasMessageContaining("identificación fiscal");
        verify(repo, never()).save(any());
    }

    @Test
    @DisplayName("QA007 [HU-02][RF-05] Rechazar un cliente cuyo país no pertenece a la UE")
    void qa007() {
        assertThatThrownBy(() -> service.registrarCliente(peticion("US", "US123", true)))
                .isInstanceOf(IllegalArgumentException.class).isInstanceOf(ReglaNegocioException.class)
                .hasMessageContaining("Unión Europea");
        verify(repo, never()).save(any());
    }

    @Test
    @DisplayName("[HU-02][RF-08][RR-05] Sin consentimiento GDPR no se registra el cliente")
    void sinConsentimiento() {
        assertThatThrownBy(() -> service.registrarCliente(peticion("FR", "FR1", false)))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("consentimiento");
        assertThatThrownBy(() -> service.registrarCliente(peticion("FR", "FR1", null))).isInstanceOf(ReglaNegocioException.class);
        verify(repo, never()).save(any());
    }

    @Test
    @DisplayName("[HU-02][RF-06] Desactivar un cliente conserva el registro (baja lógica)")
    void bajaLogica() {
        Cliente c = new Cliente();
        c.setId(5L);
        c.setActivo(true);
        when(repo.findById(5L)).thenReturn(Optional.of(c));
        when(repo.save(any(Cliente.class))).thenAnswer(i -> i.getArgument(0));
        assertThat(service.cambiarEstado(5L, false).isActivo()).isFalse();
        verify(repo, never()).delete(any());
        verify(repo, never()).deleteById(any());
    }

    @Test
    @DisplayName("[HU-02][RF-05] Al actualizar, el NIF solo choca con OTRO cliente")
    void actualizarMismoNif() {
        Cliente actual = Fixtures_clienteConId(7L);
        when(repo.findById(7L)).thenReturn(Optional.of(actual));
        when(repo.findByIdentificacionFiscalIgnoreCase("DE811234567")).thenReturn(Optional.of(actual));
        when(repo.save(any(Cliente.class))).thenAnswer(i -> i.getArgument(0));
        assertThat(service.actualizarCliente(7L, peticion("DE", "DE811234567", true)).getNombre()).isEqualTo("Kaffeehaus GmbH");
    }

    private static Cliente Fixtures_clienteConId(Long id) {
        return co.ritech.coffeeexport.Fixtures.cliente(id, "DE", true);
    }
}
