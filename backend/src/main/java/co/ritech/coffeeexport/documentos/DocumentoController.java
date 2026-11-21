package co.ritech.coffeeexport.documentos;

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
