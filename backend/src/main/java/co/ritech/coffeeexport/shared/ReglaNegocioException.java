package co.ritech.coffeeexport.shared;

/** Se incumple una regla de negocio (dato inválido, estado no permitido...). Equivale a IllegalArgumentException. */
public class ReglaNegocioException extends IllegalArgumentException {
    public ReglaNegocioException(String mensaje) {
        super(mensaje);
    }
}
