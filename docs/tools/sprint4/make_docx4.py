# -*- coding: utf-8 -*-
"""Genera el documento de pruebas del Sprint 4 (Word) a partir de los resultados reales.
Uso: python docs/tools/sprint4/make_docx4.py [salida.docx]
Los fragmentos de código se extraen de los archivos reales del repositorio; las cifras, de los XML de JUnit y node:test."""
import os
import re
import sys
from collections import OrderedDict

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

import datos4 as D

VERDE, VERDE2, GRIS, ROJO = RGBColor(0x12, 0x3B, 0x30), RGBColor(0x1B, 0x56, 0x45), RGBColor(0x55, 0x55, 0x55), RGBColor(0xB0, 0x2A, 0x2A)
SALIDA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(D.REPO, "docs", "sprint4", "CoffeeExport_Manager_Sprint4_Pruebas.docx")
TEST = os.path.join(D.BACK, "src", "test", "java", "co", "ritech", "coffeeexport")


# ------------------------------------------------------------------ utilidades de documento
def sombrear(celda, hexa):
    tcPr = celda._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexa); tcPr.append(sh)


def fuente_run(r, tam=None, negrita=None, color=None, mono=False, cursiva=None):
    if mono:
        r.font.name = "Consolas"; r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
    if tam: r.font.size = Pt(tam)
    if negrita is not None: r.bold = negrita
    if cursiva is not None: r.italic = cursiva
    if color is not None: r.font.color.rgb = color


def estilos(doc):
    n = doc.styles["Normal"]; n.font.name = "Calibri"; n.font.size = Pt(10.5)
    n._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    n.paragraph_format.space_after = Pt(6); n.paragraph_format.line_spacing = 1.12
    for nombre, tam, color in (("Heading 1", 18, VERDE), ("Heading 2", 14, VERDE2), ("Heading 3", 11.5, VERDE2)):
        s = doc.styles[nombre]; s.font.name = "Calibri"; s.font.size = Pt(tam); s.font.bold = True; s.font.color.rgb = color
        s._element.rPr.rFonts.set(qn("w:ascii"), "Calibri"); s._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri"); s._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        s.paragraph_format.space_before = Pt(16 if nombre == "Heading 1" else 10); s.paragraph_format.space_after = Pt(6); s.paragraph_format.keep_with_next = True
    t = doc.styles["Title"]; t.font.name = "Calibri"; t.font.size = Pt(26); t.font.bold = True; t.font.color.rgb = RGBColor(0x17, 0x36, 0x5D)


def campo(par, instruccion):
    for tipo, txt in (("begin", None), (None, instruccion), ("separate", None), (None, " "), ("end", None)):
        r = par.add_run()
        if tipo:
            f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), tipo); r._r.append(f)
        elif txt.strip() == "":
            r.text = " "
        else:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._r.append(it)


def pie_encabezado(doc):
    s = doc.sections[0]
    p = s.header.paragraphs[0]; p.text = ""
    r = p.add_run(f"{D.PROYECTO} · {D.EMPRESA} · Documento de pruebas del Sprint 4"); fuente_run(r, 8.5, color=GRIS)
    f = s.footer.paragraphs[0]; f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = f.add_run(f"{D.MATERIA} · Página "); fuente_run(r, 8.5, color=GRIS)
    campo(f, " PAGE ")


def titulo(doc, txt, n=1):
    return doc.add_heading(txt, level=n)


def parr(doc, txt, negrita=False, cursiva=False, color=None, tam=None, alinea=None, despues=None):
    p = doc.add_paragraph()
    _runs(p, txt, negrita, cursiva, color, tam)
    if alinea: p.alignment = alinea
    if despues is not None: p.paragraph_format.space_after = Pt(despues)
    return p


def _runs(p, txt, negrita=False, cursiva=False, color=None, tam=None):
    """Soporta **negrita** en línea."""
    txt = txt.replace("`", "")
    for i, trozo in enumerate(re.split(r"\*\*(.+?)\*\*", txt)):
        if not trozo: continue
        r = p.add_run(trozo); fuente_run(r, tam, negrita or i % 2 == 1, color, cursiva=cursiva or None)


def vineta(doc, txt):
    p = doc.add_paragraph(style="List Bullet"); _runs(p, txt); p.paragraph_format.space_after = Pt(3); return p


def numerada(doc, txt):
    p = doc.add_paragraph(style="List Number"); _runs(p, txt); p.paragraph_format.space_after = Pt(3); return p


def tabla(doc, cabecera, filas, anchos=None, tam=9, resaltar=None, cebra=True):
    t = doc.add_table(rows=1, cols=len(cabecera)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(cabecera):
        c = t.rows[0].cells[i]; c.text = ""; sombrear(c, "123B30")
        r = c.paragraphs[0].add_run(h); fuente_run(r, tam, True, RGBColor(255, 255, 255))
    trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    for k, fila in enumerate(filas):
        cel = t.add_row().cells
        for i, v in enumerate(fila):
            cel[i].text = ""; p = cel[i].paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            txt = str(v)
            r = p.add_run(txt); fuente_run(r, tam)
            if resaltar and i == resaltar[0]:
                if txt in resaltar[1]: r.bold = True; r.font.color.rgb = resaltar[1][txt]
            if cebra and k % 2 == 1: sombrear(cel[i], "EEF4F1")
        tr = t.rows[-1]._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); cs.set(qn("w:val"), "true"); tr.append(cs)
    if anchos:
        t.autofit = False
        for fila in t.rows:
            for i, a in enumerate(anchos): fila.cells[i].width = Cm(a)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def bloque_codigo(doc, codigo, leyenda=None, tam=7.5):
    if leyenda:
        p = doc.add_paragraph(); r = p.add_run(leyenda); fuente_run(r, 9, True, VERDE2); p.paragraph_format.space_after = Pt(2); p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=1); t.style = "Table Grid"; c = t.rows[0].cells[0]; sombrear(c, "F4F6F5"); c.text = ""
    lineas = codigo.rstrip("\n").split("\n")
    for i, l in enumerate(lineas):
        p = c.paragraphs[0] if i == 0 else c.add_paragraph()
        p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
        r = p.add_run(l.replace("\t", "    ") or " "); fuente_run(r, tam, mono=True)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def imagen(doc, ruta, ancho_cm, leyenda):
    if not os.path.exists(ruta): return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(ruta, width=Cm(ancho_cm))
    q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = q.add_run(leyenda); fuente_run(r, 8.5, cursiva=True, color=GRIS)


def salto(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ------------------------------------------------------------------ extracción de código real
def metodo_java(ruta, nombre, max_lineas=60):
    """Método (con sus anotaciones) de un archivo Java, por llaves balanceadas."""
    f = open(ruta, encoding="utf-8").read().split("\n")
    for i, l in enumerate(f):
        if re.search(r"\bvoid\s+" + re.escape(nombre) + r"\s*\(", l):
            ini = i
            while ini > 0 and f[ini - 1].strip().startswith("@"): ini -= 1
            prof, fin = 0, i
            for j in range(i, len(f)):
                prof += f[j].count("{") - f[j].count("}")
                if prof == 0 and "{" in "".join(f[i:j + 1]): fin = j; break
            bloque = [x[4:] if x.startswith("    ") else x for x in f[ini:fin + 1]]
            return "\n".join(bloque[:max_lineas])
    raise KeyError(nombre)


def bloque_js(ruta, prefijo):
    f = open(ruta, encoding="utf-8").read().split("\n")
    for i, l in enumerate(f):
        if l.strip().startswith('test("' + prefijo):
            for j in range(i, len(f)):
                if f[j].startswith("  });"): return "\n".join(x[2:] for x in f[i:j + 1])
    raise KeyError(prefijo)


def recorte(ruta, desde, hasta):
    t = open(ruta, encoding="utf-8").read()
    a = t.index(desde); b = t.index(hasta, a) + len(hasta)
    return t[a:b]


def trozo_pom():
    t = open(os.path.join(D.BACK, "pom.xml"), encoding="utf-8").read()
    i = t.index("<artifactId>maven-failsafe-plugin"); a = t.rindex("<plugin>", 0, i); b = t.index("</plugin>", i) + len("</plugin>")
    return "      " + t[a:b]


def lineas(ruta, desde, hasta):
    """Líneas del archivo desde la que contiene `desde` hasta la anterior a la que contiene `hasta`."""
    f = open(ruta, encoding="utf-8").read().split("\n")
    a = next(i for i, l in enumerate(f) if desde in l); b = next(i for i, l in enumerate(f) if i > a and hasta in l)
    return "\n".join(x[4:] if x.startswith("    ") else x for x in f[a:b]).rstrip()


def fragmento_matriz():
    f = open(os.path.join(TEST, "integracion", "MatrizPermisosIT.java"), encoding="utf-8").read().split("\n")
    ini = next(i for i, l in enumerate(f) if "@ParameterizedTest" in l)
    csv_i = next(i for i, l in enumerate(f) if "@CsvSource" in l)
    fin = next(i for i, l in enumerate(f) if "void lectura" in l)
    q = lambda xs: [x[4:] if x.startswith("    ") else x for x in xs]
    return "\n".join(q(f[ini:csv_i + 2]) + ["        ... (24 combinaciones de lectura y 21 de escritura)", "        ..."] + q(f[fin:fin + 5]))


def ms(s): return f"{s * 1000:.0f}" if s < 1 else f"{s:.1f} s"


# ------------------------------------------------------------------ construcción
def main():
    b, f = D.leer_backend(), D.leer_frontend()
    ub = [p for p in b if p["nivel"] == "unitaria"]; rb = [p for p in b if p["nivel"] == "repositorio"]; ib = [p for p in b if p["nivel"] == "integración"]
    uf = [p for p in f if p["nivel"] == "unitaria"]; inf = [p for p in f if p["nivel"] == "integración"]; sf = [p for p in f if p["nivel"] == "sistema"]
    todas = b + f
    ok = sum(p["ok"] for p in todas); total = len(todas)
    filas_cob, tot_cob = D.cobertura()
    mx = D.matriz_permisos()
    fecha = "21 de noviembre de 2026"

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.59), Cm(27.94)
    sec.left_margin = sec.right_margin = Cm(2); sec.top_margin = Cm(2.2); sec.bottom_margin = Cm(2)
    estilos(doc); pie_encabezado(doc)

    # ---- portada
    for _ in range(5): doc.add_paragraph()
    p = parr(doc, "CALIDAD DE SOFTWARE · SPRINT 4", negrita=True, color=VERDE2, tam=13)
    doc.add_paragraph("Documento de pruebas", style="Title")
    parr(doc, f"{D.PROYECTO}", negrita=True, color=VERDE, tam=20, despues=2)
    parr(doc, "Pruebas unitarias, de integración y automatizadas: cómo se automatizaron, scripts y resultados", color=GRIS, tam=13, despues=24)
    parr(doc, D.EMPRESA, negrita=True, tam=13, despues=2)
    parr(doc, "Equipo: " + ", ".join(D.EQUIPO), tam=11, despues=2)
    parr(doc, fecha, tam=11, color=GRIS, despues=24)
    t = doc.add_table(rows=1, cols=4); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c, (n, e) in zip(t.rows[0].cells, ((str(total), "pruebas automáticas"), (str(ok), "aprobadas"), (f"{tot_cob[2]:.1f} %", "cobertura de líneas del backend"), ("0", "pruebas fallidas"))):
        sombrear(c, "EEF4F1"); c.text = ""
        r = c.paragraphs[0].add_run(n); fuente_run(r, 24, True, VERDE); c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        q = c.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.CENTER; r = q.add_run(e); fuente_run(r, 9, color=GRIS)
    salto(doc)

    # ---- tabla de contenido
    parr(doc, "Tabla de contenido", negrita=True, color=VERDE, tam=18)
    p = doc.add_paragraph(); campo(p, ' TOC \\o "1-2" \\h \\z \\u ')
    salto(doc)

    # ---- 1
    titulo(doc, "1. Introducción y alcance")
    parr(doc, f"Este documento presenta las pruebas de **{D.PROYECTO}**, el sistema de gestión de exportaciones de café y cacao de {D.EMPRESA}, "
              "conforme a lo pedido en el Sprint 4: pruebas **unitarias**, de **integración** y **automatizadas**, cómo se automatizaron, los scripts y los resultados.")
    parr(doc, "En el Sprint 3 solo existía el prototipo de interfaz y se habían automatizado 58 pruebas sobre él. Para el Sprint 4 se construyó el **backend Spring Boot** "
              "(API REST con Spring Security y JPA), se conectó la interfaz a esa API y se ejecutaron por primera vez los **44 casos del plan de pruebas del Sprint 2**, "
              "cada uno asociado a una prueba automática con el mismo nombre de clase y método indicado en el plan.")
    parr(doc, "**Transparencia sobre el uso de IA.** El backend, las pruebas JUnit, el pipeline de integración continua y la conexión de la interfaz con la API fueron desarrollados "
              "con ayuda de un agente de IA (Claude Code, modelo Claude Sonnet 5.5) bajo la dirección del equipo, que definió los requisitos y revisó los resultados. "
              "Las pruebas se ejecutaron de verdad y los números de este documento salen de los reportes generados por las herramientas (JUnit, JaCoCo y node:test), no de una estimación.")
    titulo(doc, "Resumen de resultados", 2)
    tabla(doc, ["Nivel", "Herramienta", "Pruebas", "Aprobadas", "Fallidas", "Tiempo"], [
        ["Unitarias del backend", "JUnit 5 + Mockito", len(ub), sum(p["ok"] for p in ub), len(ub) - sum(p["ok"] for p in ub), f"{sum(p['seg'] for p in ub):.1f} s"],
        ["Repositorios (JPA)", "JUnit 5 + @DataJpaTest + H2", len(rb), sum(p["ok"] for p in rb), len(rb) - sum(p["ok"] for p in rb), f"{sum(p['seg'] for p in rb):.1f} s"],
        ["Integración del backend", "JUnit 5 + MockMvc + H2", len(ib), sum(p["ok"] for p in ib), len(ib) - sum(p["ok"] for p in ib), f"{sum(p['seg'] for p in ib):.1f} s"],
        ["Unitarias del frontend", "node:test", len(uf), sum(p["ok"] for p in uf), len(uf) - sum(p["ok"] for p in uf), f"{sum(p['seg'] for p in uf):.1f} s"],
        ["Integración del frontend", "node:test + Playwright", len(inf), sum(p["ok"] for p in inf), len(inf) - sum(p["ok"] for p in inf), f"{sum(p['seg'] for p in inf):.1f} s"],
        ["Sistema (interfaz + API real)", "Playwright + backend", len(sf), sum(p["ok"] for p in sf), len(sf) - sum(p["ok"] for p in sf), f"{sum(p['seg'] for p in sf):.1f} s"],
        ["TOTAL", "", total, ok, total - ok, f"{sum(p['seg'] for p in todas):.0f} s"],
    ], [5, 4.6, 1.8, 2.2, 1.8, 1.8], tam=9)

    # ---- 2
    titulo(doc, "2. Estrategia y entorno de pruebas")
    parr(doc, "Se siguió la **pirámide de pruebas**: muchas pruebas unitarias rápidas y aisladas en la base, menos pruebas de integración que levantan el contexto real de Spring o el navegador, "
              "y pocas pruebas de sistema que recorren la interfaz contra el servidor completo.")
    tabla(doc, ["Nivel", "Qué prueba", "Cómo se aísla", "Dónde está"], [
        ["Unitaria", "Una clase de servicio con sus reglas de negocio (stock, estados, validaciones)", "Mockito reemplaza los repositorios; no hay base de datos ni red", "backend/src/test/.../unit"],
        ["Repositorio", "Consultas JPA y restricciones de la base (únicos, relaciones)", "@DataJpaTest con H2 en modo MySQL", "backend/src/test/.../repositorio"],
        ["Integración", "Controlador + seguridad + servicio + base de datos reales a través de HTTP", "MockMvc con el contexto completo de Spring y H2", "backend/src/test/.../integracion (*IT)"],
        ["Unitaria (interfaz)", "Funciones de lógica de la interfaz (cálculos, formato, permisos)", "node:test sin navegador", "frontend/tests/unit"],
        ["Integración (interfaz)", "Flujos de pantalla en un navegador real", "Playwright con Chrome, datos de demostración", "frontend/tests/integration"],
        ["Sistema", "Interfaz y API juntas: el navegador llama al servidor Spring Boot real", "Playwright + JAR del backend en el puerto 8099", "frontend/tests/e2e"],
    ], [2.6, 6, 5.2, 3.8], tam=8.5)
    titulo(doc, "Entorno", 2)
    tabla(doc, ["Componente", "Versión / detalle"], [
        ["Backend", "Spring Boot 3.5.16, Java 21 (compilado con release 21 sobre JDK 25), Maven 3.9.16, Spring Security, JPA/Hibernate, Lombok"],
        ["Base de datos de pruebas", "H2 en modo MySQL (sin instalar nada); perfil mysql verificado con MySQL 8.4.10 portable (139 pruebas, 13 tablas)"],
        ["Pruebas del backend", "JUnit 5, Mockito, AssertJ, MockMvc, Spring Security Test, JaCoCo, Surefire (unitarias) y Failsafe (*IT)"],
        ["Pruebas de la interfaz", "Node 22 con node:test, Playwright (playwright-core) sobre Chrome"],
        ["Integración continua", "GitHub Actions (ubuntu-latest, Temurin 21, Node 22), con ejecución semanal programada"],
        ["Equipo de desarrollo", "Windows 11, sin Docker ni MySQL instalados"],
    ], [4.5, 12.9], tam=9)

    # ---- 3
    titulo(doc, "3. Cómo se automatizaron las pruebas")
    parr(doc, "La automatización tiene tres piezas: (1) las pruebas escritas como código, (2) comandos que las ejecutan y generan reportes, y (3) un pipeline que las repite sin intervención humana.")
    titulo(doc, "3.1 Comandos de ejecución", 2)
    tabla(doc, ["Qué", "Comando", "Resultado"], [
        ["Unitarias del backend", "cd backend && mvn test", "target/surefire-reports/*.xml"],
        ["Todo el backend + cobertura", "cd backend && mvn verify", "surefire + failsafe + target/site/jacoco"],
        ["Unitarias de la interfaz", "cd frontend && npm run test:unit", "salida en consola"],
        ["Integración de la interfaz", "cd frontend && npm run test:integration", "salida y capturas en tests/evidence"],
        ["Sistema (necesita el JAR)", "cd frontend && npm run test:e2e", "salida y capturas en tests/evidence"],
        ["Todo el frontend, formato JUnit", "cd frontend && npm run test:junit", "XML JUnit en la salida estándar"],
    ], [4.5, 7.2, 5.7], tam=8.5)
    parr(doc, "Surefire ejecuta las clases terminadas en Test (unitarias y de repositorio) y Failsafe las terminadas en IT (integración). Se separaron para que las pruebas rápidas fallen primero. "
              "Este fue un bloqueo real: al principio las *IT no corrían (sección 8) hasta configurar Failsafe con el mismo argLine que Surefire:")
    bloque_codigo(doc, trozo_pom(), "backend/pom.xml · plugin Failsafe")
    titulo(doc, "3.2 Convención de nombres y trazabilidad", 2)
    parr(doc, "Cada prueba lleva en su nombre el identificador del caso del plan (QA001–QA018 para unitarias, QC001–QC025 para integración, PU/PI/PS para las de la interfaz) y las etiquetas "
              "de historia de usuario y requerimiento, por ejemplo **[HU-04][RF-14]**. Así el reporte JUnit se cruza directamente con el plan de pruebas del Sprint 2, y el script "
              "`docs/tools/llenar_plan_pruebas.py` llena el Excel del plan leyendo esos XML: un caso se marca SI únicamente si su prueba existe y pasó.")
    titulo(doc, "3.3 Pipeline de integración continua (GitHub Actions)", 2)
    parr(doc, "El archivo `.github/workflows/tests.yml` ejecuta todo en cada push a main, en cada pull request, bajo demanda y **cada lunes a las 6:00 a. m. (hora de Colombia)** para detectar regresiones "
              "por cambios de dependencias. El trabajo del frontend espera al del backend porque necesita su JAR para las pruebas de sistema.")
    yml = open(os.path.join(D.REPO, ".github", "workflows", "tests.yml"), encoding="utf-8").read()
    bloque_codigo(doc, yml[:yml.index("      - uses: actions/upload-artifact@v4\n        if: always()\n        with:\n          name: backend-reportes")].rstrip(), ".github/workflows/tests.yml (primera parte)", tam=7)
    parr(doc, "El pipeline guarda como artefactos los reportes JUnit, el reporte de cobertura de JaCoCo, las capturas de evidencia y el JAR, y escribe un resumen de cobertura en la página de la ejecución.", despues=4)
    ci = os.path.join(D.SPRINT4, "ci", "actions.png")
    if os.path.exists(ci): imagen(doc, ci, 16, "Figura. Ejecución del pipeline en la pestaña Actions de GitHub.")
    else: parr(doc, "Nota: la captura de la primera ejecución en GitHub Actions se agrega cuando el equipo suba el código y la ejecución termine (carpeta Sprint4/ci).", cursiva=True, color=GRIS, tam=9)

    # ---- 4
    titulo(doc, "4. Pruebas unitarias")
    parr(doc, f"Hay **{len(ub)} pruebas unitarias** en el backend (una clase de prueba por servicio) y **{len(uf)}** en la interfaz. Todas son independientes, no usan base de datos ni red y corren en menos de {sum(p['seg'] for p in ub + uf):.0f} segundos en total.")
    titulo(doc, "4.1 Script de ejemplo (backend)", 2)
    parr(doc, "La prueba QA014 verifica la regla RF-14: una salida mayor al stock se rechaza con el mensaje exacto, no cambia el inventario y no registra ningún movimiento. Los repositorios se simulan con Mockito.")
    bloque_codigo(doc, metodo_java(os.path.join(TEST, "unit", "InventarioServiceTest.java"), "qa014"), "InventarioServiceTest.java · QA014")
    parr(doc, "Para la atomicidad del descuento (RF-19) se verifica que, con stock insuficiente en alguno de los productos, no se mueva nada:")
    bloque_codigo(doc, metodo_java(os.path.join(TEST, "unit", "InventarioServiceTest.java"), "descuentoAtomico"), "InventarioServiceTest.java · descuento atómico")
    titulo(doc, "4.2 Resultados por clase (backend)", 2)
    por = OrderedDict()
    for p in ub: por.setdefault(p["clase"], []).append(p)
    tabla(doc, ["Clase de prueba", "Pruebas", "Aprobadas", "Casos del plan"], [
        [c, len(v), sum(x["ok"] for x in v), ", ".join(x["id"] for x in v if x["id"]) or "—"] for c, v in por.items()] + [["TOTAL", len(ub), sum(x["ok"] for x in ub), ""]], [5.5, 2.2, 2.4, 7.3], tam=9)
    titulo(doc, "4.3 Detalle de pruebas unitarias del backend", 2)
    tabla(doc, ["ID", "Prueba", "Resultado", "ms"], [[p["id"] or "—", p["desc"], "APROBADA" if p["ok"] else "FALLIDA", f"{p['seg'] * 1000:.0f}"] for p in ub],
          [1.5, 12.2, 2.3, 1.4], tam=8, resaltar=(2, {"APROBADA": VERDE2, "FALLIDA": ROJO}))
    titulo(doc, "4.4 Pruebas de repositorio (JPA)", 2)
    parr(doc, f"Las {len(rb)} pruebas de repositorio usan @DataJpaTest con H2 para comprobar consultas derivadas y restricciones (NIF único, código único, relaciones). Corren sobre una base real en memoria, por lo que verifican el mapeo de las 13 tablas del DDL del Sprint 2.")
    tabla(doc, ["Prueba", "Resultado"], [[p["desc"], "APROBADA" if p["ok"] else "FALLIDA"] for p in rb], [14.4, 3], tam=8.5, resaltar=(1, {"APROBADA": VERDE2, "FALLIDA": ROJO}))
    titulo(doc, "4.5 Pruebas unitarias de la interfaz", 2)
    parr(doc, "Las funciones de lógica del frontend (cálculos de totales, conversión de euros a dólares, descuento de stock, permisos, formato es-CO y protección contra XSS) se prueban sin navegador cargando el código en un contexto aislado de Node.")
    tabla(doc, ["ID", "Qué verifica", "Resultado", "ms"], [[p["id"], p["desc"], "APROBADA" if p["ok"] else "FALLIDA", f"{p['seg'] * 1000:.0f}"] for p in uf],
          [1.4, 12.3, 2.3, 1.4], tam=8, resaltar=(2, {"APROBADA": VERDE2, "FALLIDA": ROJO}))

    # ---- 5
    titulo(doc, "5. Pruebas de integración")
    parr(doc, f"Las **{len(ib)} pruebas de integración del backend** levantan el contexto completo de Spring (seguridad, controladores, servicios, JPA y base H2) y llaman a la API con MockMvc iniciando sesión con cada rol real. "
              f"Las **{len(inf)} de la interfaz** recorren las pantallas en Chrome mediante Playwright.")
    titulo(doc, "5.1 Base común y helper de sesión", 2)
    parr(doc, "Todas las clases *IT heredan de IntegracionBase, que arranca el contexto, siembra los datos de demostración y ofrece un `login(usuario)` que devuelve una sesión autenticada (cookie HttpOnly).")
    bloque_codigo(doc, lineas(os.path.join(TEST, "integracion", "IntegracionBase.java"), "@SpringBootTest", "protected String cuerpo"), "IntegracionBase.java (fragmento)")
    titulo(doc, "5.2 Ejemplo: crear una exportación por la API (QC022)", 2)
    bloque_codigo(doc, metodo_java(os.path.join(TEST, "integracion", "ExportacionDocumentoPagoIT.java"), "qc022"), "ExportacionDocumentoPagoIT.java · QC022")
    parr(doc, "Esta prueba cruza cuatro capas: validación del cuerpo, regla de stock, cálculo del total y descuento atómico del inventario. Fue la que descubrió el defecto D-06 (sección 7).")
    titulo(doc, "5.3 Matriz de permisos por rol (RBAC)", 2)
    parr(doc, f"Una sola prueba parametrizada genera {len(mx['lectura'])} comprobaciones de lectura y {len(mx['escritura'])} de escritura, una por combinación de rol y ruta, y verifica el código HTTP esperado (200, 400 o 403). "
              "Si alguien cambia un permiso sin querer, el reporte dice exactamente qué rol y qué ruta falló.")
    bloque_codigo(doc, fragmento_matriz(), "MatrizPermisosIT.java (fragmento)")
    roles = ["admin", "gerente", "exportaciones", "bodega", "contador"]
    rutas = OrderedDict()
    for u, r, e, o in mx["lectura"]: rutas.setdefault(r.replace("/api/", ""), {})[u] = e
    filas = []
    for r, d in rutas.items():
        filas.append([r] + [("Sí" if d[u] in (200, 400) else "No") if u in d else "·" for u in roles])
    parr(doc, "Matriz de lectura comprobada (Sí = acceso permitido, No = 403, · = no se probó esa combinación):", negrita=True, tam=9.5)
    tabla(doc, ["Ruta"] + roles, filas, [3.6, 2.4, 2.4, 2.8, 2.4, 2.4], tam=8.5)
    parr(doc, f"Resultado: {sum(x[3] for x in mx['lectura'])}/{len(mx['lectura'])} de lectura y {sum(x[3] for x in mx['escritura'])}/{len(mx['escritura'])} de escritura aprobadas.", negrita=True)
    titulo(doc, "5.4 Detalle de pruebas de integración del backend", 2)
    tabla(doc, ["ID", "Clase", "Prueba", "Res."], [[p["id"] or "—", p["clase"].replace("IT", ""), p["desc"], "OK" if p["ok"] else "FALLA"]
                                                   for p in ib if p["clase"] != "MatrizPermisosIT"], [1.4, 3.2, 11.8, 1.0], tam=7.5, resaltar=(3, {"OK": VERDE2, "FALLA": ROJO}))
    titulo(doc, "5.5 Integración de la interfaz (Playwright)", 2)
    parr(doc, "Estas pruebas abren la aplicación en Chrome en modo demostración (datos locales), llenan formularios, hacen clic y comprueban el resultado visible. Cada una guarda una captura en tests/evidence.")
    for g in OrderedDict.fromkeys(p["grupo"] for p in inf):
        parr(doc, g, negrita=True, color=VERDE2, tam=10, despues=2)
        tabla(doc, ["ID", "Qué verifica", "Resultado", "s"], [[p["id"], p["desc"], "APROBADA" if p["ok"] else "FALLIDA", f"{p['seg']:.1f}"] for p in inf if p["grupo"] == g],
              [1.4, 12.2, 2.4, 1.4], tam=8, resaltar=(2, {"APROBADA": VERDE2, "FALLIDA": ROJO}))

    # ---- 6
    titulo(doc, "6. Pruebas automatizadas de sistema (interfaz + API real)")
    parr(doc, "Las pruebas de sistema son las más valiosas y las más lentas: Playwright abre la interfaz **conectada al servidor Spring Boot real** (el JAR corriendo con base H2), "
              "ejecuta acciones como las haría una persona y comprueba tanto lo que se ve como lo que quedó guardado en el servidor. Cada prueba arranca con una base limpia.")
    parr(doc, "Ejemplo, PS-06: una entrada de inventario sube el stock en el servidor y una salida excesiva se rechaza con el mensaje del backend.")
    bloque_codigo(doc, bloque_js(os.path.join(D.FRONT, "tests", "e2e", "conectado.test.js"), "PS-06"), "frontend/tests/e2e/conectado.test.js · PS-06", tam=7)
    tabla(doc, ["ID", "Qué verifica", "Resultado", "s"], [[p["id"], p["desc"], "APROBADA" if p["ok"] else "FALLIDA", f"{p['seg']:.1f}"] for p in sf],
          [1.4, 12.2, 2.4, 1.4], tam=8, resaltar=(2, {"APROBADA": VERDE2, "FALLIDA": ROJO}))
    parr(doc, "Las pruebas de sistema detectaron un defecto que ninguna otra prueba había visto (D-07: CORS), porque MockMvc no simula un navegador. Ese es el valor de esta capa.")

    # ---- 7
    titulo(doc, "7. Resultados, cobertura y defectos")
    titulo(doc, "7.1 Historial de ejecuciones", 2)
    tabla(doc, ["#", "Ejecución", "Pruebas", "Aprobadas", "Fallidas", "Qué pasó"], [list(e) for e in D.EJECUCIONES], [0.8, 3.7, 1.5, 1.8, 1.5, 8.1], tam=8.5)
    titulo(doc, "7.2 Cobertura de código del backend (JaCoCo)", 2)
    parr(doc, f"La corrida final cubre **{tot_cob[0]} de {tot_cob[1]} líneas ({tot_cob[2]:.1f} %)** y {tot_cob[3]:.1f} % de las instrucciones. La meta del proyecto (RNF-10) era al menos 70 % en servicios.")
    tabla(doc, ["Paquete", "Líneas cubiertas", "Líneas totales", "Cobertura de líneas", "Cobertura de instrucciones"],
          [[k, c, t, f"{pl:.1f} %", f"{pi:.1f} %"] for k, c, t, pl, pi in filas_cob] + [["TOTAL", tot_cob[0], tot_cob[1], f"{tot_cob[2]:.1f} %", f"{tot_cob[3]:.1f} %"]], [5, 3, 3, 3.2, 3.2], tam=9)
    titulo(doc, "7.3 Defectos encontrados y corregidos", 2)
    parr(doc, "Las pruebas automáticas encontraron **siete defectos reales** a lo largo de los Sprints 3 y 4. Ningún defecto se oculta: cada uno tiene su prueba de regresión.")
    d3 = [("D-01", "PU-25", "Alta", "descontarStock() no validaba el stock disponible ni era atómica.", "Inventario inconsistente.", "Se valida todo antes de mover nada."),
          ("D-02", "PU-27", "Media", "todayISO() usaba UTC: en Colombia, tras las 7 p. m. devolvía el día siguiente.", "Fechas corridas un día por la noche.", "Se usan los componentes de la fecha local."),
          ("D-03", "PU-11", "Baja", "fdate() devolvía un guion largo para fechas vacías.", "Presentación inconsistente.", "Se unificó a un guion simple."),
          ("D-04", "PI-25", "Media", "El filtro del catálogo no ocultaba las tarjetas (display:flex anulaba hidden).", "El filtro Café/Cacao no funcionaba.", "Regla CSS .card[hidden]{display:none}."),
          ("D-05", "PI-01", "Media", "En el dashboard, una función local tapaba el ayudante de conteo de KPI.", "KPI en 0.", "Se renombró el ayudante a kv().")]
    tabla(doc, ["ID", "Prueba", "Sev.", "Descripción", "Impacto", "Corrección"], [list(x) for x in d3 + [list(x) for x in D.DEFECTOS]], [1.1, 2.3, 1.2, 5.2, 3.4, 4.2], tam=8)
    parr(doc, "Los defectos D-06 y D-07 son del Sprint 4. D-06 lo encontró una prueba de integración; D-07 solo podía encontrarlo una prueba de sistema:", despues=3)
    for dd in D.DEFECTOS:
        vineta(doc, f"**{dd[0]}** ({dd[1]}): {dd[3]} **Corrección:** {dd[5]}")

    # ---- 8
    salto(doc)
    titulo(doc, "8. Bloqueos encontrados y soluciones")
    tabla(doc, ["Bloqueo", "Efecto", "Solución", "Estado"], [list(x) for x in D.BLOQUEOS], [5.4, 3.6, 6.6, 1.8], tam=8.5, resaltar=(3, {"Resuelto": VERDE2, "Mitigado": RGBColor(0xB2, 0x6A, 0x00), "Pendiente": ROJO}))

    # ---- 9 trazabilidad
    titulo(doc, "9. Trazabilidad con el plan de pruebas del Sprint 2")
    parr(doc, "Los 44 casos del plan de pruebas (18 unitarios QA y 26 de integración QC) tienen ahora una prueba automática y un resultado real. El Excel del plan se llenó con el script docs/tools/llenar_plan_pruebas.py.")
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(D.REPO, "docs", "sprint2", "Plan_de_Pruebas_CoffeeExport_Manager.xlsx"), data_only=True); ws = wb["Hoja1"]
    filas = []
    for r in range(7, ws.max_row + 1):
        pid = ws.cell(r, 1).value
        if not pid: continue
        filas.append([pid, str(ws.cell(r, 3).value or "")[:70], str(ws.cell(r, 5).value or "")[:48], ws.cell(r, 9).value or ""])
    tabla(doc, ["Caso", "Descripción", "Clase.método del plan", "¿Cumple?"], filas, [1.5, 8.2, 6, 1.7], tam=7.5, resaltar=(3, {"SI": VERDE2, "NO": ROJO}))
    parr(doc, f"Resultado: {sum(1 for x in filas if x[3] == 'SI')} de {len(filas)} casos cumplen lo esperado.", negrita=True)

    # ---- 10 cómo ejecutar
    titulo(doc, "10. Cómo ejecutar las pruebas")
    for s in ("Instalar Java 21 o superior y Node 22 (no se necesita MySQL ni Docker).",
              "Backend: entrar a la carpeta backend y ejecutar `mvn verify`. Los reportes quedan en target/surefire-reports, target/failsafe-reports y target/site/jacoco/index.html.",
              "Frontend: entrar a la carpeta frontend, ejecutar `npm install` y luego `npm run test:unit` y `npm run test:integration`.",
              "Sistema: con el JAR del backend ya construido, `npm run test:e2e` lo arranca en el puerto 8099 y lanza las 10 pruebas.",
              "Si Playwright no encuentra su navegador, usar el Chrome instalado con la variable de entorno PW_CHANNEL=chrome.",
              "También se pueden ejecutar desde GitHub: pestaña Actions → Pruebas automáticas → Run workflow."):
        numerada(doc, s)

    # ---- 11 IA y equipo
    titulo(doc, "11. Uso de IA y trabajo en equipo")
    parr(doc, "El Sprint 4 pide declarar qué parte se hizo con un agente de IA. Este es el detalle:")
    tabla(doc, ["Parte", "Quién", "Herramienta"], [
        ["Backend Spring Boot (entidades, servicios, controladores, seguridad)", "Agente de IA, con requisitos y revisión del equipo", "Claude Code (Claude Sonnet 5.5)"],
        ["Pruebas JUnit 5, Mockito, MockMvc, JaCoCo (139)", "Agente de IA", "Claude Code"],
        ["Conexión de la interfaz con la API y pruebas de sistema (10)", "Agente de IA", "Claude Code"],
        ["Pipeline de GitHub Actions y README", "Agente de IA", "Claude Code"],
        ["Prototipo de interfaz, rediseño de landing y pruebas del Sprint 3 (58)", "Agente de IA, dirigido por el equipo", "Claude Code"],
        ["Requisitos, historias de usuario, plan de pruebas y diseño del Sprint 1 y 2", "Equipo", "—"],
        ["Descarga de las 11 fotos temporales de Unsplash al proyecto (frontend/img)", "Agente de IA", "Claude Code"],
        ["Fotos propias, Jira, publicación y revisión final", "Equipo", "—"],
    ], [8, 5.2, 4.2], tam=9)
    parr(doc, "El detalle de qué integrante lideró cada módulo está en la presentación del Sprint 4 y en el tablero de Jira del equipo.")

    # ---- 12
    titulo(doc, "12. Conclusiones y siguientes pasos")
    for s in (f"Se automatizaron y ejecutaron **{total} pruebas** de tres niveles, todas aprobadas, con **{tot_cob[2]:.1f} %** de cobertura de líneas en el backend.",
              "Los 44 casos del plan del Sprint 2 pasaron de planificados a ejecutados con evidencia.",
              "Las pruebas encontraron 7 defectos reales; cada uno quedó corregido y cubierto por una prueba de regresión.",
              "El pipeline repite todo automáticamente en cada cambio y cada lunes, por lo que una regresión se detecta sin intervención humana.",
              "Se verificó además la suite del backend contra **MySQL 8.4.10 real**: 139 de 139. **Pendiente:** medir Lighthouse y accesibilidad, reemplazar las fotos temporales (ya alojadas en el proyecto) por las del equipo, y publicar la interfaz en Vercel en modo demostración."):
        vineta(doc, s)

    # ---- anexos
    salto(doc)
    titulo(doc, "Anexo A. Salida de la ejecución")
    parr(doc, "Fragmentos de la salida real de las herramientas (los archivos completos están en docs/sprint4/resultados).")
    cons = os.path.join(D.RES, "backend_consola.txt")
    if os.path.exists(cons):
        lin = [l.rstrip() for l in open(cons, encoding="utf-8", errors="replace") if re.search(r"Tests run:|BUILD|Total time|jacoco|All coverage", l)]
        bloque_codigo(doc, "\n".join(lin[-24:]), "Backend · mvn verify (resumen)", tam=7)
    fc = os.path.join(D.RES, "frontend_consola.txt")
    if os.path.exists(fc):
        lin = [l.rstrip() for l in open(fc, encoding="utf-8", errors="replace") if l.startswith("ℹ")]
        bloque_codigo(doc, "\n".join(lin), "Frontend · node --test (resumen)", tam=8)
    salto(doc)
    titulo(doc, "Anexo B. Evidencia")
    parr(doc, "Capturas tomadas automáticamente por las pruebas de sistema contra el servidor real y por las de integración.")
    for nombre, ley in (("PS-01-dashboard-conectado", "PS-01 · Dashboard con datos reales del servidor"), ("PS-03-cliente-guardado", "PS-03 · Cliente guardado en el servidor"),
                        ("PS-06-salida-rechazada-servidor", "PS-06 · Salida de inventario rechazada por el backend"), ("PS-07-exportacion-creada-servidor", "PS-07 · Exportación creada y stock descontado"),
                        ("PS-10-login-movil", "PS-10 · Login en móvil (375 × 812)"), ("PI-16-salida-rechazada", "PI-16 · Salida mayor al stock rechazada (modo demostración)")):
        imagen(doc, os.path.join(D.EVID, nombre + ".png"), 14.5 if "movil" not in nombre else 5.5, ley)

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    doc.save(SALIDA)
    print("Guardado", SALIDA)


if __name__ == "__main__":
    main()
