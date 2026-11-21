package co.ritech.coffeeexport.pagos;

import java.math.BigDecimal;
import java.time.LocalDate;

public record PagoDto(Long id, Long exportacionId, String exportacionCodigo, String clienteNombre, BigDecimal monto, String moneda,
                      String metodo, String referencia, LocalDate fechaPago, String estado) {
    public static PagoDto de(Pago p) {
        return new PagoDto(p.getId(), p.getExportacion().getId(), p.getExportacion().getCodigo(), p.getExportacion().getCliente().getNombre(),
                p.getMonto(), p.getMoneda().name(), p.getMetodo().name(), p.getReferencia(), p.getFechaPago(), p.getEstado().name());
    }
}
