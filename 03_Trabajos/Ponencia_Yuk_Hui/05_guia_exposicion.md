# Guía de exposición — disparadores (leer en clase)

> **Yuk Hui · «Fragmentar el futuro»** · 20:00 exactos · ~130 pal/min · respirar en slides 5, 7, 12

## ⏱ Reloj de hitos

| A los… | Debo ir en… |
|---|---|
| **5:00** | fin de Dreyfus → entrando a Experimento 1 (slide 5) |
| **10:00** | fin de Resultados Exp.1 → 13 teorías urbanas (slide 7) |
| **15:00** | fin de Heatmap (slide 10) → entrando a Costo (slide 10b) |
| **20:00** | tesis + cierre + pregunta de debate |

## 🔢 Los 3 números que NO puedo decir mal

1. **Exp.1 frontera:** Sonnet **90** · Opus **70** · Python **100** (Opus < Sonnet)
2. **Curva NO monótona:** 3B **20** · 14B **20** · 20B **40** · 32B **20**
3. **Cuatro órdenes de magnitud:** Python **$6,9×10⁻⁶** (siete millonésimas) vs Opus **$0,013–0,070**

> NUNCA recortar: **T6 = ∅** y los **cuatro órdenes de magnitud**.

---

## NÚCLEO

### [00:00–01:00] Slide 1 — Apertura · Hui
- Hui no pregunta qué *no puede* la IA.
- Pregunta cómo pensar su límite.
- Tesis de hoy: el límite no es técnico.
- Es político y cosmológico. → decir: *síntesis mía, no cita literal*.
- Texto ancla: *Fragmentar el futuro*, Yuk Hui.
- Recorrido: seis pensadores, Hui, dos experimentos, una tesis.
- ⚡*[avanzar a slide 2]*

### [01:00–02:30] Slide 2 — Bergson
- Inteligencia = fabricar herramientas. *Homo faber*.
- Fuimos *homo faber* antes que *sapiens*.
- Frente a eso: el ímpetu vital, *élan vital*. → decir: *término que Hui sí usa*.
- ⚡*[señalar: homo faber / mecánico / vital]*
- La IA: caso límite de exteriorización; desborda la intención.
- Exteriorizar no es entender. (vuelve al final)
- Paradoja de la inteligencia (Hegel): se exterioriza, puede quedar subordinada.
- Conciencia desventurada: pánico al desempleo, política reaccionaria.

### [02:30–04:30] Slide 3 — Wiener · Simondon · Kant
- Cibernética: control y comunicación en animal y máquina.
- Mecanismo: retroalimentación, la salida vuelve como entrada.
- «La información es información, no materia ni energía».
- ⚡*[señalar Wiener]*
- → decir: *Wiener malinterpretó a Bergson; vitalismo no es organicismo*.
- Simondon: solo en la 3ª *Crítica* Kant pudo pensar la cibernética.
- → decir: *individuación/concretización son de otra obra — mi lectura cuidada*.
- ⚡*[señalar Kant]*
- Juicio **determinante**: aplica la regla al caso.
- Juicio **reflexionante**: encuentra la regla desde el caso.
- La IA aplica patrones; no se da sus fines.
- Giro de Hui: el origen real no es Dartmouth 1956, es la cibernética.

### [04:30–05:30] Slide 4 — Dreyfus · Heidegger
- Dreyfus (vía Heidegger): la inteligencia no se agota en cálculo.
- Mundo = horizonte de significatividad, no datos. → decir: *según Dreyfus*.
- La IA no capta relevancia: carece de *Dasein*.
- ⚡*[señalar concepto: Dasein]*
- Matiz de Hui: ese mundo ya está digitalizado, *mathesis universalis*.
- Es el *Gestell* que vivimos.
- Diseñé un caso. El resultado no fue el que esperaba — y eso lo afila.

### [05:30–07:00] Slide 5 — Experimento 1 · Protocolo
- ⚡*[cada fila aparece con un clic al nombrarla]*
- Seis sujetos: cuatro abiertos (3B a 32B) y dos frontera (Sonnet, Opus).
- Los cuatro locales no corrieron en la nube de nadie.
- Corrieron en mi workstation, GPU de consumo, Ollama.
- Pregunta de Hui: quién posee el cómputo, quién fija la infraestructura.
- Mismas tareas, sin herramientas, dos intentos. Python da la verdad.
- ◦ *[OPCIONAL — recortar:]*
  - ◦ ⚡*[fragment T1]* multiplicar dos enteros de 12 dígitos — *Bergson*.
  - ◦ ⚡*[fragment T2]* camino más corto, grafo de 25 barrios — *óptimo global*.
  - ◦ ⚡*[fragment T3]* conteo de rutas, retícula 12×12 — *combinatoria*.
  - ◦ ⚡*[fragment T4]* recursión afín modular, 40 pasos — *Wiener*.
  - ◦ ⚡*[fragment T5]* suma de cuadrados de 30 sensores — *agregado exacto*.
- ⚡*[fragment T6, fila inversa]* la trampa: juicio de relevancia en escena urbana — *Dreyfus*.
- Hipótesis: si el límite fuera cuantitativo, se disolvería de 3B a Opus. Veamos.

### [07:00–08:30] Slide 6 — Experimento 1 · Resultados
- El argumento sale de los datos.
- ⚡*[señalar la curva]* eje: 3B a Opus; punteada arriba: 100 % de Python.
- Subir parámetros NO sube exactitud.
- 3B y 32B empatan en **veinte**; el 20B gana con **cuarenta**.
- Curva no monótona: **20, 20, 40, 20**.
- ⚡*[pausa 2 seg]*
- Salto de régimen: local a frontera. Sonnet **noventa**, Opus **setenta**.
- Ni la frontera toca el cien. Opus < Sonnet.
- Opus falló la suma de cuadrados: **651.397.404** vs exacto **651.396.404**.
- Matiz honesto: la retícula (2.700.000 rutas) la aciertan los seis — es memorizable.
- T6 = cero estructural: no se mueve con ningún tamaño. Corazón del argumento.

### [08:30–10:00] Slide 7 — 13 teorías urbanas
- Antes de juzgar a la IA: lo que la ciudad SÍ computa hace un siglo.
- Trece teorías clásicas, de von Thünen 1826 a Bettencourt-West 2007.
- Las implementé todas, semillas fijas, cada una pasa su validación.
- Schelling converge en 14 a 0,75; Christaller k=3; Zipf pendiente −1.
- ⚡*[click: abrir chip Schelling — si responde; si no, seguir]*
- ⚡*[señalar el callout]* un portátil corre las trece, exactas, en **64,7 segundos**.
- Y son **$6,9×10⁻⁶** por respuesta — siete millonésimas de dólar.
- El conocimiento urbano ya existe y es barato.
- La pregunta es qué hacemos con lo que ya sabemos.

### [10:00–11:30] Slide 8 — Galería viva (4 teorías)
- ⚡*[mostrar galería 2×2; si una celda no monta, narrar con datos]*
- Cuatro de las trece, las más expresivas.
- Schelling: preferencias suaves → segregación que nadie eligió. 0,50 → 0,75, itera 14.
- ⚡*[click: abrir chip Schelling → datos canónicos]*
- DLA (Batty-Longley): ciudad como fractal, dimensión 1,69.
- Christaller: teselación hexagonal k=3 — geometría puesta al servicio nazi. No es neutral.
- Braess-Wardrop: abrir una vía puede empeorar el tráfico de todos.
- → decir: *Zipf empírico se desvía: la «ley» es idealización*.
- → decir: *Bettencourt-West beta 1,15: lo bueno y lo malo escalan juntos*.
- ¿Pueden los seis modelos resolver lo que estas teorías plantean?

### [11:30–13:00] Slide 9 — Experimento 2 · Banco de teorías
- Segundo experimento, complementario.
- 13 teorías → **39 preguntas**, tres por teoría: dos cerradas, una emergente.
- Mismos seis sujetos, una sola pasada.
- ⚡*[señalar la curva global]*
- Exactitud: 3B **38,5**; medianos **77–79**; Sonnet **89,7**; Opus **92,3**.
- Aquí la escala ordena más limpio; Opus supera a Sonnet por poco.
- ¿Contradice al Exp.1? No: muchas cerradas son fórmulas memorizables.
- El techo no cambia: nadie toca el cien del cómputo puro.
- La verdad sigue del lado del algoritmo.

### [13:00–15:00] Slide 10 — Experimento 2 · Heatmap (cerrada vs emergente)
- ⚡*[señalar el mapa]* filas teorías, columnas sujetos, verde alto / rojo bajo.
- Por columna: el 3B casi todo rojo (38,5). De 14B en adelante domina el verde.
- Por tipo de pregunta — lo interesante.
- Cerrada: Opus **27 de 27**, cien por ciento; Sonnet, 20B, 14B rondan 93.
- Emergente: Sonnet baja a **83**, Opus a **75**, 3B a **cero de doce**.
- ⚡*[pausa 2 seg]*
- Filas verdes (Christaller, Zipf, DLA, sintaxis): fórmula cerrada, las recuerda.
- Cuando hay que simular (Schelling, autómata, Braess): la imitación se rompe.
- Patrón del Exp.1: la escala compra memorización, no ejecución.
- → decir: *una pasada, 39 preguntas, no es prueba robusta — ilustración consistente*.

### [15:00–16:00] Slide 10b — Costo
- Pongamos precio al conocimiento.
- ⚡*[señalar la imagen, escala logarítmica]*
- Abajo: Python **$6,9×10⁻⁶** (siete millonésimas) por respuesta correcta.
- → decir: *tiempo medido; energía estimada a 25 W (RAPL sin permisos)*.
- Locales en GPU: de **$0,000147** (3B) a **$0,0018** (32B). Medido; tarifa estimada.
- → decir: *frontera son rangos: la API no devuelve tokens reales*.
- Sonnet **$0,007–0,041**; Opus **$0,013–0,070**. Las barras de error son esos rangos.
- ⚡*[pausa 2 seg]*
- Del cómputo puro a Opus: **cuatro órdenes de magnitud** (≈10.000× más caro).
- Para una respuesta que sigue por debajo del cien que Python da gratis.
- Ese costo es material, energético y político: quién paga, quién posee la GPU.

### [16:00–17:30] Slide 11 — Lectura filosófica
- Calibremos sin exagerar.
- Acertar una multiplicación no es «calcular»: produce el token plausible.
- No ejecuta el algoritmo: por eso Opus falla por un dígito.
- Bergson y Kant en pie: aplica patrones, no se da la regla.
- → decir: *el experimento no prueba solo que el límite sea categorial — eso lo argumenta Hui vía Kant*.
- Pero el dato es consistente: si fuera cuantitativo, de 3B a 32B se acercaría. No lo hace.
- ⚡*[señalar T6 = ∅]*
- Python no arranca: no hay función objetivo. Escribir el algoritmo *es* el juicio.
- Los modelos respondieron distinto: repartidor, niño, acompañante; uno alucinó «mujer mayor».
- Hay relevancia, no unicidad: falta el mundo que la fije. Dreyfus puro.
- Hui: lo computable es una tendencia de la inteligencia, no toda.
- Definir inteligencia = cómputo es tomar la parte por el todo.
- ◦ *[OPCIONAL — recortar:]* salida de Hui: resituar la técnica en la vida.
- ◦ *[OPCIONAL]* «la mecánica exigirá una mística»; Hölderlin: donde está el peligro crece lo que salva.

### [17:30–19:00] Slide 12 — Urban AI
- Llevemos esto a la ciudad. La smart city promete reducir la urbe a sensores y cálculo.
- → decir: *Hui no tematiza la ciudad; la traslación mundo→ciudad y gobernar/gestionar son mías*.
- Lo que Hui sí dice: el mundo se reduce a datos, *mathesis universalis*, *Gestell*.
- Gobernar no es multiplicar enteros. Es una escena T6.
- A quién se alerta, qué barrio se prioriza, qué cuenta como riesgo: juicio, no cómputo.
- No hay respuesta única: alguien fija qué importa, y eso es político.
- La IA *gestiona* (optimiza una función dada); no *gobierna* (decide cuál es la función).
- Hui + Schmitt: la superinteligencia es neutralización y despolitización por la técnica.
- ◦ *[OPCIONAL — recortar:]* Mou Zongsan: inteligencia *zhineng* vs sabiduría *zhihui*; intuición intelectual.
- ◦ *[OPCIONAL]* tesis final: no superinteligencia sino **noodiversidad**; hace falta tecnodiversidad.
- ◦ *[OPCIONAL]* cosmotécnica = concepto analítico; tecnodiversidad = propuesta normativa.
- Que los locales corrieran en workstation propia: condición material de la tecnodiversidad.

### [19:00–20:00] Slides 13 + 14 — Tesis + Cierre
- La tesis, en tres movimientos.
- ⚡*[fragment 1]* Uno: herramientas sobredimensionadas respecto de su aplicación.
- ⚡*[fragment 2]* Dos: el límite no es técnico, es político, económico y ontológico.
- ⚡*[fragment 3]* Tres: lo que falta no es un modelo más potente, sino *aplicar* lo que ya existe.
- El Banco Epistémico Urbano lo sistematiza — construido orquestando IA bajo supervisión (evidencia performativa).
- ⚡*[avanzar a slide 14 — mostrar QR]*
- Cierro donde abrí: el límite no es técnico, es político y cosmológico.
- Falta pluralidad de mundos: noodiversidad. Aplicar antes que escalar; fragmentar antes que optimizar.
- **Pregunta de debate (textual):** *«Si gobernar la ciudad es una escena T6 —no una tarea T1— ¿qué mundo produce la Urban AI? ¿Cómo pensar la tecnodiversidad desde la experiencia urbana latinoamericana?»*
- Gracias.

---

## 📎 Anexos (solo si preguntan) — qué responder con cada uno

- **Anexo A · Gradiente Exp.1 (6×6):** «el grande no siempre gana» → Opus 3 fallos en 10 (T1, T2, T5); T3 verde para los seis; 32B con timeouts >600 s.
- **Anexo A2 · Aciertos por tarea:** T3 columna verde = régimen memorizable; T1/T4/T5 = colapso local; T6 sin casilla (no hay verdad).
- **Anexo B · Detalle T6:** si dudan de la divergencia → foco por modelo (repartidor/niño/acompañante; qwen3:14b alucinó «mujer mayor»). Relevancia sin unicidad.
- **Anexo C · Cerrada vs emergente:** si cuestionan «el grande siempre gana» → Sonnet 83 % supera a Opus 75 % en emergentes; cómputo puro 100 % en las tres columnas.
