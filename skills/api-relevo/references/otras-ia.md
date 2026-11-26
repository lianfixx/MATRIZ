# Usar api-relevo con otras IA

El método no depende de Claude. Cualquier IA que lea este archivo y el SKILL.md puede aplicarlo.

| IA | Cómo cargar la skill | Vía API equivalente | Llave (secreto) |
|---|---|---|---|
| ChatGPT / Codex | Pega `SKILL.md` y estas referencias como instrucciones del proyecto, o deja que Codex lea `skills/api-relevo/` del repositorio | API de OpenAI | `OPENAI_API_KEY` |
| Grok (X) | Instrucciones personalizadas o proyecto con estos archivos | API de xAI | `XAI_API_KEY` |
| Kimi | Proyecto o mensaje inicial con estos archivos | API de Moonshot | `MOONSHOT_API_KEY` |
| Gemini, Muse, DeepSeek | Igual: el texto es Markdown plano, sin funciones propias de ninguna plataforma | Su API | `<PROVEEDOR>_API_KEY` |

Reglas al cambiar de proveedor:
- El contrato del estado (`patron.md`) no cambia: `estado`, `motivo`, `modelo`, tokens y `costo_usd`. Así el relevo y la medición funcionan igual.
- Elige el modelo por el mismo criterio (barato para clasificar, medio para leer y redactar, el mejor solo para reparar) y anota en la ficha el precio oficial del día.
- La llave nunca va en el código ni en el chat: secreto del repositorio, creado desde la computadora virtual de Emi.
- La privacidad es la misma: datos de clientes solo con autorización expresa de Emi para ese proyecto y ese proveedor.
- Hoy solo existe la llave de Claude (`ANTHROPIC_API_KEY`). Usar otro proveedor requiere que Emi cree su llave; pídeselo con el encargo listo.
- Sin terminal ni escritura (ChatGPT web, Grok, Kimi), entrega el análisis, el plan y un «Registro pendiente para el repositorio»; la construcción la hace Claude Code o Codex.
