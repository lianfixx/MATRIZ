import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inteligencia as ia  # noqa: E402

# Datos ficticios: ningún cliente ni expediente real.
BITACORA = """---
tipo: "bitacora"
---

# Bitácora nov 2026

## 22 nov 2026

- [[Alfa|Alfa]] · Cierre diario: sin cambios · Agente: Claude Code
- [[Beta|Beta]] · Falló la subida y se repitió a mano · Agente: Codex

## 20 nov 2026

- [[Alfa|Alfa]] · Cierre diario: sin cambios · Agente: Claude Code

## 1 nov 2026

- [[Alfa|Alfa]] · Fuera de la semana · Agente: Claude Code
"""
HOY = dt.date(2026, 11, 22)
USO = {"modelo": "prueba", "entrada": 1000, "salida": 100, "costo_usd": 0.001}


def raiz_semanal(base: Path, por_clasificar=None) -> Path:
    (base / "bitacora").mkdir()
    (base / "bitacora" / "2026-11.md").write_text(BITACORA, encoding="utf-8")
    (base / "matriz.json").write_text(json.dumps({
        "metricas": {"cerebros": {"uno": {"esta_semana": 3, "semana_pasada": 1}}},
        "por_clasificar": por_clasificar or []}), encoding="utf-8")
    (base / "matriz.config.json").write_text(json.dumps({
        "cerebros": [{"id": "uno", "nombre": "Uno", "descripcion": "Área uno", "repos": ["Alfa", "Beta"]}]}), encoding="utf-8")
    (base / "CHANGELOG.md").write_text("# Cambios\n\n## 2026-11-13 · Anterior\n\n- Agente: Emi\n", encoding="utf-8")
    return base


def repo_git(base: Path) -> Path:
    def git(*a):
        subprocess.run(["git", "-C", str(base), "-c", "user.name=p", "-c", "user.email=p@p", *a], check=True, capture_output=True)
    git("init", "-q")
    (base / "bitacora").mkdir()
    (base / "bitacora" / "2026-11.md").write_text("# Bitácora\n\n- [[Alfa|Alfa]] · Línea vieja de prueba · Agente: Emi\n", encoding="utf-8")
    (base / "matriz.json").write_text("{}\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-q", "-m", "base")
    return base


class Costos(unittest.TestCase):
    def test_costo(self):
        self.assertEqual(ia.costo(ia.HAIKU, 1_000_000, 1_000_000), 0.60)
        self.assertEqual(ia.costo(ia.SONNET, 1_000_000, 100_000), 3.0)


class Red(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = repo_git(Path(self.tmp.name))
        with (self.raiz / "bitacora" / "2026-11.md").open("a", encoding="utf-8") as f:
            f.write("- [[Alfa|Alfa]] · Línea nueva con un nombre inventado · Agente: Emi\n")
            f.write("- [[Alfa|Alfa]] · Otra línea nueva sin datos · Agente: Emi\n")
            f.write("12 34\n")  # sin letras: no se envía

    def tearDown(self):
        self.tmp.cleanup()

    def test_solo_lineas_nuevas(self):
        pares = ia.lineas_nuevas(self.raiz)
        self.assertEqual([a for a, _ in pares], ["bitacora/2026-11.md"] * 2)
        self.assertFalse(any("vieja" in t for _, t in pares))

    def test_archivo_nuevo_se_revisa(self):
        (self.raiz / "repos").mkdir()
        (self.raiz / "repos" / "Nuevo.md").write_text("Resumen del repositorio nuevo de prueba\n", encoding="utf-8")
        self.assertIn("repos/Nuevo.md", [a for a, _ in ia.lineas_nuevas(self.raiz)])

    def test_informe_sin_texto_y_umbral(self):
        respuesta = {"hallazgos": [{"n": 1, "categoria": "persona", "confianza": 0.95},
                                   {"n": 2, "categoria": "persona", "confianza": 0.5},
                                   {"n": 99, "categoria": "persona", "confianza": 0.99},
                                   {"n": 1, "categoria": "inventada", "confianza": 0.99}]}
        informe = self.raiz / "informe.json"
        with mock.patch.object(ia, "llamar", return_value=(respuesta, USO)):
            self.assertEqual(ia.modo_red(self.raiz, False, informe), 0)
        doc = json.loads(informe.read_text())
        self.assertEqual(doc["hallazgos"], [{"archivo": "bitacora/2026-11.md", "linea": 4, "categoria": "persona", "confianza": 0.95}])
        self.assertNotIn("inventado", informe.read_text())

    def test_api_caida_no_detiene(self):
        with mock.patch.object(ia, "llamar", side_effect=ia.ErrorAPI("HTTP 529")):
            self.assertEqual(ia.modo_red(self.raiz, False, None), 0)

    def test_seco_no_llama(self):
        with mock.patch.object(ia, "llamar", side_effect=AssertionError("no debe llamar")):
            self.assertEqual(ia.modo_red(self.raiz, True, None), 0)

    def test_sin_cambios_no_llama(self):
        subprocess.run(["git", "-C", str(self.raiz), "checkout", "-q", "--", "."], check=True)
        with mock.patch.object(ia, "llamar", side_effect=AssertionError("no debe llamar")):
            self.assertEqual(ia.modo_red(self.raiz, False, None), 0)


class Semanal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = raiz_semanal(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_semana_solo_siete_dias(self):
        por_dia, texto = ia.semana(self.raiz, HOY)
        self.assertEqual(sorted(por_dia), ["2026-11-20", "2026-11-22"])
        self.assertNotIn("Fuera de la semana", texto)

    def test_puntos_sin_sustento_se_descartan(self):
        por_dia, _ = ia.semana(self.raiz, HOY)
        puntos = [{"texto": "Cierre repetido", "repos": ["Alfa"], "dias": ["2026-11-20", "2026-11-22"]},
                  {"texto": "Repo inventado", "repos": ["Gamma"], "dias": ["2026-11-22"]},
                  {"texto": "Día inventado", "repos": ["Beta"], "dias": ["2026-11-21"]},
                  {"texto": "", "repos": ["Alfa"], "dias": ["2026-11-22"]}, "basura"]
        buenos, descartados = ia.verificar_puntos(puntos, por_dia)
        self.assertEqual([b["texto"] for b in buenos], ["Cierre repetido"])
        self.assertEqual(descartados, 4)

    def test_escribe_revision_registro_y_changelog(self):
        respuesta = {"pulso": ["Semana tranquila."],
                     "repetido": [{"texto": "Cierre diario sin cambios", "repos": ["Alfa"], "dias": ["2026-11-20", "2026-11-22"]}],
                     "fallos": [{"texto": "Subida fallida", "repos": ["Beta"], "dias": ["2026-11-22"]}],
                     "hecho_a_mano": [{"texto": "Inventado", "repos": ["Zeta"], "dias": ["2026-11-22"]}], "propuestas": []}
        with mock.patch.object(ia, "llamar", return_value=(respuesta, USO)) as m:
            self.assertEqual(ia.modo_semanal(self.raiz, False, HOY), 0)
        self.assertEqual(m.call_count, 1)  # sin repos nuevos no se llama al clasificador
        md = (self.raiz / "revisiones" / "2026-11-22-ia.md").read_text()
        self.assertIn("Cierre diario sin cambios (Alfa", md)
        self.assertNotIn("Inventado", md)
        reg = json.loads((self.raiz / "revisiones" / "2026-11-22-ia.json").read_text())
        self.assertEqual(reg["descartados_por_verificacion"], 1)
        cambios = (self.raiz / "CHANGELOG.md").read_text()
        self.assertLess(cambios.index("2026-11-22 · Revisión semanal de la IA"), cambios.index("2026-11-13 · Anterior"))
        self.assertIn("- Agente: GitHub Actions · API de Claude", cambios)

    def test_dos_corridas_el_mismo_dia_no_duplican(self):
        respuesta = {"pulso": ["x"], "repetido": [], "fallos": [], "hecho_a_mano": [], "propuestas": []}
        with mock.patch.object(ia, "llamar", return_value=(respuesta, USO)):
            ia.modo_semanal(self.raiz, False, HOY)
            ia.modo_semanal(self.raiz, False, HOY)
        cambios = (self.raiz / "CHANGELOG.md").read_text()
        self.assertEqual(cambios.count("2026-11-22 · Revisión semanal de la IA"), 1)
        self.assertIn("2026-11-13 · Anterior", cambios)

    def test_clasificacion_baja_confianza_pregunta(self):
        self.tmp.cleanup()
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = raiz_semanal(Path(self.tmp.name), [
            {"nombre": "nuevo-a", "visibilidad": "público"}, {"nombre": "nuevo-b", "visibilidad": "público"},
            {"nombre": "1 repositorio privado (nombre reservado)", "visibilidad": "privado"}])
        retro = {"pulso": ["x"], "repetido": [], "fallos": [], "hecho_a_mano": [], "propuestas": []}
        clas = {"propuestas": [{"repo": "nuevo-a", "cerebro": "uno", "confianza": 0.9, "motivo": "encaja"},
                               {"repo": "nuevo-b", "cerebro": "inexistente", "confianza": 0.95, "motivo": "?"},
                               {"repo": "ajeno", "cerebro": "uno", "confianza": 0.99, "motivo": "?"}]}
        with mock.patch.object(ia, "llamar", side_effect=[(retro, USO), (clas, USO)]):
            ia.modo_semanal(self.raiz, False, HOY)
        reg = json.loads((self.raiz / "revisiones" / "2026-11-22-ia.json").read_text())
        self.assertEqual([c["repo"] for c in reg["clasificacion"]], ["nuevo-a"])
        self.assertEqual([c["repo"] for c in reg["preguntar_a_emi"]], ["nuevo-b"])
        self.assertIn("1 privado(s) con nombre reservado", (self.raiz / "revisiones" / "2026-11-22-ia.md").read_text())

    def test_api_caida_no_escribe(self):
        with mock.patch.object(ia, "llamar", side_effect=ia.ErrorAPI("falta ANTHROPIC_API_KEY")):
            self.assertEqual(ia.modo_semanal(self.raiz, False, HOY), 0)
        self.assertFalse((self.raiz / "revisiones").exists())

    def test_seco_no_llama(self):
        with mock.patch.object(ia, "llamar", side_effect=AssertionError("no debe llamar")):
            self.assertEqual(ia.modo_semanal(self.raiz, True, HOY), 0)


if __name__ == "__main__":
    unittest.main()
