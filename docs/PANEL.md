# Panel web de la Matriz

Una página limpia para ver la Matriz desde el iPhone o cualquier navegador, sin instalar nada. Muestra:

- **Inicio:** el grafo (Matriz → cerebros → repositorios), los avisos (tareas que fallaron, repositorios sin lectura, skills sin repositorio), lo último que hizo cada IA, los pendientes y un buscador.
- **Cada cerebro:** sus repositorios con su último registro, su última IA y su pendiente; sus tareas programadas con su resultado; sus skills instaladas.
- **«Copiar contexto para una IA»:** copia el archivo de contexto del cerebro para pegarlo en ChatGPT, Gemini, Muse, DeepSeek o cualquier otra.

Para IA que leen una dirección web: `/llms.txt` (mapa breve), `/matriz.json` (todos los datos) y `/contexto/<cerebro>.CONTEXTO.md`.

## Cómo se publica

`tools/panel.py` arma la carpeta `dist/` con `panel/index.html`, `matriz.json` y `contexto/`. El workflow «Publicar panel» la sube a Cloudflare Workers (plan gratis, solo archivos estáticos) cada vez que «Actualizar la Matriz» termina bien. Necesita dos secretos en este repositorio: `CLOUDFLARE_API_TOKEN` (plantilla «Edit Cloudflare Workers») y `CLOUDFLARE_ACCOUNT_ID`. Sin ellos el workflow termina en verde y avisa que no publicó.

La dirección es **https://matriz.milla-abogados.workers.dev** (cuenta de Cloudflare de Emi, plan gratis, subdominio `milla-abogados`). La llave `CLOUDFLARE_API_TOKEN` se llama «MATRIZ panel (GitHub Actions)» en Cloudflare → Mi perfil → Tokens de API, sin caducidad y limitada a Workers de esa cuenta. El mismo Worker sirve el conector MCP en `/mcp` ([CONECTAR_IA.md](CONECTAR_IA.md)).

## Privacidad

El panel solo publica lo que ya es público en este repositorio: de los repositorios privados, nombre, cerebro y fecha. Pide a los buscadores no indexarlo (`robots.txt` y cabecera `X-Robots-Tag`). Si más adelante quieres que solo entres tú, se protege con Cloudflare Access (gratis hasta 50 personas) sin cambiar nada del panel.
