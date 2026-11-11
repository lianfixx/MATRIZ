import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar as g  # noqa: E402

CHANGELOG = """# Cambios

## 2026-11-10 · segunda entrega
- Agente: Codex
- Cambios: algo.
- Pendiente: revisar con Emi.

## 2026-11-04 · primera entrega
- Agente: Claude Code (sesión en la nube)
- Pendiente: ninguno.
"""


def repo(base: Path, nombre: str, privado_txt: str = "") -> Path:
    d = base / nombre
    (d / "skills" / "demo").mkdir(parents=True)
    (d / ".claude" / "skills" / "demo").mkdir(parents=True)
    (d / "README.md").write_text(f"# {nombre}\n\n![x](y)\n\nTexto **claro** del proyecto. {privado_txt}\n\nOtro.\n")
    (d / "CHANGELOG.md").write_text(CHANGELOG)
    (d / "skills" / "demo" / "SKILL.md").write_text("---\nname: demo-skill\n---\n")
    (d / ".claude" / "skills" / "demo" / "SKILL.md").write_text("---\nname: puente\n---\n")
    for c in (["init", "-q"], ["add", "-A"],
              ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x"]):
        subprocess.run(["git", *c], cwd=d, check=True)
    return d


class Generar(unittest.TestCase):
    def test_changelog(self):
        e = g.entradas_changelog(CHANGELOG)
        self.assertEqual([x["fecha"] for x in e], ["2026-11-10", "2026-11-04"])
        self.assertEqual(e[0]["agente"], "Codex")
        self.assertEqual(e[0]["pendiente"], "revisar con Emi.")
        self.assertEqual(len(g.entradas_changelog(CHANGELOG, maximo=1)), 1)

    def test_readme(self):
        self.assertEqual(g.resumen_readme("# T\n\n| a |\n\nHola [mundo](http://x) y `más`.\n\nFin"), "Hola mundo y más.")

    def test_yaml(self):
        y = g.yaml({"a": 'dice "hola"', "n": 0, "vacio": "", "ultimo_cambio": "2026-11-11", "tags": ["x"]})
        self.assertEqual(y, '---\na: "dice \\"hola\\""\nn: 0\nultimo_cambio: 2026-11-11\ntags:\n  - "x"\ngenerado: "' + g.GENERADO + '"\n---\n')
        self.assertEqual(g.pendiente_real("Ninguno."), "")

    def test_validar(self):
        cfg = {"cerebros": [{"id": "a", "repos": ["r"]}, {"id": "b", "repos": ["r"]}], "privados": ["z"]}
        self.assertEqual(len(g.validar(cfg)), 2)

    def test_generar_y_privados(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            repo(t / "clones", "abierto")
            repo(t / "clones", "cerrado.", "SECRETO-DEL-CLIENTE")
            cfg = {"propietario": "x", "detalle_privados": False, "privados": ["cerrado."],
                   "cerebros": [{"id": "uno", "nombre": "Uno", "descripcion": "D.", "repos": ["abierto", "cerrado.", "falta"]}]}
            datos = g.generar(cfg, t / "out", t / "clones", False, "2026-11-11")
            a, c, f = datos["cerebros"][0]["repos"]
            self.assertEqual([s["nombre"] for s in a["skills"]], ["demo-skill"])
            self.assertEqual(a["registro"][0]["agente"], "Codex")
            self.assertTrue(c["leido"] and c["ultimo_cambio"])
            self.assertEqual((c["resumen"], c["skills"], c["registro"]), ("", [], []))
            self.assertFalse(f["leido"])
            todo = "".join(p.read_text() for p in (t / "out").rglob("*") if p.is_file())
            self.assertNotIn("SECRETO-DEL-CLIENTE", todo)
            self.assertTrue((t / "out" / "repos" / "cerrado.md").exists())
            nota = (t / "out" / "cerebros" / "Uno.md").read_text()
            self.assertIn("[[cerrado|cerrado.]]", nota)
            self.assertTrue(nota.startswith("---\ntipo: \"cerebro\"\n"))
            rabierto = (t / "out" / "repos" / "abierto.md").read_text()
            self.assertIn('pendiente: "revisar con Emi."', rabierto)
            self.assertIn('ultimo_agente: "Codex"', rabierto)
            self.assertIn("[[Uno]]", rabierto)
            rcerrado = (t / "out" / "repos" / "cerrado.md").read_text()
            self.assertNotIn("skills:", rcerrado)
            self.assertNotIn("pendiente:", rcerrado)
            portada = (t / "out" / "MATRIZ.md").read_text()
            self.assertIn("`falta`", portada)
            self.assertNotIn("[[abierto", portada)  # la portada solo enlaza cerebros
            self.assertTrue((t / "out" / "bitacora" / "2026-11.md").exists())
            json.loads((t / "out" / "matriz.json").read_text())


if __name__ == "__main__":
    unittest.main()
