package co.ritech.coffeeexport.clientes;

import co.ritech.coffeeexport.shared.ReglaNegocioException;

/** Ya existe un cliente con la misma identificación fiscal (HU-02). */
public class ClienteDuplicadoException extends ReglaNegocioException {
    public ClienteDuplicadoException(String mensaje) {
        super(mensaje);
    }
}
