# Cambios

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
