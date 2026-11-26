"""Pruebas del triaje del Guardián (tools/guardian_triaje.py). Sin red: sin llave, la API «falla» y se prueba ese camino."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guardian_triaje as gt  # noqa: E402


def h(chequeo, repo, tipo, ruta="", gravedad="medio", huella=""):
    return {"chequeo": chequeo, "gravedad": gravedad, "repo": repo, "tipo": tipo, "ruta": ruta, "linea": 0, "huella": huella}


class Triaje(unittest.TestCase):
    def setUp(self):
        self._llave = os.environ.pop("ANTHROPIC_API_KEY", None)

    def tearDown(self):
        if self._llave is not None:
            os.environ["ANTHROPIC_API_KEY"] = self._llave

    def test_solo_nuevos_y_sin_aceptados(self):
        viejo = h("acceso", "X", "sin los frenos de ia/ (registro y secretos)")
        hoy = {"fecha": "2026-11-26", "hallazgos": [viejo, h("datos", "Cerebro-Castorena-", "número de expediente", gravedad="alto"),
                                                    h("credenciales", "Y", ".gitignore no excluye .env", ".gitignore", "bajo"),
                                                    h("salida", "", "aviso", gravedad="info")]}
        t = gt.triaje(hoy, {"hallazgos": [viejo]}, {"Y"}, seco=True)
        self.assertEqual(t["nuevos"], 1)
        self.assertEqual(t["aceptados_omitidos"], 1)
        self.assertEqual(t["hallazgos"][0]["accion_regla"], "auto_gitignore_env")

    def test_ruta_de_privado_no_se_envia(self):
        d = gt.para_api(h("datos", "INDEP", "x", "carpeta/Cliente Fulano.xlsx"), set())
        self.assertNotIn("Fulano", d["ruta"])
        self.assertIn(".xlsx", d["ruta"])
        self.assertEqual(gt.para_api(h("datos", "P", "x", "docs/a.md"), {"P"})["ruta"], "docs/a.md")

    def test_sin_llave_queda_en_fallo_para_la_suscripcion(self):
        t = gt.triaje({"hallazgos": [h("llaves", "P", "token de GitHub", "a.js", "critico", "ghp_…(40)")]}, {}, {"P"}, seco=False)
        self.assertEqual(t["api"]["estado"], "fallo")
        self.assertEqual(t["hallazgos"][0]["accion_regla"], "avisar_emi_revocar")

    def test_sin_novedades_no_llama(self):
        t = gt.triaje({"hallazgos": []}, {}, set(), seco=False)
        self.assertEqual(t["api"]["estado"], "sin_novedades")

    def test_bajos_e_historial_de_la_matriz_no_avisan(self):
        self.assertEqual(gt.accion_regla(h("datos", "P", "correo", "README.md", "bajo")), "ninguna")
        self.assertTrue(gt.aceptado(h("datos", "MATRIZ", "número de expediente (en el historial)")))
        self.assertEqual(gt.accion_regla(h("credenciales", "", "vence en 12 días: Renovación de la conexión Claude–box")), "ninguna")

    def test_acciones_por_tipo(self):
        self.assertEqual(gt.accion_regla(h("salida", "R", "acción sin fijar a SHA (actions)")), "auto_fijar_accion")
        self.assertEqual(gt.accion_regla(h("credenciales", "R", "archivo de credenciales versionado")), "auto_quitar_credencial_y_avisar")
        self.assertEqual(gt.accion_regla(h("memoria", "R", "2 enlace(s) a archivos que no existen")), "revisar_memoria")


if __name__ == "__main__":
    unittest.main()
