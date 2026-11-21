package co.ritech.coffeeexport.shared;

import java.util.Set;

/** Países de la Unión Europea (ISO 3166-1 alfa-2), RF-05. */
public final class Paises {
    public static final Set<String> UE = Set.of("DE", "NL", "BE", "FR", "IT", "ES", "PT", "AT", "IE", "SE", "DK", "FI", "PL", "CZ",
            "GR", "HU", "RO", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "LU", "MT", "CY");

    private Paises() {
    }

    public static boolean esUe(String codigo) {
        return codigo != null && UE.contains(codigo.trim().toUpperCase());
    }
}
