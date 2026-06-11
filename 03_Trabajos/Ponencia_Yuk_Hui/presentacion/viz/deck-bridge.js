/* ════════════════════════════════════════════════════════════════════════
   deck-bridge.js — Puente entre reveal.js y window.VIZ / window.AMBIENT
   ────────────────────────────────────────────────────────────────────────
   Monta las visualizaciones vivas SOLO cuando su slide es visible y nunca
   más de un slide montado a la vez. Gestiona cinco escenarios:

     1) Contenedores in-slide  (data-viz="<id>")  — galería 2×2, portada.
     2) Chips clicables         (data-viz-chip="<id>") en la slide de teorías,
        que abren un overlay propio a pantalla completa.
     3) Fondo vivo de portada    (data-viz-bg="<id>") a baja opacidad,
        estático bajo prefers-reduced-motion.
     4) Ambiente de slide        (data-ambient="<variante>" data-ambient-opts='{json}')
        en cualquier <section> — monta el ambiente como capa de fondo
        absoluta (z-index:0, pointer-events:none) cuando la slide se activa
        y lo destruye al salir. Una slide puede tener ambiente Y viz a la vez.

   Contrato de window.VIZ[id]:
     mount(container, {compact}) -> { pause, resume, destroy }
   Contrato de window.AMBIENT:
     mount(container, {variante, ...params}) -> { pause, resume, destroy }
   Los módulos gestionan DPR, rAF y auto-pausa. Este puente solo decide
   CUÁNDO viven.
   ════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var VIZ     = window.VIZ     || (window.VIZ     = {});
  var AMBIENT = window.AMBIENT || null;  /* se rellena cuando ambient.js cargue */

  var prefersReduced = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* instancias VIZ montadas por contenedor */
  var mounted = [];
  /* instancias AMBIENT montadas (máx 1 por slide) */
  var mountedAmbient = [];

  /* ── Nitidez bajo el escalado de reveal.js ───────────────────────────────
     reveal escala .slides con un transform CSS (p. ej. ×1.48). Los módulos
     dimensionan su backing-store leyendo el tamaño CSS del contenedor por
     clientWidth (tamaño de LAYOUT, sin el escalado) × devicePixelRatio. Bajo
     reveal eso deja el canvas a menor resolución que sus píxeles realmente
     pintados → se ve borroso. Compensamos elevando el devicePixelRatio
     efectivo por la escala de reveal de modo que backing-store = píxeles
     mostrados. El override se mantiene MIENTRAS el slide vive (no solo durante
     el mount): algunos módulos releen window.devicePixelRatio en cada frame
     (p. ej. DLA, para centrar el cluster) y necesitan ver el mismo valor con
     el que se dimensionó el canvas. Como solo hay un slide montado a la vez,
     no compite con ningún otro dibujo. Se restaura al desmontar. ─────────── */
  var dprOverridden = false;
  var dprOriginalDescriptor = null;

  function applyScaledDPR() {
    if (dprOverridden) return;
    var scale = (window.Reveal && Reveal.getScale) ? (Reveal.getScale() || 1) : 1;
    if (scale <= 1.01) return;
    dprOriginalDescriptor = Object.getOwnPropertyDescriptor(window, 'devicePixelRatio');
    var base = (dprOriginalDescriptor && typeof dprOriginalDescriptor.get === 'function')
      ? dprOriginalDescriptor.get.call(window) : (window.devicePixelRatio || 1);
    Object.defineProperty(window, 'devicePixelRatio', {
      configurable: true, get: function () { return base * scale; }
    });
    dprOverridden = true;
  }

  function restoreDPR() {
    if (!dprOverridden) return;
    if (dprOriginalDescriptor) {
      Object.defineProperty(window, 'devicePixelRatio', dprOriginalDescriptor);
    } else {
      delete window.devicePixelRatio;
    }
    dprOverridden = false;
    dprOriginalDescriptor = null;
  }

  /* ── Montaje / desmontaje de un contenedor concreto ─────────────────── */
  function mountInto(el) {
    var id = el.getAttribute('data-viz');
    if (!id || !VIZ[id] || typeof VIZ[id].mount !== 'function') return;
    if (el.__vizMounted) return;
    try {
      applyScaledDPR();
      var api = VIZ[id].mount(el, { compact: true });
      el.__vizMounted = true;
      mounted.push({ el: el, id: id, api: api });
    } catch (err) {
      console.error('[deck-bridge] mount falló para "' + id + '":', err);
    }
  }

  function destroyAll() {
    while (mounted.length) {
      var inst = mounted.pop();
      try { if (inst.api && inst.api.destroy) inst.api.destroy(); } catch (e) {}
      inst.el.__vizMounted = false;
      /* deja el contenedor limpio por si el módulo no lo hizo */
      if (inst.el.firstChild) inst.el.innerHTML = '';
    }
    destroyAllAmbient();
    restoreDPR();
  }

  function destroyAllAmbient() {
    while (mountedAmbient.length) {
      var ai = mountedAmbient.pop();
      try { if (ai.api && ai.api.destroy) ai.api.destroy(); } catch (e) {}
      /* El contenedor envolvente fue creado por nosotros — lo eliminamos */
      if (ai.wrapper && ai.wrapper.parentElement) ai.wrapper.parentElement.removeChild(ai.wrapper);
    }
  }

  function pauseAll() {
    mounted.forEach(function (i) {
      try { if (i.api && i.api.pause) i.api.pause(); } catch (e) {}
    });
    mountedAmbient.forEach(function (i) {
      try { if (i.api && i.api.pause) i.api.pause(); } catch (e) {}
    });
  }
  function resumeAll() {
    mounted.forEach(function (i) {
      try { if (i.api && i.api.resume) i.api.resume(); } catch (e) {}
    });
    mountedAmbient.forEach(function (i) {
      try { if (i.api && i.api.resume) i.api.resume(); } catch (e) {}
    });
  }

  /* ── Montaje de ambiente de slide ─────────────────────────────────── */
  function mountAmbientForSlide(slide) {
    /* Leer ambient del <section> directo */
    var variante = slide.getAttribute('data-ambient');
    if (!variante) return;

    /* ambient.js podría cargar después del bridge; releer en el momento */
    var amb = window.AMBIENT;
    if (!amb || typeof amb.mount !== 'function') return;

    /* Parsear opciones */
    var opts = {};
    var optsRaw = slide.getAttribute('data-ambient-opts');
    if (optsRaw) {
      try { opts = JSON.parse(optsRaw); } catch (e) {}
    }
    opts.variante = variante;
    opts.compact  = true;  /* dentro del deck siempre compact */

    /* Crear wrapper de fondo */
    var wrapper = document.createElement('div');
    wrapper.style.cssText = 'position:absolute;inset:0;z-index:0;pointer-events:none;overflow:hidden;';
    wrapper.setAttribute('aria-hidden', 'true');
    wrapper.setAttribute('data-ambient-wrapper', variante);

    /* Insertar como primer hijo para que quede detrás del contenido */
    if (slide.firstChild) {
      slide.insertBefore(wrapper, slide.firstChild);
    } else {
      slide.appendChild(wrapper);
    }

    /* Asegurar que el contenido de la slide quede en z-index 1 */
    var children = slide.children;
    for (var ci = 0; ci < children.length; ci++) {
      var ch = children[ci];
      if (ch !== wrapper && ch.style.position === '') {
        ch.style.position = 'relative';
        ch.style.zIndex   = '1';
      }
    }

    try {
      var api = amb.mount(wrapper, opts);
      mountedAmbient.push({ api: api, wrapper: wrapper });
    } catch (err) {
      console.error('[deck-bridge] ambient mount falló para "' + variante + '":', err);
      if (wrapper.parentElement) wrapper.parentElement.removeChild(wrapper);
    }
  }

  /* ── Sincroniza el slide actual: monta sus viz, destruye las demás ───── */
  var currentSlide = null;
  function syncSlide(slide) {
    if (!slide) return;
    if (slide === currentSlide) { resumeAll(); return; }

    /* Cambió de slide: destruir todo lo anterior (nunca >1 slide montado) */
    destroyAll();
    currentSlide = slide;

    var hosts = slide.querySelectorAll('[data-viz]');
    for (var i = 0; i < hosts.length; i++) mountInto(hosts[i]);

    /* Montar ambiente si la slide lo declara */
    mountAmbientForSlide(slide);
  }

  /* ════════════════════════════════════════════════════════════════════
     OVERLAY a pantalla completa para los chips de teorías
  ════════════════════════════════════════════════════════════════════ */
  var overlay, overlayBody, overlayTitle, overlayInst = null;

  function buildOverlay() {
    overlay = document.createElement('div');
    overlay.className = 'viz-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'Visualización a pantalla completa');

    var head = document.createElement('div');
    head.className = 'viz-overlay-head';

    overlayTitle = document.createElement('span');
    overlayTitle.className = 'viz-overlay-title';

    var closeBtn = document.createElement('button');
    closeBtn.className = 'viz-overlay-close';
    closeBtn.setAttribute('aria-label', 'Cerrar (Esc)');
    closeBtn.innerHTML = '✕';
    closeBtn.addEventListener('click', closeOverlay);

    head.appendChild(overlayTitle);
    head.appendChild(closeBtn);

    overlayBody = document.createElement('div');
    overlayBody.className = 'viz-overlay-body';

    overlay.appendChild(head);
    overlay.appendChild(overlayBody);
    document.body.appendChild(overlay);

    /* Click en el fondo (no en la viz ni la cabecera) cierra */
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeOverlay();
    });
  }

  function openOverlay(id) {
    if (!VIZ[id] || typeof VIZ[id].mount !== 'function') return;
    if (!overlay) buildOverlay();
    closeOverlay(); /* por si quedara una abierta */

    overlayTitle.textContent = VIZ[id].titulo || id;
    overlay.classList.add('active');

    /* Pausa lo que esté vivo en el slide para no competir por CPU */
    pauseAll();

    /* El overlay vive a nivel de body: NO está bajo el transform de reveal,
       así que debe montarse con el devicePixelRatio real (sin el boost). */
    var wasBoosted = dprOverridden;
    restoreDPR();
    try {
      var api = VIZ[id].mount(overlayBody, { compact: false });
      overlayInst = { id: id, api: api, reboost: wasBoosted };
    } catch (err) {
      console.error('[deck-bridge] overlay mount falló para "' + id + '":', err);
    }
  }

  function closeOverlay() {
    var reboost = overlayInst && overlayInst.reboost;
    if (overlayInst) {
      try { if (overlayInst.api && overlayInst.api.destroy) overlayInst.api.destroy(); } catch (e) {}
      overlayInst = null;
    }
    if (overlayBody) overlayBody.innerHTML = '';
    if (overlay) overlay.classList.remove('active');
    /* Restaura el boost para que el slide vivo siga nítido al reanudarse */
    if (reboost) applyScaledDPR();
    resumeAll(); /* devuelve la vida al slide */
  }

  /* ── Chips clicables (delegación de eventos en document) ─────────────── */
  function wireChips() {
    document.addEventListener('click', function (e) {
      var chip = e.target.closest ? e.target.closest('[data-viz-chip]') : null;
      if (!chip) return;
      openOverlay(chip.getAttribute('data-viz-chip'));
    });
  }

  /* Escape cierra el overlay (sin chocar con la navegación de reveal) */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && overlay && overlay.classList.contains('active')) {
      e.stopPropagation();
      closeOverlay();
    }
  }, true);

  /* ════════════════════════════════════════════════════════════════════
     Enganche con reveal.js
  ════════════════════════════════════════════════════════════════════ */
  function init() {
    if (!window.Reveal) return;
    wireChips();

    function handle() {
      var slide = Reveal.getCurrentSlide && Reveal.getCurrentSlide();
      syncSlide(slide);
    }

    if (Reveal.isReady && Reveal.isReady()) {
      handle();
    } else {
      Reveal.on('ready', handle);
    }
    Reveal.on('slidechanged', handle);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
