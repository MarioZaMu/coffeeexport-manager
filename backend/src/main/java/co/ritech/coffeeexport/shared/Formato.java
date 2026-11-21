package co.ritech.coffeeexport.shared;

import java.math.BigDecimal;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.Locale;

/** Formato de números en es-CO (1.200 kg), igual que la interfaz. */
public final class Formato {
    private static final DecimalFormatSymbols SIMBOLOS = new DecimalFormatSymbols(Locale.forLanguageTag("es-CO"));

    private Formato() {
    }

    public static String kg(BigDecimal valor) {
        return new DecimalFormat("#,##0.##", SIMBOLOS).format(valor) + " kg";
    }
}
