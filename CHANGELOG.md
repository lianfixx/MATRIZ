# Cambios

## 2026-11-13 · Matriz 1.4.0: panel más claro y reloj de respaldo

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 13/11/2026: «Recuerda tenerlo SIEMPRE actualizado en todo momento. Pulso por cerebro no es nada entendible… no sé ni cómo funciona ni qué hace la página; hazlo más utilizable, minimalista, claro, sencillo».
- Cambios: columna de la izquierda reordenada por utilidad: «Necesita tu atención», «Tus pendientes», «Tus cerebros», «Esta semana», «Quién hizo los cambios» y «Llevar la Matriz a otra IA». «Pulso por cerebro» (barra sin etiqueta y «commits») se reemplazó por «Tus cerebros»: cada uno con su estado en palabras (Activo, Tranquilo, Quieto o Revisar), su último cambio («hoy», «ayer», «hace 9 días»), los cambios de la semana y sus pendientes, ordenados primero por lo que necesita atención, con leyenda. «Commits» pasa a «cambios» en todo el panel y se explica qué es un cambio. Hay una guía «Así funciona» la primera vez (se cierra con «Entendido» y vuelve con el botón «?»). Siempre al día: un reloj de Cloudflare (cron del Worker, cada 10 minutos, plan gratis) pide la actualización por si un aviso de GitHub se pierde, porque el horario de GitHub se saltó horas.
- Archivos: `panel/app.js`, `panel/index.html`, `panel/estilo.css`, `worker/index.js`, `worker/prueba.mjs`, `wrangler.jsonc`, `docs/PANEL.md` y este registro.
- Verificación: `node worker/prueba.mjs` → aprobado (89; incluye el reloj con y sin token). Navegador real con los datos actuales, en escritorio 1440×900 e iPhone 15: guía, estados y leyenda legibles; la guía se cierra y vuelve con «?»; sin desborde horizontal ni errores de consola.
- Pendiente: ninguno.

## 2026-11-13 · Matriz 1.3.0: cerebro «Sitios web»

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 13/11/2026: «esos van en un cerebro aparte, esos 3 son proyectos nuevos que ya tenía».
- Cambios: nuevo cerebro «Sitios web» (confirmado por Emi) con emilianomilla-site, sistemas-digitales y vicente-diablo; su descripción sale de los README de cada uno. `EMI.md` lo suma a «Dónde trabaja». Ya no quedan repositorios sin cerebro.
- Archivos: `matriz.config.json`, `EMI.md` y este registro.
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado; la configuración se valida al generar.
- Pendiente: ninguno.

## 2026-11-13 · Matriz 1.2.1: avisos en tiempo real en todos los repositorios

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 13/11/2026: «sigue» (terminar la actualización en tiempo real).
- Cambios: la llave «Matriz administración (Claude)» suma el permiso Webhooks. GitHub pidió confirmar acceso y el código llegó al correo de Emi; lo leyó Claude, sin pedirle nada a Emi. Con `~/.config/matriz/ganchos.py` (computadora virtual; idempotente) se dio de alta el aviso «push» firmado hacia `/gancho` en los 29 repositorios de Emi, menos MATRIZ. Aparecieron 4 repositorios nuevos (Instagram, LinkedIn, TikTok y REDES): son skills de redes sociales y se agregaron al cerebro «Contenido y video». Siguen sin cerebro, para que Emi decida: emilianomilla-site, sistemas-digitales y vicente-diablo.
- Archivos: `matriz.config.json`, `docs/PANEL.md` y este registro.
- Verificación: el aviso de prueba de GitHub (ping) dio 200 en X, INDEP y TikTok. Un aviso «push» firmado igual que los de GitHub disparó «Actualizar la Matriz» en 5 segundos, y el panel quedó publicado unos 2.5 minutos después. La página en línea ya mostraba los 4 repositorios nuevos sin que nadie hiciera nada. Observación: el horario de 15 minutos de GitHub no se cumplió (entre las 04:15 y las 12:20 UTC no corrió); por eso los avisos son la vía principal.
- Pendiente: Emi decide el cerebro de emilianomilla-site, sistemas-digitales y vicente-diablo (o lo pregunta la revisión del domingo).

## 2026-11-13 · Matriz 1.2.0: casi en tiempo real

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 13/11/2026: «¿Ya está actualizado de manera automática? ¿Igual la página y todo? ¿Y cada cuándo? ¿La página que se actualice en tiempo real, es posible?».
- Cambios: (1) El panel revisa cada minuto, y al volver a la pestaña, si hay datos nuevos y los pinta sin recargar: tarjetas, hoja abierta y, si cambian los repositorios, el espacio 3D, que ahora se puede destruir y volver a crear sin fugas. Un punto «en vivo» late al llegar datos y no interrumpe si estás escribiendo. (2) «Actualizar la Matriz» corre cada 15 minutos en vez de una vez al día, y «Publicar panel» solo publica si la actualización guardó algo. (3) Nuevo `/gancho` en el Worker: recibe el aviso «push» de GitHub firmado con `GANCHO_SECRETO`, comprueba la firma en tiempo constante y dispara la actualización con `repository_dispatch` usando el token de escritura (que solo toca MATRIZ). Ignora otras ramas, los avisos de MATRIZ y los de firma falsa. El secreto se creó en la computadora virtual y se guardó por API, sin páginas ni códigos.
- Archivos: `panel/app.js`, `panel/espacio.js`, `panel/index.html`, `panel/estilo.css`, `worker/index.js`, `worker/prueba.mjs`, `wrangler.jsonc`, `.github/workflows/actualizar-matriz.yml`, `.github/workflows/publicar-panel.yml`, `docs/PANEL.md` y este registro.
- Verificación: `node worker/prueba.mjs` → aprobado (87; incluye firma válida y falsa, ping, otra rama y que MATRIZ no se dispara a sí misma). Navegador real (Chromium): con la hoja de Castorena abierta se cambió `matriz.json` en el servidor; en 64 s aparecieron el pendiente nuevo en «Hoy» y en la hoja, el repositorio nuevo en el 3D y el aviso «La Matriz se actualizó», sin errores.
- Pendiente: dar de alta el aviso de GitHub en cada repositorio (siguiente paso, por API).

## 2026-11-12 · Matriz 1.1.2: decisiones de Emi sobre verificaciones

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 12/11/2026: «no limites nada y respecto Google, no quiero que quites la verificación de 2 pasos de Google, solo de Cloudflare y GitHub si era posible».
- Cambios: en `EMI.md` se corrige la regla «sin códigos». La verificación en 2 pasos de Google se queda activa y no se instaló ningún autenticador. GitHub y Cloudflare no tenían verificación en 2 pasos (comprobado en sus páginas de seguridad): los códigos venían de sus páginas, que ya no se usan. El token «CLAUDE» de Cloudflare conserva todos sus permisos por decisión de Emi (cierra el pendiente de 1.1.1). La página de Google que quedó abierta en la computadora virtual se cerró sin cambios.
- Archivos: `EMI.md` y este registro.
- Verificación: ninguna prueba de código afectada (solo texto).
- Pendiente: ninguno nuevo.

## 2026-11-12 · Matriz 1.1.1: límite exacto de intentos y regla «sin códigos» para toda IA

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 12/11/2026: «para nada quiero que me pidan códigos… audita a fondo todo».
- Cambios: la prueba en producción mostró que el limitador de Cloudflare (1.1.0) no frenaba: su propia documentación dice que es aproximado y deja pasar ráfagas. Se reemplazó por un Durable Object «Intentos» (plan gratis) que cuenta exacto los intentos fallidos por IP: 5 por minuto o 20 por hora bloquean esa IP hasta que se enfríe. `EMI.md` suma la regla para cualquier IA: nunca pedirle a Emi códigos ni verificaciones; usar las API con las llaves de la computadora virtual, códigos por correo leídos en Gmail y nunca avisos al teléfono. Inventario de los 26 repositorios: solo MATRIZ guarda secretos; los otros 25 corren sin llaves propias. En Cloudflare, sin usar el panel: token «Proyectos de Emi (cf y wrangler)» en la computadora virtual (sin dominios, DNS ni facturación) y vencimiento al token «CLAUDE» del entorno APJ (registrado en lianfixx/cloudfare).
- Archivos: `worker/index.js`, `worker/prueba.mjs`, `wrangler.jsonc`, `EMI.md` y este registro.
- Verificación: `node worker/prueba.mjs` → aprobado (81, incluida la clase real del contador con almacenamiento simulado: el sexto intento fallido da 429); `wrangler deploy --dry-run` → reconoce `INTENTOS`. En producción, antes de este cambio: 14 intentos seguidos con clave falsa dieron 401 sin bloqueo; el conector rechaza otro origen (403) y versiones desconocidas (400); `matriz.json` ya no publica huellas ni el nombre del cliente.
- Pendiente: el token «CLAUDE» de Cloudflare tiene casi todos los permisos de la cuenta; reemplazarlo por uno limitado lo decide Emi.

## 2026-11-12 · Matriz 1.1.0: correcciones de la auditoría independiente

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 12/11/2026: «audita a fondo por favor todo, absolutamente TODO».
- Cambios (auditoría hecha por un agente aparte que revisó el código sin ver las conclusiones previas):
  - Alto: la visibilidad falla cerrada. Si GitHub no responde, un repositorio solo se publica como público si una corrida anterior lo confirmó; si no, se trata como privado (antes se publicaba completo).
  - Privacidad: los formatos que nunca se publican viven en un solo archivo, `tools/privacidad.json`, que usan igual la Matriz y el panel. Nuevos: teléfonos «(55) 1234-5678», «55 12 34 56 78» y «55.1234.5678»; «Exp. No. 45/2023» y «Expediente: 45/2023»; amparo directo, causa penal, carpeta y averiguación; IDs de Google Docs y Sheets; CURP y RFC en minúsculas; montos como «$5» y «1.5 millones de pesos». Los cuantificadores están acotados, así que el filtro ya no se vuelve lento con textos largos.
  - Privacidad: los nombres de clientes ya no se publican como huella (se podían revertir con un diccionario). Vienen solo del secreto `MATRIZ_RESERVADOS`, se comparan por palabras completas sin importar acentos ni espacios, y sin ese secreto la actualización diaria se detiene en vez de publicar.
  - Privacidad: de un repositorio privado nuevo ya no se publica el nombre, solo cuántos hay. La bitácora deja de publicar lo de repositorios que pasaron a privados. Los nombres de skills pasan por el filtro.
  - Panel: el filtro revisa el texto ya limpio (antes «Ac<>me» pasaba). Al guardar se conserva lo que el panel no edita: otras secciones, texto suelto, propiedades y subtareas. Los pendientes escritos a mano tienen un id estable. Completar y prioridad mandan el estado deseado, así que un doble toque ya no deshace el cambio. Las marcas 📅 ✅ ➕ 🔺 ^ y los saltos de línea Unicode del texto ya no se vuelven datos. Tablero grande: base64 por bloques. El tope de 200 notas avisa en vez de borrar. Las fechas inexistentes se rechazan. Un 422 de GitHub ya no se reporta como «otro cambio al mismo tiempo». «Salir» avisa si falla.
  - Sesión: hay un límite de 5 intentos de contraseña por minuto por IP (Rate Limiting de Cloudflare, además de un contador local). La firma de la cookie usa la contraseña y el token de escritura, así que una cookie filtrada ya no sirve para adivinar la contraseña.
  - Conector MCP: valida `Origin` (lo pide la especificación), rechaza versiones de protocolo desconocidas, limita los lotes a 10 y lee `matriz.json` una vez por minuto.
  - Workflows: wrangler queda fijado con lockfile (`tools/despliegue/`) y se instala sin scripts. La llave de Cloudflare y los secretos del panel van en pasos separados. Una rama `claude/…` que se integra sola solo puede tocar `inventario.json`, `matriz.config.json`, `CHANGELOG.md` y `revisiones/`, revisando el diff completo con los merges. La búsqueda de repositorios pagina (más de 100). Los proyectos se leen bien aunque su nombre lleve «---» o comillas. Las fechas ISO de semana ya no tumban la generación.
- Archivos: `tools/privacidad.json` (nuevo), `tools/generar.py`, `tools/test_generar.py`, `worker/index.js`, `worker/prueba.mjs`, `panel/app.js`, `wrangler.jsonc`, `tools/despliegue/` (nuevo), `.github/workflows/publicar-panel.yml`, `.github/workflows/integrar-tareas.yml`, `matriz.config.json`, `AGENTS.md` y este registro.
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado (20, con regresiones de cada hallazgo); `node worker/prueba.mjs` → aprobado (79); `python3 ia/test_guard.py` → aprobado (33); `wrangler deploy --dry-run` con la versión fijada → aprobado, con el límite de intentos.
- Pendiente: el tablero vive en el repositorio público y `MATRIZ_ESCRITURA` puede escribir en todo MATRIZ (GitHub no limita un token por carpeta). Moverlos a un repositorio privado aparte es un cambio mayor que se propondrá a Emi. `registro-ia.yml` usa las reglas del propio commit al crear una rama nueva; es parte del protocolo común de todos los repositorios y se corregirá allí, no solo aquí. El historial de git conserva la huella publicada antes (Emi eligió no reescribir el historial).

## 2026-11-12 · Matriz 1.0.2: mantenimiento sin códigos ni verificaciones

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 12/11/2026: «haz algo para que no me ande pidiendo códigos ni verificaciones ni en GitHub ni en Cloudflare».
- Cambios: dos llaves limitadas en la computadora virtual de Emi (`~/.config/matriz/`, permiso 600): GitHub «Matriz administración (Claude)» (secretos, variables y workflows de sus repositorios; sin acceso a código) y Cloudflare «Matriz administración (Claude)» (solo «Tokens de API: Editar»), ambas hasta el 12/11/2027. Con ellas, renovar llaves, cambiar secretos y volver a publicar se hace por API, sin las páginas que piden confirmar identidad. Scripts `renovar-cloudflare.mjs`, `secreto.mjs` y `~/bin/matriz-gh`. Documentado en `docs/PANEL.md` («Mantenimiento sin códigos»); vencimientos en `inventario.json`.
- Archivos: `docs/PANEL.md`, `inventario.json` y este registro.
- Verificación: la llave de GitHub lista los secretos de MATRIZ (200) y no lee código de un repositorio privado (403); la de Cloudflare se verifica activa; `renovar-cloudflare.mjs` renovó la llave del panel y la guardó en GitHub sin abrir páginas; «Publicar panel» con esa llave → aprobado; `/api/sesion` → `configurado: true` (contraseña y token de escritura activos).
- Pendiente: agregar el conector en Claude y ChatGPT (Emi).

## 2026-11-12 · Matriz 1.0.1: llave de Cloudflare renovada y panel publicado

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 12/11/2026: «Hazlo tú ya… Puedes hacer todo?».
- Cambios: desde la computadora virtual de Emi, sin que ningún valor pasara por la conversación ni por la pantalla: se renovó la llave «MATRIZ panel (GitHub Actions)» en Cloudflare, se comprobó con la API de Cloudflare (activa) y se guardó cifrada en `CLOUDFLARE_API_TOKEN` (GitHub pidió confirmar acceso con el código que envió al correo de Emi). Se creó el token de grano fino «MATRIZ escritura» (solo `lianfixx/MATRIZ`, Contents lectura y escritura, vence el 12/11/2027), se comprobó (escribe en MATRIZ; otro repositorio responde 404) y se guardó en `MATRIZ_ESCRITURA`. Se creó `MATRIZ_RESERVADOS`. `inventario.json` suma el vencimiento del token nuevo. Causa de las fallas anteriores: el formulario de secretos de GitHub exige confirmar acceso y cifrar en el navegador; un envío sin eso no guardaba nada aunque la página no mostraba error.
- Archivos: `inventario.json` y este registro.
- Verificación: «Publicar panel» → aprobado; https://matriz.milla-abogados.workers.dev publicado (versión f75cbd6b, 17 archivos).
- Pendiente: Emi guarda su contraseña en el secreto `PANEL_CLAVE` (es la única que no debe pasar por una IA); agregar el conector en Claude y ChatGPT.

## 2026-11-12 · Matriz 1.0.0: archivo único respaldado en GitHub, Obsidian y Drive

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 12/11/2026: «QUE CON ESTA MATRIZ GENERAL SEA LA ÚNICA QUE DEBA ADJUNTAR A CUALQUIER IA PARA QUE ENTIENDA TODO… DEBE ESTAR RESPALDADA, DOCUMENTADA (Y TODO LO QUE NACE DE ELLA) EN GITHUB, OBSIDIAN Y DRIVE»; respaldo en Drive: «archivo único + copia».
- Cambios: `MATRIZ_GENERAL.md` queda como la puerta única (README, AGENTS, guía de conexión, panel y conector la ponen primero). Google Drive: carpeta privada «Matriz General» (solo Emi) con el documento de Google «Matriz General», `MATRIZ_GENERAL.md` y `MATRIZ-2026-11-12.zip` del repositorio; la revisión del domingo los renueva cuando su sesión tiene Google Drive (las tareas programadas de esta organización no pueden guardar conectores: si no lo tiene, lo dice en su resumen). Revisión semanal: vencimientos desde `inventario.json`, proyectos nuevos (encargo para Muse) y respaldo en Drive. Privacidad: al pasar los nombres de clientes al secreto `MATRIZ_RESERVADOS` (0.8.0), mientras el secreto no exista, un nombre volvió a publicarse en `matriz.json`, una nota de repositorio y la bitácora. Ahora `matriz.config.json` guarda los nombres como huella SHA-256 (`terminos_reservados_huella`, sin el nombre en claro); el generador las aplica a todo lo publicado, también a lo reutilizado de una lectura anterior y a la bitácora acumulada, y el panel rechaza esos nombres al escribir aunque falte el secreto. El historial de git conserva las versiones anteriores (Emi eligió no reescribirlo). Prueba del conector: el archivo único se verifica con y sin `MATRIZ_GENERAL.md` y `fetch` de la Matriz siempre devuelve texto. Documentación al día: README, AGENTS, PANEL, CONECTAR_IA, OBSIDIAN y REVISION_SEMANAL.
- Archivos: `tools/generar.py`, `tools/test_generar.py`, `matriz.config.json`, `worker/index.js`, `worker/prueba.mjs`, `README.md`, `AGENTS.md`, `docs/PANEL.md`, `docs/CONECTAR_IA.md`, `docs/OBSIDIAN.md`, `docs/REVISION_SEMANAL.md` y este registro.
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado (15, con regresiones de huellas y de lectura anterior); `node worker/prueba.mjs` → aprobado (48); las 9 líneas publicadas que tenían el nombre quedan tapadas con el filtro nuevo; Drive → los tres archivos subidos, el documento convertido completo y la carpeta solo con permiso de Emi.
- Pendiente: Emi renueva la llave de Cloudflare y guarda `CLOUDFLARE_API_TOKEN`, `PANEL_CLAVE`, `MATRIZ_ESCRITURA` y `MATRIZ_RESERVADOS`; agregar el conector en Claude y ChatGPT; Obsidian en el iPhone.

## 2026-11-12 · Matriz 0.9.1: actualización tras cada edición, reintentos y grafo corregido

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 12/11/2026: «QUE CONECTE A CAMBIOS DIRECTOS CON OBSIDIAN» y «AUDITA A PROFUNDIDAD Y MEJORA, ARREGLA».
- Cambios: «Actualizar la Matriz» corre también al cambiar `tablero/`, `proyectos/` o `EMI.md` (lo que se edita en el panel llega a la Matriz, al panel y a Obsidian en minutos), guarda `MATRIZ_GENERAL.md` (antes se generaba y no se subía), lee los nombres reservados del secreto `MATRIZ_RESERVADOS` y reintenta la subida si `main` cambió. «Integrar tareas programadas» también reintenta. `ia/politica.json`: `MATRIZ_GENERAL.md`, `tablero/` y `proyectos/` quedan exentos del registro en CHANGELOG como los demás archivos que no se editan a mano; su registro es el commit (con `IA-Actor`) y la bitácora. Grafo de Obsidian: `-file:EMI` también ocultaba `estilo-emi` y un `-path:ia` habría ocultado cinco repositorios; ahora usa expresiones exactas y deja fuera `tablero/`, `proyectos/`, `ia/` y `MATRIZ_GENERAL.md` (el tablero ya se ve dentro de cada nota de cerebro).
- Archivos: `.github/workflows/actualizar-matriz.yml`, `.github/workflows/integrar-tareas.yml`, `ia/politica.json`, `.obsidian/graph.json` y este registro.
- Verificación: `python3 ia/test_guard.py` → aprobado (33); `python3 ia/verificar.py reglas` → aprobado; YAML de los cuatro workflows válido; Obsidian real (Linux, bóveda de prueba con un tablero y un proyecto de ejemplo) → el grafo muestra 30 nodos: MATRIZ, 7 cerebros y los 22 repositorios, sin `EMI.md`, tablero ni proyectos.
- Pendiente: si Emi movió o cambió el grafo en su Mac, Obsidian Git puede pedir resolver `graph.json` al traer este cambio (conservar la versión del repositorio).

## 2026-11-12 · Matriz 0.9.0: panel 3D que edita y conector con diez herramientas

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 12/11/2026: «MEJORA EL PANEL, NO ES NADA CLARO, NI SENCILLO Y NO SE PUEDEN HACER CAMBIOS DESDE ÉL, QUE SEA UNA HERRAMIENTA, QUE CONECTE A CAMBIOS DIRECTOS CON OBSIDIAN, QUE TENGA MÉTRICAS PERFECTAS A MI PERFIL… usa three js, 3D… rápido, seguro, limpio». Acceso con «contraseña propia».
- Cambios: panel rehecho. Al centro, la Matriz en 3D (three.js 0.186.1 servido por el propio panel, sin servicios externos; se arma en cada publicación con esbuild y versiones fijas en `tools/three/`, porque la copia minificada tiene constantes matemáticas que el freno de secretos confunde con números de tarjeta): cada cerebro es una esfera del tamaño de su actividad de la semana, se apaga si lleva más de 21 días sin movimiento y late con un anillo si tiene vencidos o tareas fallidas; sus repositorios giran alrededor. Se gira con el dedo o el mouse; al tocar un cerebro la cámara se acerca y se abre su hoja. Las etiquetas no se enciman ni tapan esferas. A la izquierda, «Hoy»: commits de la semana con su curva de 8 semanas, Atención (vencidos, fallas y vencimientos), Pendientes, Pulso por cerebro, quién trabajó en 60 días y «Llevar la Matriz a otra IA». Hoja del cerebro: métricas, pendientes y notas editables, repositorios, tareas y skills. Buscar con ⌘K. En el iPhone la Matriz va arriba, las tarjetas abajo y la hoja sube desde abajo. Edición con contraseña (sesión de 30 días, cookie HttpOnly, Secure y SameSite=Strict; 800 ms de espera tras un intento fallido): agregar, completar, priorizar, fechar, editar y borrar pendientes; escribir y borrar notas; crear proyectos. Cada cambio es un commit en `tablero/<id>.md` o `proyectos/<slug>.md` y llega a Obsidian con la sincronización. El Worker rechaza textos que parecen datos de cliente. Conector MCP: diez herramientas (nuevas: `matriz_general`, `pendientes`, `metricas`) y respuestas de error correctas en casos límite. Encabezados de seguridad: CSP estricta, sin marcos, sin permisos de cámara ni ubicación. Workflow de publicación: Node 24, los secretos solo existen en el paso de publicar y `PANEL_CLAVE`, `MATRIZ_ESCRITURA` y `MATRIZ_RESERVADOS` se copian como secretos del Worker si están guardados.
- Archivos: `panel/index.html`, `panel/app.js`, `panel/espacio.js`, `panel/estilo.css`, `tools/three/` (entrada, package.json y lockfile), `.github/workflows/publicar-panel.yml`, `worker/index.js`, `worker/prueba.mjs`, `wrangler.jsonc`, `tools/panel.py` y este registro.
- Verificación: `node worker/prueba.mjs` → aprobado (45 casos); `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado (14); prueba de extremo a extremo con el Worker real y GitHub simulado en un iPhone 15 emulado → contraseña mala rechazada, sesión, pendiente nuevo, dato de cliente bloqueado, completar, nota, proyecto y salir correctos, con el Markdown esperado en cada commit; capturas en escritorio 1440×900 e iPhone 15 → sin desborde horizontal ni errores de consola. Safari real no probado.
- Pendiente: la llave de Cloudflare guardada en GitHub ya no es válida (se renovó dos veces y la ventana se cerró antes de copiarla): Emi debe renovarla y guardarla; secretos `PANEL_CLAVE`, `MATRIZ_ESCRITURA` y `MATRIZ_RESERVADOS`; workflows, Drive y documentación (siguiente entrada).

## 2026-11-12 · Matriz 0.8.0: generador auditado, métricas, tablero y archivo único

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 12/11/2026: «AUDITA A PROFUNDIDAD Y MEJORA, ARREGLA» y «que la Matriz General sea la única que deba adjuntar a cualquier IA para que entienda todo; todo nace y sale de ahí».
- Cambios: correcciones de la revisión independiente del código. Lectura de CHANGELOG con fecha en cualquier posición, encabezados `##` y `###`, orden por fecha y campos en negritas. Bitácora acumulativa (nunca borra líneas). Si un repositorio no se puede leer se conservan sus datos anteriores en vez de vaciarlos. Fechas inválidas ya no detienen la actualización y se validan. La visibilidad se confirma con la API de GitHub: lo que no esté confirmado como público se trata como privado. No se siguen enlaces simbólicos. Se detectan notas con el mismo nombre. No se enlazan repositorios externos. El filtro de privacidad tapa más formatos (expedientes cortos, amparos, montos en pesos y MXN, IDs de Drive) y también los textos del inventario; los nombres de clientes ya no se escriben en el repositorio: vienen del secreto `MATRIZ_RESERVADOS`. Las pruebas usan datos ficticios. Nuevo: actividad por semana e IA a partir de los commits (solo conteos), métricas por cerebro (movimiento, días sin movimiento, pendientes, vencidos, tareas fallidas), vencimientos en `inventario.json`, tablero editable por cerebro (`tablero/<id>.md`) y proyectos nuevos (`proyectos/`), y el archivo único `MATRIZ_GENERAL.md`. EMI.md: Herramientas incluye Simular Box y REA.
- Archivos: `tools/generar.py`, `tools/test_generar.py`, `matriz.config.json`, `inventario.json`, `EMI.md` y este registro.
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado (14 casos); generación con los repositorios locales → sin nombres de cliente, números de expediente ni IDs de Drive en ningún archivo generado.
- Pendiente: Worker con edición, panel 3D, workflows y respaldo en Drive (siguientes entradas).

## 2026-11-12 · Matriz 0.7.0: filtro de privacidad para todo lo que se publica

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 12/11/2026: «AUDITA A PROFUNDIDAD Y MEJORA, ARREGLA Y DAME VERSIÓN FINAL».
- Cambios: la auditoría encontró que la Matriz copiaba de los `CHANGELOG.md` de repositorios públicos un número de expediente y el nombre de un cliente, y que así llegaban al panel y al conector. `tools/generar.py` ahora pasa todo texto de un repositorio (resumen, títulos, agente y pendientes) por un filtro que tapa números de expediente, números de folio sueltos, correos, teléfonos, CURP, RFC y montos, y sustituye por «[cliente]» los nombres de `terminos_reservados` en `matriz.config.json` (hoy: Liverpool). `matriz.json` deja de publicar el campo «cambios». README explica la privacidad y el acceso del token; la guía de Obsidian ya no fija el número de repositorios. El historial de git conserva las versiones anteriores; esos datos ya eran públicos en `Cerebro-Castorena-`.
- Archivos: `tools/generar.py`, `tools/test_generar.py`, `matriz.config.json`, `README.md`, `docs/OBSIDIAN.md` y este registro.
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado (incluye una prueba de reservas); generación local con los 22 repositorios → sin «Liverpool» ni «27969» en MATRIZ.md, matriz.json, cerebros/, repos/, contexto/ ni bitacora/.
- Pendiente: integrar los hallazgos de la revisión independiente del código (en curso).

## 2026-11-12 · Matriz 0.6.0: panel publicado y conector MCP para cualquier IA

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 12/11/2026: «haz tú lo de Cloudflare» y «configura de manera perfecta y completa todo el entorno Cloudflare con las skills, GitHub, en el entorno de Claude y que se pueda usar con Muse, ChatGPT etc. Todo auditado».
- Cambios: desde la computadora virtual de Emi (box «main», con su sesión de Google y sus verificaciones en el iPhone) se creó en Cloudflare la llave «MATRIZ panel (GitHub Actions)» (plantilla de Workers, solo su cuenta, sin caducidad, sin permisos de dominios) y se guardaron en este repositorio los secretos `CLOUDFLARE_API_TOKEN` y `CLOUDFLARE_ACCOUNT_ID`; el portapapeles de la computadora virtual se vació y se guardó su estado para conservar las sesiones. El panel quedó en https://matriz.milla-abogados.workers.dev. `worker/index.js` añade al mismo Worker un conector MCP de solo lectura en `/mcp` (Streamable HTTP, respuestas JSON) con siete herramientas: `matriz_resumen`, `cerebro`, `contexto`, `ultimos_cambios`, `reglas_de_emi`, `search` y `fetch`; lee solo lo público del panel. `tools/panel.py` publica también `EMI.md` y usa direcciones completas en `llms.txt`. `worker/prueba.mjs` prueba el conector y corre antes de cada publicación. Guía por IA en `docs/CONECTAR_IA.md`.
- Archivos: `worker/index.js`, `worker/prueba.mjs`, `wrangler.jsonc`, `tools/panel.py`, `.github/workflows/publicar-panel.yml`, `docs/CONECTAR_IA.md`, `docs/PANEL.md`, `README.md`, `AGENTS.md`, `inventario.json` y este registro.
- Verificación: `node worker/prueba.mjs` → aprobado (13 casos); `wrangler deploy --dry-run` → aprobado con el enlace ASSETS; publicación del panel en Cloudflare → aprobada (11 archivos, https://matriz.milla-abogados.workers.dev); conector en producción → ver la entrada siguiente o Actions.
- Pendiente: agregar el conector en claude.ai y en ChatGPT; Obsidian en el iPhone.

## 2026-11-11 · Matriz 0.5.0: todo se actualiza y se retroalimenta solo

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 11/11/2026: «RECUERDA QUE CONTIGO SE DEBE ACTUALIZAR Y RETROALIMENTAR ABSOLUTAMENTE TODO TODO!! SIN QUE HAGA NADA».
- Cambios: la actualización diaria ahora descubre los repositorios de `lianfixx` que no están en ningún cerebro y los muestra en `MATRIZ.md`, en `matriz.json` (`por_clasificar`) y en los avisos del panel; la revisión semanal los clasifica. La revisión semanal suma dos pasos: detectar skills instaladas en Claude cuya copia quedó vieja frente a su repositorio (con encargo listo para Muse) y una retroalimentación de la semana (lo repetido, lo que falló, lo que Emi hizo a mano y cómo automatizarlo, aplicando de una vez lo que toque a la Matriz). `EMI.md` guarda la regla para cualquier IA: todo se registra y se automatiza; a Emi solo se le pide lo que nadie más puede hacer.
- Archivos: `tools/generar.py`, `tools/test_generar.py`, `panel/index.html`, `docs/REVISION_SEMANAL.md`, `EMI.md` y este registro.
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado; descubrimiento de repositorios → no ejecutado en esta sesión (el proxy de la sesión no permite listar la cuenta); se comprueba en la corrida de GitHub.
- Pendiente: que el token «MATRIZ lectura» tenga acceso a «All repositories» (solo lectura) para que un repositorio privado nuevo no requiera pasos de Emi; secretos de Cloudflare para publicar el panel.

## 2026-11-11 · registro de la Matriz 0.4.0 (panel web en Cloudflare y dos skills con repositorio)

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 11/11/2026: «1.- Sí» (crear repositorio para las skills sin respaldo) y «vamos con la fase 3» (panel en Cloudflare); dejar el iPhone para el final.
- Cambios: el commit anterior («Matriz 0.4.0…») subió sin su entrada de registro porque un script de documentación falló antes de escribirla y los hooks de git no estaban activos en esta copia; `registro-ia.yml` lo marcó en rojo. Esta entrada lo registra y activa los hooks (`sh ia/instalar.sh`). Contenido de 0.4.0: `panel/index.html` es el panel (inicio con grafo, avisos, lo último y pendientes; una vista por cerebro con repositorios, tareas y skills; buscador; botón para copiar el contexto de un cerebro a cualquier IA; claro y oscuro; adaptado al iPhone). `tools/panel.py` arma `dist/` con el panel, `matriz.json`, `contexto/`, `llms.txt`, `robots.txt` y `_headers` (no indexar). `wrangler.jsonc` y el workflow `publicar-panel.yml` lo suben a Cloudflare Workers después de cada actualización; sin secretos termina en verde sin publicar. `box-simular` y `rea-ingenieria-inversa` se agregan al cerebro Herramientas como privados (sus repositorios están listos para subirse en cuanto existan en GitHub); `video-vox` apunta a su repositorio de origen, `santmun/video-vox`, sin cambios locales que respaldar. Guía en `docs/PANEL.md`; README y AGENTS lo mencionan.
- Archivos: `panel/index.html`, `tools/panel.py`, `wrangler.jsonc`, `.github/workflows/publicar-panel.yml`, `docs/PANEL.md`, `matriz.config.json`, `inventario.json`, `.gitignore` (commit anterior); `README.md`, `AGENTS.md` y este registro (este commit).
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado; `python3 tools/panel.py` → 12 archivos; `wrangler deploy --dry-run` (4.154.0) → aprobado; panel en Chromium a 1280 px (claro y oscuro) y en iPhone 15 → sin desbordes ni errores de consola, búsqueda funciona; «Publicar panel» en GitHub → verde sin publicar (faltan los secretos); `registro-ia.yml` del commit anterior → falló por falta de registro, corregido aquí.
- Pendiente: que Emi (o Muse) cree los repositorios `box-simular` y `rea-ingenieria-inversa`, los agregue al token «MATRIZ lectura» y guarde `CLOUDFLARE_API_TOKEN` y `CLOUDFLARE_ACCOUNT_ID`; luego, conector MCP, respaldo a Drive e iPhone.

## 2026-11-11 · Matriz 0.3.0: revisión semanal, tareas programadas, skills instaladas y perfil

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 11/11/2026: «Recuerda todas TODAS las semanas actualizarlo y que tenga toda la información mía etc. Continúa».
- Cambios: `inventario.json` registra las tareas programadas (nombre, cerebro, horario, última corrida; nunca su texto) y las skills instaladas en Claude con su repositorio. El generador las muestra en la portada (activas, las que fallaron, skills sin repositorio y skills sin instalar), en cada cerebro y en los archivos de contexto. `EMI.md` resume quién es Emi y las reglas que valen siempre. `docs/REVISION_SEMANAL.md` define la revisión de cada domingo 20:13 (repositorios nuevos, tareas, skills, salud y vencimiento del token) y la ejecuta una tarea programada de Claude creada hoy. El workflow `integrar-tareas.yml` (copiado de `Cerebro-Castorena-`) pasa a `main` las ramas `claude/…` de las ejecuciones programadas, y «Actualizar la Matriz» se regenera al terminar esa integración y cuando cambia `inventario.json`. Primer informe en `revisiones/2026-11-11.md`.
- Archivos: `inventario.json`, `EMI.md`, `docs/REVISION_SEMANAL.md`, `revisiones/2026-11-11.md`, `.github/workflows/integrar-tareas.yml`, `.github/workflows/actualizar-matriz.yml`, `.obsidian/graph.json`, `tools/generar.py`, `tools/test_generar.py`, `README.md`, `AGENTS.md` y este registro.
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado; `python3 ia/test_guard.py` → aprobado; YAML de los workflows y de `Repositorios.base` → válido; corrida en GitHub → ver Actions.
- Pendiente: primera revisión automática el domingo 15/11/2026; decidir si `video-vox`, `box-simular` y `rea-ingenieria-inversa` tendrán repositorio; panel en Cloudflare, conector MCP y respaldo a Drive.

## 2026-11-11 · Matriz 0.2.0: bóveda de Obsidian lista para la Mac y el iPhone

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 11/11/2026: «por favor», a la propuesta de preparar la Fase 2 (abrir la Matriz como grafo en Obsidian en la Mac). Antes confirmó Obsidian también en el iPhone.
- Cambios: el repositorio queda como bóveda de Obsidian configurada. `.obsidian/` trae el grafo (filtrado a Matriz → cerebros → repositorios, Matriz en naranja y cerebros en morado), la apariencia con el fragmento `matriz.css`, las carpetas ocultas `ia/` y `tools/`, la carpeta de notas nuevas `notas/` y los ajustes del complemento Git (traer al abrir y cada 10 minutos, nunca subir). `Repositorios.base` muestra los 20 repositorios en tres vistas. El generador escribe propiedades de Obsidian en cada nota (tipo, cerebro, visibilidad, último cambio, skills, última IA, pendiente), nombra las notas de cerebro con su nombre visible, pone el aviso de «generado» como propiedad y deja de enlazar repositorios desde la portada para que el grafo conserve su jerarquía. `notas/` queda fuera de git. Guía paso a paso en `docs/OBSIDIAN.md`.
- Archivos: `tools/generar.py`, `tools/test_generar.py`, `.obsidian/app.json`, `.obsidian/appearance.json`, `.obsidian/graph.json`, `.obsidian/snippets/matriz.css`, `.obsidian/plugins/obsidian-git/data.json`, `Repositorios.base`, `notas/LEEME.md`, `docs/OBSIDIAN.md`, `.gitignore`, `README.md`, `AGENTS.md` y este registro.
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado; `python3 ia/test_guard.py` → aprobado; la bóveda abierta en Obsidian 1.15.0 para Linux (sin cuenta, en la sesión) → 47 notas, sin enlaces rotos salvo los de carpetas en `README.md`, grafo con la jerarquía esperada, `Repositorios.base` sin errores con sus 20 filas, propiedades ocultas y fragmento CSS activo; Mac, iPhone y Obsidian Sync → no ejecutado (no hay acceso desde la sesión).
- Pendiente: que Emi siga `docs/OBSIDIAN.md` en su Mac y contrate Obsidian Sync para el iPhone; fases siguientes: panel en Cloudflare, conector MCP, revisión semanal (con aviso de vencimiento del token el 9/02/2027) y respaldo a Drive.

## 2026-11-11 · diagnóstico del secreto MATRIZ_TOKEN

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 11/11/2026: publicar la Matriz. Corrección propia: tras la entrada anterior GitHub sigue respondiendo «Authentication failed» al leer los ocho privados.
- Cambios: el generador quita espacios y saltos de línea del token y, al clonar, informa si el secreto existe, su forma y su longitud, sin mostrarlo.
- Archivos: `tools/generar.py` y este registro.
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado; corrida en GitHub → ver Actions.
- Pendiente: si el secreto no es válido, volver a generarlo y guardarlo.

## 2026-11-11 · corrección: lectura de privados y dos corridas seguidas

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 11/11/2026: publicar la Matriz tras crear el repositorio y el secreto `MATRIZ_TOKEN` (hecho por Muse). Corrección propia al revisar las primeras corridas.
- Cambios: la primera corrida en GitHub leyó 12 de 20 repositorios aunque el secreto existía: el `git clone` se ejecutaba dentro de la copia de trabajo y heredaba la cabecera de credenciales de `actions/checkout`. Ahora clona desde la carpeta temporal, anula esa cabecera e informa el motivo si un repositorio no se puede leer. Una segunda corrida simultánea falló al subir (`fetch first`): el workflow ahora parte de lo último de `main` y hace `pull --rebase` antes de subir.
- Archivos: `tools/generar.py`, `.github/workflows/actualizar-matriz.yml` y este registro.
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado; `python3 ia/test_guard.py` → aprobado; corrida del workflow en GitHub → ver la entrada siguiente o el estado en Actions.
- Pendiente: Obsidian en la Mac, panel en Cloudflare, conector MCP, revisión semanal (con aviso de vencimiento del token el 9/02/2027) y respaldo a Drive.

## 2026-11-11 · Matriz General 0.1.0: índice de cerebros, repositorios y skills

- Agente: Claude Code (sesión en la nube)
- Solicitud: Emi, 11/11/2026, en una sesión de Claude Code aparte: una Matriz General dividida en Cerebros, complementada con GitHub y Obsidian, que cualquier IA pueda leer y continuar. Confirmó: Notion fuera, repositorio público por ahora, siete cerebros y dejar los demás repositorios como están.
- Cambios: repositorio nuevo. `matriz.config.json` define siete cerebros (Castorena, MILLA ABOGADOS, Acción Tlalnepantla, Contenido y video, Estudio, Productos, Herramientas) y asigna los 20 repositorios. `tools/generar.py` lee cada repositorio y escribe `MATRIZ.md`, `matriz.json`, `cerebros/`, `repos/`, `contexto/` y `bitacora/`. De los privados solo publica nombre, cerebro y fecha. El workflow `actualizar-matriz.yml` lo corre cada día. Protocolo común 1.1.0 copiado de `lianfixx/Escritos-juridicos-CASTORENA`; la política exime del registro a los archivos generados y exige las pruebas del generador.
- Archivos: todo el repositorio (versión inicial).
- Verificación: `python3 -m unittest discover -s tools -p 'test_*.py'` → aprobado; `python3 ia/test_guard.py` → aprobado; `python3 ia/verificar.py reglas --check` → aprobado; `python3 tools/generar.py --repos-dir <clones>` → 20 repositorios, 16 leídos; workflow `actualizar-matriz.yml` → no ejecutado (el repositorio aún no existe en GitHub).
- Pendiente: que Emi cree el repositorio `lianfixx/MATRIZ` en GitHub para poder publicar; guardar el secreto `MATRIZ_TOKEN` para leer `INDEP`, `estilo-emi`, `selector-modelos` y `maestria-alta-direccion`; fases siguientes: Obsidian en la Mac, panel en Cloudflare, conector MCP, revisión semanal y respaldo a Drive.
