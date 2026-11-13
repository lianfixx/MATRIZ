# Panel de la Matriz

**https://matriz.milla-abogados.workers.dev**: la Matriz como herramienta, en la Mac o el iPhone, sin instalar nada. Verla no pide nada; para cambiar algo se entra con contraseña.

## Qué se ve

- **Al centro, la Matriz en 3D.** El punto naranja es la Matriz; cada esfera blanca es un cerebro. Su tamaño es lo que se movió esta semana; si lleva más de 21 días quieto se apaga; si tiene algo vencido o una tarea que falló, late con un anillo. Sus repositorios giran alrededor. Se gira arrastrando, se acerca con la rueda o pellizcando; al tocar un cerebro la cámara va hacia él y se abre su hoja.
- **«Hoy» (a la izquierda; en el iPhone, debajo):**
  - Esta semana: commits en todos los repositorios, comparado con la semana pasada, y la curva de 8 semanas.
  - Atención: pendientes vencidos, tareas programadas que fallaron, llaves por vencer, repositorios sin clasificar.
  - Pendientes de todos los cerebros, del más urgente al menos.
  - Pulso por cerebro y quién trabajó (cada IA) en los últimos 60 días.
  - «Llevar la Matriz a otra IA»: copiar o descargar `MATRIZ_GENERAL.md` y la dirección del conector.
- **Hoja de cada cerebro:** commits de la semana, días sin movimiento, pendientes, notas, repositorios con su actividad, tareas programadas y skills, y «Copiar contexto».
- **Buscar** (⌘K): repositorios, skills, pendientes y cerebros.
- **«Copiar para una IA»:** copia la Matriz General completa para pegarla en cualquier chat.

## En vivo

La página se actualiza sola: cada minuto (y al volver a la pestaña) revisa si hay datos nuevos y los pinta sin recargar; el punto verde junto a la fecha late cuando llegan. Si estás escribiendo, espera a que termines. La Matriz se regenera:

- **En cuanto cambia cualquiera de tus repositorios**: GitHub avisa al panel (`/gancho`, aviso firmado con `GANCHO_SECRETO`) y el panel pide la actualización. De un cambio a verlo en la página pasan unos 2 a 4 minutos.
- **Cada 15 minutos**, por si un aviso se pierde (GitHub puede retrasar este horario unos minutos).
- **Después de cada edición desde el panel.**

Solo se guarda y se publica si algo cambió.

## Qué se edita (con contraseña)

| Dónde | Qué | Archivo que cambia |
|---|---|---|
| Hoja del cerebro | Agregar pendiente (con prioridad alta y fecha), completarlo, cambiar prioridad o fecha, editarlo, borrarlo | `tablero/<cerebro>.md` |
| Hoja del cerebro | Escribir o borrar una nota | `tablero/<cerebro>.md` |
| «Hoy» → Proyecto nuevo | Nombre, cerebro y de qué se trata | `proyectos/<nombre>.md` |

Cada cambio es un commit en GitHub firmado «IA-Actor: Panel de la Matriz (Emi)». Después, solo:

1. «Actualizar la Matriz» regenera todo (incluida `MATRIZ_GENERAL.md`) y «Publicar panel» lo sube (2 a 4 minutos).
2. Obsidian lo trae en su siguiente sincronización (cada 10 minutos): el tablero aparece dentro de la nota de cada cerebro. Los tableros usan el formato de tareas de Obsidian (`- [ ] … 🔺 📅 AAAA-MM-DD`).
3. La revisión del domingo crea el repositorio de cada proyecto nuevo (encargo para Muse, con el protocolo).

La Matriz es pública: el panel rechaza textos que parecen datos de cliente (nombres reservados, expedientes, correos, teléfonos, CURP, RFC, montos) y lo dice en pantalla.

## Seguridad

- Contraseña propia (`PANEL_CLAVE`). La sesión dura 30 días en ese equipo: cookie `HttpOnly`, `Secure`, `SameSite=Strict`, firmada. Un intento fallido espera 800 ms. «Salir» la cierra.
- El Worker escribe con un token de GitHub que solo puede tocar `lianfixx/MATRIZ` (`MATRIZ_ESCRITURA`) y solo los archivos `tablero/` y `proyectos/`. Revisa el origen de cada petición.
- Encabezados: CSP estricta (solo código del propio panel), sin marcos, sin cámara, micrófono ni ubicación, no indexar.
- three.js se sirve desde el propio panel; no se carga nada de terceros.

## Cómo se publica

`tools/panel.py` arma `dist/` (panel, `matriz.json`, `contexto/`, `EMI.md`, `MATRIZ_GENERAL.md`, `llms.txt`, encabezados) y three.js con esbuild y las versiones fijas de `tools/three/`. El workflow «Publicar panel» prueba el Worker (`node worker/prueba.mjs`) y publica en Cloudflare Workers (plan gratis) cada vez que «Actualizar la Matriz» termina bien o cambia `panel/`, `worker/` o `tools/three/`.

Secretos del repositorio (GitHub → Settings → Secrets and variables → Actions):

| Secreto | Para qué | Si falta |
|---|---|---|
| `CLOUDFLARE_API_TOKEN` | Publicar. Llave «MATRIZ panel (GitHub Actions)» en Cloudflare → Mi perfil → Tokens de API (plantilla «Edit Cloudflare Workers») | No publica |
| `CLOUDFLARE_ACCOUNT_ID` | Cuenta de Cloudflare de Emi | No publica |
| `PANEL_CLAVE` | La contraseña de Emi para editar | El panel se ve, no edita |
| `MATRIZ_ESCRITURA` | Token de grano fino «MATRIZ escritura»: solo `lianfixx/MATRIZ`, Contents lectura y escritura | El panel se ve, no edita |
| `MATRIZ_RESERVADOS` | Nombres de clientes que nunca se publican ni se aceptan, separados por coma | Solo se filtran los formatos (expedientes, correos…) |

Los secretos solo existen en el paso de publicar; los tres últimos se copian como secretos del Worker en cada publicación.

## Para otras IA

`/llms.txt` (mapa), `/MATRIZ_GENERAL.md` (todo en un archivo), `/matriz.json` (datos), `/contexto/<cerebro>.CONTEXTO.md` y el conector MCP en `/mcp` ([CONECTAR_IA.md](CONECTAR_IA.md)).

## Mantenimiento sin códigos

Emi pidió (12/11/2026) que GitHub y Cloudflare no le pidan códigos ni verificaciones. Por eso el mantenimiento no usa sus páginas (que piden confirmar identidad) sino sus API, con dos llaves limitadas guardadas en la computadora virtual de Emi (box «main»), en `~/.config/matriz/`, legibles solo por su usuario:

| Llave | Puede | No puede | Vence |
|---|---|---|---|
| GitHub «Matriz administración (Claude)» (`github-admin`) | Secretos, variables y workflows de los repositorios de Emi | Leer ni cambiar código | 12/11/2027 |
| Cloudflare «Matriz administración (Claude)» (`cloudflare-admin`) | Crear y renovar llaves de API («Tokens de API: Editar») | Nada más | 12/11/2027 |

En la computadora virtual:

- `node ~/.config/matriz/renovar-cloudflare.mjs`: renueva «MATRIZ panel (GitHub Actions)» en Cloudflare, la comprueba y la guarda en el secreto `CLOUDFLARE_API_TOKEN`.
- `printf '%s' "$VALOR" | node ~/.config/matriz/secreto.mjs <repositorio> <NOMBRE>`: crea o cambia cualquier secreto de Actions.
- `~/bin/matriz-gh <ruta de la API> [método] [json]`: llamadas a la API de GitHub; por ejemplo, volver a publicar el panel: `~/bin/matriz-gh repos/lianfixx/MATRIZ/actions/workflows/publicar-panel.yml/dispatches POST '{"ref":"main"}'`.

Ningún valor se imprime ni pasa por una conversación. Los vencimientos están en `inventario.json` y la revisión del domingo avisa 21 días antes. Para revocarlas: GitHub → Settings → Developer settings → Fine-grained tokens, y Cloudflare → Mi perfil → Tokens de API.
