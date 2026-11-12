// Pruebas del Worker (conector MCP y API de edición) contra dist/. Arma antes: python3 tools/panel.py
// Uso: node worker/prueba.mjs
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
const RAIZ = new URL("..", import.meta.url).pathname;
const mod = await import(new URL("./index.js", import.meta.url));
let fallos = 0, casos = 0;
const ok = (c, m) => { casos++; if (!c) { fallos++; console.log("FALLA:", m); } };

const ASSETS = { fetch: async (req) => { const p = new URL(req.url).pathname; try { return new Response(await readFile(RAIZ + "dist" + (p === "/" ? "/index.html" : decodeURIComponent(p)))); } catch { return new Response("no", { status: 404 }); } } };
const envLectura = { ASSETS };

// ---------- MCP
const mcp = async (cuerpo, env = envLectura, crudo) => {
  const r = await mod.default.fetch(new Request("https://matriz.test/mcp", { method: "POST", headers: { "Content-Type": "application/json" }, body: crudo ?? JSON.stringify(cuerpo) }), env);
  return [r.status, r.status === 202 ? null : await r.json()];
};
let [s, j] = await mcp({ jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "t", version: "1" } } });
ok(s === 200 && j.result.protocolVersion === "2025-06-18" && j.result.capabilities.tools, "initialize");
[s, j] = await mcp({ jsonrpc: "2.0", id: 2, method: "initialize", params: null }); ok(s === 200 && j.error?.code === -32602, "params null no tumba el Worker");
[s] = await mcp({ jsonrpc: "2.0", method: "notifications/initialized" }); ok(s === 202, "notificación 202");
[s] = await mcp({ jsonrpc: "2.0", id: 5, result: {} }); ok(s === 202, "respuesta de cliente 202");
[s, j] = await mcp(5); ok(j.error?.code === -32600, "cuerpo inválido -32600");
[s, j] = await mcp([]); ok(j.error?.code === -32600, "lote vacío -32600");
[s, j] = await mcp({ jsonrpc: "2.0", id: null, method: "ping" }); ok(j.error?.code === -32600, "id null rechazado");
[s, j] = await mcp({ jsonrpc: "2.0", id: 3, method: "tools/list" }); ok(j.result.tools.length === 10, "10 herramientas");
const call = async (name, args) => (await mcp({ jsonrpc: "2.0", id: 4, method: "tools/call", params: { name, arguments: args } }))[1].result;
let r = await call("matriz_resumen", {}); ok(r.content[0].text.includes("Castorena") && !r.isError, "resumen");
// El archivo único lo genera «Actualizar la Matriz»; sin él, el conector lo dice en vez de fallar.
const hayGeneral = existsSync(RAIZ + "dist/MATRIZ_GENERAL.md");
r = await call("matriz_general", {}); ok(r.content[0].text.includes(hayGeneral ? "Matriz General de Emi" : "todavía no está publicado"), "archivo único");
r = await mcp({ jsonrpc: "2.0", id: 9, method: "tools/call", params: { name: "fetch", arguments: { id: "matriz" } } });
ok(typeof r[1].result.content[0].text === "string" && r[1].result.content[0].text.length > 0, "fetch matriz siempre trae texto");
r = await call("cerebro", { cerebro: "milla" }); ok(r.content[0].text.startsWith("# MILLA ABOGADOS"), "cerebro parcial");
r = await call("cerebro", { cerebro: "" }); ok(r.isError, "cerebro vacío es error, no Castorena");
r = await call("contexto", { cerebro: "Contenido y video" }); ok(r.content[0].text.includes("Contexto para cualquier IA"), "contexto");
r = await call("pendientes", {}); ok(!r.isError, "pendientes");
r = await call("metricas", {}); ok(r.content[0].text.includes("| Cerebro |"), "métricas");
r = await call("ultimos_cambios", { limite: 3 }); ok(r.content[0].text.split("\n").length <= 3, "últimos 3");
r = await call("reglas_de_emi", {}); ok(r.content[0].text.includes("Reglas que valen siempre"), "EMI");
r = await call("search", { query: "x-viral" }); const res = JSON.parse(r.content[0].text).results; ok(res.length > 0, "search");
r = await call("search", { query: "" }); ok(JSON.parse(r.content[0].text).results.length === 0, "search vacío");
r = await call("fetch", { id: res[0].id }); ok(JSON.parse(r.content[0].text).text.length > 20, "fetch");
r = await call("fetch", { id: "contexto:" }); ok(r.isError, "fetch contexto vacío es error");
[s, j] = await mcp({ jsonrpc: "2.0", id: 9, method: "foo" }); ok(j.error.code === -32601, "método desconocido");
[s, j] = await mcp(null, envLectura, "{"); ok(s === 400 && j.error.code === -32700, "JSON inválido");
s = (await mod.default.fetch(new Request("https://matriz.test/mcp"), envLectura)).status; ok(s === 405, "GET 405");

// ---------- privacidad
ok(await mod.pareceDatoDeCliente("revisar el 99999/21-11-01-1", {}), "bloquea expediente");
ok(await mod.pareceDatoDeCliente("llamar a Acme", { MATRIZ_RESERVADOS: "Acme" }), "bloquea nombre reservado");
ok(!(await mod.pareceDatoDeCliente("grabar el video del jueves 11/11", {})), "deja pasar texto normal");
// Huella de «acme industrial» (la misma que calcula tools/generar.py): protege sin el secreto.
const huellaAcme = "8885aeba78e84e1c5c43b4dc04db677a48f859091332ca092d2fff4945de800e";
ok(await mod.pareceDatoDeCliente("Llamar a ACMÉ  Industrial mañana", {}, [huellaAcme]), "bloquea nombre por huella");
ok(!(await mod.pareceDatoDeCliente("Llamar a Acme mañana", {}, [huellaAcme])), "una palabra suelta no basta");

// ---------- tablero: ida y vuelta del Markdown
const md = "---\ntipo: tablero\n---\n# T\n\n## Pendientes\n\n- [ ] Uno 🔺 📅 2026-11-20 ➕ 2026-11-12 ^aaaaaa\n- [x] Dos ✅ 2026-11-11 ^bbbbbb\n\n## Notas\n\n- 2026-11-12 · Nota ^cccccc\n";
const t = mod.parsearTablero(md);
ok(t.pendientes.length === 2 && t.pendientes[0].alta && t.pendientes[0].vence === "2026-11-20" && t.notas[0].texto === "Nota", "parsear tablero");
const t2 = mod.parsearTablero(mod.serializarTablero("Uno", t));
ok(JSON.stringify(t2) === JSON.stringify(t), "serializar y volver a leer da lo mismo");

// ---------- API con GitHub simulado
const archivos = new Map();
globalThis.fetch = async (url, op = {}) => {
  const m = String(url).match(/contents\/([^?]+)/);
  const ruta = decodeURIComponent(m[1]);
  if (!op.method || op.method === "GET") {
    if (!archivos.has(ruta)) return new Response("{}", { status: 404 });
    const a = archivos.get(ruta);
    return new Response(JSON.stringify({ content: Buffer.from(a.texto).toString("base64"), sha: a.sha }));
  }
  const b = JSON.parse(op.body);
  const actual = archivos.get(ruta);
  if ((actual?.sha || undefined) !== b.sha) return new Response("{}", { status: 409 });
  archivos.set(ruta, { texto: Buffer.from(b.content, "base64").toString(), sha: Math.random().toString(16).slice(2) });
  return new Response("{}", { status: 200 });
};
const env = { ASSETS, PANEL_CLAVE: "clave-de-prueba", MATRIZ_ESCRITURA: "x", MATRIZ_RESERVADOS: "Acme" };
const pedir = async (ruta, metodo = "GET", cuerpo, galleta = "", origen = "https://matriz.test") => {
  const h = { "Content-Type": "application/json", Origin: origen };
  if (galleta) h.Cookie = galleta;
  const res = await mod.default.fetch(new Request("https://matriz.test" + ruta, { method: metodo, headers: h, body: cuerpo ? JSON.stringify(cuerpo) : undefined }), env);
  return [res.status, await res.json(), res.headers.get("Set-Cookie")];
};
let [st, cuerpo] = await pedir("/api/sesion"); ok(st === 200 && cuerpo.editor === false && cuerpo.configurado, "sesión sin entrar");
[st] = await pedir("/api/tablero/castorena"); ok(st === 401, "sin sesión no lee el tablero");
[st] = await pedir("/api/entrar", "POST", { clave: "mala" }); ok(st === 401, "contraseña mala");
let galleta;
[st, cuerpo, galleta] = await pedir("/api/entrar", "POST", { clave: "clave-de-prueba" }); ok(st === 200 && /HttpOnly; Secure; SameSite=Strict/.test(galleta), "entrar con contraseña");
galleta = galleta.split(";")[0];
[st] = await pedir("/api/tablero/castorena", "POST", { accion: "agregar_pendiente", texto: "x" }, galleta, "https://otro.sitio"); ok(st === 403, "bloquea otro origen");
[st, cuerpo] = await pedir("/api/tablero/castorena", "POST", { accion: "agregar_pendiente", texto: "Preparar escrito", alta: true, vence: "2026-11-30" }, galleta);
ok(st === 200 && cuerpo.pendientes[0].texto === "Preparar escrito" && cuerpo.pendientes[0].alta, "agregar pendiente");
const id = cuerpo.pendientes[0].id;
[st, cuerpo] = await pedir("/api/tablero/castorena", "POST", { accion: "completar", id }, galleta); ok(cuerpo.pendientes[0].hecho, "completar");
[st, cuerpo] = await pedir("/api/tablero/castorena", "POST", { accion: "agregar_nota", texto: "Idea <script>" }, galleta); ok(cuerpo.notas[0].texto === "Idea script", "nota sin etiquetas");
[st, cuerpo] = await pedir("/api/tablero/castorena", "POST", { accion: "agregar_pendiente", texto: "Llamar a Acme" }, galleta); ok(st === 422, "bloquea cliente reservado");
[st, cuerpo] = await pedir("/api/tablero/castorena", "POST", { accion: "agregar_pendiente", texto: "ver 99999/21-11-01-1" }, galleta); ok(st === 422, "bloquea expediente");
ok(archivos.get("tablero/castorena.md").texto.includes("- [x] Preparar escrito 🔺 📅 2026-11-30"), "Markdown guardado en GitHub");
[st, cuerpo] = await pedir("/api/tablero/castorena", "GET", null, galleta); ok(st === 200 && cuerpo.pendientes.length === 1, "leer tablero con sesión");
[st, cuerpo] = await pedir("/api/tablero/nada", "POST", { accion: "agregar_nota", texto: "x" }, galleta); ok(st === 404, "cerebro inexistente");
[st, cuerpo] = await pedir("/api/proyecto", "POST", { nombre: "Podcast semanal", cerebro: "contenido-y-video", descripcion: "Un episodio por semana" }, galleta);
ok(st === 200 && archivos.has("proyectos/podcast-semanal.md"), "proyecto nuevo");
[st] = await pedir("/api/proyecto", "POST", { nombre: "Podcast semanal", cerebro: "contenido-y-video" }, galleta); ok(st === 409, "proyecto duplicado");
const sinConf = await mod.default.fetch(new Request("https://matriz.test/api/entrar", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" }), { ASSETS });
ok(sinConf.status === 503, "sin secretos la edición está apagada");

console.log(fallos ? `${fallos} de ${casos} fallaron` : `Worker: ${casos} pruebas pasan`);
process.exit(fallos ? 1 : 0);
