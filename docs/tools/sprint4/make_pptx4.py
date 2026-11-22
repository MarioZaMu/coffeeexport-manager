# -*- coding: utf-8 -*-
"""Genera la presentación del Sprint 4. Las cifras salen de los reportes reales (JUnit, JaCoCo, node:test).
La captura de Jira se toma de <Sprint4>/jira/tablero.png; si no existe se deja un recuadro marcado, nunca una imagen inventada.
Uso: python docs/tools/sprint4/make_pptx4.py [salida.pptx]"""
import os
import re
import sys
from collections import OrderedDict

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

import datos4 as D

BG, CARD, VERDE, AMBAR, CREMA, MARRON, GRIS, ROJO = (RGBColor.from_string(x) for x in ("15110F", "221A16", "66BB6A", "FFB74D", "F3E9E2", "A1887F", "BCAAA4", "EF5350"))
SALIDA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(D.REPO, "docs", "sprint4", "CoffeeExport_Manager_Sprint4.pptx")
TEST = os.path.join(D.BACK, "src", "test", "java", "co", "ritech", "coffeeexport")
PIE = f"{D.PROYECTO} · {D.EMPRESA} · Sprint 4"
FECHA = "21 de noviembre de 2026"
N = [0]


# ------------------------------------------------------------------ primitivas
def rect(sl, x, y, w, h, color, forma=MSO_SHAPE.RECTANGLE, linea=None):
    s = sl.shapes.add_shape(forma, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = color
    if linea: s.line.color.rgb = linea; s.line.width = Pt(1)
    else: s.line.fill.background()
    s.shadow.inherit = False
    return s


def texto(sl, x, y, w, h, txt, tam=14, color=CREMA, negrita=False, alinea=PP_ALIGN.LEFT, ancla=MSO_ANCHOR.TOP, fuente="Calibri", interlineado=None):
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = ancla
    tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.03)
    lineas = [x.replace("`", "") for x in (txt if isinstance(txt, list) else [txt])]
    for i, l in enumerate(lineas):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = alinea
        if interlineado: p.line_spacing = interlineado
        for j, trozo in enumerate(re.split(r"\*\*(.+?)\*\*", l)):
            if not trozo: continue
            r = p.add_run(); r.text = trozo; r.font.name = fuente; r.font.size = Pt(tam); r.font.bold = negrita or j % 2 == 1; r.font.color.rgb = color
    return tb


def viñetas(sl, x, y, w, h, items, tam=13, color=CREMA, sep=4):
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.space_after = Pt(sep)
        r = p.add_run(); r.text = "▪ "; r.font.size = Pt(tam); r.font.color.rgb = VERDE; r.font.name = "Calibri"
        for j, trozo in enumerate(re.split(r"\*\*(.+?)\*\*", it.replace("`", ""))):
            if not trozo: continue
            r = p.add_run(); r.text = trozo; r.font.size = Pt(tam); r.font.name = "Calibri"; r.font.bold = j % 2 == 1; r.font.color.rgb = color
    return tb


def nueva(prs, titulo, subtitulo=None, notas=""):
    sl = prs.slides.add_slide(prs.slide_layouts[6]); N[0] += 1
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = BG
    rect(sl, 0, 0, 0.18, 7.5, VERDE)
    texto(sl, 0.6, 0.3, 12, 0.7, titulo, 30, CREMA, True)
    if subtitulo: texto(sl, 0.6, 0.95, 12, 0.4, subtitulo, 14, MARRON)
    texto(sl, 0.6, 7.05, 8, 0.3, PIE, 10, GRIS)
    texto(sl, 11.9, 7.05, 1.0, 0.3, str(N[0]), 10, GRIS, alinea=PP_ALIGN.RIGHT)
    sl.notes_slide.notes_text_frame.text = notas
    return sl


def tarjeta_kpi(sl, x, y, w, valor, etiqueta, color=VERDE):
    rect(sl, x, y, w, 1.45, CARD)
    texto(sl, x, y + 0.05, w, 0.9, valor, 40, color, True, PP_ALIGN.CENTER)
    texto(sl, x, y + 0.95, w, 0.45, etiqueta, 12, GRIS, alinea=PP_ALIGN.CENTER)


def tabla(sl, x, y, w, cabecera, filas, anchos, tam=11, alto_fila=0.34, color_col=None):
    gs = sl.shapes.add_table(len(filas) + 1, len(cabecera), Inches(x), Inches(y), Inches(w), Inches(alto_fila * (len(filas) + 1)))
    t = gs.table
    tblPr = gs._element.graphic.graphicData.tbl.tblPr
    for a in ("bandRow", "firstRow"): tblPr.set(a, "0")
    st = tblPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}tableStyleId")
    if st is not None: st.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"   # sin estilo
    tot = sum(anchos)
    for i, a in enumerate(anchos): t.columns[i].width = Inches(w * a / tot)
    def celda(c, txt, fondo, col, neg=False, tam_=tam):
        c.fill.solid(); c.fill.fore_color.rgb = fondo; c.margin_left = c.margin_right = Inches(0.07); c.margin_top = c.margin_bottom = Inches(0.03)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = c.text_frame; tf.word_wrap = True; p = tf.paragraphs[0]
        for j, trozo in enumerate(re.split(r"\*\*(.+?)\*\*", str(txt))):
            if not trozo: continue
            r = p.add_run(); r.text = trozo; r.font.size = Pt(tam_); r.font.name = "Calibri"; r.font.bold = neg or j % 2 == 1; r.font.color.rgb = col
    for i, h in enumerate(cabecera): celda(t.cell(0, i), h, RGBColor.from_string("2E2420"), VERDE, True)
    for k, fila in enumerate(filas):
        t.rows[k + 1].height = Inches(alto_fila)
        for i, v in enumerate(fila):
            col = CREMA
            if color_col and i == color_col[0]: col = color_col[1].get(str(v), CREMA)
            celda(t.cell(k + 1, i), v, CARD if k % 2 == 0 else RGBColor.from_string("1C1512"), col, neg=bool(color_col and i == color_col[0]))
    t.rows[0].height = Inches(alto_fila)
    return t


def codigo(sl, x, y, w, h, txt, tam=9):
    rect(sl, x, y, w, h, RGBColor.from_string("0F0B09"), linea=RGBColor.from_string("3A2E28"))
    tb = sl.shapes.add_textbox(Inches(x + 0.1), Inches(y + 0.08), Inches(w - 0.2), Inches(h - 0.16)); tf = tb.text_frame; tf.word_wrap = False
    import textwrap
    maxc = int((w - 0.35) * 72 / (tam * 0.56))
    lins = []
    for l in txt.rstrip("\n").split("\n"):
        l = l.replace("\t", "    ")
        if len(l) > maxc:
            sang = len(l) - len(l.lstrip())
            lins += textwrap.wrap(l.strip(), maxc - sang - 4, initial_indent=" " * sang, subsequent_indent=" " * (sang + 4))
        else:
            lins.append(l)
    for i, l in enumerate(lins):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.space_after = Pt(0)
        r = p.add_run(); r.text = l or " "; r.font.name = "Consolas"; r.font.size = Pt(tam)
        r.font.color.rgb = RGBColor.from_string("F6B26B") if l.strip().startswith("@") else (RGBColor.from_string("8BC48F") if l.strip().startswith("//") else CREMA)


def foto(sl, ruta, x, y, w, leyenda=None):
    if not os.path.exists(ruta): return
    sl.shapes.add_picture(ruta, Inches(x), Inches(y), width=Inches(w))
    if leyenda: texto(sl, x, y - 0.3, w, 0.3, leyenda, 11, MARRON)


# ------------------------------------------------------------------ extractores de código real
def metodo_java(ruta, nombre, max_lineas=14, quitar=()):
    f = open(ruta, encoding="utf-8").read().split("\n")
    for i, l in enumerate(f):
        if re.search(r"\bvoid\s+" + re.escape(nombre) + r"\s*\(", l):
            ini = i
            while ini > 0 and f[ini - 1].strip().startswith("@"): ini -= 1
            prof, fin = 0, i
            for j in range(i, len(f)):
                prof += f[j].count("{") - f[j].count("}")
                if prof == 0 and "{" in "".join(f[i:j + 1]): fin = j; break
            b = [x[4:] if x.startswith("    ") else x for x in f[ini:fin + 1]]
            b = [x for x in b if not any(q in x for q in quitar)]
            return "\n".join(b[:max_lineas])
    raise KeyError(nombre)


def main():
    b, fe = D.leer_backend(), D.leer_frontend()
    ub = [p for p in b if p["nivel"] == "unitaria"]; rb = [p for p in b if p["nivel"] == "repositorio"]; ib = [p for p in b if p["nivel"] == "integración"]
    uf = [p for p in fe if p["nivel"] == "unitaria"]; inf = [p for p in fe if p["nivel"] == "integración"]; sf = [p for p in fe if p["nivel"] == "sistema"]
    todas = b + fe; total = len(todas); ok = sum(p["ok"] for p in todas)
    filas_cob, tot_cob = D.cobertura(); mx = D.matriz_permisos()
    n_mx = len(mx["lectura"]) + len(mx["escritura"]); ok_mx = sum(x[3] for x in mx["lectura"] + mx["escritura"])
    n_unit = len(ub) + len(rb) + len(uf)

    prs = Presentation(); prs.slide_width, prs.slide_height = Emu(12191695), Emu(6858000)

    # 1 portada
    sl = prs.slides.add_slide(prs.slide_layouts[6]); N[0] += 1
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = BG
    rect(sl, 0, 0, 0.18, 7.5, VERDE)
    texto(sl, 0.9, 1.0, 11, 0.5, "CALIDAD DE SOFTWARE · SPRINT 4", 16, VERDE, True)
    texto(sl, 0.9, 1.6, 11.5, 1.3, D.PROYECTO, 60, CREMA, True)
    texto(sl, 0.9, 2.9, 11.5, 1.0, "Pruebas unitarias, de integración y automatizadas: cómo se automatizaron, scripts y resultados", 22, MARRON)
    rect(sl, 0.9, 4.0, 1.5, 0.05, VERDE)
    texto(sl, 0.9, 4.25, 11, 0.5, D.EMPRESA, 20, CREMA, True)
    texto(sl, 0.9, 4.8, 11.8, 0.9, "   ·   ".join(D.EQUIPO), 16, GRIS)
    texto(sl, 0.9, 6.3, 11, 0.4, FECHA, 14, GRIS)
    sl.notes_slide.notes_text_frame.text = ("Apertura del Sprint 4 de CoffeeExport Manager. Presentaremos cómo se automatizaron las pruebas unitarias, de integración y de sistema, "
                                             "los scripts, los resultados reales, el tablero de Jira, quién trabajó en qué, el uso de IA y los bloqueos con sus soluciones. Tiempo: 30 segundos.")

    # 2 resultados
    sl = nueva(prs, "Resultados del Sprint 4", f"Ejecución real del {FECHA}: backend con mvn verify y frontend con node --test",
               f"Este sprint pasamos de 58 pruebas sobre el prototipo a {total} pruebas automáticas de tres niveles, todas aprobadas. El backend Spring Boot tiene {len(b)} pruebas "
               f"({len(ub)} unitarias, {len(rb)} de repositorio y {len(ib)} de integración) con {tot_cob[2]:.1f} % de cobertura de líneas. El frontend tiene {len(fe)} ({len(uf)} unitarias, "
               f"{len(inf)} de integración y {len(sf)} de sistema contra el servidor real). Las pruebas encontraron 7 defectos reales entre los sprints 3 y 4. Tiempo: 1 minuto.")
    for i, (v, e, c) in enumerate(((str(total), "pruebas automáticas", VERDE), (str(ok), "aprobadas, 0 fallidas", VERDE), (f"{tot_cob[2]:.1f} %", "cobertura de líneas del backend", AMBAR), ("7", "defectos hallados y corregidos", MARRON))):
        tarjeta_kpi(sl, 0.6 + i * 3.05, 1.6, 2.9, v, e, c)
    rect(sl, 0.6, 3.3, 5.0, 3.5, CARD)
    texto(sl, 0.8, 3.4, 4.6, 0.4, "Qué cambió frente al Sprint 3", 16, VERDE, True)
    viñetas(sl, 0.8, 3.9, 4.7, 2.9, ["Backend Spring Boot nuevo, **hecho con IA** (API REST, seguridad, JPA)", "Interfaz conectada a la API", "Los **44 casos del plan del Sprint 2** ya se ejecutan",
                                     "Pipeline en GitHub Actions: repite todo en cada cambio y cada lunes"], 13)
    tabla(sl, 5.85, 3.3, 6.9, ["Nivel", "Pruebas", "Aprobadas"], [
        ["Unitarias del backend (JUnit + Mockito)", len(ub), len(ub)], ["Repositorios (@DataJpaTest)", len(rb), len(rb)], ["Integración del backend (MockMvc)", len(ib), len(ib)],
        ["Unitarias de la interfaz (node:test)", len(uf), len(uf)], ["Integración de la interfaz (Playwright)", len(inf), len(inf)], ["Sistema: interfaz + API real", len(sf), len(sf)],
        ["**TOTAL**", f"**{total}**", f"**{ok}**"]], [4.6, 1.1, 1.2], 12, 0.42)

    # 3 estrategia
    sl = nueva(prs, "Estrategia: la pirámide de pruebas", "Muchas pruebas rápidas abajo, pocas y completas arriba",
               "Seguimos la pirámide de pruebas. En la base están las pruebas unitarias, rápidas y aisladas: Mockito reemplaza los repositorios. En el medio, las de integración, "
               "que levantan el contexto real de Spring con seguridad y base de datos H2 o abren un navegador. En la punta, las de sistema, que usan la interfaz y el servidor reales. "
               "Cada capa encuentra errores que las otras no ven. Tiempo: 1 minuto.")
    niveles = [("SISTEMA", f"{len(sf)} pruebas · navegador + servidor real", 3.2, AMBAR), ("INTEGRACIÓN", f"{len(ib) + len(inf)} pruebas · Spring completo, MockMvc, Playwright", 5.6, VERDE),
               ("UNITARIAS Y REPOSITORIO", f"{n_unit} pruebas · Mockito, @DataJpaTest, node:test", 8.0, MARRON)]
    for i, (n, d, w, c) in enumerate(niveles):
        x = 0.6 + (8.0 - w) / 2; y = 1.7 + i * 1.65
        rect(sl, x, y, w, 1.5, CARD, linea=c)
        texto(sl, x, y + 0.2, w, 0.5, n, 18, c, True, PP_ALIGN.CENTER); texto(sl, x, y + 0.75, w, 0.6, d, 12, CREMA, alinea=PP_ALIGN.CENTER)
    rect(sl, 8.9, 1.7, 3.9, 4.95, CARD)
    texto(sl, 9.1, 1.8, 3.5, 0.4, "Herramientas", 16, VERDE, True)
    viñetas(sl, 9.1, 2.3, 3.6, 4.3, ["**JUnit 5** y **Mockito**: unitarias", "**@DataJpaTest** con H2 en modo MySQL: repositorios", "**MockMvc** + Spring Security Test: API con cada rol",
                                     "**JaCoCo**: cobertura", "**node:test**: lógica de la interfaz", "**Playwright**: navegador real", "**GitHub Actions**: ejecución automática"], 12)

    # 4 automatización
    sl = nueva(prs, "Cómo se automatizaron las pruebas", "Del código al reporte, sin intervención humana",
               "La automatización tiene tres piezas. Primera: las pruebas son código en el repositorio, con el identificador del caso del plan en el nombre. Segunda: Maven ejecuta las unitarias con Surefire y las de integración con Failsafe, "
               "y JaCoCo mide la cobertura; en el frontend, node ejecuta las pruebas y Playwright maneja el navegador. Tercera: el pipeline de GitHub Actions lo repite en cada push, en cada pull request y cada lunes a las 6 de la mañana. "
               "El trabajo del frontend espera al del backend porque necesita su JAR para las pruebas de sistema. Tiempo: 1 minuto 30.")
    pasos = [("1 · Disparador", "push a main, pull request, manual o cada lunes 6:00 a. m.", MARRON), ("2 · Job backend", f"mvn verify: {len(ub) + len(rb)} unitarias + {len(ib)} IT + JaCoCo", VERDE),
             ("3 · Job frontend", f"npm run test:junit: {len(fe)} pruebas con Chromium y el JAR", VERDE), ("4 · Artefactos", "reportes JUnit, cobertura, capturas y JAR", AMBAR)]
    for i, (t, d, c) in enumerate(pasos):
        x = 0.6 + i * 3.1
        rect(sl, x, 1.7, 2.85, 1.7, CARD, linea=c)
        texto(sl, x + 0.1, 1.8, 2.65, 0.4, t, 15, c, True); texto(sl, x + 0.1, 2.3, 2.65, 1.0, d, 12, CREMA)
        if i < 3: texto(sl, x + 2.85, 2.25, 0.3, 0.5, "▶", 16, GRIS, alinea=PP_ALIGN.CENTER)
    codigo(sl, 0.6, 3.7, 6.3, 3.1, "jobs:\n  backend:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/setup-java@v4\n        with: { distribution: temurin, java-version: \"21\" }\n"
           "      - run: mvn -B verify\n        working-directory: backend\n  frontend:\n    needs: backend          # usa el JAR del job anterior\n"
           "    steps:\n      - run: npx playwright-core install --with-deps chromium\n      - run: npm run test:junit | tee ../resultados-frontend.xml", 10)
    rect(sl, 7.15, 3.7, 5.6, 3.1, CARD)
    texto(sl, 7.35, 3.8, 5.2, 0.4, "Detalles que importan", 15, VERDE, True)
    viñetas(sl, 7.35, 4.3, 5.3, 2.5, ["Surefire corre `*Test`; Failsafe corre `*IT` (se separaron a propósito)", "Cada prueba lleva el ID del plan y la HU: **[QC015][HU-01][RF-01]**",
                                      "Un script llena el Excel del plan leyendo los XML: SI solo si la prueba existe y pasó"], 12)

    # 5 unitaria
    sl = nueva(prs, "Pruebas unitarias: script y resultado", f"{len(ub)} en el backend, {len(uf)} en la interfaz, sin base de datos ni red",
               "Aquí se ve un script real: la prueba QA014 del plan. Verifica la regla de negocio RF-14: una salida de inventario mayor al stock disponible se rechaza con un mensaje exacto, "
               "el stock no cambia y no se guarda ningún movimiento. El repositorio está simulado con Mockito, por eso la prueba corre en milisegundos. A la derecha, el resultado por clase de servicio. "
               "Tiempo: 1 minuto 30.")
    cod = metodo_java(os.path.join(TEST, "unit", "InventarioServiceTest.java"), "qa014", 13)
    codigo(sl, 0.6, 1.6, 7.0, 3.5, cod, 9)
    texto(sl, 0.6, 5.2, 7.0, 0.35, "InventarioServiceTest.java · QA014 (RF-14)", 11, MARRON)
    rect(sl, 0.6, 5.65, 7.0, 1.2, CARD)
    viñetas(sl, 0.75, 5.72, 6.8, 1.1, ["**Mockito** simula los repositorios: la prueba aísla la regla de negocio", "Comprueba mensaje exacto, stock sin cambios y **ningún** movimiento guardado"], 12)
    por = OrderedDict()
    for p in ub: por.setdefault(p["clase"].replace("ServiceTest", ""), []).append(p)
    tabla(sl, 7.85, 1.6, 4.9, ["Servicio", "Pruebas", "OK"], [[c, len(v), sum(x["ok"] for x in v)] for c, v in por.items()] + [["Repositorios (JPA)", len(rb), sum(x["ok"] for x in rb)], ["Interfaz (PU-01 a PU-30)", len(uf), sum(x["ok"] for x in uf)]],
          [3.0, 1.0, 0.8], 11, 0.4)

    # 6 integración
    sl = nueva(prs, "Pruebas de integración: la API con cada rol", f"{len(ib)} pruebas con el contexto completo de Spring (seguridad, JPA, H2) y MockMvc",
               f"Las pruebas de integración llaman a la API real con MockMvc, iniciando sesión como cada rol. La más completa es la matriz de permisos: una sola prueba parametrizada genera {n_mx} comprobaciones, "
               f"una por rol y ruta, y verifica el código HTTP esperado. Pasaron {ok_mx} de {n_mx}. Si alguien cambia un permiso sin querer, el reporte dice qué rol y qué ruta falló. "
               "También hay pruebas del flujo completo de exportación, carga de PDF, pagos en euros, reportes y CORS. Tiempo: 1 minuto 30.")
    f = open(os.path.join(TEST, "integracion", "MatrizPermisosIT.java"), encoding="utf-8").read().split("\n")
    ini = next(i for i, l in enumerate(f) if "@ParameterizedTest" in l); csv_i = next(i for i, l in enumerate(f) if "@CsvSource" in l); fin = next(i for i, l in enumerate(f) if "void lectura" in l)
    q = lambda xs: [x[4:] if x.startswith("    ") else x for x in xs]
    cod = "\n".join(q(f[ini:csv_i]) + ['@CsvSource({', '  "admin@ritech.co,/api/clientes,200",', '  "bodega@ritech.co,/api/clientes,403",', '  "contador@ritech.co,/api/pagos,200",', '  ... })'] + q(f[fin:fin + 5]))
    codigo(sl, 0.6, 1.6, 7.3, 3.7, cod, 9)
    texto(sl, 0.6, 5.35, 7.3, 0.35, "MatrizPermisosIT.java · RF-04 / RNF-03", 11, MARRON)
    clases = OrderedDict()
    for p in ib: clases.setdefault(p["clase"], []).append(p)
    tabla(sl, 8.15, 1.6, 4.6, ["Clase *IT", "Pruebas", "OK"], [[c.replace("IT", ""), len(v), sum(x["ok"] for x in v)] for c, v in clases.items()], [3.0, 1.0, 0.7], 10.5, 0.36)
    rect(sl, 0.6, 5.8, 7.3, 1.05, CARD)
    texto(sl, 0.75, 5.85, 7.0, 0.95, [f"**{ok_mx} de {n_mx}** combinaciones rol × ruta correctas", "Sin sesión: 401 · rol sin permiso: 403 · inyección SQL y XSS rechazados"], 13, CREMA)

    # 7 sistema
    sl = nueva(prs, "Pruebas automatizadas de sistema", f"{len(sf)} pruebas: Playwright maneja la interfaz conectada al servidor Spring Boot real",
               "Estas son las pruebas más valiosas y más lentas. Playwright abre Chrome, la interfaz habla con el servidor Spring Boot real y la prueba comprueba lo que se ve y lo que quedó guardado en el servidor. "
               "A la izquierda, el dashboard con datos reales; a la derecha, una exportación creada con el asistente de cuatro pasos, con los PDF adjuntos y el stock descontado. "
               "Estas pruebas encontraron el defecto D-07 de CORS que ninguna otra prueba había visto. Tiempo: 1 minuto.")
    foto(sl, os.path.join(D.EVID, "PS-01-dashboard-conectado.png"), 0.6, 1.75, 4.2, "PS-01 · Dashboard con datos del servidor")
    foto(sl, os.path.join(D.EVID, "PS-07-exportacion-creada-servidor.png"), 5.0, 1.75, 4.2, "PS-07 · Exportación creada y stock descontado")
    tabla(sl, 9.45, 1.45, 3.35, ["ID", "Resultado"], [[p["id"], "OK" if p["ok"] else "FALLA"] for p in sf], [1, 1.4], 10.5, 0.36, color_col=(1, {"OK": VERDE, "FALLA": ROJO}))
    rect(sl, 0.6, 4.6, 8.6, 1.65, CARD)
    viñetas(sl, 0.75, 4.68, 8.3, 1.55, ["Login, cliente nuevo y NIF duplicado, producto, inventario (entrada y salida rechazada)", "Asistente de exportación con PDF, pago en euros y **RBAC**: bodega no ve Clientes", "Usabilidad móvil a 375 × 812 sin desplazamiento horizontal"], 12, sep=3)

    # 8 cobertura
    sl = nueva(prs, "Cobertura de código del backend", f"JaCoCo: {tot_cob[0]} de {tot_cob[1]} líneas cubiertas ({tot_cob[2]:.1f} %); meta del proyecto: 70 % (RNF-10)",
               f"JaCoCo mide qué líneas del backend ejecutan las pruebas. El total es {tot_cob[2]:.1f} % de líneas y {tot_cob[3]:.1f} % de instrucciones, por encima de la meta del 70 % que fijamos en el RNF-10. "
               "La gráfica muestra el porcentaje por paquete. Una cobertura alta no prueba que no haya errores, pero una baja sí demuestra que hay código sin probar. Tiempo: 1 minuto.")
    rect(sl, 0.6, 1.6, 8.2, 5.25, CARD)
    for i, (k, c, t, pl, pi) in enumerate(filas_cob):
        y = 1.72 + i * 0.355
        texto(sl, 0.75, y, 2.2, 0.35, k, 11, CREMA)
        rect(sl, 3.0, y + 0.05, 4.8, 0.25, RGBColor.from_string("2E2420"))
        rect(sl, 3.0, y + 0.05, max(0.05, 4.8 * pl / 100), 0.25, VERDE if pl >= 70 else AMBAR)
        texto(sl, 7.85, y, 0.9, 0.35, f"{pl:.0f} %", 11, CREMA, True, PP_ALIGN.RIGHT)
    tarjeta_kpi(sl, 9.1, 1.6, 3.6, f"{tot_cob[2]:.1f} %", "cobertura de líneas", VERDE)
    tarjeta_kpi(sl, 9.1, 3.2, 3.6, f"{tot_cob[3]:.1f} %", "cobertura de instrucciones", AMBAR)
    rect(sl, 9.1, 4.8, 3.6, 2.05, CARD)
    texto(sl, 9.25, 4.85, 3.3, 1.95, ["Medida al ejecutar las 139 pruebas del backend con `mvn verify`.", "El reporte HTML completo queda en target/site/jacoco y se guarda como artefacto del pipeline."], 11.5, GRIS)

    # 9 defectos
    sl = nueva(prs, "Defectos encontrados por las pruebas", "Siete defectos reales en los sprints 3 y 4; todos corregidos y con prueba de regresión",
               "Las pruebas automáticas encontraron siete defectos reales. Los tres primeros, del Sprint 3, eran del prototipo. D-04 y D-05 aparecieron al rediseñar. "
               "Los dos del Sprint 4 son los más interesantes. D-06: una prueba de integración mostró que crear cualquier exportación fallaba porque el código provisional medía 40 caracteres y la columna admite 20. "
               "D-07: el navegador no podía llamar al servidor porque faltaban las cabeceras CORS; el servidor respondía bien con MockMvc, que no simula un navegador, y solo la prueba de sistema lo detectó. Tiempo: 1 minuto 30.")
    d = [["D-01", "PU-25", "Alta", "El descuento de stock no era atómico", "Se valida todo antes de mover nada"], ["D-02", "PU-27", "Media", "Fechas en UTC: de noche, un día corrido", "Se usa la fecha local"],
         ["D-03", "PU-11", "Baja", "Guion largo para fechas vacías", "Guion simple unificado"], ["D-04", "PI-25", "Media", "El filtro del catálogo no ocultaba tarjetas", "Regla CSS [hidden]"],
         ["D-05", "PI-01", "Media", "KPI del dashboard en 0 por una función que tapaba otra", "Se renombró el ayudante"],
         ["D-06", "QC022 (IT)", "Alta", "Código provisional de exportación de 40 caracteres en columna de 20: toda creación fallaba", "Código provisional de 20 caracteres"],
         ["D-07", "PS-01 a PS-10", "Alta", "Sin cabeceras CORS: el navegador bloqueaba toda la API (bean mal nombrado)", "Bean corsConfigurationSource + CorsIT"]]
    tabla(sl, 0.6, 1.55, 12.15, ["ID", "Prueba", "Sev.", "Qué pasaba", "Corrección"], d, [0.7, 1.4, 0.8, 5.6, 3.6], 11.5, 0.62, color_col=(2, {"Alta": ROJO, "Media": AMBAR, "Baja": GRIS}))

    # 10 jira
    sl = nueva(prs, "Tablero de Jira", "Proyecto CoffeeExport Manager (CEM) · Sprint 4",
               "Esta es la captura del tablero de Jira del equipo con las tareas del Sprint 4 en sus columnas: Por hacer, En curso y Hecho. Cada tarea tiene responsable, que es quien la ejecutó. Tiempo: 1 minuto.")
    jira = os.path.join(D.SPRINT4, "jira", "tablero.png")
    if os.path.exists(jira):
        from PIL import Image
        w, h = Image.open(jira).size; ancho = min(12.1, 5.2 * w / h)
        sl.shapes.add_picture(jira, Inches(0.6 + (12.1 - ancho) / 2), Inches(1.55), width=Inches(ancho))
    else:
        rect(sl, 0.6, 1.6, 12.1, 4.9, CARD, linea=AMBAR)
        texto(sl, 0.6, 3.1, 12.1, 0.6, "PENDIENTE: captura real del tablero de Jira", 26, AMBAR, True, PP_ALIGN.CENTER)
        texto(sl, 1.5, 3.9, 10.3, 1.2, "El equipo debe crear el proyecto en Jira, mover las tareas del Sprint 4 a sus columnas y guardar la captura como Sprint4/jira/tablero.png. "
                                        "Después se vuelve a generar esta presentación con docs/tools/sprint4/make_pptx4.py y la imagen aparece aquí.", 14, CREMA, alinea=PP_ALIGN.CENTER)
    texto(sl, 0.6, 6.55, 12.1, 0.4, "Fuente: tablero de Jira del equipo." if os.path.exists(jira) else "No se usa ninguna imagen de relleno: esta diapositiva solo muestra Jira cuando existe la captura real.", 11, MARRON)

    # 11 quién trabajó en qué
    sl = nueva(prs, "Quién trabajó en qué", "Trabajo en equipo con un foco principal por integrante",
               "El Sprint 4 se trabajó en equipo: todos participaron en el desarrollo, las pruebas y la documentación. La tabla muestra el módulo del que es responsable cada integrante según el reparto del plan del proyecto "
               "y las pruebas del Sprint 4 que cubren ese módulo. Las tareas concretas y sus responsables reales están en el tablero de Jira. Cada integrante puede ampliar su parte de forma oral. Tiempo: 1 minuto.")
    tabla(sl, 0.6, 1.6, 12.15, ["Integrante", "Módulo de responsabilidad", "Pruebas del Sprint 4 que lo cubren"], [
        ["Brayan Guerrero", "Usuarios y acceso, Dashboard", "AuthServiceTest, UsuarioServiceTest, AutenticacionIT, MatrizPermisosIT, CorsIT, dashboard"],
        ["Juan Jurado", "Clientes y pagos", "ClienteServiceTest, PagoServiceTest, ClienteIT, pagos en EUR (PS-09)"],
        ["Nicoll López", "Productos y documentación", "ProductoServiceTest, DocumentoServiceTest, carga de PDF y documentos obligatorios"],
        ["Alexander Rodríguez", "Inventario y exportaciones", "InventarioServiceTest, ExportacionServiceTest, asistente de exportación (PS-07)"],
        ["Mario Zambrano", "Reportes y pruebas", "ReporteServiceTest, pipeline de GitHub Actions, README, E2E, documento y presentación"]], [2.3, 3.0, 6.0], 12, 0.7)
    texto(sl, 0.6, 6.2, 12.1, 0.7, "Todos los integrantes participaron en el desarrollo, las pruebas y la documentación del sprint; la tabla indica el módulo de responsabilidad de cada uno. "
          "Las tareas y los responsables concretos se registran en Jira.", 13, GRIS)

    # 12 IA
    sl = nueva(prs, "Uso de agente de IA", "Agente: Claude Code (Anthropic), modelo Claude Sonnet 5.5",
               "Transparencia sobre el uso de IA. El agente fue Claude Code, de Anthropic, modelo Claude Sonnet 5.5, usado por Mario desde la aplicación de escritorio. "
               f"En este sprint construyó el backend Spring Boot, escribió y ejecutó las {len(b)} pruebas del backend y las 10 de sistema, conectó la interfaz con la API y armó el pipeline. "
               "El equipo definió el alcance, eligió las opciones, aprobó los cambios y verificó los resultados ejecutando las pruebas. El agente también encontró y corrigió dos defectos en su propio código, D-06 y D-07. "
               "Los requisitos, el plan de pruebas, las fotos, Jira y la revisión final son del equipo. Tiempo: 1 minuto 30.")
    tabla(sl, 0.6, 1.55, 12.15, ["Parte del proyecto", "¿Con IA?", "Qué hizo el agente", "Decisión y verificación del equipo"], [
        ["Backend Spring Boot (API, seguridad, JPA)", "Sí", "Lo diseñó y escribió siguiendo el DDL y los nombres del plan", "El equipo definió los requisitos y revisó el resultado"],
        [f"{len(b)} pruebas del backend (JUnit, Mockito, MockMvc)", "Sí", "Las escribió y ejecutó; halló y corrigió D-06", f"Verificado con {len(b)} de {len(b)} aprobadas y {tot_cob[2]:.0f} % de cobertura"],
        ["Conexión de la interfaz y 10 pruebas de sistema", "Sí", "Creó la capa api.js y las pruebas Playwright; halló y corrigió D-07", "Verificado con 68 de 68 en el frontend"],
        ["Pipeline de GitHub Actions y README", "Sí", "Escribió el flujo de trabajo y la documentación", "Se valida con la ejecución en GitHub"],
        ["Requisitos, plan de pruebas (Sprint 1 y 2)", "No", "—", "Responsables: el equipo"],
        ["Descarga de las 11 fotos temporales al proyecto", "Sí", "Las descargó, las optimizó y cambió las rutas; repitió las 68 pruebas", "Verificado con 68 de 68 aprobadas"],
        ["Fotos propias, Jira y revisión final", "No", "—", "Responsables: el equipo"]], [3.6, 0.9, 4.0, 3.65], 11, 0.55, color_col=(1, {"Sí": VERDE, "No": GRIS}))

    # 13 bloqueos
    sl = nueva(prs, "Bloqueos encontrados y soluciones", "Qué nos frenó y cómo se resolvió",
               "Estos fueron los bloqueos principales. El más grande: el backend del Sprint 1 no estaba disponible, así que se construyó uno nuevo con IA y se declaró así. "
               "En el equipo solo había Java 25 y no había Maven, Docker ni MySQL; se descargó Maven a una carpeta del proyecto y las pruebas usan H2 en modo MySQL. "
               "Failsafe tuvo que configurarse para que las pruebas de integración corrieran. Quedan dos puntos mitigados: publicar solo en modo demostración en Vercel, y las fotos, que son temporales pero ya están alojadas en el proyecto. La suite del backend ya se verificó en MySQL real. Tiempo: 1 minuto 30.")
    cortos = [["El backend del Sprint 1 no estaba disponible", "Se construyó un backend nuevo con IA, según el DDL y el plan", "Resuelto"],
              ["Solo Java 25: sin Maven, Docker ni MySQL", "Maven portátil en el proyecto; H2 en modo MySQL; release 21", "Resuelto"],
              ["Lombok no compilaba en JDK 23+", "annotationProcessorPaths en el compilador", "Resuelto"],
              ["Las pruebas *IT no se ejecutaban", "Se configuró Failsafe con el mismo argLine", "Resuelto"],
              ["CORS bloqueaba la web (D-07)", "Bean renombrado y CorsIT", "Resuelto"],
              ["Playwright sin su Chromium", "PW_CHANNEL=chrome; en CI se instala Chromium", "Resuelto"],
              ["Spring Boot no corre en Vercel", "Publicada en modo demostración: coffeeexport-manager.vercel.app", "Mitigado"],
              ["Sin MySQL para probar el perfil mysql", "MySQL 8.4.10 portable en tools/; suite completa (139) aprobada en MySQL real", "Resuelto"],
              ["Sin fotos propias del producto", "11 fotos temporales (Unsplash) alojadas en el proyecto; se reemplazan por archivos propios", "Mitigado"]]
    tabla(sl, 0.6, 1.5, 12.15, ["Bloqueo", "Solución", "Estado"], cortos, [4.6, 5.6, 1.2], 11.5, 0.54, color_col=(2, {"Resuelto": VERDE, "Mitigado": AMBAR, "Pendiente": ROJO}))

    # 14 cierre
    sl = nueva(prs, "Conclusiones y próximos pasos", "Calidad medible y repetible",
               f"Cerramos con las conclusiones. Se automatizaron {total} pruebas de tres niveles, todas aprobadas, con {tot_cob[2]:.1f} % de cobertura en el backend, y los 44 casos del plan del Sprint 2 tienen resultado real. "
               "Los defectos se corrigieron y quedaron cubiertos. El pipeline detecta regresiones solo. Los próximos pasos son medir Lighthouse y accesibilidad, reemplazar las fotos temporales y mantener el tablero de Jira al día. Tiempo: 1 minuto.")
    rect(sl, 0.6, 1.6, 6.0, 5.2, CARD)
    texto(sl, 0.8, 1.7, 5.6, 0.4, "Conclusiones", 18, VERDE, True)
    viñetas(sl, 0.8, 2.25, 5.6, 4.5, [f"**{total} pruebas** automáticas en tres niveles, **{ok} aprobadas**", f"**{tot_cob[2]:.1f} %** de cobertura de líneas en el backend", "Los **44 casos** del plan del Sprint 2, ejecutados con evidencia",
                                      "**7 defectos** reales hallados, corregidos y con prueba de regresión", "El pipeline repite todo en cada cambio y cada lunes"], 14, sep=8)
    rect(sl, 6.85, 1.6, 5.9, 5.2, CARD)
    texto(sl, 7.05, 1.7, 5.5, 0.4, "Próximos pasos", 18, AMBAR, True)
    viñetas(sl, 7.05, 2.25, 5.5, 4.5, ["Medir **Lighthouse** y accesibilidad con axe en la interfaz", "Reemplazar las fotos temporales por las fotos propias", "Interfaz publicada en Vercel (modo demostración): coffeeexport-manager.vercel.app",
                                       "Mantener el tablero de Jira al día", "Ampliar pruebas de carga y de accesibilidad"], 14, sep=8)

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    prs.save(SALIDA); print("Guardado", SALIDA, N[0], "diapositivas")


if __name__ == "__main__":
    main()
