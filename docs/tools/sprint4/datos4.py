# -*- coding: utf-8 -*-
"""Datos del Sprint 4 leídos de los resultados REALES de ejecución (JUnit del backend, node:test del frontend, JaCoCo).
Nada de lo que muestran el documento y la presentación se escribe a mano: se calcula desde estos archivos."""
import csv
import glob
import os
import re
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(AQUI, "..", "..", ".."))
BACK = os.path.join(REPO, "backend")
FRONT = os.path.join(REPO, "frontend")
RES = os.environ.get("SPRINT4_RESULTADOS", os.path.join(REPO, "docs", "sprint4", "resultados"))
SPRINT4 = os.environ.get("SPRINT4_CARPETA", os.path.join(REPO, ".."))      # carpeta con fotos, jira y ci del usuario
FRONT_XML = os.path.join(RES, "frontend.xml")
EVID = os.path.join(FRONT, "tests", "evidence")

PROYECTO, EMPRESA, MATERIA = "CoffeeExport Manager", "RITECH SAS", "Calidad de Software"
EQUIPO = ["Brayan Guerrero", "Juan Jurado", "Nicoll López", "Alexander Rodríguez", "Mario Zambrano"]


# ------------------------------------------------------------------ backend (JUnit)
def _nombres_visibles():
    """Mapa (clase, método) -> texto de @DisplayName, leído de las fuentes de prueba."""
    mapa = {}
    for ruta in glob.glob(os.path.join(BACK, "src", "test", "java", "**", "*.java"), recursive=True):
        fuente = open(ruta, encoding="utf-8").read()
        clase = os.path.basename(ruta)[:-5]
        for m in re.finditer(r'@DisplayName\("((?:[^"\\]|\\.)*)"\)\s*(?:@\w+(?:\([^)]*\))?\s*)*void\s+(\w+)\s*\(', fuente):
            mapa[(clase, m.group(2))] = m.group(1).replace('\\"', '"')
    return mapa


def _etiquetas(texto):
    return re.findall(r"\[([^\]]+)\]", texto)


def leer_backend():
    """Lista de pruebas del backend: dict(id, nivel, clase, metodo, desc, tags, seg, ok)."""
    nombres = _nombres_visibles()
    pruebas = []
    for nivel, carpeta in (("unitaria", "surefire-reports"), ("integración", "failsafe-reports")):
        for f in sorted(glob.glob(os.path.join(BACK, "target", carpeta, "TEST-*.xml"))):
            raiz = ET.parse(f).getroot()
            for tc in raiz.iter("testcase"):
                clase = tc.get("classname").split(".")[-1]
                metodo = re.sub(r"\(.*", "", tc.get("name"))
                visible = nombres.get((clase, metodo), tc.get("name"))
                m = re.match(r"^(Q[AC]\d{3})\s+(.*)$", visible)
                pid = m.group(1) if m else ""
                desc = m.group(2) if m else visible
                pruebas.append(dict(id=pid, nivel="repositorio" if clase == "RepositoriosTest" else nivel, clase=clase, metodo=tc.get("name"),
                                    desc=desc, tags=_etiquetas(desc), seg=float(tc.get("time")), ok=tc.find("failure") is None and tc.find("error") is None))
    return pruebas


def matriz_permisos():
    """Filas (rol, ruta, esperado) de la matriz de permisos, leídas del @CsvSource, con su resultado."""
    fuente = open(os.path.join(BACK, "src", "test", "java", "co", "ritech", "coffeeexport", "integracion", "MatrizPermisosIT.java"), encoding="utf-8").read()
    bloques = re.findall(r"@CsvSource\(\{(.*?)\}\)", fuente, re.S)
    resultado = {}
    for f in glob.glob(os.path.join(BACK, "target", "failsafe-reports", "TEST-*MatrizPermisosIT.xml")):
        for tc in ET.parse(f).getroot().iter("testcase"):
            m = re.match(r"(\w+)\(.*\)\[(\d+)\]", tc.get("name"))
            if m:
                resultado[(m.group(1), int(m.group(2)))] = tc.find("failure") is None and tc.find("error") is None
    salida = {"lectura": [], "escritura": []}
    for tipo, bloque in zip(("lectura", "escritura"), bloques):
        for i, fila in enumerate(re.findall(r'"([^"]+)"', bloque), 1):
            u, ruta, esp = [x.strip() for x in fila.split(",")]
            salida[tipo].append((u.split("@")[0], ruta, int(esp), resultado.get((tipo, i), False)))
    return salida


# ------------------------------------------------------------------ frontend (node:test)
def leer_frontend():
    pruebas = []
    if not os.path.exists(FRONT_XML):
        return pruebas
    for tc in ET.parse(FRONT_XML).getroot().iter("testcase"):
        m = re.match(r"^(P[UIS]-\d+) ((?:\[[^\]]+\])*) ?(.*)$", tc.get("name") or "")
        if not m:
            continue
        pid = m.group(1)
        pruebas.append(dict(id=pid, nivel={"PU": "unitaria", "PI": "integración", "PS": "sistema"}[pid[:2]], tags=_etiquetas(m.group(2)), desc=m.group(3),
                            grupo=tc.get("classname"), seg=float(tc.get("time")), ok=tc.find("failure") is None and tc.find("error") is None))
    return pruebas


# ------------------------------------------------------------------ cobertura (JaCoCo)
def cobertura():
    ruta = os.path.join(BACK, "target", "site", "jacoco", "jacoco.csv")
    paquetes, tot = {}, [0, 0, 0, 0]
    for r in csv.DictReader(open(ruta, encoding="utf-8")):
        k = r["PACKAGE"].replace("co.ritech.coffeeexport", "").strip(".") or "(raíz)"
        a = paquetes.setdefault(k, [0, 0, 0, 0])
        for i, c in enumerate(("INSTRUCTION_MISSED", "INSTRUCTION_COVERED", "LINE_MISSED", "LINE_COVERED")):
            a[i] += int(r[c]); tot[i] += int(r[c])
    filas = [(k, a[3], a[2] + a[3], a[3] / (a[2] + a[3]) * 100 if a[2] + a[3] else 0, a[1] / (a[0] + a[1]) * 100 if a[0] + a[1] else 0) for k, a in sorted(paquetes.items())]
    return filas, (tot[3], tot[2] + tot[3], tot[3] / (tot[2] + tot[3]) * 100, tot[1] / (tot[0] + tot[1]) * 100)


def resumen():
    b, f = leer_backend(), leer_frontend()
    todas = b + f
    return dict(backend=b, frontend=f, total=len(todas), ok=sum(p["ok"] for p in todas), seg=sum(p["seg"] for p in todas))


# ------------------------------------------------------------------ historial de ejecuciones (cifras de las corridas reales de este sprint)
EJECUCIONES = [
    ("1", "Backend: unitarias y repositorio", "47", "45", "2", "Dos errores de las propias pruebas de repositorio (BigDecimal en caché y excepción fuera de assertThrows). Las pruebas *IT aún no se ejecutaban: faltaba configurar Failsafe."),
    ("2", "Backend: integración (MockMvc)", "90", "82", "8", "Defecto real: el código provisional de la exportación medía 40 caracteres y la columna admite 20. Un error de la prueba de usuarios (usaba otra contraseña)."),
    ("3", "Backend: completo", "137", "137", "0", "Defecto corregido y prueba ajustada: 47 unitarias y 90 de integración."),
    ("4", "Sistema (Playwright contra el backend real)", "10", "0", "10", "Defecto real: el navegador no podía llamar a la API (faltaban las cabeceras CORS por el nombre del bean). Las pruebas MockMvc no lo detectan porque no envían Origin."),
    ("5", "Backend: completo con CorsIT", "139", "139", "0", "Bean renombrado a corsConfigurationSource y 2 pruebas nuevas de CORS."),
    ("6", "Frontend completo: unitarias, integración y sistema", "68", "68", "0", "30 unitarias, 28 de integración (modo demostración) y 10 de sistema contra el backend real; 133 s en total."),
]

DEFECTOS = [
    ("D-06", "ExportacionDocumentoPagoIT", "Alta", "Al crear una exportación, el código provisional (\"TMP-\" + UUID) medía 40 caracteres y la columna codigo admite 20: el servidor respondía 409 al crear cualquier exportación.",
     "Imposible crear exportaciones desde la API.", "Código provisional de 20 caracteres (\"TMP-\" + 16 hexadecimales) hasta asignar el definitivo EXP-AAAA-NNNN."),
    ("D-07", "PS-01 a PS-10 (sistema)", "Alta", "El backend no enviaba cabeceras CORS: el bean se llamaba cors y Spring Security busca corsConfigurationSource. El navegador bloqueaba todas las llamadas desde el sitio web.",
     "La web no podía conectarse al servidor, aunque la API respondía bien con curl y con MockMvc.", "Bean renombrado y 2 pruebas de integración nuevas (CorsIT): origen permitido con credenciales y origen desconocido rechazado."),
]

BLOQUEOS = [
    ("El backend Spring Boot del Sprint 1 no estaba en el repositorio ni en el equipo de trabajo.", "No se podían ejecutar las pruebas JUnit, Mockito y MockMvc del plan del Sprint 2.",
     "Se construyó un backend nuevo con el agente de IA, siguiendo el DDL del Sprint 2 y los nombres de clase y método del plan, y se declaró como hecho con IA.", "Resuelto"),
    ("El equipo solo tiene Java 25 y no tiene Maven, Gradle, Docker ni MySQL.", "No se podía compilar ni probar el backend.",
     "Se descargó Maven 3.9.16 a una carpeta del proyecto (tools/, fuera de Git), se compila con la opción release 21 (RR-01) y las pruebas usan H2 en modo MySQL.", "Resuelto"),
    ("Un comentario del pom.xml con dos guiones (--release) lo volvió ilegible para Maven.", "El build fallaba antes de compilar.", "Se reescribió el comentario sin guiones dobles.", "Resuelto"),
    ("Los JDK 23 o superiores ya no ejecutan procesadores de anotaciones del classpath (Lombok).", "Las entidades no compilaban.", "Se declaró Lombok en annotationProcessorPaths del plugin del compilador.", "Resuelto"),
    ("Las pruebas *IT no corrían con mvn verify.", "Las 92 pruebas de integración no se ejecutaban.", "Se configuró maven-failsafe-plugin con el mismo argLine que Surefire.", "Resuelto"),
    ("El backend no enviaba CORS y la web no podía llamarlo (D-07).", "La interfaz conectada fallaba entera.", "Se corrigió el nombre del bean y se agregaron pruebas de CORS.", "Resuelto"),
    ("Playwright no encontraba su Chromium (versión distinta de la instalada).", "Las pruebas de interfaz fallaban al arrancar.", "Se usa el Chrome instalado con PW_CHANNEL=chrome; en el pipeline se instala Chromium.", "Resuelto"),
    ("Spring Boot no se ejecuta en Vercel.", "La web publicada no puede usar el backend.", "La web se publica en modo demostración (localStorage) y el sistema conectado corre local y en el pipeline.", "Mitigado"),
    ("No hay MySQL instalado.", "No se pudo probar contra MySQL real.", "Perfil mysql configurado y documentado; las pruebas usan H2 en modo MySQL. Falta una corrida con MySQL.", "Mitigado"),
    ("No hay fotos propias del producto.", "La landing y el catálogo necesitan fotografías.", "Se usan 11 fotos temporales de Unsplash (licencia libre) descargadas al proyecto, sin depender de un servidor externo. Se reemplazan por fotos propias copiando archivos con el mismo nombre.", "Mitigado"),
]
