package co.ritech.coffeeexport.shared;

import co.ritech.coffeeexport.clientes.ClienteDuplicadoException;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

/** Traduce las excepciones del dominio a respuestas HTTP coherentes con los criterios de aceptación. */
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(StockInsuficienteException.class)
    public ResponseEntity<ApiError> stock(StockInsuficienteException e) {
        return ResponseEntity.status(HttpStatus.CONFLICT).body(ApiError.de(e.getMessage()));
    }

    @ExceptionHandler(ClienteDuplicadoException.class)
    public ResponseEntity<ApiError> duplicado(ClienteDuplicadoException e) {
        return ResponseEntity.status(HttpStatus.CONFLICT).body(ApiError.de(e.getMessage()));
    }

    @ExceptionHandler(ReglaNegocioException.class)
    public ResponseEntity<ApiError> regla(ReglaNegocioException e) {
        return ResponseEntity.badRequest().body(ApiError.de(e.getMessage()));
    }

    @ExceptionHandler(RecursoNoEncontradoException.class)
    public ResponseEntity<ApiError> noEncontrado(RecursoNoEncontradoException e) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(ApiError.de(e.getMessage()));
    }

    @ExceptionHandler(BadCredentialsException.class)
    public ResponseEntity<ApiError> credenciales(BadCredentialsException e) {
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiError.de("Credenciales incorrectas"));
    }

    @ExceptionHandler(DisabledException.class)
    public ResponseEntity<ApiError> inactivo(DisabledException e) {
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(ApiError.de("Su usuario está inactivo. Contacte al administrador."));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> validacion(MethodArgumentNotValidException e) {
        Map<String, String> campos = new LinkedHashMap<>();
        e.getBindingResult().getFieldErrors().forEach(f -> campos.putIfAbsent(f.getField(), f.getDefaultMessage()));
        String primero = campos.values().stream().findFirst().orElse("Datos inválidos");
        return ResponseEntity.badRequest().body(new ApiError(primero, campos));
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiError> cuerpo(HttpMessageNotReadableException e) {
        return ResponseEntity.badRequest().body(ApiError.de("El cuerpo de la petición no es válido"));
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<ApiError> tamano(MaxUploadSizeExceededException e) {
        return ResponseEntity.badRequest().body(ApiError.de("El archivo supera el tamaño máximo de 5 MB"));
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<ApiError> integridad(DataIntegrityViolationException e) {
        return ResponseEntity.status(HttpStatus.CONFLICT).body(ApiError.de("La operación viola una restricción de datos (valor duplicado o relación existente)"));
    }
}
