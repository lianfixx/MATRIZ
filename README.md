# Matriz General

El mapa de todo el trabajo de Emi: una **Matriz**, sus **Cerebros** y, debajo, los repositorios y skills de cada uno. Se llena sola leyendo los repositorios de `lianfixx`; nadie la mantiene a mano.

**Empieza aquí → [MATRIZ.md](MATRIZ.md)**

## Qué hay

| Archivo o carpeta | Qué es | Quién lo escribe |
|---|---|---|
| [`MATRIZ.md`](MATRIZ.md) | Portada: cerebros, último movimiento y lo último que hizo cada IA | Generador |
| [`cerebros/`](cerebros) | Una nota por cerebro | Generador |
| [`repos/`](repos) | Una nota por repositorio: resumen, skills, últimos registros y pendiente | Generador |
| [`contexto/`](contexto) | Un archivo por cerebro para pegar o adjuntar en cualquier IA | Generador |
| [`bitacora/`](bitacora) | Qué IA hizo qué, por día, en todos los repositorios | Generador |
| `matriz.json` | Los mismos datos, para el panel y el conector | Generador |
| [`EMI.md`](EMI.md) | Quién es Emi, dónde trabaja y las reglas que valen siempre | A mano |
| [`matriz.config.json`](matriz.config.json) | Qué cerebros existen y qué repositorio va en cuál | A mano |
| [`inventario.json`](inventario.json) | Tareas programadas y skills instaladas en Claude | Revisión semanal |
| [`revisiones/`](revisiones) | Informe de cada revisión semanal | Revisión semanal |
| `tools/generar.py` | El generador | A mano |
| `Repositorios.base`, `.obsidian/` | Tabla y configuración de Obsidian (grafo, estilo, complemento Git) | A mano |
| `panel/`, `tools/panel.py`, `wrangler.jsonc` | Panel web en Cloudflare: https://matriz.milla-abogados.workers.dev ([docs/PANEL.md](docs/PANEL.md)) | A mano |
| `worker/` | Conector MCP de solo lectura para cualquier IA en `/mcp` ([docs/CONECTAR_IA.md](docs/CONECTAR_IA.md)) | A mano |
| `notas/` | Notas propias de Emi; no se suben a GitHub | Emi |
| `AGENTS.md`, `ia/` | Protocolo común entre IA, igual que en los demás repositorios | A mano |

## Cómo se actualiza

Cada semana, el domingo a las 20:13, una tarea programada de Claude hace la [revisión semanal](docs/REVISION_SEMANAL.md): agrega repositorios nuevos, actualiza tareas programadas y skills, revisa la salud y avisa de vencimientos.

El workflow «Actualizar la Matriz» corre cada día a las 06:17 (hora del centro de México), cuando cambia la configuración, y a mano desde la pestaña Actions. Lee el `README.md`, el `CHANGELOG.md` y las skills de cada repositorio y reescribe el índice.

Para leer los repositorios privados usa el secreto `MATRIZ_TOKEN`: el token de GitHub de grano fino «MATRIZ lectura», con acceso a **todos** los repositorios de `lianfixx` y solo **Contents: Read-only** (vence el 9 de febrero de 2027; la revisión semanal avisa antes). Con ese acceso, un repositorio nuevo aparece solo en «Repositorios nuevos por clasificar». Después de cada actualización, «Publicar panel» sube el panel y el conector a Cloudflare con `CLOUDFLARE_API_TOKEN` y `CLOUDFLARE_ACCOUNT_ID`.

En una computadora, con los repositorios clonados en una misma carpeta:

```bash
python3 tools/generar.py --repos-dir ..
```

## Verla en Obsidian

Esta carpeta ya es una bóveda de Obsidian configurada: grafo con la Matriz al centro, los cerebros alrededor y los repositorios colgando de cada uno; la tabla `Repositorios.base` con tres vistas; y un estilo sobrio en claro y oscuro. Pasos para la Mac y el iPhone: **[docs/OBSIDIAN.md](docs/OBSIDIAN.md)**.

`notas/` es para notas propias y no se sube a GitHub.

## Privacidad

Este repositorio, el panel y el conector son públicos. Por eso:

- De los repositorios privados solo se publica nombre, cerebro y fecha de último cambio (`"detalle_privados": false`).
- Todo texto que viene de un repositorio (resumen, títulos y pendientes de su `CHANGELOG.md`) pasa por un filtro antes de publicarse: los números de expediente, correos, teléfonos, CURP, RFC y montos se tapan solos, y los nombres de `terminos_reservados` en `matriz.config.json` salen como «[cliente]». Para proteger otro nombre, agrégalo ahí.
- El panel y el conector piden a los buscadores no indexarlos y no escriben en ningún lado.

## Agregar un repositorio o un cerebro

Edita `matriz.config.json`: añade el nombre del repositorio a la lista `repos` de su cerebro (y a `privados` si lo es). Registra el cambio en `CHANGELOG.md`.
