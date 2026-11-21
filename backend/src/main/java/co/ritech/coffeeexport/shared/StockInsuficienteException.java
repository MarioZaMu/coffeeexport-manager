package co.ritech.coffeeexport.shared;

/** Se pide más inventario del disponible (RF-14). */
public class StockInsuficienteException extends ReglaNegocioException {
    public StockInsuficienteException(String mensaje) {
        super(mensaje);
    }
}
