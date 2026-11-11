# Claude Code en este repositorio

- Este repositorio es el índice de la Matriz General. El método está en `AGENTS.md`; el generador, en `tools/generar.py` (pruebas: `python3 -m unittest discover -s tools -p 'test_*.py'`).
- Reglas comunes entre IA: `ia/REGLAS.md` y `ia/PROTOCOLO.md`. Frenos activos en `.claude/settings.json` → `ia/guard.py` (política en `ia/politica.json`, pruebas en `ia/test_guard.py`). Si un freno bloquea algo legítimo, explícaselo a Emi; no lo desactives ni lo rodees. Todo cambio hecho a mano se registra en el mismo commit con `Agente: Claude Code`.
@./AGENTS.md
