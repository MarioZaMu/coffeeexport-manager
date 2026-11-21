# -*- coding: utf-8 -*-
"""Llena el plan de pruebas del Sprint 2 (Excel) con los resultados REALES de la ejecución automática.

Entradas : backend/target/surefire-reports y failsafe-reports (JUnit) + un XML JUnit del frontend (node --test).
Salida   : docs/sprint2/Plan_de_Pruebas_CoffeeExport_Manager.xlsx (columnas E, H, I, J y K de cada caso).
Uso      : python docs/tools/llenar_plan_pruebas.py [ruta/frontend.xml]
Un caso se marca SI solo si su prueba automática existe y pasó; nunca se inventa un resultado.
"""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

import openpyxl

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
XLSX = os.path.join(RAIZ, "docs", "sprint2", "Plan_de_Pruebas_CoffeeExport_Manager.xlsx")
FRONT_XML = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "docs", "sprint4", "resultados", "frontend.xml")

# Casos "del sistema": además de la prueba de API, los verifica una prueba de interfaz contra el backend real.
SISTEMA = {"QC015": "PS-01", "QC016": "PS-03", "QC017": "PS-05", "QC018": "PS-06", "QC019": "PS-10", "QC021": "PS-07", "QC025": "PI-24"}


def leer_backend():
    res = {}
    for f in glob.glob(os.path.join(RAIZ, "backend", "target", "surefire-reports", "TEST-*.xml")) + glob.glob(os.path.join(RAIZ, "backend", "target", "failsafe-reports", "TEST-*.xml")):
        raiz = ET.parse(f).getroot()
        fecha = datetime.fromisoformat(raiz.get("timestamp").replace("Z", "+00:00")) if raiz.get("timestamp") else None
        for tc in raiz.iter("testcase"):
            m = re.match(r"^(q[ac]\d{3})$", tc.get("name") or "")
            if m:
                res[m.group(1).upper()] = dict(clase=tc.get("classname").split(".")[-1], metodo=tc.get("name"), seg=float(tc.get("time")),
                                               ok=tc.find("failure") is None and tc.find("error") is None, fecha=fecha)
    return res


def leer_frontend():
    res = {}
    if not os.path.exists(FRONT_XML):
        return res
    raiz = ET.parse(FRONT_XML).getroot()
    for tc in raiz.iter("testcase"):
        m = re.match(r"^(P[SIU]-\d+)\b", tc.get("name") or "")
        if m:
            res[m.group(1)] = dict(seg=float(tc.get("time")), ok=tc.find("failure") is None and tc.find("error") is None)
    return res


def main():
    back, front = leer_backend(), leer_frontend()
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["Hoja1"]
    llenos = sinprueba = 0
    for r in range(7, ws.max_row + 1):
        pid = ws.cell(r, 1).value
        if not pid:
            continue
        # El código ya existe y sus nombres coinciden con la implementación: se retira la marca de verificación pendiente.
        if ws.cell(r, 5).value:
            ws.cell(r, 5).value = ws.cell(r, 5).value.replace(" [VERIFICAR]", "")
        partes, ok, fecha = [], True, None
        if pid in back:
            b = back[pid]
            partes.append(f"JUnit {b['clase']}.{b['metodo']}: {'APROBADA' if b['ok'] else 'FALLIDA'} ({b['seg']:.2f} s)")
            ok = ok and b["ok"]; fecha = b["fecha"]
        sis = SISTEMA.get(pid)
        if sis and sis in front:
            partes.append(f"Playwright {sis}: {'APROBADA' if front[sis]['ok'] else 'FALLIDA'} ({front[sis]['seg']:.1f} s)")
            ok = ok and front[sis]["ok"]
            fecha = fecha or datetime.now()
        if not partes:
            ws.cell(r, 8).value = "Sin prueba automática"; ws.cell(r, 9).value = None; ws.cell(r, 10).value = None
            ws.cell(r, 11).value = "Automatizar"; sinprueba += 1
            continue
        ws.cell(r, 8).value = ("Cumple lo esperado. " if ok else "NO cumple lo esperado. ") + "; ".join(partes)
        ws.cell(r, 9).value = "SI" if ok else "NO"
        ws.cell(r, 10).value = (fecha or datetime.now()).replace(tzinfo=None).replace(hour=0, minute=0, second=0, microsecond=0)
        ws.cell(r, 10).number_format = "d-mmm-yy"
        ws.cell(r, 11).value = "Se mantiene en la regresión automática (GitHub Actions)" if ok else "Corregir el defecto y repetir la prueba"
        llenos += 1
    wb.save(XLSX)
    print(f"Plan actualizado: {llenos} casos con resultado real, {sinprueba} sin prueba automática.")


if __name__ == "__main__":
    main()
