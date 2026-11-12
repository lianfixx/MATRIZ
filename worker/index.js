// Matriz · Worker de Cloudflare.
// 1. Sirve el panel (archivos de dist/).
// 2. /mcp: conector MCP de solo lectura para cualquier IA (Streamable HTTP, respuestas JSON).
// 3. /api: edición del tablero (pendientes, notas, proyectos) protegida con la contraseña de Emi.
//    Escribe en GitHub (lianfixx/MATRIZ); de ahí lo toman Obsidian, la Matriz y el conector.
// Secretos del Worker: PANEL_CLAVE (contraseña), MATRIZ_ESCRITURA (token de GitHub con escritura solo
// en MATRIZ) y MATRIZ_RESERVADOS (nombres de clientes que nunca se publican). Sin ellos, todo es solo lectura.

const VERSION = "2.0.0";
const REPO = "lianfixx/MATRIZ";
const PROTOCOLOS = ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"];
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Accept, Mcp-Session-Id, Mcp-Protocol-Version, Authorization",
  "Access-Control-Expose-Headers": "Mcp-Session-Id",
};
const SEGURIDAD = {
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "X-Robots-Tag": "noindex, nofollow",
};

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const esFecha = (s) => /^\d{4}-\d{2}-\d{2}$/.test(String(s || "")) && !isNaN(Date.parse(s));
const fecha = (iso) => {
  if (!iso) return "sin dato";
  if (!esFecha(String(iso).slice(0, 10))) return String(iso);
  const [a, m, d] = String(iso).slice(0, 10).split("-");
  return `${+d} ${MESES[+m - 1]} ${a}`;
};
const hoy = () => new Date(Date.now() - 6 * 3600e3).toISOString().slice(0, 10); // hora del centro de México

// ---------------------------------------------------------------- datos publicados

async function archivo(env, base, ruta) {
  const r = await env.ASSETS.fetch(new Request(new URL(ruta, base)));
  return r.ok ? r.text() : null;
}
async function datos(env, base) {
  return JSON.parse(await archivo(env, base, "/matriz.json"));
}
const quitarFrontmatter = (t) => (t || "").replace(/^---\n[\s\S]*?\n---\n/, "");
const todos = (D) => D.cerebros.flatMap((c) => c.repos.map((r) => ({ ...r, cerebro: c })));
function buscarCerebro(D, q) {
  const k = String(q ?? "").toLowerCase().trim();
  if (!k) return null;
  return D.cerebros.find((c) => c.id === k || c.nombre.toLowerCase() === k)
    || D.cerebros.find((c) => c.id.includes(k) || c.nombre.toLowerCase().includes(k)) || null;
}
const listaCerebros = (D) => D.cerebros.map((c) => c.id).join(", ");

// ---------------------------------------------------------------- privacidad (igual que tools/generar.py)

const PATRONES = [
  /(?<![\d/])\d{2,6}\/\d{2,4}(?:-[0-9A-Z]{1,6})+\b/,
  /(?<![\d/])\d{3,6}\/(?:19|20)?\d{2}(?![\d/])/,
  /\b(?:exp(?:ediente)?s?|juicio|amparo|toca|folio|causa|carpeta de investigación)\.?\s*(?:n[oú]m(?:ero)?\.?\s*)?\d[\d/.,-]{1,}/i,
  /[\w.%+-]+@[\w-]+(?:\.[\w-]+)+/,
  /\b1[A-Za-z0-9_-]{32}\b/,
  /(?:\$|\bMXN|\bUSD)\s?\d[\d,. ]*\d|\b\d[\d,. ]*\d\s?(?:pesos|MXN|USD|dólares)\b/i,
  /(?<![\w./-])\d{5,}(?![\w./-])/,
  /(?<![\w/])(?:\+?52[\s-]?)?\d{2}[\s-]?\d{4}[\s-]?\d{4}(?![\w/])/,
  /\b[A-Z][AEIOUX][A-Z]{2}\d{6}[HM][A-Z]{5}[A-Z\d]\d\b/,
  /\b[A-ZÑ&]{3,4}\d{6}[A-Z\d]{3}\b/,
];
// Igual que tools/generar.py: minúsculas, sin acentos, palabras separadas por un espacio.
const normalizar = (t) => (t.toLowerCase().normalize("NFKD").replace(/\p{M}/gu, "").match(/[0-9A-Za-zÀ-ÖØ-öø-ÿ]+/g) || []);
async function sha256(t) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t));
  return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
}
// Formatos (expedientes, correos…), nombres del secreto MATRIZ_RESERVADOS y huellas de matriz.config.json
// (llegan en matriz.json como «reservas_huella»), en grupos de hasta cuatro palabras.
async function pareceDatoDeCliente(texto, env, huellas = []) {
  if (PATRONES.some((p) => p.test(texto))) return true;
  const reservados = String(env.MATRIZ_RESERVADOS || "").split(/[,\n]/).map((t) => normalizar(t).join(" ")).filter(Boolean);
  const palabras = normalizar(texto), unido = ` ${palabras.join(" ")} `;
  if (reservados.some((r) => unido.includes(` ${r} `))) return true;
  if (!huellas.length) return false;
  const conjunto = new Set(huellas);
  for (let i = 0; i < palabras.length; i++)
    for (let n = 1; n <= 4 && i + n <= palabras.length; n++)
      if (conjunto.has(await sha256(palabras.slice(i, i + n).join(" ")))) return true;
  return false;
}

// ---------------------------------------------------------------- herramientas MCP

const SOLO_LECTURA = { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false };
const objeto = (props = {}, req = []) => ({ type: "object", properties: props, required: req, additionalProperties: false });
const CEREBRO = { cerebro: { type: "string", description: "Id o nombre del cerebro (por ejemplo «castorena», «MILLA ABOGADOS»)" } };
const HERRAMIENTAS = [
  ["matriz_general", "La Matriz General completa", "El archivo único de la Matriz General: quién es Emi, reglas, pulso, cada cerebro con sus repositorios, pendientes, tareas y skills. Úsalo para entender todo de una vez.", objeto()],
  ["matriz_resumen", "Resumen de la Matriz", "Resumen corto: cerebros, último movimiento, avisos y cómo trabajar con Emi. Empieza aquí si no necesitas todo.", objeto()],
  ["cerebro", "Ver un cerebro", "Detalle de un cerebro: repositorios, último registro, pendientes, tareas programadas y skills.", objeto(CEREBRO, ["cerebro"])],
  ["contexto", "Contexto para continuar", "Texto listo para continuar el trabajo de un cerebro con cualquier IA.", objeto(CEREBRO, ["cerebro"])],
  ["pendientes", "Pendientes de Emi", "Pendientes abiertos (y vencidos) del tablero de Emi, de un cerebro o de todos.", objeto({ cerebro: { type: "string", description: "Opcional: id o nombre del cerebro" } })],
  ["metricas", "Métricas", "Pulso de la Matriz: commits por semana, días sin movimiento, pendientes, tareas que fallaron, quién trabaja y vencimientos.", objeto()],
  ["ultimos_cambios", "Últimos cambios", "Lo último que hizo cada IA en todos los repositorios, del más reciente al más antiguo.", objeto({ limite: { type: "integer", minimum: 1, maximum: 50, description: "Cuántos (por defecto 15)" } })],
  ["reglas_de_emi", "Quién es Emi y sus reglas", "Perfil de Emi, dónde trabaja, con qué IA y equipos, y las reglas que valen siempre.", objeto()],
  ["search", "Buscar en la Matriz", "Busca repositorios, skills, tareas, pendientes y cerebros. Devuelve ids para «fetch».", objeto({ query: { type: "string", description: "Texto a buscar" } }, ["query"])],
  ["fetch", "Abrir un resultado", "Contenido completo de un resultado de «search» (repo:<nombre>, cerebro:<id>, contexto:<id>, emi o matriz).", objeto({ id: { type: "string", description: "Id devuelto por search" } }, ["id"])],
].map(([name, title, description, inputSchema]) => ({ name, title, description, inputSchema, annotations: { ...SOLO_LECTURA, title } }));

function textoRepo(r) {
  const e = r.registro?.[0];
  const L = [`### ${r.nombre} (${r.visibilidad}) · cerebro ${r.cerebro.nombre}`, r.url, `Último cambio: ${fecha(r.ultimo_cambio)}`];
  if (r.resumen) L.push(r.resumen);
  if (r.skills?.length) L.push("Skills: " + r.skills.map((s) => s.nombre).join(", "));
  if (e) L.push(`Último registro: ${fecha(e.fecha)} · ${e.titulo} · Agente: ${e.agente || "no consta"}`);
  if (e?.pendiente) L.push(`Pendiente: ${e.pendiente}`);
  if (r.visibilidad === "privado" && !r.resumen) L.push("Privado: aquí solo se publica su nombre, fecha y actividad.");
  return L.join("\n");
}
function textoPendientes(c) {
  const ab = (c.tablero?.pendientes || []).filter((p) => !p.hecho);
  if (!ab.length) return `${c.nombre}: sin pendientes abiertos.`;
  return `${c.nombre}:\n` + ab.map((p) => `- ${p.alta ? "(alta) " : ""}${p.texto}${p.vence ? ` · vence ${fecha(p.vence)}${p.vence < hoy() ? " (vencido)" : ""}` : ""}`).join("\n");
}
function textoCerebro(D, c) {
  const inv = D.inventario || {};
  const L = [`# ${c.nombre}`, c.descripcion, "", "## Pendientes de Emi", textoPendientes(c), "", "## Repositorios",
    ...c.repos.map((r) => textoRepo({ ...r, cerebro: c }) + "\n")];
  const ts = (inv.tareas || []).filter((t) => t.cerebro === c.id);
  if (ts.length) L.push("## Tareas programadas", ...ts.map((t) => `- ${t.nombre} · ${t.horario || ""}${t.ultima_corrida ? ` · última: ${fecha(t.ultima_corrida)}${t.resultado ? `, ${t.resultado}` : ""}` : ""}`), "");
  const ks = (inv.skills_instaladas || []).filter((k) => k.cerebro === c.id);
  if (ks.length) L.push("## Skills instaladas en Claude", ...ks.map((k) => `- ${k.nombre} · ${k.repo || "sin repositorio"}`));
  return L.join("\n");
}
function textoMetricas(D) {
  const M = D.metricas || {};
  const L = [`# Métricas · ${fecha(D.actualizada)}`, "", "| Cerebro | Esta semana | Semana pasada | Días sin movimiento | Pendientes | Vencidos | Tareas que fallaron |", "|---|---|---|---|---|---|---|"];
  for (const c of D.cerebros) {
    const m = M.cerebros?.[c.id] || {};
    L.push(`| ${c.nombre} | ${m.esta_semana ?? 0} | ${m.semana_pasada ?? 0} | ${m.dias_sin_movimiento ?? "—"} | ${m.pendientes_abiertos ?? 0} | ${m.pendientes_vencidos ?? 0} | ${m.tareas_falladas ?? 0} |`);
  }
  if (M.commits_por_semana) L.push("", "Commits por semana (8 semanas, la última es la actual): " + M.commits_por_semana.join(", "));
  if (M.actores_60d) L.push("Quién trabajó (60 días): " + Object.entries(M.actores_60d).map(([a, n]) => `${a} ${n}`).join(", "));
  if (M.vencimientos?.length) L.push("Vencimientos: " + M.vencimientos.map((v) => `${v.nombre} ${fecha(v.fecha)}`).join("; "));
  return L.join("\n");
}

async function ejecutar(nombre, args, env, base) {
  const D = await datos(env, base);
  const inv = D.inventario || {};
  const panel = new URL("/", base).toString();
  switch (nombre) {
    case "matriz_general":
      return (await archivo(env, base, "/MATRIZ_GENERAL.md")) || "MATRIZ_GENERAL.md todavía no está publicado.";
    case "matriz_resumen": {
      const rs = todos(D);
      const L = [`# Matriz General de Emi · actualizada el ${fecha(D.actualizada)}`,
        `${rs.length} repositorios en ${D.cerebros.length} cerebros, ${(inv.tareas || []).length} tareas programadas y ${(inv.skills_instaladas || []).length} skills instaladas.`,
        `Panel: ${panel} · Fuente de verdad: https://github.com/${D.propietario}/MATRIZ · Todo en un archivo: herramienta «matriz_general».`, "", "## Cerebros"];
      for (const c of D.cerebros) {
        const m = D.metricas?.cerebros?.[c.id] || {};
        L.push(`- ${c.nombre} (id «${c.id}») · ${c.repos.length} repos · ${m.esta_semana ?? 0} commits esta semana · ${m.pendientes_abiertos ?? 0} pendientes · ${c.descripcion}`);
      }
      const avisos = [
        ...(inv.tareas || []).filter((t) => String(t.resultado || "").startsWith("falló")).map((t) => `Falló «${t.nombre}» (${fecha(t.ultima_corrida)}): ${t.resultado}`),
        ...rs.filter((r) => !r.leido).map((r) => `Sin lectura reciente: ${r.nombre}`),
        ...(D.por_clasificar || []).map((r) => `Repositorio nuevo por clasificar: ${r.nombre}`),
        ...(D.metricas?.vencimientos || []).filter((v) => v.dias <= 30).map((v) => `Vence ${v.nombre} el ${fecha(v.fecha)}`),
      ];
      L.push("", "## Avisos", ...(avisos.length ? avisos.map((a) => "- " + a) : ["- Ninguno"]));
      L.push("", "## Cómo trabajar", "1. Usa «contexto» con el cerebro antes de trabajar.", "2. El trabajo se hace en el repositorio de GitHub correspondiente: lee su AGENTS.md, ia/REGLAS.md e ia/PROTOCOLO.md.",
        "3. Todo cambio se registra en su CHANGELOG.md con la línea «Agente:». Si no puedes escribir en GitHub, entrega a Emi un bloque «Registro pendiente para el repositorio».",
        "4. No envíes, publiques ni muevas datos de clientes sin confirmación expresa de Emi.");
      return L.join("\n");
    }
    case "cerebro":
    case "contexto": {
      const c = buscarCerebro(D, args.cerebro);
      if (!c) throw new Error(`No existe el cerebro «${args.cerebro ?? ""}». Cerebros: ${listaCerebros(D)}.`);
      if (nombre === "cerebro") return textoCerebro(D, c);
      return quitarFrontmatter(await archivo(env, base, `/contexto/${c.id}.CONTEXTO.md`)) || textoCerebro(D, c);
    }
    case "pendientes": {
      if (args.cerebro !== undefined && String(args.cerebro).trim() !== "") {
        const c = buscarCerebro(D, args.cerebro);
        if (!c) throw new Error(`No existe el cerebro «${args.cerebro}». Cerebros: ${listaCerebros(D)}.`);
        return textoPendientes(c);
      }
      return D.cerebros.map(textoPendientes).join("\n\n");
    }
    case "metricas":
      return textoMetricas(D);
    case "ultimos_cambios": {
      const n = args.limite === undefined ? 15 : Math.min(Math.max(Math.trunc(+args.limite) || 1, 1), 50);
      const feed = todos(D).flatMap((r) => (r.registro || []).map((e) => ({ ...e, repo: r.nombre })))
        .sort((a, b) => b.fecha.localeCompare(a.fecha)).slice(0, n);
      return feed.map((e) => `- ${fecha(e.fecha)} · ${e.repo} · ${e.titulo} · Agente: ${e.agente || "no consta"}`).join("\n") || "Sin registros.";
    }
    case "reglas_de_emi":
      return quitarFrontmatter(await archivo(env, base, "/EMI.md")) || "EMI.md no está publicado.";
    case "search":
      return JSON.stringify({ results: buscar(D, args.query, panel) });
    case "fetch":
      return JSON.stringify(await abrir(D, String(args.id ?? ""), env, base, panel));
    default:
      throw new Error(`Herramienta desconocida: ${nombre}`);
  }
}

function buscar(D, q, panel) {
  const k = String(q ?? "").toLowerCase().trim();
  if (!k) return [];
  const ok = (t) => String(t || "").toLowerCase().includes(k);
  const R = [];
  for (const c of D.cerebros) {
    if (ok(c.nombre) || ok(c.descripcion) || (c.tablero?.pendientes || []).some((p) => ok(p.texto)))
      R.push({ id: `cerebro:${c.id}`, title: `Cerebro ${c.nombre}`, url: `${panel}#${c.id}` });
    for (const r of c.repos)
      if (ok(r.nombre) || ok(r.resumen) || (r.skills || []).some((s) => ok(s.nombre)) || (r.registro || []).some((e) => ok(e.titulo)))
        R.push({ id: `repo:${r.nombre}`, title: `${r.nombre} (${c.nombre})`, url: r.url });
  }
  const inv = D.inventario || {};
  for (const t of inv.tareas || []) if (ok(t.nombre)) R.push({ id: `cerebro:${t.cerebro}`, title: `Tarea programada: ${t.nombre}`, url: `${panel}#${t.cerebro}` });
  for (const s of inv.skills_instaladas || []) if (ok(s.nombre)) R.push({ id: s.repo && !s.repo.includes("/") ? `repo:${s.repo}` : `cerebro:${s.cerebro}`, title: `Skill ${s.nombre}`, url: `${panel}#${s.cerebro}` });
  const vistos = new Set();
  return R.filter((x) => (vistos.has(x.id + x.title) ? false : vistos.add(x.id + x.title))).slice(0, 25);
}

async function abrir(D, id, env, base, panel) {
  const i = id.indexOf(":");
  const tipo = i < 0 ? id : id.slice(0, i);
  const valor = i < 0 ? "" : id.slice(i + 1);
  if (tipo === "repo") {
    for (const c of D.cerebros) for (const r of c.repos)
      if (r.nombre === valor) return { id, title: r.nombre, text: textoRepo({ ...r, cerebro: c }), url: r.url, metadata: { cerebro: c.nombre, visibilidad: r.visibilidad } };
  }
  if ((tipo === "cerebro" || tipo === "contexto") && valor) {
    const c = buscarCerebro(D, valor);
    if (c) {
      const text = tipo === "cerebro" ? textoCerebro(D, c) : quitarFrontmatter(await archivo(env, base, `/contexto/${c.id}.CONTEXTO.md`));
      return { id, title: `${tipo === "cerebro" ? "Cerebro" : "Contexto"} ${c.nombre}`, text, url: `${panel}#${c.id}` };
    }
  }
  if (tipo === "emi") return { id, title: "Emi", text: quitarFrontmatter(await archivo(env, base, "/EMI.md")), url: panel };
  if (tipo === "matriz") return { id, title: "Matriz General", text: (await archivo(env, base, "/MATRIZ_GENERAL.md")) || "MATRIZ_GENERAL.md todavía no está publicado; usa matriz_resumen.", url: panel };
  throw new Error(`No encontré «${id}».`);
}

// ---------------------------------------------------------------- JSON-RPC / MCP

const respuesta = (id, result) => ({ jsonrpc: "2.0", id, result });
const error = (id, code, message) => ({ jsonrpc: "2.0", id, error: { code, message } });
const esObjeto = (x) => x !== null && typeof x === "object" && !Array.isArray(x);

async function atender(msg, env, base) {
  if (!esObjeto(msg) || msg.jsonrpc !== "2.0") return error(null, -32600, "Solicitud inválida");
  const tieneId = Object.prototype.hasOwnProperty.call(msg, "id");
  if (typeof msg.method !== "string") {
    // Respuesta de un cliente (resultado o error a una solicitud del servidor): se acepta sin contestar.
    return tieneId && ("result" in msg || "error" in msg) ? null : error(msg.id ?? null, -32600, "Solicitud inválida");
  }
  if (!tieneId) return null; // notificación
  const { id, method } = msg;
  if (id === null || (typeof id !== "string" && typeof id !== "number")) return error(null, -32600, "El id debe ser texto o número");
  if (msg.params !== undefined && !esObjeto(msg.params)) return error(id, -32602, "params debe ser un objeto");
  const params = msg.params || {};
  try {
    switch (method) {
      case "initialize": {
        const pedido = params.protocolVersion;
        return respuesta(id, {
          protocolVersion: PROTOCOLOS.includes(pedido) ? pedido : PROTOCOLOS[0],
          capabilities: { tools: { listChanged: false } },
          serverInfo: { name: "matriz", title: "Matriz General de Emi", version: VERSION },
          instructions: "Conector de solo lectura a la Matriz General de Emi. Para entender todo de una vez usa «matriz_general»; para algo puntual, «matriz_resumen», «cerebro» o «contexto». El trabajo se hace y se registra en los repositorios de GitHub (línea «Agente:»), no aquí.",
        });
      }
      case "ping": return respuesta(id, {});
      case "tools/list": return respuesta(id, { tools: HERRAMIENTAS });
      case "tools/call": {
        const nombre = params.name;
        if (!HERRAMIENTAS.some((h) => h.name === nombre)) return error(id, -32602, `Herramienta desconocida: ${nombre}`);
        if (params.arguments !== undefined && !esObjeto(params.arguments)) return error(id, -32602, "arguments debe ser un objeto");
        try {
          const texto = await ejecutar(nombre, params.arguments || {}, env, base);
          return respuesta(id, { content: [{ type: "text", text: texto }], isError: false });
        } catch (e) {
          return respuesta(id, { content: [{ type: "text", text: String(e.message || e) }], isError: true });
        }
      }
      case "resources/list": return respuesta(id, { resources: [] });
      case "resources/templates/list": return respuesta(id, { resourceTemplates: [] });
      case "prompts/list": return respuesta(id, { prompts: [] });
      default: return error(id, -32601, `Método no disponible: ${method}`);
    }
  } catch (e) {
    return error(id, -32603, "Error interno: " + String(e.message || e));
  }
}

async function mcp(request, env) {
  const H = { ...CORS, ...SEGURIDAD };
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: H });
  if (request.method === "GET") {
    return new Response(JSON.stringify({ nombre: "Matriz General de Emi · conector MCP", uso: "POST JSON-RPC 2.0 (Streamable HTTP). Agrega esta dirección como conector MCP remoto en tu IA." }),
      { status: 405, headers: { ...H, "Content-Type": "application/json; charset=utf-8", Allow: "POST, OPTIONS" } });
  }
  if (request.method !== "POST") return new Response("Método no permitido", { status: 405, headers: H });
  const json = (cuerpo, status = 200) => new Response(JSON.stringify(cuerpo), { status, headers: { ...H, "Content-Type": "application/json; charset=utf-8" } });
  let cuerpo;
  try { cuerpo = await request.json(); } catch { return json(error(null, -32700, "JSON inválido"), 400); }
  const base = request.url;
  if (Array.isArray(cuerpo)) {
    if (!cuerpo.length) return json(error(null, -32600, "Lote vacío"));
    const salidas = (await Promise.all(cuerpo.map((m) => atender(m, env, base)))).filter(Boolean);
    return salidas.length ? json(salidas) : new Response(null, { status: 202, headers: H });
  }
  const salida = await atender(cuerpo, env, base);
  return salida ? json(salida) : new Response(null, { status: 202, headers: H });
}

// ---------------------------------------------------------------- sesión de Emi

const enc = new TextEncoder();
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
async function hmac(clave, texto) {
  const k = await crypto.subtle.importKey("raw", enc.encode(clave), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", k, enc.encode(texto)));
}
async function iguales(a, b) {
  // Comparación en tiempo constante: compara los HMAC de ambos textos.
  const k = crypto.getRandomValues(new Uint8Array(32));
  const [x, y] = await Promise.all([hmac(hex(k), a), hmac(hex(k), b)]);
  let d = 0;
  for (let i = 0; i < x.length; i++) d |= x.charCodeAt(i) ^ y.charCodeAt(i);
  return d === 0;
}
const SESION = "matriz_sesion";
const DIAS = 30;
async function crearSesion(env) {
  const vence = Date.now() + DIAS * 864e5;
  return `${vence}.${await hmac(env.PANEL_CLAVE + "·sesión", String(vence))}`;
}
async function sesionValida(request, env) {
  if (!env.PANEL_CLAVE) return false;
  const m = (request.headers.get("Cookie") || "").match(new RegExp(`(?:^|;\\s*)${SESION}=([0-9]+)\\.([0-9a-f]{64})`));
  if (!m || +m[1] < Date.now()) return false;
  return iguales(m[2], await hmac(env.PANEL_CLAVE + "·sesión", m[1]));
}
const cookie = (valor, edad) => `${SESION}=${valor}; Path=/api; HttpOnly; Secure; SameSite=Strict; Max-Age=${edad}`;

// ---------------------------------------------------------------- GitHub (escritura del tablero)

async function gh(env, ruta, opciones = {}) {
  const r = await fetch(`https://api.github.com/repos/${REPO}/contents/${ruta}`, {
    ...opciones,
    headers: { Authorization: `Bearer ${env.MATRIZ_ESCRITURA}`, Accept: "application/vnd.github+json", "User-Agent": "matriz-panel", "X-GitHub-Api-Version": "2022-11-28", ...(opciones.headers || {}) },
  });
  return r;
}
const b64 = (texto) => btoa(String.fromCharCode(...enc.encode(texto)));
const deb64 = (b) => new TextDecoder().decode(Uint8Array.from(atob(b.replace(/\n/g, "")), (c) => c.charCodeAt(0)));
async function leerGH(env, ruta) {
  const r = await gh(env, `${ruta}?ref=main`);
  if (r.status === 404) return { texto: "", sha: null };
  if (!r.ok) throw new Error(`GitHub respondió ${r.status} al leer ${ruta}`);
  const j = await r.json();
  return { texto: deb64(j.content), sha: j.sha };
}
async function escribirGH(env, ruta, texto, sha, mensaje) {
  const r = await gh(env, ruta, { method: "PUT", body: JSON.stringify({ message: mensaje, content: b64(texto), sha: sha || undefined, branch: "main" }) });
  if (r.status === 409 || r.status === 422) return { conflicto: true };
  if (!r.ok) throw new Error(`GitHub respondió ${r.status} al guardar ${ruta}`);
  return { conflicto: false };
}

// ---------------------------------------------------------------- tablero: leer y escribir el Markdown

const TAREA = /^\s*-\s*\[( |x|X)\]\s+(.*)$/;
function parsearTablero(md) {
  const pendientes = [], notas = [];
  let seccion = "";
  for (const linea of (md || "").split("\n")) {
    if (linea.startsWith("## ")) { seccion = linea.slice(3).trim().toLowerCase(); continue; }
    const m = linea.match(TAREA);
    if (m && seccion.startsWith("pendiente")) {
      const t = m[2];
      const id = (t.match(/\^([a-z0-9]{4,12})\s*$/) || [])[1] || nuevoId();
      pendientes.push({
        id, hecho: m[1] !== " ", alta: t.includes("🔺"),
        vence: (t.match(/📅\s*(\d{4}-\d{2}-\d{2})/) || [])[1] || "",
        hecho_el: (t.match(/✅\s*(\d{4}-\d{2}-\d{2})/) || [])[1] || "",
        creado: (t.match(/➕\s*(\d{4}-\d{2}-\d{2})/) || [])[1] || "",
        texto: t.replace(/\s*(?:📅|✅|➕)\s*\d{4}-\d{2}-\d{2}|\s*🔺|\s*\^[a-z0-9]{4,12}\s*$/g, "").trim(),
      });
    } else if (seccion.startsWith("nota") && linea.trim().startsWith("- ")) {
      const t = linea.trim().slice(2);
      const f = t.match(/^(\d{4}-\d{2}-\d{2})\s*·\s*(.*)$/);
      const id = (t.match(/\^([a-z0-9]{4,12})\s*$/) || [])[1] || nuevoId();
      notas.push({ id, fecha: f ? f[1] : "", texto: (f ? f[2] : t).replace(/\s*\^[a-z0-9]{4,12}\s*$/, "").trim() });
    }
  }
  return { pendientes, notas };
}
function serializarTablero(nombre, t) {
  const L = ["---", "tipo: tablero", `cerebro: ${JSON.stringify(nombre)}`, "---", `# Tablero · ${nombre}`, "",
    "Pendientes y notas de Emi para este cerebro. Se editan desde el panel de la Matriz; también puedes editarlos aquí con el mismo formato.",
    "", "## Pendientes", ""];
  for (const p of t.pendientes) {
    L.push(`- [${p.hecho ? "x" : " "}] ${p.texto}${p.alta ? " 🔺" : ""}${p.vence ? ` 📅 ${p.vence}` : ""}${p.creado ? ` ➕ ${p.creado}` : ""}${p.hecho && p.hecho_el ? ` ✅ ${p.hecho_el}` : ""} ^${p.id}`);
  }
  L.push("", "## Notas", "");
  for (const n of t.notas) L.push(`- ${n.fecha ? `${n.fecha} · ` : ""}${n.texto} ^${n.id}`);
  return L.join("\n") + "\n";
}
const nuevoId = () => hex(crypto.getRandomValues(new Uint8Array(4))).slice(0, 6);
const limpiar = (s, max = 400) => String(s ?? "").replace(/[\r\n\t]+/g, " ").replace(/[<>]/g, "").trim().slice(0, max);

function aplicar(t, accion, a) {
  const buscarP = () => {
    const p = t.pendientes.find((x) => x.id === a.id);
    if (!p) throw new Error("Ese pendiente ya no existe; recarga la página.");
    return p;
  };
  switch (accion) {
    case "agregar_pendiente": {
      const texto = limpiar(a.texto);
      if (!texto) throw new Error("Escribe el pendiente.");
      if (t.pendientes.length >= 300) throw new Error("Hay demasiados pendientes en este cerebro; cierra algunos.");
      t.pendientes.unshift({ id: nuevoId(), texto, hecho: false, alta: !!a.alta, vence: esFecha(a.vence) ? a.vence : "", creado: hoy(), hecho_el: "" });
      return `nuevo pendiente`;
    }
    case "completar": { const p = buscarP(); p.hecho = !p.hecho; p.hecho_el = p.hecho ? hoy() : ""; return p.hecho ? "pendiente hecho" : "pendiente reabierto"; }
    case "prioridad": { const p = buscarP(); p.alta = !p.alta; return p.alta ? "prioridad alta" : "prioridad normal"; }
    case "fecha": { const p = buscarP(); p.vence = esFecha(a.vence) ? a.vence : ""; return "fecha de vencimiento"; }
    case "editar_pendiente": { const p = buscarP(); const texto = limpiar(a.texto); if (!texto) throw new Error("El pendiente no puede quedar vacío."); p.texto = texto; return "pendiente editado"; }
    case "borrar_pendiente": { buscarP(); t.pendientes = t.pendientes.filter((x) => x.id !== a.id); return "pendiente borrado"; }
    case "agregar_nota": {
      const texto = limpiar(a.texto, 800);
      if (!texto) throw new Error("Escribe la nota.");
      t.notas.push({ id: nuevoId(), fecha: hoy(), texto });
      if (t.notas.length > 200) t.notas = t.notas.slice(-200);
      return "nota nueva";
    }
    case "borrar_nota": { t.notas = t.notas.filter((x) => x.id !== a.id); return "nota borrada"; }
    default: throw new Error("Acción desconocida.");
  }
}
const textosDe = (accion, a) => (["agregar_pendiente", "editar_pendiente", "agregar_nota"].includes(accion) ? [String(a.texto ?? "")] : []);

// ---------------------------------------------------------------- API

async function api(request, env, url) {
  const H = { ...SEGURIDAD, "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" };
  const json = (obj, status = 200, extra = {}) => new Response(JSON.stringify(obj), { status, headers: { ...H, ...extra } });
  const configurado = !!(env.PANEL_CLAVE && env.MATRIZ_ESCRITURA);
  const ruta = url.pathname.replace(/\/+$/, "");

  if (request.method === "POST") {
    // Protección contra peticiones desde otros sitios: solo el propio panel puede escribir.
    const origen = request.headers.get("Origin");
    if (origen && origen !== url.origin) return json({ error: "Origen no permitido." }, 403);
    if ((request.headers.get("Content-Type") || "").split(";")[0] !== "application/json") return json({ error: "Se esperaba JSON." }, 415);
  }
  let cuerpo = {};
  if (request.method === "POST") {
    try { cuerpo = await request.json(); } catch { return json({ error: "JSON inválido." }, 400); }
    if (!esObjeto(cuerpo)) return json({ error: "JSON inválido." }, 400);
  }

  if (ruta === "/api/sesion" && request.method === "GET") return json({ editor: await sesionValida(request, env), configurado });
  if (ruta === "/api/entrar" && request.method === "POST") {
    if (!configurado) return json({ error: "La edición todavía no está activada: faltan la contraseña o el token de escritura." }, 503);
    if (!(await iguales(String(cuerpo.clave ?? ""), env.PANEL_CLAVE))) {
      await new Promise((r) => setTimeout(r, 800)); // frena a quien intente adivinar
      return json({ error: "Contraseña incorrecta." }, 401);
    }
    return json({ editor: true }, 200, { "Set-Cookie": cookie(await crearSesion(env), DIAS * 86400) });
  }
  if (ruta === "/api/salir" && request.method === "POST") return json({ editor: false }, 200, { "Set-Cookie": cookie("", 0) });

  if (!(await sesionValida(request, env))) return json({ error: "Entra con tu contraseña para editar." }, 401);
  const D = await datos(env, url);

  const mt = ruta.match(/^\/api\/tablero\/([a-z0-9-]+)$/);
  if (mt) {
    const c = D.cerebros.find((x) => x.id === mt[1]);
    if (!c) return json({ error: "Ese cerebro no existe." }, 404);
    const archivoMd = `tablero/${c.id}.md`;
    if (request.method === "GET") {
      const { texto } = await leerGH(env, archivoMd);
      return json(parsearTablero(texto));
    }
    if (request.method === "POST") {
      const accion = String(cuerpo.accion || "");
      for (const t of textosDe(accion, cuerpo)) {
        if (await pareceDatoDeCliente(t, env, D.reservas_huella)) return json({ error: "Parece un dato de cliente (nombre, expediente, correo, teléfono o monto). La Matriz es pública: escríbelo sin ese dato." }, 422);
      }
      for (let intento = 0; intento < 3; intento++) {
        const { texto, sha } = await leerGH(env, archivoMd);
        const t = parsearTablero(texto);
        let que;
        try { que = aplicar(t, accion, cuerpo); } catch (e) { return json({ error: e.message }, 400); }
        const r = await escribirGH(env, archivoMd, serializarTablero(c.nombre, t), sha,
          `Tablero · ${c.nombre}: ${que}\n\nIA-Actor: Panel de la Matriz (Emi)`);
        if (!r.conflicto) return json(t);
      }
      return json({ error: "Otro cambio se guardó al mismo tiempo. Intenta de nuevo." }, 409);
    }
  }

  if (ruta === "/api/proyecto" && request.method === "POST") {
    const nombre = limpiar(cuerpo.nombre, 80), descripcion = limpiar(cuerpo.descripcion, 400);
    const c = D.cerebros.find((x) => x.id === cuerpo.cerebro);
    if (!nombre || !c) return json({ error: "Escribe el nombre y elige el cerebro." }, 400);
    if (await pareceDatoDeCliente(nombre + " " + descripcion, env, D.reservas_huella)) return json({ error: "Parece un dato de cliente. La Matriz es pública: descríbelo sin ese dato." }, 422);
    const slug = nombre.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || nuevoId();
    const ruta2 = `proyectos/${slug}.md`;
    const { sha } = await leerGH(env, ruta2);
    if (sha) return json({ error: "Ya existe un proyecto con ese nombre." }, 409);
    const md = ["---", "tipo: proyecto", `nombre: ${JSON.stringify(nombre)}`, `cerebro: ${JSON.stringify(c.id)}`, "estado: idea", `fecha: ${hoy()}`,
      `descripcion: ${JSON.stringify(descripcion)}`, "---", `# ${nombre}`, "", descripcion, "",
      `Nació en la Matriz General el ${fecha(hoy())}, en el cerebro ${c.nombre}. La revisión semanal propone su repositorio con el protocolo común entre IA.`, ""].join("\n");
    const r = await escribirGH(env, ruta2, md, null, `Proyecto nuevo: ${nombre} (${c.nombre})\n\nIA-Actor: Panel de la Matriz (Emi)`);
    if (r.conflicto) return json({ error: "No se pudo guardar; intenta de nuevo." }, 409);
    return json({ ok: true, archivo: ruta2 });
  }
  return json({ error: "No encontrado." }, 404);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/mcp" || url.pathname === "/mcp/") return mcp(request, env);
    if (url.pathname.startsWith("/api/")) {
      try { return await api(request, env, url); } catch (e) {
        return new Response(JSON.stringify({ error: "Error del servidor: " + String(e.message || e) }), { status: 500, headers: { ...SEGURIDAD, "Content-Type": "application/json; charset=utf-8" } });
      }
    }
    return env.ASSETS.fetch(request);
  },
};

export { atender, HERRAMIENTAS, parsearTablero, serializarTablero, aplicar, pareceDatoDeCliente };
