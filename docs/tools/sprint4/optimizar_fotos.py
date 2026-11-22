# -*- coding: utf-8 -*-
"""Ajusta el tamaño de las fotos al que realmente se muestra (rendimiento: Lighthouse) y crea la portada ligera hero-800.jpg.
Se ejecuta después de fotos_temporales.py o tras reemplazar las fotos por las propias.
Uso: python docs/tools/sprint4/optimizar_fotos.py"""
import os

from PIL import Image

IMG = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "frontend", "img"))
# archivo -> (ancho máximo, calidad JPEG)
AJUSTES = {"hero.jpg": (1400, 76), "cierre.jpg": (1400, 70), "normativa.jpg": (720, 74), "cifras.jpg": (720, 74), "proceso.jpg": (720, 74)}


def guardar(im, ruta, ancho, calidad):
    if im.width > ancho:
        im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)
    im.save(ruta, "JPEG", quality=calidad, optimize=True, progressive=True)
    return os.path.getsize(ruta) / 1024


for nombre, (ancho, calidad) in AJUSTES.items():
    ruta = os.path.join(IMG, nombre)
    im = Image.open(ruta); im.load(); im = im.convert("RGB")
    antes = os.path.getsize(ruta) / 1024
    print(f"{nombre:14} {antes:5.0f} KB -> {guardar(im, ruta, ancho, calidad):5.0f} KB")
im = Image.open(os.path.join(IMG, "hero.jpg")).convert("RGB")
print(f"{'hero-800.jpg':14} nuevo   -> {guardar(im, os.path.join(IMG, 'hero-800.jpg'), 800, 72):5.0f} KB")
