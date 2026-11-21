package co.ritech.coffeeexport.documentos;

import java.time.LocalDateTime;

public record DocumentoDto(Long id, Long exportacionId, String exportacionCodigo, String tipo, String nombreArchivo, long tamanoBytes,
                           String estadoValidacion, String subidoPor, LocalDateTime fecha) {
    public static DocumentoDto de(Documento d) {
        return new DocumentoDto(d.getId(), d.getExportacion().getId(), d.getExportacion().getCodigo(), d.getTipo().name(), d.getNombreArchivo(),
                d.getTamanoBytes(), d.getEstadoValidacion().name(), d.getSubidoPor().getNombre(), d.getCreatedAt());
    }
}
