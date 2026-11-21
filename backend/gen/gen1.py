# -*- coding: utf-8 -*-
"""Generador de fuentes Java del backend (bloque 1: compartido, usuarios, auth, config)."""
import os
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "java", "co", "ritech", "coffeeexport")
F = {}

F["CoffeeExportApplication.java"] = r'''package co.ritech.coffeeexport;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** CoffeeExport Manager (RITECH SAS): API REST para exportaciones de café y cacao a la Unión Europea. */
@SpringBootApplication
public class CoffeeExportApplication {
    public static void main(String[] args) {
        SpringApplication.run(CoffeeExportApplication.class, args);
    }
}
'''

# ----------------------------------------------------------------- shared
F["shared/ReglaNegocioException.java"] = r'''package co.ritech.coffeeexport.shared;

/** Se incumple una regla de negocio (dato inválido, estado no permitido...). Equivale a IllegalArgumentException. */
public class ReglaNegocioException extends IllegalArgumentException {
    public ReglaNegocioException(String mensaje) {
        super(mensaje);
    }
}
'''
F["shared/StockInsuficienteException.java"] = r'''package co.ritech.coffeeexport.shared;

/** Se pide más inventario del disponible (RF-14). */
public class StockInsuficienteException extends ReglaNegocioException {
    public StockInsuficienteException(String mensaje) {
        super(mensaje);
    }
}
'''
F["shared/RecursoNoEncontradoException.java"] = r'''package co.ritech.coffeeexport.shared;

public class RecursoNoEncontradoException extends RuntimeException {
    public RecursoNoEncontradoException(String mensaje) {
        super(mensaje);
    }
}
'''
F["shared/Paises.java"] = r'''package co.ritech.coffeeexport.shared;

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
'''
F["shared/ApiError.java"] = r'''package co.ritech.coffeeexport.shared;

import java.util.Map;

/** Cuerpo estándar de error de la API. {@code campos} se llena en errores de validación por campo. */
public record ApiError(String error, Map<String, String> campos) {
    public static ApiError de(String mensaje) {
        return new ApiError(mensaje, Map.of());
    }
}
'''
F["shared/GlobalExceptionHandler.java"] = r'''package co.ritech.coffeeexport.shared;

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
'''

# ----------------------------------------------------------------- usuarios
F["usuarios/Permiso.java"] = r'''package co.ritech.coffeeexport.usuarios;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "permisos")
@Getter @Setter @NoArgsConstructor
public class Permiso {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, unique = true, length = 80)
    private String codigo;
    @Column(length = 255)
    private String descripcion;

    public Permiso(String codigo, String descripcion) {
        this.codigo = codigo;
        this.descripcion = descripcion;
    }
}
'''
F["usuarios/Rol.java"] = r'''package co.ritech.coffeeexport.usuarios;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

@Entity
@Table(name = "roles")
@Getter @Setter @NoArgsConstructor
public class Rol {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, unique = true, length = 50)
    private String nombre;
    @Column(length = 255)
    private String descripcion;
    @CreationTimestamp @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(name = "roles_permisos", joinColumns = @JoinColumn(name = "rol_id"), inverseJoinColumns = @JoinColumn(name = "permiso_id"))
    private Set<Permiso> permisos = new HashSet<>();

    public Rol(String nombre, String descripcion) {
        this.nombre = nombre;
        this.descripcion = descripcion;
    }
}
'''
F["usuarios/Usuario.java"] = r'''package co.ritech.coffeeexport.usuarios;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

@Entity
@Table(name = "usuarios")
@Getter @Setter @NoArgsConstructor
public class Usuario {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, length = 100)
    private String nombre;
    @Column(nullable = false, unique = true, length = 150)
    private String email;
    /** Hash BCrypt de la contraseña (RNF-01). Nunca se guarda ni se devuelve en texto plano. */
    @Column(nullable = false, length = 100)
    private String passwordHash;
    @ManyToOne(optional = false, fetch = FetchType.EAGER)
    @JoinColumn(name = "rol_id", nullable = false)
    private Rol rol;
    @Column(nullable = false)
    private boolean activo = true;
    private LocalDateTime ultimoAcceso;
    @CreationTimestamp @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
    @UpdateTimestamp @Column(nullable = false)
    private LocalDateTime updatedAt;
}
'''
F["usuarios/RolRepository.java"] = r'''package co.ritech.coffeeexport.usuarios;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RolRepository extends JpaRepository<Rol, Long> {
    Optional<Rol> findByNombre(String nombre);
}
'''
F["usuarios/PermisoRepository.java"] = r'''package co.ritech.coffeeexport.usuarios;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PermisoRepository extends JpaRepository<Permiso, Long> {
    Optional<Permiso> findByCodigo(String codigo);
}
'''
F["usuarios/UsuarioRepository.java"] = r'''package co.ritech.coffeeexport.usuarios;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UsuarioRepository extends JpaRepository<Usuario, Long> {
    Optional<Usuario> findByEmailIgnoreCase(String email);

    boolean existsByEmailIgnoreCase(String email);
}
'''
F["usuarios/UsuarioRequest.java"] = r'''package co.ritech.coffeeexport.usuarios;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record UsuarioRequest(
        @NotBlank(message = "El nombre es obligatorio") String nombre,
        @NotBlank(message = "El correo es obligatorio") @Email(message = "Ingrese un correo válido") String email,
        String password,
        @NotBlank(message = "El rol es obligatorio") String rol,
        Boolean activo) {
}
'''
F["usuarios/UsuarioDto.java"] = r'''package co.ritech.coffeeexport.usuarios;

import java.util.List;

/** Vista pública del usuario: sin hash de contraseña. */
public record UsuarioDto(Long id, String nombre, String email, String rol, boolean activo, List<String> permisos) {
    public static UsuarioDto de(Usuario u) {
        return new UsuarioDto(u.getId(), u.getNombre(), u.getEmail(), u.getRol().getNombre(), u.isActivo(),
                u.getRol().getPermisos().stream().map(Permiso::getCodigo).sorted().toList());
    }
}
'''
F["usuarios/UsuarioService.java"] = r'''package co.ritech.coffeeexport.usuarios;

import co.ritech.coffeeexport.shared.RecursoNoEncontradoException;
import co.ritech.coffeeexport.shared.ReglaNegocioException;
import java.util.List;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Gestión de usuarios y roles (HU-05, RF-03, RF-04). */
@Service
public class UsuarioService {
    static final int LARGO_MINIMO_CLAVE = 8;

    private final UsuarioRepository usuarios;
    private final RolRepository roles;
    private final PasswordEncoder encoder;

    public UsuarioService(UsuarioRepository usuarios, RolRepository roles, PasswordEncoder encoder) {
        this.usuarios = usuarios;
        this.roles = roles;
        this.encoder = encoder;
    }

    /** RNF-01: la contraseña se guarda únicamente como hash BCrypt. */
    @Transactional
    public Usuario crearUsuario(UsuarioRequest r) {
        if (r.password() == null || r.password().length() < LARGO_MINIMO_CLAVE) {
            throw new ReglaNegocioException("La contraseña debe tener al menos " + LARGO_MINIMO_CLAVE + " caracteres");
        }
        if (usuarios.existsByEmailIgnoreCase(r.email())) {
            throw new ReglaNegocioException("Ya existe un usuario con ese correo");
        }
        Usuario u = new Usuario();
        u.setNombre(r.nombre().trim());
        u.setEmail(r.email().trim().toLowerCase());
        u.setPasswordHash(encoder.encode(r.password()));
        u.setRol(rolDe(r.rol()));
        u.setActivo(r.activo() == null || r.activo());
        return usuarios.save(u);
    }

    @Transactional
    public Usuario actualizarUsuario(Long id, UsuarioRequest r, Long idActor) {
        Usuario u = obtener(id);
        usuarios.findByEmailIgnoreCase(r.email()).filter(o -> !o.getId().equals(id)).ifPresent(o -> {
            throw new ReglaNegocioException("Ya existe un usuario con ese correo");
        });
        boolean activo = r.activo() == null || r.activo();
        if (id.equals(idActor) && (!activo || !"ADMIN".equals(r.rol()))) {
            throw new ReglaNegocioException("No puede desactivarse ni quitarse el rol de administrador a sí mismo");
        }
        u.setNombre(r.nombre().trim());
        u.setEmail(r.email().trim().toLowerCase());
        u.setRol(rolDe(r.rol()));
        u.setActivo(activo);
        if (r.password() != null && !r.password().isBlank()) {
            if (r.password().length() < LARGO_MINIMO_CLAVE) {
                throw new ReglaNegocioException("La contraseña debe tener al menos " + LARGO_MINIMO_CLAVE + " caracteres");
            }
            u.setPasswordHash(encoder.encode(r.password()));
        }
        return usuarios.save(u);
    }

    @Transactional(readOnly = true)
    public List<Usuario> listar() {
        return usuarios.findAll();
    }

    @Transactional(readOnly = true)
    public Usuario obtener(Long id) {
        return usuarios.findById(id).orElseThrow(() -> new RecursoNoEncontradoException("Usuario no encontrado"));
    }

    private Rol rolDe(String nombre) {
        return roles.findByNombre(nombre).orElseThrow(() -> new ReglaNegocioException("Rol no válido: " + nombre));
    }
}
'''
F["usuarios/UsuarioController.java"] = r'''package co.ritech.coffeeexport.usuarios;

import co.ritech.coffeeexport.auth.AuthService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

/** Solo el administrador (matriz de permisos en SecurityConfig). */
@RestController
@RequestMapping("/api/usuarios")
public class UsuarioController {
    private final UsuarioService service;
    private final AuthService auth;

    public UsuarioController(UsuarioService service, AuthService auth) {
        this.service = service;
        this.auth = auth;
    }

    @GetMapping
    public List<UsuarioDto> listar() {
        return service.listar().stream().map(UsuarioDto::de).toList();
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UsuarioDto crear(@Valid @RequestBody UsuarioRequest r) {
        return UsuarioDto.de(service.crearUsuario(r));
    }

    @PutMapping("/{id}")
    public UsuarioDto actualizar(@PathVariable Long id, @Valid @RequestBody UsuarioRequest r, Authentication a) {
        return UsuarioDto.de(service.actualizarUsuario(id, r, auth.actual(a).getId()));
    }
}
'''

# ----------------------------------------------------------------- auth
F["auth/LoginRequest.java"] = r'''package co.ritech.coffeeexport.auth;

import jakarta.validation.constraints.NotBlank;

public record LoginRequest(
        @NotBlank(message = "Ingrese su correo") String email,
        @NotBlank(message = "Ingrese su contraseña") String password) {
}
'''
F["auth/AuthService.java"] = r'''package co.ritech.coffeeexport.auth;

import co.ritech.coffeeexport.usuarios.Usuario;
import co.ritech.coffeeexport.usuarios.UsuarioRepository;
import java.time.LocalDateTime;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Autenticación de usuarios (HU-01, RF-01). */
@Service
public class AuthService {
    private final UsuarioRepository usuarios;
    private final PasswordEncoder encoder;

    public AuthService(UsuarioRepository usuarios, PasswordEncoder encoder) {
        this.usuarios = usuarios;
        this.encoder = encoder;
    }

    /**
     * Valida correo y contraseña contra el hash BCrypt.
     * El mensaje de error es genérico a propósito: no revela si falló el correo o la contraseña (UC-01 3a).
     */
    @Transactional
    public Usuario autenticar(String email, String password) {
        Usuario u = usuarios.findByEmailIgnoreCase(email == null ? "" : email.trim())
                .orElseThrow(() -> new BadCredentialsException("Credenciales incorrectas"));
        if (password == null || !encoder.matches(password, u.getPasswordHash())) {
            throw new BadCredentialsException("Credenciales incorrectas");
        }
        if (!u.isActivo()) {
            throw new DisabledException("Usuario inactivo");
        }
        u.setUltimoAcceso(LocalDateTime.now());
        return u;
    }

    /** Usuario de la sesión actual. */
    @Transactional(readOnly = true)
    public Usuario actual(Authentication authentication) {
        return usuarios.findByEmailIgnoreCase(authentication.getName())
                .orElseThrow(() -> new BadCredentialsException("Sesión no válida"));
    }
}
'''
F["auth/AuthController.java"] = r'''package co.ritech.coffeeexport.auth;

import co.ritech.coffeeexport.usuarios.Usuario;
import co.ritech.coffeeexport.usuarios.UsuarioDto;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.web.bind.annotation.*;

/** Inicio y cierre de sesión por cookie de sesión HttpOnly (RF-01, RF-02, RNF-02). */
@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthService service;

    public AuthController(AuthService service) {
        this.service = service;
    }

    @PostMapping("/login")
    public UsuarioDto login(@Valid @RequestBody LoginRequest r, HttpServletRequest request, HttpServletResponse response) {
        Usuario u = service.autenticar(r.email(), r.password());
        request.getSession(true);
        request.changeSessionId();   // evita fijación de sesión
        Authentication auth = new UsernamePasswordAuthenticationToken(u.getEmail(), null,
                List.of(new SimpleGrantedAuthority("ROLE_" + u.getRol().getNombre())));
        SecurityContext contexto = SecurityContextHolder.createEmptyContext();
        contexto.setAuthentication(auth);
        SecurityContextHolder.setContext(contexto);
        new HttpSessionSecurityContextRepository().saveContext(contexto, request, response);
        return UsuarioDto.de(u);
    }

    @PostMapping("/logout")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void logout(HttpServletRequest request) {
        HttpSession sesion = request.getSession(false);
        if (sesion != null) {
            sesion.invalidate();
        }
        SecurityContextHolder.clearContext();
    }

    @GetMapping("/me")
    public UsuarioDto me(Authentication authentication) {
        return UsuarioDto.de(service.actual(authentication));
    }
}
'''

# ----------------------------------------------------------------- config
F["config/Acceso.java"] = r'''package co.ritech.coffeeexport.config;

import java.util.List;
import java.util.Map;

/**
 * Matriz de permisos por módulo (RF-04, RNF-03). Es la misma del prototipo web (PERMISOS en data.js):
 * "leer" incluye a quienes pueden escribir.
 */
public final class Acceso {
    public static final String ADMIN = "ADMIN", GERENTE = "GERENTE", OP_EXPORTACIONES = "OP_EXPORTACIONES", OP_BODEGA = "OP_BODEGA", CONTADOR = "CONTADOR";
    public static final List<String> ROLES = List.of(ADMIN, GERENTE, OP_EXPORTACIONES, OP_BODEGA, CONTADOR);

    public record Modulo(String[] leer, String[] escribir) {
    }

    public static final Map<String, Modulo> MODULOS = Map.ofEntries(
            Map.entry("dashboard", new Modulo(new String[]{ADMIN, GERENTE}, new String[]{})),
            Map.entry("clientes", new Modulo(new String[]{ADMIN, GERENTE, OP_EXPORTACIONES}, new String[]{ADMIN, OP_EXPORTACIONES})),
            Map.entry("productos", new Modulo(new String[]{ADMIN, GERENTE, OP_EXPORTACIONES, OP_BODEGA}, new String[]{ADMIN})),
            Map.entry("inventario", new Modulo(new String[]{ADMIN, GERENTE, OP_EXPORTACIONES, OP_BODEGA}, new String[]{ADMIN, OP_BODEGA})),
            Map.entry("exportaciones", new Modulo(new String[]{ADMIN, GERENTE, OP_EXPORTACIONES, CONTADOR}, new String[]{ADMIN, OP_EXPORTACIONES})),
            Map.entry("documentos", new Modulo(new String[]{ADMIN, GERENTE, OP_EXPORTACIONES}, new String[]{ADMIN, OP_EXPORTACIONES})),
            Map.entry("pagos", new Modulo(new String[]{ADMIN, GERENTE, CONTADOR}, new String[]{ADMIN, CONTADOR})),
            Map.entry("reportes", new Modulo(new String[]{ADMIN, GERENTE, CONTADOR}, new String[]{})),
            Map.entry("usuarios", new Modulo(new String[]{ADMIN}, new String[]{ADMIN})));

    private Acceso() {
    }
}
'''
F["config/SecurityConfig.java"] = r'''package co.ritech.coffeeexport.config;

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
'''

for ruta, contenido in F.items():
    destino = os.path.normpath(os.path.join(BASE, ruta))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    open(destino, "w", encoding="utf-8", newline="\n").write(contenido)
print(len(F), "archivos")
