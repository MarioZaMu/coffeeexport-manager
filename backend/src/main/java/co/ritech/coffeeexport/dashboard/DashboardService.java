package co.ritech.coffeeexport.dashboard;

import co.ritech.coffeeexport.clientes.ClienteRepository;
import co.ritech.coffeeexport.dashboard.KpiDto.Par;
import co.ritech.coffeeexport.dashboard.KpiDto.ParKg;
import co.ritech.coffeeexport.dashboard.KpiDto.Ultima;
import co.ritech.coffeeexport.exportaciones.EstadoExportacion;
import co.ritech.coffeeexport.exportaciones.Exportacion;
import co.ritech.coffeeexport.exportaciones.ExportacionRepository;
import co.ritech.coffeeexport.inventario.Inventario;
import co.ritech.coffeeexport.inventario.InventarioRepository;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.ZoneId;
import java.util.*;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Indicadores del dashboard ejecutivo (HU-20, HU-21, RF-29 a RF-31). */
@Service
public class DashboardService {
    private static final Set<EstadoExportacion> SIN_VENTA = Set.of(EstadoExportacion.CANCELADA, EstadoExportacion.BORRADOR);

    private final ExportacionRepository exportaciones;
    private final ClienteRepository clientes;
    private final InventarioRepository inventario;

    public DashboardService(ExportacionRepository exportaciones, ClienteRepository clientes, InventarioRepository inventario) {
        this.exportaciones = exportaciones;
        this.clientes = clientes;
        this.inventario = inventario;
    }

    @Transactional(readOnly = true)
    public KpiDto kpis() {
        List<Exportacion> todas = exportaciones.findAllByOrderByIdDesc();
        YearMonth mes = YearMonth.now(ZoneId.of("America/Bogota"));
        YearMonth anterior = mes.minusMonths(1);
        List<Exportacion> vendidas = todas.stream().filter(e -> !SIN_VENTA.contains(e.getEstado())).toList();

        BigDecimal ventasMes = suma(vendidas, mes), ventasAnt = suma(vendidas, anterior);
        long delMes = todas.stream().filter(e -> YearMonth.from(e.getFechaEnvio()).equals(mes)).count();
        long delAnterior = todas.stream().filter(e -> YearMonth.from(e.getFechaEnvio()).equals(anterior)).count();

        Map<String, Long> porPais = todas.stream().filter(e -> e.getEstado() != EstadoExportacion.CANCELADA)
                .collect(Collectors.groupingBy(Exportacion::getPaisDestino, Collectors.counting()));
        List<Par> paises = porPais.entrySet().stream().sorted((a, b) -> Long.compare(b.getValue(), a.getValue())).limit(6)
                .map(e -> new Par(e.getKey(), e.getValue())).toList();

        Map<String, BigDecimal> kgProducto = new HashMap<>();
        vendidas.forEach(e -> e.getDetalles().forEach(d -> kgProducto.merge(d.getProducto().getNombre(), d.getCantidadKg(), BigDecimal::add)));
        List<ParKg> masVendidos = kgProducto.entrySet().stream().sorted((a, b) -> b.getValue().compareTo(a.getValue())).limit(4)
                .map(e -> new ParKg(e.getKey(), e.getValue())).toList();

        List<Ultima> ultimas = todas.stream().sorted(Comparator.comparing(Exportacion::getFechaEnvio).reversed().thenComparing(Exportacion::getId, Comparator.reverseOrder()))
                .limit(5).map(e -> new Ultima(e.getCodigo(), e.getCliente().getNombre(), e.getPaisDestino(),
                        e.getDetalles().isEmpty() ? "" : e.getDetalles().get(0).getProducto().getNombre(), e.getFechaEnvio(), e.getEstado().name())).toList();

        return new KpiDto(todas.size(), delMes, delAnterior, clientes.countByActivoTrue(), clientes.count(), inventario.totalGeneral(),
                productosBajoMinimo(), ventasMes, ventasAnt, paises, masVendidos, ultimas);
    }

    private static BigDecimal suma(List<Exportacion> lista, YearMonth mes) {
        return lista.stream().filter(e -> YearMonth.from(e.getFechaEnvio()).equals(mes)).map(Exportacion::getTotalUsd).reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    private long productosBajoMinimo() {
        Map<Long, BigDecimal[]> p = new HashMap<>();   // [stock, mínimo]
        for (Inventario i : inventario.findAllByOrderByIdAsc()) {
            BigDecimal[] a = p.computeIfAbsent(i.getProducto().getId(), k -> new BigDecimal[]{BigDecimal.ZERO, BigDecimal.ZERO});
            a[0] = a[0].add(i.getCantidadKg());
            a[1] = a[1].add(i.getStockMinimoKg());
        }
        return p.values().stream().filter(a -> a[1].signum() > 0 && a[0].compareTo(a[1]) < 0).count();
    }
}
