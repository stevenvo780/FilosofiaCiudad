/* Motor de la ponencia: inicializa reveal.js y gestiona el ciclo de vida
   de las simulaciones de computo urbano segun el atributo data-sim. */

let mounted = null;   // { name, sim, stage }

function mountSimFor(slide) {
  if (!slide) return;
  const name = slide.getAttribute('data-sim');
  // Desmontar la anterior si cambia de diapositiva
  if (mounted && (!name || mounted.name !== name)) {
    try { mounted.sim.unmount(); } catch (e) { /* noop */ }
    if (mounted.stage) mounted.stage.innerHTML = '';
    mounted = null;
  }
  if (!name) return;
  if (mounted && mounted.name === name) return; // ya montada
  const registry = window.PonenciaSims || {};
  const sim = registry[name];
  const stage = slide.querySelector('.sim-stage');
  if (!sim || !stage) {
    if (stage) stage.innerHTML =
      '<div class="sim-missing">[modelo "' + name + '" no disponible]</div>';
    return;
  }
  stage.innerHTML = '';
  // Garantizar una altura util aunque el tema no la fije
  if (stage.clientHeight < 80) stage.style.minHeight = '60vh';
  try {
    sim.mount(stage);
    mounted = { name, sim, stage };
  } catch (e) {
    stage.innerHTML = '<div class="sim-missing">[error montando "' + name + '"]</div>';
    console.error('Sim mount error:', name, e);
  }
}

function initDeck() {
  const deck = new Reveal({
    hash: true,
    slideNumber: 'c/t',
    progress: true,
    controls: true,
    controlsTutorial: false,
    transition: 'slide',
    transitionSpeed: 'default',
    backgroundTransition: 'fade',
    width: 1280,
    height: 800,
    margin: 0.06,
    minScale: 0.2,
    maxScale: 1.6,
  });
  deck.initialize().then(() => {
    mountSimFor(deck.getCurrentSlide());
    deck.on('slidechanged', (event) => mountSimFor(event.currentSlide));
  });
  window._deck = deck;
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDeck);
} else {
  initDeck();
}
