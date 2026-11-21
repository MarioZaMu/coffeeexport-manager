package co.ritech.coffeeexport.productos;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

@Entity
@Table(name = "productos")
@Getter @Setter @NoArgsConstructor
public class Producto {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, unique = true, length = 30)
    private String codigo;
    @Column(nullable = false, length = 120)
    private String nombre;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 10)
    private TipoProducto tipo;
    @Column(length = 80)
    private String variedad;
    /** Precio de lista en USD por kg (RR-07). */
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal precioUsdKg;
    @Column(nullable = false)
    private boolean activo = true;
    @CreationTimestamp @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
    @UpdateTimestamp @Column(nullable = false)
    private LocalDateTime updatedAt;
}
