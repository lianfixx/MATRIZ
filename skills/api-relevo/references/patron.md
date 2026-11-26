# Patrón API con relevo (contrato común)

Es el mismo en todos los proyectos de Emi. Copia las plantillas de `../plantillas/`.

## Piezas

1. **Script de la vía API** (`tools/<tarea>_api.py` o similar). Reúne la entrada con código, llama a la API con salida estructurada, **comprueba con código** cada respuesta (citas que existen, códigos válidos, cobertura completa) y escribe el estado. Nunca deja que el modelo decida qué se cubre: lo decide el código.
2. **Estado por corrida** (`ESTADO_<TAREA>.json` o un campo `api` dentro de la salida):
   ```json
   {"fecha": "AAAA-MM-DD", "estado": "ok | sin_novedades | parcial | fallo",
    "motivo": "texto corto si no es ok", "modelo": "claude-…", "entrada": 0, "salida": 0,
    "costo_usd": 0.0, "lote": false, "run_id": "…", "version": "x.y.z"}
   ```
   `ok` y `sin_novedades` significan que la suscripción no tiene que entrar.
3. **Workflow** (`plantillas/workflow-api.yml`): `continue-on-error`, tope de minutos, llave en secreto, solo conteos y costo en el registro, salida privada a un repositorio privado si hay datos.
4. **Lanzador** cuando hay hora límite: el reloj de GitHub dispara con horas de retraso o no dispara (medido el 23/11/2026). Una tarea programada mínima (Haiku) lanza el workflow si no hay corrida válida reciente. Si no hay hora límite, basta con encadenarlo a otro workflow que sí corre (`workflow_run`) o al de la Matriz.
5. **Tarea de relevo** (`plantillas/relevo-prompt.md`): primero comprueba el estado del día y termina en una línea si está `ok`; si no, diagnostica con datos, repara la causa de fondo (subagente Fable alto; si no, Opus alto), prueba, registra, relanza la API y confirma; si la falla no es de código (llave, tope, pago), hace el trabajo del día y le dice a Emi qué hacer.
6. **Topes**: por corrida en el script (corta y deja `parcial` antes de pasarse) y por mes en el espacio de Console.
7. **Registro y sincronía**: cada cambio en `CHANGELOG.md` con `Agente:`; el script, la tarea de relevo y la documentación cambian juntos.

## Señales de que algo está mal diseñado
- La suscripción entra seguido: la API falla por algo que el código podría evitar (respuesta cortada, contexto grande). Parte la entrada, sube `max_tokens`, usa lote.
- El costo crece sin que crezca el trabajo: falta caché, se relee lo ya leído, se usa un modelo más caro de lo necesario.
- La tarea de relevo hace más que comprobar en días normales: su primer paso no es lo bastante corto.
