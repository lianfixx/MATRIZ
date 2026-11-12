# Revisión semanal de la Matriz

Emi pidió el 11/11/2026 que la Matriz se actualice **todas las semanas** y tenga **toda** su información, y que todo se actualice y se retroalimente solo, sin que él tenga que hacer nada. Lo diario lo hace solo GitHub Actions (06:17): leer los repositorios y reescribir el índice. Esta revisión, cada domingo a las 20:13 (hora del centro de México), cubre lo que ese proceso no ve:

1. **Repositorios nuevos o desaparecidos** en la cuenta `lianfixx`.
2. **Tareas programadas** de Claude: cuáles hay, su horario y si su última corrida salió bien.
3. **Skills instaladas** en Claude y si cada una tiene repositorio.
4. **Salud:** que la actualización diaria haya corrido bien y que la Matriz lea todos los repositorios.
5. **Vencimientos:** los de `inventario.json → vencimientos` (el token «MATRIZ lectura» vence el **9 de febrero de 2027**).
6. **Proyectos nuevos** que Emi creó desde el panel (`proyectos/`).
7. **Respaldo en Google Drive** de la Matriz General.

La ejecuta una tarea programada de Claude («Revisión semanal de la Matriz»). Cualquier otra IA con acceso a GitHub puede hacerla siguiendo estos mismos pasos.

## Pasos

1. Adjunta `lianfixx/MATRIZ` con escritura y clónalo. Corre `python3 ia/verificar.py inicio`. Lee `AGENTS.md`, `EMI.md`, `matriz.config.json`, `inventario.json` y `MATRIZ.md`.
2. **Repositorios.** Lista todos los repositorios de `lianfixx` (en Claude: `list_repos`).
   - Uno que no esté en `matriz.config.json`: adjúntalo con lectura, lee su `README.md` y `AGENTS.md` y agrégalo al cerebro que le corresponda por su contenido. Si es privado, agrégalo también a `privados`. Si no está claro a qué cerebro va, no lo adivines: déjalo fuera y pregúntaselo a Emi en el resumen. Nunca crees un cerebro nuevo sin su confirmación.
   - Uno que esté en la configuración y ya no exista: no lo borres; avísale a Emi.
   - La actualización diaria ya avisa en `MATRIZ.md` («Repositorios nuevos por clasificar») de los repositorios que aún no están en un cerebro: empieza por esa lista.
   - Si un repositorio privado aparece «sin lectura», el token «MATRIZ lectura» no lo alcanza (debe tener acceso a «All repositories»): dale a Emi en el resumen un encargo listo para Muse.
3. **Tareas programadas.** Lista todas (en Claude: `list_triggers` con todas sus páginas, y otra vez con `enabled=false`). Actualiza `inventario.json → tareas`: nombre, cerebro, repositorio, horario legible en hora del centro de México, estado (activa o pausada), fecha y resultado de la última corrida («bien» o «falló: <motivo en palabras llanas>»). Una tarea que ya disparó y no se repetirá se quita. **Nunca copies el texto de una tarea**, solo su nombre. No cambies, pauses ni borres ninguna tarea.
4. **Skills instaladas.** Compara la lista de skills de esta sesión (las de la cuenta de Emi) con `inventario.json → skills_instaladas` y actualízala con su cerebro y su repositorio (vacío si no tiene).
5. **Skills instaladas al día.** Para cada skill instalada que tenga repositorio, compara el `SKILL.md` instalado (en esta sesión, bajo `~/.claude/skills/`) con el del repositorio. Si difieren, la copia de Claude está vieja: anótala en el informe como «reinstalar» y deja en el resumen el encargo para Muse (descargar el repositorio, comprimir la carpeta de la skill y subirla en claude.ai → Ajustes → Capacidades → Skills, reemplazando la anterior).
6. **Retroalimentación.** Lee las entradas de la semana de los `CHANGELOG.md` de todos los repositorios (están en `bitacora/`). Anota en el informe: lo que se repitió, lo que falló dos veces, lo que Emi tuvo que hacer a mano y cómo dejarlo automático la próxima vez. Si la mejora es de la Matriz, hazla tú en esta misma revisión; si es de otro repositorio, déjala como propuesta concreta para Emi.
7. **Salud.** Revisa las corridas de los últimos 7 días del workflow «Actualizar la Matriz» y que `MATRIZ.md` no tenga «Sin lectura». Si falta leer un repositorio, di cuál y por qué.
8. **Vencimientos.** Para cada entrada de `inventario.json → vencimientos` con 21 días o menos, avísale a Emi con el encargo listo (para el token «MATRIZ lectura», los pasos están en el `CHANGELOG.md` del 11/11/2026).
8b. **Proyectos nuevos.** Para cada `proyectos/*.md` con `estado: idea`, deja en el resumen un encargo para Muse: crear el repositorio privado `lianfixx/<nombre>` con `README.md`, `AGENTS.md`, `CLAUDE.md` e `ia/` copiados de un repositorio del mismo cerebro. Cuando el repositorio exista, agrégalo a su cerebro en `matriz.config.json` y cambia el proyecto a `estado: con repositorio`. No crees repositorios tú.
8c. **Respaldo en Google Drive** (solo si esta sesión tiene el conector de Google Drive). En la carpeta «Matriz General» de Emi (no la crees si no existe: avísale): actualiza el documento «Matriz General» con el texto de `MATRIZ_GENERAL.md`, reemplaza `MATRIZ_GENERAL.md` y sube `MATRIZ-AAAA-MM-DD.zip` con el repositorio (`git archive --format=zip HEAD`). Conserva los últimos 8 zip y manda los más viejos a la papelera. Nunca compartas la carpeta ni cambies sus permisos. Sin conector: anótalo en el informe como «respaldo en Drive no hecho».
9. **Informe.** Escribe `revisiones/AAAA-MM-DD.md`: qué cambió, qué falló, qué necesita decidir Emi. Cambia `inventario.json → revisado` a la fecha de hoy.
10. **Guardar.** Corre `python3 -m unittest discover -s tools -p 'test_*.py'`. Añade la entrada en `CHANGELOG.md` con la línea `Agente:`. Un solo commit cuyo mensaje termine en `IA-Actor: Claude Code (ejecución programada)`. Sube a `main`; si la sesión solo puede subir a ramas `claude/…`, sube a esa rama: el workflow «Integrar tareas programadas» la pasa a `main` y la Matriz se regenera sola. Comprueba en 5 minutos que el commit llegó a `main`.
11. **Resumen para Emi** (cinco líneas como máximo): repositorios nuevos y dónde quedaron, tareas que fallaron, skills sin repositorio, lo que debe decidir y cualquier vencimiento cercano.

## Lo que esta revisión nunca hace

Escribir en otros repositorios, crear repositorios, enviar correos, publicar, compartir archivos de Drive, crear o cambiar tareas programadas, cambiar `ia/` o los workflows, ni copiar a esta Matriz información de clientes o el contenido de los repositorios privados.
