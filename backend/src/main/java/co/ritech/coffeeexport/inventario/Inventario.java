package co.ritech.coffeeexport.inventario;

import co.ritech.coffeeexport.productos.Producto;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.UpdateTimestamp;

/** Existencias de un producto en una bodega. Único por (producto, bodega). */
@Entity
@Table(name = "inventario", uniqueConstraints = @UniqueConstraint(name = "uq_inventario_producto_bodega", columnNames = {"producto_id", "bodega_id"}))
@Getter @Setter @NoArgsConstructor
public class Inventario {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "producto_id", nullable = false)
    private Producto producto;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "bodega_id", nullable = false)
    private Bodega bodega;
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal cantidadKg = BigDecimal.ZERO;
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal stockMinimoKg = BigDecimal.ZERO;
    @UpdateTimestamp @Column(nullable = false)
    private LocalDateTime updatedAt;
}
