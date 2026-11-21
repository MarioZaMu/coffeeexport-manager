package co.ritech.coffeeexport.reportes;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record ReporteDto(String titulo, String tipo, LocalDate desde, LocalDate hasta, long totalExportaciones, BigDecimal ventasUsd,
                         long clientesConEnvios, List<Par> porPais, List<ParMonto> productosTop, List<String> cabeceras,
                         List<List<Object>> filas) {
    public record Par(String clave, long valor) {
    }

    public record ParMonto(String clave, BigDecimal valor) {
    }
}
