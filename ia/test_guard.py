#!/usr/bin/env python3
"""Pruebas de las reglas comunes (ia/). Uso: python3 ia/test_guard.py

- PolicyCases: casos declarados en `ia/politica.json` → `tests` (decisión esperada del hook).
- GenericRules: cada tipo de regla en un repositorio temporal.
- GitAndCI: hooks de git y modo CI de verificar.py, como los usaría cualquier IA.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PY = sys.executable


def call(event: dict, root: Path, nested: bool = False, assume_no_hooks: bool = False) -> str:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
    env.pop("IA_GUARD_NESTED", None)
    env.pop("IA_GUARD_ASSUME_NO_HOOKS", None)
    if assume_no_hooks:
        env["IA_GUARD_ASSUME_NO_HOOKS"] = "1"
    if nested:
        env["IA_GUARD_NESTED"] = "1"
    out = subprocess.run([PY, str(root / "ia" / "guard.py")], input=json.dumps(event), text=True,
                         capture_output=True, env=env, timeout=900).stdout.strip()
    if not out:
        return "none"
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"]


class PolicyCases(unittest.TestCase):
    def test_declared_cases(self):
        policy = json.loads((HERE / "politica.json").read_text(encoding="utf-8"))
        cases = policy.get("tests", [])
        self.assertTrue(cases, "politica.json debe declarar casos en `tests`")
        for case in cases:
            with self.subTest(case=case["name"]):
                event = {"hook_event_name": "PreToolUse", "tool_name": case["tool"], "tool_input": case["input"]}
                self.assertEqual(call(event, ROOT, nested=True, assume_no_hooks=True), case["expect"])

    def test_reglas_md_al_dia(self):
        code = subprocess.run([PY, str(HERE / "verificar.py"), "reglas", "--check"], cwd=ROOT).returncode
        self.assertEqual(code, 0, "ia/REGLAS.md está desactualizado")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "ia").mkdir()
        for f in ("guard.py", "verificar.py", "check_skill.py"):
            shutil.copy2(HERE / f, self.root / "ia" / f)
        self.sh("git init -q -b main && git config user.email t@t && git config user.name t")

    def tearDown(self):
        self.tmp.cleanup()

    def sh(self, cmd, **kw):
        return subprocess.run(cmd, shell=True, cwd=self.root, capture_output=True, text=True, **kw)

    def policy(self, rules, registro=None):
        data = {"rules": rules}
        if registro:
            data["registro"] = registro
        (self.root / "ia" / "politica.json").write_text(json.dumps(data), encoding="utf-8")

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def bash(self, command):
        return call({"tool_name": "Bash", "tool_input": {"command": command}}, self.root)


class GenericRules(Base):
    def test_secret_scan_blocks_commit(self):
        self.policy([{"type": "secrets", "git": "commit", "pii": True, "reason": "Secreto."}])
        self.write("a.txt", "token = 'EAA" + "B" * 50 + "'\n")
        self.sh("git add a.txt")
        self.assertEqual(self.bash("git commit -m x"), "deny")
        self.assertEqual(self.bash("git status"), "none")

    def test_secret_scan_allows_clean_commit(self):
        self.policy([{"type": "secrets", "git": "commit", "pii": True, "reason": "Secreto."}])
        self.write("a.txt", "hola\n")
        self.sh("git add a.txt")
        self.assertEqual(self.bash("git -C . commit -m x"), "none")

    def test_curp_and_card(self):
        self.policy([{"type": "secrets", "git": "commit", "pii": True, "reason": "PII."}])
        curp, card = "GAMY900101" + "HDFRLH09", " ".join(["4111"] * 4)  # armados en ejecución
        self.write("b.txt", f"{curp}\n{card}\n")
        self.sh("git add b.txt")
        self.assertEqual(self.bash("git commit -m x"), "deny")

    def test_commit_all_scans_unstaged(self):
        self.policy([{"type": "secrets", "git": "commit", "reason": "Secreto."}])
        self.write("a.txt", "x\n")
        self.sh("git add a.txt && git commit -qm base")
        self.write("a.txt", "x\nghp_" + "a" * 30 + "\n")
        self.assertEqual(self.bash("git commit -am cambio"), "deny")

    def test_before_git_runs_check(self):
        self.policy([{"type": "before_git", "git": "commit", "run": "exit 3", "reason": "Pruebas."}])
        self.assertEqual(self.bash("cd x && git commit -m y"), "deny")
        self.policy([{"type": "before_git", "git": "commit", "run": "true", "reason": "Pruebas."}])
        self.assertEqual(self.bash("git commit -m y"), "none")

    def test_staged_regex_alternatives_without_group(self):
        self.policy([{"type": "before_git", "git": "commit", "staged_regex": r"^(skills|tests)/|^PUBLIC\.json$",
                      "run": "exit 3", "reason": "Pruebas."}])
        self.write("PUBLIC.json", "{}")
        self.sh("git add PUBLIC.json")
        self.assertEqual(self.bash("git commit -m y"), "deny")

    def test_missing_dependency_asks(self):
        self.policy([{"type": "before_git", "git": "commit", "requires": "exit 1", "run": "exit 3", "reason": "Pruebas."}])
        self.assertEqual(self.bash("git commit -m y"), "ask")

    def test_staged_regex_dir_substitution(self):
        self.policy([{"type": "before_git", "git": "commit", "staged_regex": "^temas/([^/]+)/",
                      "run": "test {dir} = uno", "reason": "Validador."}])
        self.write("temas/uno/x.md", "x")
        self.sh("git add .")
        self.assertEqual(self.bash("git commit -m y"), "none")
        self.write("temas/dos/x.md", "x")
        self.sh("git add .")
        self.assertEqual(self.bash("git commit -m y"), "deny")

    def test_path_only_existing(self):
        self.policy([{"type": "path", "tool": "Edit|Write", "globs": ["versiones/*/*"], "only_existing": True,
                      "decision": "deny", "reason": "Inmutable."}])
        self.write("versiones/1/a.json", "{}")
        ev = lambda p: call({"tool_name": "Write", "tool_input": {"file_path": str(self.root / p)}}, self.root)
        self.assertEqual(ev("versiones/1/a.json"), "deny")
        self.assertEqual(ev("versiones/2/a.json"), "none")

    def test_recipients(self):
        self.policy([{"type": "recipients", "tool": "mcp__.*Gmail.*__send_message", "allow": ["yo@x.mx"],
                      "forbid_cc": True, "reason": "Solo a mí."}])
        send = lambda i: call({"tool_name": "mcp__Gmail__send_message", "tool_input": i}, self.root)
        self.assertEqual(send({"to": ["yo@x.mx"], "body": "copia a otro@x.mx"}), "none")
        self.assertEqual(send({"to": "Otro <otro@x.mx>"}), "deny")
        self.assertEqual(send({"to": ["yo@x.mx"], "cc": ["yo@x.mx"]}), "deny")
        self.assertEqual(send({"threadId": "abc"}), "ask")

    def test_git_rules_respect_quotes(self):
        self.policy([
            {"type": "git", "git": "push", "decision": "ask", "reason": "a"},
            {"type": "git", "git": "push", "flags": [r"--force.*", r"--mirror", r"--delete", r"-[a-zA-Z]*[fd][a-zA-Z]*", r"\+.+", r":.*"], "decision": "deny", "reason": "b"},
        ])
        self.assertEqual(self.bash("git push origin main"), "ask")
        self.assertEqual(self.bash("git -C repo push --force origin main"), "deny")
        self.assertEqual(self.bash("git push origin +main"), "deny")
        self.assertEqual(self.bash("git commit -m 'no hagas git push --force'"), "none")
        self.assertEqual(self.bash("echo listo && git push -u origin rama"), "ask")
        for cmd in ("echo a\ngit push -f", "bash -c 'git push --force'", "env X=1 time git --git-dir .git push +main",
                    "if true; then git push origin :main; fi", "{ git push --mirror; }", "git push -fu origin main"):
            self.assertEqual(self.bash(cmd), "deny", cmd)

    def test_staging_and_pathspecs(self):
        self.policy([{"type": "secrets", "git": "commit", "reason": "Secreto."}])
        self.assertEqual(self.bash("git add -A && git commit -m x"), "deny")
        self.assertEqual(self.bash("git commit -m x a.txt"), "deny")
        self.assertEqual(self.bash("git commit -am 'mensaje con espacios'"), "none")
        self.sh("git config core.hooksPath ia/githooks")
        self.assertEqual(self.bash("git add -A && git commit -m x"), "none")  # lo revisa el hook de git

    def test_amend_compara_con_el_padre(self):
        self.policy([{"type": "registro", "git": "commit", "reason": "R"}], REGISTRO)
        self.write("CHANGELOG.md", "# C\n")
        self.sh("git add -A && git commit -qm base")
        self.write("a.txt", "x\n")
        self.write("CHANGELOG.md", "# C\n- Agente: Codex\n")
        self.sh("git add -A && git commit -qm con-registro")
        self.write("a.txt", "y\n")
        self.sh("git add a.txt")
        self.assertEqual(self.bash("git commit --amend --no-edit"), "none")
        self.assertEqual(self.bash("git commit -m otro"), "deny")

    def test_inmutable_y_registro_solo_altas(self):
        reg = {"logs": [{"path": r"^CHANGELOG\.md$", "require": "Agente:"}, {"path": r"^versiones/", "only_added": True}]}
        self.policy([{"type": "registro", "git": "commit", "reason": "R"},
                     {"type": "inmutable", "git": "commit", "paths": r"^versiones/", "reason": "Inmutable."}], reg)
        self.write("versiones/1/a.json", "{}")
        self.write("CHANGELOG.md", "# C\n")
        self.sh("git add -A && git commit -qm base")
        self.write("versiones/2/Notificación.pdf", "x")  # nombre con acento
        self.write("codigo.py", "x = 1\n")
        self.sh("git add -A")
        self.assertEqual(self.bash("git commit -m entrega"), "none")
        self.sh("git commit -qm entrega")
        self.sh("git rm -q versiones/1/a.json")
        self.write("codigo.py", "x = 2\n")
        self.sh("git add -A")
        self.assertEqual(self.bash("git commit -m borra"), "deny")

    def test_archivo_no_utf8_no_desactiva_controles(self):
        self.policy([{"type": "secrets", "git": "commit", "reason": "Secreto."}])
        (self.root / "datos.csv").write_bytes("nombre;Peña\n".encode("cp1252"))
        self.write("a.txt", "ghp_" + "a" * 30 + "\n")
        self.sh("git add -A")
        self.assertEqual(self.bash("git commit -m x"), "deny")

    def test_secretos_con_guion_bajo(self):
        sys.path.insert(0, str(self.root / "ia"))
        import importlib, guard as g
        importlib.reload(g)
        k1, k2 = "GMAIL_CLIENT_" + "SECRET", "DB_" + "PASSWORD"  # armados en ejecución: el repo no guarda ejemplos con forma real
        diff = f'+++ b/x\n@@ -0,0 +1,3 @@\n+{k1}="{"abcdefgh" * 2}12"\n+{k2}={"supersecreto" + "123456"}\n+token: ${{{{ secrets.X }}}}\n'
        hits = g.scan_secrets(diff, False)
        self.assertEqual(len(hits), 2, hits)

    def test_responder_a_todos_y_borrador(self):
        self.policy([{"type": "recipients", "tool": "mcp__.*Gmail.*", "allow": ["yo@x.mx"], "reason": "Solo a mí."}])
        send = lambda name, i: call({"tool_name": name, "tool_input": i}, self.root)
        self.assertEqual(send("mcp__Gmail__reply", {"to": ["yo@x.mx"], "replyAll": True}), "ask")
        self.assertEqual(send("mcp__Gmail__send_message", {"to": ["yo@x.mx"], "draftId": "d1"}), "ask")

    def test_ruta_en_mayusculas(self):
        self.policy([{"type": "path", "tool": "Write", "globs": ["versiones/*/*"], "only_existing": False,
                      "decision": "deny", "reason": "Inmutable."}])
        self.assertEqual(call({"tool_name": "Write", "tool_input": {"file_path": "VERSIONES/3/a.md"}}, self.root), "deny")

    def test_broken_policy_does_not_block(self):
        (self.root / "ia" / "politica.json").write_text("{", encoding="utf-8")
        self.assertEqual(self.bash("ls"), "none")
        self.assertEqual(call({"tool_name": "mcp__Gmail__send_message", "tool_input": {}}, self.root), "ask")


REGISTRO = {"logs": [{"path": r"(^|/)CHANGELOG\.md$", "require": "Agente:"}, {"path": r"^OPERACION\.json$"}],
            "exentos": [r"^\.gitignore$"]}


class Registro(Base):
    def setUp(self):
        super().setUp()
        self.policy([{"type": "registro", "git": "commit", "reason": "Registro."}], REGISTRO)
        self.write("CHANGELOG.md", "# Cambios\n")
        self.write("a.txt", "x\n")
        self.sh("git add -A && git commit -qm base")

    def test_commit_sin_registro(self):
        self.write("a.txt", "y\n")
        self.sh("git add a.txt")
        self.assertEqual(self.bash("git commit -m y"), "deny")

    def test_registro_sin_agente(self):
        self.write("a.txt", "y\n")
        self.write("CHANGELOG.md", "# Cambios\n\n## 2026-11-04 · algo\n")
        self.sh("git add -A")
        self.assertEqual(self.bash("git commit -m y"), "deny")

    def test_registro_completo(self):
        self.write("a.txt", "y\n")
        self.write("CHANGELOG.md", "# Cambios\n\n## 2026-11-04 · algo\n- Agente: Codex\n")
        self.sh("git add -A")
        self.assertEqual(self.bash("git commit -m y"), "none")

    def test_log_sin_requisito(self):
        self.write("a.txt", "y\n")
        self.write("OPERACION.json", "{}\n")
        self.sh("git add -A")
        self.assertEqual(self.bash("git commit -m y"), "none")

    def test_exento_y_solo_registro(self):
        self.write(".gitignore", "x\n")
        self.sh("git add -A")
        self.assertEqual(self.bash("git commit -m y"), "none")
        self.sh("git commit -qm ign")
        self.write("CHANGELOG.md", "# Cambios\n\ncorrección\n")
        self.sh("git add -A")
        self.assertEqual(self.bash("git commit -m y"), "none")


class GitAndCI(Base):
    def setUp(self):
        super().setUp()
        self.policy([{"type": "registro", "git": "commit", "reason": "Registro."},
                     {"type": "secrets", "git": "commit", "reason": "Secreto."}], REGISTRO)
        self.write("CHANGELOG.md", "# Cambios\n")
        self.sh("git add -A && git commit -qm base")

    def verificar(self, *args, stdin=""):
        env = {k: v for k, v in os.environ.items() if k != "IA_GUARD_NESTED"}
        return subprocess.run([PY, "ia/verificar.py", *args], cwd=self.root, input=stdin,
                              capture_output=True, text=True, timeout=600, env=env)

    def test_precommit_hook(self):
        self.write("a.txt", "y\n")
        self.sh("git add a.txt")
        self.assertEqual(self.verificar("precommit").returncode, 1)
        self.write("CHANGELOG.md", "# Cambios\n- Agente: Gemini CLI\n")
        self.sh("git add -A")
        self.assertEqual(self.verificar("precommit").returncode, 0)

    def test_ci_range(self):
        base = self.sh("git rev-parse HEAD").stdout.strip()
        self.write("a.txt", "y\n")
        self.sh("git add -A && git commit -qm sin-registro --no-verify")
        head = self.sh("git rev-parse HEAD").stdout.strip()
        (self.root / "ia" / "REGLAS.md").unlink(missing_ok=True)
        self.verificar("reglas")
        self.sh("git add -A && git commit -qm reglas --no-verify")
        head = self.sh("git rev-parse HEAD").stdout.strip()
        self.assertEqual(self.verificar("ci", "--base", base, "--head", head).returncode, 1)
        mid = head
        self.write("CHANGELOG.md", "# Cambios\n- Agente: ChatGPT (conector GitHub)\n")
        self.sh("git add -A && git commit -qm registro --no-verify")
        head = self.sh("git rev-parse HEAD").stdout.strip()
        # el registro va en el mismo commit: un commit posterior no subsana el anterior
        self.assertEqual(self.verificar("ci", "--base", base, "--head", head).returncode, 1)
        self.assertEqual(self.verificar("ci", "--base", mid, "--head", head).returncode, 0)
        self.assertEqual(self.verificar("ci", "--base", "0" * 40, "--head", head).returncode, 0)

    def test_ci_usa_politica_de_la_base(self):
        base = self.sh("git rev-parse HEAD").stdout.strip()
        self.sh(f"git show {base}:ia/politica.json > ../politica_base.json")
        (self.root / "ia" / "politica.json").write_text(json.dumps({"rules": []}), encoding="utf-8")
        self.verificar("reglas")
        self.write("a.txt", "ghp_" + "a" * 30 + "\n")
        self.sh("git add -A && git commit -qm quita-reglas --no-verify")
        head = self.sh("git rev-parse HEAD").stdout.strip()
        self.assertEqual(self.verificar("ci", "--base", base, "--head", head).returncode, 0)  # con la política nueva
        self.assertEqual(self.verificar("ci", "--base", base, "--head", head, "--politica", "../politica_base.json").returncode, 1)

    def test_prepush_revisa_registro(self):
        base = self.sh("git rev-parse HEAD").stdout.strip()
        self.write("a.txt", "y\n")
        self.sh("git add -A && git commit -qm sin-registro --no-verify")
        head = self.sh("git rev-parse HEAD").stdout.strip()
        line = f"refs/heads/main {head} refs/heads/main {base}\n"
        self.assertEqual(self.verificar("prepush", stdin=line).returncode, 1)
        line_new = f"refs/heads/nueva {head} refs/heads/nueva {'0' * 40}\n"
        self.assertEqual(self.verificar("prepush", stdin=line_new).returncode, 1)

    def test_nested_guard_skips_git_time_rules(self):
        self.policy([{"type": "before_git", "git": "commit", "run": "exit 3", "reason": "x"}])
        self.assertEqual(self.bash("git commit -m y"), "deny")
        self.assertEqual(call({"tool_name": "Bash", "tool_input": {"command": "git commit -m y"}}, self.root, nested=True), "none")

    def test_inicio_resume_y_activa_hooks(self):
        out = self.verificar("inicio")
        self.assertEqual(out.returncode, 0)
        self.assertIn("ia/REGLAS.md", out.stdout)
        self.assertIn("Agente:", out.stdout)
        self.assertIn("NO activos", out.stdout)
        (self.root / "ia" / "githooks").mkdir(exist_ok=True)
        (self.root / "ia" / "githooks" / "pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")
        (self.root / "ia" / "instalar.sh").write_text("git config core.hooksPath ia/githooks\n", encoding="utf-8")
        texto = self.verificar("inicio").stdout  # Codex, Gemini o ChatGPT con terminal
        self.assertIn("activados ahora", texto)
        self.assertEqual(self.sh("git config --get core.hooksPath").stdout.strip(), "ia/githooks")
        hook = json.loads(self.verificar("inicio", "--hook").stdout)  # Claude Code
        self.assertEqual(hook["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("Hooks de git: activos", hook["hookSpecificOutput"]["additionalContext"])

    def test_hooks_installed_avoid_double_run(self):
        self.policy([{"type": "before_git", "git": "commit", "run": "exit 3", "reason": "Pruebas."}])
        self.assertEqual(self.bash("git commit -m y"), "deny")
        self.sh("git config core.hooksPath ia/githooks")
        self.assertEqual(self.bash("git commit -m y"), "none")


if __name__ == "__main__":
    unittest.main(verbosity=1)
