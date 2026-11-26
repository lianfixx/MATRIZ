# Guardián de la Matriz (seguridad y privacidad)

Desde el 25/11/2026 la Matriz revisa una vez al día la seguridad y la privacidad de **todos** los repositorios de Emi y da un puntaje de 0 a 100 con un veredicto. Lo hace `tools/guardian.py`. **Solo lee y aconseja**: no cambia, borra ni publica nada en los repositorios que revisa, no usa la API de Claude y no cuesta nada.

La idea viene del «Guardián Imperial» (Leyvi Cauich, Motor Agéntico de la comunidad Imperio Agéntico, junio de 2026): una página que audita el entorno de IA con siete chequeos (aquí son ocho: se sumó la salud de la memoria para IA), explica cada hallazgo en lenguaje simple y muestra cómo evoluciona el puntaje. Aquí no se usó su código (es de otra plataforma); se adaptó la idea a la Matriz y a un despacho jurídico, donde el riesgo mayor es el secreto profesional.

## Los ocho chequeos

| Chequeo | Qué revisa | Gravedad típica |
|---|---|---|
| 🔑 Llaves a la vista | Tokens y llaves (GitHub, Claude/OpenAI, Google, AWS, Meta, Slack, claves privadas) en los archivos actuales. Usa los mismos patrones que el freno de commits (`ia/guard.py`). | Crítico en público; medio en privado |
| 🕵️ Secretos en el historial | Las mismas llaves en cualquier commit anterior, aunque ya se hayan borrado. | Igual |
| 🪪 Credenciales y vencimientos | `.env`, `.pem`, `credentials.json` y similares versionados; `.gitignore` sin `.env` en repositorios con código; vencimientos de `inventario.json` a 14 días o menos. | Crítico a bajo |
| 👥 Acceso | Colaboradores y llaves de despliegue (requiere permiso de administración de lectura en el token; sin él dice «sin permiso para revisar» y no resta); repositorios sin los frenos de `ia/`. | Medio |
| 📡 Qué sale | Workflows con `pull_request_target` o `write-all`, acciones de terceros sin fijar a SHA y cuántos repositorios de los despachos son públicos. | Alto a aviso |
| 🧾 Datos de clientes | Solo en repositorios **públicos**: CURP, RFC de persona, tarjetas (Luhn), nombres del secreto `MATRIZ_RESERVADOS`, números de expediente, teléfonos y correos; y documentos de trabajo descargables (Excel, Word, PDF) en los cerebros Castorena y MILLA ABOGADOS. En archivos actuales y en el historial. | Crítico a bajo |
| 🧠 Memoria para tus IA | Que las instrucciones que leen tus IA se carguen completas: `AGENTS.md`, `CLAUDE.md` o `GEMINI.md` de más de 40 000 caracteres, enlaces a archivos que ya no existen y skills sin `name` o `description` (o con más de 1024 caracteres, o de más de 500 líneas). En todos los repositorios, públicos y privados. Idea de «Salud de Memoria Real» (Alejandro Álvarez, Motor Agéntico). | Medio a bajo |
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

- En el repositorio **privado** `lianfixx/guardian-detalle`: `detalle/AAAA-MM-DD.json` (uno por día) y `detalle/ULTIMO.json` (el más reciente). Lo escribe el paso del Guardián con la llave de despliegue del secreto `GUARDIAN_DEPLOY_KEY`, que solo puede escribir en ese repositorio (no lee ni cambia ningún otro). Antes de escribir, el paso comprueba que ese repositorio no sea público y, si lo es, no guarda nada. La llave se creó en la computadora virtual de Emi y no pasó por ninguna conversación; para revocarla: `guardian-detalle` → Settings → Deploy keys.
- Si falta la llave, el detalle solo existe durante la corrida y se borra al terminar.
- Con terminal, cualquier IA puede generarlo: `python3 tools/guardian.py --clonar --detalle /tmp/detalle.json` (con `MATRIZ_TOKEN` para los privados). El script se niega a escribir el detalle dentro de este repositorio.

## Cuándo corre y cómo avisa

Es un paso de «Actualizar la Matriz», antes de «Generar», y corre la primera vez de cada día (hora del centro de México); las demás actualizaciones del día lo saltan. Para repetirlo el mismo día: Actions → «Actualizar la Matriz» → Run workflow con «Repetir hoy la revisión del Guardián» activado (o, desde la computadora virtual, `~/bin/matriz-gh repos/lianfixx/MATRIZ/actions/workflows/actualizar-matriz.yml/dispatches POST '{"ref":"main","inputs":{"guardian":"true"}}'`). Así no depende del reloj de GitHub. Si falla, la Matriz se actualiza igual.

Si el puntaje baja 5 puntos o más, o aumentan los hallazgos críticos, abre o comenta el aviso «Guardián: bajó el puntaje de seguridad» en Issues (solo conteos; GitHub le avisa a Emi por correo).

## Reparación automática (API + suscripción)

Emi lo autorizó el 25/11/2026 («SÍ A TODO… que funcione a la API y con una segunda verificación para que entre mi suscripción, todo de forma automática»). Sigue su regla de que toda mejora quede en las dos vías y sincronizada.

1. **Vía API (GitHub Actions, diaria).** Después del Guardián, `tools/guardian_triaje.py` toma solo los hallazgos **nuevos** frente al último detalle y escribe en el repositorio privado `detalle/AAAA-MM-DD.triaje.json` y `detalle/TRIAJE_ULTIMO.json`. Cada hallazgo lleva dos opiniones: el arreglo que le toca por regla fija y el veredicto de Haiku 5.5 (parece real, falsa alarma o dudoso). A la API solo van chequeo, gravedad, tipo y repositorio, y la ruta de los públicos; de los privados, solo la extensión. Nunca contenidos, huellas ni valores. Costo: centavos de dólar al mes, dentro del tope del espacio «matriz».
2. **Relevo de la suscripción (tarea programada «Guardián · relevo si falla la API», diaria a las 12:53).** Regla de Emi (25/11/2026): ahorrar la suscripción. Si el triaje de la API de ese día está bien, la tarea termina en una línea. Si la API falló o no corrió, diagnostica con los registros, repara la causa de fondo en el código (con prueba y registro), vuelve a lanzar la revisión y confirma que la API funciona. Si la falla no es de código (llave, tope de gasto, pago), hace ella el triaje del día y le dice a Emi exactamente qué hacer. Su resumen le llega por aviso y por correo.
3. **Aplicar.** La plataforma no permite que una tarea sin nadie mirando cambie varios repositorios a la vez (se intentó el 25/11/2026 y lo frenó por seguridad). Por eso los arreglos se aplican cuando Emi lo pide en cualquier sesión con «aplica los arreglos del Guardián»: esa sesión toma el triaje del día, verifica cada hallazgo con el archivo real y hace los cambios de la tabla, cada uno con su registro.

| Arreglo | Qué se aplica |
|---|---|
| `auto_gitignore_env` | Agrega `.env` a `.gitignore`, con su registro y respetando las reglas propias del repositorio. |
| `auto_fijar_accion` | Fija la acción de GitHub al SHA de su versión, consultado en GitHub. |
| `auto_quitar_credencial_y_avisar` | Si el archivo trae de verdad una credencial, lo saca del repositorio (sin borrarlo del equipo de nadie), lo excluye en `.gitignore` y avisa a Emi para que la revoque. Si no trae, lo anota como falsa alarma. |
| `revisar_frenos` | Instala el control ligero solo si el repositorio registra cada cambio en su `CHANGELOG.md` y no recibe commits automáticos sin registro; si no, lo deja anotado. Nunca en bifurcaciones de terceros ni en `guardian-detalle`. |
| `revisar_memoria` | Corrige un enlace roto cuando el archivo solo cambió de lugar; si no, lo anota. |
| `avisar_emi_revocar`, `avisar_emi_datos`, `avisar_emi` | Solo Emi puede resolverlos: un correo a su Gmail, sin copiar valores ni datos. |
| `ninguna` | Detalles menores o ya cubiertos (por ejemplo, el vencimiento del box tiene su propia tarea). |

Límites que no cambian: no vuelve privado ni público ningún repositorio, no reescribe historial, no hace force-push ni salta frenos, no revoca llaves, no toca el contenido de `Cerebro-Castorena-` ni los datos que Emi decidió mantener, no crea ni cambia tareas programadas y solo escribe a emilianogarciamilla@gmail.com.

## Probar

```
python3 tools/guardian.py --demo                     # datos ficticios, no escribe nada
python3 tools/guardian.py --repos-dir ~/codigo --detalle /tmp/detalle.json --salida /tmp/guardian
python3 -m unittest discover -s tools -p 'test_*.py'
```

## Apagar

Quitar el paso «Guardián» de `.github/workflows/actualizar-matriz.yml`. La Matriz deja de mostrar la tarjeta cuando se borra `guardian/`.
