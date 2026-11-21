package co.ritech.coffeeexport.dashboard;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record KpiDto(long totalExportaciones, long exportacionesMes, long exportacionesMesAnterior, long clientesActivos,
                     long clientesRegistrados, BigDecimal inventarioKg, long productosBajoMinimo, BigDecimal ventasMesUsd,
                     BigDecimal ventasMesAnteriorUsd, List<Par> exportacionesPorPais, List<ParKg> productosMasVendidos,
                     List<Ultima> ultimasExportaciones) {
    public record Par(String pais, long cantidad) {
    }

    public record ParKg(String producto, BigDecimal kg) {
    }

    public record Ultima(String codigo, String cliente, String pais, String producto, LocalDate fechaEnvio, String estado) {
    }
}
