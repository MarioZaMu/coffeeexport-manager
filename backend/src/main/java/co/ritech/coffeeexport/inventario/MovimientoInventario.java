package co.ritech.coffeeexport.inventario;

import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.usuarios.Usuario;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

/** Trazabilidad de entradas, salidas y ajustes (RF-13, RNF-13). */
@Entity
@Table(name = "movimientos_inventario")
@Getter @Setter @NoArgsConstructor
public class MovimientoInventario {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "inventario_id", nullable = false)
    private Inventario inventario;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 10)
    private TipoMovimiento tipo;
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal cantidadKg;
    @Column(length = 255)
    private String motivo;
    @ManyToOne(fetch = FetchType.LAZY) @JoinColumn(name = "exportacion_id")
    private Exportacion exportacion;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "usuario_id", nullable = false)
    private Usuario usuario;
    @CreationTimestamp @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
