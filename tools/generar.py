#!/usr/bin/env python3
"""Genera la Matriz General a partir de los repositorios de Emi.

Lee `matriz.config.json` (cerebros y sus repositorios), abre cada repositorio y escribe:

  MATRIZ.md                  portada
  matriz.json                los mismos datos, para el panel y el conector
  cerebros/<Nombre>.md       una nota por cerebro
  repos/<nombre>.md          una nota por repositorio (nodos del grafo en Obsidian)
  contexto/<id>.CONTEXTO.md  un archivo por cerebro para pegar en cualquier IA
  bitacora/AAAA-MM.md        qué IA hizo qué, por día, en todos los repositorios

También lee `inventario.json` (tareas programadas y skills instaladas en Claude), que mantiene la
revisión semanal, y lo muestra en la portada, en cada cerebro y en los archivos de contexto.

Uso:
  python3 tools/generar.py --repos-dir <carpeta con los clones>   # usa clones locales
  python3 tools/generar.py --clonar                               # clona lo que falte (GitHub Actions)

Solo biblioteca estándar. No escribe en ningún otro repositorio. De los repositorios privados
publica únicamente nombre, cerebro y fecha, salvo que `detalle_privados` sea true en la
configuración: este repositorio es público.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
ENTRADA = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*[·\-–—:]?\s*(.*)$")
GENERADO = "tools/generar.py · no editar a mano: se reescribe cada día"


def fecha_corta(iso: str) -> str:
    if not iso:
        return "sin dato"
    a, m, d = iso.split("-")
    return f"{int(d)} {MESES[int(m) - 1]} {a}"


def git(args: list[str], cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def leer(p: Path) -> str:
    try:
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
    m = re.search(rf"^\s*[-*]\s*{nombre}:\s*(.+)$", cuerpo, re.M)
    return m.group(1).strip() if m else ""


def entradas_changelog(texto: str, maximo: int = 8) -> list[dict]:
    """Entradas `## AAAA-MM-DD · título` con sus campos Agente, Cambios y Pendiente."""
    salida: list[dict] = []
    actual: dict | None = None
    cuerpo: list[str] = []

    def cerrar() -> None:
        if actual is not None:
            c = "\n".join(cuerpo)
            actual["agente"] = campo(c, "Agente")
            actual["cambios"] = campo(c, "Cambios")
            actual["pendiente"] = campo(c, "Pendiente")
            salida.append(actual)

    for linea in texto.splitlines():
        m = ENTRADA.match(linea)
        if m:
            cerrar()
            if len(salida) >= maximo:
                actual = None
                break
            actual = {"fecha": m.group(1), "titulo": m.group(2).strip()}
            cuerpo = []
        elif actual is not None:
            cuerpo.append(linea)
    else:
        cerrar()
    return salida[:maximo]


def skills(repo: Path) -> list[dict]:
    """SKILL.md propios del repositorio (se omiten los puentes .claude/ y .agents/)."""
    encontrados: dict[str, dict] = {}
    for p in sorted(repo.rglob("SKILL.md")):
        partes = p.relative_to(repo).parts
        if any(x.startswith(".") or x == "node_modules" for x in partes):
            continue
        cab = leer(p)[:3000]
        m = re.search(r"^name:\s*(.+)$", cab, re.M)
        nombre = (m.group(1).strip().strip("\"'") if m else p.parent.name)
        encontrados.setdefault(nombre, {"nombre": nombre, "ruta": "/".join(partes)})
    return list(encontrados.values())


def leer_repo(nombre: str, carpeta: Path | None, privado: bool, detalle: bool, propietario: str) -> dict:
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
    }
    if not carpeta:
        return d
    d["ultimo_cambio"] = git(["log", "-1", "--format=%cs"], carpeta)
    if privado and not detalle:
        return d
    d["resumen"] = resumen_readme(leer(carpeta / "README.md"))
    d["skills"] = skills(carpeta)
    m = re.search(r"(\d+\.\d+\.\d+)", leer(carpeta / "ia" / "PROTOCOLO.md")[:200])
    d["protocolo"] = m.group(1) if m else ""
    d["registro"] = entradas_changelog(leer(carpeta / "CHANGELOG.md"))
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


# ---------------------------------------------------------------- escritura

def descubrir(propietario: str, conocidos: set[str]) -> list[dict]:
    """Repositorios de la cuenta que todavía no están en ningún cerebro.

    Sin token ve los públicos; con MATRIZ_TOKEN (si su acceso es «All repositories») también los
    privados nuevos. La revisión semanal los clasifica; aquí solo se avisan. Si GitHub no responde,
    devuelve una lista vacía y la Matriz se genera igual.
    """
    token = os.environ.get("MATRIZ_TOKEN", "").strip()
    urls = [f"https://api.github.com/users/{propietario}/repos?per_page=100&type=owner"]
    if token:
        urls.append("https://api.github.com/user/repos?per_page=100&affiliation=owner")
    vistos: dict[str, dict] = {}
    for url in urls:
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "matriz"})
        if token and "/user/" in url:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                for x in json.load(r):
                    if x.get("owner", {}).get("login", "").lower() == propietario.lower() and not x.get("archived"):
                        vistos[x["name"]] = {"nombre": x["name"], "visibilidad": "privado" if x.get("private") else "público",
                                             "creado": (x.get("created_at") or "")[:10]}
        except Exception as e:  # sin red o sin permiso: no bloquea la generación
            print(f"No se pudo listar repositorios ({url.split('?')[0]}): {e}", file=sys.stderr)
    return sorted((v for n, v in vistos.items() if n not in conocidos), key=lambda v: v["nombre"].lower())


def yaml(campos: dict) -> str:
    """Propiedades de Obsidian (frontmatter YAML). Las cadenas van como JSON, que YAML acepta."""
    L = ["---"]
    for k, v in {**campos, "generado": GENERADO}.items():
        if v in ("", None, []):
            continue
        if isinstance(v, list):
            L.append(f"{k}:")
            L += [f"  - {json.dumps(x, ensure_ascii=False)}" for x in v]
        elif isinstance(v, (int, float)) or (k == "ultimo_cambio" or k == "actualizada"):
            L.append(f"{k}: {v}")
        else:
            L.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    return "\n".join(L + ["---", ""])


def pendiente_real(texto: str) -> str:
    t = (texto or "").strip()
    return "" if t.lower().rstrip(".") in ("", "ninguno", "ninguna", "no", "sin pendientes") else t


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


def bloque_inventario(inv: dict, cid: str, enlazar: bool) -> list[str]:
    L = []
    ts, ks = tareas_de(inv, cid), skills_de(inv, cid)
    if ts:
        L.append("## Tareas programadas\n")
        L += [f"- {linea_tarea(t)}" + (f" · repo `{t['repo']}`" if t.get("repo") else "") for t in ts]
        L.append("")
    if ks:
        L.append("## Skills instaladas en Claude\n")
        for k in ks:
            if k.get("repo"):
                destino = f"[[{slug(k['repo'])}|{k['repo']}]]" if enlazar else f"`{k['repo']}`"
            else:
                destino = "sin repositorio"
            L.append(f"- `{k['nombre']}` · {destino}")
        L.append("")
    return L


def slug(nombre: str) -> str:
    """Nombre de nota seguro para Obsidian: sin punto ni guion finales."""
    return nombre.rstrip(".-") or nombre


def nota_repo(r: dict, cerebro: dict) -> str:
    ult = r["registro"][0] if r["registro"] else {}
    props = {
        "tipo": "repo",
        "cerebro": cerebro["nombre"],
        "visibilidad": r["visibilidad"],
        "ultimo_cambio": r["ultimo_cambio"],
        "skills": len(r["skills"]) if r["leido"] and not (r["visibilidad"] == "privado" and not r["resumen"]) else "",
        "ultimo_agente": ult.get("agente", ""),
        "pendiente": pendiente_real(ult.get("pendiente", "")),
        "github": r["url"],
        "tags": ["repo", "publico" if r["visibilidad"] == "público" else "privado"],
    }
    L = [yaml(props) , f"# {r['nombre']}\n",
         f"Cerebro: [[{cerebro['nombre']}]] · {r['visibilidad']} · último cambio: {fecha_corta(r['ultimo_cambio'])}\n",
         f"[Abrir en GitHub]({r['url']})\n"]
    if not r["leido"]:
        L.append("Sin lectura en esta corrida (falta acceso o el token de la Matriz).\n")
    elif r["visibilidad"] == "privado" and not r["resumen"]:
        L.append("Repositorio privado: aquí solo se publica su nombre y su fecha.\n")
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
        pend = pendiente_real(r["registro"][0]["pendiente"])
        if pend:
            L.append(f"\n## Pendiente más reciente\n\n{pend}")
        L.append("")
    return "\n".join(L).rstrip() + "\n"


def nota_cerebro(c: dict, repos: list[dict], inv: dict | None = None) -> str:
    props = {"tipo": "cerebro", "repos": len(repos),
             "ultimo_cambio": max((r["ultimo_cambio"] for r in repos), default=""), "tags": ["cerebro"]}
    L = [yaml(props) , f"# {c['nombre']}\n", c["descripcion"] + "\n", "Parte de la [[MATRIZ]].\n", "## Repositorios\n"]
    for r in repos:
        extra = f" · {len(r['skills'])} skill(s)" if r["skills"] else ""
        L.append(f"- [[{slug(r['nombre'])}|{r['nombre']}]] · {r['visibilidad']} · {fecha_corta(r['ultimo_cambio'])}{extra}")
    L.append("")
    L += bloque_inventario(inv or {}, c["id"], enlazar=True)
    L.append(f"Para continuar con otra IA: [[{c['id']}.CONTEXTO|archivo de contexto]].")
    return "\n".join(L) + "\n"


def contexto(c: dict, repos: list[dict], propietario: str, inv: dict | None = None) -> str:
    L = [yaml({"tipo": "contexto", "cerebro": c["nombre"]}), f"# Contexto para cualquier IA · {c['nombre']}\n",
         f"Soy Emi (Yohualli Emiliano García Milla). Este es el cerebro «{c['nombre']}» de mi Matriz General "
         f"(https://github.com/{propietario}/MATRIZ). {c['descripcion']}\n",
         "## Cómo trabajar\n",
         "1. La fuente de verdad es el repositorio en GitHub, no esta conversación ni lo que recuerdes.",
         "2. Antes de cambiar algo en un repositorio, lee su `AGENTS.md`, `ia/REGLAS.md` e `ia/PROTOCOLO.md`.",
         "3. Todo cambio se registra en el mismo commit, en `CHANGELOG.md`, con la línea `Agente:`.",
         "4. Si no puedes escribir en el repositorio, termina con un bloque «Registro pendiente para el "
         "repositorio» con la entrada completa y los cambios exactos. No digas «guardado» si no escribiste.",
         "5. No envíes correos, no publiques ni cambies reglas sin mi confirmación expresa.\n",
         "## Repositorios de este cerebro\n"]
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
            L.append("Privado: pide acceso a Emi o usa un conector con sesión iniciada.\n")
    L += bloque_inventario(inv or {}, c["id"], enlazar=False)
    return "\n".join(L).rstrip() + "\n"


def portada(cerebros: list[dict], por_cerebro: dict, hoy: str, inv: dict | None = None,
            nuevos: list[dict] | None = None) -> str:
    inv = inv or {}
    todos = [r for c in cerebros for r in por_cerebro[c["id"]]]
    recientes = sorted(
        ((e["fecha"], r["nombre"], e) for r in todos for e in r["registro"][:3]),
        key=lambda x: x[0], reverse=True)[:10]
    L = [yaml({"tipo": "matriz", "actualizada": hoy, "tags": ["matriz"]}) , "# Matriz General\n",
         f"{len(todos)} repositorios en {len(cerebros)} cerebros · actualizada el {fecha_corta(hoy)}.\n",
         "Si eres una IA: lee [AGENTS.md](AGENTS.md) y luego el archivo de `contexto/` del cerebro en el que vas a trabajar.\n",
         "## Cerebros\n", "| Cerebro | Repos | Último movimiento | Qué es |", "|---|---|---|---|"]
    for c in cerebros:
        rs = por_cerebro[c["id"]]
        ult = max((r["ultimo_cambio"] for r in rs), default="")
        L.append(f"| [[{c['nombre']}]] | {len(rs)} | {fecha_corta(ult)} | {c['descripcion']} |")
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
        propias = [t for t in tareas if t.get("cerebro") == "matriz"]
        if propias:
            L.append("De la Matriz misma:\n")
            L += [f"- {linea_tarea(t)}" for t in propias]
            L.append("")
        nombres = {k["nombre"] for k in instaladas}
        sin_repo = [k["nombre"] for k in instaladas if not k.get("repo")]
        sin_instalar = sorted({s["nombre"] for r in todos for s in r["skills"]} - nombres)
        if sin_repo:
            L.append("Skills instaladas sin repositorio (sin respaldo ni historial en GitHub): "
                     + ", ".join(f"`{n}`" for n in sin_repo) + ".\n")
        if sin_instalar:
            L.append("Skills que están en un repositorio pero no instaladas en Claude: "
                     + ", ".join(f"`{n}`" for n in sin_instalar) + ".\n")
    pub = [r["nombre"] for r in todos if r["visibilidad"] == "público"]
    L.append(f"\n## Visibilidad\n\n{len(pub)} públicos y {len(todos) - len(pub)} privados. "
             "Cualquier persona puede leer los públicos.")
    return "\n".join(L) + "\n"


def bitacoras(todos: list[dict]) -> dict[str, str]:
    por_mes: dict[str, list] = {}
    for r in todos:
        for e in r["registro"]:
            por_mes.setdefault(e["fecha"][:7], []).append((e["fecha"], r["nombre"], e))
    salida = {}
    for mes, filas in por_mes.items():
        L = [yaml({"tipo": "bitacora"}), f"# Bitácora {MESES[int(mes[5:]) - 1]} {mes[:4]}\n",
             "Lo que registró cada IA en los `CHANGELOG.md` leídos (las entradas más recientes de cada repositorio).\n"]
        dia = ""
        for f, nombre, e in sorted(filas, key=lambda x: (x[0], x[1]), reverse=True):
            if f != dia:
                dia = f
                L.append(f"\n## {fecha_corta(f)}\n")
            L.append(f"- [[{slug(nombre)}|{nombre}]] · {e['titulo']} · Agente: {e['agente'] or 'no consta'}")
        salida[mes] = "\n".join(L) + "\n"
    return salida


def escribir(ruta: Path, texto: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def validar(cfg: dict, inv: dict | None = None) -> list[str]:
    errores, vistos = [], {}
    for c in cfg["cerebros"]:
        for r in c["repos"]:
            if r in vistos:
                errores.append(f"«{r}» está en dos cerebros: {vistos[r]} y {c['id']}")
            vistos[r] = c["id"]
    errores += [f"«{p}» figura como privado pero no pertenece a ningún cerebro" for p in cfg.get("privados", []) if p not in vistos]
    ids = {c["id"] for c in cfg["cerebros"]} | {"matriz"}
    for clave in ("tareas", "skills_instaladas"):
        for x in (inv or {}).get(clave, []):
            if x.get("cerebro") not in ids:
                errores.append(f"inventario: «{x.get('nombre')}» apunta al cerebro inexistente «{x.get('cerebro')}»")
    return errores


def generar(cfg: dict, salida: Path, repos_dir: Path | None, clonar: bool, hoy: str, inv: dict | None = None,
            nuevos: list[dict] | None = None) -> dict:
    inv = inv or {}
    nuevos = nuevos or []
    errores = validar(cfg, inv)
    if errores:
        raise SystemExit("Configuración inválida:\n- " + "\n- ".join(errores))
    prop, privados, detalle = cfg["propietario"], set(cfg.get("privados", [])), bool(cfg.get("detalle_privados"))
    por_cerebro: dict[str, list[dict]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for c in cfg["cerebros"]:
            por_cerebro[c["id"]] = [
                leer_repo(n, localizar(n, repos_dir, clonar, prop, Path(tmp)), n in privados, detalle, prop)
                for n in c["repos"]]
    for carpeta in ("cerebros", "repos", "contexto"):
        for viejo in (salida / carpeta).glob("*.md"):
            viejo.unlink()
    todos = []
    for c in cfg["cerebros"]:
        rs = por_cerebro[c["id"]]
        todos += rs
        escribir(salida / "cerebros" / f"{c['nombre']}.md", nota_cerebro(c, rs, inv))
        escribir(salida / "contexto" / f"{c['id']}.CONTEXTO.md", contexto(c, rs, prop, inv))
        for r in rs:
            escribir(salida / "repos" / f"{slug(r['nombre'])}.md", nota_repo(r, c))
    for mes, texto in bitacoras(todos).items():
        escribir(salida / "bitacora" / f"{mes}.md", texto)
    escribir(salida / "MATRIZ.md", portada(cfg["cerebros"], por_cerebro, hoy, inv, nuevos))
    datos = {"actualizada": hoy, "propietario": prop,
             "cerebros": [{"id": c["id"], "nombre": c["nombre"], "descripcion": c["descripcion"],
                           "repos": por_cerebro[c["id"]]} for c in cfg["cerebros"]],
             "inventario": inv, "por_clasificar": nuevos}
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
    hoy = a.hoy or subprocess.run(["date", "+%F"], capture_output=True, text=True).stdout.strip()
    cfg = json.loads((RAIZ / "matriz.config.json").read_text(encoding="utf-8"))
    ruta_inv = RAIZ / "inventario.json"
    inv = json.loads(ruta_inv.read_text(encoding="utf-8")) if ruta_inv.exists() else {}
    conocidos = {r for c in cfg["cerebros"] for r in c["repos"]} | {"MATRIZ"} | set(cfg.get("ignorar", []))
    nuevos = descubrir(cfg["propietario"], conocidos) if a.clonar else []
    datos = generar(cfg, a.salida, a.repos_dir, a.clonar, hoy, inv, nuevos)
    todos = [r for c in datos["cerebros"] for r in c["repos"]]
    print(f"Matriz generada: {len(datos['cerebros'])} cerebros, {len(todos)} repositorios, "
          f"{sum(r['leido'] for r in todos)} leídos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
