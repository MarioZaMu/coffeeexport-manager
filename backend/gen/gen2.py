# -*- coding: utf-8 -*-
"""Bloque 2: clientes, productos, inventario."""
import os
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "java", "co", "ritech", "coffeeexport")
F = {}

F["shared/Formato.java"] = r'''package co.ritech.coffeeexport.shared;

import java.math.BigDecimal;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.Locale;

/** Formato de números en es-CO (1.200 kg), igual que la interfaz. */
public final class Formato {
    private static final DecimalFormatSymbols SIMBOLOS = new DecimalFormatSymbols(Locale.forLanguageTag("es-CO"));

    private Formato() {
    }

    public static String kg(BigDecimal valor) {
        return new DecimalFormat("#,##0.##", SIMBOLOS).format(valor) + " kg";
    }
}
'''

# ================================================================= clientes
F["clientes/Cliente.java"] = r'''package co.ritech.coffeeexport.clientes;

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
'''
F["clientes/ClienteDuplicadoException.java"] = r'''package co.ritech.coffeeexport.clientes;

import co.ritech.coffeeexport.shared.ReglaNegocioException;

/** Ya existe un cliente con la misma identificación fiscal (HU-02). */
public class ClienteDuplicadoException extends ReglaNegocioException {
    public ClienteDuplicadoException(String mensaje) {
        super(mensaje);
    }
}
'''
F["clientes/ClienteRepository.java"] = r'''package co.ritech.coffeeexport.clientes;

import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ClienteRepository extends JpaRepository<Cliente, Long> {

    List<Cliente> findByPais(String pais);

    Optional<Cliente> findByIdentificacionFiscalIgnoreCase(String identificacionFiscal);

    boolean existsByIdentificacionFiscalIgnoreCase(String identificacionFiscal);

    long countByActivoTrue();

    /** Búsqueda parametrizada (RNF-04): ningún valor se concatena en la consulta. */
    @Query("""
            select c from Cliente c
            where (:q is null or lower(c.nombre) like lower(concat('%', :q, '%'))
                   or lower(c.identificacionFiscal) like lower(concat('%', :q, '%'))
                   or lower(c.contactoEmail) like lower(concat('%', :q, '%'))
                   or lower(c.contactoNombre) like lower(concat('%', :q, '%')))
              and (:pais is null or c.pais = :pais)
              and (:activo is null or c.activo = :activo)
            order by c.id
            """)
    List<Cliente> buscar(@Param("q") String q, @Param("pais") String pais, @Param("activo") Boolean activo);
}
'''
F["clientes/ClienteRequest.java"] = r'''package co.ritech.coffeeexport.clientes;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record ClienteRequest(
        @NotBlank(message = "El nombre es obligatorio") String nombre,
        @NotBlank(message = "Seleccione un país perteneciente a la Unión Europea") String pais,
        @NotBlank(message = "La identificación fiscal es obligatoria") String identificacionFiscal,
        @NotBlank(message = "La persona de contacto es obligatoria") String contactoNombre,
        @NotBlank(message = "El correo de contacto es obligatorio") @Email(message = "Ingrese un correo de contacto válido") String contactoEmail,
        String contactoTelefono,
        String direccion,
        Boolean consentimientoDatos) {
}
'''
F["clientes/ClienteDto.java"] = r'''package co.ritech.coffeeexport.clientes;

import java.time.LocalDateTime;

public record ClienteDto(Long id, String nombre, String pais, String identificacionFiscal, String contactoNombre, String contactoEmail,
                         String contactoTelefono, String direccion, boolean consentimientoDatos, LocalDateTime fechaConsentimiento, boolean activo) {
    public static ClienteDto de(Cliente c) {
        return new ClienteDto(c.getId(), c.getNombre(), c.getPais(), c.getIdentificacionFiscal(), c.getContactoNombre(), c.getContactoEmail(),
                c.getContactoTelefono(), c.getDireccion(), c.isConsentimientoDatos(), c.getFechaConsentimiento(), c.isActivo());
    }
}
'''
F["clientes/ClienteService.java"] = r'''package co.ritech.coffeeexport.clientes;

import co.ritech.coffeeexport.shared.Paises;
import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Gestión de clientes de la Unión Europea (HU-02, RF-05 a RF-08). */
@Service
public class ClienteService {
    private final ClienteRepository repo;

    public ClienteService(ClienteRepository repo) {
        this.repo = repo;
    }

    @Transactional
    public Cliente registrarCliente(ClienteRequest r) {
        validar(r, null);
        Cliente c = new Cliente();
        copiar(r, c);
        c.setActivo(true);
        c.setFechaConsentimiento(LocalDateTime.now());
        return repo.save(c);
    }

    @Transactional
    public Cliente actualizarCliente(Long id, ClienteRequest r) {
        Cliente c = obtener(id);
        validar(r, id);
        boolean tenia = c.isConsentimientoDatos();
        copiar(r, c);
        if (!tenia || c.getFechaConsentimiento() == null) {
            c.setFechaConsentimiento(LocalDateTime.now());
        }
        return repo.save(c);
    }

    /** RF-06: los clientes se desactivan, no se borran, para conservar su historial. */
    @Transactional
    public Cliente cambiarEstado(Long id, boolean activo) {
        Cliente c = obtener(id);
        c.setActivo(activo);
        return repo.save(c);
    }

    @Transactional(readOnly = true)
    public List<Cliente> buscar(String q, String pais, Boolean activo) {
        String texto = q == null || q.isBlank() ? null : q.trim();
        String codigo = pais == null || pais.isBlank() ? null : pais.trim().toUpperCase();
        return repo.buscar(texto, codigo, activo);
    }

    @Transactional(readOnly = true)
    public Cliente obtener(Long id) {
        return repo.findById(id).orElseThrow(() -> new RecursoNoEncontradoException("Cliente no encontrado"));
    }

    private void validar(ClienteRequest r, Long idActual) {
        if (!Paises.esUe(r.pais())) {
            throw new ReglaNegocioException("Seleccione un país perteneciente a la Unión Europea");
        }
        if (!Boolean.TRUE.equals(r.consentimientoDatos())) {
            throw new ReglaNegocioException("Se requiere el consentimiento de tratamiento de datos (GDPR)");
        }
        String nif = r.identificacionFiscal().trim();
        boolean duplicado = idActual == null
                ? repo.existsByIdentificacionFiscalIgnoreCase(nif)
                : repo.findByIdentificacionFiscalIgnoreCase(nif).filter(o -> !o.getId().equals(idActual)).isPresent();
        if (duplicado) {
            throw new ClienteDuplicadoException("Ya existe un cliente con esa identificación fiscal");
        }
    }

    private void copiar(ClienteRequest r, Cliente c) {
        c.setNombre(r.nombre().trim());
        c.setPais(r.pais().trim().toUpperCase());
        c.setIdentificacionFiscal(r.identificacionFiscal().trim());
        c.setContactoNombre(r.contactoNombre().trim());
        c.setContactoEmail(r.contactoEmail().trim());
        c.setContactoTelefono(r.contactoTelefono());
        c.setDireccion(r.direccion());
        c.setConsentimientoDatos(true);
    }
}
'''
F["clientes/EstadoRequest.java"] = r'''package co.ritech.coffeeexport.clientes;

public record EstadoRequest(boolean activo) {
}
'''
F["clientes/ClienteController.java"] = r'''package co.ritech.coffeeexport.clientes;

import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/clientes")
public class ClienteController {
    private final ClienteService service;

    public ClienteController(ClienteService service) {
        this.service = service;
    }

    @GetMapping
    public List<ClienteDto> listar(@RequestParam(required = false) String q, @RequestParam(required = false) String pais,
                                   @RequestParam(required = false) Boolean activo) {
        return service.buscar(q, pais, activo).stream().map(ClienteDto::de).toList();
    }

    @GetMapping("/{id}")
    public ClienteDto obtener(@PathVariable Long id) {
        return ClienteDto.de(service.obtener(id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ClienteDto crear(@Valid @RequestBody ClienteRequest r) {
        return ClienteDto.de(service.registrarCliente(r));
    }

    @PutMapping("/{id}")
    public ClienteDto actualizar(@PathVariable Long id, @Valid @RequestBody ClienteRequest r) {
        return ClienteDto.de(service.actualizarCliente(id, r));
    }

    @PatchMapping("/{id}/estado")
    public ClienteDto estado(@PathVariable Long id, @RequestBody EstadoRequest r) {
        return ClienteDto.de(service.cambiarEstado(id, r.activo()));
    }
}
'''

# ================================================================= productos
F["productos/TipoProducto.java"] = r'''package co.ritech.coffeeexport.productos;

public enum TipoProducto {
    CAFE, CACAO
}
'''
F["productos/Producto.java"] = r'''package co.ritech.coffeeexport.productos;

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
'''
F["productos/ProductoRepository.java"] = r'''package co.ritech.coffeeexport.productos;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ProductoRepository extends JpaRepository<Producto, Long> {

    List<Producto> findByTipo(TipoProducto tipo);

    boolean existsByCodigoIgnoreCase(String codigo);

    @Query("""
            select p from Producto p
            where (:q is null or lower(p.nombre) like lower(concat('%', :q, '%')) or lower(p.codigo) like lower(concat('%', :q, '%')))
              and (:tipo is null or p.tipo = :tipo)
              and (:activo is null or p.activo = :activo)
            order by p.id
            """)
    List<Producto> buscar(@Param("q") String q, @Param("tipo") TipoProducto tipo, @Param("activo") Boolean activo);
}
'''
F["productos/ProductoRequest.java"] = r'''package co.ritech.coffeeexport.productos;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

public record ProductoRequest(
        @NotBlank(message = "El código es obligatorio") String codigo,
        @NotBlank(message = "El nombre es obligatorio") String nombre,
        @NotBlank(message = "El tipo es obligatorio") String tipo,
        String variedad,
        @NotNull(message = "El precio es obligatorio") BigDecimal precioUsdKg) {
}
'''
F["productos/ProductoDto.java"] = r'''package co.ritech.coffeeexport.productos;

import java.math.BigDecimal;

public record ProductoDto(Long id, String codigo, String nombre, String tipo, String variedad, BigDecimal precioUsdKg, boolean activo) {
    public static ProductoDto de(Producto p) {
        return new ProductoDto(p.getId(), p.getCodigo(), p.getNombre(), p.getTipo().name(), p.getVariedad(), p.getPrecioUsdKg(), p.isActivo());
    }
}
'''
F["productos/ProductoService.java"] = r'''package co.ritech.coffeeexport.productos;

import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Catálogo de café y cacao (HU-03, RF-09 a RF-11). */
@Service
public class ProductoService {
    private final ProductoRepository repo;

    public ProductoService(ProductoRepository repo) {
        this.repo = repo;
    }

    @Transactional
    public Producto crearProducto(ProductoRequest r) {
        validar(r, null);
        Producto p = new Producto();
        copiar(r, p);
        p.setActivo(true);
        return repo.save(p);
    }

    @Transactional
    public Producto actualizarProducto(Long id, ProductoRequest r) {
        Producto p = obtener(id);
        validar(r, p);
        copiar(r, p);
        return repo.save(p);
    }

    /** RF-11: se desactiva sin eliminar físicamente. */
    @Transactional
    public Producto cambiarEstado(Long id, boolean activo) {
        Producto p = obtener(id);
        p.setActivo(activo);
        return repo.save(p);
    }

    @Transactional(readOnly = true)
    public List<Producto> buscar(String q, String tipo, Boolean activo) {
        String texto = q == null || q.isBlank() ? null : q.trim();
        return repo.buscar(texto, tipo == null || tipo.isBlank() ? null : parsearTipo(tipo), activo);
    }

    @Transactional(readOnly = true)
    public Producto obtener(Long id) {
        return repo.findById(id).orElseThrow(() -> new RecursoNoEncontradoException("Producto no encontrado"));
    }

    private void validar(ProductoRequest r, Producto actual) {
        if (r.precioUsdKg() == null || r.precioUsdKg().compareTo(BigDecimal.ZERO) <= 0) {
            throw new ReglaNegocioException("El precio debe ser mayor que cero");
        }
        parsearTipo(r.tipo());
        boolean cambiaCodigo = actual == null || !actual.getCodigo().equalsIgnoreCase(r.codigo().trim());
        if (cambiaCodigo && repo.existsByCodigoIgnoreCase(r.codigo().trim())) {
            throw new ReglaNegocioException("Ya existe un producto con ese código");
        }
    }

    private static TipoProducto parsearTipo(String tipo) {
        try {
            return TipoProducto.valueOf(tipo.trim().toUpperCase());
        } catch (IllegalArgumentException | NullPointerException e) {
            throw new ReglaNegocioException("Tipo de producto no válido: use CAFE o CACAO");
        }
    }

    private void copiar(ProductoRequest r, Producto p) {
        p.setCodigo(r.codigo().trim());
        p.setNombre(r.nombre().trim());
        p.setTipo(parsearTipo(r.tipo()));
        p.setVariedad(r.variedad());
        p.setPrecioUsdKg(r.precioUsdKg().setScale(2, RoundingMode.HALF_UP));
    }
}
'''
F["productos/ProductoController.java"] = r'''package co.ritech.coffeeexport.productos;

import co.ritech.coffeeexport.clientes.EstadoRequest;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/productos")
public class ProductoController {
    private final ProductoService service;

    public ProductoController(ProductoService service) {
        this.service = service;
    }

    @GetMapping
    public List<ProductoDto> listar(@RequestParam(required = false) String q, @RequestParam(required = false) String tipo,
                                    @RequestParam(required = false) Boolean activo) {
        return service.buscar(q, tipo, activo).stream().map(ProductoDto::de).toList();
    }

    @GetMapping("/{id}")
    public ProductoDto obtener(@PathVariable Long id) {
        return ProductoDto.de(service.obtener(id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ProductoDto crear(@Valid @RequestBody ProductoRequest r) {
        return ProductoDto.de(service.crearProducto(r));
    }

    @PutMapping("/{id}")
    public ProductoDto actualizar(@PathVariable Long id, @Valid @RequestBody ProductoRequest r) {
        return ProductoDto.de(service.actualizarProducto(id, r));
    }

    @PatchMapping("/{id}/estado")
    public ProductoDto estado(@PathVariable Long id, @RequestBody EstadoRequest r) {
        return ProductoDto.de(service.cambiarEstado(id, r.activo()));
    }
}
'''

# ================================================================= inventario
F["inventario/Bodega.java"] = r'''package co.ritech.coffeeexport.inventario;

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
'''
F["inventario/Inventario.java"] = r'''package co.ritech.coffeeexport.inventario;

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
'''
F["inventario/TipoMovimiento.java"] = r'''package co.ritech.coffeeexport.inventario;

public enum TipoMovimiento {
    ENTRADA, SALIDA, AJUSTE
}
'''
F["inventario/MovimientoInventario.java"] = r'''package co.ritech.coffeeexport.inventario;

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
'''
F["inventario/BodegaRepository.java"] = r'''package co.ritech.coffeeexport.inventario;

import org.springframework.data.jpa.repository.JpaRepository;

public interface BodegaRepository extends JpaRepository<Bodega, Long> {
}
'''
F["inventario/InventarioRepository.java"] = r'''package co.ritech.coffeeexport.inventario;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface InventarioRepository extends JpaRepository<Inventario, Long> {

    Optional<Inventario> findByProductoIdAndBodegaId(Long productoId, Long bodegaId);

    List<Inventario> findByProductoId(Long productoId);

    List<Inventario> findAllByOrderByIdAsc();

    @Query("select coalesce(sum(i.cantidadKg), 0) from Inventario i")
    BigDecimal totalGeneral();
}
'''
F["inventario/MovimientoInventarioRepository.java"] = r'''package co.ritech.coffeeexport.inventario;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MovimientoInventarioRepository extends JpaRepository<MovimientoInventario, Long> {

    List<MovimientoInventario> findAllByOrderByIdDesc();

    List<MovimientoInventario> findByExportacionIdAndTipo(Long exportacionId, TipoMovimiento tipo);
}
'''
F["inventario/MovimientoRequest.java"] = r'''package co.ritech.coffeeexport.inventario;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

public record MovimientoRequest(
        @NotNull(message = "Seleccione un producto") Long productoId,
        @NotNull(message = "Seleccione una bodega") Long bodegaId,
        @NotBlank(message = "Seleccione el tipo de movimiento") String tipo,
        @NotNull(message = "Ingrese la cantidad") BigDecimal cantidadKg,
        String motivo) {
}
'''
F["inventario/InventarioDtos.java"] = r'''package co.ritech.coffeeexport.inventario;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

public final class InventarioDtos {
    private InventarioDtos() {
    }

    public record InventarioDto(Long id, Long productoId, String productoNombre, Long bodegaId, String bodegaNombre,
                                BigDecimal cantidadKg, BigDecimal stockMinimoKg) {
        public static InventarioDto de(Inventario i) {
            return new InventarioDto(i.getId(), i.getProducto().getId(), i.getProducto().getNombre(), i.getBodega().getId(),
                    i.getBodega().getNombre(), i.getCantidadKg(), i.getStockMinimoKg());
        }
    }

    public record StockBodegaDto(Long bodegaId, String bodega, BigDecimal cantidadKg) {
    }

    public record StockDto(Long productoId, BigDecimal totalKg, List<StockBodegaDto> bodegas) {
    }

    public record MovimientoDto(Long id, Long inventarioId, String tipo, BigDecimal cantidadKg, String motivo, Long exportacionId,
                                String usuario, LocalDateTime fecha) {
        public static MovimientoDto de(MovimientoInventario m) {
            return new MovimientoDto(m.getId(), m.getInventario().getId(), m.getTipo().name(), m.getCantidadKg(), m.getMotivo(),
                    m.getExportacion() == null ? null : m.getExportacion().getId(), m.getUsuario().getNombre(), m.getCreatedAt());
        }
    }

    public record MinimoRequest(BigDecimal stockMinimoKg) {
    }
}
'''
F["inventario/InventarioService.java"] = r'''package co.ritech.coffeeexport.inventario;

import co.ritech.coffeeexport.exportaciones.DetalleExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.inventario.InventarioDtos.StockBodegaDto;
import co.ritech.coffeeexport.inventario.InventarioDtos.StockDto;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.ProductoRepository;
import co.ritech.coffeeexport.shared.Formato;
import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.shared.StockInsuficienteException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Inventario en tiempo real por producto y bodega (HU-04, RF-12 a RF-15, RF-19). */
@Service
public class InventarioService {
    private final InventarioRepository inventarios;
    private final MovimientoInventarioRepository movimientos;
    private final ProductoRepository productos;
    private final BodegaRepository bodegas;

    public InventarioService(InventarioRepository inventarios, MovimientoInventarioRepository movimientos,
                             ProductoRepository productos, BodegaRepository bodegas) {
        this.inventarios = inventarios;
        this.movimientos = movimientos;
        this.productos = productos;
        this.bodegas = bodegas;
    }

    /** RF-12: stock total del producto sumando todas sus bodegas, con el detalle por bodega. */
    @Transactional(readOnly = true)
    public StockDto consultarStock(Long productoId) {
        List<Inventario> filas = inventarios.findByProductoId(productoId);
        BigDecimal total = filas.stream().map(Inventario::getCantidadKg).reduce(BigDecimal.ZERO, BigDecimal::add);
        List<StockBodegaDto> detalle = filas.stream()
                .map(i -> new StockBodegaDto(i.getBodega().getId(), i.getBodega().getNombre(), i.getCantidadKg())).toList();
        return new StockDto(productoId, total, detalle);
    }

    @Transactional
    public MovimientoInventario registrarEntrada(Long productoId, Long bodegaId, BigDecimal kg, String motivo, Usuario usuario) {
        exigirPositiva(kg);
        Inventario inv = inventarios.findByProductoIdAndBodegaId(productoId, bodegaId).orElseGet(() -> nuevo(productoId, bodegaId));
        inv.setCantidadKg(inv.getCantidadKg().add(kg));
        inventarios.save(inv);
        return registrar(inv, TipoMovimiento.ENTRADA, kg, motivo, null, usuario);
    }

    /** RF-14: no se permite una salida mayor al stock disponible. */
    @Transactional
    public MovimientoInventario registrarSalida(Long productoId, Long bodegaId, BigDecimal kg, String motivo, Usuario usuario) {
        return salida(productoId, bodegaId, kg, motivo, null, usuario);
    }

    @Transactional
    public MovimientoInventario ajustar(Long productoId, Long bodegaId, BigDecimal nuevoStock, String motivo, Usuario usuario) {
        if (nuevoStock == null || nuevoStock.compareTo(BigDecimal.ZERO) < 0) {
            throw new ReglaNegocioException("El stock ajustado no puede ser negativo");
        }
        Inventario inv = inventarios.findByProductoIdAndBodegaId(productoId, bodegaId).orElseGet(() -> nuevo(productoId, bodegaId));
        inv.setCantidadKg(nuevoStock);
        inventarios.save(inv);
        return registrar(inv, TipoMovimiento.AJUSTE, nuevoStock, motivo, null, usuario);
    }

    @Transactional
    public MovimientoInventario registrarMovimiento(MovimientoRequest r, Usuario usuario) {
        TipoMovimiento tipo;
        try {
            tipo = TipoMovimiento.valueOf(r.tipo().trim().toUpperCase());
        } catch (IllegalArgumentException e) {
            throw new ReglaNegocioException("Tipo de movimiento no válido: ENTRADA, SALIDA o AJUSTE");
        }
        return switch (tipo) {
            case ENTRADA -> registrarEntrada(r.productoId(), r.bodegaId(), r.cantidadKg(), r.motivo(), usuario);
            case SALIDA -> registrarSalida(r.productoId(), r.bodegaId(), r.cantidadKg(), r.motivo(), usuario);
            case AJUSTE -> ajustar(r.productoId(), r.bodegaId(), r.cantidadKg(), r.motivo(), usuario);
        };
    }

    /** Comprueba que haya stock de todos los productos de la exportación antes de comprometerla (UC-08 3a). */
    @Transactional(readOnly = true)
    public void validarDisponibilidad(Exportacion ex) {
        for (Map.Entry<Long, BigDecimal> e : pedidoPorProducto(ex).entrySet()) {
            BigDecimal disponible = consultarStock(e.getKey()).totalKg();
            if (e.getValue().compareTo(disponible) > 0) {
                String nombre = productos.findById(e.getKey()).map(Producto::getNombre).orElse("producto " + e.getKey());
                throw new StockInsuficienteException("Stock insuficiente de " + nombre + ": solicitado "
                        + Formato.kg(e.getValue()) + ", disponible " + Formato.kg(disponible));
            }
        }
    }

    private Map<Long, BigDecimal> pedidoPorProducto(Exportacion ex) {
        Map<Long, BigDecimal> pedido = new LinkedHashMap<>();
        for (DetalleExportacion d : ex.getDetalles()) {
            pedido.merge(d.getProducto().getId(), d.getCantidadKg(), BigDecimal::add);
        }
        return pedido;
    }

    /**
     * RF-19: descuenta el inventario de una exportación, de la bodega con más stock a la de menos.
     * Es atómica: primero valida todos los productos y solo entonces mueve existencias.
     */
    @Transactional
    public void descontarParaExportacion(Exportacion ex, Usuario usuario) {
        validarDisponibilidad(ex);
        Map<Long, BigDecimal> pedido = pedidoPorProducto(ex);
        for (Map.Entry<Long, BigDecimal> e : pedido.entrySet()) {
            BigDecimal falta = e.getValue();
            List<Inventario> filas = inventarios.findByProductoId(e.getKey()).stream()
                    .filter(i -> i.getCantidadKg().signum() > 0)
                    .sorted(Comparator.comparing(Inventario::getCantidadKg).reversed()).toList();
            for (Inventario inv : filas) {
                if (falta.signum() == 0) {
                    break;
                }
                BigDecimal t = falta.min(inv.getCantidadKg());
                inv.setCantidadKg(inv.getCantidadKg().subtract(t));
                inventarios.save(inv);
                registrar(inv, TipoMovimiento.SALIDA, t, "Exportación " + ex.getCodigo(), ex, usuario);
                falta = falta.subtract(t);
            }
        }
    }

    /** Devuelve al inventario lo descontado por una exportación cancelada. */
    @Transactional
    public void devolverStock(Exportacion ex, Usuario usuario) {
        for (MovimientoInventario m : movimientos.findByExportacionIdAndTipo(ex.getId(), TipoMovimiento.SALIDA)) {
            Inventario inv = m.getInventario();
            inv.setCantidadKg(inv.getCantidadKg().add(m.getCantidadKg()));
            inventarios.save(inv);
            registrar(inv, TipoMovimiento.ENTRADA, m.getCantidadKg(), "Cancelación " + ex.getCodigo(), ex, usuario);
        }
    }

    @Transactional
    public Inventario actualizarMinimo(Long inventarioId, BigDecimal minimo) {
        if (minimo == null || minimo.signum() < 0) {
            throw new ReglaNegocioException("Ingrese un valor válido (mayor o igual a 0)");
        }
        Inventario inv = inventarios.findById(inventarioId).orElseThrow(() -> new RecursoNoEncontradoException("Registro de inventario no encontrado"));
        inv.setStockMinimoKg(minimo);
        return inventarios.save(inv);
    }

    @Transactional(readOnly = true)
    public List<Inventario> listar(Long productoId) {
        return productoId == null ? inventarios.findAllByOrderByIdAsc() : inventarios.findByProductoId(productoId);
    }

    @Transactional(readOnly = true)
    public List<MovimientoInventario> listarMovimientos() {
        return movimientos.findAllByOrderByIdDesc();
    }

    @Transactional(readOnly = true)
    public List<Bodega> listarBodegas() {
        return bodegas.findAll();
    }

    private MovimientoInventario salida(Long productoId, Long bodegaId, BigDecimal kg, String motivo, Exportacion ex, Usuario usuario) {
        exigirPositiva(kg);
        Inventario inv = inventarios.findByProductoIdAndBodegaId(productoId, bodegaId)
                .orElseThrow(() -> new StockInsuficienteException("No hay existencias de ese producto en la bodega seleccionada."));
        if (kg.compareTo(inv.getCantidadKg()) > 0) {
            throw new StockInsuficienteException("Stock insuficiente: disponible " + Formato.kg(inv.getCantidadKg()) + " en esa bodega.");
        }
        inv.setCantidadKg(inv.getCantidadKg().subtract(kg));
        inventarios.save(inv);
        return registrar(inv, TipoMovimiento.SALIDA, kg, motivo, ex, usuario);
    }

    private MovimientoInventario registrar(Inventario inv, TipoMovimiento tipo, BigDecimal kg, String motivo, Exportacion ex, Usuario usuario) {
        MovimientoInventario m = new MovimientoInventario();
        m.setInventario(inv);
        m.setTipo(tipo);
        m.setCantidadKg(kg);
        m.setMotivo(motivo);
        m.setExportacion(ex);
        m.setUsuario(usuario);
        return movimientos.save(m);
    }

    private Inventario nuevo(Long productoId, Long bodegaId) {
        Inventario inv = new Inventario();
        inv.setProducto(productos.findById(productoId).orElseThrow(() -> new RecursoNoEncontradoException("Producto no encontrado")));
        inv.setBodega(bodegas.findById(bodegaId).orElseThrow(() -> new RecursoNoEncontradoException("Bodega no encontrada")));
        return inv;
    }

    private static void exigirPositiva(BigDecimal kg) {
        if (kg == null || kg.compareTo(BigDecimal.ZERO) <= 0) {
            throw new ReglaNegocioException("La cantidad debe ser mayor que cero.");
        }
    }
}
'''
F["inventario/InventarioController.java"] = r'''package co.ritech.coffeeexport.inventario;

import co.ritech.coffeeexport.auth.AuthService;
import co.ritech.coffeeexport.inventario.InventarioDtos.*;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/inventario")
public class InventarioController {
    private final InventarioService service;
    private final AuthService auth;

    public InventarioController(InventarioService service, AuthService auth) {
        this.service = service;
        this.auth = auth;
    }

    @GetMapping
    public List<InventarioDto> consultar(@RequestParam(required = false) Long productoId) {
        return service.listar(productoId).stream().map(InventarioDto::de).toList();
    }

    @GetMapping("/stock/{productoId}")
    public StockDto stock(@PathVariable Long productoId) {
        return service.consultarStock(productoId);
    }

    @GetMapping("/bodegas")
    public List<Bodega> bodegas() {
        return service.listarBodegas();
    }

    @GetMapping("/movimientos")
    public List<MovimientoDto> movimientos() {
        return service.listarMovimientos().stream().map(MovimientoDto::de).toList();
    }

    @PostMapping("/movimientos")
    @ResponseStatus(HttpStatus.CREATED)
    public MovimientoDto registrarMovimiento(@Valid @RequestBody MovimientoRequest r, Authentication a) {
        return MovimientoDto.de(service.registrarMovimiento(r, auth.actual(a)));
    }

    @PatchMapping("/{id}/minimo")
    public InventarioDto minimo(@PathVariable Long id, @RequestBody MinimoRequest r) {
        return InventarioDto.de(service.actualizarMinimo(id, r.stockMinimoKg()));
    }
}
'''

for ruta, contenido in F.items():
    destino = os.path.normpath(os.path.join(BASE, ruta))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    open(destino, "w", encoding="utf-8", newline="\n").write(contenido)
print(len(F), "archivos")
