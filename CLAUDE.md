# CLAUDE.md — Proyecto Ponencia Yuk Hui / Banco Epistémico Urbano

Contexto para sesiones de Claude Code en este repositorio. Complementa `AGENTS.md`
(convenciones del curso) y la carpeta `.claude/` (dossier operativo para continuar
el trabajo en la workstation kratos).

## Qué es esto

Repositorio del curso **Filosofía de la ciudad: ontología, poder y política**.
Entre el 10 y 11 de junio de 2026 se construyó aquí, orquestando ~340 subagentes
en 10 workflows, el proyecto completo de la ponencia del 12 de junio sobre
Yuk Hui, *"Sobre el límite de la inteligencia artificial"* (Fragmentar el futuro,
pp. 163-191), que creció hasta ser una tesis con aparato experimental propio.

## Entregables y mapa

| Ruta | Qué es |
|---|---|
| `03_Trabajos/Ponencia_Yuk_Hui/presentacion/index.html` | Deck reveal.js: 19 slides (14 núcleo = 20:00 exactos + 4 anexos + costos), 8 visualizaciones vivas en canvas, capa ambiental animada en TODAS las slides, galería interactiva, chips→overlay, botón global a la tesis, QR a móvil |
| `presentacion/m/index.html` | Versión móvil scrollytelling táctil (otra óptica, no slides encogidas) |
| `presentacion/tesis/index.html` | Render HTML navegable de la tesis (regenerar con `tesis/generar_html.py`) |
| `presentacion/viz/*.js` | 8 módulos de visualización (`window.VIZ`, contrato `mount(el,{compact})→{pause,resume,destroy}`) + `ambient.js` (6 variantes) + `deck-bridge.js` (monta solo el slide activo) |
| `03_Trabajos/Ponencia_Yuk_Hui/tesis/*.md` | Tesis "Una epistemología de la urbanidad" — 12 capítulos, ~35k palabras |
| `simulaciones/` | 13 teorías urbanas clásicas implementadas, validadas y auditadas contra el canon; `banco_preguntas.json` (39 preguntas con respuesta exacta) |
| `experimento/` | Dos experimentos LLM vs cómputo + costos medidos. **Los JSON de aquí son la única fuente de verdad numérica** |
| `04_libreto.md` / `05_guia_exposicion.md` | Guion hablado de 20:00 (2.591 palabras) y hoja de enunciados para leer en clase |
| `02_Lecturas_Base/Yuk_Hui/` | El libro (PDF + OCR) y `capitulo_limite_ia_extracto.md` (texto primario del capítulo) |

**Producción:** https://ponencia-yuk-hui-critertec-a963d21e.vercel.app
(deck `/`, móvil `/m/`, tesis `/tesis/`, demo viz `/viz/demo.html`).
Redesplegar: `cd presentacion && vercel deploy --prod --yes --scope critertec-a963d21e`.

## Resultados científicos centrales (citables, todos en los JSON)

- **Exp. 1** (6 tareas exactas, 2 intentos): Python 100% trivial; Sonnet 90%, Opus 70%;
  locales en kratos 20/20/40/20% (3B/14B/20B/32B) — **curva no monótona**: el 20B
  supera al 32B; la escala no compra fiabilidad aritmética. T6 (juicio de relevancia
  en escena urbana) = NO_COMPUTABLE para Python: límite especular.
- **Exp. 2** (39 preguntas de las 13 teorías, 1 intento): 3B 38,5% · 14B 76,9% ·
  20B 79,5% · 32B 76,9% · Sonnet 89,7% · Opus 92,3%. Forma cerrada vs emergente:
  Opus 100%/75%, 3B 0% emergente — la IA recita la teoría, no sustituye al cómputo
  que la ejecuta.
- **Costos por respuesta correcta**: Python $6,9×10⁻⁶ (tiempo medido, energía estimada
  25 W declarados) · locales $0,000147–0,0018 (tiempo medido, GPU 281,5 W medida) ·
  Sonnet $0,007–0,041 · Opus $0,013–0,070 (estimados por banda de tokens, precios
  oficiales jun-2026: Sonnet $3/$15, Opus $5/$25 por MTok). **Cuatro órdenes de
  magnitud** (log₁₀ = 3,97).

## Decisiones tomadas (y su porqué)

1. **Orquestación por workflows con jerarquía de modelos** (regla del usuario):
   el modelo principal solo orquesta; Sonnet ejecuta lo mecánico; Opus diseña,
   redacta lo crítico, audita y corrige. Las síntesis finales son siempre Opus.
2. **Honestidad numérica como regla dura**: todo número visible debe existir en un
   JSON canónico; lo estimado se declara estimado y se muestra como rango; los
   timeouts cuentan como fallo con asterisco; los aciertos de la IA se reportan
   aunque debiliten la hipótesis (terminaron fortaleciéndola: el giro "lo que de
   verdad ocurrió").
3. **Verificación por capas**: implementador → verificador independiente →
   auditoría Opus contra el canon publicado → cotejo final contra el TEXTO PRIMARIO.
   Cada capa encontró errores reales que la anterior no vio.
4. **Las animaciones sirven al contenido**: re-simulación ilustrativa en JS, pero
   los números de los paneles salen del JSON canónico, nunca del re-cómputo del
   navegador. Un solo slide montado a la vez (perf). `prefers-reduced-motion`
   congela todo.
5. **Atribución filosófica estricta**: lo que es de Hui, citado del capítulo; lo
   que es del ponente, marcado "marco del presentador" / "según mi lectura". La
   dicotomía gobernar/gestionar y la extensión smart-city son del ponente; el
   caso desarrollado por Hui es el pensamiento chino (Mou Zongsan → noodiversidad).
6. **Despliegue controlado**: solo `presentacion/` se publicó (no el repo del curso);
   `ssoProtection` desactivado vía API para acceso público de la clase.

## Lecciones aprendidas (las que cuestan caro ignorar)

- **El LLM alucina aun con la fuente en el prompt**: el agente de costos usó precios
  de API de su memoria ($15/$75) ignorando los oficiales que tenía escritos ($5/$25).
  Toda cifra crítica necesita un auditor que la coteje contra la fuente, no contra
  la memoria del modelo.
- **La verificación "de memoria" puede invertir hechos**: una auditoría añadió la
  advertencia "Hui no usa élan vital en este capítulo" — el texto primario demostró
  lo contrario (lo usa explícitamente). **Solo el texto primario manda**; las
  verificaciones de memoria deben etiquetarse como tales.
- **Sonnet verificando a Sonnet comparte puntos ciegos**: la auditoría Opus contra
  el canon encontró errores de especificación (von Thünen sin anillos, pregunta de
  Christaller contradiciendo su propia simulación) que el verificador same-model
  había aprobado. El verificador debe cotejar contra el CANON, no solo código-vs-spec.
- **Cachés de navegador y de http.server engañan**: tras cada edición del deck,
  verificar con cache-buster (`?v=N`) y avisar Ctrl+F5 al usuario.
- **`git fetch` de packs grandes se corta** en esta red (sideband disconnect con el
  PDF de 10 MB); descargar blobs puntuales con `gh api .../git/blobs/<sha>` funciona.
- **Los módulos canvas no deben pisar `container.style.position`** incondicionalmente
  (rompió hosts absolutos: portada 0×0, otro a 117.000 px de alto). Patrón seguro:
  solo posicionar si `getComputedStyle(c).position === 'static'`.
- **El QA visual necesita pruebas objetivas**: "anima de verdad" = dos capturas
  separadas 1,5 s con hash de píxeles distinto; no basta mirar una vez.

## Cómo correr todo

```bash
# Servidor local (con watchdog: relanza si muere)
python3 -m http.server 8123 --directory 03_Trabajos/Ponencia_Yuk_Hui/presentacion

# Entorno Python (matplotlib, networkx, numpy, qrcode, markdown)
source .venv/bin/activate

# Re-ejecutar una simulación (deterministas, semillas fijas)
.venv/bin/python 03_Trabajos/Ponencia_Yuk_Hui/simulaciones/sim_schelling_segregacion.py

# Experimentos y costos (ver .claude/continuar_en_torre.md para sujetos locales)
.venv/bin/python 03_Trabajos/Ponencia_Yuk_Hui/experimento/medir_costos.py

# Tesis HTML tras editar capítulos
.venv/bin/python 03_Trabajos/Ponencia_Yuk_Hui/presentacion/tesis/generar_html.py
```

## Reglas de trabajo de este usuario

- Español académico; jamás usar la palabra "doctoral" en entregables.
- El modelo principal orquesta workflows; no ejecuta trabajo pesado inline.
- Confirmar antes de publicar hacia afuera; commits solo cuando los pide.
- Reportar fielmente: si algo falló o quedó estimado, se dice tal cual.

## Estado y pendientes

Ver `.claude/continuar_en_torre.md` para el plan de continuación en kratos.
Pendientes conocidos: versión offline del deck (CDN de reveal.js), incorporar
"noodiversidad" a la tesis (ya está en deck y libreto), avisos sobre la ficha
de lectura del autor (4 imprecisiones reportadas, no corregidas por ser su
documento), ampliar el banco con más modelos locales y demo en vivo desde kratos.
