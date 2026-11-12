#!/usr/bin/env python3
"""Genera la Matriz General a partir de los repositorios de Emi.

Lee `matriz.config.json` (cerebros y sus repositorios), `inventario.json` (tareas programadas, skills
instaladas y vencimientos), `tablero/` (pendientes y notas de Emi por cerebro) y `proyectos/`
(proyectos nuevos), abre cada repositorio y escribe:

  MATRIZ_GENERAL.md          el archivo único: todo lo necesario para que cualquier IA entienda todo
  MATRIZ.md                  portada para Obsidian y GitHub
  matriz.json                los mismos datos, para el panel y el conector
  cerebros/<Nombre>.md       una nota por cerebro
  repos/<nombre>.md          una nota por repositorio (nodos del grafo en Obsidian)
  contexto/<id>.CONTEXTO.md  un archivo por cerebro para pegar en cualquier IA
  bitacora/AAAA-MM.md        qué IA hizo qué, por día (acumulativo: nunca borra líneas)

Uso:
  python3 tools/generar.py --repos-dir <carpeta con los clones>   # usa clones locales
  python3 tools/generar.py --clonar                               # clona lo que falte (GitHub Actions)

Solo biblioteca estándar. No escribe en ningún otro repositorio. Este repositorio es público: de los
repositorios privados publica solo nombre, cerebro, fecha y conteos de actividad, y todo texto que viene
de un repositorio pasa por `reservar()` (expedientes, clientes, correos, teléfonos, CURP, RFC, montos).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import unicodedata
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
FECHA = re.compile(r"(\d{4}-\d{2}-\d{2})")
ENCABEZADO = re.compile(r"^#{2,3}\s+(.+?)\s*$")
GENERADO = "tools/generar.py · no editar a mano: se reescribe cada día"
SEMANAS = 8
PANEL = "https://matriz.milla-abogados.workers.dev"


# ---------------------------------------------------------------- utilidades

def fecha_valida(iso: str) -> bool:
    if not re.match(r"^\d{4}-\d{2}-\d{2}", str(iso)):
        return False  # solo AAAA-MM-DD (no semanas ISO como 2026-W45-1)
    try:
        dt.date.fromisoformat(str(iso)[:10])
        return True
    except ValueError:
        return False


def fecha_corta(iso: str) -> str:
    if not iso:
        return "sin dato"
    if not fecha_valida(iso):
        return str(iso)
    a, m, d = str(iso)[:10].split("-")
    return f"{int(d)} {MESES[int(m) - 1]} {a}"


def git(args: list[str], cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def leer(p: Path, maximo: int = 2_000_000) -> str:
    """Lee un archivo de texto del repositorio. Nunca sigue enlaces simbólicos (podrían apuntar fuera)."""
    try:
        if p.is_symlink() or not p.is_file() or p.stat().st_size > maximo:
            return ""
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def resumen_readme(texto: str) -> str:
    """Primer párrafo de prosa del README, sin títulos, tablas, listas ni insignias."""
    parrafo: list[str] = []
    for linea in texto.splitlines():
        s = linea.strip()
        if not s:
            if parrafo:
                break
            continue
        if s.startswith(("#", "|", "!", "<", "```", "- ", "* ", ">")) and not parrafo:
            continue
        parrafo.append(s)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", " ".join(parrafo))
    t = re.sub(r"[*_`]", "", t)
    return t if len(t) <= 280 else t[:277].rsplit(" ", 1)[0] + "…"


def campo(cuerpo: str, nombre: str) -> str:
    m = re.search(rf"^\s*[-*]\s*(?:\*\*)?{nombre}(?:\*\*)?\s*:\s*(?:\*\*)?\s*(.+)$", cuerpo, re.M | re.I)
    return m.group(1).strip().strip("*").strip() if m else ""


def entradas_changelog(texto: str, maximo: int = 8) -> list[dict]:
    """Entradas de un CHANGELOG con fecha en el encabezado (## o ###, la fecha en cualquier posición).

    Acepta `## 2026-11-11 · título`, `## 0.3.0 · 2026-11-11 · título` y `### Skill 1.2 — 2026-11-09:`.
    Devuelve las más recientes primero, sin importar el orden del archivo.
    """
    salida: list[dict] = []
    actual: dict | None = None
    cuerpo: list[str] = []

    def cerrar() -> None:
        if actual is not None:
            c = "\n".join(cuerpo)
            actual["agente"] = campo(c, "Agente")
            actual["pendiente"] = campo(c, "Pendiente")
            salida.append(actual)

    for linea in texto.splitlines():
        m = ENCABEZADO.match(linea)
        f = FECHA.search(m.group(1)) if m else None
        if m and f and fecha_valida(f.group(1)):
            cerrar()
            titulo = (m.group(1)[:f.start()] + " " + m.group(1)[f.end():]).strip()
            titulo = re.sub(r"^[\s·\-–—:|]+|[\s·\-–—:|]+$", "", titulo)
            titulo = re.sub(r"\s*[·\-–—:|]\s*[·\-–—:|]\s*", " · ", titulo)
            actual = {"fecha": f.group(1), "titulo": titulo or "sin título"}
            cuerpo = []
        elif actual is not None:
            cuerpo.append(linea)
    cerrar()
    salida.sort(key=lambda e: e["fecha"], reverse=True)
    return salida[:maximo]


def skills(repo: Path) -> list[dict]:
    """SKILL.md propios del repositorio (se omiten los puentes .claude/ y .agents/)."""
    encontrados: dict[str, dict] = {}
    for p in sorted(repo.rglob("SKILL.md")):
        partes = p.relative_to(repo).parts
        if any(x.startswith(".") or x == "node_modules" for x in partes) or p.is_symlink():
            continue
        cab = leer(p)[:3000]
        m = re.search(r"^name:\s*(.+)$", cab, re.M)
        nombre = (m.group(1).strip().strip("\"'") if m else p.parent.name)
        encontrados.setdefault(nombre, {"nombre": reservar(nombre), "ruta": reservar("/".join(partes))})
    return list(encontrados.values())


# ---------------------------------------------------------------- privacidad
# Todo texto que viene de un repositorio o que escribe Emi en el tablero pasa por aquí antes de
# publicarse: la Matriz, el panel y el conector son públicos.
# Los formatos están en tools/privacidad.json, el mismo archivo que usa el Worker del panel.
def _cargar_patrones() -> list[tuple[re.Pattern, str]]:
    datos = json.loads((Path(__file__).resolve().parent / "privacidad.json").read_text(encoding="utf-8"))
    return [(re.compile(x["re"], re.I if x.get("i") else 0), x["por"]) for x in datos["patrones"]]


PATRONES_RESERVADOS = _cargar_patrones()
# Nombres de clientes (secreto MATRIZ_RESERVADOS), ya normalizados: minúsculas, sin acentos, un espacio.
TERMINOS_RESERVADOS: set[str] = set()
MAX_PALABRAS_TERMINO = 6
PALABRA = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]+")
MAX_TEXTO = 20000  # nada que publique la Matriz necesita más; acota el costo del filtro


def normalizar_termino(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(PALABRA.findall(t))


def configurar_reservas(terminos: list[str]) -> None:
    TERMINOS_RESERVADOS.clear()
    TERMINOS_RESERVADOS.update(n for n in (normalizar_termino(t) for t in terminos) if n)


def terminos_del_entorno() -> list[str]:
    """Nombres de clientes reservados: vienen del secreto MATRIZ_RESERVADOS (separados por coma o renglón).

    No se guardan en el repositorio, ni en claro ni como huella: escribirlos ahí sería publicarlos.
    """
    crudo = os.environ.get("MATRIZ_RESERVADOS", "")
    return [t.strip() for t in re.split(r"[,\n]", crudo) if t.strip()]


def tapar_terminos(texto: str) -> str:
    """Tapa los nombres reservados por palabras completas, sin importar mayúsculas, acentos ni espacios."""
    if not TERMINOS_RESERVADOS or not texto:
        return texto
    palabras = list(PALABRA.finditer(texto))
    norm = [normalizar_termino(m.group()) for m in palabras]
    tramos, i = [], 0
    while i < len(palabras):
        for n in range(min(MAX_PALABRAS_TERMINO, len(palabras) - i), 0, -1):
            if " ".join(norm[i:i + n]) in TERMINOS_RESERVADOS:
                inicio = palabras[i].start()
                if i > 0 and norm[i - 1] == "grupo":
                    inicio = palabras[i - 1].start()
                tramos.append((inicio, palabras[i + n - 1].end()))
                i += n
                break
        else:
            i += 1
    for x, y in reversed(tramos):
        texto = texto[:x] + "[cliente]" + texto[y:]
    return texto


def reservar(texto: str) -> str:
    """Tapa números de expediente, nombres de clientes, correos, teléfonos, CURP, RFC, montos e IDs de Drive."""
    if not texto:
        return texto
    texto = texto[:MAX_TEXTO]
    for patron, sustituto in PATRONES_RESERVADOS:
        texto = patron.sub(sustituto, texto)
    return tapar_terminos(texto)


# ---------------------------------------------------------------- actividad

ACTORES = [("Claude", r"claude"), ("ChatGPT · Codex", r"codex|chatgpt|openai"), ("Gemini", r"gemini|jules|antigravity"),
           ("Muse", r"\bmuse\b"), ("GitHub Actions", r"github actions|matriz-bot|github-actions"), ("Emi", r"\bemi\b|emiliano")]


def actor(texto: str) -> str:
    t = (texto or "").lower()
    for nombre, patron in ACTORES:
        if re.search(patron, t):
            return nombre
    return "Otra" if t.strip() else "Sin dato"


def lunes(fecha: dt.date) -> dt.date:
    return fecha - dt.timedelta(days=fecha.weekday())


def actividad(carpeta: Path, hoy: dt.date) -> dict:
    """Commits por semana (últimas 8, la más reciente al final) y quién los hizo en 60 días.

    Solo conteos: ningún mensaje de commit se publica.
    """
    semanas = [lunes(hoy) - dt.timedelta(weeks=i) for i in range(SEMANAS - 1, -1, -1)]
    conteo = [0] * SEMANAS
    actores: dict[str, int] = {}
    desde = (hoy - dt.timedelta(days=60)).isoformat()
    salida = git(["log", f"--since={desde}", "--format=%cs%x1f%an%x1f%(trailers:key=IA-Actor,valueonly,separator=%x2C)%x1f%s", "--no-merges"], carpeta)
    for linea in salida.splitlines():
        partes = linea.split("\x1f")
        if len(partes) < 4 or not fecha_valida(partes[0]):
            continue
        f = dt.date.fromisoformat(partes[0])
        sem = lunes(f)
        if sem in semanas:
            conteo[semanas.index(sem)] += 1
        quien = actor(partes[2]) if partes[2].strip() else actor(partes[1] + " " + partes[3])
        if quien == "Sin dato":
            quien = "Otra"
        actores[quien] = actores.get(quien, 0) + 1
    return {"semanas": [s.isoformat() for s in semanas], "commits": conteo, "actores_60d": actores}


# ---------------------------------------------------------------- lectura de repositorios

def leer_repo(nombre: str, carpeta: Path | None, privado: bool, detalle: bool, propietario: str,
              hoy: dt.date | None = None) -> dict:
    d: dict = {
        "nombre": nombre,
        "url": f"https://github.com/{propietario}/{nombre}",
        "visibilidad": "privado" if privado else "público",
        "leido": bool(carpeta),
        "ultimo_cambio": "",
        "resumen": "",
        "skills": [],
        "protocolo": "",
        "registro": [],
        "actividad": {},
    }
    if not carpeta:
        return d
    d["ultimo_cambio"] = git(["log", "-1", "--format=%cs"], carpeta)
    d["actividad"] = actividad(carpeta, hoy or dt.date.today())
    if privado and not detalle:
        return d
    d["resumen"] = reservar(resumen_readme(leer(carpeta / "README.md")))
    d["skills"] = skills(carpeta)
    m = re.search(r"(\d+\.\d+\.\d+)", leer(carpeta / "ia" / "PROTOCOLO.md")[:200])
    d["protocolo"] = m.group(1) if m else ""
    d["registro"] = [{"fecha": e["fecha"], "titulo": reservar(e["titulo"]), "agente": reservar(e["agente"]),
                      "pendiente": reservar(pendiente_real(e["pendiente"]))}
                     for e in entradas_changelog(leer(carpeta / "CHANGELOG.md"))]
    return d


def localizar(nombre: str, repos_dir: Path | None, clonar: bool, propietario: str, tmp: Path) -> Path | None:
    if repos_dir:
        for cand in (repos_dir / nombre, repos_dir / nombre.lower()):
            if (cand / ".git").exists():
                return cand
    if not clonar:
        return None
    token = os.environ.get("MATRIZ_TOKEN", "").strip()
    auth = f"x-access-token:{token}@" if token else ""
    destino = tmp / nombre
    # cwd fuera de este repositorio: actions/checkout deja en su configuración local una cabecera
    # con el token del workflow, que git aplicaría también a este clone y taparía MATRIZ_TOKEN.
    r = subprocess.run(
        ["git", "-c", "http.https://github.com/.extraheader=", "clone", "--quiet", "--shallow-since=75 days ago",
         "--single-branch", f"https://{auth}github.com/{propietario}/{nombre}", str(destino)],
        capture_output=True, text=True, cwd=tmp,
    )
    if r.returncode != 0:  # repositorio sin commits recientes: basta el último
        r = subprocess.run(
            ["git", "-c", "http.https://github.com/.extraheader=", "clone", "--quiet", "--depth", "1",
             f"https://{auth}github.com/{propietario}/{nombre}", str(destino)],
            capture_output=True, text=True, cwd=tmp,
        )
    if r.returncode != 0:
        motivo = (r.stderr.strip().splitlines() or ["sin mensaje"])[-1]
        if token:
            motivo = motivo.replace(token, "***")
        print(f"No se pudo leer {nombre}: {motivo}", file=sys.stderr)
        return None
    return destino


def descubrir(propietario: str) -> dict[str, dict] | None:
    """Todos los repositorios de la cuenta con su visibilidad real según GitHub.

    Sin token ve los públicos; con MATRIZ_TOKEN (acceso «All repositories») también los privados.
    Devuelve None si GitHub no respondió: entonces no se puede confirmar ninguna visibilidad.
    """
    token = os.environ.get("MATRIZ_TOKEN", "").strip()
    urls = [f"https://api.github.com/users/{propietario}/repos?per_page=100&type=owner"]
    if token:
        urls.append("https://api.github.com/user/repos?per_page=100&affiliation=owner")
    vistos: dict[str, dict] = {}
    respondio = False
    for base_url in urls:
        for pagina in range(1, 11):  # hasta 1000 repositorios
            url = f"{base_url}&page={pagina}"
            req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "matriz"})
            if token and "/user/" in url:
                req.add_header("Authorization", f"Bearer {token}")
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    lote = json.load(r)
            except Exception as e:  # sin red o sin permiso: no bloquea la generación
                print(f"No se pudo listar repositorios ({url.split('?')[0]}): {e}", file=sys.stderr)
                break
            respondio = True
            for x in lote:
                if x.get("owner", {}).get("login", "").lower() == propietario.lower() and not x.get("archived"):
                    vistos[x["name"]] = {"nombre": x["name"], "visibilidad": "privado" if x.get("private") else "público",
                                         "creado": (x.get("created_at") or "")[:10]}
            if len(lote) < 100:
                break
    return vistos if respondio else None


# ---------------------------------------------------------------- tablero y proyectos (los escribe Emi)

TAREA = re.compile(r"^\s*-\s*\[( |x|X)\]\s+(.*)$")


def leer_tablero(ruta: Path) -> dict:
    """Pendientes y notas de un cerebro (`tablero/<id>.md`, formato de tareas de Obsidian)."""
    pendientes, notas, seccion = [], [], ""
    for linea in leer(ruta).splitlines():
        if linea.startswith("## "):
            seccion = linea[3:].strip().lower()
            continue
        m = TAREA.match(linea)
        if m and seccion.startswith("pendiente"):
            t = m.group(2)
            vence = re.search(r"📅\s*(\d{4}-\d{2}-\d{2})", t)
            hecho = re.search(r"✅\s*(\d{4}-\d{2}-\d{2})", t)
            creado = re.search(r"➕\s*(\d{4}-\d{2}-\d{2})", t)
            ident = re.search(r"\^([a-z0-9]{4,12})\s*$", t)
            texto = re.sub(r"\s*(?:📅|✅|➕)\s*\d{4}-\d{2}-\d{2}|\s*🔺|\s*\^[a-z0-9]{4,12}\s*$", "", t).strip()
            pendientes.append({"id": ident.group(1) if ident else "", "texto": reservar(texto), "hecho": m.group(1) != " ",
                               "alta": "🔺" in t, "vence": vence.group(1) if vence else "",
                               "hecho_el": hecho.group(1) if hecho else "", "creado": creado.group(1) if creado else ""})
        elif seccion.startswith("nota") and linea.strip().startswith("- "):
            t = linea.strip()[2:]
            f = re.match(r"(\d{4}-\d{2}-\d{2})\s*·\s*(.*)", t)
            ident = re.search(r"\^([a-z0-9]{4,12})\s*$", t)
            cuerpo = re.sub(r"\s*\^[a-z0-9]{4,12}\s*$", "", f.group(2) if f else t)
            notas.append({"id": ident.group(1) if ident else "", "fecha": f.group(1) if f else "", "texto": reservar(cuerpo)})
    return {"pendientes": pendientes, "notas": notas}


def leer_proyectos(carpeta: Path) -> list[dict]:
    salida = []
    for p in sorted(carpeta.glob("*.md")):
        texto = leer(p)
        fm = re.match(r"^---\n(.*?)\n---", texto, re.S)
        props = {}
        for k, v in re.findall(r"^(\w+):[ \t]*(.*?)[ \t]*$", fm.group(1) if fm else "", re.M):
            if v.startswith('"'):
                try:
                    v = json.loads(v)  # el panel escribe los valores como JSON
                except ValueError:
                    v = v.strip('"')
            props[k] = str(v)
        if props.get("tipo") != "proyecto":
            continue
        salida.append({"archivo": p.name, "nombre": reservar(props.get("nombre", p.stem)), "cerebro": props.get("cerebro", ""),
                       "estado": props.get("estado", "idea"), "fecha": props.get("fecha", ""),
                       "descripcion": reservar(props.get("descripcion", ""))})
    return salida


# ---------------------------------------------------------------- métricas

def metricas(cerebros: list[dict], por_cerebro: dict, tableros: dict, inv: dict, hoy: dt.date) -> dict:
    """Lo que sirve para decidir: dónde hay movimiento, qué está quieto, qué urge y quién trabaja."""
    salida_c = {}
    actores_total: dict[str, int] = {}
    semanas_total = [0] * SEMANAS
    for c in cerebros:
        rs = por_cerebro[c["id"]]
        semanas = [0] * SEMANAS
        for r in rs:
            for i, n in enumerate(r.get("actividad", {}).get("commits", [])[:SEMANAS]):
                semanas[i] += n
            for a, n in r.get("actividad", {}).get("actores_60d", {}).items():
                actores_total[a] = actores_total.get(a, 0) + n
        semanas_total = [x + y for x, y in zip(semanas_total, semanas)]
        ult = max((r["ultimo_cambio"] for r in rs if fecha_valida(r["ultimo_cambio"])), default="")
        quieto = (hoy - dt.date.fromisoformat(ult)).days if ult else None
        tab = tableros.get(c["id"], {"pendientes": [], "notas": []})
        abiertos = [p for p in tab["pendientes"] if not p["hecho"]]
        vencidos = [p for p in abiertos if p["vence"] and p["vence"] < hoy.isoformat()]
        salida_c[c["id"]] = {
            "semanas": semanas, "esta_semana": semanas[-1], "semana_pasada": semanas[-2] if SEMANAS > 1 else 0,
            "dias_sin_movimiento": quieto, "pendientes_abiertos": len(abiertos), "pendientes_vencidos": len(vencidos),
            "pendientes_de_repos": sum(1 for r in rs if r["registro"] and r["registro"][0]["pendiente"]),
            "tareas_falladas": sum(1 for t in inv.get("tareas", []) if t.get("cerebro") == c["id"]
                                   and str(t.get("resultado", "")).startswith("falló")),
        }
    venc = []
    for v in inv.get("vencimientos", []):
        if fecha_valida(v.get("fecha", "")):
            venc.append({**v, "dias": (dt.date.fromisoformat(v["fecha"][:10]) - hoy).days})
    venc.sort(key=lambda v: v["dias"])
    sem_lunes = [(lunes(hoy) - dt.timedelta(weeks=i)).isoformat() for i in range(SEMANAS - 1, -1, -1)]
    return {"cerebros": salida_c, "semanas": sem_lunes, "commits_por_semana": semanas_total,
            "actores_60d": dict(sorted(actores_total.items(), key=lambda x: -x[1])), "vencimientos": venc}


# ---------------------------------------------------------------- escritura

def yaml(campos: dict) -> str:
    """Propiedades de Obsidian (frontmatter YAML). Las cadenas van como JSON, que YAML acepta."""
    L = ["---"]
    for k, v in {**campos, "generado": GENERADO}.items():
        if v in ("", None, []):
            continue
        if isinstance(v, list):
            L.append(f"{k}:")
            L += [f"  - {json.dumps(x, ensure_ascii=False)}" for x in v]
        elif isinstance(v, (int, float)) or (k in ("ultimo_cambio", "actualizada") and fecha_valida(str(v))):
            L.append(f"{k}: {v}")
        else:
            L.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    return "\n".join(L + ["---", ""])


def pendiente_real(texto: str) -> str:
    t = (texto or "").strip()
    return "" if t.lower().rstrip(".") in ("", "ninguno", "ninguna", "no", "sin pendientes", "n/a", "—", "-") else t


def tareas_de(inv: dict, cid: str) -> list[dict]:
    return [t for t in inv.get("tareas", []) if t.get("cerebro") == cid]


def skills_de(inv: dict, cid: str) -> list[dict]:
    return [k for k in inv.get("skills_instaladas", []) if k.get("cerebro") == cid]


def linea_tarea(t: dict) -> str:
    s = f"{t['nombre']} · {t.get('horario', 'sin horario')}"
    if t.get("estado", "activa") != "activa":
        s += f" · {t['estado']}"
    if t.get("ultima_corrida"):
        s += f" · última: {fecha_corta(t['ultima_corrida'])}" + (f", {t['resultado']}" if t.get("resultado") else "")
    return s


def slug(nombre: str) -> str:
    """Nombre de nota seguro para Obsidian: sin punto ni guion finales."""
    return nombre.rstrip(".-") or nombre


def bloque_inventario(inv: dict, cid: str, enlazar: bool, conocidos: set[str]) -> list[str]:
    L = []
    ts, ks = tareas_de(inv, cid), skills_de(inv, cid)
    if ts:
        L.append("## Tareas programadas\n")
        L += [f"- {linea_tarea(t)}" + (f" · repo `{t['repo']}`" if t.get("repo") else "") for t in ts]
        L.append("")
    if ks:
        L.append("## Skills instaladas en Claude\n")
        for k in ks:
            repo = k.get("repo", "")
            if repo and enlazar and repo in conocidos:
                destino = f"[[{slug(repo)}|{repo}]]"
            elif repo:
                destino = f"`{repo}`"
            else:
                destino = "sin repositorio"
            L.append(f"- `{k['nombre']}` · {destino}")
        L.append("")
    return L


def bloque_tablero(tab: dict) -> list[str]:
    L = []
    abiertos = [p for p in tab.get("pendientes", []) if not p["hecho"]]
    if abiertos:
        L.append("## Pendientes de Emi\n")
        for p in sorted(abiertos, key=lambda p: (not p["alta"], p["vence"] or "9999")):
            L.append(f"- {'(alta) ' if p['alta'] else ''}{p['texto']}" + (f" · vence {fecha_corta(p['vence'])}" if p["vence"] else ""))
        L.append("")
    if tab.get("notas"):
        L.append("## Notas de Emi\n")
        L += [f"- {fecha_corta(n['fecha'])} · {n['texto']}" if n["fecha"] else f"- {n['texto']}" for n in tab["notas"][-10:]]
        L.append("")
    return L


def nota_repo(r: dict, cerebro: dict) -> str:
    ult = r["registro"][0] if r["registro"] else {}
    props = {
        "tipo": "repo",
        "cerebro": cerebro["nombre"],
        "visibilidad": r["visibilidad"],
        "ultimo_cambio": r["ultimo_cambio"],
        "skills": len(r["skills"]) if r["leido"] and not (r["visibilidad"] == "privado" and not r["resumen"]) else "",
        "commits_8_semanas": sum(r.get("actividad", {}).get("commits", [])) or "",
        "ultimo_agente": ult.get("agente", ""),
        "pendiente": ult.get("pendiente", ""),
        "github": r["url"],
        "tags": ["repo", "publico" if r["visibilidad"] == "público" else "privado"],
    }
    L = [yaml(props), f"# {r['nombre']}\n",
         f"Cerebro: [[{cerebro['nombre']}]] · {r['visibilidad']} · último cambio: {fecha_corta(r['ultimo_cambio'])}\n",
         f"[Abrir en GitHub]({r['url']})\n"]
    if r.get("lectura") == "anterior":
        L.append("No se pudo leer en la última corrida: se muestran los datos de la lectura anterior.\n")
    elif not r["leido"]:
        L.append("Sin lectura en esta corrida (falta acceso o el token de la Matriz).\n")
    elif r["visibilidad"] == "privado" and not r["resumen"]:
        L.append("Repositorio privado: aquí solo se publica su nombre, su fecha y su actividad.\n")
    if r["resumen"]:
        L.append(r["resumen"] + "\n")
    if r["skills"]:
        L.append("## Skills\n")
        L += [f"- `{s['nombre']}` · `{s['ruta']}`" for s in r["skills"]]
        L.append("")
    if r["registro"]:
        L.append("## Últimos registros\n")
        for e in r["registro"][:5]:
            L.append(f"- {fecha_corta(e['fecha'])} · {e['titulo']} · Agente: {e['agente'] or 'no consta'}")
        if r["registro"][0]["pendiente"]:
            L.append(f"\n## Pendiente más reciente\n\n{r['registro'][0]['pendiente']}")
        L.append("")
    return "\n".join(L).rstrip() + "\n"


def nota_cerebro(c: dict, repos: list[dict], inv: dict, tab: dict, conocidos: set[str]) -> str:
    props = {"tipo": "cerebro", "repos": len(repos),
             "ultimo_cambio": max((r["ultimo_cambio"] for r in repos if fecha_valida(r["ultimo_cambio"])), default=""),
             "pendientes": sum(1 for p in tab.get("pendientes", []) if not p["hecho"]) or "", "tags": ["cerebro"]}
    L = [yaml(props), f"# {c['nombre']}\n", c["descripcion"] + "\n", "Parte de la [[MATRIZ]].\n"]
    L += bloque_tablero(tab)
    L.append("## Repositorios\n")
    for r in repos:
        extra = f" · {len(r['skills'])} skill(s)" if r["skills"] else ""
        L.append(f"- [[{slug(r['nombre'])}|{r['nombre']}]] · {r['visibilidad']} · {fecha_corta(r['ultimo_cambio'])}{extra}")
    L.append("")
    L += bloque_inventario(inv, c["id"], True, conocidos)
    L.append(f"Tablero editable: `tablero/{c['id']}.md` (o desde el panel). Para otra IA: [[{c['id']}.CONTEXTO|archivo de contexto]].")
    return "\n".join(L) + "\n"


REGLAS_IA = [
    "1. La fuente de verdad es GitHub (`lianfixx`), no esta conversación ni lo que recuerdes.",
    "2. Antes de cambiar un repositorio, lee su `AGENTS.md`, `ia/REGLAS.md` e `ia/PROTOCOLO.md`.",
    "3. Todo cambio se registra en el mismo commit, en `CHANGELOG.md`, con la línea `Agente:`.",
    "4. Si no puedes escribir en el repositorio, termina con un bloque «Registro pendiente para el repositorio» "
    "con la entrada completa y los cambios exactos. No digas «guardado» si no escribiste.",
    "5. No envíes correos, no publiques, no contrates ni cambies reglas sin confirmación expresa de Emi.",
    "6. Nada de datos de clientes (nombres, expedientes, montos) en repositorios públicos ni en la Matriz.",
]


def contexto(c: dict, repos: list[dict], propietario: str, inv: dict, tab: dict) -> str:
    L = [yaml({"tipo": "contexto", "cerebro": c["nombre"]}), f"# Contexto para cualquier IA · {c['nombre']}\n",
         f"Soy Emi (Yohualli Emiliano García Milla). Este es el cerebro «{c['nombre']}» de mi Matriz General "
         f"(https://github.com/{propietario}/MATRIZ · {PANEL}). {c['descripcion']}\n",
         "## Cómo trabajar\n", *REGLAS_IA, ""]
    L += bloque_tablero(tab)
    L.append("## Repositorios de este cerebro\n")
    for r in repos:
        L.append(f"### {r['nombre']} ({r['visibilidad']})\n")
        L.append(f"{r['url']} · último cambio: {fecha_corta(r['ultimo_cambio'])}\n")
        if r["resumen"]:
            L.append(r["resumen"] + "\n")
        if r["skills"]:
            L.append("Skills: " + ", ".join(f"`{s['nombre']}`" for s in r["skills"]) + "\n")
        if r["registro"]:
            e = r["registro"][0]
            L.append(f"Último registro: {fecha_corta(e['fecha'])} · {e['titulo']} · Agente: {e['agente'] or 'no consta'}")
            if e["pendiente"]:
                L.append(f"Pendiente: {e['pendiente']}")
            L.append("")
        if r["visibilidad"] == "privado" and not r["resumen"]:
            L.append("Privado: pide acceso a Emi o usa un conector de GitHub con su sesión.\n")
    L += bloque_inventario(inv, c["id"], False, set())
    return "\n".join(L).rstrip() + "\n"


def portada(cerebros: list[dict], por_cerebro: dict, hoy: str, inv: dict, nuevos: list[dict], met: dict) -> str:
    todos = [r for c in cerebros for r in por_cerebro[c["id"]]]
    recientes = sorted(((e["fecha"], r["nombre"], e) for r in todos for e in r["registro"][:3]),
                       key=lambda x: x[0], reverse=True)[:10]
    L = [yaml({"tipo": "matriz", "actualizada": hoy, "tags": ["matriz"]}), "# Matriz General\n",
         f"{len(todos)} repositorios en {len(cerebros)} cerebros · actualizada el {fecha_corta(hoy)}.\n",
         f"Para una IA: el archivo único es [MATRIZ_GENERAL.md](MATRIZ_GENERAL.md). Panel: {PANEL}\n",
         "## Cerebros\n", "| Cerebro | Repos | Esta semana | Sin movimiento | Pendientes | Qué es |", "|---|---|---|---|---|---|"]
    for c in cerebros:
        rs, m = por_cerebro[c["id"]], met["cerebros"][c["id"]]
        quieto = f"{m['dias_sin_movimiento']} días" if m["dias_sin_movimiento"] is not None else "sin dato"
        L.append(f"| [[{c['nombre']}]] | {len(rs)} | {m['esta_semana']} commits | {quieto} | {m['pendientes_abiertos']} | {c['descripcion']} |")
    L.append("\n## Lo último que se hizo\n")
    for f, nombre, e in recientes:
        L.append(f"- {fecha_corta(f)} · **{nombre}** · {e['titulo']} · Agente: {e['agente'] or 'no consta'}")
    if not recientes:
        L.append("Sin registros leídos todavía.")
    sin = [r["nombre"] for r in todos if not r["leido"]]
    if sin:
        L.append("\n## Sin lectura en esta corrida\n")
        L.append(", ".join(f"`{n}`" for n in sin) + ". Falta acceso o el secreto `MATRIZ_TOKEN`.")
    if nuevos:
        L.append("\n## Repositorios nuevos por clasificar\n")
        L += [f"- `{n['nombre']}` · {n['visibilidad']}" + (f" · creado el {fecha_corta(n['creado'])}" if n.get("creado") else "")
              for n in nuevos]
        L.append("\nLa revisión semanal los asigna a su cerebro; si alguno es dudoso, le pregunta a Emi.")
    if met["vencimientos"]:
        L.append("\n## Vencimientos\n")
        L += [f"- {v['nombre']} · {fecha_corta(v['fecha'])} ({cuando(v['dias'])})" for v in met["vencimientos"]]
    tareas, instaladas = inv.get("tareas", []), inv.get("skills_instaladas", [])
    if tareas or instaladas:
        activas = [t for t in tareas if t.get("estado", "activa") == "activa"]
        L.append("\n## Automatizaciones y skills\n")
        L.append(f"{len(activas)} tareas programadas activas y {len(instaladas)} skills instaladas en Claude"
                 + (f" · inventario revisado el {fecha_corta(inv['revisado'])}" if inv.get("revisado") else "") + ".\n")
        fallas = [t for t in tareas if str(t.get("resultado", "")).startswith("falló")]
        if fallas:
            L.append("Fallaron en su última corrida:\n")
            L += [f"- {linea_tarea(t)}" for t in fallas]
            L.append("")
        nombres = {k["nombre"] for k in instaladas}
        sin_repo = [k["nombre"] for k in instaladas if not k.get("repo")]
        sin_instalar = sorted({s["nombre"] for r in todos for s in r["skills"]} - nombres)
        if sin_repo:
            L.append("Skills instaladas sin repositorio: " + ", ".join(f"`{n}`" for n in sin_repo) + ".\n")
        if sin_instalar:
            L.append("Skills en un repositorio pero no instaladas en Claude: " + ", ".join(f"`{n}`" for n in sin_instalar) + ".\n")
    pub = [r["nombre"] for r in todos if r["visibilidad"] == "público"]
    L.append(f"\n## Visibilidad\n\n{len(pub)} públicos y {len(todos) - len(pub)} privados. "
             "Cualquier persona puede leer los públicos.")
    return "\n".join(L) + "\n"


def matriz_general(cfg: dict, por_cerebro: dict, hoy: str, inv: dict, nuevos: list[dict], met: dict,
                   tableros: dict, proyectos: list[dict], emi: str) -> str:
    """El archivo único. Adjuntarlo a cualquier IA basta para que entienda todo y sepa por dónde seguir."""
    cerebros, prop = cfg["cerebros"], cfg["propietario"]
    todos = [r for c in cerebros for r in por_cerebro[c["id"]]]
    L = [f"# Matriz General de Emi · {fecha_corta(hoy)}\n",
         "Este es el archivo único de la Matriz General: el mapa de todo el trabajo de Emi. Si te lo adjuntaron, "
         "con esto basta para entender quién es, dónde trabaja, qué hay en cada cerebro, qué se hizo último, "
         "qué está pendiente y cómo continuar. Todo nace y se registra desde aquí.\n",
         f"- Fuente de verdad: https://github.com/{prop}/MATRIZ (se regenera solo cada día).",
         f"- Panel: {PANEL} · Conector MCP de solo lectura: {PANEL}/mcp",
         f"- {len(todos)} repositorios en {len(cerebros)} cerebros, {len(inv.get('tareas', []))} tareas programadas, "
         f"{len(inv.get('skills_instaladas', []))} skills instaladas.\n",
         "## Cómo trabajar con Emi (cualquier IA)\n", *REGLAS_IA,
         "7. Si Emi te pide algo nuevo, dile en qué cerebro va. Un proyecto nuevo nace en el tablero de la Matriz "
         "(panel → «Nuevo proyecto» o `proyectos/` en el repositorio) y la revisión semanal le crea su repositorio.\n"]
    perfil = re.sub(r"^# .*\n", "", quitar_frontmatter(emi)).strip()
    if perfil:
        L += ["## Quién es Emi\n", re.sub(r"^## ", "### ", perfil, flags=re.M), ""]
    L += ["## Pulso\n", "| Cerebro | Repos | Commits esta semana | Semana pasada | Días sin movimiento | Pendientes | Vencidos |",
          "|---|---|---|---|---|---|---|"]
    for c in cerebros:
        m = met["cerebros"][c["id"]]
        L.append(f"| {c['nombre']} | {len(por_cerebro[c['id']])} | {m['esta_semana']} | {m['semana_pasada']} | "
                 f"{m['dias_sin_movimiento'] if m['dias_sin_movimiento'] is not None else '—'} | {m['pendientes_abiertos']} | {m['pendientes_vencidos']} |")
    if met["actores_60d"]:
        L.append("\nQuién trabajó en los últimos 60 días (commits): " + ", ".join(f"{a} {n}" for a, n in met["actores_60d"].items()) + ".")
    if met["vencimientos"]:
        L.append("\nVencimientos: " + "; ".join(f"{v['nombre']} el {fecha_corta(v['fecha'])}" for v in met["vencimientos"]) + ".")
    fallas = [t for t in inv.get("tareas", []) if str(t.get("resultado", "")).startswith("falló")]
    if fallas or nuevos:
        L.append("\nAvisos: " + "; ".join([f"falló «{t['nombre']}» ({t['resultado']})" for t in fallas]
                                         + [f"repositorio nuevo sin cerebro: {n['nombre']}" for n in nuevos]) + ".")
    L.append("")
    for c in cerebros:
        rs = por_cerebro[c["id"]]
        L += [f"## Cerebro: {c['nombre']}\n", c["descripcion"] + "\n"]
        L += [x.replace("## ", "### ", 1) if x.startswith("## ") else x for x in bloque_tablero(tableros.get(c["id"], {}))]
        L.append("### Repositorios\n")
        for r in rs:
            e = r["registro"][0] if r["registro"] else None
            linea = f"- **{r['nombre']}** ({r['visibilidad']}) · {r['url']} · último cambio {fecha_corta(r['ultimo_cambio'])}"
            if r["skills"]:
                linea += " · skills: " + ", ".join(s["nombre"] for s in r["skills"])
            L.append(linea)
            if r["resumen"]:
                L.append(f"  - {r['resumen']}")
            if e:
                L.append(f"  - Último: {fecha_corta(e['fecha'])} · {e['titulo']} · {e['agente'] or 'agente no consta'}")
                if e["pendiente"]:
                    L.append(f"  - Pendiente: {e['pendiente']}")
        L.append("")
        L += [x.replace("## ", "### ", 1) if x.startswith("## ") else x for x in bloque_inventario(inv, c["id"], False, set())]
    if proyectos:
        L += ["## Proyectos nuevos\n"] + [f"- {p['nombre']} · {p['estado']} · cerebro {p['cerebro']} · {p['descripcion']}" for p in proyectos] + [""]
    propias = [t for t in inv.get("tareas", []) if t.get("cerebro") == "matriz"]
    if propias:
        L += ["## Cómo se mantiene sola\n"] + [f"- {linea_tarea(t)}" for t in propias] + [
            "- Obsidian en la Mac trae los cambios cada 10 minutos; el panel se publica después de cada actualización.", ""]
    L += ["## Conectar otra IA\n",
          f"- Claude y ChatGPT: conector MCP {PANEL}/mcp (solo lectura). Para escribir: Claude Code o Codex sobre GitHub.",
          f"- Gemini, Muse y otras que leen páginas: {PANEL}/llms.txt o este archivo.",
          "- DeepSeek: pega este archivo; nunca datos de clientes.\n"]
    return "\n".join(L).rstrip() + "\n"


def cuando(dias: int) -> str:
    return "vencido" if dias < 0 else "hoy" if dias == 0 else f"en {dias} días"


def quitar_frontmatter(t: str) -> str:
    return re.sub(r"^---\n[\s\S]*?\n---\n", "", t or "")


LINEA_BITACORA = re.compile(r"^- \[\[.+?\]\] · .+")


def bitacoras(todos: list[dict], salida: Path) -> dict[str, str]:
    """Bitácora acumulativa: junta lo leído hoy con lo que ya estaba escrito.

    Solo borra las líneas de repositorios que hoy son privados o ya no están en la Matriz: lo que dejó de
    ser público no se sigue publicando."""
    publicos = {slug(r["nombre"]) for r in todos if r.get("visibilidad") == "público"}
    por_mes: dict[str, dict[str, set]] = {}
    for p in (salida / "bitacora").glob("*.md"):
        mes, dia = p.stem, ""
        por_mes.setdefault(mes, {})  # el mes se reescribe aunque se queden sin líneas
        for linea in leer(p).splitlines():
            m = re.match(r"^## (\d{1,2}) (\w{3}) (\d{4})$", linea)
            if m and m.group(2) in MESES:
                dia = f"{m.group(3)}-{MESES.index(m.group(2)) + 1:02d}-{int(m.group(1)):02d}"
            elif dia and LINEA_BITACORA.match(linea):
                destino = re.match(r"^- \[\[([^|\]]+)", linea)
                if destino and destino.group(1) not in publicos:
                    continue
                por_mes.setdefault(mes, {}).setdefault(dia, set()).add(reservar(linea))
    for r in todos:
        for e in r["registro"]:
            linea = f"- [[{slug(r['nombre'])}|{r['nombre']}]] · {e['titulo']} · Agente: {e['agente'] or 'no consta'}"
            por_mes.setdefault(e["fecha"][:7], {}).setdefault(e["fecha"], set()).add(linea)
    textos = {}
    for mes, dias in por_mes.items():
        if not re.match(r"^\d{4}-\d{2}$", mes):
            continue
        L = [yaml({"tipo": "bitacora"}), f"# Bitácora {MESES[int(mes[5:]) - 1]} {mes[:4]}\n",
             "Lo que registró cada IA en los `CHANGELOG.md` leídos. Acumulativa: cada corrida suma, nunca borra.\n"]
        for dia in sorted(dias, reverse=True):
            L.append(f"\n## {fecha_corta(dia)}\n")
            L += sorted(dias[dia])
        textos[mes] = "\n".join(L) + "\n"
    return textos


def escribir(ruta: Path, texto: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def validar(cfg: dict, inv: dict | None = None) -> list[str]:
    errores, vistos, notas = [], {}, {}
    for c in cfg["cerebros"]:
        notas.setdefault(c["nombre"].lower(), []).append(f"cerebro {c['nombre']}")
        for r in c["repos"]:
            if r in vistos:
                errores.append(f"«{r}» está en dos cerebros: {vistos[r]} y {c['id']}")
            vistos[r] = c["id"]
            notas.setdefault(slug(r).lower(), []).append(f"repositorio {r}")
    errores += [f"Dos notas tendrían el mismo nombre ({', '.join(v)}): Obsidian en la Mac no distingue mayúsculas"
                for v in notas.values() if len(v) > 1]
    errores += [f"«{p}» figura como privado pero no pertenece a ningún cerebro" for p in cfg.get("privados", []) if p not in vistos]
    ids = {c["id"] for c in cfg["cerebros"]} | {"matriz"}
    inv = inv or {}
    for clave in ("tareas", "skills_instaladas"):
        for x in inv.get(clave, []):
            if x.get("cerebro") not in ids:
                errores.append(f"inventario: «{x.get('nombre')}» apunta al cerebro inexistente «{x.get('cerebro')}»")
    for t in inv.get("tareas", []):
        if t.get("ultima_corrida") and not fecha_valida(t["ultima_corrida"]):
            errores.append(f"inventario: «{t['nombre']}» tiene una fecha inválida ({t['ultima_corrida']}); usa AAAA-MM-DD")
    for v in inv.get("vencimientos", []):
        if not fecha_valida(v.get("fecha", "")):
            errores.append(f"inventario: el vencimiento «{v.get('nombre')}» tiene una fecha inválida; usa AAAA-MM-DD")
    if inv.get("revisado") and not fecha_valida(inv["revisado"]):
        errores.append("inventario: «revisado» debe ser AAAA-MM-DD")
    return errores


def inventario_publico(inv: dict) -> dict:
    """Copia del inventario para publicar: textos libres filtrados."""
    copia = json.loads(json.dumps(inv))
    for t in copia.get("tareas", []):
        for k in ("nombre", "resultado", "horario"):
            if t.get(k):
                t[k] = reservar(t[k])
    for v in copia.get("vencimientos", []):
        for k in ("nombre", "nota"):
            if v.get(k):
                v[k] = reservar(v[k])
    return copia


def generar(cfg: dict, salida: Path, repos_dir: Path | None, clonar: bool, hoy: str, inv: dict | None = None,
            api: dict | None = None, previo: dict | None = None, base: Path | None = None) -> dict:
    """Genera todo. `api`: repositorios según GitHub (None si no respondió). `previo`: matriz.json anterior."""
    base = base or salida
    configurar_reservas(cfg.get("terminos_reservados", []) + terminos_del_entorno())
    errores = validar(cfg, inv)
    if errores:
        raise SystemExit("Configuración inválida:\n- " + "\n- ".join(errores))
    inv = inventario_publico(inv or {})
    prop, privados, detalle = cfg["propietario"], set(cfg.get("privados", [])), bool(cfg.get("detalle_privados"))
    hoy_d = dt.date.fromisoformat(hoy)
    anteriores = {r["nombre"]: r for c in (previo or {}).get("cerebros", []) for r in c.get("repos", [])}
    conocidos = {r for c in cfg["cerebros"] for r in c["repos"]}
    visibilidad_previa = {n: r.get("visibilidad") for n, r in anteriores.items()}

    def es_privado(nombre: str) -> bool:
        # Ante la duda, privado: un repositorio que GitHub no confirma como público no publica su contenido.
        if nombre in privados:
            return True
        if api is not None:
            return api.get(nombre, {}).get("visibilidad") != "público"
        # GitHub no respondió (o corrida local): solo es público lo que una corrida anterior confirmó como público.
        return visibilidad_previa.get(nombre) != "público"

    por_cerebro: dict[str, list[dict]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for c in cfg["cerebros"]:
            lista = []
            for n in c["repos"]:
                r = leer_repo(n, localizar(n, repos_dir, clonar, prop, Path(tmp)), es_privado(n), detalle, prop, hoy_d)
                ant = anteriores.get(n)
                if not r["leido"] and ant and (ant.get("leido") or ant.get("lectura") == "anterior"):
                    r = {**ant, "visibilidad": r["visibilidad"], "leido": False, "lectura": "anterior"}
                    if r["visibilidad"] == "privado" and not detalle:
                        r.update(resumen="", skills=[], registro=[], protocolo="")
                    # Lo anterior también pasa por el filtro: las reservas pudieron cambiar desde entonces.
                    r["resumen"] = reservar(r.get("resumen", ""))
                    r["registro"] = [{k: reservar(v) if isinstance(v, str) and k != "fecha" else v for k, v in e.items()}
                                     for e in r.get("registro", [])]
                lista.append(r)
            por_cerebro[c["id"]] = lista
    sin_cerebro = [v for n, v in (api or {}).items() if n not in conocidos and n not in {"MATRIZ", *cfg.get("ignorar", [])}]
    # De los privados no se publica el nombre (puede decir de qué cliente es): solo cuántos hay.
    nuevos = sorted(({**v, "nombre": reservar(v["nombre"])} for v in sin_cerebro if v.get("visibilidad") == "público"),
                    key=lambda v: v["nombre"].lower())
    n_priv = sum(1 for v in sin_cerebro if v.get("visibilidad") != "público")
    if n_priv:
        nuevos.append({"nombre": f"{n_priv} repositorio{'s' if n_priv > 1 else ''} privado{'s' if n_priv > 1 else ''} (nombre reservado)",
                       "visibilidad": "privado", "creado": ""})
    tableros = {c["id"]: leer_tablero(base / "tablero" / f"{c['id']}.md") for c in cfg["cerebros"]}
    proyectos = leer_proyectos(base / "proyectos")
    met = metricas(cfg["cerebros"], por_cerebro, tableros, inv, hoy_d)

    for carpeta in ("cerebros", "repos", "contexto"):
        for viejo in (salida / carpeta).glob("*.md"):
            viejo.unlink()
    todos = []
    for c in cfg["cerebros"]:
        rs = por_cerebro[c["id"]]
        todos += rs
        escribir(salida / "cerebros" / f"{c['nombre']}.md", nota_cerebro(c, rs, inv, tableros[c["id"]], conocidos))
        escribir(salida / "contexto" / f"{c['id']}.CONTEXTO.md", contexto(c, rs, prop, inv, tableros[c["id"]]))
        for r in rs:
            escribir(salida / "repos" / f"{slug(r['nombre'])}.md", nota_repo(r, c))
    for mes, texto in bitacoras(todos, salida).items():
        escribir(salida / "bitacora" / f"{mes}.md", texto)
    escribir(salida / "MATRIZ.md", portada(cfg["cerebros"], por_cerebro, hoy, inv, nuevos, met))
    emi = leer(base / "EMI.md")
    escribir(salida / "MATRIZ_GENERAL.md", matriz_general(cfg, por_cerebro, hoy, inv, nuevos, met, tableros, proyectos, emi))
    datos = {"actualizada": hoy, "propietario": prop, "panel": PANEL,
             "cerebros": [{"id": c["id"], "nombre": c["nombre"], "descripcion": c["descripcion"],
                           "repos": por_cerebro[c["id"]], "tablero": tableros[c["id"]]} for c in cfg["cerebros"]],
             "inventario": inv, "por_clasificar": nuevos, "proyectos": proyectos, "metricas": met}
    escribir(salida / "matriz.json", json.dumps(datos, ensure_ascii=False, indent=2) + "\n")
    return datos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repos-dir", type=Path, help="carpeta con los clones locales")
    ap.add_argument("--clonar", action="store_true", help="clonar los repositorios que falten")
    ap.add_argument("--salida", type=Path, default=RAIZ)
    ap.add_argument("--hoy", default=os.environ.get("MATRIZ_HOY", ""))
    a = ap.parse_args()
    tk = os.environ.get("MATRIZ_TOKEN", "")
    if a.clonar:
        forma = "ausente" if not tk else ("grano fino" if tk.strip().startswith("github_pat_") else "formato no reconocido")
        print(f"MATRIZ_TOKEN: {forma}, {len(tk.strip())} caracteres" + (", traía espacios" if tk != tk.strip() else ""))
        print(f"Nombres reservados en el secreto MATRIZ_RESERVADOS: {len(terminos_del_entorno())}")
        if os.environ.get("GITHUB_ACTIONS") and not terminos_del_entorno():
            # Falla cerrada: sin la lista de clientes no se publica nada nuevo.
            print("Falta el secreto MATRIZ_RESERVADOS: no se genera para no publicar nombres de clientes.", file=sys.stderr)
            return 1
    hoy = a.hoy or dt.date.today().isoformat()
    cfg = json.loads((RAIZ / "matriz.config.json").read_text(encoding="utf-8"))
    ruta_inv = RAIZ / "inventario.json"
    inv = json.loads(ruta_inv.read_text(encoding="utf-8")) if ruta_inv.exists() else {}
    ruta_prev = a.salida / "matriz.json"
    previo = json.loads(ruta_prev.read_text(encoding="utf-8")) if ruta_prev.exists() else {}
    api = descubrir(cfg["propietario"]) if a.clonar else None
    datos = generar(cfg, a.salida, a.repos_dir, a.clonar, hoy, inv, api, previo, RAIZ)
    todos = [r for c in datos["cerebros"] for r in c["repos"]]
    print(f"Matriz generada: {len(datos['cerebros'])} cerebros, {len(todos)} repositorios, "
          f"{sum(r['leido'] for r in todos)} leídos, {sum(1 for r in todos if r.get('lectura') == 'anterior')} con datos anteriores.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
