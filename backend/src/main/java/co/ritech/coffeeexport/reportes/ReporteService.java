package co.ritech.coffeeexport.reportes;

import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.inventario.Inventario;
import co.ritech.coffeeexport.inventario.InventarioRepository;
import co.ritech.coffeeexport.reportes.ReporteDto.Par;
import co.ritech.coffeeexport.reportes.ReporteDto.ParMonto;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Reportes por rango de fechas (HU-18, RF-26, RF-28). La exportación a PDF y Excel se hace en la interfaz (RF-27). */
@Service
public class ReporteService {
    private static final Set<String> TIPOS = Set.of("exportaciones", "ventas", "existencias");
    private static final List<EstadoExportacion> EXCLUIDOS = List.of(EstadoExportacion.CANCELADA, EstadoExportacion.BORRADOR);

    private final ExportacionRepository exportaciones;
    private final InventarioRepository inventario;

    public ReporteService(ExportacionRepository exportaciones, InventarioRepository inventario) {
        this.exportaciones = exportaciones;
        this.inventario = inventario;
    }

    @Transactional(readOnly = true)
    public ReporteDto generarReporte(LocalDate desde, LocalDate hasta, String tipo) {
        if (desde == null || hasta == null) {
            throw new ReglaNegocioException("Seleccione el rango de fechas");
        }
        if (hasta.isBefore(desde)) {
            throw new ReglaNegocioException("La fecha final no puede ser anterior a la fecha inicial");
        }
        String t = tipo == null || tipo.isBlank() ? "exportaciones" : tipo.trim().toLowerCase();
        if (!TIPOS.contains(t)) {
            throw new ReglaNegocioException("Tipo de reporte no válido: exportaciones, ventas o existencias");
        }
        List<Exportacion> lista = exportaciones.enRango(desde, hasta, EXCLUIDOS);
        BigDecimal ventas = lista.stream().map(Exportacion::getTotalUsd).reduce(BigDecimal.ZERO, BigDecimal::add);
        long clientes = lista.stream().map(e -> e.getCliente().getId()).distinct().count();

        Map<String, Long> porPais = lista.stream().collect(Collectors.groupingBy(Exportacion::getPaisDestino, Collectors.counting()));
        Map<String, BigDecimal> porProducto = new HashMap<>();
        lista.forEach(e -> e.getDetalles().forEach(d -> porProducto.merge(d.getProducto().getNombre(), d.getSubtotal(), BigDecimal::add)));

        String titulo;
        List<String> cabeceras;
        List<List<Object>> filas = new ArrayList<>();
        switch (t) {
            case "ventas" -> {
                titulo = "Ventas por producto y país";
                cabeceras = List.of("Producto", "País", "Cantidad (kg)", "Ventas (USD)", "% del total");
                Map<String, BigDecimal[]> agg = new TreeMap<>();
                lista.forEach(e -> e.getDetalles().forEach(d -> {
                    BigDecimal[] a = agg.computeIfAbsent(d.getProducto().getNombre() + "|" + e.getPaisDestino(), k -> new BigDecimal[]{BigDecimal.ZERO, BigDecimal.ZERO});
                    a[0] = a[0].add(d.getCantidadKg());
                    a[1] = a[1].add(d.getSubtotal());
                }));
                agg.entrySet().stream().sorted((x, y) -> y.getValue()[1].compareTo(x.getValue()[1])).forEach(en -> {
                    String[] k = en.getKey().split("\\|");
                    BigDecimal pct = ventas.signum() == 0 ? BigDecimal.ZERO : en.getValue()[1].multiply(BigDecimal.valueOf(100)).divide(ventas, 1, RoundingMode.HALF_UP);
                    filas.add(List.of(k[0], k[1], en.getValue()[0], en.getValue()[1], pct + " %"));
                });
            }
            case "existencias" -> {
                titulo = "Existencias actuales";
                cabeceras = List.of("Producto", "Bodega", "Stock (kg)", "Mínimo (kg)", "Estado");
                for (Inventario i : inventario.findAllByOrderByIdAsc()) {
                    boolean bajo = i.getStockMinimoKg().signum() > 0 && i.getCantidadKg().compareTo(i.getStockMinimoKg()) < 0;
                    filas.add(List.of(i.getProducto().getNombre(), i.getBodega().getNombre(), i.getCantidadKg(), i.getStockMinimoKg(), bajo ? "Bajo mínimo" : "Normal"));
                }
            }
            default -> {
                titulo = "Detalle de exportaciones";
                cabeceras = List.of("Código", "Cliente", "País", "Cantidad (kg)", "Total (USD)", "Fecha de envío", "Estado");
                lista.forEach(e -> filas.add(List.of(e.getCodigo(), e.getCliente().getNombre(), e.getPaisDestino(), e.getTotalKg(), e.getTotalUsd(),
                        e.getFechaEnvio().toString(), e.getEstado().name())));
            }
        }
        List<Par> paises = porPais.entrySet().stream().sorted((a, b) -> Long.compare(b.getValue(), a.getValue())).map(e -> new Par(e.getKey(), e.getValue())).toList();
        List<ParMonto> top = porProducto.entrySet().stream().sorted((a, b) -> b.getValue().compareTo(a.getValue())).limit(5)
                .map(e -> new ParMonto(e.getKey(), e.getValue().setScale(2, RoundingMode.HALF_UP))).toList();
        return new ReporteDto(titulo, t, desde, hasta, lista.size(), ventas.setScale(2, RoundingMode.HALF_UP), clientes, paises, top, cabeceras, filas);
    }
}
