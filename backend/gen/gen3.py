# -*- coding: utf-8 -*-
"""Bloque 3: exportaciones, documentos, pagos."""
import os
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "java", "co", "ritech", "coffeeexport")
F = {}

# ================================================================= exportaciones
F["exportaciones/EstadoExportacion.java"] = r'''package co.ritech.coffeeexport.exportaciones;

public enum EstadoExportacion {
    BORRADOR, EN_PREPARACION, EN_TRANSITO, ENTREGADA, CANCELADA
}
'''
F["exportaciones/Exportacion.java"] = r'''package co.ritech.coffeeexport.exportaciones;

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
'''
F["exportaciones/DetalleExportacion.java"] = r'''package co.ritech.coffeeexport.exportaciones;

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
'''
F["exportaciones/ExportacionRepository.java"] = r'''package co.ritech.coffeeexport.exportaciones;

import java.time.LocalDate;
import java.util.Collection;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ExportacionRepository extends JpaRepository<Exportacion, Long> {

    List<Exportacion> findAllByOrderByIdDesc();

    @Query("""
            select e from Exportacion e
            where e.fechaEnvio between :desde and :hasta and e.estado not in :excluidos
            order by e.fechaEnvio, e.id
            """)
    List<Exportacion> enRango(@Param("desde") LocalDate desde, @Param("hasta") LocalDate hasta,
                              @Param("excluidos") Collection<EstadoExportacion> excluidos);
}
'''
F["exportaciones/ExportacionRequest.java"] = r'''package co.ritech.coffeeexport.exportaciones;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

/** Datos del asistente de 4 pasos (RF-16): básica, cliente y destino, productos y documentos. */
public record ExportacionRequest(
        @NotNull(message = "Seleccione un cliente") Long clienteId,
        @NotBlank(message = "Seleccione el país destino") String paisDestino,
        @NotBlank(message = "Seleccione el puerto de salida") String puertoSalida,
        @NotBlank(message = "Seleccione el puerto de llegada") String puertoLlegada,
        @NotNull(message = "La fecha de envío es obligatoria") LocalDate fechaEnvio,
        String estadoInicial,
        String observaciones,
        @NotEmpty(message = "Agregue al menos un producto") @Valid List<Linea> lineas) {

    public record Linea(
            @NotNull(message = "Seleccione un producto") Long productoId,
            @NotNull(message = "Ingrese la cantidad") BigDecimal cantidadKg,
            @NotNull(message = "Ingrese el precio") BigDecimal precioUnitario) {
    }
}
'''
F["exportaciones/ExportacionDto.java"] = r'''package co.ritech.coffeeexport.exportaciones;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

public record ExportacionDto(Long id, String codigo, Long clienteId, String clienteNombre, String paisDestino, String puertoSalida,
                             String puertoLlegada, LocalDate fechaEnvio, String estado, Long creadorId, String observaciones,
                             boolean descontado, LocalDateTime createdAt, BigDecimal totalUsd, BigDecimal totalKg, List<LineaDto> lineas) {

    public record LineaDto(Long productoId, String productoNombre, BigDecimal cantidadKg, BigDecimal precioUnitario, BigDecimal subtotal) {
    }

    public static ExportacionDto de(Exportacion e) {
        List<LineaDto> lineas = e.getDetalles().stream().map(d -> new LineaDto(d.getProducto().getId(), d.getProducto().getNombre(),
                d.getCantidadKg(), d.getPrecioUnitario(), d.getSubtotal())).toList();
        return new ExportacionDto(e.getId(), e.getCodigo(), e.getCliente().getId(), e.getCliente().getNombre(), e.getPaisDestino(),
                e.getPuertoSalida(), e.getPuertoLlegada(), e.getFechaEnvio(), e.getEstado().name(), e.getUsuarioCreador().getId(),
                e.getObservaciones(), e.isDescontado(), e.getCreatedAt(), e.getTotalUsd(), e.getTotalKg(), lineas);
    }
}
'''
F["exportaciones/ExportacionService.java"] = r'''package co.ritech.coffeeexport.exportaciones;

import co.ritech.coffeeexport.clientes.Cliente;
import co.ritech.coffeeexport.clientes.ClienteRepository;
import co.ritech.coffeeexport.documentos.DocumentoService;
import co.ritech.coffeeexport.documentos.TipoDocumento;
import co.ritech.coffeeexport.inventario.InventarioService;
import co.ritech.coffeeexport.productos.Producto;
import co.ritech.coffeeexport.productos.ProductoRepository;
import co.ritech.coffeeexport.shared.Paises;
import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Pedidos y envíos de exportación (HU-11, HU-12, RF-16 a RF-19). */
@Service
public class ExportacionService {
    static final ZoneId ZONA = ZoneId.of("America/Bogota");

    private final ExportacionRepository exportaciones;
    private final ClienteRepository clientes;
    private final ProductoRepository productos;
    private final InventarioService inventario;
    private final DocumentoService documentos;

    public ExportacionService(ExportacionRepository exportaciones, ClienteRepository clientes, ProductoRepository productos,
                              InventarioService inventario, DocumentoService documentos) {
        this.exportaciones = exportaciones;
        this.clientes = clientes;
        this.productos = productos;
        this.inventario = inventario;
        this.documentos = documentos;
    }

    /** Crea la exportación en BORRADOR o la confirma de inmediato (descontando inventario) según el estado inicial. */
    @Transactional
    public Exportacion crearExportacion(ExportacionRequest r, Usuario creador) {
        Cliente cliente = clientes.findById(r.clienteId()).orElseThrow(() -> new ReglaNegocioException("El cliente seleccionado no existe"));
        if (!cliente.isActivo()) {
            throw new ReglaNegocioException("El cliente seleccionado no está activo");
        }
        if (!Paises.esUe(r.paisDestino())) {
            throw new ReglaNegocioException("Seleccione el país destino dentro de la Unión Europea");
        }
        if (r.fechaEnvio().isBefore(LocalDate.now(ZONA))) {
            throw new ReglaNegocioException("La fecha de envío no puede estar en el pasado");
        }
        boolean confirmar = r.estadoInicial() != null && r.estadoInicial().equalsIgnoreCase("EN_PREPARACION");
        if (r.estadoInicial() != null && !r.estadoInicial().isBlank() && !confirmar && !r.estadoInicial().equalsIgnoreCase("BORRADOR")) {
            throw new ReglaNegocioException("El estado inicial debe ser BORRADOR o EN_PREPARACION");
        }

        Exportacion ex = new Exportacion();
        ex.setCodigo("TMP-" + UUID.randomUUID().toString().replace("-", "").substring(0, 16));   // provisional (20 caracteres como máximo)
        ex.setCliente(cliente);
        ex.setPaisDestino(r.paisDestino().trim().toUpperCase());
        ex.setPuertoSalida(r.puertoSalida().trim());
        ex.setPuertoLlegada(r.puertoLlegada().trim());
        ex.setFechaEnvio(r.fechaEnvio());
        ex.setObservaciones(r.observaciones());
        ex.setUsuarioCreador(creador);
        ex.setEstado(EstadoExportacion.BORRADOR);
        for (ExportacionRequest.Linea l : r.lineas()) {
            if (l.cantidadKg().compareTo(BigDecimal.ZERO) <= 0) {
                throw new ReglaNegocioException("La cantidad debe ser mayor que cero");
            }
            if (l.precioUnitario().compareTo(BigDecimal.ZERO) <= 0) {
                throw new ReglaNegocioException("El precio debe ser mayor que cero");
            }
            Producto p = productos.findById(l.productoId()).orElseThrow(() -> new ReglaNegocioException("Producto no encontrado"));
            if (!p.isActivo()) {
                throw new ReglaNegocioException("El producto " + p.getNombre() + " no está activo");
            }
            DetalleExportacion d = new DetalleExportacion();
            d.setProducto(p);
            d.setCantidadKg(l.cantidadKg());
            d.setPrecioUnitario(l.precioUnitario());
            ex.agregarDetalle(d);
        }
        inventario.validarDisponibilidad(ex);   // UC-08 3a: el stock insuficiente bloquea el avance
        Exportacion guardada = exportaciones.save(ex);
        guardada.setCodigo(String.format("EXP-%d-%04d", LocalDate.now(ZONA).getYear(), guardada.getId()));
        if (confirmar) {
            confirmarInterno(guardada, creador);
        }
        return exportaciones.save(guardada);
    }

    /** Transiciones válidas: BORRADOR → EN_PREPARACION → EN_TRANSITO → ENTREGADA; cancelar desde BORRADOR o EN_PREPARACION. */
    @Transactional
    public Exportacion cambiarEstado(Long id, EstadoExportacion nuevo, Usuario usuario) {
        Exportacion ex = obtener(id);
        EstadoExportacion actual = ex.getEstado();
        switch (nuevo) {
            case EN_PREPARACION -> {
                exigir(actual == EstadoExportacion.BORRADOR, actual, nuevo);
                confirmarInterno(ex, usuario);
            }
            case EN_TRANSITO -> {
                exigir(actual == EstadoExportacion.EN_PREPARACION, actual, nuevo);
                List<TipoDocumento> faltan = documentos.faltantes(id);   // RF-21
                if (!faltan.isEmpty()) {
                    throw new ReglaNegocioException("Faltan documentos obligatorios: "
                            + faltan.stream().map(TipoDocumento::getEtiqueta).collect(Collectors.joining(", ")) + ".");
                }
                ex.setEstado(nuevo);
            }
            case ENTREGADA -> {
                exigir(actual == EstadoExportacion.EN_TRANSITO, actual, nuevo);
                ex.setEstado(nuevo);
            }
            case CANCELADA -> {
                exigir(actual == EstadoExportacion.BORRADOR || actual == EstadoExportacion.EN_PREPARACION, actual, nuevo);
                if (ex.isDescontado()) {
                    inventario.devolverStock(ex, usuario);
                    ex.setDescontado(false);
                }
                ex.setEstado(nuevo);
            }
            default -> throw new ReglaNegocioException("Transición de estado no permitida: " + actual + " a " + nuevo);
        }
        return exportaciones.save(ex);
    }

    @Transactional(readOnly = true)
    public Exportacion obtener(Long id) {
        return exportaciones.findById(id).orElseThrow(() -> new RecursoNoEncontradoException("Exportación no encontrada"));
    }

    @Transactional(readOnly = true)
    public List<Exportacion> listar(String q, String estado) {
        EstadoExportacion filtro = estado == null || estado.isBlank() ? null : parsear(estado);
        String texto = q == null ? "" : q.trim().toLowerCase();
        return exportaciones.findAllByOrderByIdDesc().stream()
                .filter(e -> filtro == null || e.getEstado() == filtro)
                .filter(e -> texto.isEmpty() || e.getCodigo().toLowerCase().contains(texto)
                        || e.getCliente().getNombre().toLowerCase().contains(texto))
                .toList();
    }

    public static EstadoExportacion parsear(String estado) {
        try {
            return EstadoExportacion.valueOf(estado.trim().toUpperCase());
        } catch (IllegalArgumentException | NullPointerException e) {
            throw new ReglaNegocioException("Estado de exportación no válido");
        }
    }

    private void confirmarInterno(Exportacion ex, Usuario usuario) {
        inventario.descontarParaExportacion(ex, usuario);   // RF-19
        ex.setDescontado(true);
        ex.setEstado(EstadoExportacion.EN_PREPARACION);
    }

    private static void exigir(boolean condicion, EstadoExportacion actual, EstadoExportacion nuevo) {
        if (!condicion) {
            throw new ReglaNegocioException("Transición de estado no permitida: " + actual + " a " + nuevo);
        }
    }
}
'''
F["exportaciones/EstadoExportacionRequest.java"] = r'''package co.ritech.coffeeexport.exportaciones;

import jakarta.validation.constraints.NotBlank;

public record EstadoExportacionRequest(@NotBlank(message = "Indique el nuevo estado") String estado) {
}
'''
F["exportaciones/ExportacionController.java"] = r'''package co.ritech.coffeeexport.exportaciones;

import co.ritech.coffeeexport.auth.AuthService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/exportaciones")
public class ExportacionController {
    private final ExportacionService service;
    private final AuthService auth;

    public ExportacionController(ExportacionService service, AuthService auth) {
        this.service = service;
        this.auth = auth;
    }

    @GetMapping
    public List<ExportacionDto> listar(@RequestParam(required = false) String q, @RequestParam(required = false) String estado) {
        return service.listar(q, estado).stream().map(ExportacionDto::de).toList();
    }

    @GetMapping("/{id}")
    public ExportacionDto obtener(@PathVariable Long id) {
        return ExportacionDto.de(service.obtener(id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ExportacionDto crear(@Valid @RequestBody ExportacionRequest r, Authentication a) {
        return ExportacionDto.de(service.crearExportacion(r, auth.actual(a)));
    }

    @PatchMapping("/{id}/estado")
    public ExportacionDto estado(@PathVariable Long id, @Valid @RequestBody EstadoExportacionRequest r, Authentication a) {
        return ExportacionDto.de(service.cambiarEstado(id, ExportacionService.parsear(r.estado()), auth.actual(a)));
    }
}
'''

# ================================================================= documentos
F["documentos/TipoDocumento.java"] = r'''package co.ritech.coffeeexport.documentos;

import java.util.List;

public enum TipoDocumento {
    CERTIFICADO_ORIGEN("Certificado de origen"), FITOSANITARIO("Certificado fitosanitario"), FACTURA_COMERCIAL("Factura comercial"),
    LISTA_EMPAQUE("Lista de empaque"), DECLARACION_ADUANERA("Declaración aduanera"), OTRO("Otro");

    /** RF-21, RR-06: sin estos cuatro la exportación no puede pasar a En tránsito. */
    public static final List<TipoDocumento> OBLIGATORIOS = List.of(CERTIFICADO_ORIGEN, FITOSANITARIO, FACTURA_COMERCIAL, DECLARACION_ADUANERA);

    private final String etiqueta;

    TipoDocumento(String etiqueta) {
        this.etiqueta = etiqueta;
    }

    public String getEtiqueta() {
        return etiqueta;
    }
}
'''
F["documentos/EstadoValidacion.java"] = r'''package co.ritech.coffeeexport.documentos;

public enum EstadoValidacion {
    PENDIENTE, VALIDADO, RECHAZADO
}
'''
F["documentos/Documento.java"] = r'''package co.ritech.coffeeexport.documentos;

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
'''
F["documentos/DocumentoRepository.java"] = r'''package co.ritech.coffeeexport.documentos;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DocumentoRepository extends JpaRepository<Documento, Long> {
    List<Documento> findAllByOrderByIdDesc();

    List<Documento> findByExportacionIdOrderByIdDesc(Long exportacionId);
}
'''
F["documentos/DocumentoDto.java"] = r'''package co.ritech.coffeeexport.documentos;

import java.time.LocalDateTime;

public record DocumentoDto(Long id, Long exportacionId, String exportacionCodigo, String tipo, String nombreArchivo, long tamanoBytes,
                           String estadoValidacion, String subidoPor, LocalDateTime fecha) {
    public static DocumentoDto de(Documento d) {
        return new DocumentoDto(d.getId(), d.getExportacion().getId(), d.getExportacion().getCodigo(), d.getTipo().name(), d.getNombreArchivo(),
                d.getTamanoBytes(), d.getEstadoValidacion().name(), d.getSubidoPor().getNombre(), d.getCreatedAt());
    }
}
'''
F["documentos/DocumentoService.java"] = r'''package co.ritech.coffeeexport.documentos;

import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.PathResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

/** Documentación de exportación: certificados y aduanas (HU-14, HU-15, RF-20 a RF-22). */
@Service
public class DocumentoService {
    static final long MAXIMO_BYTES = 5L * 1024 * 1024;

    private final DocumentoRepository documentos;
    private final ExportacionRepository exportaciones;
    private final Path directorio;

    public DocumentoService(DocumentoRepository documentos, ExportacionRepository exportaciones, @Value("${app.storage.dir}") String dir) {
        this.documentos = documentos;
        this.exportaciones = exportaciones;
        this.directorio = Path.of(dir).toAbsolutePath().normalize();
    }

    /** RF-20: solo PDF de hasta 5 MB; se valida la extensión, el tipo MIME y la firma "%PDF" del contenido. */
    @Transactional
    public Documento subir(Long exportacionId, String tipo, MultipartFile archivo, Usuario usuario) {
        Exportacion ex = exportaciones.findById(exportacionId).orElseThrow(() -> new RecursoNoEncontradoException("Exportación no encontrada"));
        if (ex.getEstado() == EstadoExportacion.CANCELADA || ex.getEstado() == EstadoExportacion.ENTREGADA) {
            throw new ReglaNegocioException("No se pueden cargar documentos en una exportación cancelada o entregada");
        }
        TipoDocumento td = parsearTipo(tipo);
        if (archivo == null || archivo.isEmpty()) {
            throw new ReglaNegocioException("Seleccione un archivo");
        }
        String nombre = archivo.getOriginalFilename() == null ? "" : archivo.getOriginalFilename();
        String mime = archivo.getContentType();
        if (!nombre.toLowerCase().endsWith(".pdf") || (mime != null && !mime.equalsIgnoreCase("application/pdf"))) {
            throw new ReglaNegocioException("Solo se permiten archivos PDF");
        }
        if (archivo.getSize() > MAXIMO_BYTES) {
            throw new ReglaNegocioException("El archivo supera el tamaño máximo de 5 MB");
        }
        byte[] contenido;
        try {
            contenido = archivo.getBytes();
        } catch (IOException e) {
            throw new ReglaNegocioException("No se pudo leer el archivo");
        }
        if (contenido.length < 4 || !"%PDF".equals(new String(Arrays.copyOf(contenido, 4), StandardCharsets.ISO_8859_1))) {
            throw new ReglaNegocioException("Solo se permiten archivos PDF");
        }
        Path destino = directorio.resolve(String.valueOf(exportacionId)).resolve(UUID.randomUUID() + ".pdf");
        try {
            Files.createDirectories(destino.getParent());
            Files.write(destino, contenido);
        } catch (IOException e) {
            throw new ReglaNegocioException("No se pudo guardar el archivo");
        }
        Documento d = new Documento();
        d.setExportacion(ex);
        d.setTipo(td);
        d.setNombreArchivo(nombre.length() > 200 ? nombre.substring(nombre.length() - 200) : nombre);
        d.setRutaArchivo(destino.toString());
        d.setTamanoBytes(contenido.length);
        d.setSubidoPor(usuario);
        return documentos.save(d);
    }

    @Transactional
    public Documento cambiarValidacion(Long id, EstadoValidacion nuevo) {
        Documento d = obtener(id);
        if (d.getEstadoValidacion() != EstadoValidacion.PENDIENTE || nuevo == EstadoValidacion.PENDIENTE) {
            throw new ReglaNegocioException("Solo se puede validar o rechazar un documento pendiente");
        }
        d.setEstadoValidacion(nuevo);
        return documentos.save(d);
    }

    /** RF-21: tipos obligatorios que aún no tiene la exportación (un documento rechazado no cuenta). */
    @Transactional(readOnly = true)
    public List<TipoDocumento> faltantes(Long exportacionId) {
        List<TipoDocumento> presentes = documentos.findByExportacionIdOrderByIdDesc(exportacionId).stream()
                .filter(d -> d.getEstadoValidacion() != EstadoValidacion.RECHAZADO).map(Documento::getTipo).toList();
        return TipoDocumento.OBLIGATORIOS.stream().filter(t -> !presentes.contains(t)).toList();
    }

    @Transactional(readOnly = true)
    public Resource archivo(Long id) {
        Path ruta = Path.of(obtener(id).getRutaArchivo());
        if (!Files.exists(ruta)) {
            throw new RecursoNoEncontradoException("El archivo ya no está disponible");
        }
        return new PathResource(ruta);
    }

    @Transactional(readOnly = true)
    public Documento obtener(Long id) {
        return documentos.findById(id).orElseThrow(() -> new RecursoNoEncontradoException("Documento no encontrado"));
    }

    @Transactional(readOnly = true)
    public List<Documento> listar() {
        return documentos.findAllByOrderByIdDesc();
    }

    @Transactional(readOnly = true)
    public List<Documento> listarPorExportacion(Long exportacionId) {
        return documentos.findByExportacionIdOrderByIdDesc(exportacionId);
    }

    private static TipoDocumento parsearTipo(String tipo) {
        try {
            return TipoDocumento.valueOf(tipo.trim().toUpperCase());
        } catch (IllegalArgumentException | NullPointerException e) {
            throw new ReglaNegocioException("Tipo de documento no válido");
        }
    }
}
'''
F["documentos/DocumentoController.java"] = r'''package co.ritech.coffeeexport.documentos;

import co.ritech.coffeeexport.auth.AuthService;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.util.List;
import java.util.Map;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api")
public class DocumentoController {
    private final DocumentoService service;
    private final AuthService auth;

    public DocumentoController(DocumentoService service, AuthService auth) {
        this.service = service;
        this.auth = auth;
    }

    @GetMapping("/documentos")
    public List<DocumentoDto> listar() {
        return service.listar().stream().map(DocumentoDto::de).toList();
    }

    @GetMapping("/exportaciones/{id}/documentos")
    public List<DocumentoDto> porExportacion(@PathVariable Long id) {
        return service.listarPorExportacion(id).stream().map(DocumentoDto::de).toList();
    }

    /** Carga un PDF a una exportación (multipart: tipo + archivo). */
    @PostMapping(value = "/exportaciones/{id}/documentos", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseStatus(HttpStatus.CREATED)
    public DocumentoDto subir(@PathVariable Long id, @RequestParam("tipo") String tipo, @RequestParam("archivo") MultipartFile archivo,
                              Authentication a) {
        return DocumentoDto.de(service.subir(id, tipo, archivo, auth.actual(a)));
    }

    @PatchMapping("/documentos/{id}/validacion")
    public DocumentoDto validacion(@PathVariable Long id, @RequestBody Map<String, String> cuerpo) {
        try {
            return DocumentoDto.de(service.cambiarValidacion(id, EstadoValidacion.valueOf(String.valueOf(cuerpo.get("estado")).toUpperCase())));
        } catch (IllegalArgumentException e) {
            if (e instanceof ReglaNegocioException) {
                throw e;
            }
            throw new ReglaNegocioException("Estado de validación no válido");
        }
    }

    @GetMapping("/documentos/{id}/archivo")
    public ResponseEntity<Resource> archivo(@PathVariable Long id) {
        Documento d = service.obtener(id);
        return ResponseEntity.ok().contentType(MediaType.APPLICATION_PDF)
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + d.getNombreArchivo().replace("\"", "") + "\"")
                .body(service.archivo(id));
    }
}
'''

# ================================================================= pagos
F["pagos/Moneda.java"] = r'''package co.ritech.coffeeexport.pagos;

import co.ritech.coffeeexport.shared.ReglaNegocioException;

/** RR-07: solo USD y EUR. */
public enum Moneda {
    USD, EUR;

    public static Moneda de(String codigo) {
        try {
            return Moneda.valueOf(codigo.trim().toUpperCase());
        } catch (IllegalArgumentException | NullPointerException e) {
            throw new ReglaNegocioException("Moneda no soportada: solo USD o EUR");
        }
    }
}
'''
F["pagos/MetodoPago.java"] = r'''package co.ritech.coffeeexport.pagos;

public enum MetodoPago {
    TRANSFERENCIA, CARTA_CREDITO, OTRO
}
'''
F["pagos/EstadoPago.java"] = r'''package co.ritech.coffeeexport.pagos;

public enum EstadoPago {
    PENDIENTE, CONFIRMADO, RECHAZADO
}
'''
F["pagos/Pago.java"] = r'''package co.ritech.coffeeexport.pagos;

import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.usuarios.Usuario;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

@Entity
@Table(name = "pagos")
@Getter @Setter @NoArgsConstructor
public class Pago {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "exportacion_id", nullable = false)
    private Exportacion exportacion;
    @Column(nullable = false, precision = 14, scale = 2)
    private BigDecimal monto;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 3)
    private Moneda moneda;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 15)
    private MetodoPago metodo = MetodoPago.TRANSFERENCIA;
    @Column(length = 80)
    private String referencia;
    @Column(nullable = false)
    private LocalDate fechaPago;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 12)
    private EstadoPago estado = EstadoPago.PENDIENTE;
    @ManyToOne(optional = false, fetch = FetchType.EAGER) @JoinColumn(name = "registrado_por", nullable = false)
    private Usuario registradoPor;
    @CreationTimestamp @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
'''
F["pagos/PagoRepository.java"] = r'''package co.ritech.coffeeexport.pagos;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PagoRepository extends JpaRepository<Pago, Long> {
    List<Pago> findAllByOrderByIdDesc();

    List<Pago> findByExportacionId(Long exportacionId);
}
'''
F["pagos/PagoRequest.java"] = r'''package co.ritech.coffeeexport.pagos;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDate;

public record PagoRequest(
        @NotNull(message = "Seleccione una exportación") Long exportacionId,
        @NotNull(message = "Ingrese el monto") BigDecimal monto,
        @NotBlank(message = "Seleccione la moneda") String moneda,
        String metodo,
        String referencia,
        @NotNull(message = "Ingrese la fecha de pago") LocalDate fechaPago) {
}
'''
F["pagos/PagoDto.java"] = r'''package co.ritech.coffeeexport.pagos;

import java.math.BigDecimal;
import java.time.LocalDate;

public record PagoDto(Long id, Long exportacionId, String exportacionCodigo, String clienteNombre, BigDecimal monto, String moneda,
                      String metodo, String referencia, LocalDate fechaPago, String estado) {
    public static PagoDto de(Pago p) {
        return new PagoDto(p.getId(), p.getExportacion().getId(), p.getExportacion().getCodigo(), p.getExportacion().getCliente().getNombre(),
                p.getMonto(), p.getMoneda().name(), p.getMetodo().name(), p.getReferencia(), p.getFechaPago(), p.getEstado().name());
    }
}
'''
F["pagos/PagoService.java"] = r'''package co.ritech.coffeeexport.pagos;

import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import java.util.Set;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Pagos internacionales en USD o EUR (HU-16, HU-17, RF-23 a RF-25). */
@Service
public class PagoService {
    private static final Set<EstadoExportacion> FACTURABLES =
            Set.of(EstadoExportacion.EN_PREPARACION, EstadoExportacion.EN_TRANSITO, EstadoExportacion.ENTREGADA);

    private final PagoRepository pagos;
    private final ExportacionRepository exportaciones;
    private final BigDecimal tasaEurUsd;

    public PagoService(PagoRepository pagos, ExportacionRepository exportaciones, @Value("${app.tasa-eur-usd}") BigDecimal tasaEurUsd) {
        this.pagos = pagos;
        this.exportaciones = exportaciones;
        this.tasaEurUsd = tasaEurUsd;
    }

    @Transactional
    public Pago registrarPago(PagoRequest r, Usuario usuario) {
        Moneda moneda = Moneda.de(r.moneda());   // RR-07
        if (r.monto() == null || r.monto().compareTo(BigDecimal.ZERO) <= 0) {
            throw new ReglaNegocioException("El monto debe ser mayor que cero");
        }
        Exportacion ex = exportaciones.findById(r.exportacionId()).orElseThrow(() -> new ReglaNegocioException("La exportación no existe"));
        if (!FACTURABLES.contains(ex.getEstado())) {
            throw new ReglaNegocioException("Solo se registran pagos de exportaciones confirmadas");
        }
        Pago p = new Pago();
        p.setExportacion(ex);
        p.setMonto(r.monto().setScale(2, RoundingMode.HALF_UP));
        p.setMoneda(moneda);
        p.setMetodo(r.metodo() == null || r.metodo().isBlank() ? MetodoPago.TRANSFERENCIA : parsearMetodo(r.metodo()));
        p.setReferencia(r.referencia());
        p.setFechaPago(r.fechaPago());
        p.setEstado(EstadoPago.PENDIENTE);
        p.setRegistradoPor(usuario);
        return pagos.save(p);
    }

    @Transactional
    public Pago confirmar(Long id) {
        return resolver(id, EstadoPago.CONFIRMADO);
    }

    @Transactional
    public Pago rechazar(Long id) {
        return resolver(id, EstadoPago.RECHAZADO);
    }

    /** RF-24: saldo pendiente en USD = total de la exportación menos los pagos confirmados. */
    @Transactional(readOnly = true)
    public BigDecimal saldoPendiente(Long exportacionId) {
        Exportacion ex = exportaciones.findById(exportacionId).orElseThrow(() -> new RecursoNoEncontradoException("Exportación no encontrada"));
        BigDecimal confirmado = pagos.findByExportacionId(exportacionId).stream().filter(p -> p.getEstado() == EstadoPago.CONFIRMADO)
                .map(this::aUsd).reduce(BigDecimal.ZERO, BigDecimal::add);
        return ex.getTotalUsd().subtract(confirmado).max(BigDecimal.ZERO).setScale(2, RoundingMode.HALF_UP);
    }

    /** Conversión de un pago a USD con la tasa EUR/USD configurable. */
    public BigDecimal aUsd(Pago p) {
        return p.getMoneda() == Moneda.EUR ? p.getMonto().multiply(tasaEurUsd) : p.getMonto();
    }

    @Transactional(readOnly = true)
    public List<Pago> listar() {
        return pagos.findAllByOrderByIdDesc();
    }

    private Pago resolver(Long id, EstadoPago nuevo) {
        Pago p = pagos.findById(id).orElseThrow(() -> new RecursoNoEncontradoException("Pago no encontrado"));
        if (p.getEstado() != EstadoPago.PENDIENTE) {
            throw new ReglaNegocioException("Solo se pueden confirmar o rechazar pagos pendientes");
        }
        p.setEstado(nuevo);
        return pagos.save(p);
    }

    private static MetodoPago parsearMetodo(String metodo) {
        try {
            return MetodoPago.valueOf(metodo.trim().toUpperCase());
        } catch (IllegalArgumentException e) {
            throw new ReglaNegocioException("Método de pago no válido");
        }
    }
}
'''
F["pagos/PagoController.java"] = r'''package co.ritech.coffeeexport.pagos;

import co.ritech.coffeeexport.auth.AuthService;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/pagos")
public class PagoController {
    private final PagoService service;
    private final AuthService auth;

    public PagoController(PagoService service, AuthService auth) {
        this.service = service;
        this.auth = auth;
    }

    @GetMapping
    public List<PagoDto> listar() {
        return service.listar().stream().map(PagoDto::de).toList();
    }

    @GetMapping("/saldo/{exportacionId}")
    public Map<String, BigDecimal> saldo(@PathVariable Long exportacionId) {
        return Map.of("saldoPendienteUsd", service.saldoPendiente(exportacionId));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public PagoDto registrar(@Valid @RequestBody PagoRequest r, Authentication a) {
        return PagoDto.de(service.registrarPago(r, auth.actual(a)));
    }

    @PatchMapping("/{id}/estado")
    public PagoDto estado(@PathVariable Long id, @RequestBody Map<String, String> cuerpo) {
        String estado = String.valueOf(cuerpo.get("estado")).toUpperCase();
        return switch (estado) {
            case "CONFIRMADO" -> PagoDto.de(service.confirmar(id));
            case "RECHAZADO" -> PagoDto.de(service.rechazar(id));
            default -> throw new ReglaNegocioException("Estado de pago no válido: CONFIRMADO o RECHAZADO");
        };
    }
}
'''

for ruta, contenido in F.items():
    destino = os.path.normpath(os.path.join(BASE, ruta))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    open(destino, "w", encoding="utf-8", newline="\n").write(contenido)
print(len(F), "archivos")
