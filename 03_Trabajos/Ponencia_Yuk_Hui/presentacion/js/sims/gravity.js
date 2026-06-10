(function () {
  /* -----------------------------------------------------------------------
   * MODELO GRAVITACIONAL — Interacción espacial (Ullman / Wilson, 1962)
   * T_ij = k * (M_i * M_j) / d_ij^beta
   * Varios centros urbanos con masa (población).  Flujos visualizados como
   * arcos curvos cuyo grosor/opacidad refleja la magnitud del flujo.
   * El usuario puede arrastrar centros → flujos se recalculan en vivo.
   * Clic en zona vacía → añade un nuevo centro.
   * Demuestra el modelo gravitacional (geografía cuantitativa clásica)
   * como objeto epistémico computable, sin IA.
   * --------------------------------------------------------------------- */

  /* ── Paleta ────────────────────────────────────────────────────────── */
  const C_BG      = '#0d1117';
  const C_GRID    = '#222b3a';
  const C_TEXT    = '#e8e6df';
  const C_MUTED   = '#8a93a3';
  const C_NODE_S  = '#e0a44e';   // residencial/amber — ciudades pequeñas
  const C_NODE_L  = '#e0524a';   // CBD/rojo — ciudades grandes
  const C_FLOW    = '#2dd4bf';   // transit/cian — flujos
  const C_ACCENT  = '#a78bfa';   // violeta — seleccionado/hover

  const K         = 1.0;         // constante gravitacional (normalizada)
  const MIN_DIST  = 20;          // evita división por cero

  /* ── Estado mutable ─────────────────────────────────────────────────── */
  let canvas, ctx, container;
  let rafId       = null;
  let observer    = null;
  let playing     = true;
  let beta        = 1.8;         // fricción de distancia por defecto

  let centers     = [];          // [{x, y, mass, name}]
  let dragIdx     = -1;
  let dragOffX    = 0;
  let dragOffY    = 0;

  let topPair     = { i: -1, j: -1, flow: 0 };

  /* ── Centros iniciales ──────────────────────────────────────────────── */
  function defaultCenters(W, H) {
    const pts = [
      { rx: 0.18, ry: 0.30, mass: 420, name: 'A' },
      { rx: 0.50, ry: 0.18, mass: 870, name: 'B' },
      { rx: 0.78, ry: 0.28, mass: 310, name: 'C' },
      { rx: 0.65, ry: 0.60, mass: 640, name: 'D' },
      { rx: 0.30, ry: 0.65, mass: 530, name: 'E' },
      { rx: 0.48, ry: 0.82, mass: 250, name: 'F' },
      { rx: 0.85, ry: 0.72, mass: 190, name: 'G' },
    ];
    return pts.map(p => ({
      x: p.rx * W,
      y: p.ry * H,
      mass: p.mass,
      name: p.name
    }));
  }

  /* ── Geometría ──────────────────────────────────────────────────────── */
  function nodeRadius(mass) {
    return 6 + Math.sqrt(mass) * 0.18;
  }

  function dist(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y;
    return Math.max(MIN_DIST, Math.sqrt(dx * dx + dy * dy));
  }

  function gravFlow(mi, mj, dij) {
    return K * (mi * mj) / Math.pow(dij, beta);
  }

  /* ── Calcular todos los flujos y el par máximo ──────────────────────── */
  function computeFlows() {
    const n = centers.length;
    const flows = [];
    let maxFlow = 0;
    let top = { i: -1, j: -1, flow: 0 };

    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const d = dist(centers[i], centers[j]);
        const f = gravFlow(centers[i].mass, centers[j].mass, d);
        flows.push({ i, j, f });
        if (f > maxFlow) { maxFlow = f; top = { i, j, flow: f }; }
      }
    }
    topPair = top;
    return { flows, maxFlow };
  }

  /* ── Dibujar ────────────────────────────────────────────────────────── */
  function draw() {
    const W = canvas.width  / (window.devicePixelRatio || 1);
    const H = canvas.height / (window.devicePixelRatio || 1);

    /* fondo */
    ctx.fillStyle = C_BG;
    ctx.fillRect(0, 0, W, H);

    /* grilla sutil */
    ctx.strokeStyle = C_GRID;
    ctx.lineWidth = 0.5;
    const gStep = 40;
    for (let x = 0; x < W; x += gStep) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y < H; y += gStep) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }

    const { flows, maxFlow } = computeFlows();
    if (maxFlow === 0) return;

    /* ── Arcos de flujo ──────────────────────────────────────────────── */
    for (const { i, j, f } of flows) {
      const ci = centers[i], cj = centers[j];
      const norm = f / maxFlow;              // 0..1
      const alpha = 0.08 + norm * 0.72;
      const lw    = 0.5 + norm * 5.5;

      /* punto de control curvado perpendicularmente */
      const mx = (ci.x + cj.x) / 2;
      const my = (ci.y + cj.y) / 2;
      const dx = cj.x - ci.x, dy = cj.y - ci.y;
      const len = Math.sqrt(dx * dx + dy * dy);
      const curv = Math.min(len * 0.25, 60);
      const cpx = mx + (-dy / len) * curv;
      const cpy = my + ( dx / len) * curv;

      /* color: cian con alpha según magnitud */
      const r = parseInt(C_FLOW.slice(1, 3), 16);
      const g = parseInt(C_FLOW.slice(3, 5), 16);
      const b = parseInt(C_FLOW.slice(5, 7), 16);

      ctx.strokeStyle = `rgba(${r},${g},${b},${alpha.toFixed(3)})`;
      ctx.lineWidth   = lw;
      ctx.lineCap     = 'round';

      /* destaca el par máximo */
      if (i === topPair.i && j === topPair.j) {
        ctx.shadowColor = C_FLOW;
        ctx.shadowBlur  = 10;
      } else {
        ctx.shadowBlur = 0;
      }

      ctx.beginPath();
      ctx.moveTo(ci.x, ci.y);
      ctx.quadraticCurveTo(cpx, cpy, cj.x, cj.y);
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    /* ── Nodos ───────────────────────────────────────────────────────── */
    for (let k = 0; k < centers.length; k++) {
      const c = centers[k];
      const r = nodeRadius(c.mass);
      /* color según masa: >500 → rojo CBD, resto → amber residencial */
      const fill = c.mass >= 500 ? C_NODE_L : C_NODE_S;

      /* halo para el par máximo */
      if (k === topPair.i || k === topPair.j) {
        ctx.beginPath();
        ctx.arc(c.x, c.y, r + 5, 0, Math.PI * 2);
        ctx.strokeStyle = C_ACCENT;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      /* círculo relleno */
      ctx.beginPath();
      ctx.arc(c.x, c.y, r, 0, Math.PI * 2);
      ctx.fillStyle = fill;
      ctx.fill();

      /* borde */
      ctx.strokeStyle = C_TEXT;
      ctx.lineWidth = 1;
      ctx.stroke();

      /* etiqueta */
      ctx.font = "bold 11px 'Inter', system-ui, sans-serif";
      ctx.fillStyle = C_TEXT;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(c.name, c.x, c.y);

      /* masa debajo */
      ctx.font = "10px 'Inter', system-ui, sans-serif";
      ctx.fillStyle = C_MUTED;
      ctx.fillText(c.mass + 'k', c.x, c.y + r + 10);
    }

    /* ── Readout en canvas (esquina superior izq) ────────────────────── */
    if (topPair.i >= 0 && topPair.j >= 0) {
      const ci = centers[topPair.i], cj = centers[topPair.j];
      ctx.font = "12px 'Inter', system-ui, sans-serif";
      ctx.textAlign = 'left';
      ctx.textBaseline = 'top';
      ctx.fillStyle = C_MUTED;
      ctx.fillText(`Mayor flujo: ${ci.name} ↔ ${cj.name}  (β=${beta.toFixed(1)})`, 12, 12);
    }
  }

  /* ── Loop RAF ────────────────────────────────────────────────────────── */
  function loop() {
    if (!playing) { rafId = requestAnimationFrame(loop); return; }
    draw();
    rafId = requestAnimationFrame(loop);
  }

  /* ── Interacción mouse ───────────────────────────────────────────────── */
  function hitTest(x, y) {
    for (let i = centers.length - 1; i >= 0; i--) {
      const c = centers[i];
      const r = nodeRadius(c.mass) + 4;
      const dx = x - c.x, dy = y - c.y;
      if (dx * dx + dy * dy <= r * r) return i;
    }
    return -1;
  }

  function canvasXY(e) {
    const rect = canvas.getBoundingClientRect();
    const src  = e.touches ? e.touches[0] : e;
    return {
      x: src.clientX - rect.left,
      y: src.clientY - rect.top
    };
  }

  function onMouseDown(e) {
    e.preventDefault();
    const { x, y } = canvasXY(e);
    const hit = hitTest(x, y);
    if (hit >= 0) {
      dragIdx  = hit;
      dragOffX = centers[hit].x - x;
      dragOffY = centers[hit].y - y;
    }
  }

  function onMouseMove(e) {
    if (dragIdx < 0) return;
    e.preventDefault();
    const { x, y } = canvasXY(e);
    centers[dragIdx].x = x + dragOffX;
    centers[dragIdx].y = y + dragOffY;
  }

  function onMouseUp(e) {
    if (dragIdx >= 0) { dragIdx = -1; return; }
    /* clic en vacío → nuevo centro */
    const { x, y } = canvasXY(e);
    if (hitTest(x, y) >= 0) return;
    const letter = String.fromCharCode(65 + centers.length % 26);
    centers.push({ x, y, mass: 150 + Math.round(Math.random() * 400), name: letter });
  }

  /* ── Resize ──────────────────────────────────────────────────────────── */
  function resize() {
    if (!canvas || !container) return;
    const dpr = window.devicePixelRatio || 1;
    const W   = container.clientWidth;
    const H   = container.clientHeight;
    canvas.width  = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width  = W + 'px';
    canvas.style.height = H + 'px';
    ctx.scale(dpr, dpr);
  }

  /* ── Mount / Unmount ─────────────────────────────────────────────────── */
  const SIM = {
    title: 'Modelo Gravitacional',

    mount(cont) {
      container = cont;

      /* canvas */
      canvas = document.createElement('canvas');
      canvas.style.display = 'block';
      container.appendChild(canvas);
      ctx = canvas.getContext('2d');
      resize();

      /* centros iniciales */
      const W = container.clientWidth;
      const H = container.clientHeight;
      centers = defaultCenters(W, H);
      dragIdx = -1;
      beta    = 1.8;
      playing = true;

      /* controles */
      const controls = document.createElement('div');
      controls.className = 'sim-controls';

      /* play/pause */
      const btnPlay = document.createElement('button');
      btnPlay.className = 'sim-btn';
      btnPlay.textContent = '⏸';
      btnPlay.title = 'Play / Pausa';
      btnPlay.addEventListener('click', () => {
        playing = !playing;
        btnPlay.textContent = playing ? '⏸' : '▶';
      });

      /* reset */
      const btnReset = document.createElement('button');
      btnReset.className = 'sim-btn';
      btnReset.textContent = '↺';
      btnReset.title = 'Reiniciar';
      btnReset.addEventListener('click', () => {
        const W2 = container.clientWidth;
        const H2 = container.clientHeight;
        centers = defaultCenters(W2, H2);
        playing = true;
        btnPlay.textContent = '⏸';
      });

      /* slider beta */
      const lblBeta = document.createElement('label');
      lblBeta.style.display = 'flex';
      lblBeta.style.alignItems = 'center';
      lblBeta.style.gap = '6px';
      lblBeta.style.color = 'var(--color-text-muted, #8a93a3)';
      lblBeta.style.fontSize = '12px';

      const spanBeta = document.createElement('span');
      spanBeta.textContent = 'β ' + beta.toFixed(1);

      const sliderBeta = document.createElement('input');
      sliderBeta.type      = 'range';
      sliderBeta.className = 'sim-range';
      sliderBeta.min       = '0.5';
      sliderBeta.max       = '3.0';
      sliderBeta.step      = '0.1';
      sliderBeta.value     = String(beta);
      sliderBeta.addEventListener('input', () => {
        beta = parseFloat(sliderBeta.value);
        spanBeta.textContent = 'β ' + beta.toFixed(1);
      });

      lblBeta.appendChild(spanBeta);
      lblBeta.appendChild(sliderBeta);

      controls.appendChild(btnPlay);
      controls.appendChild(btnReset);
      controls.appendChild(lblBeta);
      container.appendChild(controls);

      /* leyenda */
      const legend = document.createElement('div');
      legend.className = 'sim-legend';
      legend.innerHTML =
        '<span style="color:#e0524a">●</span> Ciudad grande &nbsp;' +
        '<span style="color:#e0a44e">●</span> Ciudad pequeña &nbsp;' +
        '<span style="color:#2dd4bf">─</span> Flujo T<sub>ij</sub> (grosor = magnitud) &nbsp;' +
        '<span style="color:#a78bfa">○</span> Par máximo &nbsp;' +
        '| Arrastra nodos · Clic vacío = nuevo centro';
      container.appendChild(legend);

      /* readout DOM (oculto — info dibujada en canvas) */
      const readout = document.createElement('div');
      readout.className = 'sim-readout';
      readout.style.display = 'none';
      container.appendChild(readout);

      /* listeners de interacción */
      canvas.addEventListener('mousedown',  onMouseDown);
      canvas.addEventListener('mousemove',  onMouseMove);
      canvas.addEventListener('mouseup',    onMouseUp);
      canvas.addEventListener('touchstart', onMouseDown, { passive: false });
      canvas.addEventListener('touchmove',  onMouseMove, { passive: false });
      canvas.addEventListener('touchend',   onMouseUp);

      /* ResizeObserver */
      observer = new ResizeObserver(() => {
        resize();
        draw();
      });
      observer.observe(container);

      /* RAF */
      rafId = requestAnimationFrame(loop);
    },

    unmount() {
      if (rafId   !== null) { cancelAnimationFrame(rafId); rafId = null; }
      if (observer !== null) { observer.disconnect(); observer = null; }

      if (canvas) {
        canvas.removeEventListener('mousedown',  onMouseDown);
        canvas.removeEventListener('mousemove',  onMouseMove);
        canvas.removeEventListener('mouseup',    onMouseUp);
        canvas.removeEventListener('touchstart', onMouseDown);
        canvas.removeEventListener('touchmove',  onMouseMove);
        canvas.removeEventListener('touchend',   onMouseUp);
      }

      if (container) container.innerHTML = '';

      canvas    = null;
      ctx       = null;
      container = null;
      centers   = [];
      dragIdx   = -1;
    }
  };

  window.PonenciaSims = window.PonenciaSims || {};
  window.PonenciaSims['gravity'] = SIM;
})();
