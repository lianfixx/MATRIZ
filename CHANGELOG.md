# Cambios

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
