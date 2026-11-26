"""Pruebas de tools/redes_api.py sin red ni llaves."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redes_api as ra  # noqa: E402


class Redes(unittest.TestCase):
    def test_sin_llave_del_panel_no_configurado(self):
        with mock.patch.dict(os.environ, {"REDES_CLAUDE_LLAVE": ""}):
            r = ra.correr(seco=False)
        self.assertEqual(r["estado"], "no_configurado")
        self.assertIn("REDES_CLAUDE_LLAVE", r["motivo"])

    def test_sin_pendientes_no_llama_a_la_api(self):
        with mock.patch.dict(os.environ, {"REDES_CLAUDE_LLAVE": "x"}), mock.patch.object(ra, "panel", return_value={"inspiracion": [], "notas": []}), \
             mock.patch.object(ra, "firma_redes", return_value=("abc", {})), \
             mock.patch.object(ra, "firma_sincronizada", return_value="abc"), \
             mock.patch.object(ra, "llamar_con_imagen", side_effect=AssertionError("no debía llamar")):
            r = ra.correr(seco=False)
        self.assertEqual((r["estado"], r["sync_pendiente"], r["costo_usd"]), ("sin_novedades", False, 0.0))

    def test_inspiracion_y_sincronia_pendiente(self):
        estado = {"inspiracion": [{"id": "i1", "meta": {"titulo": "t"}, "que_me_llamo": "el gancho"}], "notas": []}
        posts = []
        def panel(ruta, metodo="GET", cuerpo=None, binario=False):
            if metodo == "POST":
                posts.append((ruta, cuerpo))
                return {}
            return estado
        datos = {**{c: "x" for c in ra.CAMPOS}, "espacio_propuesto": "personal"}
        with mock.patch.dict(os.environ, {"REDES_CLAUDE_LLAVE": "x"}), mock.patch.object(ra, "panel", side_effect=panel), \
             mock.patch.object(ra, "firma_redes", return_value=("nueva", {})), \
             mock.patch.object(ra, "firma_sincronizada", return_value="vieja"), \
             mock.patch.object(ra, "llamar_con_imagen", return_value=(datos, {"modelo": "m", "entrada": 1, "salida": 1, "costo_usd": 0.01})):
            r = ra.correr(seco=False)
        self.assertEqual((r["estado"], r["inspiraciones"], r["sync_pendiente"]), ("ok", 1, True))
        self.assertEqual(posts[0][0], "/api/claude/inspiracion/i1")


if __name__ == "__main__":
    unittest.main()
