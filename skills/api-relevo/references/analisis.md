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
- Construido: `tools/redes_api.py` en cada «Actualizar la Matriz»; estado público `automatizaciones/redes-api.json` (solo conteos, costo y los ids públicos que faltan por sincronizar). La suscripción entra solo si la API falló o si alguna publicación o programación de las skills todavía no consta en el panel (la API lo compara sin IA con la clave `externa.clave` y el enlace de cada pieza; no hace falta registrar la sincronía en otro repositorio).
- Costo esperado: centavos por inspiración (Sonnet con una imagen); notas, milésimas.
- Requisito: el secreto `REDES_CLAUDE_LLAVE` en `lianfixx/MATRIZ`. Sin él, el estado es `no_configurado` y la suscripción hace la tarea completa, como antes.

**Cierre diario de la Matriz Castorena** (18:43, suscripción) — **no se mueve a la API**.
- La secuencia (`cerebro/skill/references/operacion.md`) busca versiones nuevas en Drive y en conversaciones, compara Excel de clientes con criterio jurídico, sincroniza Escritorio, iCloud y Drive y comprueba cada destino: todo eso es S (conectores, Mac y juicio). La parte D ya existe: `auditoria-hashes.yml` corre sin IA.
- Ahorro posible sin tocar el procedimiento: una puerta D que diga si hubo fuentes nuevas para que el cierre «sin cambios» sea corto. Requiere acceso de Actions a Drive (cuenta de servicio de Google que hoy no existe): propuesta para Emi.

**INDEP · seguimiento diario** (tarea «INDEP seguimiento diario (Claude)», cada hora de 09:04 a 17:04 entre semana, Opus, suscripción). Autorizado por Emi el 25/11/2026, incluido que la API vea los datos.
- Medido: la corrida pesada es la de las 09:04 (unos 6 minutos de Opus leyendo el boletín de unas 16 páginas, cotejando 29 asuntos, actualizando el maestro, publicando la entrega y enviando el correo); las otras ocho horas terminan en segundos.
- Pasos: índice, descarga y validadores (D); lectura íntegra y cotejo (A, dos lecturas independientes: Opus y Sonnet, conciliadas por código contra el texto del PDF); Detalles y Fuente de coincidencias exactas (A, Opus redacta y Sonnet revisa); maestro, entrega, continuidad, manifiesto y pre-cotejo (D); correo diario (S: Gmail y la regla del único remitente); Drive (S, hoy pendiente por cuota).
- Construido en `lianfixx/INDEP`: `scripts/seguimiento_api.py` + workflow `seguimiento-api.yml` (colaborador automático sin correo), pruebas sin costo con el caso real del boletín 205, estado `ESTADO_API.json`. La tarea programada quedó en relevo: lanza el workflow, comprueba la entrega, envía el correo; si la API no cuadra o falla, hace todo como siempre y repara.
- Costo esperado: 0.5 a 0.8 USD por boletín; 11 a 18 USD al mes. Topes: 3 por corrida, 25 al mes.
- Falta: el secreto `ANTHROPIC_API_KEY` en `INDEP` y la prueba en real (modo prueba sobre las entregas 54 y 55). Mientras tanto queda `no_configurado` y la suscripción trabaja como hoy.
