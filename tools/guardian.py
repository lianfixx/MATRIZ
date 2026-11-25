#!/usr/bin/env python3
"""Guardián de la Matriz: auditoría de seguridad y privacidad de todos los repositorios de Emi.

Idea tomada del «Guardián Imperial» (Leyvi Cauich, Motor Agéntico, jun. 2026) y adaptada a la Matriz:
un puntaje de 0 a 100, un veredicto y siete chequeos, cada uno con «por qué importa» y «cómo lo
arreglas», en lenguaje simple. Solo lee y aconseja: nunca cambia, borra ni publica nada en los
repositorios que revisa.

Los siete chequeos (adaptados a un despacho jurídico que trabaja con IA):
  llaves       Llaves y tokens a la vista en los archivos actuales.
  historial    Llaves que se borraron, pero siguen en el historial de Git.
  credenciales Archivos de credenciales versionados, .gitignore sin .env y vencimientos próximos.
  acceso       Quién más tiene acceso (colaboradores, llaves de despliegue) y si están los frenos de ia/.
  salida       Qué sale de la cuenta: repositorios públicos del despacho, workflows de riesgo y acciones sin fijar.
  datos        Datos de clientes o personales (expedientes, CURP, RFC, tarjetas, teléfonos, correos,
               nombres reservados) en repositorios PÚBLICOS, en los archivos actuales o en el historial.
  skills       De dónde salieron las skills instaladas (propias o de terceros).

Dos salidas, nunca mezcladas:
  pública  guardian/estado.json y guardian/historial.json (este repositorio es público): puntaje,
           veredicto y conteos por chequeo y gravedad. Sin nombres de repositorios, rutas ni textos.
  privada  --detalle ruta.json (fuera del repositorio): repositorio, archivo, línea, tipo y una huella
           corta (primeros 4 caracteres + longitud). Nunca el valor completo de una llave ni el dato.

En consola solo se imprimen conteos (los registros de Actions de un repositorio público son públicos).

Uso:
  python3 tools/guardian.py --clonar [--detalle /tmp/detalle.json]       # en Actions, con MATRIZ_TOKEN
  python3 tools/guardian.py --repos-dir ~/codigo [--detalle /tmp/d.json] # con copias locales
  python3 tools/guardian.py --demo                                       # datos ficticios, sin red

Solo biblioteca estándar.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "ia"))
sys.path.insert(0, str(RAIZ / "tools"))
from guard import SECRET_PATTERNS, CURP, CARD, luhn  # noqa: E402  mismas reglas que el freno de commits
import generar as g  # noqa: E402

VERSION = "1.0.0"
SALIDA = RAIZ / "guardian"
MAX_HISTORIAL = 180
CEREBROS_JURIDICOS = {"castorena", "milla-abogados"}   # despachos: secreto profesional
MAX_BLOB = 1_000_000          # bytes por archivo revisado
LIMITE_CLON = "2m"            # los archivos más grandes (videos, PDF pesados) no se descargan

# ---------------------------------------------------------------- puntaje

PESO = {"critico": 30, "alto": 12, "medio": 5, "bajo": 1, "info": 0}
TOPE_POR_CHEQUEO = 40          # un solo chequeo no puede bajar más de 40 puntos
TOPE_BAJOS = 3                 # los detalles menores, juntos, restan a lo más 3 por chequeo
VEREDICTOS = [(90, "Fortaleza"), (75, "Vigilante"), (50, "Expuesto"), (0, "En riesgo")]

CHEQUEOS = {
    "llaves": {
        "icono": "🔑", "nombre": "Llaves a la vista",
        "por_que": "Una llave de API o un token en un archivo deja usar tus cuentas (Claude, GitHub, Google, "
                   "Cloudflare) a quien lo vea. En un repositorio público, los robots las encuentran en minutos.",
        "como": "Revoca la llave en su servicio y crea otra; guárdala como secreto (GitHub → Settings → "
                "Secrets, o ~/.config de tu box) y bórrala del archivo. Borrarla sin revocarla no basta.",
    },
    "historial": {
        "icono": "🕵️", "nombre": "Secretos en el historial de Git",
        "por_que": "Aunque ya borraste la llave, sigue en los commits anteriores y cualquiera puede verla en el "
                   "historial. Lo borrado en Git no desaparece.",
        "como": "Lo único seguro es revocar la llave y crear otra. Reescribir el historial no es necesario "
                "después de revocarla (y está prohibido el force-push sin tu confirmación).",
    },
    "credenciales": {
        "icono": "🪪", "nombre": "Credenciales expuestas y vencimientos",
        "por_que": "Archivos como .env, .pem o credentials.json guardan accesos completos; si se suben, "
                   "se filtran todos juntos. Y una llave que vence sin aviso detiene tus automatizaciones.",
        "como": "Saca el archivo del repositorio, agrégalo a .gitignore y revoca lo que traía. Renueva antes "
                "del vencimiento: la Matriz te muestra la fecha en «Vencimientos».",
    },
    "acceso": {
        "icono": "👥", "nombre": "Quién tiene acceso a qué",
        "por_que": "Cada colaborador o llave de despliegue es una puerta. Y un repositorio sin los frenos de ia/ "
                   "acepta commits sin registro y sin la revisión de secretos.",
        "como": "Quita colaboradores y llaves de despliegue que ya no uses (Settings → Collaborators / Deploy "
                "keys). Instala los frenos con el protocolo común (ia/ y registro-ia.yml).",
    },
    "salida": {
        "icono": "📡", "nombre": "Qué sale de tu cuenta",
        "por_que": "Todo lo de un repositorio público lo puede leer cualquiera, también lo que tus workflows "
                   "publican. Una acción de GitHub de terceros sin versión fija puede cambiar y ejecutar código "
                   "ajeno con tus secretos.",
        "como": "Vuelve privado lo que no necesita ser público. En los workflows, fija cada acción a su SHA "
                "(como ya hace la Matriz) y declara «permissions» con lo mínimo.",
    },
    "datos": {
        "icono": "🧾", "nombre": "Datos de clientes y personales expuestos",
        "por_que": "Expedientes, CURP, RFC, teléfonos o nombres de clientes en un repositorio público violan el "
                   "secreto profesional y la protección de datos personales, aunque sea en un archivo viejo.",
        "como": "Saca el dato del archivo (o vuelve privado el repositorio) y agrega el nombre del cliente al "
                "secreto MATRIZ_RESERVADOS. Si estuvo en el historial de un repositorio público, considéralo visto.",
    },
    "skills": {
        "icono": "📦", "nombre": "Origen de tus skills",
        "por_que": "Una skill son instrucciones (y a veces scripts) que tu IA sigue con tus permisos. Una de "
                   "terceros puede cambiar sin que lo sepas.",
        "como": "Usa skills de tus repositorios. Si una es de terceros, revisa su contenido, fija la versión "
                "(una copia en tu cuenta) y vuelve a revisarla cuando la actualices.",
    },
}

# ---------------------------------------------------------------- utilidades

EXT_BINARIAS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".mp4", ".mov", ".mp3", ".wav", ".m4a",
                ".zip", ".gz", ".tgz", ".woff", ".woff2", ".ttf", ".otf", ".docx", ".xlsx", ".pptx", ".psd",
                ".sqlite", ".db", ".heic", ".avif", ".glb", ".bin"}
EXT_TEXTO_LIBRE = {".md", ".txt", ".csv", ".tsv", ".json", ".html", ".htm", ".xml", ".yml", ".yaml", ".rtf", ""}
ARCHIVOS_DE_PRUEBA = re.compile(r"(^|/)(test_[^/]*|[^/]*[._]test\.[a-z]+|prueba[^/]*|tests?/|fixtures?/|ejemplos?/)|"
                                r"\.(ejemplo|example|sample|plantilla|template)$", re.I)
DOCUMENTO = re.compile(r"\.(xlsx|xlsm|xls|csv|docx|doc|pdf|odt|ods|pages|numbers|eml|msg)$", re.I)
DOCUMENTO_DE_ASUNTO = re.compile(r"expediente|control|concentrado|acuse|demanda|escrito|archivo[_ -]?muerto|junta|"
                                 r"amparo|sentencia|acuerdo|boletin|cliente|cotejo|promoci|contrato|poder|indep|tfca|tfja", re.I)
VALOR_FICTICIO = re.compile(r"(x{6,}|0{6,}|\.\.\.|example|ejemplo|dummy|fake|ficticio|placeholder|your[_-]|tu[_-]|"
                            r"changeme|redacted|\*{4,}|abcdef|123456789|<[^>]*>)", re.I)
ARCHIVO_CREDENCIAL = re.compile(r"(^|/)(\.env(\.[\w-]+)?|id_(rsa|ed25519|ecdsa)|[^/]*\.(pem|p12|pfx|key|keystore|jks)|"
                                r"credentials?[^/]*\.json|service[-_]?account[^/]*\.json|client_secret[^/]*\.json|"
                                r"token\.json|\.npmrc|\.pypirc|\.netrc)$", re.I)
ENV_PLANTILLA = re.compile(r"\.env\.(example|ejemplo|sample|template|plantilla)$", re.I)
CORREO = re.compile(r"[\w.%+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){1,6}")
CORREO_INOCUO = re.compile(r"(noreply|no-reply|users\.noreply\.github\.com|example\.(com|org|mx)|ejemplo\.|correo\.mx|"
                           r"dominio\.|anthropic\.com$|@(sentry|git)|\.(png|jpg|svg|webp)$)", re.I)
TELEFONO = re.compile(r"(?<![\w/.:#-])(?:\+?52[\s.-]?)?(?:\(\d{2,3}\)\s?|\d{2,3}[\s.-])\d{4}[\s.-]?\d{4}(?![\w/])")
EXPEDIENTE = [re.compile(x["re"], re.I if x.get("i") else 0) for x in
              json.loads((RAIZ / "tools" / "privacidad.json").read_text(encoding="utf-8"))["patrones"]
              if x["por"] == "[expediente]"][::2]  # el de sufijo (27969/22-17-02-5) y el rotulado («Exp. No. 45/2023»)
RFC_FISICA = re.compile(r"\b[A-ZÑ&]{4}(\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])[A-Z\d]{2}[A\d]\b")
ACCION = re.compile(r"^\s*-?\s*uses:\s*([\w.-]+/[\w./-]+)@([\w.-]+)", re.M)


def git(args: list[str], cwd: Path, entrada: bytes | None = None) -> bytes:
    r = subprocess.run(["git", *args], cwd=cwd, input=entrada, capture_output=True)
    return r.stdout if r.returncode == 0 else b""


def huella(valor: str) -> str:
    """Identifica un hallazgo sin revelarlo: 4 primeros caracteres y longitud."""
    v = valor.strip()
    return f"{v[:4]}…({len(v)})"


def es_binario(ruta: str, contenido: bytes) -> bool:
    return Path(ruta).suffix.lower() in EXT_BINARIAS or b"\0" in contenido[:8000]


def hallazgo(chequeo: str, gravedad: str, repo: str, tipo: str, ruta: str = "", linea: int = 0, pista: str = "") -> dict:
    return {"chequeo": chequeo, "gravedad": gravedad, "repo": repo, "tipo": tipo, "ruta": ruta, "linea": linea,
            "huella": pista}


# ---------------------------------------------------------------- lectura de objetos

def blobs(carpeta: Path) -> tuple[dict[str, set[str]], set[str]]:
    """Todos los archivos de todo el historial: {oid: {rutas}} y el conjunto de oids del último commit.

    En un clon parcial (--filter=blob:limit) los archivos grandes faltan: se saltan sin descargarlos
    (--missing=print los marca con «?» en lugar de pedirlos a GitHub)."""
    por_oid: dict[str, set[str]] = {}
    for linea in git(["rev-list", "--objects", "--all", "--missing=print"], carpeta).decode(errors="replace").splitlines():
        if not linea or linea.startswith("?"):
            continue
        partes = linea.split(" ", 1)
        if len(partes) == 2:
            por_oid.setdefault(partes[0], set()).add(partes[1])
    actuales = set()
    for linea in git(["ls-tree", "-r", "HEAD"], carpeta).decode(errors="replace").splitlines():
        meta, _, _ruta = linea.partition("\t")
        m = meta.split()
        if len(m) == 3 and m[1] == "blob":
            actuales.add(m[2])
    return por_oid, actuales


def leer_blobs(carpeta: Path, oids: list[str]):
    """Devuelve (oid, contenido) de los blobs de texto de tamaño razonable, con una sola llamada a git."""
    if not oids:
        return
    chequeo = git(["cat-file", "--batch-check"], carpeta, ("\n".join(oids) + "\n").encode()).decode().splitlines()
    validos = [l.split()[0] for l in chequeo if len(l.split()) == 3 and l.split()[1] == "blob" and int(l.split()[2]) <= MAX_BLOB]
    if not validos:
        return
    salida = git(["cat-file", "--batch"], carpeta, ("\n".join(validos) + "\n").encode())
    i = 0
    while i < len(salida):
        fin = salida.index(b"\n", i)
        oid, tipo, tam = salida[i:fin].decode().split()
        tam = int(tam)
        yield oid, salida[fin + 1:fin + 1 + tam]
        i = fin + 1 + tam + 1


# ---------------------------------------------------------------- chequeos por repositorio

def entropia(v: str) -> float:
    return -sum((v.count(c) / len(v)) * math.log2(v.count(c) / len(v)) for c in set(v)) if v else 0.0


def parece_secreto(valor: str) -> bool:
    """Una asignación (token = …) solo cuenta si el valor parece una llave real y no código ni una plantilla:
    sin puntos, paréntesis ni variables; letras y números mezclados; alta entropía."""
    v = re.split(r"[:=]", valor, maxsplit=1)[-1].strip().strip("'\"`")
    if len(v) < 16 or re.search(r"[.()\[\]{}$|,;\\/ ]", v) or VALOR_FICTICIO.search(v):
        return False
    if re.fullmatch(r"[A-Z0-9_]+", v) or not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
        return False  # NOMBRE_DE_VARIABLE o una palabra sin números
    return entropia(v) >= 3.5


def buscar_llaves(texto: str):
    for n, linea in enumerate(texto.splitlines(), 1):
        if len(linea) > 4000:
            continue
        for etiqueta, patron in SECRET_PATTERNS:
            m = patron.search(linea)
            if not m or VALOR_FICTICIO.search(m.group(0)):
                continue
            if etiqueta == "asignación de secreto" and not parece_secreto(m.group(0)):
                continue
            yield n, etiqueta, m.group(0)


def buscar_datos(texto: str, ruta: str, reservados: set[str]):
    libre = Path(ruta).suffix.lower() in EXT_TEXTO_LIBRE
    for n, linea in enumerate(texto.splitlines(), 1):
        if len(linea) > 4000:
            continue
        if m := CURP.search(linea):
            yield n, "critico", "CURP", m.group(0)
        if m := RFC_FISICA.search(linea):
            yield n, "critico", "RFC de persona", m.group(0)
        sin_urls = re.sub(r"https?://\S+", " ", linea)
        menciona = re.search(r"tarjeta|card|visa|master|amex|cvv", sin_urls, re.I)
        for cand in CARD.findall(sin_urls):
            d = re.sub(r"\D", "", cand)
            agrupada = re.fullmatch(r"\d{4}([ -])\d{4}\1\d{4}\1\d{4}", cand.strip())
            if len(d) == 16 and luhn(d) and len(set(d)) > 3 and (agrupada or menciona):
                yield n, "critico", "número de tarjeta", cand
        if reservados:
            norm = " " + g.normalizar_termino(linea) + " "
            for t in reservados:
                if f" {t} " in norm:
                    yield n, "critico", "nombre de cliente reservado", t
                    break
        if not libre:
            continue  # en código, los números y correos casi siempre son otra cosa
        for patron in EXPEDIENTE:
            if m := patron.search(linea):
                yield n, "alto", "número de expediente", m.group(0)
                break
        if m := TELEFONO.search(linea):
            yield n, "bajo", "teléfono", m.group(0)
        for c in CORREO.findall(linea):
            if not CORREO_INOCUO.search(c):
                yield n, "bajo", "correo", c
                break


def auditar_repo(nombre: str, carpeta: Path, publico: bool, reservados: set[str], juridico: bool = False) -> list[dict]:
    H: list[dict] = []
    por_oid, actuales = blobs(carpeta)
    vistos_llave: set[tuple[str, str]] = set()   # (etiqueta, valor): una llave se cuenta una vez por repositorio
    vistos_dato: set[tuple[str, str, bool]] = set()
    for oid, contenido in leer_blobs(carpeta, list(por_oid)):
        rutas = sorted(por_oid.get(oid, {""}))
        ruta = rutas[0]
        if es_binario(ruta, contenido):
            continue
        texto = contenido.decode("utf-8", errors="replace")
        actual = oid in actuales
        prueba = all(ARCHIVOS_DE_PRUEBA.search(r) for r in rutas)
        for n, etiqueta, valor in buscar_llaves(texto):
            if (etiqueta, valor) in vistos_llave:
                continue
            vistos_llave.add((etiqueta, valor))
            if prueba:
                grav = "info" if etiqueta in ("asignación de secreto", "clave privada") else "bajo"
            elif etiqueta == "asignación de secreto":
                grav = "alto" if publico else "bajo"
            else:
                grav = "critico" if publico else "medio"
            H.append(hallazgo("llaves" if actual else "historial", grav, nombre, etiqueta, ruta if actual else ruta + " (borrado)",
                              n if actual else 0, huella(valor)))
        if publico and not prueba:
            for n, grav, tipo, valor in buscar_datos(texto, ruta, reservados):
                clave = (tipo, valor.lower(), actual)
                if clave in vistos_dato:
                    continue
                vistos_dato.add(clave)
                H.append(hallazgo("datos", grav, nombre, tipo + ("" if actual else " (en el historial)"),
                                  ruta, n if actual else 0, huella(valor)))
    # credenciales versionadas y .gitignore
    rutas_actuales = [l.decode(errors="replace") for l in git(["ls-tree", "-r", "--name-only", "HEAD"], carpeta).splitlines()]
    for r in rutas_actuales:
        if ARCHIVO_CREDENCIAL.search(r) and not ENV_PLANTILLA.search(r):
            H.append(hallazgo("credenciales", "critico" if publico else "alto", nombre, "archivo de credenciales versionado", r))
    # Documentos de trabajo (Excel, Word, PDF) en repositorios públicos: el escáner de texto no los lee,
    # pero cualquiera los puede descargar. En los cerebros jurídicos se tratan como datos de asuntos.
    if publico:
        docs = [r for r in rutas_actuales if DOCUMENTO.search(r)]
        for r in docs:
            if juridico and DOCUMENTO_DE_ASUNTO.search(r):
                H.append(hallazgo("datos", "critico", nombre, "documento de asuntos descargable", r))
            elif juridico:
                H.append(hallazgo("datos", "alto", nombre, "documento de trabajo descargable", r))
    hay_codigo = any(r.endswith(("package.json", ".py", "requirements.txt", "wrangler.jsonc", "wrangler.toml")) for r in rutas_actuales)
    ignorar = git(["show", "HEAD:.gitignore"], carpeta).decode(errors="replace")
    if hay_codigo and not re.search(r"^\s*/?\.env\b|^\s*\*\.env|^\s*\.env\*", ignorar, re.M):
        H.append(hallazgo("credenciales", "bajo", nombre, ".gitignore no excluye .env", ".gitignore"))
    # frenos del protocolo común: la versión completa (ia/guard.py + registro-ia.yml) o la ligera
    # (un workflow que corre `ia/verificar.py ci`, que revisa registro y secretos en cada push)
    completa = {"ia/guard.py", ".github/workflows/registro-ia.yml"} <= set(rutas_actuales)
    ligera = "ia/verificar.py" in rutas_actuales and any(
        re.match(r"\.github/workflows/[^/]+\.ya?ml$", r) and "ia/verificar.py ci" in git(["show", f"HEAD:{r}"], carpeta).decode(errors="replace")
        for r in rutas_actuales)
    if not (completa or ligera):
        H.append(hallazgo("acceso", "medio" if publico else "bajo", nombre, "sin los frenos de ia/ (registro y secretos)"))
    # workflows
    for r in rutas_actuales:
        if not re.match(r"\.github/workflows/[^/]+\.ya?ml$", r):
            continue
        wf = git(["show", f"HEAD:{r}"], carpeta).decode(errors="replace")
        if re.search(r"^\s*pull_request_target\s*:", wf, re.M) or re.search(r"\bon:\s*\[?[^\n]*pull_request_target", wf):
            H.append(hallazgo("salida", "alto", nombre, "workflow con pull_request_target", r))
        if re.search(r"permissions:\s*write-all", wf):
            H.append(hallazgo("salida", "medio", nombre, "workflow con permissions: write-all", r))
        for accion, ref in ACCION.findall(wf):
            if accion.startswith(("./", "docker://")):
                continue
            if not re.fullmatch(r"[0-9a-f]{40}", ref):
                H.append(hallazgo("salida", "bajo", nombre, f"acción sin fijar a SHA ({accion.split('/')[0]})", r))
    return H


# ---------------------------------------------------------------- chequeos de cuenta

def api_github(ruta: str, token: str):
    req = urllib.request.Request(f"https://api.github.com{ruta}", headers={
        "Accept": "application/vnd.github+json", "User-Agent": "matriz-guardian", "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return None


def auditar_acceso_api(repos: list[dict], propietario: str, token: str) -> tuple[list[dict], dict]:
    """Colaboradores y llaves de despliegue. Requieren el permiso «Administration: read» del token;
    sin él se informa «sin permiso para revisar» y no resta puntos."""
    H, cobertura = [], {"revisados": 0, "sin_permiso": 0}
    if not token:
        cobertura["sin_permiso"] = len(repos)
        return H, cobertura
    for r in repos:
        colab = api_github(f"/repos/{propietario}/{r['nombre']}/collaborators?per_page=100&affiliation=direct", token)
        llaves = api_github(f"/repos/{propietario}/{r['nombre']}/keys?per_page=100", token)
        if colab is None and llaves is None:
            cobertura["sin_permiso"] += 1
            continue
        cobertura["revisados"] += 1
        for c in colab or []:
            if c.get("login", "").lower() != propietario.lower():
                H.append(hallazgo("acceso", "medio", r["nombre"], "colaborador con acceso", pista=c.get("login", "")[:2] + "…"))
        for k in llaves or []:
            H.append(hallazgo("acceso", "medio" if not k.get("read_only", True) else "bajo", r["nombre"],
                              "llave de despliegue " + ("con escritura" if not k.get("read_only", True) else "de solo lectura")))
    return H, cobertura


def auditar_cuenta(cfg: dict, inv: dict, visibilidad: dict[str, str], hoy: dt.date) -> list[dict]:
    H = []
    for v in inv.get("vencimientos", []):
        try:
            dias = (dt.date.fromisoformat(v["fecha"]) - hoy).days
        except (KeyError, ValueError):
            continue
        if dias < 0:
            H.append(hallazgo("credenciales", "alto", "", f"vencido: {v.get('nombre', '')}"))
        elif dias <= 14:
            H.append(hallazgo("credenciales", "medio", "", f"vence en {dias} días: {v.get('nombre', '')}"))
    for s in inv.get("skills_instaladas", []):
        origen = s.get("repo", "")
        if "/" in origen and not origen.lower().startswith(cfg.get("propietario", "lianfixx").lower() + "/"):
            H.append(hallazgo("skills", "medio", "", f"skill de terceros: {s.get('nombre', '')}", pista=origen.split("/")[0]))
        elif origen and "/" not in origen and origen not in visibilidad:
            H.append(hallazgo("skills", "bajo", "", f"skill sin repositorio localizable: {s.get('nombre', '')}"))
    # El despacho donde trabaja Emi no debería tener repositorios públicos con contenido de asuntos.
    for c in cfg.get("cerebros", []):
        if c["id"] in CEREBROS_JURIDICOS:
            pub = [r for r in c["repos"] if visibilidad.get(r) == "público"]
            if pub:
                H.append(hallazgo("salida", "info", "", f"{len(pub)} de {len(c['repos'])} repositorios de {c['nombre']} son públicos"))
    return H


# ---------------------------------------------------------------- puntaje y salidas

def puntuar(H: list[dict]) -> dict:
    por = {}
    for cid, meta in CHEQUEOS.items():
        propios = [h for h in H if h["chequeo"] == cid]
        conteo = {gv: sum(1 for h in propios if h["gravedad"] == gv) for gv in PESO}
        # El primer hallazgo de cada gravedad resta su peso completo; cada uno más, una cuarta parte.
        resta = min(TOPE_POR_CHEQUEO, round(sum(PESO[gv] * (1 + (n - 1) / 4) for gv, n in conteo.items()
                                                if n and gv not in ("bajo", "info")) + min(conteo["bajo"], TOPE_BAJOS)))
        estado = ("En riesgo" if conteo["critico"] else "Atender" if conteo["alto"] else
                  "Revisar" if conteo["medio"] else "Bien")
        por[cid] = {"icono": meta["icono"], "nombre": meta["nombre"], "estado": estado, "resta": resta,
                    "conteo": {k: v for k, v in conteo.items() if v}, "por_que": meta["por_que"], "como": meta["como"]}
    puntaje = max(0, 100 - sum(c["resta"] for c in por.values()))
    veredicto = next(v for umbral, v in VEREDICTOS if puntaje >= umbral)
    return {"puntaje": puntaje, "veredicto": veredicto, "chequeos": por}


def salida_publica(res: dict, cobertura: dict, hoy: str) -> dict:
    return {"_doc": "Lo escribe tools/guardian.py. Público: solo puntaje, veredicto y conteos; nunca repositorios, "
                    "rutas ni textos. El detalle es privado (ver docs/GUARDIAN.md).",
            "version": VERSION, "fecha": hoy, "puntaje": res["puntaje"], "veredicto": res["veredicto"],
            "cobertura": cobertura, "chequeos": res["chequeos"]}


def actualizar_historial(ruta: Path, hoy: str, puntaje: int) -> list[dict]:
    try:
        hist = json.loads(ruta.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        hist = []
    hist = [h for h in hist if h.get("fecha") != hoy] + [{"fecha": hoy, "puntaje": puntaje}]
    return sorted(hist, key=lambda h: h["fecha"])[-MAX_HISTORIAL:]


def resumen_md(pub: dict, hist: list[dict]) -> str:
    L = [f"# Guardián de la Matriz · {pub['fecha']}", "",
         f"**{pub['puntaje']}/100 · {pub['veredicto']}**", "",
         "Auditoría de seguridad y privacidad de todos los repositorios de Emi. Solo lee y aconseja. "
         "Aquí solo hay conteos: el detalle (qué repositorio, qué archivo) es privado. Cómo funciona: "
         "[docs/GUARDIAN.md](../docs/GUARDIAN.md).", ""]
    if len(hist) > 1:
        L += ["Evolución: " + " → ".join(f"{h['puntaje']}" for h in hist[-8:]), ""]
    c = pub["cobertura"]
    L += [f"Revisados: {c.get('repos', 0)} repositorios ({c.get('publicos', 0)} públicos). "
          f"Acceso por API: {c.get('revisados', 0)} revisados, {c.get('sin_permiso', 0)} sin permiso para revisar.", ""]
    nombres = {"critico": "crítico", "alto": "alto", "medio": "medio", "bajo": "bajo", "info": "aviso"}
    for ch in pub["chequeos"].values():
        cuenta = ", ".join(f"{v} {nombres[k]}" for k, v in ch["conteo"].items()) or "sin hallazgos"
        L += [f"## {ch['icono']} {ch['nombre']} · {ch['estado']}", "", f"Hallazgos: {cuenta}.", "",
              f"- **Por qué importa:** {ch['por_que']}", f"- **Cómo lo arreglas:** {ch['como']}", ""]
    return "\n".join(L)


def clonar(nombre: str, propietario: str, destino: Path) -> Path | None:
    token = os.environ.get("MATRIZ_TOKEN", "").strip()
    auth = f"x-access-token:{token}@" if token else ""
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1", "GIT_TERMINAL_PROMPT": "0"}
    r = subprocess.run(["git", "-c", "http.https://github.com/.extraheader=", "clone", "--quiet", "--no-checkout",
                        f"--filter=blob:limit={LIMITE_CLON}", f"https://{auth}github.com/{propietario}/{nombre}",
                        str(destino / nombre)], capture_output=True, text=True, cwd=destino, env=env, timeout=600)
    return destino / nombre if r.returncode == 0 else None


def visibilidad_confirmada(propietario: str) -> dict[str, str]:
    """Visibilidad según GitHub. Si la API no responde, la última que GitHub confirmó al generar matriz.json.
    Lo que no se pueda confirmar se trata como privado (no se revisan sus datos, pero sí sus llaves)."""
    vistos = g.descubrir(propietario)
    if vistos:
        return {n: d["visibilidad"] for n, d in vistos.items()}
    try:
        m = json.loads((RAIZ / "matriz.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}
    return {r["nombre"]: r["visibilidad"] for c in m.get("cerebros", []) for r in c.get("repos", []) if r.get("visibilidad")}


def comparar(previo: dict, actual: dict) -> str:
    """Texto del aviso si el estado empeoró (más críticos o 5 puntos menos). Solo conteos: va a un Issue público."""
    def criticos(e: dict) -> int:
        return sum((c.get("conteo") or {}).get("critico", 0) for c in (e.get("chequeos") or {}).values())
    if not isinstance(previo.get("puntaje"), int):
        return ""  # primera corrida: no hay contra qué comparar
    antes, ahora = criticos(previo), criticos(actual)
    p0, p1 = previo.get("puntaje"), actual.get("puntaje")
    if not (ahora > antes or (isinstance(p0, int) and isinstance(p1, int) and p1 <= p0 - 5)):
        return ""
    L = [f"El Guardián bajó de {p0 if p0 is not None else 'sin dato'} a **{p1}/100 · {actual.get('veredicto')}** "
         f"({actual.get('fecha')}). Hallazgos críticos: {antes} → {ahora}.", "",
         "Por chequeo (solo conteos; el detalle es privado):"]
    for c in (actual.get("chequeos") or {}).values():
        if c.get("conteo"):
            L.append(f"- {c['icono']} {c['nombre']}: {c['estado']} · " + ", ".join(f"{n} {k}" for k, n in c["conteo"].items()))
    L += ["", "Qué hacer: abre el detalle privado (docs/GUARDIAN.md, «Dónde está el detalle») o pide a Claude "
          "«revisa el Guardián». Cierra este aviso cuando quede atendido."]
    return "\n".join(L)


def demo() -> tuple[list[dict], dict]:
    H = [hallazgo("historial", "critico", "demo-publico", "token de GitHub", "config.js (borrado)", 0, "ghp_…(40)"),
         hallazgo("datos", "alto", "demo-publico", "número de expediente", "notas.md", 12, "1234…(9)"),
         hallazgo("salida", "bajo", "demo", "acción sin fijar a SHA (actions)", ".github/workflows/x.yml"),
         hallazgo("skills", "medio", "", "skill de terceros: demo", pista="tercero")]
    return H, {"repos": 2, "publicos": 1, "revisados": 0, "sin_permiso": 2}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--clonar", action="store_true", help="clona cada repositorio (historial completo, sin archivos de más de 2 MB)")
    ap.add_argument("--repos-dir", type=Path, help="carpeta con copias locales (una por repositorio)")
    ap.add_argument("--detalle", type=Path, help="dónde escribir el detalle PRIVADO (nunca dentro de este repositorio)")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    ap.add_argument("--hoy", default="")
    ap.add_argument("--demo", action="store_true", help="datos ficticios, sin red ni repositorios")
    ap.add_argument("--comparar", type=Path, metavar="PREVIO.json",
                    help="no audita: imprime el aviso si guardian/estado.json empeoró respecto de PREVIO.json")
    a = ap.parse_args()
    if a.comparar:
        try:
            previo = json.loads(a.comparar.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            previo = {}
        actual = json.loads((a.salida / "estado.json").read_text(encoding="utf-8"))
        print(comparar(previo, actual))
        return 0
    hoy_d = dt.date.fromisoformat(a.hoy) if a.hoy else dt.datetime.now().date()
    hoy = hoy_d.isoformat()
    if a.detalle and RAIZ in a.detalle.resolve().parents:
        print("El detalle es privado: escríbelo fuera de este repositorio público.", file=sys.stderr)
        return 2
    cfg = json.loads((RAIZ / "matriz.config.json").read_text(encoding="utf-8"))
    inv = json.loads((RAIZ / "inventario.json").read_text(encoding="utf-8"))
    propietario = cfg.get("propietario", "lianfixx")

    if a.demo:
        H, cobertura = demo()
    else:
        reservados = {g.normalizar_termino(t) for t in g.terminos_del_entorno()} - {""}
        visibilidad = visibilidad_confirmada(propietario)
        nombres = sorted(set(visibilidad) | {r for c in cfg["cerebros"] for r in c["repos"]} | {"MATRIZ"})
        juridicos = {r for c in cfg["cerebros"] if c["id"] in CEREBROS_JURIDICOS for r in c["repos"]}
        H, cobertura = [], {"repos": 0, "publicos": 0, "sin_lectura": 0}
        with tempfile.TemporaryDirectory() as tmp:
            for n in nombres:
                carpeta = None
                if a.repos_dir:
                    for cand in (a.repos_dir / n, a.repos_dir / n.lower()):
                        if (cand / ".git").exists() or (cand / "HEAD").exists():
                            carpeta = cand
                            break
                if carpeta is None and a.clonar:
                    carpeta = clonar(n, propietario, Path(tmp))
                if carpeta is None:
                    cobertura["sin_lectura"] += 1
                    continue
                publico = visibilidad.get(n) == "público"  # si GitHub no lo confirma, se trata como privado
                cobertura["repos"] += 1
                cobertura["publicos"] += int(publico)
                H += auditar_repo(n, carpeta, publico, reservados, n in juridicos)
        acc, cob_api = auditar_acceso_api([{"nombre": n} for n in nombres], propietario,
                                          os.environ.get("MATRIZ_TOKEN", "").strip())
        H += acc
        cobertura.update(cob_api)
        H += auditar_cuenta(cfg, inv, visibilidad, hoy_d)

    res = puntuar(H)
    pub = salida_publica(res, cobertura, hoy)
    a.salida.mkdir(parents=True, exist_ok=True)
    if not a.demo:
        hist = actualizar_historial(a.salida / "historial.json", hoy, res["puntaje"])
        (a.salida / "historial.json").write_text(json.dumps(hist, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (a.salida / "estado.json").write_text(json.dumps(pub, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (a.salida / "GUARDIAN.md").write_text(resumen_md(pub, hist), encoding="utf-8")
    orden = {k: i for i, k in enumerate(PESO)}
    detalle = {"fecha": hoy, "version": VERSION, "puntaje": res["puntaje"], "veredicto": res["veredicto"],
               "hallazgos": sorted(H, key=lambda h: (orden[h["gravedad"]], h["chequeo"], h["repo"], h["ruta"]))}
    if a.detalle:
        a.detalle.write_text(json.dumps(detalle, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # Solo conteos en consola.
    print(f"Guardián {VERSION}: {res['puntaje']}/100 · {res['veredicto']} · {len(H)} hallazgos · "
          + " · ".join(f"{cid} {sum(c['conteo'].values())}" for cid, c in res["chequeos"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
