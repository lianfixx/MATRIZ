// Matriz · Worker de Cloudflare.
// Sirve el panel (archivos de dist/) y, en /mcp, un conector MCP de solo lectura para cualquier IA
// (Claude, ChatGPT, Muse Code, Gemini CLI/Antigravity, Cursor…). Lee los mismos datos públicos del
// panel: matriz.json, contexto/*.md y EMI.md. No guarda nada ni escribe en GitHub.
// Transporte: «Streamable HTTP» de MCP con respuestas JSON (sin SSE).

const VERSION = "1.0.0";
const PROTOCOLOS = ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"];
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Accept, Mcp-Session-Id, Mcp-Protocol-Version, Authorization",
  "Access-Control-Expose-Headers": "Mcp-Session-Id",
};

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const fecha = (iso) => {
  if (!iso) return "sin dato";
  const [a, m, d] = iso.split("-");
  return `${+d} ${MESES[+m - 1]} ${a}`;
};
const pendiente = (r) => {
  const p = (r.registro?.[0]?.pendiente || "").trim();
  return /^(ninguno|ninguna|no)\.?$/i.test(p) ? "" : p;
};

async function archivo(env, base, ruta) {
  const r = await env.ASSETS.fetch(new Request(new URL(ruta, base)));
  return r.ok ? r.text() : null;
}
async function datos(env, base) {
  return JSON.parse(await archivo(env, base, "/matriz.json"));
}
const quitarFrontmatter = (t) => (t || "").replace(/^---[\s\S]*?---\n/, "");
const todos = (D) => D.cerebros.flatMap((c) => c.repos.map((r) => ({ ...r, cerebro: c })));
const buscarCerebro = (D, q) => {
  const k = String(q || "").toLowerCase().trim();
  return D.cerebros.find((c) => c.id === k || c.nombre.toLowerCase() === k)
    || D.cerebros.find((c) => c.id.includes(k) || c.nombre.toLowerCase().includes(k));
};

// ---------------------------------------------------------------- herramientas

const SOLO_LECTURA = { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false };
const HERRAMIENTAS = [
  {
    name: "matriz_resumen",
    title: "Resumen de la Matriz",
    description: "Empieza aquí. Resumen de la Matriz General de Emi: sus cerebros, cuántos repositorios tiene cada uno, último movimiento, avisos (tareas que fallaron, repositorios nuevos o sin lectura, skills sin repositorio) y cómo trabajar con él.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "cerebro",
    title: "Ver un cerebro",
    description: "Detalle de un cerebro: repositorios (enlace, visibilidad, último registro, última IA, pendiente, skills), tareas programadas y skills instaladas. Acepta el id o el nombre (por ejemplo «castorena», «MILLA ABOGADOS», «contenido-y-video»).",
    inputSchema: { type: "object", properties: { cerebro: { type: "string", description: "Id o nombre del cerebro" } }, required: ["cerebro"], additionalProperties: false },
  },
  {
    name: "contexto",
    title: "Contexto para continuar",
    description: "Texto de contexto listo para continuar el trabajo de un cerebro con cualquier IA: quién es Emi, reglas de trabajo y estado de cada repositorio. Úsalo antes de trabajar en un cerebro.",
    inputSchema: { type: "object", properties: { cerebro: { type: "string", description: "Id o nombre del cerebro" } }, required: ["cerebro"], additionalProperties: false },
  },
  {
    name: "ultimos_cambios",
    title: "Últimos cambios",
    description: "Lo último que hizo cada IA en todos los repositorios (fecha, repositorio, título, agente), del más reciente al más antiguo.",
    inputSchema: { type: "object", properties: { limite: { type: "integer", minimum: 1, maximum: 50, description: "Cuántos (por defecto 15)" } }, additionalProperties: false },
  },
  {
    name: "reglas_de_emi",
    title: "Quién es Emi y sus reglas",
    description: "Perfil de Emi, dónde trabaja, con qué IA y equipos, y las reglas que valen siempre para cualquier IA (registro con «Agente:», nada de datos de clientes, qué requiere su confirmación).",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
  {
    name: "search",
    title: "Buscar en la Matriz",
    description: "Busca repositorios, skills, tareas programadas y cerebros por texto. Devuelve resultados con id para usar en «fetch».",
    inputSchema: { type: "object", properties: { query: { type: "string", description: "Texto a buscar" } }, required: ["query"], additionalProperties: false },
  },
  {
    name: "fetch",
    title: "Abrir un resultado",
    description: "Devuelve el contenido completo de un resultado de «search» por su id (repo:<nombre>, cerebro:<id>, contexto:<id> o emi).",
    inputSchema: { type: "object", properties: { id: { type: "string", description: "Id devuelto por search" } }, required: ["id"], additionalProperties: false },
  },
].map((h) => ({ ...h, annotations: { ...SOLO_LECTURA, title: h.title } }));

function textoRepo(r) {
  const e = r.registro?.[0];
  const L = [`### ${r.nombre} (${r.visibilidad}) · cerebro ${r.cerebro.nombre}`, r.url, `Último cambio: ${fecha(r.ultimo_cambio)}`];
  if (r.resumen) L.push(r.resumen);
  if (r.skills?.length) L.push("Skills: " + r.skills.map((s) => s.nombre).join(", "));
  if (e) L.push(`Último registro: ${fecha(e.fecha)} · ${e.titulo} · Agente: ${e.agente || "no consta"}`);
  if (pendiente(r)) L.push(`Pendiente: ${pendiente(r)}`);
  if (r.visibilidad === "privado" && !r.resumen) L.push("Privado: aquí solo se publica su nombre y fecha; ábrelo con un conector de GitHub con la sesión de Emi.");
  return L.join("\n");
}

function textoCerebro(D, c) {
  const inv = D.inventario || {};
  const L = [`# ${c.nombre}`, c.descripcion, "", "## Repositorios", ...c.repos.map((r) => textoRepo({ ...r, cerebro: c }) + "\n")];
  const ts = (inv.tareas || []).filter((t) => t.cerebro === c.id);
  if (ts.length) {
    L.push("## Tareas programadas");
    for (const t of ts) L.push(`- ${t.nombre} · ${t.horario || ""}${t.ultima_corrida ? ` · última: ${fecha(t.ultima_corrida)}${t.resultado ? `, ${t.resultado}` : ""}` : ""}`);
  }
  const ks = (inv.skills_instaladas || []).filter((k) => k.cerebro === c.id);
  if (ks.length) {
    L.push("", "## Skills instaladas en Claude");
    for (const k of ks) L.push(`- ${k.nombre} · ${k.repo || "sin repositorio"}`);
  }
  return L.join("\n");
}

async function ejecutar(nombre, args, env, base) {
  const D = await datos(env, base);
  const inv = D.inventario || {};
  const panel = new URL("/", base).toString();
  if (nombre === "matriz_resumen") {
    const rs = todos(D);
    const fallas = (inv.tareas || []).filter((t) => String(t.resultado || "").startsWith("falló"));
    const L = [`# Matriz General de Emi · actualizada el ${fecha(D.actualizada)}`,
      `${rs.length} repositorios en ${D.cerebros.length} cerebros, ${(inv.tareas || []).length} tareas programadas y ${(inv.skills_instaladas || []).length} skills instaladas.`,
      `Panel: ${panel} · Fuente de verdad: https://github.com/${D.propietario}/MATRIZ`, "", "## Cerebros"];
    for (const c of D.cerebros) {
      const ult = c.repos.map((r) => r.ultimo_cambio || "").sort().pop();
      L.push(`- ${c.nombre} (id «${c.id}») · ${c.repos.length} repos · último movimiento ${fecha(ult)} · ${c.descripcion}`);
    }
    const avisos = [
      ...fallas.map((t) => `Falló «${t.nombre}» (${fecha(t.ultima_corrida)}): ${t.resultado}`),
      ...rs.filter((r) => !r.leido).map((r) => `Sin lectura: ${r.nombre}`),
      ...(D.por_clasificar || []).map((r) => `Repositorio nuevo por clasificar: ${r.nombre}`),
      ...(inv.skills_instaladas || []).filter((k) => !k.repo).map((k) => `Skill sin repositorio: ${k.nombre}`),
    ];
    L.push("", "## Avisos", ...(avisos.length ? avisos.map((a) => "- " + a) : ["- Ninguno"]));
    L.push("", "## Cómo trabajar", "1. Usa «contexto» con el cerebro antes de trabajar.", "2. El trabajo se hace en el repositorio de GitHub correspondiente: lee su AGENTS.md, ia/REGLAS.md e ia/PROTOCOLO.md.",
      "3. Todo cambio se registra en su CHANGELOG.md con la línea «Agente:». Si no puedes escribir en GitHub, entrega a Emi un bloque «Registro pendiente para el repositorio».",
      "4. No envíes, publiques ni muevas datos de clientes sin confirmación expresa de Emi.");
    return L.join("\n");
  }
  if (nombre === "cerebro" || nombre === "contexto") {
    const c = buscarCerebro(D, args.cerebro);
    if (!c) throw new Error(`No existe el cerebro «${args.cerebro}». Cerebros: ${D.cerebros.map((x) => x.id).join(", ")}.`);
    if (nombre === "cerebro") return textoCerebro(D, c);
    return quitarFrontmatter(await archivo(env, base, `/contexto/${c.id}.CONTEXTO.md`)) || textoCerebro(D, c);
  }
  if (nombre === "ultimos_cambios") {
    const n = Math.min(Math.max(+args.limite || 15, 1), 50);
    const feed = todos(D).flatMap((r) => (r.registro || []).map((e) => ({ ...e, repo: r.nombre })))
      .sort((a, b) => b.fecha.localeCompare(a.fecha)).slice(0, n);
    return feed.map((e) => `- ${fecha(e.fecha)} · ${e.repo} · ${e.titulo} · Agente: ${e.agente || "no consta"}`).join("\n") || "Sin registros.";
  }
  if (nombre === "reglas_de_emi") {
    return quitarFrontmatter(await archivo(env, base, "/EMI.md")) || "EMI.md no está publicado.";
  }
  if (nombre === "search") {
    return JSON.stringify({ results: buscar(D, args.query, panel) });
  }
  if (nombre === "fetch") {
    return JSON.stringify(await abrir(D, String(args.id || ""), env, base, panel));
  }
  throw new Error(`Herramienta desconocida: ${nombre}`);
}

function buscar(D, q, panel) {
  const k = String(q || "").toLowerCase().trim();
  const R = [];
  const ok = (t) => !k || String(t || "").toLowerCase().includes(k);
  for (const c of D.cerebros) {
    if (ok(c.nombre) || ok(c.descripcion)) R.push({ id: `cerebro:${c.id}`, title: `Cerebro ${c.nombre}`, url: `${panel}#${c.id}` });
    for (const r of c.repos) {
      if (ok(r.nombre) || ok(r.resumen) || (r.skills || []).some((s) => ok(s.nombre)) || (r.registro || []).some((e) => ok(e.titulo)))
        R.push({ id: `repo:${r.nombre}`, title: `${r.nombre} (${c.nombre})`, url: r.url });
    }
  }
  const inv = D.inventario || {};
  for (const t of inv.tareas || []) if (ok(t.nombre)) R.push({ id: `cerebro:${t.cerebro}`, title: `Tarea programada: ${t.nombre}`, url: `${panel}#${t.cerebro}` });
  for (const s of inv.skills_instaladas || []) if (ok(s.nombre)) R.push({ id: s.repo && !s.repo.includes("/") ? `repo:${s.repo}` : `cerebro:${s.cerebro}`, title: `Skill ${s.nombre}`, url: `${panel}#${s.cerebro}` });
  const vistos = new Set();
  return R.filter((x) => (vistos.has(x.id + x.title) ? false : vistos.add(x.id + x.title))).slice(0, 25);
}

async function abrir(D, id, env, base, panel) {
  const [tipo, ...resto] = id.split(":");
  const valor = resto.join(":");
  if (tipo === "repo") {
    for (const c of D.cerebros) for (const r of c.repos)
      if (r.nombre === valor) return { id, title: r.nombre, text: textoRepo({ ...r, cerebro: c }), url: r.url, metadata: { cerebro: c.nombre, visibilidad: r.visibilidad } };
  }
  if (tipo === "cerebro" || tipo === "contexto") {
    const c = buscarCerebro(D, valor);
    if (c) {
      const text = tipo === "cerebro" ? textoCerebro(D, c) : quitarFrontmatter(await archivo(env, base, `/contexto/${c.id}.CONTEXTO.md`));
      return { id, title: `${tipo === "cerebro" ? "Cerebro" : "Contexto"} ${c.nombre}`, text, url: `${panel}#${c.id}` };
    }
  }
  if (tipo === "emi") return { id, title: "Emi", text: quitarFrontmatter(await archivo(env, base, "/EMI.md")), url: panel };
  throw new Error(`No encontré «${id}».`);
}

// ---------------------------------------------------------------- JSON-RPC

const respuesta = (id, result) => ({ jsonrpc: "2.0", id, result });
const error = (id, code, message) => ({ jsonrpc: "2.0", id, error: { code, message } });

async function atender(msg, env, base) {
  const { id, method, params = {} } = msg || {};
  const esNotificacion = id === undefined || id === null;
  if (!msg || msg.jsonrpc !== "2.0" || typeof method !== "string") return esNotificacion ? null : error(id ?? null, -32600, "Solicitud inválida");
  if (esNotificacion) return null;
  switch (method) {
    case "initialize": {
      const pedido = params.protocolVersion;
      return respuesta(id, {
        protocolVersion: PROTOCOLOS.includes(pedido) ? pedido : PROTOCOLOS[0],
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: "matriz", title: "Matriz General de Emi", version: VERSION },
        instructions: "Conector de solo lectura a la Matriz General de Emi. Empieza con «matriz_resumen» y usa «contexto» antes de trabajar en un cerebro. El trabajo se hace y se registra en los repositorios de GitHub (línea «Agente:»), no aquí.",
      });
    }
    case "ping": return respuesta(id, {});
    case "tools/list": return respuesta(id, { tools: HERRAMIENTAS });
    case "tools/call": {
      const nombre = params.name;
      if (!HERRAMIENTAS.some((h) => h.name === nombre)) return error(id, -32602, `Herramienta desconocida: ${nombre}`);
      try {
        const texto = await ejecutar(nombre, params.arguments || {}, env, base);
        return respuesta(id, { content: [{ type: "text", text: texto }], isError: false });
      } catch (e) {
        return respuesta(id, { content: [{ type: "text", text: String(e.message || e) }], isError: true });
      }
    }
    case "resources/list": return respuesta(id, { resources: [] });
    case "prompts/list": return respuesta(id, { prompts: [] });
    default: return error(id, -32601, `Método no disponible: ${method}`);
  }
}

async function mcp(request, env) {
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (request.method === "GET") {
    return new Response(JSON.stringify({ nombre: "Matriz General de Emi · conector MCP", uso: "POST JSON-RPC 2.0 (Streamable HTTP). Agrega esta dirección como conector MCP remoto en tu IA." }),
      { status: 405, headers: { ...CORS, "Content-Type": "application/json; charset=utf-8", Allow: "POST, OPTIONS" } });
  }
  if (request.method !== "POST") return new Response("Método no permitido", { status: 405, headers: CORS });
  let cuerpo;
  try { cuerpo = await request.json(); } catch { return Response.json(error(null, -32700, "JSON inválido"), { status: 400, headers: CORS }); }
  const base = request.url;
  const lote = Array.isArray(cuerpo);
  const salidas = (await Promise.all((lote ? cuerpo : [cuerpo]).map((m) => atender(m, env, base)))).filter(Boolean);
  if (!salidas.length) return new Response(null, { status: 202, headers: CORS });
  return new Response(JSON.stringify(lote ? salidas : salidas[0]), { status: 200, headers: { ...CORS, "Content-Type": "application/json; charset=utf-8" } });
}

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (pathname === "/mcp" || pathname === "/mcp/") return mcp(request, env);
    return env.ASSETS.fetch(request);
  },
};

export { atender, HERRAMIENTAS };
