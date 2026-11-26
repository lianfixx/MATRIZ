# Modelos y costos de la API de Claude

Precios de lista en USD por millón de tokens, verificados el 25/11/2026 en la documentación oficial de precios (platform.claude.com/docs/en/about-claude/pricing) y en reportes de terceros que la citan. **Vuelve a verificarlos** antes de un cambio grande: cambian.

| Modelo (id) | Entrada | Salida | Caché leída | Úsalo para |
|---|---|---|---|---|
| Haiku 5.5 (`claude-haiku-5-5`), prompt ≤ 100 000 tokens | 0.10 | 0.50 | 0.01 | Clasificar, extraer, triaje, revisar privacidad, tablas de cifras |
| Haiku 5.5, prompt > 100 000 tokens | 0.50 | 2.50 | 0.05 | Mejor partir el texto en bloques más chicos |
| Sonnet 5.5 (`claude-sonnet-5-5`) | 2 | 10 | 0.10 | Leer con criterio, redactar, analizar imágenes, revisión semanal |
| Opus 5.5 (`claude-opus-5-5`) | 4 | 20 | 0.20 | Síntesis difícil de muchas notas, decisiones con mucho contexto |
| Fable 5.2 (`claude-fable-5-2`) | 8 | 40 | 0.20 | Solo para reparar código difícil en un relevo; nunca para trabajo diario |

- **Lote (Message Batches): 50 % menos** en entrada y salida. Para todo lo que no necesita respuesta en minutos (el DOF lee por lote).
- **Caché:** cuando el mismo prompt de sistema o documento se repite, la lectura en caché cuesta entre 2.5 % y 10 % de la entrada normal.
- **Salida estructurada:** pide JSON con esquema (`output_config.format`, ver `tools/inteligencia.py` de la Matriz); Sonnet 5.5 rechaza forzar una herramienta con `tool_choice` (comprobado el 23/11/2026).
- **Estimar antes de construir:** tokens ≈ caracteres / 3 en español. Costo = entrada × precio + salida × precio. Multiplica por corridas al mes y compara con el tope del espacio.

## Espacios y topes de Emi (Claude Console)

| Espacio | Proyectos | Tope al mes | Aviso |
|---|---|---|---|
| `castorena-dof` | Lector del DOF | 60 USD | 30 USD |
| `matriz` | Segunda red, revisión semanal, Guardián, inspiración de Redes | 10 USD | 5 USD |

Sin recarga automática. Si un tope se alcanza, la API falla y entra el relevo; el relevo no sube topes ni compra crédito: avisa a Emi.

## Costos medidos (ver `docs/COSTOS_API.md` de la Matriz para el detalle)
- DOF: ~2 USD por corrida en lote (552 páginas). 15–25 USD al mes.
- Matriz: segunda red ~0.15, semanal ~0.17, Guardián < 0.01 USD al mes.

## Otras IA
Mismo método con sus API (OpenAI, xAI para Grok, Moonshot para Kimi). Sus precios y modelos cambian seguido: consúltalos en su página oficial el día que diseñes y anótalos en la ficha con la fecha. Ver [otras-ia.md](otras-ia.md).
