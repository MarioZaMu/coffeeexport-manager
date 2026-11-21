package co.ritech.coffeeexport.inventario;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "bodegas")
@Getter @Setter @NoArgsConstructor
public class Bodega {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, unique = true, length = 100)
    private String nombre;
    @Column(length = 100)
    private String ciudad;
    @Column(nullable = false)
    private boolean activa = true;

    public Bodega(String nombre, String ciudad) {
        this.nombre = nombre;
        this.ciudad = ciudad;
    }
}
