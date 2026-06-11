# Corpus de simulaciones urbanas — Ponencia Yuk Hui

Directorio: `/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui/simulaciones/`

Graficos en: `../presentacion/assets/sim/`

---

## Indice de simulaciones

| ID | Teoria | Autor | Año | Criterio de validacion (resultado obtenido) | Graficos | Relevancia filosofica (sintesis) |
|----|--------|-------|-----|----------------------------------------------|----------|----------------------------------|
| `von_thunen_anillos` | Anillos de von Thunen (renta agricola) | Johann Heinrich von Thunen | 1826 | Pendientes R_k: A=-6.0, B=-3.0 exactas; d0_A=10.0, d0_B=16.0 km (±0.01); dos anillos reales (A interior, B exterior) con frontera d*=4.0 km; envolvente monotona no creciente — **aprobada** | `sim_von_thunen_anillos_1.png`, `_2.png` | El espacio deja de ser cualidad y se convierte en distancia computable al mercado; ontologia de la ciudad como gradiente de valor |
| `alonso_bid_rent` | Bid-rent urbano de Alonso | William Alonso | 1964 | Cruce d*=13.33 km (±0.05); grupo mayor gradiente asignado al interior; envolvente decreciente — **aprobada** | `sim_alonso_bid_rent_1.png`, `_2.png` | La segregacion de clases emerge de la matematica del trade-off acceso/espacio, no de la moral; naturalizacion de la desigualdad via elegancia del modelo |
| `christaller_lugares_centrales` | Lugares centrales k=3 | Walter Christaller | 1933 | Razon areas=[3.0, 3.0, 3.0] (±0.001); razon lugares 18/6=3, 6/2=3, 2/1=2 (correcto); area base=259.8076 km² (error=0.0 km²) — **OK** | `sim_christaller_lugares_centrales_1.png`, `_2.png` | Geometria normativa de la ciudad: la jerarquia urbana como optimo deducible a priori; peligro politico del uso planificador (caso nazi) |
| `reilly_huff_gravitacion_comercial` | Gravitacion comercial Reilly/Huff | W.J. Reilly / D.L. Huff | 1931/1964 | BP=10.0 km (±0.05); P(T2)=0.5 exacto cuando A_1/d_1²=A_2/d_2²; fraccion rejilla 0.7755 (|0.7755-0.78|=0.0045 ≤ 0.05) — **aprobada** | `sim_reilly_huff_gravitacion_comercial_1.png`, `_2.png` | La metafora newtoniana reduce el deseo humano a masa/distancia; quien define el "atractivo" gana por construccion del modelo |
| `schelling_segregacion` | Modelo de segregacion de Schelling | Thomas Schelling | 1971 | frac_final=0.7507 > 0.70; convergencia iter=14 con 0 insatisfechos; T=0.75 no converge — **OK** | `sim_schelling_segregacion_1.png`, `_2.png` | Emergencia: preferencias individuales suaves generan segregacion macro que nadie eligio; la falacia de inferir intencion desde patron |
| `duncan_disimilitud` | Indice de disimilitud de Duncan | O.D. Duncan / B. Duncan | 1955 | D(4 tracts)=0.4000 (±0.001); D(3 tracts)=0.3000; D(rejilla Schelling canonica del proyecto, 25 bloques 10x10)=0.2462 (segregacion baja-moderada; baseline aleatorio ~0.09); D(identica)=0.0 — **OK** | `sim_duncan_disimilitud_1.png`, `_2.png` | El poder del indicador: lo que se mide se gobierna; la falacia ecologica de la unidad de analisis |
| `zipf_rank_size` | Ley rango-tamano de Zipf | George K. Zipf | 1949 | Sistema ideal q=1: pendiente=-1.000 (±0.001); R²=1.0; P(4)=250000 exacto. Sistema empirico q=0.85 perturbado (semilla fija): pendiente≈-0.857; R²=0.987, ilustra desviacion de la referencia -1 — **aprobada** | `sim_zipf_rank_size_1.png`, `_2.png` | Regularidad estadistica universal sin teoria causal: la ciudad como instancia de ley natural-social; tension entre unicidad vivida y lugar anonimo en una distribucion. q=1 es la version estricta/idealizada, no un invariante fisico exacto: los sistemas reales se desvian (q~0.8-1.2; Gabaix 1999) |
| `bettencourt_west_escalamiento` | Escalamiento urbano superlineal | Bettencourt / Lobo / Helbing / Kuhnert / West (PNAS 2007) | 2007 | beta socioecon=1.1500 en [1.10,1.20]; beta infraestr=0.8500 en [0.80,0.90]; R²=1.0; factor duplicacion=2.2191 (±0.01) — **aprobada** | `sim_bettencourt_west_escalamiento_1.png`, `_2.png` | La ciudad como reactor social: el escalamiento superlineal promete la "prima urbana" pero oculta la distribucion; lo bueno y lo malo escalan juntos |
| `automata_celular_crecimiento_urbano` | Automata celular de crecimiento urbano (regla estocastica de transicion) | Formulacion: White-Engelen / Clarke (SLEUTH); antecedente: Tobler (geografia celular) | White-Engelen 1993 / Clarke 1997; Tobler 1979 (antecedente) | Conexidad 100% todos los pasos; compacidad isoperimetrica final ~0.20 (medida primaria); df box-counting=1.6812 en [1.6, 2.0] (secundario, cajas que dividen la rejilla); 2672 celdas urbanas en paso 50 (determinista) — **OK** | `sim_automata_celular_crecimiento_urbano_1.png`, `_2.png` | El crecimiento urbano como contagio espacial sin plan; regla fronteriza adoptada (p_base refuerza el frente, no nuclea islas: solo crecimiento compacto); la responsabilidad oculta tras los parametros del modelo (p_base/p_difusion como politica encubierta) |
| `dla_batty_longley_fractal` | DLA y dimension fractal urbana Batty-Longley | M. Batty / P. Longley | 1994 | D_sim=1.693 en [1.60, 1.80] (region de escalamiento, N≤60% total); R²=0.9989 > 0.97; D(dos puntos)=1.266 (±0.001) — **OK** | `sim_dla_batty_longley_fractal_1.png`, `_2.png` | La ciudad como objeto fractal: su irregularidad es medible y autosimilar; pregunta ontologica de si la dimension fraccionaria capta algo esencial o solo el contorno |
| `sintaxis_espacial_integracion` | Sintaxis espacial Hillier-Hanson | B. Hillier / J. Hanson | 1984 | Integration(C)=3.0000 (±0.01); Integration(A)=1.0000 (±0.01); Integration(rejilla central)=7.6667 (±1.0) — **OK** | `sim_sintaxis_espacial_integracion_1.png`, `_2.png` | La topologia de las calles configura la sociedad; la politica de que calles quedan "integradas" por diseno; determinismo espacial que puede ocultar decisiones de poder |
| `braess_wardrop_equilibrio` | Paradoja de Braess / equilibrio de Wardrop | D. Braess / J.G. Wardrop | 1968/1952 | t_sin=65 exacto; t_con=80 exacto; aumento=15 (±1) — **aprobada** | `sim_braess_wardrop_equilibrio_1.png`, `_2.png` | Mas opciones no siempre mejoran el bienestar; la brecha entre optimo individual y optimo del sistema justifica la intervencion publica (cerrar calles puede mejorar el trafico) |
| `modelo_gravitacional_flujos` | Modelo gravitacional de flujos | J. Q. Stewart (c=2); raíces Carey/Zipf; entropía Wilson | 1948/1967 | T_12=55556, T_13=125000, T_23=40000 (±0.5%); suma=220556; simetria T_ij=T_ji — **aprobada** | `sim_modelo_gravitacional_flujos_1.png`, `_2.png` | La formalizacion entropica de Wilson revela que la "ley fisica" es el estado mas probable bajo restricciones; planificar flujos como fenomenos inevitables naturaliza lo politico |

---

## Nota de reproducibilidad

**Interprete:**
```
/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/.venv/bin/python
```

**Semillas fijas** (numpy.random.seed / numpy.random.default_rng):

| Simulacion | Semilla |
|------------|---------|
| schelling_segregacion | 42 |
| automata_celular_crecimiento_urbano | 7 |
| dla_batty_longley_fractal | 3 |
| zipf_rank_size | 42 (solo el sistema empirico perturbado q=0.85; el sistema ideal q=1 es analitico) |
| resto (modelos deterministicos) | sin semilla |

**Comando por simulacion** (ejecutar desde el directorio `simulaciones/`):

```bash
VENV=/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/.venv/bin/python
SIM=/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui/simulaciones

$VENV $SIM/sim_von_thunen_anillos.py
$VENV $SIM/sim_alonso_bid_rent.py
$VENV $SIM/sim_christaller_lugares_centrales.py
$VENV $SIM/sim_reilly_huff_gravitacion_comercial.py
$VENV $SIM/sim_schelling_segregacion.py
$VENV $SIM/sim_duncan_disimilitud.py
$VENV $SIM/sim_zipf_rank_size.py
$VENV $SIM/sim_bettencourt_west_escalamiento.py
$VENV $SIM/sim_automata_celular_crecimiento_urbano.py
$VENV $SIM/sim_dla_batty_longley_fractal.py
$VENV $SIM/sim_sintaxis_espacial_integracion.py
$VENV $SIM/sim_braess_wardrop_equilibrio.py
$VENV $SIM/sim_modelo_gravitacional_flujos.py
```

Cada script genera sus PNG en `../presentacion/assets/sim/`, sus datos en `datos_<id>.json` y sus preguntas en `preguntas_<id>.json` dentro del directorio `simulaciones/`. Los resultados son identicos entre ejecuciones para semillas fijadas. Los modelos sin semilla son analiticos y cerrados.

**Archivos de corpus:**
- `catalogo.json` — 13 teorias con formulacion, experimento, criterios y preguntas canonicas
- `banco_preguntas.json` — 39 preguntas en lista plana (3 por teoria) con valor_exacto, tipo y tolerancia
- `preguntas_<id>.json` — archivo individual por teoria (generado por cada script)
- `datos_<id>.json` — datos numericos de validacion por teoria
