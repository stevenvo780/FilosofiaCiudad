(function () {
  /* -----------------------------------------------------------------------
   * TRÁFICO BASADO EN AGENTES — Microsimulación sobre red vial
   * Red tipo grid con arteriales diagonales. Vehículos-agente se spawnean
   * con origen/destino aleatorios, enrutan por camino más corto (Dijkstra)
   * y avanzan respetando la vía. La acumulación genera congestión y baja la
   * velocidad. Los segmentos se colorean por densidad/velocidad:
   *   verde #5cab73 (fluido) → amber #e0a44e → rojo #e0524a (congestionado)
   * Demuestra modelado de transporte (microsimulación) como objeto epistémico,
   * sin IA.
   * --------------------------------------------------------------------- */

  // ---- Paleta (SPEC.md) --------------------------------------------------
  const C_BG       = '#0d1117';
  const C_GRID     = '#222b3a';
  const C_PANEL    = '#161b26';
  const C_TEXT     = '#e8e6df';
  const C_MUTED    = '#8a93a3';
  const C_VIA      = '#cdd6e3';
  const C_FREE     = '#5cab73';   // parque/verde — fluido
  const C_MID      = '#e0a44e';   // residencial/amber — moderado
  const C_JAM      = '#e0524a';   // CBD/rojo — congestionado
  const C_VEHICLE  = '#2dd4bf';   // transit/cian
  const C_ACCENT   = '#a78bfa';   // acento violeta
  const C_WATER    = '#3b82c4';

  // ---- Parámetros del modelo ---------------------------------------------
  const SPEED_FREE     = 1.8;   // píxeles/frame a velocidad libre
  const JAM_DENSITY    = 4;     // vehículos/segmento → congestión total
  const SPAWN_INTERVAL_BASE = 60; // frames base entre spawns (escala con slider)
  const MAX_VEHICLES   = 120;
  const VEHICLE_R      = 3.5;

  // ---- Utilidades de color -----------------------------------------------
  function hexToRgb(h) {
    const v = parseInt(h.slice(1), 16);
    return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
  }
  function rgbToHex(r, g, b) {
    return '#' + [r, g, b].map(x => Math.round(Math.max(0, Math.min(255, x)))
      .toString(16).padStart(2, '0')).join('');
  }
  function lerp(a, b, t) { return a + (b - a) * t; }

  // Rampa verde → amber → rojo para t ∈ [0,1]
  function densityColor(t) {
    const free = hexToRgb(C_FREE);
    const mid  = hexToRgb(C_MID);
    const jam  = hexToRgb(C_JAM);
    let r, g, b;
    if (t < 0.5) {
      const s = t / 0.5;
      r = lerp(free[0], mid[0], s);
      g = lerp(free[1], mid[1], s);
      b = lerp(free[2], mid[2], s);
    } else {
      const s = (t - 0.5) / 0.5;
      r = lerp(mid[0], jam[0], s);
      g = lerp(mid[1], jam[1], s);
      b = lerp(mid[2], jam[2], s);
    }
    return rgbToHex(r, g, b);
  }

  // ---- Generación de red vial --------------------------------------------
  // Grid ~6×5 con jitter + 4–6 arteriales diagonales

  function buildNetwork(W, H) {
    const COLS = 7, ROWS = 6;
    const MX = W * 0.07, MY = H * 0.09;
    const UW = W - 2 * MX, UH = H - 2 * MY;

    const nodes = [];   // { x, y, id }
    const nodeMap = {}; // "col_row" → id

    // Grid principal
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const bx = MX + (c / (COLS - 1)) * UW;
        const by = MY + (r / (ROWS - 1)) * UH;
        // Pequeño jitter: menos en bordes
        const jf = 0.38;
        const jx = (c === 0 || c === COLS - 1) ? 0 : (seededRand(c * 17 + r * 31) - 0.5) * (UW / COLS) * jf;
        const jy = (r === 0 || r === ROWS - 1) ? 0 : (seededRand(c * 37 + r * 13) - 0.5) * (UH / ROWS) * jf;
        const id = nodes.length;
        nodes.push({ x: bx + jx, y: by + jy, id });
        nodeMap[c + '_' + r] = id;
      }
    }

    // Nodos arteriales en cruce diagonal (4 puntos extra)
    const arterials = [
      { x: MX + UW * 0.22, y: MY + UH * 0.30 },
      { x: MX + UW * 0.55, y: MY + UH * 0.18 },
      { x: MX + UW * 0.78, y: MY + UH * 0.60 },
      { x: MX + UW * 0.38, y: MY + UH * 0.72 },
    ];
    const arterialIds = arterials.map(p => {
      const id = nodes.length;
      nodes.push({ x: p.x, y: p.y, id });
      return id;
    });

    const edgeSet = new Set();
    const edges = []; // { a, b, length, id, vehicles }

    function addEdge(i, j) {
      if (i === j) return;
      const key = i < j ? i + '_' + j : j + '_' + i;
      if (edgeSet.has(key)) return;
      edgeSet.add(key);
      const dx = nodes[i].x - nodes[j].x;
      const dy = nodes[i].y - nodes[j].y;
      const length = Math.sqrt(dx * dx + dy * dy);
      edges.push({ a: i, b: j, length, id: edges.length, vehicles: 0 });
    }

    // Conectar grid horizontal y vertical
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const id = nodeMap[c + '_' + r];
        if (c + 1 < COLS) addEdge(id, nodeMap[(c + 1) + '_' + r]);
        if (r + 1 < ROWS) addEdge(id, nodeMap[c + '_' + (r + 1)]);
      }
    }

    // Arteriales: conectar cada nodo arterial a sus 3 grid-nodos más cercanos
    for (const aid of arterialIds) {
      const dists = [];
      for (let i = 0; i < nodes.length - arterialIds.length; i++) {
        const dx = nodes[i].x - nodes[aid].x;
        const dy = nodes[i].y - nodes[aid].y;
        dists.push({ i, d: Math.sqrt(dx * dx + dy * dy) });
      }
      dists.sort((a, b) => a.d - b.d);
      for (let k = 0; k < Math.min(3, dists.length); k++) addEdge(aid, dists[k].i);
    }
    // Conectar arteriales entre sí (red diagonal)
    for (let i = 0; i < arterialIds.length; i++) {
      for (let j = i + 1; j < arterialIds.length; j++) {
        const dx = nodes[arterialIds[i]].x - nodes[arterialIds[j]].x;
        const dy = nodes[arterialIds[i]].y - nodes[arterialIds[j]].y;
        if (Math.sqrt(dx * dx + dy * dy) < Math.min(W, H) * 0.45) {
          addEdge(arterialIds[i], arterialIds[j]);
        }
      }
    }

    // Lista de adyacencia
    const adj = nodes.map(() => []);
    for (const e of edges) {
      adj[e.a].push({ to: e.b, eid: e.id, w: e.length });
      adj[e.b].push({ to: e.a, eid: e.id, w: e.length });
    }

    return { nodes, edges, adj };
  }

  // PRNG determinista (evita que cada resize genere una red diferente)
  function seededRand(seed) {
    let x = Math.sin(seed + 1) * 10000;
    return x - Math.floor(x);
  }

  // ---- Dijkstra ----------------------------------------------------------
  // Retorna array de edge-ids en orden (origen→destino), o null si no hay camino
  function dijkstra(src, dst, adj, nodes) {
    const n = nodes.length;
    const dist  = new Float64Array(n).fill(Infinity);
    const prevN = new Int32Array(n).fill(-1);
    const prevE = new Int32Array(n).fill(-1);
    const vis   = new Uint8Array(n);
    dist[src] = 0;

    // Min-heap simple (array con ordenamiento manual; red pequeña)
    const pq = [{ d: 0, u: src }];

    while (pq.length > 0) {
      // Extraer mínimo
      let minIdx = 0;
      for (let i = 1; i < pq.length; i++) {
        if (pq[i].d < pq[minIdx].d) minIdx = i;
      }
      const { u } = pq[minIdx];
      pq.splice(minIdx, 1);

      if (vis[u]) continue;
      vis[u] = 1;
      if (u === dst) break;

      for (const nb of adj[u]) {
        const nd = dist[u] + nb.w;
        if (nd < dist[nb.to]) {
          dist[nb.to] = nd;
          prevN[nb.to] = u;
          prevE[nb.to] = nb.eid;
          pq.push({ d: nd, u: nb.to });
        }
      }
    }

    if (dist[dst] === Infinity) return null;

    // Reconstruir camino como lista de { eid, from, to }
    const path = [];
    let cur = dst;
    while (cur !== src) {
      const eid  = prevE[cur];
      const from = prevN[cur];
      path.unshift({ eid, from, to: cur });
      cur = from;
    }
    return path; // [{ eid, from, to }, ...]
  }

  // ---- Vehículo-agente ---------------------------------------------------
  // Un vehículo sigue su path segmento a segmento.
  // En cada segmento su velocidad = SPEED_FREE * (1 - density/JAM_DENSITY)
  // donde density = vehículos en ese segmento.

  let _uidCounter = 0;
  function createVehicle(src, dst, path, nodes) {
    if (!path || path.length === 0) return null;
    const first = path[0];
    return {
      uid: _uidCounter++,
      src, dst,
      path,            // lista de { eid, from, to }
      segIdx: 0,       // índice en path
      // Posición interpolada sobre el segmento actual
      t: 0,            // 0..1 a lo largo del segmento
      x: nodes[first.from].x,
      y: nodes[first.from].y,
      done: false,
      color: C_VEHICLE
    };
  }

  // ---- Cómputo de densidad y color de aristas ----------------------------
  function updateEdgeDensity(edges, vehicles) {
    // Reset
    for (const e of edges) e.vehicles = 0;
    for (const v of vehicles) {
      if (v.done) continue;
      if (v.segIdx < v.path.length) {
        const seg = v.path[v.segIdx];
        edges[seg.eid].vehicles++;
      }
    }
  }

  function edgeDensityT(edge) {
    return Math.min(1, edge.vehicles / JAM_DENSITY);
  }

  // ---- Render ------------------------------------------------------------
  function render(ctx, state, W, H) {
    ctx.fillStyle = C_BG;
    ctx.fillRect(0, 0, W, H);

    const { nodes, edges, vehicles } = state;
    if (!nodes) return;

    // --- Aristas coloreadas por densidad
    for (const e of edges) {
      const na = nodes[e.a], nb = nodes[e.b];
      const t = edgeDensityT(e);
      const color = densityColor(t);
      // Grosor 2→6 según densidad
      const thick = 2 + t * 4;

      ctx.beginPath();
      ctx.moveTo(na.x, na.y);
      ctx.lineTo(nb.x, nb.y);
      ctx.strokeStyle = color;
      ctx.lineWidth = thick;
      ctx.lineCap = 'round';
      ctx.stroke();
    }

    // --- Nodos (intersecciones)
    for (const n of nodes) {
      ctx.beginPath();
      ctx.arc(n.x, n.y, 3, 0, Math.PI * 2);
      ctx.fillStyle = C_VIA;
      ctx.fill();
    }

    // --- Vehículos
    for (const v of vehicles) {
      if (v.done) continue;
      ctx.beginPath();
      ctx.arc(v.x, v.y, VEHICLE_R, 0, Math.PI * 2);
      ctx.fillStyle = C_VEHICLE;
      ctx.fill();
      // Anillo tenue
      ctx.beginPath();
      ctx.arc(v.x, v.y, VEHICLE_R + 1.5, 0, Math.PI * 2);
      ctx.strokeStyle = C_VEHICLE + '55';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // --- Título
    ctx.font = "bold 13px 'Inter', system-ui, sans-serif";
    ctx.fillStyle = C_MUTED;
    ctx.fillText('Microsimulación de tráfico basada en agentes', 12, 18);
  }

  // ---- SIM object --------------------------------------------------------
  const SIM = {
    title: 'Tráfico — Agentes',

    // Estado persistente del SIM
    _container:   null,
    _canvas:      null,
    _ctx:         null,
    _observer:    null,
    _rafId:       null,
    _running:     false,

    // Red vial
    _nodes:       null,
    _edges:       null,
    _adj:         null,

    // Vehículos
    _vehicles:    null,
    _frameCount:  0,
    _spawnRate:   1.0,   // multiplicador; 1 = normal, 2 = doble

    // UI
    _readoutEl:   null,
    _btnPlay:     null,

    // ---- Construcción de red ---------------------------------------------
    _buildNetwork() {
      if (!this._canvas) return;
      const dpr = window.devicePixelRatio || 1;
      const W = this._canvas.width  / dpr;
      const H = this._canvas.height / dpr;
      const net = buildNetwork(W, H);
      this._nodes    = net.nodes;
      this._edges    = net.edges;
      this._adj      = net.adj;
      this._vehicles = [];
      this._frameCount = 0;
      _uidCounter = 0;
    },

    // ---- Spawn de vehículo aleatorio ------------------------------------
    _spawnVehicle() {
      const nodes = this._nodes;
      const n = nodes.length;
      if (n < 2) return;

      let src, dst, attempts = 0;
      do {
        src = (Math.random() * n) | 0;
        dst = (Math.random() * n) | 0;
        attempts++;
      } while (src === dst && attempts < 20);
      if (src === dst) return;

      const path = dijkstra(src, dst, this._adj, nodes);
      if (!path || path.length === 0) return;

      const v = createVehicle(src, dst, path, nodes);
      if (v) this._vehicles.push(v);
    },

    // ---- Paso de simulación ---------------------------------------------
    _step() {
      if (!this._nodes) return;

      const nodes   = this._nodes;
      const edges   = this._edges;
      const vehicles = this._vehicles;

      // Actualizar densidad por arista
      updateEdgeDensity(edges, vehicles);

      // Avanzar cada vehículo
      for (const v of vehicles) {
        if (v.done) continue;

        const seg = v.path[v.segIdx];
        const e   = edges[seg.eid];

        // Velocidad reducida por densidad del segmento actual
        const density = Math.min(1, e.vehicles / JAM_DENSITY);
        const speed   = SPEED_FREE * Math.max(0.05, 1 - density * 0.92);

        // Incremento de t: speed en px/frame, longitud del segmento en px
        const dtPerPx = 1 / Math.max(1, e.length);
        v.t += speed * dtPerPx;

        // Interpolar posición
        const fromN = nodes[seg.from];
        const toN   = nodes[seg.to];
        const tc    = Math.min(1, v.t);
        v.x = lerp(fromN.x, toN.x, tc);
        v.y = lerp(fromN.y, toN.y, tc);

        // Llegó al final del segmento → avanzar al siguiente
        if (v.t >= 1) {
          v.t = 0;
          v.segIdx++;
          if (v.segIdx >= v.path.length) {
            v.done = true;
          }
        }
      }

      // Limpiar vehículos finalizados (mantener array manejable)
      if (vehicles.length > MAX_VEHICLES * 1.5) {
        this._vehicles = vehicles.filter(v => !v.done);
      }

      // Spawn según tasa
      this._frameCount++;
      const interval = Math.max(8, Math.round(SPAWN_INTERVAL_BASE / this._spawnRate));
      if (this._frameCount % interval === 0 && this._vehicles.filter(v => !v.done).length < MAX_VEHICLES) {
        this._spawnVehicle();
      }
    },

    // ---- Resize -----------------------------------------------------------
    _resize() {
      if (!this._canvas || !this._container) return;
      const dpr = window.devicePixelRatio || 1;
      const W = this._container.clientWidth  || 800;
      const H = this._container.clientHeight || 533;
      this._canvas.width  = W * dpr;
      this._canvas.height = H * dpr;
      this._ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      this._buildNetwork();
    },

    // ---- Readout ---------------------------------------------------------
    _updateReadout() {
      if (!this._readoutEl || !this._vehicles || !this._edges) return;

      const active = this._vehicles.filter(v => !v.done).length;

      // Velocidad media: promedio de (1 - density) sobre aristas con vehículos
      let sumSpeed = 0, countSeg = 0;
      for (const v of this._vehicles) {
        if (v.done || v.segIdx >= v.path.length) continue;
        const seg = v.path[v.segIdx];
        const e   = this._edges[seg.eid];
        const density = Math.min(1, e.vehicles / JAM_DENSITY);
        sumSpeed  += Math.max(0.05, 1 - density * 0.92);
        countSeg++;
      }
      const avgSpeedPct = countSeg > 0 ? Math.round((sumSpeed / countSeg) * 100) : 100;

      // % de red congestionada (densidad > 0.5)
      const jamEdges = this._edges.filter(e => edgeDensityT(e) > 0.5).length;
      const jamPct   = Math.round((jamEdges / Math.max(1, this._edges.length)) * 100);

      this._readoutEl.innerHTML =
        '<span style="color:' + C_MUTED + '">Vehículos activos: </span>' +
        '<span style="color:' + C_TEXT  + '">' + active + '</span>' +
        '<span style="color:' + C_MUTED + '"> &nbsp;|&nbsp; Velocidad media: </span>' +
        '<span style="color:' + C_FREE  + '">' + avgSpeedPct + '%</span>' +
        '<span style="color:' + C_MUTED + '"> &nbsp;|&nbsp; Red congestionada: </span>' +
        '<span style="color:' + C_JAM   + '">' + jamPct + '%</span>';
    },

    // ---- mount -----------------------------------------------------------
    mount(container) {
      this._container  = container;
      this._running    = false;
      this._spawnRate  = 1.0;
      this._vehicles   = [];
      this._frameCount = 0;

      // Canvas
      const canvas = document.createElement('canvas');
      canvas.style.cssText = 'display:block;width:100%;height:100%;';
      container.appendChild(canvas);
      this._canvas = canvas;

      const dpr = window.devicePixelRatio || 1;
      const W = container.clientWidth  || 800;
      const H = container.clientHeight || 533;
      canvas.width  = W * dpr;
      canvas.height = H * dpr;
      const ctx = canvas.getContext('2d');
      ctx.scale(dpr, dpr);
      this._ctx = ctx;

      // Construir red
      this._buildNetwork();

      // ---- Controles
      const controls = document.createElement('div');
      controls.className = 'sim-controls';

      // Play / Pause
      const btnPlay = document.createElement('button');
      btnPlay.className = 'sim-btn';
      btnPlay.textContent = '▶';
      btnPlay.title = 'Play / Pause';
      btnPlay.addEventListener('click', () => {
        this._running = !this._running;
        btnPlay.textContent = this._running ? '⏸' : '▶';
      });
      this._btnPlay = btnPlay;

      // Reset
      const btnReset = document.createElement('button');
      btnReset.className = 'sim-btn';
      btnReset.textContent = '↺';
      btnReset.title = 'Reiniciar simulación';
      btnReset.addEventListener('click', () => {
        this._running = false;
        if (this._btnPlay) this._btnPlay.textContent = '▶';
        this._buildNetwork();
        this._drawFrame();
      });

      // Slider: tasa de aparición
      const sliderLabel = document.createElement('label');
      sliderLabel.style.cssText = 'display:flex;align-items:center;gap:6px;font-size:11px;color:' + C_MUTED + ';';
      sliderLabel.textContent = 'Tasa de aparición:';

      const slider = document.createElement('input');
      slider.type = 'range';
      slider.className = 'sim-range';
      slider.min  = '0.2';
      slider.max  = '5';
      slider.step = '0.1';
      slider.value = '1';
      slider.style.cssText = 'width:90px;';

      const sliderVal = document.createElement('span');
      sliderVal.style.cssText = 'color:' + C_TEXT + ';min-width:28px;font-size:11px;';
      sliderVal.textContent = '×1.0';

      slider.addEventListener('input', () => {
        this._spawnRate = parseFloat(slider.value);
        sliderVal.textContent = '×' + this._spawnRate.toFixed(1);
      });

      sliderLabel.appendChild(slider);
      sliderLabel.appendChild(sliderVal);

      // Readout
      const readout = document.createElement('div');
      readout.className = 'sim-readout';
      readout.style.cssText = 'font-size:11px;flex:1;text-align:right;';
      this._readoutEl = readout;

      controls.appendChild(btnPlay);
      controls.appendChild(btnReset);
      controls.appendChild(sliderLabel);
      controls.appendChild(readout);
      container.appendChild(controls);

      // ---- Leyenda
      const legend = document.createElement('div');
      legend.className = 'sim-legend';
      legend.style.cssText =
        'display:flex;align-items:center;gap:10px;padding:2px 8px 4px;font-size:11px;flex-wrap:wrap;';

      function swatch(color, label) {
        return '<span style="display:inline-flex;align-items:center;gap:4px;">' +
          '<span style="display:inline-block;width:28px;height:4px;border-radius:2px;background:' +
          color + ';"></span>' +
          '<span style="color:' + C_MUTED + ';">' + label + '</span></span>';
      }
      legend.innerHTML =
        swatch(C_FREE, 'fluido') +
        swatch(C_MID,  'moderado') +
        swatch(C_JAM,  'congestionado') +
        '<span style="display:inline-flex;align-items:center;gap:4px;margin-left:6px;">' +
        '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + C_VEHICLE + ';"></span>' +
        '<span style="color:' + C_MUTED + ';">vehículo-agente</span></span>';
      container.appendChild(legend);

      // ---- ResizeObserver
      const ro = new ResizeObserver(() => {
        this._resize();
        this._drawFrame();
      });
      ro.observe(container);
      this._observer = ro;

      // ---- RAF loop
      const loop = () => {
        if (!this._canvas) return;
        if (this._running) this._step();
        this._drawFrame();
        this._updateReadout();
        this._rafId = requestAnimationFrame(loop);
      };
      this._rafId = requestAnimationFrame(loop);
    },

    _drawFrame() {
      if (!this._canvas || !this._ctx || !this._nodes) return;
      const dpr = window.devicePixelRatio || 1;
      const W = this._canvas.width  / dpr;
      const H = this._canvas.height / dpr;
      render(this._ctx, {
        nodes:    this._nodes,
        edges:    this._edges,
        vehicles: this._vehicles || []
      }, W, H);
    },

    // ---- unmount ---------------------------------------------------------
    unmount() {
      if (this._rafId !== null) {
        cancelAnimationFrame(this._rafId);
        this._rafId = null;
      }
      if (this._observer) {
        this._observer.disconnect();
        this._observer = null;
      }
      if (this._container) {
        this._container.innerHTML = '';
        this._container = null;
      }
      this._canvas    = null;
      this._ctx       = null;
      this._nodes     = null;
      this._edges     = null;
      this._adj       = null;
      this._vehicles  = null;
      this._readoutEl = null;
      this._btnPlay   = null;
      this._running   = false;
      this._frameCount = 0;
    }
  };

  window.PonenciaSims = window.PonenciaSims || {};
  window.PonenciaSims['agent-traffic'] = SIM;
})();
