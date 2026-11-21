package co.ritech.coffeeexport.unit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import co.ritech.coffeeexport.Fixtures;
import co.ritech.coffeeexport.documentos.*;
import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import co.ritech.coffeeexport.usuarios.Usuario;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;

@ExtendWith(MockitoExtension.class)
class DocumentoServiceTest {
    @Mock DocumentoRepository documentos;
    @Mock ExportacionRepository exportaciones;
    @TempDir Path carpeta;
    DocumentoService service;
    final Usuario operador = Fixtures.usuario(3L, "exportaciones@ritech.co", "x", "OP_EXPORTACIONES", true);
    Exportacion ex;

    @BeforeEach
    void preparar() {
        service = new DocumentoService(documentos, exportaciones, carpeta.toString());
        ex = Fixtures.exportacion(1L, Fixtures.cliente(1L, "DE", true), operador, LocalDate.now().plusDays(3));
        ex.setEstado(EstadoExportacion.EN_PREPARACION);
        lenient().when(exportaciones.findById(1L)).thenReturn(Optional.of(ex));
    }

    private static MockMultipartFile pdf(String nombre, String mime, byte[] contenido) {
        return new MockMultipartFile("archivo", nombre, mime, contenido);
    }

    @Test
    @DisplayName("[HU-14][RF-20] Un PDF válido se guarda y queda PENDIENTE de validación")
    void pdfValido() throws Exception {
        when(documentos.save(any(Documento.class))).thenAnswer(i -> i.getArgument(0));
        Documento d = service.subir(1L, "fitosanitario", pdf("fito.pdf", "application/pdf", "%PDF-1.4 contenido".getBytes()), operador);
        assertThat(d.getTipo()).isEqualTo(TipoDocumento.FITOSANITARIO);
        assertThat(d.getEstadoValidacion()).isEqualTo(EstadoValidacion.PENDIENTE);
        assertThat(Files.exists(Path.of(d.getRutaArchivo()))).isTrue();
    }

    @Test
    @DisplayName("[HU-14][RF-20] Se rechazan archivos que no son PDF, aunque cambien la extensión")
    void noPdf() {
        assertThatThrownBy(() -> service.subir(1L, "OTRO", pdf("virus.exe", "application/octet-stream", "MZ".getBytes()), operador))
                .isInstanceOf(ReglaNegocioException.class).hasMessage("Solo se permiten archivos PDF");
        assertThatThrownBy(() -> service.subir(1L, "OTRO", pdf("falso.pdf", "application/pdf", "MZ-no-soy-pdf".getBytes()), operador))
                .isInstanceOf(ReglaNegocioException.class).hasMessage("Solo se permiten archivos PDF");
        verify(documentos, never()).save(any());
    }

    @Test
    @DisplayName("[HU-14][RF-20] Un archivo de más de 5 MB se rechaza")
    void demasiadoGrande() {
        byte[] grande = new byte[5 * 1024 * 1024 + 1];
        System.arraycopy("%PDF".getBytes(), 0, grande, 0, 4);
        assertThatThrownBy(() -> service.subir(1L, "OTRO", pdf("grande.pdf", "application/pdf", grande), operador))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("5 MB");
    }

    @Test
    @DisplayName("[HU-15][RF-21] faltantes() lista los obligatorios sin cargar e ignora los rechazados")
    void faltantes() {
        Documento ok = doc(TipoDocumento.CERTIFICADO_ORIGEN, EstadoValidacion.VALIDADO);
        Documento rechazado = doc(TipoDocumento.FITOSANITARIO, EstadoValidacion.RECHAZADO);
        when(documentos.findByExportacionIdOrderByIdDesc(1L)).thenReturn(List.of(ok, rechazado));
        assertThat(service.faltantes(1L)).containsExactly(TipoDocumento.FITOSANITARIO, TipoDocumento.FACTURA_COMERCIAL, TipoDocumento.DECLARACION_ADUANERA);
    }

    @Test
    @DisplayName("[HU-14][RF-22] En una exportación cancelada no se cargan documentos")
    void exportacionCancelada() {
        ex.setEstado(EstadoExportacion.CANCELADA);
        assertThatThrownBy(() -> service.subir(1L, "OTRO", pdf("a.pdf", "application/pdf", "%PDF".getBytes()), operador))
                .isInstanceOf(ReglaNegocioException.class).hasMessageContaining("cancelada o entregada");
    }

    private Documento doc(TipoDocumento tipo, EstadoValidacion estado) {
        Documento d = new Documento();
        d.setTipo(tipo);
        d.setEstadoValidacion(estado);
        return d;
    }
}
