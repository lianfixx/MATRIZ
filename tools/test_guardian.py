"""Pruebas del Guardián (tools/guardian.py). Solo biblioteca estándar: python3 -m unittest discover -s tools -p 'test_*.py'

Las llaves y datos de prueba se arman en tiempo de ejecución para que el freno de secretos de ia/ no los confunda
con reales; todos son ficticios.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guardian as gu  # noqa: E402

TOKEN_FICTICIO = "gh" + "p_" + "Q7w9Zr2Lk4Tn8Vb1Xc6Md3Pf5Hs0Jy" + "Ae4Ru7"   # 40 caracteres, no existe
CURP_FICTICIA = "GAMA" + "900101" + "HDF" + "RRN" + "09"
EXPEDIENTE_FICTICIO = "12345/" + "21-17-01-3"


def repo_de_prueba(carpeta: Path, archivos: dict[str, str], borrar: list[str] = ()) -> Path:
    r = carpeta / "r"
    r.mkdir()
    run = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=/dev/null", *a],
                                    cwd=r, check=True, capture_output=True)
    run("init", "-q")
    for ruta, texto in archivos.items():
        (r / ruta).parent.mkdir(parents=True, exist_ok=True)
        (r / ruta).write_text(texto, encoding="utf-8")
    run("add", "-A")
    run("commit", "-qm", "uno")
    for ruta in borrar:
        (r / ruta).unlink()
    if borrar:
        run("add", "-A")
        run("commit", "-qm", "dos")
    return r


class Filtros(unittest.TestCase):
    def test_asignacion_de_codigo_no_es_llave(self):
        # Las llaves se arman por partes para que el freno de commits no confunda la prueba con un secreto real.
        k = {"tok": "to" + "ken", "pw": "pass" + "word", "cs": "client_" + "secret", "sec": "sec" + "ret"}
        for v in [f"access_{k['tok']}: t.access_{k['tok']}", f"{k['tok']} = env.CLOUDFLARE_API_TOKEN",
                  f"{k['pw']}=REPLACE_ME_PLEASE_NOW", f"{k['cs']}: String(x || '').trim()", k["sec"] + " = '${{ secrets.X }}'"]:
            self.assertFalse(gu.parece_secreto(v), v)

    def test_asignacion_con_valor_real_si_cuenta(self):
        self.assertTrue(gu.parece_secreto("api" + "_key = '" + "Zq8Lr4Tx1Vn7" + "Mb2Kc9Pw5Hd3'"))

    def test_tarjeta_en_url_no_cuenta(self):
        datos = list(gu.buscar_datos("https://help.instagram.com/1525783237707138 · Grado: oficial", "a.md", set()))
        self.assertFalse([d for d in datos if d[2] == "número de tarjeta"])

    def test_datos_de_cliente(self):
        tipos = {d[2] for d in gu.buscar_datos(f"CURP {CURP_FICTICIA}, Exp. {EXPEDIENTE_FICTICIO}", "nota.md", set())}
        self.assertIn("CURP", tipos)
        self.assertIn("número de expediente", tipos)

    def test_nombre_reservado(self):
        datos = list(gu.buscar_datos("Reunión con Constructora Ficticia del Valle", "x.py", {"constructora ficticia"}))
        self.assertEqual(datos[0][2], "nombre de cliente reservado")


class Repositorio(unittest.TestCase):
    def test_llave_actual_e_historial(self):
        with tempfile.TemporaryDirectory() as t:
            r = repo_de_prueba(Path(t), {"config.js": f"const k = '{TOKEN_FICTICIO}';\n", "README.md": "hola\n"}, borrar=["config.js"])
            H = gu.auditar_repo("demo", r, publico=True, reservados=set())
            hist = [h for h in H if h["chequeo"] == "historial"]
            self.assertEqual(len(hist), 1)
            self.assertEqual(hist[0]["gravedad"], "critico")
            self.assertNotIn(TOKEN_FICTICIO, json.dumps(H))  # nunca el valor completo

    def test_privado_no_revisa_datos_y_baja_gravedad(self):
        with tempfile.TemporaryDirectory() as t:
            r = repo_de_prueba(Path(t), {"n.md": f"{CURP_FICTICIA}\nghp = '{TOKEN_FICTICIO}'\n"})
            H = gu.auditar_repo("demo", r, publico=False, reservados=set())
            self.assertFalse([h for h in H if h["chequeo"] == "datos"])
            self.assertEqual({h["gravedad"] for h in H if h["chequeo"] == "llaves"}, {"medio"})

    def test_documentos_de_asuntos_en_publico_juridico(self):
        with tempfile.TemporaryDirectory() as t:
            r = repo_de_prueba(Path(t), {"fuentes/Control_de_expedientes.xlsx": "x", "fuentes/foto.png": "x"})
            H = gu.auditar_repo("demo", r, publico=True, reservados=set(), juridico=True)
            docs = [h for h in H if h["tipo"].startswith("documento")]
            self.assertEqual([(h["gravedad"], h["ruta"]) for h in docs], [("critico", "fuentes/Control_de_expedientes.xlsx")])

    def test_npmrc_sin_credencial_no_cuenta(self):
        with tempfile.TemporaryDirectory() as t:
            r = repo_de_prueba(Path(t), {".npmrc": "audit=false\nfund=false\n"})
            self.assertFalse([h for h in gu.auditar_repo("demo", r, False, set()) if h["chequeo"] == "credenciales" and "versionado" in h["tipo"]])
        with tempfile.TemporaryDirectory() as t:
            r = repo_de_prueba(Path(t), {".npmrc": "//registry.npmjs.org/:_auth" + "Token=abc\n"})
            self.assertTrue([h for h in gu.auditar_repo("demo", r, False, set()) if h["chequeo"] == "credenciales" and "versionado" in h["tipo"]])

    def test_credencial_versionada_y_workflow(self):
        with tempfile.TemporaryDirectory() as t:
            r = repo_de_prueba(Path(t), {".env": "A=1\n", ".env.example": "A=\n", "package.json": "{}",
                                         ".github/workflows/w.yml": "on: pull_request_target\njobs:\n  a:\n    steps:\n      - uses: actions/checkout@v4\n"})
            tipos = [(h["chequeo"], h["tipo"]) for h in gu.auditar_repo("demo", r, True, set())]
            self.assertIn(("credenciales", "archivo de credenciales versionado"), tipos)
            self.assertEqual(sum(1 for c, x in tipos if x == "archivo de credenciales versionado"), 1)  # .env.example no cuenta
            self.assertIn(("salida", "workflow con pull_request_target"), tipos)
            self.assertIn(("salida", "acción sin fijar a SHA (actions)"), tipos)


class Frenos(unittest.TestCase):
    def test_version_ligera_cuenta(self):
        with tempfile.TemporaryDirectory() as t:
            r = repo_de_prueba(Path(t), {"ia/verificar.py": "#", ".github/workflows/control.yml": "jobs:\n  c:\n    steps:\n      - run: python3 ia/verificar.py ci\n"})
            self.assertFalse([h for h in gu.auditar_repo("demo", r, True, set()) if h["chequeo"] == "acceso"])

    def test_sin_frenos(self):
        with tempfile.TemporaryDirectory() as t:
            r = repo_de_prueba(Path(t), {"README.md": "hola"})
            self.assertTrue([h for h in gu.auditar_repo("demo", r, True, set()) if h["chequeo"] == "acceso"])


class Memoria(unittest.TestCase):
    def test_enlace_roto_skill_sin_description_y_archivo_largo(self):
        with tempfile.TemporaryDirectory() as t:
            r = repo_de_prueba(Path(t), {"AGENTS.md": "Lee [reglas](ia/REGLAS.md) y [web](https://x.mx) y [doc](docs/ok.md)\n" + "x" * 41000,
                                         "docs/ok.md": "ok", "skills/s/SKILL.md": "---\nname: s\n---\nhola\n"})
            tipos = {h["tipo"] for h in gu.auditar_repo("demo", r, False, set()) if h["chequeo"] == "memoria"}
            self.assertIn("1 enlace(s) a archivos que no existen", tipos)
            self.assertIn("skill sin name o description en su encabezado", tipos)
            self.assertTrue(any(x.startswith("instrucciones de 41") for x in tipos))

    def test_memoria_sana(self):
        with tempfile.TemporaryDirectory() as t:
            r = repo_de_prueba(Path(t), {"AGENTS.md": "Lee [esto](docs/a.md#parte)\n", "docs/a.md": "a",
                                         "skills/s/SKILL.md": "---\nname: s\ndescription: Hace algo.\n---\nhola\n"})
            self.assertFalse([h for h in gu.auditar_repo("demo", r, False, set()) if h["chequeo"] == "memoria"])


class Puntaje(unittest.TestCase):
    def test_sin_hallazgos_es_fortaleza(self):
        r = gu.puntuar([])
        self.assertEqual((r["puntaje"], r["veredicto"]), (100, "Fortaleza"))

    def test_tope_por_chequeo_y_bajos(self):
        H = [gu.hallazgo("datos", "critico", "x", "CURP") for _ in range(50)] + [gu.hallazgo("acceso", "bajo", "x", "y") for _ in range(50)]
        r = gu.puntuar(H)
        self.assertEqual(r["chequeos"]["datos"]["resta"], gu.TOPE_POR_CHEQUEO)
        self.assertEqual(r["chequeos"]["acceso"]["resta"], gu.TOPE_BAJOS)
        self.assertEqual(r["puntaje"], 100 - gu.TOPE_POR_CHEQUEO - gu.TOPE_BAJOS)

    def test_veredictos(self):
        self.assertEqual(gu.puntuar([gu.hallazgo("llaves", "critico", "x", "y")])["veredicto"], "Expuesto")
        self.assertEqual(gu.puntuar([gu.hallazgo("skills", "medio", "x", "y")])["veredicto"], "Fortaleza")


class Publicacion(unittest.TestCase):
    def test_salida_publica_sin_repos_ni_rutas(self):
        H = [gu.hallazgo("datos", "critico", "repo-secreto-cliente", "CURP", "carpeta/cliente.md", 3, "GAMA…(18)")]
        pub = gu.salida_publica(gu.puntuar(H), {"repos": 1}, "2026-11-25")
        texto = json.dumps(pub, ensure_ascii=False)
        for prohibido in ("repo-secreto-cliente", "cliente.md", "GAMA"):
            self.assertNotIn(prohibido, texto)
        self.assertNotIn("repo-secreto-cliente", gu.resumen_md(pub, []))

    def test_aviso_solo_si_empeora(self):
        bien = gu.salida_publica(gu.puntuar([]), {}, "2026-11-24")
        mal = gu.salida_publica(gu.puntuar([gu.hallazgo("llaves", "critico", "x", "y")]), {}, "2026-11-25")
        self.assertEqual(gu.comparar(mal, mal), "")
        self.assertIn("1", gu.comparar(bien, mal))
        self.assertEqual(gu.comparar(mal, bien), "")

    def test_detalle_dentro_del_repositorio_se_rechaza(self):
        r = subprocess.run([sys.executable, str(gu.RAIZ / "tools" / "guardian.py"), "--demo", "--detalle",
                            str(gu.RAIZ / "detalle.json")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertFalse((gu.RAIZ / "detalle.json").exists())

    def test_primera_corrida_sin_aviso(self):
        mal = gu.salida_publica(gu.puntuar([gu.hallazgo("llaves", "critico", "x", "y")]), {}, "2026-11-25")
        self.assertEqual(gu.comparar({}, mal), "")


if __name__ == "__main__":
    unittest.main()
