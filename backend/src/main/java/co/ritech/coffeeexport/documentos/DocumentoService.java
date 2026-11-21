package co.ritech.coffeeexport.documentos;

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
