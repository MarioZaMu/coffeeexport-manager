package co.ritech.coffeeexport.clientes;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

@Entity
@Table(name = "clientes")
@Getter @Setter @NoArgsConstructor
public class Cliente {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, length = 150)
    private String nombre;
    /** Código ISO 3166-1 alfa-2 de un país de la Unión Europea. */
    @Column(nullable = false, length = 2, columnDefinition = "char(2)")
    private String pais;
    @Column(nullable = false, unique = true, length = 30)
    private String identificacionFiscal;
    @Column(nullable = false, length = 100)
    private String contactoNombre;
    @Column(nullable = false, length = 150)
    private String contactoEmail;
    @Column(length = 30)
    private String contactoTelefono;
    @Column(length = 255)
    private String direccion;
    /** RF-08, RR-05: consentimiento de tratamiento de datos (GDPR) y su fecha. */
    @Column(nullable = false)
    private boolean consentimientoDatos;
    private LocalDateTime fechaConsentimiento;
    @Column(nullable = false)
    private boolean activo = true;
    @CreationTimestamp @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
    @UpdateTimestamp @Column(nullable = false)
    private LocalDateTime updatedAt;
}
