package co.ritech.coffeeexport.pagos;

import co.ritech.coffeeexport.shared.ReglaNegocioException;

/** RR-07: solo USD y EUR. */
public enum Moneda {
    USD, EUR;

    public static Moneda de(String codigo) {
        try {
            return Moneda.valueOf(codigo.trim().toUpperCase());
        } catch (IllegalArgumentException | NullPointerException e) {
            throw new ReglaNegocioException("Moneda no soportada: solo USD o EUR");
        }
    }
}
