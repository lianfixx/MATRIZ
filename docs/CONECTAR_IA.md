# Conectar cualquier IA a la Matriz

**Lo más sencillo: adjunta un solo archivo, `MATRIZ_GENERAL.md`.** Tiene todo: quién es Emi, sus reglas, el pulso de la semana, cada cerebro con sus repositorios, pendientes, tareas y skills, y cómo trabajar. Se regenera solo cada día y después de cada edición. Está en el repositorio, en el panel (`/MATRIZ_GENERAL.md`, o el botón «Copiar para una IA»), en Obsidian y en Google Drive (carpeta «Matriz General»).

Además, la Matriz está en tres lugares que se actualizan solos. Cualquier IA entra por el que pueda usar:

| Puerta | Dirección | Para |
|---|---|---|
| Conector MCP (solo lectura) | `https://matriz.milla-abogados.workers.dev/mcp` | IA que aceptan conectores MCP remotos |
| Panel y archivos | `https://matriz.milla-abogados.workers.dev` · `/MATRIZ_GENERAL.md` · `/llms.txt` · `/matriz.json` · `/contexto/<cerebro>.CONTEXTO.md` · `/EMI.md` | IA que leen páginas web |
| GitHub | `https://github.com/lianfixx/MATRIZ` y cada repositorio | IA que leen y escriben en GitHub |

El conector y el panel solo muestran lo que ya es público en el repositorio MATRIZ: de los repositorios privados, nombre, cerebro y fecha. **El trabajo se hace y se registra en GitHub**, en el repositorio que toque, con la línea `Agente:`. El conector no escribe; los pendientes, notas y proyectos de Emi se editan en el panel con su contraseña ([PANEL.md](PANEL.md)).

## Herramientas del conector

| Herramienta | Qué devuelve |
|---|---|
| `matriz_general` | El archivo único completo. Úsalo para entenderlo todo de una vez. |
| `matriz_resumen` | Cerebros, último movimiento, avisos y cómo trabajar. Empezar aquí si no hace falta todo. |
| `cerebro` | Repositorios, último registro, pendientes, tareas programadas y skills de un cerebro. |
| `contexto` | El texto para continuar el trabajo de un cerebro. |
| `pendientes` | Pendientes abiertos y vencidos del tablero de Emi, de un cerebro o de todos. |
| `metricas` | Commits por semana, días sin movimiento, pendientes, tareas que fallaron, quién trabaja y vencimientos. |
| `ultimos_cambios` | Lo último que hizo cada IA. |
| `reglas_de_emi` | Quién es Emi y las reglas que valen siempre. |
| `search`, `fetch` | Búsqueda y apertura de resultados (el formato que pide ChatGPT). |

## Por IA

**Claude (claude.ai, app y Claude Code).** Ajustes → Conectores → «Agregar conector personalizado» → nombre `Matriz`, URL `https://matriz.milla-abogados.workers.dev/mcp`. No pide inicio de sesión. Para escribir, Claude Code trabaja directo en los repositorios. En Claude Code también: `claude mcp add --transport http matriz https://matriz.milla-abogados.workers.dev/mcp`.

**ChatGPT (Pro).** Ajustes → Apps y conectores → Configuración avanzada → activar «Modo desarrollador» → «Crear» → URL `https://matriz.milla-abogados.workers.dev/mcp`, sin autenticación. En Pro los conectores propios son de lectura, que es justo lo que ofrece este. Para escribir: Codex sobre el repositorio (lee `AGENTS.md`).

**Gemini.** Los conectores propios de la app de Gemini solo están disponibles en EE. UU. Pídele que lea `https://matriz.milla-abogados.workers.dev/llms.txt`, o adjunta `MATRIZ_GENERAL.md` (botón «Copiar para una IA» del panel). Para escribir: Jules sobre el repositorio, o Antigravity CLI con el conector (`mcp_config.json` con la URL de arriba).

**Muse (Meta).** Dale la dirección del panel y de `llms.txt`: Muse navega como una persona. Si pide crear un conector, usa la API `https://matriz.milla-abogados.workers.dev/matriz.json`. Para escribir en GitHub, Muse usa el sitio de GitHub con la sesión de Emi y registra con `Agente: Muse`. Muse Code acepta el conector MCP.

**DeepSeek.** No tiene conectores. Adjunta `MATRIZ_GENERAL.md` o pega el contexto del cerebro (botón «Copiar contexto» de su hoja en el panel). No le pases datos de clientes: su política permite guardar datos en China y usarlos para entrenar. Sin escritura: termina con «Registro pendiente para el repositorio».

**Cualquier otra (Cursor, Copilot, Windsurf…).** Conector MCP con la URL de arriba, o `AGENTS.md` del repositorio.

## Probar el conector

```bash
curl -s https://matriz.milla-abogados.workers.dev/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"matriz_resumen","arguments":{}}}'
```

Las pruebas automáticas están en `worker/prueba.mjs` y corren antes de cada publicación.
