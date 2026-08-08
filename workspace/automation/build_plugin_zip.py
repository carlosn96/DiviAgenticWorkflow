#!/usr/bin/env python3
"""
build_plugin_zip.py — Empaqueta el plugin sanpablo-librerias en un ZIP
instalable por WordPress.

MOTIVO
------
Un zip construido con Compress-Archive (PowerShell) usa separadores "\\"
en las entradas. Al subirlo por FTP, el servidor los interpreta como parte
del nombre de archivo (sanpablo-librerias\\sanpablo-librerias.php), y
WordPress no encuentra el plugin ("el plugin no existe").

Este script usa el módulo estándar `zipfile` de Python, que siempre escribe
separadores "/" en las entradas, generando una estructura limpia:

    sanpablo-librerias/
    ├── sanpablo-librerias.php
    ├── assets/
    ├── includes/
    └── vendor/

USO
---
    python build_plugin_zip.py
    python build_plugin_zip.py --plugin <ruta-al-plugin> --out <ruta-zip-salida>

Seguridad: solo LEE el directorio del plugin y escribe el zip de salida.
No modifica el plugin ni ningún archivo remoto.
"""

import argparse
import os
import re
import sys
import zipfile

PLUGIN_REL = os.path.join(
    "app", "public", "wp-content", "plugins", "sanpablo-librerias"
)

# Nombres no deseados dentro del zip (git, cache, basura).
EXCLUDED_NAMES = {".git", "__pycache__", ".DS_Store", "Thumbs.db"}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".log", ".swp")
# Archivos sueltos del repo que no deben viajar en el paquete de producción.
# README.md y AGENTS.md son documentación de desarrollo; WordPress no las usa
# (el estándar del repo público es readme.txt, no README.md) y no forman parte
# del plugin en producción.
EXCLUDED_FILES = {".gitignore", ".gitattributes", ".editorconfig", "README.md", "AGENTS.md"}


def plugin_root():
    """Resuelve la raíz del proyecto (donde vive app/)."""
    here = os.path.dirname(os.path.abspath(__file__))
    # automation/ -> DAW_bundle/workspace -> DAW_bundle -> sanpablo-mx
    for _ in range(4):
        if os.path.isdir(os.path.join(here, "app", "public", "wp-content", "plugins")):
            return here
        here = os.path.dirname(here)
    return None


def plugin_version(src_dir: str) -> str:
    """Lee la versión desde el header del archivo principal del plugin."""
    main_file = os.path.join(src_dir, "sanpablo-librerias.php")
    try:
        with open(main_file, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except OSError:
        return "0.0.0"
    m = re.search(r"Version:\s*([0-9]+\.[0-9]+\.[0-9]+)", content)
    return m.group(1) if m else "0.0.0"


def should_skip(relpath: str, name: str) -> bool:
    parts = relpath.replace(os.sep, "/").split("/")
    if any(p in EXCLUDED_NAMES for p in parts):
        return True
    if name in EXCLUDED_FILES:
        return True
    return name.endswith(EXCLUDED_SUFFIXES)


def build_zip(src_dir: str, zip_path: str) -> int:
    src_dir = os.path.normpath(src_dir)
    if not os.path.isdir(src_dir):
        print(f"ERROR: no existe el directorio del plugin: {src_dir}", file=sys.stderr)
        return 1

    base_name = os.path.basename(src_dir)  # sanpablo-librerias
    zip_path = os.path.abspath(zip_path)
    os.makedirs(os.path.dirname(zip_path), exist_ok=True) if os.path.dirname(zip_path) else None

    count = 0
    skipped = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src_dir):
            # Podar directorios excluidos in-place para no recorrerlos.
            dirs[:] = [d for d in dirs if d not in EXCLUDED_NAMES]
            for name in files:
                if should_skip(name, name):
                    skipped += 1
                    continue
                full = os.path.join(root, name)
                rel = os.path.relpath(full, src_dir)
                entry = f"{base_name}/{rel}".replace(os.sep, "/")
                zf.write(full, entry)
                count += 1

    print(f"OK: {zip_path}")
    print(f"    entradas: {count} (omitidas: {skipped})")
    print(f"    tamaño:   {os.path.getsize(zip_path):,} bytes")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Empaqueta sanpablo-librerias en un zip instalable.")
    parser.add_argument("--plugin", help="Ruta al directorio del plugin (default: app/public/wp-content/plugins/sanpablo-librerias)")
    parser.add_argument("--out", help="Ruta del zip de salida (default: ./sanpablo-librerias-<version>.zip)")
    args = parser.parse_args()

    root = plugin_root()
    src = args.plugin or (os.path.join(root, PLUGIN_REL) if root else None)
    if not src or not os.path.isdir(src):
        print(
            "ERROR: no se pudo localizar el plugin. Pasa --plugin <ruta>.",
            file=sys.stderr,
        )
        return 1

    version = plugin_version(src)
    out = args.out or os.path.join(os.getcwd(), f"sanpablo-librerias-{version}.zip")
    return build_zip(src, out)


if __name__ == "__main__":
    sys.exit(main())
