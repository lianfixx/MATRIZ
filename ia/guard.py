#!/usr/bin/env python3
"""Reglas comunes para cualquier IA o persona que trabaje en este repositorio.

Una sola política (`ia/politica.json`) y tres puntos de aplicación:

1. Claude Code: hook PreToolUse (`.claude/settings.json`) → este archivo por stdin.
2. Cualquier IA o persona con copia local: hooks de git (`ia/githooks/`, instalar con
   `sh ia/instalar.sh`) → `ia/verificar.py precommit|prepush`.
3. GitHub Actions (`.github/workflows/registro-ia.yml`) → `ia/verificar.py ci`, que revisa
   también lo que se sube por API o conectores (ChatGPT, Gemini, web), con las reglas de la base.

Respuesta en modo hook: `deny`, `ask` o nada (flujo normal de permisos). Solo usa la
biblioteca estándar y no envía datos a ningún servicio.

Tipos de regla (`rules`, se evalúan todas; gana la más estricta: deny > ask > nada):
- `pattern`: `tool` (regex sobre el nombre de la herramienta) y opcionalmente `input`
  (regex sobre `field` de tool_input, o sobre todo tool_input en JSON).
- `path`: `tool` y `globs` relativos a la raíz (sin distinguir mayúsculas); `only_existing`.
- `recipients`: `tool` y `allow`; deniega destinatarios fuera de la lista; `forbid_cc` deniega
  CC/CCO; pregunta si no hay destinatarios visibles, si se responde a todos o se envía un borrador.
- `git`: `git` (subcomando) y `flags` (regex que deben coincidir con un argumento completo) o
  `args` (regex sobre los argumentos unidos). Lee el comando respetando comillas, saltos de línea,
  `bash -c`, `env`, `time` y opciones globales de git.
- `before_git`: corre `run` antes de `git commit|push`; `staged_regex` limita a ciertos archivos
  (`{dir}` = grupo 1); `requires` comprueba dependencias (si faltan, pregunta).
- `secrets`: busca secretos y, con `pii`, CURP y tarjetas válidas (Luhn) en el diff.
- `registro`: cada commit que cambie archivos actualiza un registro de `registro.logs`; si el
  log tiene `require`, lo añadido debe contenerlo; `only_added` cuenta solo archivos nuevos.
- `inmutable`: `paths` (regex); deniega modificar, borrar o renombrar archivos ya versionados.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

RANK = {None: 0, "ask": 1, "deny": 2}
GIT_TIME = {"before_git", "secrets", "registro", "inmutable"}
COMMIT_TIME_EVERYWHERE = {"secrets", "registro", "inmutable"}  # también en pre-push y CI
SEND_TOOL = re.compile(r"(send|reply|forward|draft|publish|post)", re.I)
RECIPIENT_KEYS = {"to", "cc", "bcc", "recipient", "recipients", "torecipients",
                  "ccrecipients", "bccrecipients", "forward_to", "forwardto", "addresses"}
CC_KEYS = {"cc", "bcc", "ccrecipients", "bccrecipients"}
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
SECRET_PATTERNS = [
    ("clave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("token de Meta", re.compile(r"\bEAA[A-Za-z0-9]{40,}")),
    ("clave OpenAI/Anthropic", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{24,}")),
    ("token de GitHub", re.compile(r"\b(?:ghp|gho|ghs|ghu|github_pat)_[A-Za-z0-9_]{20,}")),
    ("clave de Google", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("secreto OAuth de Google", re.compile(r"\bGOCSPX-[A-Za-z0-9_\-]{20,}")),
    ("clave AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("token de Slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("asignación de secreto", re.compile(
        r"(?i)(?:^|[^A-Za-z0-9])(?:api[_-]?key|client[_-]?secret|secret|token|password|passwd|contraseña)"
        r"\s*[:=]\s*['\"]?(?!\$|os\.|process\.|\{\{|<|env\b)[^'\"\s]{12,}")),
]
CURP = re.compile(r"\b[A-Z][AEIOUX][A-Z]{2}\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])[HM][A-Z]{2}[B-DF-HJ-NP-TV-Z]{3}[A-Z\d]\d\b")
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
NESTED = "IA_GUARD_NESTED"  # evita que un control previo a commit vuelva a disparar estas reglas
PREFIXES = {"command", "exec", "sudo", "env", "time", "nohup", "then", "do", "else", "elif", "{", "}", "!",
            "xargs", "if", "while", "until"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}
COMMIT_OPTS_WITH_VALUE = {"-m", "--message", "-F", "--file", "-C", "--reuse-message", "-c", "--reedit-message",
                          "--author", "--date", "--fixup", "--squash", "-t", "--template", "--cleanup",
                          "--trailer", "-S", "--gpg-sign", "--pathspec-from-file"}


# ---------------------------------------------------------------- utilidades
def luhn(digits: str) -> bool:
    nums = [int(c) for c in digits][::-1]
    total = sum(n if i % 2 == 0 else (n * 2 - 9 if n * 2 > 9 else n * 2) for i, n in enumerate(nums))
    return total % 10 == 0


def repo_root(prefer_env: bool = True, start: Path | None = None) -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if prefer_env and env:
        return Path(env)
    for cwd in ([start] if start else []) + [Path.cwd(), Path(__file__).resolve().parent]:
        try:
            out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                                 cwd=cwd, timeout=30)
            if out.returncode == 0:
                return Path(out.stdout.strip())
        except (OSError, subprocess.TimeoutExpired):
            continue
    return Path(__file__).resolve().parents[1]


def load_policy(root: Path, path: Path | None = None) -> dict:
    return json.loads((path or root / "ia" / "politica.json").read_text(encoding="utf-8"))


def child_env() -> dict:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    env[NESTED] = "1"
    return env


def run(cmd: str, root: Path, timeout: int = 900) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=timeout,
                              env=child_env(), encoding="utf-8", errors="replace")
        return proc.returncode, (proc.stdout + proc.stderr)[-3000:]
    except subprocess.TimeoutExpired:
        return 1, f"Tiempo agotado ({timeout} s) al ejecutar: {cmd}"


def git_out(args: str, root: Path) -> str:
    proc = subprocess.run("git -c core.quotePath=false " + args, shell=True, cwd=root, capture_output=True,
                          text=True, timeout=300, encoding="utf-8", errors="replace")
    return proc.stdout


def _tokens(command: str) -> list[str]:
    try:
        lex = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=";&|()")
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        return command.replace("\n", " ; ").split()


def git_segments(command: str, depth: int = 0) -> list[list[str]]:
    """Devuelve los argumentos (subcomando incluido) de cada invocación de git en un comando."""
    segments, current = [], []
    for tok in _tokens(command):
        if tok and set(tok) <= set(";&|()"):
            segments.append(current)
            current = []
        else:
            current.append(tok)
    segments.append(current)
    found = []
    for seg in segments:
        while seg and (seg[0] in PREFIXES or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", seg[0])):
            seg = seg[1:]
        if seg and depth < 3 and Path(seg[0]).name in ("bash", "sh", "zsh", "dash") and "-c" in seg:
            i = seg.index("-c")
            if i + 1 < len(seg):
                found.extend(git_segments(seg[i + 1], depth + 1))
            continue
        if seg and Path(seg[0]).name == "git":
            rest, globals_ = seg[1:], []
            while rest and rest[0].startswith("-"):
                opt = rest[0]
                take = 2 if opt in GIT_OPTS_WITH_VALUE else 1
                globals_.extend(rest[:take])
                rest = rest[take:]
            if rest:
                found.append(rest + ["\0globals"] + globals_)
    return found


def git_calls(command: str, sub: str) -> list[tuple[list[str], list[str]]]:
    out = []
    for item in git_segments(command):
        sep = item.index("\0globals")
        rest, globals_ = item[:sep], item[sep + 1:]
        if rest[0] == sub:
            out.append((rest[1:], globals_))
    return out


def git_call(command: str, sub: str) -> list[str] | None:
    calls = git_calls(command, sub)
    return calls[0][0] if calls else None


def commit_pathspecs(args: list[str]) -> list[str]:
    paths, i = [], 0
    while i < len(args):
        a = args[i]
        if a == "--":
            paths.extend(args[i + 1:])
            break
        if a in COMMIT_OPTS_WITH_VALUE or (a.startswith("-") and not a.startswith("--") and len(a) > 2 and a[-1] in "mFCctS"):
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        paths.append(a)
        i += 1
    return paths


def collect_recipients(value, key=None, out=None, cc=None):
    out = [] if out is None else out
    cc = [] if cc is None else cc
    if isinstance(value, dict):
        for k, v in value.items():
            collect_recipients(v, k, out, cc)
    elif isinstance(value, list):
        for item in value:
            collect_recipients(item, key, out, cc)
    elif isinstance(value, str) and key is not None:
        k = key.lower()
        if k in RECIPIENT_KEYS or "recipient" in k:
            found = EMAIL.findall(value)
            out.extend(found)
            if k in CC_KEYS or k.startswith(("cc", "bcc")):
                cc.extend(found)
    return out, cc


def scan_secrets(diff: str, pii: bool) -> list[str]:
    hits, current, line_no = [], "?", 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else line[4:]
            continue
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
        if m:
            line_no = int(m.group(1)) - 1
            continue
        if line.startswith("+"):
            line_no += 1
            text = line[1:]
            for label, pat in SECRET_PATTERNS:
                if pat.search(text):
                    hits.append(f"{current}:{line_no} ({label})")
            if pii:
                if CURP.search(text):
                    hits.append(f"{current}:{line_no} (posible CURP)")
                for cand in CARD.findall(text):
                    digits = re.sub(r"\D", "", cand)
                    if 13 <= len(digits) <= 19 and luhn(digits) and len(set(digits)) > 2:
                        hits.append(f"{current}:{line_no} (posible número de tarjeta)")
        elif not line.startswith("-"):
            line_no += 1
    return hits


# ---------------------------------------------------------- contexto de git
class Changes:
    """Cambios a revisar: staged (o commit -a / --amend), push o un rango (CI y pre-push)."""

    def __init__(self, root: Path, mode: str, command: str = "", base: str | None = None, head: str | None = None):
        self.root, self.mode, self.command, self.base, self.head = root, mode, command, base, head
        self._status = self._diff = None

    def _range(self) -> str:
        if self.base and self.head:
            return f"{self.base} {self.head}"
        if self.mode == "push":
            up = git_out("rev-parse --verify --quiet @{upstream}", self.root).strip()
            return f"{up} HEAD" if up else "HEAD~1 HEAD"
        args = git_call(self.command, "commit") or []
        flags = [a for a in args if a.startswith("-") and not a.startswith("--")]
        if "--amend" in args:
            parent = git_out("rev-parse --verify --quiet HEAD~1", self.root).strip() or EMPTY_TREE
            return f"--cached {parent}"
        if "--all" in args or any("a" in f[1:] for f in flags if f not in ("-m", "-F", "-C", "-c", "-t")):
            return "HEAD"
        return "--cached"

    def status(self) -> list[tuple[str, str]]:
        if self._status is None:
            out = git_out(f"diff --no-renames --name-status {self._range()}", self.root)
            self._status = [(l.split("\t", 1)[0][:1], l.split("\t", 1)[1]) for l in out.splitlines() if "\t" in l]
        return self._status

    def files(self) -> list[str]:
        return [p for _, p in self.status()]

    def diff(self, paths: list[str] | None = None) -> str:
        if self._diff is None or paths:
            spec = (" -- " + " ".join(shlex.quote(p) for p in paths)) if paths else ""
            text = git_out(f"diff --no-color --no-ext-diff --no-textconv --unified=0 {self._range()}{spec}", self.root)
            if paths:
                return text
            self._diff = text
        return self._diff

    def commits(self) -> list["Changes"]:
        """Un Changes por commit (sin merges) del rango; para el registro «en el mismo commit»."""
        if not (self.base and self.head):
            return [self]
        base = "" if self.base == EMPTY_TREE else f"{self.base}.."
        shas = git_out(f"rev-list --no-merges --reverse {base}{self.head}", self.root).split()
        out = []
        for sha in shas:
            parent = git_out(f"rev-parse --verify --quiet {sha}^", self.root).strip() or EMPTY_TREE
            out.append(Changes(self.root, "ci", base=parent, head=sha))
        return out


def check_registro(policy: dict, changes: Changes) -> str | None:
    cfg = policy.get("registro") or {}
    logs = cfg.get("logs") or []
    status = changes.status()
    if not logs or not status:
        return None
    exentos = [re.compile(p) for p in cfg.get("exentos", [])]
    relevant = [(s, f) for s, f in status if not any(p.search(f) for p in exentos)]
    if not relevant:
        return None
    touched = []
    for s, f in relevant:
        for log in logs:
            if re.search(log["path"], f) and (not log.get("only_added") or s == "A"):
                touched.append((f, log.get("require")))
                break
    label = f" (commit {changes.head[:10]})" if changes.head and changes.mode == "ci" else ""
    if not touched:
        names = ", ".join(l["path"] for l in logs)
        return (f"Falta el registro del cambio{label}. Todo cambio, lo haga la IA que lo haga, debe actualizar en el "
                f"mismo commit uno de estos registros: {names}. Formato en ia/PROTOCOLO.md.")
    if len(touched) == len(relevant):
        return None  # solo se editan registros
    for f, req in touched:
        if not req:
            return None
        added = "\n".join(l for l in changes.diff([f]).splitlines() if l.startswith("+") and not l.startswith("+++"))
        if req in added:
            return None
    req = next(r for _, r in touched if r)
    return f"La entrada nueva del registro{label} debe incluir «{req}» (qué IA o persona hizo el cambio). Formato en ia/PROTOCOLO.md."


def check_inmutable(rule: dict, changes: Changes) -> str | None:
    bad = [f"{s} {f}" for s, f in changes.status() if s in ("M", "D") and re.search(rule["paths"], f)]
    if bad:
        return f"{rule['reason']} Cambios no permitidos: {', '.join(bad[:10])}."
    return None


# --------------------------------------------------------------- evaluación
def evaluate(event: dict, policy: dict, root: Path, changes: Changes | None = None,
             skip_git_time: bool = False, hooks_installed: bool = False) -> tuple[str | None, list[str]]:
    tool = event.get("tool_name", "")
    tinput = event.get("tool_input") or {}
    command = tinput.get("command", "") if isinstance(tinput, dict) else ""
    decision, reasons = None, []
    if os.environ.get(NESTED):
        skip_git_time = True

    def hit(dec: str, reason: str):
        nonlocal decision
        if RANK[dec] > RANK[decision]:
            decision = dec
        if reason not in reasons:
            reasons.append(reason)

    # En Claude Code el hook corre antes del comando entero: solo ve lo que ya está preparado.
    if changes is None and tool == "Bash" and not hooks_installed and git_call(command, "commit") is not None:
        args = git_call(command, "commit")
        add_before = any(git_calls(command, sub) for sub in ("add", "rm", "mv"))
        if add_before or commit_pathspecs(args):
            hit("deny", "Haz `git add` (o `git rm`) en un comando aparte y luego `git commit` sin rutas, para que se "
                        "revisen exactamente los cambios del commit. Alternativa: `sh ia/instalar.sh` activa los hooks de git.")

    for rule in policy.get("rules", []):
        kind = rule.get("type", "pattern")
        if kind in GIT_TIME:
            sub = rule.get("git", "commit")
            if skip_git_time:
                continue
            if changes is None:  # hook de Claude Code: solo cuando el comando es ese git
                if tool != "Bash" or git_call(command, sub) is None:
                    continue
                ctxs = [Changes(root, "push" if sub == "push" else "commit", command)]
                if sub == "push" and kind in COMMIT_TIME_EVERYWHERE:
                    continue
            elif changes.mode == "ci":  # CI y pre-push: registro, secretos e inmutables por rango
                if kind == "before_git" or (kind == "secrets" and sub == "push"):
                    continue
                ctxs = changes.commits() if kind == "registro" else [changes]
            else:  # hooks de git: fase commit o push
                if (changes.mode == "push") != (sub == "push"):
                    continue
                ctxs = [changes]
            for ctx in ctxs:
                if kind == "registro":
                    msg = check_registro(policy, ctx)
                    if msg:
                        hit("deny", msg)
                elif kind == "inmutable":
                    msg = check_inmutable(rule, ctx)
                    if msg:
                        hit("deny", msg)
                elif kind == "secrets":
                    found = scan_secrets(ctx.diff(), rule.get("pii", False))
                    if found:
                        shown = "; ".join(found[:15]) + ("…" if len(found) > 15 else "")
                        hit("deny", f"{rule['reason']} Revisar: {shown}. Si es un falso positivo, explícalo a Emi y que decida.")
                else:  # before_git
                    dirs = [""]
                    if rule.get("staged_regex"):
                        rx = re.compile(rule["staged_regex"])
                        matches = [m for m in (rx.search(f) for f in ctx.files()) if m]
                        if not matches:
                            continue
                        if "{dir}" in rule["run"]:
                            dirs = sorted({m.group(1) for m in matches if m.groups() and m.group(1)}) or [""]
                    if rule.get("requires"):
                        code, _ = run(rule["requires"], root, 60)
                        if code != 0:
                            hit("ask", f"{rule['reason']} No se pudo ejecutar el control porque faltan dependencias "
                                       f"(`{rule['requires']}`). Instálalas o confirma que aceptas continuar sin él.")
                            continue
                    for d in dirs:
                        cmd = rule["run"].replace("{dir}", d)
                        code, out = run(cmd, root, rule.get("timeout", 900))
                        if code != 0:
                            hit("deny", f"{rule['reason']} Falló `{cmd}` (código {code}).\n{out}")
                            break
            continue

        if changes is not None:
            continue  # en git/CI solo aplican las reglas de momento de commit/push
        if kind == "hookspath":  # cambiar o anular los hooks de git, salvo la instalación oficial
            if tool != "Bash":
                continue
            for item in git_segments(command):
                sep = item.index("\0globals")
                rest, globals_ = item[:sep], item[sep + 1:]
                override = any(g.lower().startswith("core.hookspath") for g in globals_)
                config = rest[0] == "config" and any(a.lower() == "core.hookspath" or a.lower().startswith("core.hookspath=")
                                                    for a in rest[1:])
                official = rest[0] == "config" and rest[1:] == ["core.hooksPath", "ia/githooks"]
                if (override or config) and not official and not (rest[0] == "config" and "--get" in rest):
                    hit(rule.get("decision", "deny"), rule["reason"])
            continue
        if kind == "git":
            if tool != "Bash":
                continue
            for args, _globals in git_calls(command, rule["git"]):
                if rule.get("flags"):
                    if not any(re.fullmatch(f, a) for a in args for f in rule["flags"]):
                        continue
                elif rule.get("args") and not re.search(rule["args"], " " + " ".join(args) + " "):
                    continue
                hit(rule["decision"], rule["reason"])
            continue
        if not re.fullmatch(rule.get("tool", ".*"), tool):
            continue
        if kind == "pattern":
            field = rule.get("field")
            target = tinput.get(field, "") if field and isinstance(tinput, dict) else json.dumps(tinput, ensure_ascii=False)
            if not isinstance(target, str):
                target = json.dumps(target, ensure_ascii=False)
            pat = rule.get("input")
            if pat is None or re.search(pat, target, re.I | re.S):
                hit(rule["decision"], rule["reason"])
        elif kind == "path":
            raw = (tinput.get("file_path") or tinput.get("notebook_path") or tinput.get("path") or "") if isinstance(tinput, dict) else ""
            if not raw:
                continue
            p = Path(raw)
            p = p if p.is_absolute() else root / p
            try:
                rel = p.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                continue
            if any(fnmatch.fnmatch(rel.lower(), g.lower()) for g in rule["globs"]):
                if rule.get("only_existing") and not p.exists():
                    continue
                hit(rule["decision"], f"{rule['reason']} ({rel})")
        elif kind == "recipients":
            found, cc = collect_recipients(tinput)
            allow = {a.lower() for a in rule.get("allow", [])}
            outside = sorted({f for f in found if f.lower() not in allow})
            flat = json.dumps(tinput).lower() if isinstance(tinput, dict) else ""
            if outside:
                hit("deny", f"{rule['reason']} Destinatarios no permitidos: {', '.join(outside)}.")
            elif rule.get("forbid_cc") and cc:
                hit("deny", f"{rule['reason']} No se permiten CC/CCO.")
            elif re.search(r'"(reply_?all|replyall)":\s*true', flat):
                hit("ask", f"{rule['reason']} «Responder a todos» puede incluir destinatarios no permitidos; confirma la lista real.")
            elif re.search(r'"draft_?id"', flat):
                hit("ask", f"{rule['reason']} Se envía un borrador cuyos destinatarios no se ven aquí; confirma que va solo a destinatarios permitidos.")
            elif not found and rule.get("ask_if_unknown", True):
                hit("ask", f"{rule['reason']} No se pudieron identificar destinatarios; confirma antes de continuar.")
    return decision, reasons


def git_hooks_installed(root: Path) -> bool:
    if os.environ.get("IA_GUARD_ASSUME_NO_HOOKS"):  # solo pruebas: evaluar como copia sin hooks de git
        return False
    return git_out("config --get core.hooksPath", root).strip().rstrip("/") == "ia/githooks"


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return 0
    root = repo_root()
    try:
        # Con los hooks de git instalados, ellos aplican las reglas de commit/push; no duplicar.
        installed = git_hooks_installed(root)
        decision, reasons = evaluate(event, load_policy(root), root, skip_git_time=installed, hooks_installed=installed)
        reason = "\n".join(reasons)
    except Exception as exc:  # un error del freno no bloquea todo, salvo envíos y commits
        name = event.get("tool_name", "")
        command = (event.get("tool_input") or {}).get("command", "") if isinstance(event.get("tool_input"), dict) else ""
        if (name.startswith("mcp__") and SEND_TOOL.search(name)) or re.search(r"\bgit\b.*\b(commit|push)\b", command):
            decision, reason = "ask", f"El freno falló ({exc}); confirma esta acción manualmente."
        else:
            print(f"guard.py: error interno ignorado: {exc}", file=sys.stderr)
            return 0
    if decision:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
