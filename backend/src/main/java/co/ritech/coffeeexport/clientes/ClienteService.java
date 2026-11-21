package co.ritech.coffeeexport.clientes;

import co.ritech.coffeeexport.shared.Paises;
import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Gestión de clientes de la Unión Europea (HU-02, RF-05 a RF-08). */
@Service
public class ClienteService {
    private final ClienteRepository repo;

    public ClienteService(ClienteRepository repo) {
        this.repo = repo;
    }

    @Transactional
    public Cliente registrarCliente(ClienteRequest r) {
        validar(r, null);
        Cliente c = new Cliente();
        copiar(r, c);
        c.setActivo(true);
        c.setFechaConsentimiento(LocalDateTime.now());
        return repo.save(c);
    }

    @Transactional
    public Cliente actualizarCliente(Long id, ClienteRequest r) {
        Cliente c = obtener(id);
        validar(r, id);
        boolean tenia = c.isConsentimientoDatos();
        copiar(r, c);
        if (!tenia || c.getFechaConsentimiento() == null) {
            c.setFechaConsentimiento(LocalDateTime.now());
        }
        return repo.save(c);
    }

    /** RF-06: los clientes se desactivan, no se borran, para conservar su historial. */
    @Transactional
    public Cliente cambiarEstado(Long id, boolean activo) {
        Cliente c = obtener(id);
        c.setActivo(activo);
        return repo.save(c);
    }

    @Transactional(readOnly = true)
    public List<Cliente> buscar(String q, String pais, Boolean activo) {
        String texto = q == null || q.isBlank() ? null : q.trim();
        String codigo = pais == null || pais.isBlank() ? null : pais.trim().toUpperCase();
        return repo.buscar(texto, codigo, activo);
    }

    @Transactional(readOnly = true)
    public Cliente obtener(Long id) {
        return repo.findById(id).orElseThrow(() -> new RecursoNoEncontradoException("Cliente no encontrado"));
    }

    private void validar(ClienteRequest r, Long idActual) {
        if (!Paises.esUe(r.pais())) {
            throw new ReglaNegocioException("Seleccione un país perteneciente a la Unión Europea");
        }
        if (!Boolean.TRUE.equals(r.consentimientoDatos())) {
            throw new ReglaNegocioException("Se requiere el consentimiento de tratamiento de datos (GDPR)");
        }
        String nif = r.identificacionFiscal().trim();
        boolean duplicado = idActual == null
                ? repo.existsByIdentificacionFiscalIgnoreCase(nif)
                : repo.findByIdentificacionFiscalIgnoreCase(nif).filter(o -> !o.getId().equals(idActual)).isPresent();
        if (duplicado) {
            throw new ClienteDuplicadoException("Ya existe un cliente con esa identificación fiscal");
        }
    }

    private void copiar(ClienteRequest r, Cliente c) {
        c.setNombre(r.nombre().trim());
        c.setPais(r.pais().trim().toUpperCase());
        c.setIdentificacionFiscal(r.identificacionFiscal().trim());
        c.setContactoNombre(r.contactoNombre().trim());
        c.setContactoEmail(r.contactoEmail().trim());
        c.setContactoTelefono(r.contactoTelefono());
        c.setDireccion(r.direccion());
        c.setConsentimientoDatos(true);
    }
}
