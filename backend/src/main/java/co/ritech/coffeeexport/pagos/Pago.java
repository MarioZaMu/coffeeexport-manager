package co.ritech.coffeeexport.pagos;

import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.usuarios.Usuario;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

@Entity
@Table(name = "pagos")
@Getter @Setter @NoArgsConstructor
public class Pago {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "exportacion_id", nullable = false)
    private Exportacion exportacion;
    @Column(nullable = false, precision = 14, scale = 2)
    private BigDecimal monto;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 3)
    private Moneda moneda;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 15)
    private MetodoPago metodo = MetodoPago.TRANSFERENCIA;
    @Column(length = 80)
    private String referencia;
    @Column(nullable = false)
    private LocalDate fechaPago;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 12)
    private EstadoPago estado = EstadoPago.PENDIENTE;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "registrado_por", nullable = false)
    private Usuario registradoPor;
    @CreationTimestamp @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
