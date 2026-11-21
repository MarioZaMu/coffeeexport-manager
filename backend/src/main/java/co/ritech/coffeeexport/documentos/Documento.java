package co.ritech.coffeeexport.documentos;

import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.usuarios.Usuario;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

@Entity
@Table(name = "documentos")
@Getter @Setter @NoArgsConstructor
public class Documento {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "exportacion_id", nullable = false)
    private Exportacion exportacion;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 30)
    private TipoDocumento tipo;
    @Column(nullable = false, length = 200)
    private String nombreArchivo;
    @Column(nullable = false, length = 255)
    private String rutaArchivo;
    @Column(nullable = false)
    private long tamanoBytes;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 12)
    private EstadoValidacion estadoValidacion = EstadoValidacion.PENDIENTE;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "subido_por", nullable = false)
    private Usuario subidoPor;
    @CreationTimestamp @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
