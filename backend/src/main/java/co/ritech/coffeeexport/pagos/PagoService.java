package co.ritech.coffeeexport.pagos;

import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import java.util.Set;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Pagos internacionales en USD o EUR (HU-16, HU-17, RF-23 a RF-25). */
@Service
public class PagoService {
    private static final Set<EstadoExportacion> FACTURABLES =
            Set.of(EstadoExportacion.EN_PREPARACION, EstadoExportacion.EN_TRANSITO, EstadoExportacion.ENTREGADA);

    private final PagoRepository pagos;
    private final ExportacionRepository exportaciones;
    private final BigDecimal tasaEurUsd;

    public PagoService(PagoRepository pagos, ExportacionRepository exportaciones, @Value("${app.tasa-eur-usd}") BigDecimal tasaEurUsd) {
        this.pagos = pagos;
        this.exportaciones = exportaciones;
        this.tasaEurUsd = tasaEurUsd;
    }

    @Transactional
    public Pago registrarPago(PagoRequest r, Usuario usuario) {
        Moneda moneda = Moneda.de(r.moneda());   // RR-07
        if (r.monto() == null || r.monto().compareTo(BigDecimal.ZERO) <= 0) {
            throw new ReglaNegocioException("El monto debe ser mayor que cero");
        }
        Exportacion ex = exportaciones.findById(r.exportacionId()).orElseThrow(() -> new ReglaNegocioException("La exportación no existe"));
        if (!FACTURABLES.contains(ex.getEstado())) {
            throw new ReglaNegocioException("Solo se registran pagos de exportaciones confirmadas");
        }
        Pago p = new Pago();
        p.setExportacion(ex);
        p.setMonto(r.monto().setScale(2, RoundingMode.HALF_UP));
        p.setMoneda(moneda);
        p.setMetodo(r.metodo() == null || r.metodo().isBlank() ? MetodoPago.TRANSFERENCIA : parsearMetodo(r.metodo()));
        p.setReferencia(r.referencia());
        p.setFechaPago(r.fechaPago());
        p.setEstado(EstadoPago.PENDIENTE);
        p.setRegistradoPor(usuario);
        return pagos.save(p);
    }

    @Transactional
    public Pago confirmar(Long id) {
        return resolver(id, EstadoPago.CONFIRMADO);
    }

    @Transactional
    public Pago rechazar(Long id) {
        return resolver(id, EstadoPago.RECHAZADO);
    }

    /** RF-24: saldo pendiente en USD = total de la exportación menos los pagos confirmados. */
    @Transactional(readOnly = true)
    public BigDecimal saldoPendiente(Long exportacionId) {
        Exportacion ex = exportaciones.findById(exportacionId).orElseThrow(() -> new RecursoNoEncontradoException("Exportación no encontrada"));
        BigDecimal confirmado = pagos.findByExportacionId(exportacionId).stream().filter(p -> p.getEstado() == EstadoPago.CONFIRMADO)
                .map(this::aUsd).reduce(BigDecimal.ZERO, BigDecimal::add);
        return ex.getTotalUsd().subtract(confirmado).max(BigDecimal.ZERO).setScale(2, RoundingMode.HALF_UP);
    }

    /** Conversión de un pago a USD con la tasa EUR/USD configurable. */
    public BigDecimal aUsd(Pago p) {
        return p.getMoneda() == Moneda.EUR ? p.getMonto().multiply(tasaEurUsd) : p.getMonto();
    }

    @Transactional(readOnly = true)
    public List<Pago> listar() {
        return pagos.findAllByOrderByIdDesc();
    }

    private Pago resolver(Long id, EstadoPago nuevo) {
        Pago p = pagos.findById(id).orElseThrow(() -> new RecursoNoEncontradoException("Pago no encontrado"));
        if (p.getEstado() != EstadoPago.PENDIENTE) {
            throw new ReglaNegocioException("Solo se pueden confirmar o rechazar pagos pendientes");
        }
        p.setEstado(nuevo);
        return pagos.save(p);
    }

    private static MetodoPago parsearMetodo(String metodo) {
        try {
            return MetodoPago.valueOf(metodo.trim().toUpperCase());
        } catch (IllegalArgumentException e) {
            throw new ReglaNegocioException("Método de pago no válido");
        }
    }
}
