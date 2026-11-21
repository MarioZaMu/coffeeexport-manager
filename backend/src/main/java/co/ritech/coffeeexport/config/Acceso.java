package co.ritech.coffeeexport.config;

import java.util.List;
import java.util.Map;

/**
 * Matriz de permisos por módulo (RF-04, RNF-03). Es la misma del prototipo web (PERMISOS en data.js):
 * "leer" incluye a quienes pueden escribir.
 */
public final class Acceso {
    public static final String ADMIN = "ADMIN", GERENTE = "GERENTE", OP_EXPORTACIONES = "OP_EXPORTACIONES", OP_BODEGA = "OP_BODEGA", CONTADOR = "CONTADOR";
    public static final List<String> ROLES = List.of(ADMIN, GERENTE, OP_EXPORTACIONES, OP_BODEGA, CONTADOR);

    public record Modulo(String[] leer, String[] escribir) {
    }

    public static final Map<String, Modulo> MODULOS = Map.ofEntries(
            Map.entry("dashboard", new Modulo(new String[]{ADMIN, GERENTE}, new String[]{})),
            Map.entry("clientes", new Modulo(new String[]{ADMIN, GERENTE, OP_EXPORTACIONES}, new String[]{ADMIN, OP_EXPORTACIONES})),
            Map.entry("productos", new Modulo(new String[]{ADMIN, GERENTE, OP_EXPORTACIONES, OP_BODEGA}, new String[]{ADMIN})),
            Map.entry("inventario", new Modulo(new String[]{ADMIN, GERENTE, OP_EXPORTACIONES, OP_BODEGA}, new String[]{ADMIN, OP_BODEGA})),
            Map.entry("exportaciones", new Modulo(new String[]{ADMIN, GERENTE, OP_EXPORTACIONES, CONTADOR}, new String[]{ADMIN, OP_EXPORTACIONES})),
            Map.entry("documentos", new Modulo(new String[]{ADMIN, GERENTE, OP_EXPORTACIONES}, new String[]{ADMIN, OP_EXPORTACIONES})),
            Map.entry("pagos", new Modulo(new String[]{ADMIN, GERENTE, CONTADOR}, new String[]{ADMIN, CONTADOR})),
            Map.entry("reportes", new Modulo(new String[]{ADMIN, GERENTE, CONTADOR}, new String[]{})),
            Map.entry("usuarios", new Modulo(new String[]{ADMIN}, new String[]{ADMIN})));

    private Acceso() {
    }
}
