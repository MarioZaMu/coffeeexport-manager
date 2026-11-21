package co.ritech.coffeeexport.integracion;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.options;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;

/** CORS: el sitio web (otro puerto) debe poder llamar a la API con cookies, y ningún otro origen. */
class CorsIT extends IntegracionBase {

    @Test
    @DisplayName("[HU-01][RNF-05] Un origen local permitido recibe las cabeceras CORS con credenciales (preflight y petición real)")
    void origenPermitido() throws Exception {
        mvc.perform(options("/api/auth/login").header(HttpHeaders.ORIGIN, "http://127.0.0.1:5500")
                        .header(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD, "POST").header(HttpHeaders.ACCESS_CONTROL_REQUEST_HEADERS, "content-type"))
                .andExpect(status().isOk()).andExpect(header().string(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN, "http://127.0.0.1:5500"))
                .andExpect(header().string(HttpHeaders.ACCESS_CONTROL_ALLOW_CREDENTIALS, "true"));
        mvc.perform(post("/api/auth/login").header(HttpHeaders.ORIGIN, "http://localhost:8000").contentType(MediaType.APPLICATION_JSON)
                        .content(cuerpo("email", "admin@ritech.co", "password", CLAVE)))
                .andExpect(status().isOk()).andExpect(header().string(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN, "http://localhost:8000"));
    }

    @Test
    @DisplayName("[HU-01][RNF-05] Un origen desconocido es rechazado por CORS (403) y no recibe cabeceras de permiso")
    void origenNoPermitido() throws Exception {
        mvc.perform(post("/api/auth/login").header(HttpHeaders.ORIGIN, "https://sitio-malicioso.example").contentType(MediaType.APPLICATION_JSON)
                        .content(cuerpo("email", "admin@ritech.co", "password", CLAVE)))
                .andExpect(status().isForbidden()).andExpect(header().doesNotExist(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN));
    }
}
