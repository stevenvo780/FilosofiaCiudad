(function () {
  /* -----------------------------------------------------------------------
   * SINTAXIS ESPACIAL — Centralidad de red de calles
   * ~50 nodos (intersecciones) en layout 2D irregular de ciudad.
   * Calcula BETWEENNESS (intermediación) o DEGREE (grado) sobre aristas.
   * Betweenness: BFS desde cada nodo → cuenta paso por aristas → calor.
   * Colorea calles con rampa fría (#8a93a3) → cálida (#2dd4bf / #e0524a).
   * El cálculo acumula de a 2 fuentes por frame cuando está en "play",
   * haciendo visible el proceso iterativo.
   * Demuestra: teoría de grafos como objeto epistemico del urbanismo, sin IA.
   * --------------------------------------------------------------------- */

  // ---- Paleta (SPEC.md) --------------------------------------------------
  const C_BG      = '#0d1117';
  const C_GRID    = '#222b3a';
  const C_PANEL   = '#161b26';
  const C_TEXT    = '#e8e6df';
  const C_MUTED   = '#8a93a3';
  const C_COLD    = '#8a93a3';   // low centrality
  const C_MID     = '#2dd4bf';   // transit/cian — medium
  const C_HOT     = '#e0524a';   // CBD/rojo — high centrality
  const C_NODE    = '#cdd6e3';   // vía/calle
  const C_NODE_HI = '#e0524a';
  const C_ACCENT  = '#a78bfa';

  // ---- Graph generation --------------------------------------------------
  const N_NODES = 52;
  const MARGIN  = 0.06;   // fraction of canvas

  function lerp(a, b, t) { return a + (b - a) * t; }

  // Interpolate a 3-stop colour ramp [cold → mid → hot] for t in [0,1]
  function rampColor(t) {
    function hexToRgb(h) {
      const v = parseInt(h.slice(1), 16);
      return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
    }
    function rgbToHex(r, g, b) {
      return '#' + [r, g, b].map(x => Math.round(x).toString(16).padStart(2, '0')).join('');
    }
    const cold = hexToRgb(C_COLD);
    const mid  = hexToRgb(C_MID);
    const hot  = hexToRgb(C_HOT);
    let r, g, b;
    if (t < 0.5) {
      const s = t / 0.5;
      r = lerp(cold[0], mid[0], s);
      g = lerp(cold[1], mid[1], s);
      b = lerp(cold[2], mid[2], s);
    } else {
      const s = (t - 0.5) / 0.5;
      r = lerp(mid[0], hot[0], s);
      g = lerp(mid[1], hot[1], s);
      b = lerp(mid[2], hot[2], s);
    }
    return rgbToHex(r, g, b);
  }

  // Generate nodes: blend of grid-ish + organic noise to mimic street layout
  function generateNodes(W, H) {
    const mx = W * MARGIN;
    const my = H * MARGIN;
    const uw = W - 2 * mx;
    const uh = H - 2 * my;

    const nodes = [];
    // Lay out on a rough 8×7 grid with jitter
    const cols = 8, rows = 7;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (nodes.length >= N_NODES) break;
        // skip ~15% to create irregular blocks
        if (Math.random() < 0.15) continue;
        const bx = mx + (c / (cols - 1)) * uw;
        const by = my + (r / (rows - 1)) * uh;
        const jx = (Math.random() - 0.5) * (uw / cols) * 0.55;
        const jy = (Math.random() - 0.5) * (uh / rows) * 0.55;
        nodes.push({ x: bx + jx, y: by + jy, id: nodes.length });
      }
    }
    // Fill up to N_NODES if grid skipped too many
    while (nodes.length < N_NODES) {
      nodes.push({
        x: mx + Math.random() * uw,
        y: my + Math.random() * uh,
        id: nodes.length
      });
    }
    return nodes;
  }

  // Euclidean distance
  function dist(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  // Build edges: connect each node to its K nearest (no crossings check —
  // simpler and still looks like a plausible street net).
  function generateEdges(nodes, W, H) {
    const K = 3;                        // min connections per node
    const D_MAX = Math.min(W, H) * 0.30; // max edge length
    const edgeSet = new Set();
    const edges = [];

    function addEdge(i, j) {
      const key = i < j ? i + '_' + j : j + '_' + i;
      if (edgeSet.has(key)) return;
      edgeSet.add(key);
      const w = dist(nodes[i], nodes[j]);
      edges.push({ a: i, b: j, weight: w, id: edges.length });
    }

    // For each node, connect to K nearest within D_MAX
    for (let i = 0; i < nodes.length; i++) {
      const dists = [];
      for (let j = 0; j < nodes.length; j++) {
        if (i === j) continue;
        const d = dist(nodes[i], nodes[j]);
        if (d <= D_MAX) dists.push({ j, d });
      }
      dists.sort((a, b) => a.d - b.d);
      const take = Math.max(K, 2);
      for (let k = 0; k < Math.min(take, dists.length); k++) {
        addEdge(i, dists[k].j);
      }
    }
    return edges;
  }

  // Build adjacency list for BFS/Dijkstra
  function buildAdj(nodes, edges) {
    const adj = nodes.map(() => []);
    for (const e of edges) {
      adj[e.a].push({ to: e.b, w: e.weight, eid: e.id });
      adj[e.b].push({ to: e.a, w: e.weight, eid: e.id });
    }
    return adj;
  }

  // BFS shortest path (unweighted hops) from source → returns prev-edge array
  // Used when metric = betweenness (treat all edges equal for simplicity;
  // gives a clear readable result at presentation scale).
  function bfsFrom(src, adj, n) {
    const dist  = new Int32Array(n).fill(-1);
    const prevE = new Int32Array(n).fill(-1);
    dist[src] = 0;
    const queue = [src];
    let head = 0;
    while (head < queue.length) {
      const u = queue[head++];
      for (const { to, eid } of adj[u]) {
        if (dist[to] === -1) {
          dist[to] = dist[u] + 1;
          prevE[to] = eid;
          queue.push(to);
        }
      }
    }
    return { dist, prevE };
  }

  // Accumulate betweenness counts on edges by backtracking all paths from src
  function accumulateBetweennessFrom(src, adj, n, edgeCounts) {
    const { dist, prevE } = bfsFrom(src, adj, n);
    for (let t = 0; t < n; t++) {
      if (t === src || prevE[t] === -1) continue;
      // Walk back the path
      let cur = t;
      while (cur !== src) {
        const eid = prevE[cur];
        edgeCounts[eid]++;
        // find which end leads back
        // we need to traverse back through prevE
        // prevE[cur] is the edge that reached cur — find the other endpoint
        // We'll re-derive it from BFS dist: the predecessor has dist = dist[cur]-1
        // Scan adj[cur] for the node with dist[that] = dist[cur]-1 and edge eid
        let found = false;
        for (const nb of adj[cur]) {
          if (nb.eid === eid && dist[nb.to] === dist[cur] - 1) {
            cur = nb.to;
            found = true;
            break;
          }
        }
        if (!found) break;
      }
    }
  }

  // Degree centrality per edge = avg degree of its two endpoints
  function computeDegreeCentrality(nodes, edges, adj) {
    const deg = adj.map(a => a.length);
    const scores = new Float64Array(edges.length);
    for (let i = 0; i < edges.length; i++) {
      scores[i] = (deg[edges[i].a] + deg[edges[i].b]) / 2;
    }
    return scores;
  }

  // ---- Rendering ---------------------------------------------------------
  function render(ctx, state, W, H) {
    ctx.fillStyle = C_BG;
    ctx.fillRect(0, 0, W, H);

    const { nodes, edges, edgeScores, maxScore, highlightSrc, metric } = state;

    // Draw edges
    for (let i = 0; i < edges.length; i++) {
      const e = edges[i];
      const na = nodes[e.a], nb = nodes[e.b];
      const sc = maxScore > 0 ? edgeScores[i] / maxScore : 0;
      const color = rampColor(sc);
      // Thickness 1→5 with centrality
      const thick = 1 + sc * 4;

      ctx.beginPath();
      ctx.moveTo(na.x, na.y);
      ctx.lineTo(nb.x, nb.y);
      ctx.strokeStyle = color;
      ctx.lineWidth = thick;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Label structurally-integrating edges (top 10%)
      if (sc > 0.90 && maxScore > 0) {
        const mx = (na.x + nb.x) / 2;
        const my = (na.y + nb.y) / 2;
        ctx.fillStyle = C_HOT;
        ctx.font = "bold 10px 'Inter', system-ui, sans-serif";
        ctx.fillText('★', mx - 5, my + 4);
      }
    }

    // Draw nodes
    const NODE_R = 4;
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      const isActive = (i === highlightSrc);
      ctx.beginPath();
      ctx.arc(n.x, n.y, isActive ? NODE_R + 2 : NODE_R, 0, Math.PI * 2);
      ctx.fillStyle = isActive ? C_ACCENT : C_NODE;
      ctx.fill();
      if (isActive) {
        ctx.strokeStyle = C_BG;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    }

    // BFS wavefront indicator (active source pulse ring)
    if (highlightSrc >= 0 && state.running) {
      const n = nodes[highlightSrc];
      const pulse = (Date.now() % 800) / 800;
      ctx.beginPath();
      ctx.arc(n.x, n.y, NODE_R + 4 + pulse * 14, 0, Math.PI * 2);
      ctx.strokeStyle = C_ACCENT + '88';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }

  // ---- Normalise scores into [0,1] display array ------------------------
  function normaliseScores(raw) {
    let max = 0;
    for (let i = 0; i < raw.length; i++) if (raw[i] > max) max = raw[i];
    return { edgeScores: raw, maxScore: max };
  }

  // ---- Find best edge (highest score) -----------------------------------
  function bestEdge(edges, edgeScores, maxScore) {
    let best = -1, bestV = -1;
    for (let i = 0; i < edgeScores.length; i++) {
      if (edgeScores[i] > bestV) { bestV = edgeScores[i]; best = i; }
    }
    return best;
  }

  // ---- SIM object --------------------------------------------------------
  const SIM = {
    title: 'Sintaxis Espacial',

    // State
    _container:   null,
    _canvas:      null,
    _ctx:         null,
    _observer:    null,
    _rafId:       null,
    _running:     false,

    // Graph
    _nodes:       null,
    _edges:       null,
    _adj:         null,

    // Computation
    _metric:      'betweenness',  // 'betweenness' | 'degree'
    _edgeCounts:  null,           // accumulation array (betweenness)
    _srcIdx:      0,              // next BFS source to process
    _done:        false,

    // Display
    _edgeScores:  null,
    _maxScore:    0,
    _highlightSrc: -1,

    // UI refs
    _readoutEl:   null,
    _btnPlay:     null,
    _btnMetric:   null,

    // ---- Build / reset graph -------------------------------------------
    _buildGraph(W, H) {
      this._nodes     = generateNodes(W, H);
      this._edges     = generateEdges(this._nodes, W, H);
      this._adj       = buildAdj(this._nodes, this._edges);
      this._edgeCounts = new Float64Array(this._edges.length);
      this._srcIdx    = 0;
      this._done      = false;
      this._highlightSrc = -1;
      // Initial display: cold everywhere
      this._edgeScores = new Float64Array(this._edges.length);
      this._maxScore   = 0;
      // If degree mode, compute immediately (instant)
      if (this._metric === 'degree') {
        this._computeDegreeInstant();
      }
    },

    _computeDegreeInstant() {
      const scores = computeDegreeCentrality(this._nodes, this._edges, this._adj);
      const { edgeScores, maxScore } = normaliseScores(scores);
      this._edgeScores = edgeScores;
      this._maxScore   = maxScore;
      this._done       = true;
      this._highlightSrc = -1;
    },

    // Process BATCH_SIZE BFS sources per animation frame (betweenness)
    _stepBetweenness(batchSize) {
      if (this._done) return;
      const n = this._nodes.length;
      for (let k = 0; k < batchSize; k++) {
        if (this._srcIdx >= n) {
          this._done = true;
          this._highlightSrc = -1;
          break;
        }
        accumulateBetweennessFrom(this._srcIdx, this._adj, n, this._edgeCounts);
        this._highlightSrc = this._srcIdx;
        this._srcIdx++;
      }
      const { edgeScores, maxScore } = normaliseScores(this._edgeCounts);
      this._edgeScores = edgeScores;
      this._maxScore   = maxScore;
    },

    // ---- Canvas resize --------------------------------------------------
    _resize() {
      if (!this._canvas || !this._container) return;
      const dpr = window.devicePixelRatio || 1;
      const W = this._container.clientWidth  || 800;
      const H = this._container.clientHeight || 533;
      this._canvas.width  = W * dpr;
      this._canvas.height = H * dpr;
      const ctx = this._ctx;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      // Rebuild graph at new size
      this._buildGraph(W, H);
    },

    // ---- Readout --------------------------------------------------------
    _updateReadout() {
      if (!this._readoutEl) return;
      const { _edges: edges, _nodes: nodes, _edgeScores: sc, _maxScore: mx,
              _srcIdx: si, _nodes: ns, _done: done, _metric: metric } = this;
      if (!edges || !sc) return;
      const n = ns ? ns.length : 0;
      const prog = (metric === 'degree' || done)
        ? '100'
        : Math.round((si / n) * 100);

      let bestLabel = '—';
      if (mx > 0) {
        const bi = bestEdge(edges, sc, mx);
        if (bi >= 0) {
          const ea = edges[bi].a + 1, eb = edges[bi].b + 1;
          bestLabel = 'N' + ea + '–N' + eb;
        }
      }

      const metricName = metric === 'betweenness' ? 'Intermediación' : 'Grado';
      this._readoutEl.innerHTML =
        '<span style="color:' + C_MUTED + '">Métrica: </span>' +
        '<span style="color:' + C_TEXT  + '">' + metricName + '</span>' +
        '<span style="color:' + C_MUTED + '"> &nbsp;|&nbsp; Progreso: </span>' +
        '<span style="color:' + C_MID   + '">' + prog + '%</span>' +
        '<span style="color:' + C_MUTED + '"> &nbsp;|&nbsp; Calle más central: </span>' +
        '<span style="color:' + C_HOT   + '">' + bestLabel + '</span>';
    },

    // ---- mount ---------------------------------------------------------
    mount(container) {
      this._container  = container;
      this._running    = false;
      this._metric     = 'betweenness';
      this._done       = false;
      this._srcIdx     = 0;
      this._highlightSrc = -1;

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

      // Build initial graph
      this._buildGraph(W, H);

      // Controls
      const controls = document.createElement('div');
      controls.className = 'sim-controls';

      // Play/Pause
      const btnPlay = document.createElement('button');
      btnPlay.className = 'sim-btn';
      btnPlay.textContent = '⏸';
      btnPlay.title = 'Play / Pause cálculo';
      btnPlay.addEventListener('click', () => {
        if (this._done && this._metric === 'betweenness') return; // already done
        this._running = !this._running;
        btnPlay.textContent = this._running ? '⏸' : '▶';
      });
      this._btnPlay = btnPlay;
      this._running = true; // auto-arranque del cálculo al entrar a la diapositiva

      // Reset / regenerar
      const btnReset = document.createElement('button');
      btnReset.className = 'sim-btn';
      btnReset.textContent = '↺';
      btnReset.title = 'Regenerar red';
      btnReset.addEventListener('click', () => {
        this._running = false;
        btnPlay.textContent = '▶';
        const dpr2 = window.devicePixelRatio || 1;
        const W2 = this._canvas.width  / dpr2;
        const H2 = this._canvas.height / dpr2;
        this._buildGraph(W2, H2);
        this._drawFrame();
      });

      // Toggle metric
      const btnMetric = document.createElement('button');
      btnMetric.className = 'sim-btn';
      btnMetric.textContent = 'Métrica: Intermediación';
      btnMetric.title = 'Alternar métrica';
      btnMetric.style.cssText = 'min-width:190px;font-size:11px;';
      btnMetric.addEventListener('click', () => {
        this._metric = this._metric === 'betweenness' ? 'degree' : 'betweenness';
        btnMetric.textContent = 'Métrica: ' +
          (this._metric === 'betweenness' ? 'Intermediación' : 'Grado');
        this._running = false;
        btnPlay.textContent = '▶';
        const dpr2 = window.devicePixelRatio || 1;
        const W2 = this._canvas.width  / dpr2;
        const H2 = this._canvas.height / dpr2;
        this._buildGraph(W2, H2);
        this._drawFrame();
      });
      this._btnMetric = btnMetric;

      // Readout
      const readout = document.createElement('div');
      readout.className = 'sim-readout';
      readout.style.cssText = 'font-size:11px;flex:1;text-align:right;';
      this._readoutEl = readout;

      controls.appendChild(btnPlay);
      controls.appendChild(btnReset);
      controls.appendChild(btnMetric);
      controls.appendChild(readout);
      container.appendChild(controls);

      // Legend
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
        swatch(C_COLD, 'baja centralidad') +
        swatch(C_MID,  'media') +
        swatch(C_HOT,  'alta / integradora') +
        '<span style="color:' + C_HOT + ';margin-left:6px;">★</span>' +
        '<span style="color:' + C_MUTED + ';">top 10% estructural</span>' +
        '<span style="color:' + C_ACCENT + ';margin-left:8px;">●</span>' +
        '<span style="color:' + C_MUTED + ';">fuente BFS activa</span>';
      container.appendChild(legend);

      // ResizeObserver
      const ro = new ResizeObserver(() => {
        this._resize();
        this._drawFrame();
      });
      ro.observe(container);
      this._observer = ro;

      // RAF loop
      let lastTs = 0;
      const BATCH_INTERVAL = 40; // ms between betweenness batches
      const BATCH_SIZE = 2;      // sources per batch
      const loop = (ts) => {
        if (!this._canvas) return;
        if (this._running && this._metric === 'betweenness' && !this._done) {
          if (ts - lastTs >= BATCH_INTERVAL) {
            this._stepBetweenness(BATCH_SIZE);
            lastTs = ts;
            if (this._done && this._btnPlay) {
              this._btnPlay.textContent = '▶';
              this._running = false;
            }
          }
        }
        this._drawFrame();
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
        nodes:        this._nodes,
        edges:        this._edges,
        edgeScores:   this._edgeScores,
        maxScore:     this._maxScore,
        highlightSrc: this._running ? this._highlightSrc : -1,
        running:      this._running,
        metric:       this._metric
      }, W, H);
      this._updateReadout();
    },

    // ---- unmount -------------------------------------------------------
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
      this._canvas      = null;
      this._ctx         = null;
      this._nodes       = null;
      this._edges       = null;
      this._adj         = null;
      this._edgeCounts  = null;
      this._edgeScores  = null;
      this._readoutEl   = null;
      this._btnPlay     = null;
      this._btnMetric   = null;
      this._running     = false;
      this._done        = false;
    }
  };

  window.PonenciaSims = window.PonenciaSims || {};
  window.PonenciaSims['space-syntax'] = SIM;
})();
