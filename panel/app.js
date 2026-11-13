// Matriz · panel. Datos: matriz.json (público). Edición: /api con la contraseña de Emi.
// El espacio 3D (three.js, servido desde este mismo sitio) se carga después de pintar lo esencial.

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const esFecha = (s) => /^\d{4}-\d{2}-\d{2}$/.test(String(s || ""));
const f = (iso) => (esFecha(String(iso).slice(0, 10)) ? (([a, m, d]) => `${+d} ${MESES[m - 1]} ${a}`)(String(iso).slice(0, 10).split("-")) : esc(iso || "sin dato"));
const hoyISO = () => new Date(Date.now() - 6 * 3600e3).toISOString().slice(0, 10);
const $ = (s) => document.querySelector(s);
const reducido = matchMedia("(prefers-reduced-motion: reduce)").matches;
const angosto = () => matchMedia("(max-width: 860px)").matches;

const S = { D: null, editor: false, configurado: false, cerebro: null, espacio: null };

// ---------------------------------------------------------------- utilidades de interfaz

function avisar(t) {
  const a = $("#aviso");
  a.textContent = t;
  a.classList.add("ver");
  clearTimeout(avisar.t);
  avisar.t = setTimeout(() => a.classList.remove("ver"), 2600);
}
async function copiar(texto, mensaje) {
  try { await navigator.clipboard.writeText(texto); avisar(mensaje); }
  catch {
    const t = document.createElement("textarea");
    t.value = texto; t.style.position = "fixed"; t.style.opacity = "0";
    document.body.appendChild(t); t.select();
    try { document.execCommand("copy"); avisar(mensaje); } catch { avisar("No se pudo copiar"); }
    t.remove();
  }
}
async function api(ruta, cuerpo) {
  const r = await fetch(ruta, cuerpo === undefined ? { credentials: "same-origin" } : {
    method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(j.error || "No se pudo completar."), { status: r.status });
  return j;
}
function chispa(valores, alto = 44) {
  const n = valores.length, max = Math.max(1, ...valores), w = 300;
  const x = (i) => (n === 1 ? w : (i / (n - 1)) * (w - 6) + 3);
  const y = (v) => alto - 4 - (v / max) * (alto - 10);
  const pts = valores.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`);
  return `<svg class="chispa" viewBox="0 0 ${w} ${alto}" preserveAspectRatio="none" aria-hidden="true">
    <path class="area" d="M${pts[0]} L${pts.join(" L")} L${x(n - 1)},${alto} L${x(0)},${alto} Z"/>
    <path class="trazo" d="M${pts.join(" L")}" vector-effect="non-scaling-stroke"/>
    <circle cx="${x(n - 1)}" cy="${y(valores[n - 1])}" r="3"/></svg>`;
}
const miniBarras = (v) => { const m = Math.max(1, ...v); return `<span class="mini-barras" aria-hidden="true">${v.map((x) => `<i style="height:${Math.max(2, Math.round((x / m) * 16))}px"></i>`).join("")}</span>`; };
const COLORES = { "Claude": "#ece9e4", "ChatGPT · Codex": "#9fb7a6", "Gemini": "#8fa3c4", "Muse": "#c7a6d9", "Emi": "#ff5a1f", "GitHub Actions": "#5d5b56", "Otra": "#3d3c39" };

// ---------------------------------------------------------------- vista «Hoy»

function vistaHoy() {
  const D = S.D, M = D.metricas || { cerebros: {} }, inv = D.inventario || {};
  const semanas = M.commits_por_semana || [0];
  const esta = semanas.at(-1) || 0, pasada = semanas.at(-2) || 0, dif = esta - pasada;
  const cerebros = D.cerebros.map((c) => ({ c, m: M.cerebros?.[c.id] || {} }));
  const maxSem = Math.max(1, ...cerebros.map((x) => x.m.esta_semana || 0));

  // Lo que pide atención, en orden de urgencia
  const atencion = [];
  for (const { c } of cerebros) for (const p of (c.tablero?.pendientes || [])) if (!p.hecho && p.vence && p.vence < hoyISO()) atencion.push({ t: `Vencido: ${esc(p.texto)}`, sub: `${esc(c.nombre)} · venció el ${f(p.vence)}`, ir: c.id, nivel: "alerta" });
  for (const t of (inv.tareas || [])) if (String(t.resultado || "").startsWith("falló")) atencion.push({ t: `Falló «${esc(t.nombre)}»`, sub: `${f(t.ultima_corrida)} · ${esc(t.resultado.replace(/^falló:?\s*/, ""))}`, ir: t.cerebro !== "matriz" ? t.cerebro : "", nivel: "alerta" });
  for (const v of (M.vencimientos || [])) if (v.dias <= 30) atencion.push({ t: esc(v.nombre), sub: v.dias < 0 ? "vencido" : `vence en ${v.dias} días · ${f(v.fecha)}`, nivel: v.dias <= 7 ? "alerta" : "" });
  for (const r of (D.por_clasificar || [])) atencion.push({ t: `Repositorio nuevo: ${esc(r.nombre)}`, sub: "la revisión del domingo lo acomoda en su cerebro", nivel: "" });
  for (const { c, m } of cerebros) if ((m.dias_sin_movimiento ?? 0) > 21) atencion.push({ t: `${esc(c.nombre)} lleva ${m.dias_sin_movimiento} días quieto`, sub: "sin commits en sus repositorios", ir: c.id, nivel: "" });

  // Pendientes más urgentes de todos los cerebros
  const urgentes = cerebros.flatMap(({ c }) => (c.tablero?.pendientes || []).filter((p) => !p.hecho).map((p) => ({ ...p, c })))
    .sort((a, b) => (b.alta - a.alta) || (a.vence || "9999").localeCompare(b.vence || "9999")).slice(0, 6);

  const actores = Object.entries(M.actores_60d || {});
  const totalAct = actores.reduce((s, [, n]) => s + n, 0) || 1;

  $("#hoy").innerHTML = `
  <section class="tarjeta" style="animation-delay:.05s">
    <h2>Esta semana</h2>
    <div class="cifra num">${esta}<small>commits en ${D.cerebros.reduce((s, c) => s + c.repos.length, 0)} repositorios</small></div>
    <div class="delta ${dif > 0 ? "sube" : dif < 0 ? "baja" : ""} num">${dif === 0 ? "igual que la semana pasada" : `${dif > 0 ? "+" : "−"}${Math.abs(dif)} frente a la semana pasada`}</div>
    ${chispa(semanas)}
  </section>

  <section class="tarjeta" style="animation-delay:.1s">
    <h2>Atención</h2>
    <div class="filas">${atencion.length ? atencion.slice(0, 7).map((a) => `${a.ir ? `<button class="fila" data-ir="${esc(a.ir)}">` : `<div class="fila">`}
      <span class="nombre">${a.t}</span>${a.nivel ? `<span class="pastilla alerta">revisar</span>` : `<span></span>`}<span class="sub">${a.sub}</span>${a.ir ? "</button>" : "</div>"}`).join("")
      : `<p class="vacio">Todo en orden.</p>`}</div>
  </section>

  <section class="tarjeta" style="animation-delay:.15s">
    <h2>Pendientes${S.editor ? "" : " · entra para marcarlos"}</h2>
    <div class="filas">${urgentes.length ? urgentes.map((p) => `<div class="pend">
      <button class="caja" role="checkbox" aria-checked="false" aria-label="Marcar como hecho" data-completar="${esc(p.c.id)}:${esc(p.id)}" ${S.editor ? "" : "disabled"}></button>
      <span class="texto">${esc(p.texto)}<span class="meta ${p.vence && p.vence < hoyISO() ? "vencido" : ""}">${esc(p.c.nombre)}${p.vence ? ` · ${p.vence < hoyISO() ? "venció" : "vence"} ${f(p.vence)}` : ""}</span></span>
      ${p.alta ? `<span class="pastilla acento">alta</span>` : "<span></span>"}</div>`).join("")
      : `<p class="vacio">Sin pendientes. ${S.editor ? "Abre un cerebro para agregar uno." : ""}</p>`}</div>
    ${S.editor ? `<div style="margin-top:12px"><button class="boton suave" id="b-proyecto" type="button">Proyecto nuevo</button></div>` : ""}
  </section>

  <section class="tarjeta" style="animation-delay:.2s">
    <h2>Pulso por cerebro</h2>
    <div class="filas">${cerebros.map(({ c, m }) => `<button class="fila" data-ir="${esc(c.id)}">
      <span class="nombre">${esc(c.nombre)}</span>
      <span class="num tenue" style="font-size:12.5px"><span class="barrita" style="width:${Math.round(((m.esta_semana || 0) / maxSem) * 48) + 2}px"></span> ${m.esta_semana || 0}</span>
      <span class="sub">${c.repos.length} repos · ${m.dias_sin_movimiento == null ? "sin dato" : m.dias_sin_movimiento === 0 ? "movimiento hoy" : `último movimiento hace ${m.dias_sin_movimiento} d`}${m.pendientes_abiertos ? ` · ${m.pendientes_abiertos} pendientes` : ""}</span>
    </button>`).join("")}</div>
  </section>

  ${actores.length ? `<section class="tarjeta" style="animation-delay:.25s">
    <h2>Quién trabajó · 60 días</h2>
    <div class="reparto">${actores.map(([a, n]) => `<span style="width:${(n / totalAct) * 100}%;background:${COLORES[a] || "#55534e"}" title="${esc(a)}: ${n}"></span>`).join("")}</div>
    <div class="leyenda">${actores.map(([a, n]) => `<span><i style="background:${COLORES[a] || "#55534e"}"></i>${esc(a)} <span class="num">${n}</span></span>`).join("")}</div>
  </section>` : ""}

  <section class="tarjeta" style="animation-delay:.3s">
    <h2>Llevar la Matriz a otra IA</h2>
    <p class="tenue" style="margin:0 0 10px;font-size:13.5px">Un solo archivo con todo: quién eres, tus reglas, cada cerebro, lo último y lo pendiente.</p>
    <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="boton fuerte" type="button" data-copiar-general>Copiar Matriz General</button>
    <a class="boton suave" href="MATRIZ_GENERAL.md" download="MATRIZ_GENERAL.md">Descargar</a></div>
    <p class="tenue" style="margin:10px 0 0;font-size:12.5px">Conector para Claude o ChatGPT: <span class="num" style="font-family:var(--mono)">${esc(location.origin)}/mcp</span></p>
  </section>
  <p class="tenue" style="font-size:12px;margin:2px 4px">Actualizada el ${f(D.actualizada)} · <a href="https://github.com/${esc(D.propietario)}/MATRIZ" target="_blank" rel="noopener">GitHub</a></p>`;
}

// ---------------------------------------------------------------- hoja del cerebro

function vistaCerebro(c) {
  const D = S.D, m = D.metricas?.cerebros?.[c.id] || {}, inv = D.inventario || {};
  const tab = c.tablero || { pendientes: [], notas: [] };
  const abiertos = tab.pendientes.filter((p) => !p.hecho), hechos = tab.pendientes.filter((p) => p.hecho).slice(0, 5);
  const orden = (a, b) => (b.alta - a.alta) || (a.vence || "9999").localeCompare(b.vence || "9999");
  const fila = (p) => `<div class="pend ${p.hecho ? "hecho" : ""}">
    <button class="caja" role="checkbox" aria-checked="${p.hecho}" aria-label="${p.hecho ? "Reabrir" : "Marcar como hecho"}" data-completar="${esc(c.id)}:${esc(p.id)}" ${S.editor ? "" : "disabled"}></button>
    <span class="texto">${esc(p.texto)}${p.vence || p.hecho_el ? `<span class="meta ${!p.hecho && p.vence && p.vence < hoyISO() ? "vencido" : ""}">${p.hecho ? `hecho el ${f(p.hecho_el)}` : `${p.vence < hoyISO() ? "venció" : "vence"} ${f(p.vence)}`}</span>` : ""}</span>
    <span>${S.editor && !p.hecho ? `<button class="mini ${p.alta ? "activa" : ""}" data-prioridad="${esc(p.id)}" title="Prioridad alta">alta</button>` : p.alta ? `<span class="pastilla acento">alta</span>` : ""}${S.editor ? `<button class="mini" data-borrar="${esc(p.id)}" title="Borrar" aria-label="Borrar">×</button>` : ""}</span></div>`;
  const ts = (inv.tareas || []).filter((t) => t.cerebro === c.id);
  const ks = (inv.skills_instaladas || []).filter((k) => k.cerebro === c.id);

  $("#hoja").innerHTML = `
  <button class="cerrar" type="button" data-cerrar-hoja aria-label="Cerrar">✕</button>
  <p class="tenue" style="margin:0;font-size:12.5px">Cerebro</p>
  <h1>${esc(c.nombre)}</h1>
  <p class="desc">${esc(c.descripcion)}</p>
  <div class="trio">
    <div><b class="num">${m.esta_semana ?? 0}</b><span>commits esta semana</span></div>
    <div><b class="num">${m.dias_sin_movimiento ?? "—"}</b><span>días sin movimiento</span></div>
    <div><b class="num">${abiertos.length}</b><span>pendientes${m.pendientes_vencidos ? ` · ${m.pendientes_vencidos} vencidos` : ""}</span></div>
  </div>

  <section>
    <h3>Pendientes ${S.editor ? "" : `<button class="mini" data-entrar>entrar para editar</button>`}</h3>
    <div class="filas">${abiertos.sort(orden).map(fila).join("") || `<p class="vacio">Sin pendientes abiertos.</p>`}</div>
    ${S.editor ? `<form class="nuevo" data-nuevo-pendiente>
      <input type="text" name="texto" maxlength="400" placeholder="Agregar pendiente" aria-label="Pendiente nuevo" required>
      <button class="boton fuerte">Agregar</button>
      <div class="opciones"><label><input type="checkbox" name="alta"> alta</label><label>vence <input type="date" name="vence"></label><span>Sin nombres de clientes.</span></div>
    </form>` : ""}
    ${hechos.length ? `<details style="margin-top:8px"><summary class="tenue" style="font-size:12.5px;cursor:pointer">Hechos recientes</summary><div class="filas">${hechos.map(fila).join("")}</div></details>` : ""}
  </section>

  <section>
    <h3>Notas</h3>
    <div class="filas">${tab.notas.slice().reverse().slice(0, 12).map((n) => `<div class="fila"><span>${esc(n.texto)}</span>${S.editor ? `<button class="mini" data-borrar-nota="${esc(n.id)}" aria-label="Borrar nota">×</button>` : "<span></span>"}<span class="sub">${f(n.fecha)}</span></div>`).join("") || `<p class="vacio">Sin notas.</p>`}</div>
    ${S.editor ? `<form class="nuevo" data-nueva-nota><input type="text" name="texto" maxlength="800" placeholder="Escribir una nota" aria-label="Nota nueva" required><button class="boton suave">Guardar</button></form>` : ""}
  </section>

  <section>
    <h3>Repositorios</h3>
    <div class="filas">${c.repos.map((r) => { const e = r.registro?.[0]; const sem = r.actividad?.commits || []; return `<div class="repo">
      <a class="nombre" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.nombre)}</a>
      <span style="display:flex;gap:8px;align-items:center">${sem.length ? miniBarras(sem) : ""}<span class="pastilla">${esc(r.visibilidad)}</span></span>
      <span class="sub">${e ? `${f(e.fecha)} · ${esc(e.titulo)}${e.agente ? ` · ${esc(e.agente)}` : ""}` : r.visibilidad === "privado" ? `privado · último cambio ${f(r.ultimo_cambio)}` : `último cambio ${f(r.ultimo_cambio)}`}</span>
      ${e?.pendiente ? `<span class="sub pendiente">Pendiente: ${esc(e.pendiente)}</span>` : ""}
      ${(r.skills || []).length ? `<span class="chips">${r.skills.map((s) => `<span class="chip">${esc(s.nombre)}</span>`).join("")}</span>` : ""}
    </div>`; }).join("")}</div>
  </section>

  ${ts.length ? `<section><h3>Tareas programadas</h3><div class="filas">${ts.map((t) => { const mal = String(t.resultado || "").startsWith("falló"); return `<div class="fila"><span>${esc(t.nombre)}</span>${mal ? `<span class="pastilla alerta">falló</span>` : t.resultado === "bien" ? `<span class="pastilla bien">bien</span>` : `<span class="pastilla">programada</span>`}<span class="sub">${esc(t.horario || "")}${t.ultima_corrida ? ` · última ${f(t.ultima_corrida)}` : ""}${mal ? ` · ${esc(t.resultado)}` : ""}</span></div>`; }).join("")}</div></section>` : ""}
  ${ks.length ? `<section><h3>Skills instaladas en Claude</h3><div class="chips">${ks.map((k) => `<span class="chip">${esc(k.nombre)}${k.repo ? "" : " · sin repo"}</span>`).join("")}</div></section>` : ""}

  <section style="display:flex;gap:8px;flex-wrap:wrap">
    <button class="boton fuerte" type="button" data-copiar-contexto="${esc(c.id)}">Copiar contexto para una IA</button>
    <a class="boton suave" href="contexto/${esc(c.id)}.CONTEXTO.md" target="_blank" rel="noopener">Ver contexto</a>
  </section>`;
}

function abrirCerebro(id, desdeEspacio = false) {
  const c = S.D.cerebros.find((x) => x.id === id);
  if (!c) return cerrarCerebro();
  S.cerebro = c;
  vistaCerebro(c);
  const h = $("#hoja");
  h.hidden = false;
  h.scrollTop = 0;
  if (location.hash !== "#" + id) history.replaceState(null, "", "#" + id);
  if (!desdeEspacio) S.espacio?.enfocar(id);
  if (S.editor) refrescarTablero(c);
}
function cerrarCerebro() {
  S.cerebro = null;
  $("#hoja").hidden = true;
  if (location.hash && location.hash !== "#inicio") history.replaceState(null, "", "#inicio");
  S.espacio?.enfocar(null);
}
async function refrescarTablero(c) {
  try {
    const t = await api(`/api/tablero/${c.id}`);
    c.tablero = { ...t, pendientes: t.pendientes.map((p) => ({ ...p })) };
    if (S.cerebro === c) vistaCerebro(c);
    vistaHoy();
  } catch (e) { if (e.status === 401) { S.editor = false; pintarSesion(); } }
}
async function editar(cid, cuerpo, mensaje) {
  const c = S.D.cerebros.find((x) => x.id === cid);
  try {
    const t = await api(`/api/tablero/${cid}`, cuerpo);
    c.tablero = t;
    if (S.cerebro === c) vistaCerebro(c);
    vistaHoy();
    avisar(mensaje + " En Obsidian en unos minutos.");
  } catch (e) {
    if (e.status === 401) { S.editor = false; pintarSesion(); }
    avisar(e.message);
  }
}

// ---------------------------------------------------------------- sesión

function pintarSesion() {
  const b = $("#b-sesion");
  b.textContent = S.editor ? "Salir" : "Entrar";
  b.classList.toggle("acento", S.editor);
  b.title = S.editor ? "Estás editando. Toca para cerrar la sesión en este equipo." : "Entra con tu contraseña para editar";
  vistaHoy();
  if (S.cerebro) vistaCerebro(S.cerebro);
}
async function sesion() {
  try { const s = await api("/api/sesion"); S.editor = !!s.editor; S.configurado = !!s.configurado; } catch { S.editor = false; }
  pintarSesion();
}

// ---------------------------------------------------------------- búsqueda

function buscar(q) {
  const k = q.trim().toLowerCase();
  const D = S.D, R = [];
  if (k) {
    for (const c of D.cerebros) {
      if (c.nombre.toLowerCase().includes(k) || c.descripcion.toLowerCase().includes(k)) R.push({ t: c.nombre, sub: "cerebro", ir: c.id });
      for (const p of (c.tablero?.pendientes || [])) if (!p.hecho && p.texto.toLowerCase().includes(k)) R.push({ t: p.texto, sub: `pendiente · ${c.nombre}`, ir: c.id });
      for (const r of c.repos) {
        const skills = (r.skills || []).map((s) => s.nombre).join(" ");
        if ((r.nombre + " " + (r.resumen || "") + " " + skills).toLowerCase().includes(k)) R.push({ t: r.nombre, sub: `repositorio · ${c.nombre}${skills ? " · " + skills : ""}`, ir: c.id });
      }
    }
    for (const t of (D.inventario?.tareas || [])) if (t.nombre.toLowerCase().includes(k)) R.push({ t: t.nombre, sub: `tarea programada · ${t.horario || ""}`, ir: t.cerebro });
  }
  $("#resultados").innerHTML = R.slice(0, 30).map((r) => `<button class="resultado" data-ir="${esc(r.ir)}"><span>${esc(r.t)}</span><span></span><span class="sub">${esc(r.sub)}</span></button>`).join("")
    || `<p class="vacio" style="padding:10px 12px">${k ? "Nada coincide." : "Escribe para buscar."}</p>`;
}

// ---------------------------------------------------------------- eventos

document.addEventListener("click", async (e) => {
  const t = e.target;
  const ir = t.closest("[data-ir]");
  if (ir && ir.dataset.ir) { $("#d-buscar").open && $("#d-buscar").close(); abrirCerebro(ir.dataset.ir); return; }
  if (t.closest("[data-cerrar-hoja]")) return cerrarCerebro();
  if (t.closest("[data-cerrar]")) return t.closest("dialog").close();
  if (t.closest("[data-entrar]")) return abrirEntrar();
  const comp = t.closest("[data-completar]");
  if (comp && S.editor) {
    const [cid, id] = comp.dataset.completar.split(":");
    const hecho = comp.getAttribute("aria-checked") !== "true"; // se manda el estado deseado, no «alternar»
    comp.setAttribute("aria-checked", String(hecho));
    return editar(cid, { accion: "completar", id, hecho }, hecho ? "Listo." : "Reabierto.");
  }
  const pr = t.closest("[data-prioridad]");
  if (pr && S.cerebro) return editar(S.cerebro.id, { accion: "prioridad", id: pr.dataset.prioridad, alta: !pr.classList.contains("activa") }, "Prioridad cambiada.");
  const bo = t.closest("[data-borrar]");
  if (bo && S.cerebro) return editar(S.cerebro.id, { accion: "borrar_pendiente", id: bo.dataset.borrar }, "Pendiente borrado.");
  const bn = t.closest("[data-borrar-nota]");
  if (bn && S.cerebro) return editar(S.cerebro.id, { accion: "borrar_nota", id: bn.dataset.borrarNota }, "Nota borrada.");
  if (t.closest("[data-copiar-general]")) {
    const r = await fetch("MATRIZ_GENERAL.md", { cache: "no-store" });
    return copiar(await r.text(), "Matriz General copiada. Pégala en cualquier IA.");
  }
  const cc = t.closest("[data-copiar-contexto]");
  if (cc) {
    const r = await fetch(`contexto/${cc.dataset.copiarContexto}.CONTEXTO.md`, { cache: "no-store" });
    return copiar((await r.text()).replace(/^---\n[\s\S]*?\n---\n/, ""), "Contexto copiado. Pégalo en cualquier IA.");
  }
  if (t.closest("#b-proyecto")) return abrirProyecto();
});
document.addEventListener("submit", async (e) => {
  const fp = e.target.closest("[data-nuevo-pendiente]"), fn = e.target.closest("[data-nueva-nota]");
  if (!fp && !fn) return;
  e.preventDefault();
  const d = new FormData(e.target);
  if (fp) await editar(S.cerebro.id, { accion: "agregar_pendiente", texto: d.get("texto"), alta: d.get("alta") === "on", vence: d.get("vence") || "" }, "Pendiente agregado.");
  else await editar(S.cerebro.id, { accion: "agregar_nota", texto: d.get("texto") }, "Nota guardada.");
});

function abrirEntrar() {
  if (!S.configurado) return avisar("La edición se activa cuando Emi guarde su contraseña y el token de escritura.");
  $("#e-entrar").textContent = "";
  $("#d-entrar").showModal();
  $("#clave").focus();
}
$("#b-sesion").addEventListener("click", async () => {
  if (!S.editor) return abrirEntrar();
  try {
    await api("/api/salir", {});
    S.editor = false; pintarSesion(); avisar("Sesión cerrada en este equipo.");
  } catch { avisar("No se pudo cerrar la sesión; revisa tu conexión e intenta de nuevo."); }
});
$("#f-entrar").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/entrar", { clave: $("#clave").value });
    $("#clave").value = "";
    $("#d-entrar").close();
    S.editor = true; pintarSesion(); avisar("Listo, ya puedes editar.");
    if (S.cerebro) refrescarTablero(S.cerebro);
  } catch (err) { $("#e-entrar").textContent = err.message; }
});
function abrirProyecto() {
  $("#p-cerebro").innerHTML = S.D.cerebros.map((c) => `<option value="${esc(c.id)}" ${S.cerebro?.id === c.id ? "selected" : ""}>${esc(c.nombre)}</option>`).join("");
  $("#e-proyecto").textContent = "";
  $("#d-proyecto").showModal();
}
$("#f-proyecto").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/proyecto", { nombre: $("#p-nombre").value, cerebro: $("#p-cerebro").value, descripcion: $("#p-desc").value });
    $("#d-proyecto").close(); $("#f-proyecto").reset();
    avisar("Proyecto creado. Aparecerá en la Matriz en unos minutos.");
  } catch (err) { $("#e-proyecto").textContent = err.message; }
});
$("#b-buscar").addEventListener("click", () => { $("#d-buscar").showModal(); $("#q").value = ""; buscar(""); $("#q").focus(); });
$("#q").addEventListener("input", (e) => buscar(e.target.value));
$("#b-copiar").addEventListener("click", async () => {
  const r = await fetch("MATRIZ_GENERAL.md", { cache: "no-store" });
  copiar(await r.text(), "Matriz General copiada. Pégala en cualquier IA.");
});
document.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); $("#b-buscar").click(); }
  if (e.key === "Escape" && S.cerebro && !document.querySelector("dialog[open]")) cerrarCerebro();
});
window.addEventListener("hashchange", () => {
  const id = location.hash.slice(1);
  if (id && id !== "inicio") abrirCerebro(id); else if (S.cerebro) cerrarCerebro();
});

// ---------------------------------------------------------------- arranque

// ---------------------------------------------------------------- en vivo
// Cada minuto (y al volver a la pestaña) revisa si hay datos nuevos y los pinta sin recargar la página.
// No interrumpe: si estás escribiendo en un formulario, espera a que termines.
const CADA = 60e3;
async function revisar() {
  if (document.hidden) return;
  let texto;
  try { texto = await (await fetch("matriz.json", { cache: "no-store" })).text(); } catch { pintarVivo(false); return; }
  S.revisado = Date.now();
  if (texto === S.texto) { pintarVivo(true); return; }
  const activo = document.activeElement;
  if (activo && activo.closest && activo.closest("form, dialog[open]") && /INPUT|TEXTAREA|SELECT/.test(activo.tagName)) { S.pendiente = true; return; }
  let D;
  try { D = JSON.parse(texto); } catch { return; }
  const estructura = (x) => x.cerebros.map((c) => c.id + ":" + c.repos.map((r) => r.nombre).join(",")).join("|");
  const cambioEstructura = estructura(D) !== estructura(S.D);
  S.D = D; S.texto = texto; S.pendiente = false;
  $("#fecha").textContent = `actualizada el ${f(S.D.actualizada).replace(/&amp;/g, "&")}`;
  vistaHoy();
  if (S.cerebro) { const c = S.D.cerebros.find((x) => x.id === S.cerebro.id); if (c) { S.cerebro = c; vistaCerebro(c); } }
  if (cambioEstructura && S.espacio && S.espacio.destruir) { S.espacio.destruir(); S.espacio = null; await montarEspacio(); }
  pintarVivo(true, true);
}
function pintarVivo(ok, nuevo = false) {
  const e = $("#vivo");
  if (!e) return;
  e.classList.toggle("caido", !ok);
  e.title = ok ? "En vivo: revisa cada minuto si hay cambios" : "Sin conexión: se reintenta cada minuto";
  if (nuevo) { e.classList.remove("latido"); void e.offsetWidth; e.classList.add("latido"); avisar("La Matriz se actualizó."); }
}
document.addEventListener("visibilitychange", () => { if (!document.hidden && Date.now() - (S.revisado || 0) > 15e3) revisar(); });
document.addEventListener("focusout", () => { if (S.pendiente) setTimeout(revisar, 500); });

async function montarEspacio() {
  try {
    const { crearEspacio } = await import("./espacio.js");
    S.espacio = await crearEspacio($("#espacio"), $("#etiquetas"), S.D, { alElegir: (cid) => (cid ? abrirCerebro(cid, true) : cerrarCerebro()), reducido });
    if (S.cerebro) S.espacio.enfocar(S.cerebro.id);
  } catch (err) {
    console.warn("Sin espacio 3D:", err);
  }
}

async function arrancar() {
  try {
    S.texto = await (await fetch("matriz.json", { cache: "no-store" })).text();
    S.D = JSON.parse(S.texto);
    S.revisado = Date.now();
  } catch {
    $("#hoy").innerHTML = `<section class="tarjeta"><h2>Sin conexión</h2><p class="vacio">No se pudo cargar la Matriz. Revisa tu conexión y recarga.</p></section>`;
    return;
  }
  $("#fecha").textContent = `actualizada el ${f(S.D.actualizada).replace(/&amp;/g, "&")}`;
  vistaHoy();
  sesion();
  const id = location.hash.slice(1);
  if (id && id !== "inicio") abrirCerebro(id);
  // El espacio 3D se carga después: lo esencial ya está en pantalla.
  await montarEspacio();
  pintarVivo(true);
  setInterval(revisar, CADA);
}
arrancar();
