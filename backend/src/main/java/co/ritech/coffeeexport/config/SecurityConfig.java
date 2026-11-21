package co.ritech.coffeeexport.config;

import co.ritech.coffeeexport.shared.ApiError;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

/** Autorización en el backend por URL y método (RNF-03): sin sesión 401, sin permiso 403. */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();   // RNF-01
    }

    @Bean
    public SecurityFilterChain filtro(HttpSecurity http, ObjectMapper json) throws Exception {
        http.csrf(AbstractHttpConfigurer::disable)   // API con cookie SameSite=Lax y CORS restringido
            .cors(Customizer.withDefaults())
            .headers(h -> h.frameOptions(f -> f.deny()))
            .exceptionHandling(e -> e
                .authenticationEntryPoint((req, res, ex) -> escribir(json, res, 401, "Debe iniciar sesión"))
                .accessDeniedHandler((req, res, ex) -> escribir(json, res, 403, "Su rol no tiene permiso para esta acción")))
            .authorizeHttpRequests(a -> {
                a.requestMatchers("/api/auth/login", "/actuator/health").permitAll();
                a.requestMatchers("/api/auth/**").authenticated();
                regla(a, "/api/clientes/**", "clientes");
                regla(a, "/api/productos/**", "productos");
                regla(a, "/api/inventario/**", "inventario");
                regla(a, "/api/exportaciones/**", "exportaciones");
                regla(a, "/api/documentos/**", "documentos");
                regla(a, "/api/pagos/**", "pagos");
                regla(a, "/api/reportes/**", "reportes");
                regla(a, "/api/dashboard/**", "dashboard");
                regla(a, "/api/usuarios/**", "usuarios");
                a.requestMatchers("/api/snapshot").authenticated();
                a.anyRequest().denyAll();
            });
        return http.build();
    }

    private static void regla(org.springframework.security.config.annotation.web.configurers.AuthorizeHttpRequestsConfigurer<HttpSecurity>.AuthorizationManagerRequestMatcherRegistry a,
                              String ruta, String modulo) {
        Acceso.Modulo m = Acceso.MODULOS.get(modulo);
        a.requestMatchers(HttpMethod.GET, ruta).hasAnyRole(m.leer());
        if (m.escribir().length > 0) {
            a.requestMatchers(ruta).hasAnyRole(m.escribir());   // POST, PUT, PATCH, DELETE
        }
        a.requestMatchers(ruta).denyAll();
    }

    private static void escribir(ObjectMapper json, jakarta.servlet.http.HttpServletResponse res, int estado, String mensaje) throws java.io.IOException {
        res.setStatus(estado);
        res.setContentType(MediaType.APPLICATION_JSON_VALUE + ";charset=UTF-8");
        json.writeValue(res.getWriter(), ApiError.de(mensaje));
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource(@Value("${app.cors.origenes}") List<String> origenes) {   // el nombre del bean es el que busca Spring Security
        CorsConfiguration c = new CorsConfiguration();
        c.setAllowedOriginPatterns(origenes);
        c.setAllowedMethods(List.of("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        c.setAllowedHeaders(List.of("*"));
        c.setAllowCredentials(true);
        UrlBasedCorsConfigurationSource fuente = new UrlBasedCorsConfigurationSource();
        fuente.registerCorsConfiguration("/api/**", c);
        return fuente;
    }
}
