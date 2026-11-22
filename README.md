# CoffeeExport Manager

[![Pruebas automáticas](https://github.com/brayanckr/Proyecto-Calidad-de-software/actions/workflows/tests.yml/badge.svg)](https://github.com/brayanckr/Proyecto-Calidad-de-software/actions/workflows/tests.yml)

Sistema web de **RITECH SAS** (empresa ficticia) para administrar las exportaciones de café y cacao de Colombia hacia la Unión Europea:
clientes, productos, inventario, exportaciones, documentos aduaneros, pagos, reportes y dashboard.
Proyecto de la materia *Calidad de Software*.

## Estructura

| Carpeta | Contenido |
|---|---|
| `backend/` | API REST en **Java 21 y Spring Boot 3.5** (Spring Security con BCrypt, JPA/Hibernate, MySQL o H2). Pruebas JUnit 5, Mockito y MockMvc con cobertura JaCoCo. |
| `frontend/` | Sitio web (HTML, CSS, JavaScript y Bootstrap): landing pública `index.html` y el sistema `app.html`. Pruebas con `node:test` y Playwright. |
| `.github/workflows/` | Pipeline de pruebas automáticas (GitHub Actions). |
| `docs/` | Entregables de los Sprints 2, 3 y 4 (documentos, presentaciones, diagramas, script SQL). |

## Ejecutar

**Backend** (requiere JDK 21 o superior y Maven; en el equipo del equipo hay un Maven portable en `tools/`):

```bash
cd backend
mvn spring-boot:run                       # H2 en memoria con datos de demostración, http://localhost:8080
# con MySQL: mvn spring-boot:run -Dspring-boot.run.profiles=mysql   (variables DB_URL, DB_USER, DB_PASSWORD)
```

**Frontend** (cualquier servidor estático):

```bash
cd frontend
python -m http.server 8000                # http://localhost:8000
```

- **Modo demostración** (por defecto): los datos viven en el navegador (localStorage), sin backend.
- **Modo conectado**: abra `http://localhost:8000/app.html?api=http://localhost:8080`. La dirección se recuerda; `?api=off` vuelve al modo demostración.

Cuentas de demostración (contraseña `Demo2026*`; el backend las guarda con BCrypt): `admin@ritech.co`, `gerente@ritech.co`,
`exportaciones@ritech.co`, `bodega@ritech.co` y `contador@ritech.co`. **No usar en producción.**

## Pruebas

```bash
cd backend  && mvn verify                 # unitarias (Mockito), repositorios, integración (MockMvc) y cobertura JaCoCo
cd frontend && npm install && npm test    # unitarias e integración de la interfaz (Chrome)
cd frontend && npm run test:e2e           # sistema completo: interfaz + backend real (necesita el JAR de `mvn verify`)
```

Si Playwright no encuentra su navegador: `PW_CHANNEL=chrome` (o `msedge`). El informe de cobertura queda en `backend/target/site/jacoco/index.html`.
El pipeline `.github/workflows/tests.yml` ejecuta todo en cada push, en cada pull request y cada lunes.

## Despliegue

La web estática (`frontend/`) está publicada en Vercel en modo demostración: https://coffeeexport-manager.vercel.app (usuarios de prueba en la pantalla de acceso). Spring Boot no se ejecuta en Vercel: el sistema conectado corre localmente y en el pipeline de pruebas.

## Uso de IA

El backend, las pruebas automáticas, el pipeline y el rediseño del frontend se desarrollaron con apoyo del agente **Claude Code** (Anthropic), con decisiones y revisión del equipo.
Las fotos del catálogo son temporales (Unsplash) hasta reemplazarlas por fotos propias.
