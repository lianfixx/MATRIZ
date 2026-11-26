# Análisis de un proyecto (ficha obligatoria)

Antes de diseñar, llena esta ficha en el `CHANGELOG.md` o en la documentación del proyecto. Todo dato sale del repositorio, de `list_triggers` o de los registros, nunca de memoria.

```
Proyecto · repositorio · cerebro
Tarea programada: nombre · horario · modelo · última corrida y resultado
Qué lee (fuentes, conectores, archivos) · qué escribe · a quién llega
Pasos: por cada uno, clase D/A/S (tabla del SKILL.md) y por qué
Datos sensibles que tocaría la API · autorización de Emi (fecha y dónde)
Modelo y modo por paso · tokens estimados · costo por corrida y al mes · tope del espacio
Cómo se comprueba con código la salida de la API
Qué hace el relevo si la API falla · qué solo puede hacer Emi
Ahorro esperado de suscripción (corridas al mes que dejan de usarla)
```

## Fichas hechas el 25/11/2026

**Redes · análisis de inspiración del panel** (tarea «Redes: analizar inspiración del panel», 13:17 y 21:17, Sonnet, suscripción).
- Pasos: leer estado del panel (D); sincronizar con el panel lo publicado o programado por cada skill (S: empatar piezas pide criterio, pero *detectar* que hay algo nuevo es D); analizar inspiraciones con miniatura (A, Sonnet con imagen); proponer espacio de notas (A, Haiku).
- Medido: el 25/11/2026 había 0 inspiraciones y 0 notas pendientes: casi todas las corridas de la suscripción no tenían trabajo.
- Construido: `tools/redes_api.py` en cada «Actualizar la Matriz»; estado público `automatizaciones/redes-api.json` (solo conteos, costo y la firma de lo publicado). La suscripción entra solo si la API falló o si la firma de lo publicado cambió desde su última sincronía (`red/sync-panel.json` de `lianfixx/redes`).
- Costo esperado: centavos por inspiración (Sonnet con una imagen); notas, milésimas.
- Requisito: el secreto `REDES_CLAUDE_LLAVE` en `lianfixx/MATRIZ`. Sin él, el estado es `no_configurado` y la suscripción hace la tarea completa, como antes.

**Cierre diario de la Matriz Castorena** (18:43, suscripción) — **no se mueve a la API**.
- La secuencia (`cerebro/skill/references/operacion.md`) busca versiones nuevas en Drive y en conversaciones, compara Excel de clientes con criterio jurídico, sincroniza Escritorio, iCloud y Drive y comprueba cada destino: todo eso es S (conectores, Mac y juicio). La parte D ya existe: `auditoria-hashes.yml` corre sin IA.
- Ahorro posible sin tocar el procedimiento: una puerta D que diga si hubo fuentes nuevas para que el cierre «sin cambios» sea corto. Requiere acceso de Actions a Drive (cuenta de servicio de Google que hoy no existe): propuesta para Emi.

**INDEP · seguimiento** (cada hora, lunes a viernes, suscripción) — pendiente de explicación y decisión de Emi (25/11/2026).
