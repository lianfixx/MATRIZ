# Reglas de este repositorio para cualquier IA

Generado desde `ia/politica.json` con `python3 ia/verificar.py reglas`. No editar a mano.

Valen igual en Claude, ChatGPT, Codex, Gemini o cualquier otra IA, y para personas. En
Claude Code se aplican solas (hooks); con copia local, con los hooks de git (`sh ia/instalar.sh`);
en GitHub, el workflow `registro-ia.yml` revisa cada push. Donde no hay freno automático
(chat de claude.ai, ChatGPT o Gemini, conectores), la IA debe cumplirlas por sí misma.

- Requiere confirmación expresa de Emi: Vas a enviar o publicar algo a través de un conector. Confirma destinatario, propósito y adjuntos.
- Prohibido: No se permite forzar ni borrar en el remoto (`--force`, `+rama`, `--mirror`, `--delete`, `:rama`): puede borrar historial ajeno.
- Prohibido: No se permite saltar los controles (`--no-verify`). Corrige lo que señalan.
- Prohibido: No se permite cambiar ni anular `core.hooksPath`; solo `sh ia/instalar.sh` lo configura.
- Requiere confirmación expresa de Emi: Un alias de git puede ocultar acciones prohibidas. Confirma para qué es.
- Requiere confirmación expresa de Emi: Vas a cambiar las reglas comunes, los frenos o los workflows. Confirma que Emi lo pidió y registra el cambio.
- Requiere confirmación expresa de Emi: Vas a publicar en GitHub. Confirma que la tarea actual autoriza este push.
- Prohibido: commit con secretos (claves, tokens) ni datos personales (CURP, tarjetas).
- Antes de `git commit`: `python3 ia/test_guard.py` debe pasar. Las pruebas de las reglas comunes fallaron.
- Antes de `git commit`: `python3 -m unittest discover -s tools -p 'test_*.py'` debe pasar. Las pruebas del generador de la Matriz no pasan.
- Prohibido: commit sin entrada en el registro del repositorio (ver «Registro obligatorio»).

## Registro obligatorio

Todo commit que cambie archivos debe actualizar, en el mismo commit, al menos uno de:

- `^CHANGELOG\.md$` (la entrada nueva incluye «Agente:»)
