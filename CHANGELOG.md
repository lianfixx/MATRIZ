# Cambios

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
