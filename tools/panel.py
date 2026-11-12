#!/usr/bin/env python3
"""Arma el panel web de la Matriz en `dist/` para publicarlo en Cloudflare.

  dist/index.html        el panel (panel/index.html, app.js, espacio.js, estilo.css)
  dist/vendor/           three.js minificado, armado aquí con esbuild desde tools/three (versiones fijas)
  dist/matriz.json       los datos que genera tools/generar.py
  dist/contexto/*.md     los archivos de contexto, para copiarlos o pegarlos en cualquier IA
  dist/EMI.md            quién es Emi y sus reglas
  dist/llms.txt          mapa breve para IA que leen una URL
  dist/robots.txt        pide a los buscadores no indexar
  dist/_headers          lo mismo como cabecera, más caché corta

Todo lo publicado ya es público en GitHub (lianfixx/MATRIZ); el panel no añade información.
Uso: python3 tools/panel.py [--salida dist]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def llms(d: dict, base: str) -> str:
    L = ["# Matriz General de Emi", "",
         "> Mapa de todo el trabajo de Emi (Yohualli Emiliano García Milla): cerebros, repositorios de GitHub, "
         "tareas programadas y skills. Fuente de verdad: https://github.com/lianfixx/MATRIZ", "",
         "Antes de trabajar en un repositorio, lee su AGENTS.md, ia/REGLAS.md e ia/PROTOCOLO.md. Todo cambio se "
         "registra en su CHANGELOG.md con la línea «Agente:». Si no puedes escribir, entrega un «Registro pendiente "
         "para el repositorio».", "", "## Cerebros", ""]
    for c in d["cerebros"]:
        L.append(f"- [{c['nombre']}]({base}contexto/{c['id']}.CONTEXTO.md): {c['descripcion']}")
    L += ["", "## Datos", "", f"- [MATRIZ_GENERAL.md]({base}MATRIZ_GENERAL.md): el archivo único con todo (empieza aquí)",
          f"- [matriz.json]({base}matriz.json): todo en JSON",
          f"- [EMI.md]({base}EMI.md): quién es Emi y sus reglas",
          f"- Conector MCP de solo lectura (Streamable HTTP): {base}mcp", ""]
    return "\n".join(L)


PANEL_URL = os.environ.get("PANEL_URL", "https://matriz.milla-abogados.workers.dev/")


def armar_three(destino: Path) -> None:
    """three.js no se guarda minificado en el repositorio: se arma en cada publicación con las
    versiones fijas de tools/three/package-lock.json (npm ci) y solo con las piezas que usa el panel."""
    carpeta = RAIZ / "tools" / "three"
    if not shutil.which("npm"):
        raise SystemExit("Falta Node.js (npm) para armar three.js del panel.")
    if not (carpeta / "node_modules" / "three").exists():
        subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=carpeta, check=True)
    destino.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(carpeta / "node_modules" / ".bin" / "esbuild"), "entrada.mjs", "--bundle", "--format=esm",
                    "--minify", "--legal-comments=none", f"--outfile={destino / 'three.matriz.min.js'}"],
                   cwd=carpeta, check=True, capture_output=True)
    shutil.copy(carpeta / "node_modules" / "three" / "LICENSE", destino / "THREE-LICENSE")


def armar(salida: Path, base: str = PANEL_URL) -> None:
    datos = RAIZ / "matriz.json"
    if not datos.exists():
        raise SystemExit("Falta matriz.json: corre antes tools/generar.py")
    d = json.loads(datos.read_text(encoding="utf-8"))
    if salida.exists():
        shutil.rmtree(salida)
    (salida / "contexto").mkdir(parents=True)
    for nombre in ("index.html", "app.js", "espacio.js", "estilo.css"):
        shutil.copy(RAIZ / "panel" / nombre, salida / nombre)
    shutil.copy(datos, salida / "matriz.json")
    shutil.copy(RAIZ / "EMI.md", salida / "EMI.md")
    if (RAIZ / "MATRIZ_GENERAL.md").exists():
        shutil.copy(RAIZ / "MATRIZ_GENERAL.md", salida / "MATRIZ_GENERAL.md")
    armar_three(salida / "vendor")
    for p in sorted((RAIZ / "contexto").glob("*.md")):
        shutil.copy(p, salida / "contexto" / p.name)
    (salida / "llms.txt").write_text(llms(d, base), encoding="utf-8")
    (salida / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (salida / "_headers").write_text(
        "/*\n  X-Robots-Tag: noindex, nofollow\n  Referrer-Policy: no-referrer\n  X-Content-Type-Options: nosniff\n"
        "  X-Frame-Options: DENY\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n"
        "  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'\n"
        "/vendor/*\n  Cache-Control: public, max-age=604800\n"
        "/matriz.json\n  Cache-Control: no-cache\n/MATRIZ_GENERAL.md\n  Content-Type: text/markdown; charset=utf-8\n  Cache-Control: no-cache\n/EMI.md\n  Content-Type: text/markdown; charset=utf-8\n/contexto/*\n  Content-Type: text/markdown; charset=utf-8\n  Cache-Control: no-cache\n",
        encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--salida", type=Path, default=RAIZ / "dist")
    a = ap.parse_args()
    armar(a.salida)
    print(f"Panel armado en {a.salida}: {sum(1 for p in a.salida.rglob('*') if p.is_file())} archivos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
