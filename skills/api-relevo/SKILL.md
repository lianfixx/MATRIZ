---
name: api-relevo
description: Analiza cualquier proyecto ya hecho de Emi y pasa a la API de Claude lo que se puede, para ahorrar su suscripción, con relevo automático de la suscripción si la API falla (repara la causa y deja la API lista). Elige modelos, mide costos y propone mejoras. Funciona en Claude, ChatGPT/Codex, Grok y Kimi.
---

# api-relevo · la API trabaja, la suscripción releva

Regla de Emi (25/11/2026): **ahorrar la suscripción usando la API**; la suscripción **solo entra si la API falló**, repara el porqué de fondo, hace el trabajo de ese día y deja la API lista para que la próxima vez lo haga ella. Toda mejora queda en las dos vías y sincronizada (regla del 23/11/2026). Todo documentado y registrado (regla de noviembre de 2026).

Esta skill no es un proyecto: es el método para convertir cualquier proyecto que ya corre (repositorio, tarea programada, workflow) a ese esquema, medirlo y mejorarlo. Funciona igual con cualquier IA: ver [references/otras-ia.md](references/otras-ia.md).

## Cuándo usarla

- Emi pide «pasa esto a la API», «ahorra suscripción», «qué puede correr por API», «mide costos», «por qué falló la API», o un proyecto nuevo va a automatizarse.
- La revisión semanal de la Matriz la usa para proponer qué tarea mover y para reportar costos.
- Una tarea de relevo la usa para reparar una falla de la API.

## Procedimiento (siempre en este orden)

### 1. Entender el proyecto a fondo, sin suponer
1. Matriz primero: `matriz_general` del conector Matriz (o `MATRIZ_GENERAL.md` de `lianfixx/MATRIZ`): cerebro, repositorios, tareas programadas, skills, pendientes y reglas.
2. En el repositorio: `AGENTS.md`, `ia/REGLAS.md`, `ia/PROTOCOLO.md`, su SKILL.md y sus referencias, sus workflows y su `CHANGELOG.md`. La fuente de verdad es GitHub, no una conversación.
3. Tareas programadas: `list_triggers` (todas las páginas). Por cada una anota horario, modelo, última corrida, qué lee, qué escribe, qué herramientas usa y qué decide.
4. Escribe la ficha del proyecto con [references/analisis.md](references/analisis.md). Sin ficha no se diseña nada.

### 2. Clasificar cada paso (la decisión la toma la tabla, no el gusto)

| Clase | Cuándo | Dónde corre | Costo para Emi |
|---|---|---|---|
| **D · Determinista** | Comparar, contar, descargar, validar, sincronizar, calcular hashes: no requiere juicio | Script + GitHub Actions (o la computadora virtual) | Cero |
| **A · API** | Leer, clasificar, resumir o redactar con entradas que el código puede reunir y salidas que el código puede comprobar | Script + Actions con `ANTHROPIC_API_KEY` | Créditos de API (topes por espacio) |
| **S · Suscripción** | Necesita conectores (Gmail, Drive, Calendar), navegador, la Mac, la computadora virtual interactiva, juicio jurídico final, o algo que se envía a terceros | Tarea programada de Claude | Suscripción |
| **R · Relevo** | Siempre que haya A: la suscripción entra solo si A falló | Tarea programada que primero comprueba y termina en una línea | Casi cero si A cumplió |

Reglas para clasificar: primero intenta D; lo que queda, A; S solo por las razones de la tabla. Si una parte S tiene una parte D o A, se separa (por ejemplo, detectar si hay algo nuevo es D aunque procesarlo sea S: así la suscripción solo despierta cuando hay trabajo).

### 3. Elegir el modelo y el modo
Con [references/modelos-y-costos.md](references/modelos-y-costos.md): Haiku 5.5 para clasificar y extraer; Sonnet 5.5 para leer y redactar con criterio; Opus 5.5 para síntesis difíciles; Fable 5.2 solo para reparar código difícil en el relevo. Lote (50 %) cuando no corre prisa; caché cuando el prompt se repite. Estima el costo por corrida y al mes antes de construir y ponlo en la ficha.

### 4. Construir con el patrón común
[references/patron.md](references/patron.md): un script con salida comprobable por código, un `ESTADO_*.json` por corrida (estado, modelo, tokens, costo, motivo de falla), un workflow que nunca rompe lo demás, topes por corrida y por mes, el lanzador si hay hora límite (el reloj de GitHub no es confiable) y la tarea de relevo con la plantilla del patrón. Pruebas que reproduzcan el éxito y la falla. Registro en `CHANGELOG.md` con `Agente:`.

### 5. Privacidad (antes de enviar nada a la API)
- A la API solo va lo necesario para la tarea. Datos de clientes y expedientes solo con autorización expresa de Emi para ese proyecto, anotada en su `CHANGELOG.md` y en `docs/INTELIGENCIA.md` de la Matriz.
- Nada de la salida de la API va a un repositorio público si contiene datos de clientes; el material de trabajo va a un repositorio privado.
- En los registros de Actions de repositorios públicos solo conteos y costos.

### 6. Medir y sincronizar
- Cada corrida deja su costo en su estado; `scripts/costos.py` los junta por mes y por origen (con `--bitacora`, desde las bitácoras). Actualiza `docs/COSTOS_API.md` de la Matriz cuando cambie algo; la cifra oficial está en Claude Console.
- Sincronía de las dos vías: si cambias el procedimiento en el script (A), cambia en el mismo trabajo la tarea de relevo (S) con `update_trigger` y su documentación, y viceversa. Antes de cerrar, compara el texto de la tarea (`list_triggers`) con el script y la documentación: mismos archivos, mismos estados, mismas condiciones de entrada.

### 7. Proponer mejoras
Cada revisión semanal (o cuando Emi lo pida) entrega: qué tarea S podría pasar a D/A y cuánto ahorraría; qué tarea A cuesta de más (modelo más barato, lote, caché, menos contexto); qué falló y si el relevo dejó la API lista. Solo propone; Emi decide, salvo lo que ya autorizó.

## Límites que no cambian
No cambiar visibilidad de repositorios, no reescribir historial, no force-push ni `--no-verify`, no crear ni revocar llaves, no subir topes ni comprar crédito, no enviar correos a terceros. La plataforma no deja que una tarea sin nadie mirando haga commits en varios repositorios ni que envíe correos (comprobado el 25/11/2026): el aviso a Emi es el resumen de la tarea (aviso y correo de la propia tarea), y los cambios en varios repositorios se hacen en una sesión con Emi presente.

## Casos ya hechos (usar como ejemplo)
- **DOF Castorena** (`dof-juridico-monitor` + `dof-trabajo`): lector por API (Sonnet en lote, Opus síntesis, Haiku tablas), relevo documento por documento decidido por código, lanzador por la hora límite, guardia que repara con Fable. ~2 USD por corrida.
- **Guardián de la Matriz**: escaneo D diario, triaje A con Haiku (centavos), tarea de relevo S que solo entra si la API falló.
- **Segunda red de privacidad y revisión semanal de la Matriz**: A con Haiku y Sonnet; menos de 1 USD al mes.
- **Inspiración de Redes** (25/11/2026): sincronía D + análisis A con Sonnet y visión; relevo S.
- **INDEP · seguimiento diario** (25/11/2026, `lianfixx/INDEP`): la API como «colaborador automático» del protocolo de INDEP (dos lecturas independientes del PDF completo conciliadas por código, edición quirúrgica del Excel, entrega y correo preparado); la suscripción queda como responsable que comprueba, envía el correo y releva. Patrón para tareas con un único remitente.
- **Cierre diario Castorena**: analizado el 25/11/2026 y **no** movible a la API (depende de Drive, iCloud y la Mac, y de juicio sobre Excel de clientes); se queda en S. Ver la ficha en [references/analisis.md](references/analisis.md).
