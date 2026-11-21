package co.ritech.coffeeexport;

import co.ritech.coffeeexport.clientes.Cliente;
import co.ritech.coffeeexport.exportaciones.DetalleExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.inventario.Bodega;
import co.ritech.coffeeexport.inventario.Inventario;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.TipoProducto;
import co.ritech.coffeeexport.usuarios.Rol;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.time.LocalDate;

/** Constructores de datos de prueba compartidos por las pruebas unitarias. */
public final class Fixtures {
    private Fixtures() {
    }

    public static Usuario usuario(Long id, String email, String hash, String rol, boolean activo) {
        Usuario u = new Usuario();
        u.setId(id);
        u.setNombre("Usuario " + id);
        u.setEmail(email);
        u.setPasswordHash(hash);
        u.setRol(new Rol(rol, rol));
        u.setActivo(activo);
        return u;
    }

    public static Cliente cliente(Long id, String pais, boolean activo) {
        Cliente c = new Cliente();
        c.setId(id);
        c.setNombre("Cliente " + id);
        c.setPais(pais);
        c.setIdentificacionFiscal("NIF-" + id);
        c.setContactoNombre("Contacto");
        c.setContactoEmail("c" + id + "@cliente.eu");
        c.setConsentimientoDatos(true);
        c.setActivo(activo);
        return c;
    }

    public static Producto producto(Long id, String nombre, String precio) {
        Producto p = new Producto();
        p.setId(id);
        p.setCodigo("P-" + id);
        p.setNombre(nombre);
        p.setTipo(TipoProducto.CAFE);
        p.setPrecioUsdKg(new BigDecimal(precio));
        return p;
    }

    public static Bodega bodega(Long id, String nombre) {
        Bodega b = new Bodega(nombre, "Ciudad");
        b.setId(id);
        return b;
    }

    public static Inventario inventario(Long id, Producto p, Bodega b, String kg) {
        Inventario i = new Inventario();
        i.setId(id);
        i.setProducto(p);
        i.setBodega(b);
        i.setCantidadKg(new BigDecimal(kg));
        return i;
    }

    public static Exportacion exportacion(Long id, Cliente c, Usuario creador, LocalDate fecha) {
        Exportacion e = new Exportacion();
        e.setId(id);
        e.setCodigo("EXP-2026-" + String.format("%04d", id));
        e.setCliente(c);
        e.setPaisDestino(c.getPais());
        e.setPuertoSalida("Cartagena");
        e.setPuertoLlegada("Róterdam");
        e.setFechaEnvio(fecha);
        e.setUsuarioCreador(creador);
        return e;
    }

    public static DetalleExportacion detalle(Producto p, String kg, String precio) {
        DetalleExportacion d = new DetalleExportacion();
        d.setProducto(p);
        d.setCantidadKg(new BigDecimal(kg));
        d.setPrecioUnitario(new BigDecimal(precio));
        return d;
    }
}
