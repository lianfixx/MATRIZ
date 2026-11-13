// Matriz · espacio 3D. La Matriz al centro, los cerebros en órbita y sus repositorios girando alrededor.
// El tamaño de cada cerebro sigue su actividad; los que llevan semanas quietos se apagan un poco.
import * as THREE from "./vendor/three.matriz.min.js";

const ACENTO = new THREE.Color("#ff5a1f");
const TINTA = new THREE.Color("#ece9e4");
const TENUE = new THREE.Color("#8a8780");

function halo(color, fuerza = 1) {
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const g = c.getContext("2d");
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  const [r, v, a] = [color.r * 255, color.g * 255, color.b * 255].map(Math.round);
  gr.addColorStop(0, `rgba(${r},${v},${a},${0.55 * fuerza})`);
  gr.addColorStop(0.25, `rgba(${r},${v},${a},${0.18 * fuerza})`);
  gr.addColorStop(1, `rgba(${r},${v},${a},0)`);
  g.fillStyle = gr;
  g.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(c);
  return new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
}

export async function crearEspacio(lienzo, capaEtiquetas, D, { alElegir, reducido }) {
  const renderer = new THREE.WebGLRenderer({ canvas: lienzo, antialias: true, alpha: true, powerPreference: "low-power" });
  renderer.setClearColor(0x000000, 0);
  const escena = new THREE.Scene();
  const camara = new THREE.PerspectiveCamera(42, 1, 0.1, 400);
  const M = D.metricas?.cerebros || {};

  // Polvo de fondo: muy tenue, apenas se mueve.
  const nPolvo = 700, pos = new Float32Array(nPolvo * 3);
  for (let i = 0; i < nPolvo; i++) {
    const r = 60 + Math.random() * 90, t = Math.random() * Math.PI * 2, p = Math.acos(2 * Math.random() - 1);
    pos.set([r * Math.sin(p) * Math.cos(t), r * Math.cos(p) * 0.6, r * Math.sin(p) * Math.sin(t)], i * 3);
  }
  const gPolvo = new THREE.BufferGeometry();
  gPolvo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  const polvo = new THREE.Points(gPolvo, new THREE.PointsMaterial({ color: 0x8a8780, size: 0.35, sizeAttenuation: true, transparent: true, opacity: 0.35, depthWrite: false }));
  escena.add(polvo);

  // Núcleo: la Matriz.
  const raiz = new THREE.Group();
  escena.add(raiz);
  const nucleo = new THREE.Mesh(new THREE.SphereGeometry(0.9, 48, 32), new THREE.MeshBasicMaterial({ color: ACENTO }));
  raiz.add(nucleo);
  const haloNucleo = halo(ACENTO, 1.2);
  haloNucleo.scale.setScalar(9);
  raiz.add(haloNucleo);

  // Órbita de los cerebros.
  const R = 7.2, segs = 160, orbita = [];
  for (let i = 0; i < segs; i++) {
    const a = (i / segs) * Math.PI * 2, b = ((i + 1) / segs) * Math.PI * 2;
    orbita.push(Math.cos(a) * R, 0, Math.sin(a) * R, Math.cos(b) * R, 0, Math.sin(b) * R);
  }
  const gOrb = new THREE.BufferGeometry();
  gOrb.setAttribute("position", new THREE.Float32BufferAttribute(orbita, 3));
  raiz.add(new THREE.LineSegments(gOrb, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.07 })));

  const maxAct = Math.max(1, ...D.cerebros.map((c) => M[c.id]?.esta_semana || 0));
  const nodos = D.cerebros.map((c, i) => {
    const m = M[c.id] || {};
    const ang = -Math.PI / 2 + (i / D.cerebros.length) * Math.PI * 2;
    const quieto = (m.dias_sin_movimiento ?? 0) > 21;
    const radio = 0.32 + 0.38 * Math.sqrt((m.esta_semana || 0) / maxAct);
    const color = quieto ? TENUE : TINTA;
    const malla = new THREE.Mesh(new THREE.SphereGeometry(radio, 32, 20), new THREE.MeshBasicMaterial({ color }));
    const h = halo(color, quieto ? 0.4 : 0.8);
    h.scale.setScalar(radio * 7);
    const grupo = new THREE.Group();
    grupo.add(malla, h);
    grupo.position.set(Math.cos(ang) * R, Math.sin(i * 1.7) * 0.9, Math.sin(ang) * R);
    if ((m.pendientes_vencidos || 0) + (m.tareas_falladas || 0) > 0) {
      const aviso = new THREE.Mesh(new THREE.RingGeometry(radio * 1.6, radio * 1.68, 48), new THREE.MeshBasicMaterial({ color: 0xef8a6a, transparent: true, opacity: 0.7, side: THREE.DoubleSide }));
      grupo.add(aviso);
      grupo.userData.aviso = aviso;
    }
    malla.userData.cerebro = c.id;
    raiz.add(grupo);
    const repos = c.repos.map((r, j) => {
      const act = (r.actividad?.commits || []).reduce((s, x) => s + x, 0);
      const p = new THREE.Mesh(new THREE.SphereGeometry(0.06 + Math.min(0.12, act * 0.01), 12, 8),
        new THREE.MeshBasicMaterial({ color: r.visibilidad === "privado" ? TENUE : TINTA, transparent: true, opacity: 0.85 }));
      raiz.add(p);
      return { malla: p, r, radio: 1.15 + (j % 3) * 0.32 + radio, fase: (j / c.repos.length) * Math.PI * 2, vel: 0.12 + (j % 4) * 0.035, incl: 0.35 + (j % 2) * 0.3 };
    });
    return { c, grupo, malla, repos, radio };
  });

  // Líneas núcleo→cerebro y cerebro→repositorios (se recalculan en cada cuadro).
  const totalSeg = nodos.length + nodos.reduce((s, n) => s + n.repos.length, 0);
  const lineas = new Float32Array(totalSeg * 6);
  const gLin = new THREE.BufferGeometry();
  gLin.setAttribute("position", new THREE.Float32BufferAttribute(lineas, 3));
  const enlaces = new THREE.LineSegments(gLin, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.1 }));
  raiz.add(enlaces);

  // Etiquetas en HTML: texto nítido y accesible.
  const etiquetas = nodos.map((n) => { const e = document.createElement("div"); e.className = "etq"; e.textContent = n.c.nombre; capaEtiquetas.appendChild(e); return e; });
  const etNucleo = document.createElement("div"); etNucleo.className = "etq nucleo"; etNucleo.textContent = "Matriz"; capaEtiquetas.appendChild(etNucleo);
  const etRepos = [];

  // Cámara: órbita suave, se puede girar con el dedo o el mouse y acercar con la rueda o pellizcando.
  const vista = { yaw: 0.55, pitch: 0.42, dist: 23, objetivo: new THREE.Vector3(), yawO: 0.55, pitchO: 0.42, distO: 23, objO: new THREE.Vector3() };
  let foco = null, arrastre = null, inactivo = 0;
  const ray = new THREE.Raycaster(), puntero = new THREE.Vector2();

  function tamano() {
    const w = lienzo.clientWidth, h = lienzo.clientHeight;
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.75));
    renderer.setSize(w, h, false);
    camara.aspect = w / Math.max(1, h);
    camara.updateProjectionMatrix();
    // En pantallas angostas (iPhone) la cámara se aleja para que quepan los siete cerebros.
    lejos = 23 * Math.max(1, 1.05 / camara.aspect);
    if (!foco) vista.distO = lejos;
    desplazar(true);
  }
  let lejos = 23;
  // En pantallas anchas la Matriz se centra en el hueco libre: a la derecha de la columna «Hoy»
  // y, con un cerebro abierto, entre la columna y la hoja.
  let desp = 0;
  function desplazar(forzar, k = 1) {
    const w = lienzo.clientWidth, h = lienzo.clientHeight;
    const meta = w <= 860 ? 0 : foco ? (460 - 392) / 2 : -Math.min(196, w * 0.13);
    const nuevo = desp + (meta - desp) * k;
    if (!forzar && Math.abs(nuevo - desp) < 0.25) return;
    desp = Math.abs(meta - nuevo) < 0.25 ? meta : nuevo;
    camara.setViewOffset(w, h, desp, 0, w, h);
  }
  const corte = new AbortController(), sig = { signal: corte.signal };
  let vivo = true;
  addEventListener("resize", tamano, sig);
  // Cuando cargan las fuentes cambian los anchos de las etiquetas: se vuelven a medir.
  document.fonts?.ready.then(() => capaEtiquetas.querySelectorAll(".etq").forEach((e) => { e._a = 0; }));
  tamano();

  function elegir(ev) {
    const r = lienzo.getBoundingClientRect();
    puntero.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(puntero, camara);
    const hit = ray.intersectObjects(nodos.map((n) => n.malla))[0];
    return hit ? hit.object.userData.cerebro : null;
  }
  lienzo.addEventListener("pointerdown", (e) => { arrastre = { x: e.clientX, y: e.clientY, yaw: vista.yawO, pitch: vista.pitchO, movio: false }; lienzo.setPointerCapture(e.pointerId); }, sig);
  lienzo.addEventListener("pointermove", (e) => {
    if (arrastre) {
      const dx = e.clientX - arrastre.x, dy = e.clientY - arrastre.y;
      if (Math.abs(dx) + Math.abs(dy) > 4) arrastre.movio = true;
      vista.yawO = arrastre.yaw - dx * 0.005;
      vista.pitchO = Math.max(0.05, Math.min(1.2, arrastre.pitch + dy * 0.004));
      inactivo = 0;
    } else if (e.pointerType === "mouse") {
      lienzo.style.cursor = elegir(e) ? "pointer" : "grab";
    }
  }, sig);
  lienzo.addEventListener("pointerup", (e) => {
    if (arrastre && !arrastre.movio) {
      const id = elegir(e);
      if (id) { enfocar(id); alElegir(id); } else if (foco) { enfocar(null); alElegir(null); }
    }
    arrastre = null;
  }, sig);
  lienzo.addEventListener("wheel", (e) => { e.preventDefault(); vista.distO = Math.max(9, Math.min(40, vista.distO * (1 + e.deltaY * 0.001))); inactivo = 0; }, { passive: false, ...sig });

  function enfocar(id) {
    foco = nodos.find((n) => n.c.id === id) || null;
    etRepos.splice(0).forEach((e) => e.remove());
    if (foco) {
      foco.repos.forEach((p) => { const e = document.createElement("div"); e.className = "etq repo"; e.textContent = p.r.nombre; capaEtiquetas.appendChild(e); etRepos.push(e); });
      vista.distO = 13 + foco.radio * 3;
    } else {
      vista.distO = lejos;
      vista.objO.set(0, 0, 0);
    }
  }

  // Animación
  const reloj = new THREE.Clock();
  const v = new THREE.Vector3(), m3 = new THREE.Vector3();
  let visible = true;
  document.addEventListener("visibilitychange", () => { visible = !document.hidden; if (visible) reloj.getDelta(); }, sig);
  const suave = (a, b, k) => a + (b - a) * k;

  function cuadro() {
    if (!vivo) return;
    requestAnimationFrame(cuadro);
    if (!visible) return;
    const dt = Math.min(reloj.getDelta(), 0.05), t = reloj.elapsedTime;
    const mov = reducido ? 0 : 1;
    inactivo += dt;
    if (!arrastre && !foco && inactivo > 2.5) vista.yawO += dt * 0.035 * mov;
    raiz.rotation.y += dt * 0.012 * mov;
    polvo.rotation.y -= dt * 0.004 * mov;

    let k = 0;
    nodos.forEach((n, i) => {
      n.grupo.position.y = Math.sin(i * 1.7) * 0.9 + Math.sin(t * 0.4 + i) * 0.12 * mov;
      if (n.grupo.userData.aviso) { n.grupo.userData.aviso.lookAt(camara.position); n.grupo.userData.aviso.material.opacity = 0.45 + 0.3 * Math.sin(t * 2.2) * mov; }
      const cp = n.grupo.position;
      lineas.set([0, 0, 0, cp.x, cp.y, cp.z], k); k += 6;
      n.repos.forEach((p) => {
        const a = p.fase + t * p.vel * mov;
        p.malla.position.set(cp.x + Math.cos(a) * p.radio, cp.y + Math.sin(a) * p.radio * p.incl, cp.z + Math.sin(a) * p.radio);
        lineas.set([cp.x, cp.y, cp.z, p.malla.position.x, p.malla.position.y, p.malla.position.z], k); k += 6;
      });
    });
    gLin.attributes.position.needsUpdate = true;
    nucleo.scale.setScalar(1 + Math.sin(t * 1.3) * 0.025 * mov);

    if (foco) foco.grupo.getWorldPosition(vista.objO);
    const kk = reducido ? 1 : 1 - Math.pow(0.0015, dt);
    vista.yaw = suave(vista.yaw, vista.yawO, kk); vista.pitch = suave(vista.pitch, vista.pitchO, kk);
    vista.dist = suave(vista.dist, vista.distO, kk); vista.objetivo.lerp(vista.objO, kk);
    desplazar(false, kk);
    camara.position.set(
      vista.objetivo.x + vista.dist * Math.cos(vista.pitch) * Math.sin(vista.yaw),
      vista.objetivo.y + vista.dist * Math.sin(vista.pitch),
      vista.objetivo.z + vista.dist * Math.cos(vista.pitch) * Math.cos(vista.yaw));
    camara.lookAt(vista.objetivo);
    renderer.render(escena, camara);

    // Etiquetas: cada una debajo de su esfera; si choca con otra o tapa una esfera, prueba arriba;
    // si tampoco cabe, se apaga. El cerebro elegido y la Matriz tienen prioridad.
    const w = lienzo.clientWidth, h = lienzo.clientHeight;
    const tanMedio = Math.tan(THREE.MathUtils.degToRad(camara.fov / 2));
    const items = [];
    const medir = (el, obj, r, base, prioridad) => {
      obj.getWorldPosition(m3);
      v.copy(m3).project(camara);
      if (!(v.z < 1 && Math.abs(v.x) < 1.15 && Math.abs(v.y) < 1.15)) { el.style.visibility = "hidden"; el.style.opacity = 0; return null; }
      const d = m3.distanceTo(camara.position);
      const it = { el, base, prioridad, d, x: ((v.x + 1) / 2) * w, y: ((1 - v.y) / 2) * h, rp: (r / Math.max(0.1, d * tanMedio)) * (h / 2) };
      items.push(it);
      return it;
    };
    nodos.forEach((n, i) => medir(etiquetas[i], n.grupo, n.grupo.userData.aviso ? n.radio * 1.7 : n.radio, foco && foco !== n ? 0.35 : 1, n === foco ? 0 : 2));
    medir(etNucleo, nucleo, 0.9, foco ? 0.3 : 1, 1);
    if (foco) foco.repos.forEach((p, i) => medir(etRepos[i], p.malla, 0.1, 0.9, 3));
    const esferas = items.filter((it) => it.prioridad < 3);
    const puestas = [];
    const choca = (c, propio) => puestas.some((o) => c.x0 < o.x1 + 4 && c.x1 > o.x0 - 4 && c.y0 < o.y1 + 1 && c.y1 > o.y0 - 1)
      || esferas.some((e) => e !== propio &&
        Math.hypot(Math.max(c.x0 - e.x, 0, e.x - c.x1), Math.max(c.y0 - e.y, 0, e.y - c.y1)) < e.rp * 0.95);
    items.sort((a, b) => a.prioridad - b.prioridad || a.d - b.d).forEach((it) => {
      const el = it.el;
      if (!el._a) { el._a = el.offsetWidth; el._b = el.offsetHeight; }
      const a = el._a || 60, b = el._b || 16;
      const caja = (top) => ({ x0: it.x - a / 2, x1: it.x + a / 2, y0: top, y1: top + b });
      const opciones = [it.y + it.rp + 6, it.y - it.rp - 6 - b];
      let top = opciones.find((t) => !choca(caja(t), it));
      const cabe = top !== undefined || it.prioridad < 2;
      if (top === undefined) top = opciones[0];
      if (cabe) puestas.push(caja(top));
      el.style.visibility = "visible";
      el.style.opacity = cabe ? it.base : 0;
      el.style.transform = `translate(${it.x - a / 2}px, ${top}px)`;
    });
  }
  cuadro();
  // Para datos nuevos con otra estructura: suelta todo y deja el lienzo listo para crear otro espacio.
  function destruir() {
    vivo = false; corte.abort();
    capaEtiquetas.replaceChildren();
    escena.traverse((o) => { o.geometry?.dispose?.(); (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => { m?.map?.dispose?.(); m?.dispose?.(); }); });
    renderer.dispose();
  }
  return { enfocar, destruir };
}
