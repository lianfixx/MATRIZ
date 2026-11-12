import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar as g  # noqa: E402

# Datos ficticios: ningún cliente ni expediente real.
CHANGELOG = """# Cambios

## 2026-11-10 · segunda entrega del 99999/21-11-01-1
- **Agente:** Codex
- Cambios: algo.
- Pendiente: revisar con Emi.

## 2026-11-04 · primera entrega
- Agente: Claude Code (sesión en la nube)
- Pendiente: ninguno.
"""


def repo(base: Path, nombre: str, extra: str = "", changelog: str = CHANGELOG) -> Path:
    d = base / nombre
    (d / "skills" / "demo").mkdir(parents=True)
    (d / ".claude" / "skills" / "demo").mkdir(parents=True)
    (d / "README.md").write_text(f"# {nombre}\n\n![x](y)\n\nTexto **claro** del proyecto. {extra}\n\nOtro.\n")
    (d / "CHANGELOG.md").write_text(changelog)
    (d / "skills" / "demo" / "SKILL.md").write_text("---\nname: demo-skill\n---\n")
    (d / ".claude" / "skills" / "demo" / "SKILL.md").write_text("---\nname: puente\n---\n")
    env = {**os.environ, "GIT_AUTHOR_DATE": "2026-11-10T10:00:00", "GIT_COMMITTER_DATE": "2026-11-10T10:00:00"}
    for c in (["init", "-q"], ["add", "-A"],
              ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x", "-m", "IA-Actor: Claude Code"]):
        subprocess.run(["git", *c], cwd=d, check=True, env=env)
    return d


CFG = {"propietario": "x", "detalle_privados": False, "privados": ["cerrado."],
       "cerebros": [{"id": "uno", "nombre": "Uno", "descripcion": "D.", "repos": ["abierto", "cerrado.", "falta"]}]}


class Parser(unittest.TestCase):
    def test_changelog(self):
        e = g.entradas_changelog(CHANGELOG)
        self.assertEqual([x["fecha"] for x in e], ["2026-11-10", "2026-11-04"])
        self.assertEqual(e[0]["agente"], "Codex")  # quita los ** de Markdown
        self.assertEqual(e[0]["pendiente"], "revisar con Emi.")
        self.assertEqual(len(g.entradas_changelog(CHANGELOG, maximo=1)), 1)

    def test_formatos_de_encabezado(self):
        txt = ("## 0.3.0 · 2026-11-11 · candidato\n- Agente: Muse\n\n### Skill 1.2.1 — 2026-11-09: arreglo\n"
               "### 2026-10-01 · viejo\n## 2026-12-01 · ascendente al final\n")
        e = g.entradas_changelog(txt)
        self.assertEqual([x["fecha"] for x in e], ["2026-12-01", "2026-11-11", "2026-11-09", "2026-10-01"])
        self.assertEqual(e[1]["titulo"], "0.3.0 · candidato")
        self.assertEqual(e[2]["titulo"], "Skill 1.2.1 · arreglo")

    def test_readme(self):
        self.assertEqual(g.resumen_readme("# T\n\n| a |\n\nHola [mundo](http://x) y `más`.\n\nFin"), "Hola mundo y más.")

    def test_fechas(self):
        self.assertEqual(g.fecha_corta("2026-11-11"), "11 nov 2026")
        for raro in ("2026-11", "11/11/2026", "x"):
            self.assertEqual(g.fecha_corta(raro), raro)  # no se cae

    def test_yaml(self):
        y = g.yaml({"a": 'dice "hola"', "n": 0, "vacio": "", "ultimo_cambio": "2026-11-11", "tags": ["x"]})
        self.assertEqual(y, '---\na: "dice \\"hola\\""\nn: 0\nultimo_cambio: 2026-11-11\ntags:\n  - "x"\ngenerado: "' + g.GENERADO + '"\n---\n')
        self.assertEqual(g.pendiente_real("Ninguno."), "")
        self.assertEqual(g.pendiente_real("sin pendientes"), "")

    def test_actor(self):
        self.assertEqual(g.actor("Claude Code (ejecución programada)"), "Claude")
        self.assertEqual(g.actor("Codex"), "ChatGPT · Codex")
        self.assertEqual(g.actor("Muse (Muse Spark)"), "Muse")


class Privacidad(unittest.TestCase):
    def tearDown(self):
        g.configurar_reservas([])

    def test_reservar(self):
        g.configurar_reservas(["Acme"])
        txt = ("Cotejo Grupo Acme: el 99999/21-11-01-1, el 4321/2023, el 77777/22 y el amparo indirecto 456/24 vivos; exp. 45/2022; "
               "escribe a fulano@correo.mx o al 55 1111 2222; GODE561331HDFRRN09; pago $12,500.00, MXN 9,000 y 1 200 pesos; "
               "archivo 1abcdefghijklmnopqrstuvwxyz012345; anotación del 88888; corte 09/11 y 50/51 filas; versión 1.2.3; 11/11/2026")
        r = g.reservar(txt)
        for fuera in ("Acme", "99999", "4321/2023", "77777", "456/24", "45/2022", "fulano", "2222", "GODE56", "12,500",
                      "9,000", "1 200", "1abcdefghij", "88888"):
            self.assertNotIn(fuera, r)
        for queda in ("09/11", "50/51", "1.2.3", "11/11/2026", "[cliente]", "[expediente]"):
            self.assertIn(queda, r)

    def test_terminos_del_entorno(self):
        os.environ["MATRIZ_RESERVADOS"] = "Acme, Beta\nGamma"
        try:
            self.assertEqual(g.terminos_del_entorno(), ["Acme", "Beta", "Gamma"])
        finally:
            del os.environ["MATRIZ_RESERVADOS"]

    def test_symlink_no_se_lee(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "secreto").write_text("TOKEN=abc")
            (Path(t) / "README.md").symlink_to(Path(t) / "secreto")
            self.assertEqual(g.leer(Path(t) / "README.md"), "")


class Generacion(unittest.TestCase):
    def test_generar_privados_y_bitacora(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            repo(t / "clones", "abierto")
            repo(t / "clones", "cerrado.", "SECRETO-DEL-CLIENTE")
            datos = g.generar(CFG, t / "out", t / "clones", False, "2026-11-11", {}, None, None, t)
            a, c, f = datos["cerebros"][0]["repos"]
            self.assertEqual([s["nombre"] for s in a["skills"]], ["demo-skill"])
            self.assertEqual(a["registro"][0]["agente"], "Codex")
            self.assertEqual(sum(a["actividad"]["commits"]), 1)
            self.assertEqual(a["actividad"]["actores_60d"], {"Claude": 1})
            self.assertTrue(c["leido"] and c["ultimo_cambio"])
            self.assertEqual((c["resumen"], c["skills"], c["registro"]), ("", [], []))
            self.assertFalse(f["leido"])
            todo = "".join(p.read_text() for p in (t / "out").rglob("*") if p.is_file())
            self.assertNotIn("SECRETO-DEL-CLIENTE", todo)
            self.assertNotIn("99999", todo)
            self.assertIn("[[cerrado|cerrado.]]", (t / "out" / "cerebros" / "Uno.md").read_text())
            portada = (t / "out" / "MATRIZ.md").read_text()
            self.assertIn("`falta`", portada)
            self.assertNotIn("[[abierto", portada)
            general = (t / "out" / "MATRIZ_GENERAL.md").read_text()
            self.assertIn("## Cerebro: Uno", general)
            self.assertIn("Cómo trabajar con Emi", general)
            # bitácora acumulativa: una línea que ya estaba no se borra
            b = t / "out" / "bitacora" / "2026-11.md"
            b.write_text(b.read_text() + "\n## 1 nov 2026\n\n- [[viejo|viejo]] · algo de antes · Agente: Gemini\n")
            g.generar(CFG, t / "out", t / "clones", False, "2026-11-12", {}, None, None, t)
            self.assertIn("algo de antes", b.read_text())

    def test_lectura_anterior(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            repo(t / "clones", "abierto")
            previo = g.generar(CFG, t / "out", t / "clones", False, "2026-11-11", {}, None, None, t)
            import shutil
            shutil.rmtree(t / "clones" / "abierto")
            datos = g.generar(CFG, t / "out", t / "clones", False, "2026-11-12", {}, None, previo, t)
            a = datos["cerebros"][0]["repos"][0]
            self.assertEqual(a["lectura"], "anterior")
            self.assertEqual(a["registro"][0]["agente"], "Codex")

    def test_visibilidad_por_api(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            repo(t / "clones", "abierto", "TEXTO-DE-REPO")
            cfg = {**CFG, "privados": [], "cerebros": [{"id": "uno", "nombre": "Uno", "descripcion": "D.", "repos": ["abierto"]}]}
            api = {"abierto": {"nombre": "abierto", "visibilidad": "privado"}, "nuevo": {"nombre": "nuevo", "visibilidad": "público", "creado": "2026-11-12"}}
            datos = g.generar(cfg, t / "out", t / "clones", False, "2026-11-12", {}, api, None, t)
            self.assertEqual(datos["cerebros"][0]["repos"][0]["visibilidad"], "privado")
            self.assertNotIn("TEXTO-DE-REPO", (t / "out" / "matriz.json").read_text())
            self.assertEqual(datos["por_clasificar"][0]["nombre"], "nuevo")
            self.assertIn("`nuevo` · público", (t / "out" / "MATRIZ.md").read_text())
            # repositorio que la API no confirma: se trata como privado
            datos = g.generar(cfg, t / "out", t / "clones", False, "2026-11-12", {}, {}, None, t)
            self.assertEqual(datos["cerebros"][0]["repos"][0]["visibilidad"], "privado")

    def test_tablero_y_metricas(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            repo(t / "clones", "abierto")
            (t / "tablero").mkdir()
            (t / "tablero" / "uno.md").write_text(
                "---\ntipo: tablero\n---\n# Tablero\n\n## Pendientes\n\n- [ ] Llamar al despacho 🔺 📅 2026-11-01 ➕ 2026-10-30 ^a1b2c3\n"
                "- [ ] Revisar video\n- [x] Hecho ✅ 2026-11-10 ^d4e5f6\n\n## Notas\n\n- 2026-11-12 · idea suelta ^n1n2n3\n")
            inv = {"vencimientos": [{"nombre": "Token", "fecha": "2026-11-20"}],
                   "tareas": [{"nombre": "Cierre", "cerebro": "uno", "horario": "Diario", "ultima_corrida": "2026-11-10", "resultado": "falló: límite"}]}
            datos = g.generar(CFG, t / "out", t / "clones", False, "2026-11-12", inv, None, None, t)
            tab = datos["cerebros"][0]["tablero"]
            self.assertEqual(len(tab["pendientes"]), 3)
            p = tab["pendientes"][0]
            self.assertEqual((p["id"], p["alta"], p["vence"], p["texto"]), ("a1b2c3", True, "2026-11-01", "Llamar al despacho"))
            m = datos["metricas"]["cerebros"]["uno"]
            self.assertEqual((m["pendientes_abiertos"], m["pendientes_vencidos"], m["tareas_falladas"]), (2, 1, 1))
            self.assertEqual(datos["metricas"]["vencimientos"][0]["dias"], 8)
            self.assertIn("(alta) Llamar al despacho", (t / "out" / "cerebros" / "Uno.md").read_text())
            self.assertIn("Pendientes de Emi", (t / "out" / "contexto" / "uno.CONTEXTO.md").read_text())

    def test_validar(self):
        cfg = {"cerebros": [{"id": "a", "nombre": "A", "repos": ["r"]}, {"id": "b", "nombre": "B", "repos": ["r", "mes.", "Mes"]}], "privados": ["z"]}
        errores = g.validar(cfg, {"tareas": [{"nombre": "t", "cerebro": "a", "ultima_corrida": "ayer"}]})
        self.assertTrue(any("dos cerebros" in e for e in errores))
        self.assertTrue(any("mismo nombre" in e for e in errores))
        self.assertTrue(any("fecha inválida" in e for e in errores))
        self.assertTrue(any("privado" in e for e in errores))


if __name__ == "__main__":
    unittest.main()
