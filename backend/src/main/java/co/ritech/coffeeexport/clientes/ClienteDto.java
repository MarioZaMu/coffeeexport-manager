package co.ritech.coffeeexport.clientes;

import java.time.LocalDateTime;

public record ClienteDto(Long id, String nombre, String pais, String identificacionFiscal, String contactoNombre, String contactoEmail,
                         String contactoTelefono, String direccion, boolean consentimientoDatos, LocalDateTime fechaConsentimiento, boolean activo) {
    public static ClienteDto de(Cliente c) {
        return new ClienteDto(c.getId(), c.getNombre(), c.getPais(), c.getIdentificacionFiscal(), c.getContactoNombre(), c.getContactoEmail(),
                c.getContactoTelefono(), c.getDireccion(), c.isConsentimientoDatos(), c.getFechaConsentimiento(), c.isActivo());
    }
}
