#!/usr/bin/env python3
"""Junta los costos de la API que dejan las corridas (skill api-relevo).

Busca en las carpetas dadas los estados de corrida (ESTADO*.json, *-ia.json, *triaje*.json, *-api.json) con
«costo_usd» y suma por mes y por origen. Las notas parciales no se cuentan (su costo ya está en el estado).
Con --bitacora suma en cambio las líneas «AAAA-MM-DD … USD <cifra>» de bitácoras Markdown (no mezclar ambas
fuentes del mismo proyecto: se contaría dos veces). Solo lee.

Uso: python3 costos.py <carpeta> [<carpeta> …] [--mes AAAA-MM]
Ejemplo: python3 skills/api-relevo/scripts/costos.py revisiones automatizaciones ../dof-trabajo/fuentes
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


def costos_json(dato, ruta: str, salida: list) -> None:
    if isinstance(dato, dict):
        fecha = str(dato.get("fecha", ""))[:7]
        if isinstance(dato.get("costo_usd"), (int, float)):
            salida.append((fecha, ruta, float(dato["costo_usd"])))
            return  # el total del archivo ya incluye sus partes
        for v in dato.values():
            costos_json(v, ruta, salida)
    elif isinstance(dato, list):
        for v in dato:
            costos_json(v, ruta, salida)


BITACORA = "--bitacora" in sys.argv


def recorrer(carpetas: list[str]) -> list[tuple[str, str, float]]:
    filas = []
    for c in carpetas:
        for p in Path(c).rglob("*"):
            if p.suffix == ".json" and re.search(r"^ESTADO|-ia\.json$|triaje|-api\.json$", p.name) and not BITACORA:
                try:
                    costos_json(json.loads(p.read_text(encoding="utf-8")), str(p), filas)
                except (ValueError, OSError):
                    pass
            elif p.suffix == ".md" and BITACORA:
                for linea in p.read_text(encoding="utf-8", errors="replace").splitlines():
                    m = re.search(r"(\d{4}-\d{2})-\d{2}.*?USD (\d+(?:\.\d+)?)", linea)
                    if m:
                        filas.append((m.group(1), str(p), float(m.group(2))))
    return filas


def main(argv: list[str]) -> int:
    mes = argv[argv.index("--mes") + 1] if "--mes" in argv else ""
    carpetas = [a for i, a in enumerate(argv) if i and not a.startswith("--") and argv[i - 1] != "--mes"]
    if not carpetas:
        print(__doc__)
        return 2
    filas = [f for f in recorrer(carpetas) if not mes or f[0] == mes]
    por_mes, por_origen = defaultdict(float), defaultdict(float)
    for fecha, ruta, usd in filas:
        por_mes[fecha or "sin fecha"] += usd
        por_origen[str(Path(ruta).parent)] += usd
    for k in sorted(por_mes):
        print(f"{k}: USD {por_mes[k]:.4f}")
    for k, v in sorted(por_origen.items(), key=lambda x: -x[1]):
        print(f"  {k}: USD {v:.4f}")
    print(f"Total: USD {sum(u for _, _, u in filas):.4f} en {len(filas)} registros")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
