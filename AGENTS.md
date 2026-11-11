# Instrucciones para cualquier IA · lianfixx/MATRIZ

Este repositorio es el mapa de todo el trabajo de Emi: la **Matriz General**, sus **Cerebros** y los repositorios y skills de cada uno. No guarda trabajo: apunta a donde está. Las instrucciones actuales de Emi prevalecen.

## Cómo entrar

1. Lee `MATRIZ.md`: qué cerebros hay y qué se movió.
2. Lee `contexto/<cerebro>.CONTEXTO.md` del cerebro en el que vas a trabajar.
3. Ve al repositorio que corresponda y lee **su** `AGENTS.md`, `ia/REGLAS.md` e `ia/PROTOCOLO.md`. El trabajo se hace y se registra allá, no aquí.

## Qué se edita aquí y qué no

- A mano solo se edita `matriz.config.json` (qué cerebros existen y qué repositorio pertenece a cuál), `tools/`, la documentación y `ia/`.
- `MATRIZ.md`, `matriz.json`, `cerebros/`, `repos/`, `contexto/` y `bitacora/` los genera `python3 tools/generar.py`. No los edites: se reescriben solos cada día.
- Este repositorio es público. De los repositorios privados solo se publica nombre, cerebro y fecha. No copies aquí datos de clientes, expedientes ni secretos.
- Un repositorio nuevo de Emi se agrega a un cerebro en `matriz.config.json`. Un cerebro nuevo requiere confirmación de Emi.

## Trabajo entre IA (obligatorio para cualquier IA o persona)

Este repositorio sigue el protocolo común de `ia/PROTOCOLO.md`; las reglas concretas están en `ia/REGLAS.md`.
- Al empezar, ejecuta `python3 ia/verificar.py inicio`: resume rama, último commit y su IA, reglas y registro, y activa los hooks de git si faltan (en Claude Code corre solo).
- Fuente de verdad: el repositorio remoto y su estado vigente (`matriz.config.json` y `CHANGELOG.md`), no la memoria de una conversación.
- Todo cambio hecho a mano se registra en el mismo commit, con la línea `Agente:` (protocolo, sección 3). Los archivos generados están exentos: su registro es `bitacora/`. Sin escritura, entrega un «Registro pendiente para el repositorio».
- Lo prohibido y lo que requiere confirmación de Emi vale en Claude, ChatGPT, Codex, Gemini, Muse, DeepSeek y cualquier otra IA. Con terminal, ejecuta `sh ia/instalar.sh` una vez por copia. GitHub revisa cada push con `registro-ia.yml`.
- Para pasar trabajo a otra IA: `ia/plantillas/PETICION.md` y `ia/plantillas/ENTREGA.md`.
