---
tipo: "contexto"
cerebro: "Castorena"
generado: "tools/generar.py · no editar a mano: se reescribe cada día"
---

# Contexto para cualquier IA · Castorena

Soy Emi (Yohualli Emiliano García Milla). Este es el cerebro «Castorena» de mi Matriz General (https://github.com/lianfixx/MATRIZ · https://matriz.milla-abogados.workers.dev). Castorena Abogados, el despacho donde trabaja Emi: matriz de expedientes, INDEP, escritos y monitor del DOF.

## Cómo trabajar

1. La fuente de verdad es GitHub (`lianfixx`), no esta conversación ni lo que recuerdes.
2. Antes de cambiar un repositorio, lee su `AGENTS.md`, `ia/REGLAS.md` e `ia/PROTOCOLO.md`.
3. Todo cambio se registra en el mismo commit, en `CHANGELOG.md`, con la línea `Agente:`.
4. Si no puedes escribir en el repositorio, termina con un bloque «Registro pendiente para el repositorio» con la entrada completa y los cambios exactos. No digas «guardado» si no escribiste.
5. No envíes correos, no publiques, no contrates ni cambies reglas sin confirmación expresa de Emi.
6. Nada de datos de clientes (nombres, expedientes, montos) en repositorios públicos ni en la Matriz.

## Repositorios de este cerebro

### Cerebro-Castorena- (público)

https://github.com/lianfixx/Cerebro-Castorena- · último cambio: 23 nov 2026

Matriz documental de Emi para Castorena Abogados. Aquí están las cinco tablas de referencia, las versiones recuperadas, las reglas de trabajo y los pendientes.

Skills: `matriz-castorena`

Último registro: 23 nov 2026 · Fecha real del cierre de hoy, auditoría contra fechas futuras y reloj de GitHub (skill 1.6.2) · Agente: claude.ai (sesión en la nube, claude-fable-5-2)
Pendiente: guardar la skill 1.6.2 en Claude (tarjeta en el chat).

### INDEP (privado)

https://github.com/lianfixx/INDEP · último cambio: 23 nov 2026

Privado: pide acceso a Emi o usa un conector de GitHub con su sesión.

### Escritos-juridicos-CASTORENA (público)

https://github.com/lianfixx/Escritos-juridicos-CASTORENA · último cambio: 4 nov 2026

Skills: `escritos-juridicos-castorena`

Último registro: 4 nov 2026 · corrección: puentes de skill con YAML válido · Agente: Claude Code (sesión en la nube)

### dof-juridico-monitor (público)

https://github.com/lianfixx/dof-juridico-monitor · último cambio: 23 nov 2026

Sistema autónomo, auditable y agnóstico de proveedor para revisar el Diario Oficial de la Federación (DOF), verificar cobertura, detectar novedades jurídicas relevantes y producir entregables ejecutivos y de estudio.

Skills: `dof-castorena`

Último registro: 23 nov 2026 · las tareas cargan add_repo antes de usarlo · Agente: claude.ai (sesión en la nube, claude-opus-5-5)
Pendiente: si aun cargándola la herramienta no existe en esas sesiones, el plan B es que el box lea `dof-trabajo` con un token de solo lectura, que tendría que crear Emi.

## Tareas programadas

- Cierre diario matriz Castorena (Claude) · Diario 18:43 · última: 10 nov 2026, bien · repo `Cerebro-Castorena-`
- INDEP seguimiento diario (Claude) · Lunes a viernes, cada hora de 09:04 a 17:04 · última: 11 nov 2026, bien · repo `INDEP`
- Aviso boletines JFCA · Lunes a viernes 10:41 · última: 11 nov 2026, bien · repo `INDEP`
- DOF Castorena · cierre martes · Martes 05:50 · última: 10 nov 2026, bien · repo `dof-juridico-monitor`
- DOF Castorena · cierre jueves · Jueves 06:05 · última: 12 nov 2026, recuperada a mano: falló por límite de uso; el paquete se entregó el mismo día · repo `dof-juridico-monitor`
- DOF Castorena · lector nocturno · Lunes y miércoles 21:41 · última: 11 nov 2026, recuperada a mano: falló por límite de uso; el cierre del jueves cubrió lo pendiente · repo `dof-juridico-monitor`
- DOF Castorena · SJF viernes · Viernes 15:37 · repo `dof-juridico-monitor`

## Skills instaladas en Claude

- `matriz-castorena` · `Cerebro-Castorena-`
- `indep` · `INDEP`
- `escritos-juridicos-castorena` · `Escritos-juridicos-CASTORENA`
- `dof-castorena` · `dof-juridico-monitor`
