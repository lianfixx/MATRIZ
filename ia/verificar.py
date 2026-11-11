#!/usr/bin/env python3
"""Aplica las reglas de `ia/politica.json` fuera de Claude Code.

Uso:
  python3 ia/verificar.py precommit          # hook de git pre-commit (cualquier IA o persona)
  python3 ia/verificar.py prepush            # hook de git pre-push (lee las refs por stdin)
  python3 ia/verificar.py ci --base A --head B   # GitHub Actions: registro, secretos, skill, reglas
  python3 ia/verificar.py reglas [--check]   # regenera (o comprueba) ia/REGLAS.md desde la política
  python3 ia/verificar.py inicio [--hook]    # resumen de arranque para cualquier IA (estado, reglas, registro)

Código de salida 1 si algo queda bloqueado. Las decisiones «ask» se muestran como aviso:
en git no hay a quién preguntar, así que la confirmación con Emi debe constar antes.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard  # noqa: E402

ZERO = "0" * 40
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
KIND_LABEL = {"deny": "Prohibido", "ask": "Requiere confirmación expresa de Emi"}


def report(decision, reasons, where: str) -> int:
    for r in reasons:
        print(f"[{where}] {r}", file=sys.stderr)
    if decision == "deny":
        print(f"[{where}] Bloqueado. Corrige y vuelve a intentar; no uses --no-verify para saltarlo.", file=sys.stderr)
        return 1
    return 0


def resolve_base(root: Path, base: str | None, head: str) -> str:
    if base and base != ZERO and subprocess.run(["git", "cat-file", "-e", base], cwd=root).returncode == 0:
        return base
    for ref in ("origin/HEAD", "origin/main", "origin/master"):
        mb = subprocess.run(["git", "merge-base", ref, head], cwd=root, capture_output=True, text=True)
        if mb.returncode == 0 and mb.stdout.strip() and mb.stdout.strip() != subprocess.run(
                ["git", "rev-parse", head], cwd=root, capture_output=True, text=True).stdout.strip():
            return mb.stdout.strip()
    parent = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{head}~1"], cwd=root, capture_output=True, text=True)
    return parent.stdout.strip() or EMPTY_TREE


def describe(rule: dict) -> str | None:
    kind = rule.get("type", "pattern")
    if kind == "registro":
        return "Prohibido: commit sin entrada en el registro del repositorio (ver «Registro obligatorio»)."
    if kind == "secrets":
        momento = "push" if rule.get("git") == "push" else "commit"
        extra = " ni datos personales (CURP, tarjetas)" if rule.get("pii") else ""
        return f"Prohibido: {momento} con secretos (claves, tokens){extra}."
    if kind == "inmutable":
        return f"Prohibido: {rule['reason']}"
    if kind == "before_git":
        return f"Antes de `git {rule.get('git', 'commit')}`: `{rule['run']}` debe pasar. {rule['reason']}"
    label = KIND_LABEL.get(rule.get("decision"), "Regla")
    if kind == "recipients":
        return f"Prohibido: {rule['reason']} Destinatarios permitidos: {', '.join(rule['allow'])}" + (", sin CC/CCO." if rule.get("forbid_cc") else ".")
    return f"{label}: {rule['reason']}"


def reglas_md(policy: dict) -> str:
    lines = [
        "# Reglas de este repositorio para cualquier IA",
        "",
        "Generado desde `ia/politica.json` con `python3 ia/verificar.py reglas`. No editar a mano.",
        "",
        "Valen igual en Claude, ChatGPT, Codex, Gemini o cualquier otra IA, y para personas. En",
        "Claude Code se aplican solas (hooks); con copia local, con los hooks de git (`sh ia/instalar.sh`);",
        "en GitHub, el workflow `registro-ia.yml` revisa cada push. Donde no hay freno automático",
        "(chat de claude.ai, ChatGPT o Gemini, conectores), la IA debe cumplirlas por sí misma.",
        "",
    ]
    seen = set()
    for rule in policy.get("rules", []):
        text = describe(rule)
        if text and text not in seen:
            seen.add(text)
            lines.append(f"- {text}")
    logs = (policy.get("registro") or {}).get("logs") or []
    if logs:
        lines += ["", "## Registro obligatorio", "",
                  "Todo commit que cambie archivos debe actualizar, en el mismo commit, al menos uno de:", ""]
        for log in logs:
            req = f" (la entrada nueva incluye «{log['require']}»)" if log.get("require") else ""
            add = " (solo archivos nuevos)" if log.get("only_added") else ""
            lines.append(f"- `{log['path']}`{req}{add}")
    return "\n".join(lines) + "\n"


def _git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.stdout.strip() if p.returncode == 0 else ""


def legible(pattern: str) -> str:
    """Convierte la regex de un registro en una ruta legible (`^temas/[^/]+/CAMBIOS\\.md$` → `temas/<tema>/CAMBIOS.md`)."""
    import re
    t = pattern.strip("^$").replace("\\.", ".").replace("(^|/)", "")
    t = re.sub(r"\[\^/\]\+", "<…>", t)
    return t.rstrip("/") + ("/…" if pattern.endswith("/") else "")


def ultimas_entradas(root: Path, policy: dict, n: int = 3) -> list[str]:
    """Títulos de las entradas más recientes de los registros del proyecto."""
    import re
    out = []
    for log in (policy.get("registro") or {}).get("logs", []):
        pat = log["path"].strip("^$").replace("\\.", ".")
        if any(c in pat for c in "[(*+?|") or not (root / pat).is_file():
            continue
        heads = [l.strip("# ").strip() for l in (root / pat).read_text(encoding="utf-8", errors="replace").splitlines()
                 if re.match(r"^#{2,3} ", l)]
        out += [f"{pat}: {h}" for h in heads[:n]]
    return out[: n * 2]


def inicio(root: Path, policy: dict, hook: bool) -> int:
    """Resumen de arranque: lo mismo para Claude (hook SessionStart), Codex, Gemini o una persona."""
    instalados = _git(root, "config", "--get", "core.hooksPath").rstrip("/") == "ia/githooks"
    recien = False
    # Cualquier IA que siga AGENTS.md (Claude, Codex, ChatGPT con terminal, Gemini CLI) activa aquí los hooks de git.
    if not instalados and (root / "ia" / "githooks" / "pre-commit").exists() and _git(root, "rev-parse", "--git-dir"):
        subprocess.run(["sh", "ia/instalar.sh"], cwd=root, capture_output=True)
        instalados = recien = _git(root, "config", "--get", "core.hooksPath").rstrip("/") == "ia/githooks"
    rama = _git(root, "branch", "--show-current") or "(sin rama)"
    ultimo = _git(root, "log", "-1", "--format=%h · %ad · %an · %s", "--date=format:%Y-%m-%d %H:%M")
    actor = _git(root, "log", "-1", "--format=%(trailers:key=IA-Actor,valueonly,separator=%x2C )") or \
        _git(root, "log", "-1", "--format=%(trailers:key=Mes-Actor,valueonly,separator=%x2C )")
    pendientes = _git(root, "status", "--porcelain")
    skill = policy.get("skill")
    logs = ", ".join(f"`{legible(l['path'])}`" for l in (policy.get("registro") or {}).get("logs", []))
    lineas = [
        f"Protocolo común entre IA activo en {policy.get('repo', root.name)} (ia/PROTOCOLO.md).",
        "Antes de trabajar: leer AGENTS.md, ia/REGLAS.md e ia/PROTOCOLO.md"
        + (f", y la skill `{skill['name']}` ({skill['dir']}/SKILL.md)." if skill else "."),
        "Fuente de verdad: el repositorio remoto, no la memoria. Hacer `git pull` antes de escribir.",
        f"Todo cambio se registra en el mismo commit en {logs}, con la línea `Agente:` (quién lo hizo).",
        "Sin escritura en el repositorio: terminar con «Registro pendiente para el repositorio».",
        f"Rama: {rama}. Último commit: {ultimo or 'no disponible'}" + (f" (IA: {actor})." if actor else "."),
        "Hooks de git: " + ("activados ahora en esta copia." if recien else "activos." if instalados
                            else "NO activos; ejecutar `sh ia/instalar.sh`."),
    ]
    if pendientes:
        lineas.append(f"Hay {len(pendientes.splitlines())} archivos con cambios sin commit: revisar de quién son antes de seguir.")
    entradas = ultimas_entradas(root, policy)
    if entradas:
        lineas.append("Últimas entradas del registro: " + " | ".join(entradas))
    texto = "\n".join(lineas)
    if hook:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": texto}},
                         ensure_ascii=False))
    else:
        print(texto)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["precommit", "prepush", "ci", "reglas", "inicio"])
    ap.add_argument("--hook", action="store_true", help="inicio: salida JSON para el hook SessionStart de Claude Code")
    ap.add_argument("--base")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--root", help="raíz del repositorio (por defecto, la del directorio actual)")
    ap.add_argument("--politica", help="política a aplicar (CI: la de la base, no la del push)")
    a = ap.parse_args()
    root = Path(a.root).resolve() if a.root else guard.repo_root(prefer_env=False)
    policy = guard.load_policy(root, Path(a.politica) if a.politica else None)

    if a.modo == "reglas":
        text = reglas_md(policy)
        target = root / "ia" / "REGLAS.md"
        if a.check:
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                print("ia/REGLAS.md no coincide con ia/politica.json; ejecuta `python3 ia/verificar.py reglas`.", file=sys.stderr)
                return 1
            return 0
        target.write_text(text, encoding="utf-8")
        print("ia/REGLAS.md actualizado")
        return 0

    if a.modo == "inicio":
        return inicio(root, policy, a.hook)

    if a.modo == "precommit":
        changes = guard.Changes(root, "commit", "git commit")
        d, r = guard.evaluate({}, policy, root, changes=changes)
        return report(d, r, "pre-commit")

    if a.modo == "prepush":
        status = 0
        for line in sys.stdin.read().splitlines():
            parts = line.split()
            if len(parts) != 4 or parts[1] == ZERO:
                continue  # borrado de rama
            head = parts[1]
            base = resolve_base(root, parts[3], head)
            d, r = guard.evaluate({}, policy, root, changes=guard.Changes(root, "push", base=base, head=head))
            status |= report(d, r, "pre-push")
            # además, registro, secretos e inmutables de cada commit que se sube (como en CI)
            d, r = guard.evaluate({}, policy, root, changes=guard.Changes(root, "ci", base=base, head=head))
            status |= report(d, r, "pre-push")
        return status

    # ci
    head = subprocess.run(["git", "rev-parse", a.head], cwd=root, capture_output=True, text=True).stdout.strip()
    base = resolve_base(root, a.base, head)
    changes = guard.Changes(root, "ci", base=base, head=head)
    print(f"Revisando {base[:12]}..{head[:12]}: {len(changes.files())} archivos")
    d, r = guard.evaluate({}, policy, root, changes=changes)
    status = report(d, r, "ci")
    skill = policy.get("skill")
    files = changes.files()
    if skill and any(f == skill["dir"].strip("./") + "/SKILL.md" or f.endswith("SKILL.md") for f in files):
        code, out = guard.run(f"{sys.executable} ia/check_skill.py {skill['dir']}", root, 120)
        print(out.strip())
        status |= code != 0
    if any(f.startswith("ia/") for f in files) and (root / "ia" / "test_guard.py").exists():
        code, out = guard.run(f"{sys.executable} ia/test_guard.py", root, 900)
        print(out.strip()[-1500:])
        status |= code != 0
    code = subprocess.run([sys.executable, str(root / "ia" / "verificar.py"), "reglas", "--check"], cwd=root).returncode
    status |= code != 0
    print("Resultado:", "correcto" if status == 0 else "con errores")
    return 1 if status else 0


if __name__ == "__main__":
    sys.exit(main())
