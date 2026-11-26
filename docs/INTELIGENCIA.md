# Inteligencia de la Matriz (API de Claude)

Desde el 23/11/2026 la Matriz usa la API de Claude para tres cosas. Todo lo hace `tools/inteligencia.py`, paga con los **créditos de API** del plan Max de Emi (nunca con la suscripción) y **solo propone o avisa**: ninguna decisión se toma sola.

| Función | Cuándo | Modelo | Qué deja |
|---|---|---|---|
| Segunda red de privacidad | En cada actualización que trae líneas nuevas | Haiku 5.5 | Un aviso en Issues si queda un posible dato de cliente o personal |
| Retroalimentación semanal | Domingo, antes de la revisión de las 20:13 | Sonnet 5.5 | `revisiones/AAAA-MM-DD-ia.md` y `.json` |
| Propuesta de clasificación | Domingo, mismo archivo | Haiku 5.5 | A qué cerebro va cada repositorio nuevo, con su confianza |
| Redes · inspiración y notas | En cada actualización, solo si hay pendientes | Sonnet 5.5 (con la miniatura) y Haiku 5.5 | En el panel de Redes: análisis de cada inspiración y espacio de cada nota (`tools/redes_api.py`) |
| Triaje del Guardián | Diario, con el Guardián, solo si hay hallazgos nuevos | Haiku 5.5 | En el repositorio privado `guardian-detalle`: veredicto por hallazgo para la reparación automática ([GUARDIAN.md](GUARDIAN.md)) |

## Cómo encaja

- **Segunda red.** Es un paso de «Actualizar la Matriz», entre «Generar» y «Guardar». Lee solo las líneas nuevas de los archivos generados, ya pasadas por `reservar()`. Si marca algo con confianza de 0.85 o más, abre o actualiza el aviso «Segunda red de privacidad». El aviso dice archivo, línea y categoría; **nunca copia el texto**. No detiene la publicación: es un aviso, no un freno.
- **Revisión semanal de la IA.** Workflow «Inteligencia semanal (API)». Lee la bitácora pública de los últimos siete días y la tabla de actividad. Cada punto debe citar repositorios y días; el script comprueba que existan juntos en la bitácora y descarta lo que no pueda comprobar. La revisión semanal de Claude (domingo 20:13, [REVISION_SEMANAL.md](REVISION_SEMANAL.md)) empieza leyendo ese archivo y decide qué aplicar; si todavía no existe, ella misma lanza el workflow y lo espera. El reloj de GitHub (domingo 19:07) es solo un respaldo, porque dispara con horas de retraso o no dispara: una corrida suya que llegue tarde no repite la revisión ni gasta.
- **Clasificación.** Solo para repositorios nuevos públicos. Con confianza menor a 0.80, o con un cerebro que no existe, queda como «preguntar a Emi». Los privados sin cerebro no se nombran ni se envían: los clasifica la revisión de Claude.

- **Prueba semanal de la red.** Cada domingo el mismo workflow manda a Haiku dos líneas ficticias, una con datos inventados. Si no la marca, la corrida queda en rojo y GitHub avisa por correo. Así se sabe que la red sigue viendo, aunque en la semana no haya marcado nada.

## Reglas

1. **Nada nuevo se expone.** A la API solo se envía lo que ya es público o está por publicarse. Nunca contenido de repositorios privados. Excepción acotada (triaje del Guardián, 25/11/2026): de los hallazgos de repositorios privados se envían chequeo, tipo, gravedad, nombre del repositorio y extensión del archivo; nunca su ruta, su contenido ni el dato. Redes (25/11/2026, autorización de Emi): las inspiraciones (publicaciones públicas que Emi guardó, con su nota) y las notas de contenido del panel van a la API para analizarlas; nada de eso se guarda en este repositorio.
2. **Registros mudos.** Este repositorio es público y sus registros de Actions también: el script solo imprime conteos, tokens y costo.
3. **Si falla, no pasa nada.** Sin llave, sin crédito o con la API caída, el paso termina sin error y la Matriz se actualiza igual.
4. **No decide.** No edita `matriz.config.json`, no crea cerebros y no toca otros repositorios.
5. **Todo queda registrado.** La corrida semanal agrega su entrada a `CHANGELOG.md` (línea `Agente: GitHub Actions · API de Claude`), y el `.json` guarda modelo, tokens, costo, SHA-256 de la entrada y de la salida y el número de corrida.

## Costo y topes

- Precios usados (USD por millón de tokens, 20/11/2026): Haiku 5.5, 0.10 de entrada y 0.50 de salida; Sonnet 5.5, 2 y 10.
- Revisión semanal: hasta unos 0.10 USD por corrida (tope de 8 000 tokens de salida, que incluye el razonamiento del modelo). Segunda red: milésimas de dólar por actualización. Estimado total: menos de 2 USD al mes.
- Topes del script: 400 líneas por llamada y 2 llamadas por actualización en la segunda red; 60 000 caracteres de bitácora en la semanal.
- Tope duro: el espacio de trabajo `matriz` de Claude Console tiene límite de 10 USD al mes y aviso a los 5. La llave vive en el secreto `ANTHROPIC_API_KEY` de este repositorio. No hay recarga automática.

## Detalle técnico

Las respuestas se piden con salida estructurada (`output_config.format`, JSON con esquema) de la Messages API. Forzar una herramienta con `tool_choice` no sirve: Sonnet 5.5 lo rechaza con HTTP 400 (comprobado el 23/11/2026).

## Probar sin gastar

```
python3 tools/inteligencia.py semanal --seco
python3 tools/inteligencia.py red --seco
python3 -m unittest discover -s tools -p 'test_*.py'
```

En GitHub: Actions → «Inteligencia semanal (API)» → Run workflow, con «seco» activado.

## Apagar

- Semanal: Actions → «Inteligencia semanal (API)» → menú «…» → Disable workflow.
- Segunda red: borrar el secreto `ANTHROPIC_API_KEY` (el paso se salta solo) o quitar el paso del workflow.

## Pendiente de decidir

La segunda red hoy solo avisa. Convertirla en freno (retener la línea antes de publicar) exige guardar qué se retuvo sin publicarlo; se decide después de observar dos semanas cuántas falsas alarmas da.
