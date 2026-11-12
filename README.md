# Matriz General

El mapa de todo el trabajo de Emi: una **Matriz**, sus **Cerebros** y, debajo, los repositorios y skills de cada uno. Se llena sola leyendo los repositorios de `lianfixx`; nadie la mantiene a mano.

**Para cualquier IA, adjunta un solo archivo → [MATRIZ_GENERAL.md](MATRIZ_GENERAL.md).** Ahí está todo: quién es Emi, sus reglas, el pulso de la semana y cada cerebro con sus repositorios, pendientes, tareas y skills. Todo nace y se registra desde aquí.

**Para verla:** el panel **https://matriz.milla-abogados.workers.dev** (3D, con métricas y edición con contraseña), Obsidian ([docs/OBSIDIAN.md](docs/OBSIDIAN.md)) o [MATRIZ.md](MATRIZ.md).

**Respaldo:** GitHub (este repositorio, con todo su historial), Obsidian en la Mac y Google Drive, carpeta privada «Matriz General» (documento de Google, `MATRIZ_GENERAL.md` y un .zip del repositorio; lo renueva la revisión semanal).

## Qué hay

| Archivo o carpeta | Qué es | Quién lo escribe |
|---|---|---|
| [`MATRIZ_GENERAL.md`](MATRIZ_GENERAL.md) | El archivo único para cualquier IA | Generador |
| [`MATRIZ.md`](MATRIZ.md) | Portada: cerebros, último movimiento y lo último que hizo cada IA | Generador |
| [`cerebros/`](cerebros) | Una nota por cerebro | Generador |
| [`repos/`](repos) | Una nota por repositorio: resumen, skills, últimos registros y pendiente | Generador |
| [`contexto/`](contexto) | Un archivo por cerebro para pegar o adjuntar en cualquier IA | Generador |
| [`bitacora/`](bitacora) | Qué IA hizo qué, por día, en todos los repositorios | Generador |
| `matriz.json` | Los mismos datos, con métricas, para el panel y el conector | Generador |
| `tablero/` | Pendientes y notas de Emi por cerebro (formato de tareas de Obsidian) | Emi, desde el panel |
| `proyectos/` | Proyectos nuevos; la revisión semanal pide su repositorio | Emi, desde el panel |
| [`EMI.md`](EMI.md) | Quién es Emi, dónde trabaja y las reglas que valen siempre | A mano |
| [`matriz.config.json`](matriz.config.json) | Qué cerebros existen y qué repositorio va en cuál | A mano |
| [`inventario.json`](inventario.json) | Tareas programadas, skills instaladas en Claude y vencimientos | Revisión semanal |
| [`revisiones/`](revisiones) | Informe de cada revisión semanal | Revisión semanal |
| `tools/generar.py` | El generador | A mano |
| `Repositorios.base`, `.obsidian/` | Tabla y configuración de Obsidian (grafo, estilo, complemento Git) | A mano |
| `panel/`, `tools/panel.py`, `tools/three/`, `wrangler.jsonc` | Panel web en Cloudflare: https://matriz.milla-abogados.workers.dev ([docs/PANEL.md](docs/PANEL.md)) | A mano |
| `worker/` | Conector MCP de solo lectura para cualquier IA en `/mcp` ([docs/CONECTAR_IA.md](docs/CONECTAR_IA.md)) y la edición del panel en `/api` | A mano |
| `notas/` | Notas propias de Emi; no se suben a GitHub | Emi |
| `AGENTS.md`, `ia/` | Protocolo común entre IA, igual que en los demás repositorios | A mano |

## Cómo se actualiza

Cada semana, el domingo a las 20:13, una tarea programada de Claude hace la [revisión semanal](docs/REVISION_SEMANAL.md): agrega repositorios nuevos, actualiza tareas programadas y skills, revisa la salud y avisa de vencimientos.

El workflow «Actualizar la Matriz» corre cada día a las 06:17 (hora del centro de México), cuando cambia la configuración, después de cada edición desde el panel y a mano desde la pestaña Actions. Lee el `README.md`, el `CHANGELOG.md` y las skills de cada repositorio y reescribe el índice.

Para leer los repositorios privados usa el secreto `MATRIZ_TOKEN`: el token de GitHub de grano fino «MATRIZ lectura», con acceso a **todos** los repositorios de `lianfixx` y solo **Contents: Read-only** (vence el 9 de febrero de 2027; la revisión semanal avisa antes). Con ese acceso, un repositorio nuevo aparece solo en «Repositorios nuevos por clasificar». Después de cada actualización, «Publicar panel» sube el panel y el conector a Cloudflare. Sus secretos están explicados en [docs/PANEL.md](docs/PANEL.md#cómo-se-publica).

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
- Todo texto que viene de un repositorio (resumen, títulos y pendientes de su `CHANGELOG.md`) pasa por un filtro antes de publicarse: los números de expediente, correos, teléfonos, CURP, RFC y montos se tapan solos, y los nombres de clientes guardados en el secreto `MATRIZ_RESERVADOS` (separados por coma; no se escriben en el repositorio) salen como «[cliente]». Para proteger otro nombre, agrégalo a ese secreto.
- El panel rechaza al escribir cualquier texto que parezca dato de cliente. Ver y el conector no piden contraseña; editar sí, y solo toca `tablero/` y `proyectos/`.
- El panel y el conector piden a los buscadores no indexarlos.

## Agregar un repositorio o un cerebro

Edita `matriz.config.json`: añade el nombre del repositorio a la lista `repos` de su cerebro (y a `privados` si lo es). Registra el cambio en `CHANGELOG.md`.
