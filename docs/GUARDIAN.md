# Guardián de la Matriz (seguridad y privacidad)

Desde el 25/11/2026 la Matriz revisa una vez al día la seguridad y la privacidad de **todos** los repositorios de Emi y da un puntaje de 0 a 100 con un veredicto. Lo hace `tools/guardian.py`. **Solo lee y aconseja**: no cambia, borra ni publica nada en los repositorios que revisa, no usa la API de Claude y no cuesta nada.

La idea viene del «Guardián Imperial» (Leyvi Cauich, Motor Agéntico de la comunidad Imperio Agéntico, junio de 2026): una página que audita el entorno de IA con siete chequeos, explica cada hallazgo en lenguaje simple y muestra cómo evoluciona el puntaje. Aquí no se usó su código (es de otra plataforma); se adaptó la idea a la Matriz y a un despacho jurídico, donde el riesgo mayor es el secreto profesional.

## Los siete chequeos

| Chequeo | Qué revisa | Gravedad típica |
|---|---|---|
| 🔑 Llaves a la vista | Tokens y llaves (GitHub, Claude/OpenAI, Google, AWS, Meta, Slack, claves privadas) en los archivos actuales. Usa los mismos patrones que el freno de commits (`ia/guard.py`). | Crítico en público; medio en privado |
| 🕵️ Secretos en el historial | Las mismas llaves en cualquier commit anterior, aunque ya se hayan borrado. | Igual |
| 🪪 Credenciales y vencimientos | `.env`, `.pem`, `credentials.json` y similares versionados; `.gitignore` sin `.env` en repositorios con código; vencimientos de `inventario.json` a 14 días o menos. | Crítico a bajo |
| 👥 Acceso | Colaboradores y llaves de despliegue (requiere permiso de administración de lectura en el token; sin él dice «sin permiso para revisar» y no resta); repositorios sin los frenos de `ia/`. | Medio |
| 📡 Qué sale | Workflows con `pull_request_target` o `write-all`, acciones de terceros sin fijar a SHA y cuántos repositorios de los despachos son públicos. | Alto a aviso |
| 🧾 Datos de clientes | Solo en repositorios **públicos**: CURP, RFC de persona, tarjetas (Luhn), nombres del secreto `MATRIZ_RESERVADOS`, números de expediente, teléfonos y correos; y documentos de trabajo descargables (Excel, Word, PDF) en los cerebros Castorena y MILLA ABOGADOS. En archivos actuales y en el historial. | Crítico a bajo |
| 📦 Origen de skills | Skills instaladas que vienen de repositorios de terceros o que no tienen repositorio localizable. | Medio a bajo |

Los archivos de prueba (`test_*`, `prueba*`, `tests/`, `.example`, `.ejemplo`) y los valores de plantilla (`xxxx`, `REPLACE_ME`, `<tu-llave>`) cuentan como «aviso» y no restan. Una asignación del tipo `token = …` solo cuenta si el valor parece una llave real (letras y números mezclados, alta entropía, sin código).

## Puntaje y veredicto

Se parte de 100. Por cada chequeo, el primer hallazgo de cada gravedad resta su peso completo y cada uno más, una cuarta parte: crítico 30, alto 12, medio 5. Los «bajo» restan a lo más 3 por chequeo y los «aviso» no restan. Ningún chequeo resta más de 40.

| Puntaje | Veredicto |
|---|---|
| 90 a 100 | Fortaleza |
| 75 a 89 | Vigilante |
| 50 a 74 | Expuesto |
| 0 a 49 | En riesgo |

## Qué se publica y qué no

Este repositorio es público, así que hay dos salidas que nunca se mezclan:

- **Pública** (`guardian/estado.json`, `guardian/historial.json`, `guardian/GUARDIAN.md`, y de ahí `matriz.json`, la Matriz General, el panel y el conector MCP): puntaje, veredicto y conteos por chequeo y gravedad. **Nunca** nombres de repositorios, rutas, líneas ni textos. Publicar dónde está una llave filtrada sería señalarla.
- **Privada** (el detalle): repositorio, archivo, línea, tipo y una huella corta (los primeros 4 caracteres y la longitud). Nunca el valor completo de una llave ni el dato.

En los registros de Actions solo se imprimen conteos.

### Dónde está el detalle

- En Actions, el detalle se escribe en la carpeta temporal del runner y se borra al terminar. Si existen la variable `GUARDIAN_REPO` (por ejemplo `lianfixx/guardian-detalle`) y el secreto `GUARDIAN_TOKEN` (token de grano fino con «Contents: Read and write» **solo** sobre ese repositorio), se guarda en `detalle/AAAA-MM-DD.json` de ese repositorio. El script comprueba antes que el destino sea privado y se niega si no lo es.
- Con terminal, cualquier IA puede generarlo: `python3 tools/guardian.py --clonar --detalle /tmp/detalle.json` (con `MATRIZ_TOKEN` para los privados). El script se niega a escribir el detalle dentro de este repositorio.

## Cuándo corre y cómo avisa

Es un paso de «Actualizar la Matriz», antes de «Generar», y corre la primera vez de cada día (hora del centro de México); las demás actualizaciones del día lo saltan. Así no depende del reloj de GitHub. Si falla, la Matriz se actualiza igual.

Si el puntaje baja 5 puntos o más, o aumentan los hallazgos críticos, abre o comenta el aviso «Guardián: bajó el puntaje de seguridad» en Issues (solo conteos; GitHub le avisa a Emi por correo).

## Probar

```
python3 tools/guardian.py --demo                     # datos ficticios, no escribe nada
python3 tools/guardian.py --repos-dir ~/codigo --detalle /tmp/detalle.json --salida /tmp/guardian
python3 -m unittest discover -s tools -p 'test_*.py'
```

## Apagar

Quitar el paso «Guardián» de `.github/workflows/actualizar-matriz.yml`. La Matriz deja de mostrar la tarjeta cuando se borra `guardian/`.
