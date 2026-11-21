package co.ritech.coffeeexport.exportaciones;

import co.ritech.coffeeexport.clientes.Cliente;
import co.ritech.coffeeexport.usuarios.Usuario;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

@Entity
@Table(name = "exportaciones")
@Getter @Setter @NoArgsConstructor
public class Exportacion {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, unique = true, length = 20)
    private String codigo;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "cliente_id", nullable = false)
    private Cliente cliente;
    @Column(nullable = false, length = 2, columnDefinition = "char(2)")
    private String paisDestino;
    @Column(nullable = false, length = 100)
    private String puertoSalida;
    @Column(nullable = false, length = 100)
    private String puertoLlegada;
    @Column(nullable = false)
    private LocalDate fechaEnvio;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 20)
    private EstadoExportacion estado = EstadoExportacion.BORRADOR;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "usuario_creador_id", nullable = false)
    private Usuario usuarioCreador;
    @Column(length = 500)
    private String observaciones;
    /** Indica si ya se descontó del inventario (RF-19). */
    @Column(nullable = false)
    private boolean descontado;
    @OneToMany(mappedBy = "exportacion", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.EAGER)
    private List<DetalleExportacion> detalles = new ArrayList<>();
    @CreationTimestamp @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
    @UpdateTimestamp @Column(nullable = false)
    private LocalDateTime updatedAt;

    public void agregarDetalle(DetalleExportacion d) {
        d.setExportacion(this);
        detalles.add(d);
    }

    /** Total en USD: suma de cantidad × precio de cada línea. */
    public BigDecimal getTotalUsd() {
        return detalles.stream().map(DetalleExportacion::getSubtotal).reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    public BigDecimal getTotalKg() {
        return detalles.stream().map(DetalleExportacion::getCantidadKg).reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}
