# -*- coding: utf-8 -*-
"""Descarga las fotos temporales de Unsplash al proyecto (frontend/img) para que la web no dependa de un servidor externo.
Cada archivo se baja a una carpeta temporal, se comprueba con Pillow que sea una imagen válida y solo entonces se copia.
Cuando el equipo tenga fotos propias, basta con reemplazar los archivos de frontend/img con los mismos nombres.
Uso: python docs/tools/sprint4/fotos_temporales.py"""
import io
import os
import sys
import tempfile
import urllib.request

from PIL import Image

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
IMG = os.path.join(REPO, "frontend", "img")

# nombre -> (id de foto en Unsplash, ancho final, subcarpeta)
FOTOS = {
    "hero": ("1672851612794-6687bf0bf1a3", 1400, ""),
    "proceso": ("1742576437150-3a79cae681f2", 900, ""),
    "cifras": ("1493925410384-84f842e616fb", 1000, ""),
    "normativa": ("1573710661345-610f790e1218", 1000, ""),
    "cierre": ("1590497008432-598f04441de8", 1800, ""),
    "cafe-arabica": ("1447933601403-0c6688de566e", 600, "productos"),
    "cafe-robusta": ("1513530176992-0cf39c4cbed4", 600, "productos"),
    "cafe-castillo": ("1675306408031-a9aad9f23308", 600, "productos"),
    "cacao-grano": ("1507576164121-220762647800", 600, "productos"),
    "cacao-polvo": ("1602101025912-f4a36c505e28", 600, "productos"),
    "cacao-nibs": ("1545567724-9b16e57c906d", 600, "productos"),
}


def bajar(foto_id, ancho):
    url = f"https://images.unsplash.com/photo-{foto_id}?fm=jpg&fit=max&q=80&w={ancho}"
    req = urllib.request.Request(url, headers={"User-Agent": "coffeeexport-fotos/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        tipo = r.headers.get("Content-Type", "")
        datos = r.read()
    if not tipo.startswith("image/"):
        raise ValueError(f"no es una imagen ({tipo})")
    return url, datos


def main():
    total = 0
    with tempfile.TemporaryDirectory() as tmp:
        for nombre, (foto_id, ancho, sub) in FOTOS.items():
            url, datos = bajar(foto_id, ancho)
            im = Image.open(io.BytesIO(datos)); im.load()
            if im.width < 200 or im.height < 200:
                raise ValueError(f"{nombre}: imagen demasiado pequeña {im.size}")
            im = im.convert("RGB")
            if im.width > ancho: im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)
            borrador = os.path.join(tmp, nombre + ".jpg")
            im.save(borrador, "JPEG", quality=80, optimize=True, progressive=True)
            destino_dir = os.path.join(IMG, sub) if sub else IMG
            os.makedirs(destino_dir, exist_ok=True)
            destino = os.path.join(destino_dir, nombre + ".jpg")
            with open(borrador, "rb") as a, open(destino, "wb") as b: b.write(a.read())
            kb = os.path.getsize(destino) / 1024; total += kb
            print(f"{nombre:14} {im.width}x{im.height}  {kb:6.0f} KB  <- {url}")
    print(f"Total: {total:.0f} KB en {len(FOTOS)} fotos")


if __name__ == "__main__":
    sys.exit(main())
