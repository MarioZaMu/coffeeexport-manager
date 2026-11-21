package co.ritech.coffeeexport.exportaciones;

import co.ritech.coffeeexport.productos.Producto;
import jakarta.persistence.*;
import java.math.BigDecimal;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/** Línea de una exportación: un producto con su cantidad y el precio pactado (RF-17). */
@Entity
@Table(name = "detalle_exportacion")
@Getter @Setter @NoArgsConstructor
public class DetalleExportacion {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(optional = false, fetch = FetchType.LAZY) @JoinColumn(name = "exportacion_id", nullable = false)
    private Exportacion exportacion;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "producto_id", nullable = false)
    private Producto producto;
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal cantidadKg;
    /** Precio USD/kg congelado al crear la línea, aunque el catálogo cambie después. */
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal precioUnitario;

    public BigDecimal getSubtotal() {
        return cantidadKg.multiply(precioUnitario);
    }
}
