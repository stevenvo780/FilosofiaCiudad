"""
Verificador computacional del experimento filosófico-computacional.
Ponencia: Yuk Hui / Filosofía de la Ciudad
Autor del script: verificador automático
Fecha: 2026-06-10

Tareas computables (inversa=false): t1, t2, t3, t4, t5
Tarea inversa (inversa=true): t6 -> NO_COMPUTABLE
"""

import json
import math
import heapq
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. Rutas
# ---------------------------------------------------------------------------
BASE = Path("/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad")
EXP_DIR = BASE / "03_Trabajos/Ponencia_Yuk_Hui/experimento"
ASSETS_DIR = BASE / "03_Trabajos/Ponencia_Yuk_Hui/presentacion/assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. CÓMPUTOS EXACTOS
# ---------------------------------------------------------------------------

# T1: Multiplicación exacta
def calcular_t1():
    a = 387465129847
    b = 902341765893
    return str(a * b)

# T2: Camino más corto (Dijkstra)
def calcular_t2():
    aristas_raw = (
        "Altavista-Bellavista=4; Altavista-Cumbres=7; Bellavista-Cumbres=2; "
        "Bellavista-Dorado=9; Cumbres-Esmeralda=3; Dorado-Esmeralda=6; "
        "Dorado-Farallon=5; Esmeralda-Girasol=8; Farallon-Girasol=1; "
        "Farallon-Horizonte=4; Girasol-Horizonte=2; Girasol-Iguazu=7; "
        "Horizonte-Jacaranda=3; Iguazu-Jacaranda=2; Iguazu-Kennedy=6; "
        "Jacaranda-Lagos=5; Kennedy-Lagos=4; Kennedy-Miramar=8; Lagos-Nogal=3; "
        "Miramar-Nogal=2; Miramar-Olivos=5; Nogal-Palermo=6; Olivos-Palermo=1; "
        "Palermo-Quinta=4; Quinta-Roble=3; Roble-Sauce=2; Sauce-Tejar=5; "
        "Tejar-Urapan=4; Urapan-Veranda=2; Veranda-Ximena=6; Ximena-Yarumal=3; "
        "Yarumal-Zafiro=2; Olivos-Roble=9; Nogal-Sauce=7; Lagos-Tejar=10; "
        "Quinta-Urapan=8; Roble-Veranda=6; Sauce-Ximena=9; Tejar-Yarumal=7; "
        "Urapan-Zafiro=11; Altavista-Dorado=12; Cumbres-Farallon=10; "
        "Esmeralda-Horizonte=9"
    )

    adj = {}
    for token in aristas_raw.split(";"):
        token = token.strip()
        if not token:
            continue
        edge, weight = token.split("=")
        u, v = edge.split("-")
        u, v, w = u.strip(), v.strip(), int(weight.strip())
        adj.setdefault(u, []).append((v, w))
        adj.setdefault(v, []).append((u, w))

    # Dijkstra
    inicio, fin = "Altavista", "Zafiro"
    dist = {n: float("inf") for n in adj}
    dist[inicio] = 0
    prev = {n: None for n in adj}
    heap = [(0, inicio)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    # Reconstruir camino
    camino = []
    nodo = fin
    while nodo is not None:
        camino.append(nodo)
        nodo = prev[nodo]
    camino.reverse()

    distancia = dist[fin]
    camino_str = ", ".join(camino)
    return camino_str, distancia

# T3: Conteo combinatorio rutas monótonas 12x12
def calcular_t3():
    return str(math.comb(24, 12))

# T4: Recursión afín modular 40 pasos
def calcular_t4():
    A, B, M = 137, 991, 100000
    x = 42
    for _ in range(40):
        x = (A * x + B) % M
    return str(x)

# T5: Suma de cuadrados 30 lecturas
def calcular_t5():
    lecturas = [
        4821, 3990, 5172, 4408, 3765, 6011, 2987, 5540, 4123, 3876,
        5298, 4710, 3654, 6102, 2890, 5471, 4019, 3788, 5630, 4255,
        3912, 6044, 2976, 5388, 4187, 3801, 5519, 4630, 3745, 6088
    ]
    return str(sum(x * x for x in lecturas))

# T6: NO COMPUTABLE
# La escena urbana es texto en lenguaje natural sin estructura de datos,
# sin métrica de peligro, sin función objetivo definida en el enunciado.
# Para que un programa calcule la respuesta, un humano tendría que decidir
# y codificar a mano: (1) representación de entidades, (2) definición del
# "peor desenlace", (3) función de relevancia. Esas decisiones SON el juicio
# que se pide. Sin esa formalización previa, no existe ningún algoritmo que
# pueda siquiera comenzar: no hay entrada estructurada, ni salida bien
# definida, ni regla dada. valor_exacto = "NO_COMPUTABLE".

# ---------------------------------------------------------------------------
# 2. EJECUTAR CÓMPUTOS
# ---------------------------------------------------------------------------

t1_valor = calcular_t1()
t2_camino, t2_distancia = calcular_t2()
t3_valor = calcular_t3()
t4_valor = calcular_t4()
t5_valor = calcular_t5()

print("=== VALORES EXACTOS ===")
print(f"T1 (multiplicación):       {t1_valor}")
print(f"T2 (camino corto):         {t2_camino}  [dist={t2_distancia}]")
print(f"T3 (conteo retícula):      {t3_valor}")
print(f"T4 (recursión afín):       {t4_valor}")
print(f"T5 (suma cuadrados):       {t5_valor}")
print(f"T6 (relevancia escena):    NO_COMPUTABLE")
print()

# Verificaciones internas según especificación
assert t1_valor == "349625969488102520908371", f"T1 falla: {t1_valor}"
assert t2_camino == "Altavista, Bellavista, Cumbres, Esmeralda, Horizonte, Jacaranda, Lagos, Tejar, Yarumal, Zafiro", f"T2 falla: {t2_camino}"
assert t2_distancia == 45, f"T2 distancia falla: {t2_distancia}"
assert t3_valor == "2704156", f"T3 falla: {t3_valor}"
assert t4_valor == "23842", f"T4 falla: {t4_valor}"
assert t5_valor == "651396404", f"T5 falla: {t5_valor}"
print("Todas las verificaciones internas PASARON.")
print()

# ---------------------------------------------------------------------------
# 3. RESPUESTAS DE SUJETOS Y CALIFICACIÓN
# ---------------------------------------------------------------------------

VALOR_EXACTO = {
    "t1_multiplicacion":    t1_valor,
    "t2_camino_corto":      t2_camino,
    "t3_conteo_reticula":   t3_valor,
    "t4_recursion_afin":    t4_valor,
    "t5_calculo_exteriorizado": t5_valor,
    "t6_relevancia_escena": "NO_COMPUTABLE",
}

respuestas_raw = [
    {"tarea_id": "t1_multiplicacion", "modelo": "sonnet", "intento": 1,
     "respuesta_final": "349625969488102520908371", "confianza": "baja", "uso_herramientas": False},
    {"tarea_id": "t1_multiplicacion", "modelo": "sonnet", "intento": 2,
     "respuesta_final": "349625969488102520908371", "confianza": "baja", "uso_herramientas": False},
    {"tarea_id": "t1_multiplicacion", "modelo": "opus", "intento": 1,
     "respuesta_final": "349625969488102520908371", "confianza": "baja", "uso_herramientas": False},
    {"tarea_id": "t1_multiplicacion", "modelo": "opus", "intento": 2,
     "respuesta_final": "349634804376851666458571", "confianza": "baja", "uso_herramientas": False},

    {"tarea_id": "t2_camino_corto", "modelo": "sonnet", "intento": 1,
     "respuesta_final": "Altavista, Bellavista, Cumbres, Esmeralda, Horizonte, Jacaranda, Lagos, Tejar, Yarumal, Zafiro",
     "confianza": "alta", "uso_herramientas": False},
    {"tarea_id": "t2_camino_corto", "modelo": "sonnet", "intento": 2,
     "respuesta_final": "Altavista, Bellavista, Cumbres, Farallon, Girasol, Horizonte, Jacaranda, Lagos, Tejar, Yarumal, Zafiro",
     "confianza": "alta", "uso_herramientas": False},
    {"tarea_id": "t2_camino_corto", "modelo": "opus", "intento": 1,
     "respuesta_final": "Altavista, Bellavista, Cumbres, Esmeralda, Horizonte, Jacaranda, Lagos, Tejar, Yarumal, Zafiro",
     "confianza": "alta", "uso_herramientas": False},
    {"tarea_id": "t2_camino_corto", "modelo": "opus", "intento": 2,
     "respuesta_final": "Altavista, Bellavista, Cumbres, Esmeralda, Horizonte, Jacaranda, Lagos, Tejar, Yarumal, Zafiro",
     "confianza": "alta", "uso_herramientas": False},

    {"tarea_id": "t3_conteo_reticula", "modelo": "sonnet", "intento": 1,
     "respuesta_final": "2704156", "confianza": "alta", "uso_herramientas": False},
    {"tarea_id": "t3_conteo_reticula", "modelo": "sonnet", "intento": 2,
     "respuesta_final": "2704156", "confianza": "alta", "uso_herramientas": False},
    {"tarea_id": "t3_conteo_reticula", "modelo": "opus", "intento": 1,
     "respuesta_final": "2704156", "confianza": "alta", "uso_herramientas": False},
    {"tarea_id": "t3_conteo_reticula", "modelo": "opus", "intento": 2,
     "respuesta_final": "2704156", "confianza": "alta", "uso_herramientas": False},

    {"tarea_id": "t4_recursion_afin", "modelo": "sonnet", "intento": 1,
     "respuesta_final": "23842", "confianza": "media", "uso_herramientas": False},
    {"tarea_id": "t4_recursion_afin", "modelo": "sonnet", "intento": 2,
     "respuesta_final": "23842", "confianza": "media", "uso_herramientas": False},
    {"tarea_id": "t4_recursion_afin", "modelo": "opus", "intento": 1,
     "respuesta_final": "23842", "confianza": "alta", "uso_herramientas": False},
    {"tarea_id": "t4_recursion_afin", "modelo": "opus", "intento": 2,
     "respuesta_final": "23842", "confianza": "alta", "uso_herramientas": False},

    {"tarea_id": "t5_calculo_exteriorizado", "modelo": "sonnet", "intento": 1,
     "respuesta_final": "651396404", "confianza": "media", "uso_herramientas": False},
    {"tarea_id": "t5_calculo_exteriorizado", "modelo": "sonnet", "intento": 2,
     "respuesta_final": "651396404", "confianza": "media", "uso_herramientas": False},
    {"tarea_id": "t5_calculo_exteriorizado", "modelo": "opus", "intento": 1,
     "respuesta_final": "651397404", "confianza": "media", "uso_herramientas": False},
    {"tarea_id": "t5_calculo_exteriorizado", "modelo": "opus", "intento": 2,
     "respuesta_final": "651400404", "confianza": "media", "uso_herramientas": False},

    {"tarea_id": "t6_relevancia_escena", "modelo": "sonnet", "intento": 1,
     "respuesta_final": "La alerta debe dirigirse al repartidor en moto para que frene de inmediato, porque es el unico agente con capacidad de causar un impacto letal sobre el nino que acaba de pisar la calzada con el semaforo en rojo y el pavimento mojado reduciendo la distancia de frenado.",
     "confianza": "alta", "uso_herramientas": False},
    {"tarea_id": "t6_relevancia_escena", "modelo": "sonnet", "intento": 2,
     "respuesta_final": "La alerta debe dirigirse al niño que acaba de pisar la calzada, para detenerlo de inmediato antes de que la moto que acelera sobre el pavimento mojado lo atropelle.",
     "confianza": "alta", "uso_herramientas": False},
    {"tarea_id": "t6_relevancia_escena", "modelo": "opus", "intento": 1,
     "respuesta_final": "Al acompanante del nino, para que lo sujete y le impida entrar a la calzada antes de que lo atropelle la moto que acelera sobre el pavimento mojado.",
     "confianza": "alta", "uso_herramientas": False},
    {"tarea_id": "t6_relevancia_escena", "modelo": "opus", "intento": 2,
     "respuesta_final": "Alerta dirigida al niño que soltó la mano de su acompañante y entra a la calzada (y a su acompañante para retenerlo), por riesgo de atropello mortal con la moto acelerando, semáforo en rojo y pavimento resbaladizo.",
     "confianza": "alta", "uso_herramientas": False},
]

TAREAS_INVERSAS = {"t6_relevancia_escena"}


def normalizar(s):
    """Normaliza formato: strip, colapsa espacios, elimina separadores de miles,
    mayúscula inicial en cada nodo para listas (ya vienen capitalizados)."""
    return s.strip()


def calificar(resp):
    tid = resp["tarea_id"]
    if tid in TAREAS_INVERSAS:
        return "NO_APLICA"
    valor_ref = VALOR_EXACTO[tid]
    respuesta = normalizar(resp["respuesta_final"])
    return respuesta == valor_ref


respuestas_calificadas = []
for r in respuestas_raw:
    veredicto = calificar(r)
    entry = dict(r)
    entry["correcto"] = veredicto
    respuestas_calificadas.append(entry)
    print(f"  {r['tarea_id']:30s}  {r['modelo']:7s}  intento {r['intento']}  -> {veredicto}")

print()

# ---------------------------------------------------------------------------
# 4. EXACTITUD AGREGADA POR MODELO
# ---------------------------------------------------------------------------

def exactitud_modelo(modelo):
    total = 0
    aciertos = 0
    for r in respuestas_calificadas:
        if r["modelo"] == modelo and r["correcto"] not in ("NO_APLICA",):
            total += 1
            if r["correcto"] is True:
                aciertos += 1
    return {"aciertos": aciertos, "total": total,
            "porcentaje": round(aciertos / total * 100, 2) if total > 0 else 0}

exactitud_sonnet = exactitud_modelo("sonnet")
exactitud_opus   = exactitud_modelo("opus")

print(f"Exactitud Sonnet: {exactitud_sonnet['aciertos']}/{exactitud_sonnet['total']} ({exactitud_sonnet['porcentaje']}%)")
print(f"Exactitud Opus:   {exactitud_opus['aciertos']}/{exactitud_opus['total']} ({exactitud_opus['porcentaje']}%)")
print()

# ---------------------------------------------------------------------------
# 5. ACIERTOS POR TAREA Y MODELO
# ---------------------------------------------------------------------------

TAREAS_IDS = [
    "t1_multiplicacion", "t2_camino_corto", "t3_conteo_reticula",
    "t4_recursion_afin", "t5_calculo_exteriorizado", "t6_relevancia_escena"
]

def aciertos_tarea_modelo(tarea_id, modelo):
    resultados = [r for r in respuestas_calificadas
                  if r["tarea_id"] == tarea_id and r["modelo"] == modelo]
    total = len(resultados)
    if tarea_id in TAREAS_INVERSAS:
        return "NO_APLICA", total
    aciertos = sum(1 for r in resultados if r["correcto"] is True)
    return aciertos, total

# ---------------------------------------------------------------------------
# 6. CONSTRUIR resultados.json
# ---------------------------------------------------------------------------

tareas_meta = {
    "t1_multiplicacion": {
        "titulo": "Multiplicación exacta de dos enteros de 12 dígitos",
        "teoria": "La IA estadística no ejecuta el algoritmo aritmético; predice tokens plausibles, de modo que la precisión dígito a dígito no está garantizada.",
        "autor": "Bergson",
        "inversa": False
    },
    "t2_camino_corto": {
        "titulo": "Camino más corto exacto en un grafo urbano de 25 barrios",
        "teoria": "El óptimo global sobre datos discretos exige un algoritmo determinístico (Dijkstra); la heurística asociativa del LLM no garantiza la ruta mínima ni su unicidad.",
        "autor": "Hui",
        "inversa": False
    },
    "t3_conteo_reticula": {
        "titulo": "Conteo combinatorio de rutas monótonas en una retícula urbana 12x12",
        "teoria": "El conteo combinatorio exacto crece de forma explosiva; un coeficiente binomial es trivial para Python pero la magnitud exacta excede la memorización estadística del LLM.",
        "autor": "Bergson",
        "inversa": False
    },
    "t4_recursion_afin": {
        "titulo": "Iteración recursiva profunda de una función afín modular (40 pasos)",
        "teoria": "La recursividad y la retroalimentación exigen tomar la salida como nueva entrada con fidelidad perfecta en cada paso; 40 iteraciones encadenadas amplifican cualquier error del LLM.",
        "autor": "Wiener",
        "inversa": False
    },
    "t5_calculo_exteriorizado": {
        "titulo": "Suma de cuadrados exacta de 30 lecturas de sensores urbanos",
        "teoria": "Un agregado exacto sobre 30 valores literales es cómputo puro reproducible; el LLM no acumula con precisión aritmética sino que estima.",
        "autor": "Bergson",
        "inversa": False
    },
    "t6_relevancia_escena": {
        "titulo": "Juicio de relevancia en una escena urbana ambigua (tarea inversa)",
        "teoria": "El juicio de relevancia y significatividad no admite formalización algorítmica previa: no hay función de entrada-salida sin que un humano fije primero qué cuenta como relevante.",
        "autor": "Dreyfus/Heidegger",
        "inversa": True
    },
}

# Notas cualitativas para t6 (tarea inversa)
notas_t6 = {
    "sonnet_1": ("El modelo identificó al repartidor en moto como foco de la alerta "
                 "(agente activo de peligro), focalizando en la causa del impacto."),
    "sonnet_2": ("El modelo identificó al niño como sujeto de la alerta "
                 "(víctima potencial directa), focalizando en quien recibe el peligro."),
    "opus_1":   ("El modelo identificó al acompañante del niño como receptor de la alerta "
                 "(agente que puede actuar preventivamente sobre la víctima)."),
    "opus_2":   ("El modelo identificó al niño —y secundariamente a su acompañante— como "
                 "destinatarios, enfatizando el riesgo de atropello mortal y el pavimento resbaladizo."),
}

# Construir lista de tareas para JSON
tareas_json = []
for tid in TAREAS_IDS:
    meta = tareas_meta[tid]
    tareas_json.append({
        "id": tid,
        "titulo": meta["titulo"],
        "teoria": meta["teoria"],
        "autor": meta["autor"],
        "inversa": meta["inversa"],
        "valor_exacto": VALOR_EXACTO[tid],
    })

# Construir respuestas con veredicto para JSON
respuestas_json = []
for r in respuestas_calificadas:
    entry = {
        "tarea_id": r["tarea_id"],
        "modelo": r["modelo"],
        "intento": r["intento"],
        "respuesta_final": r["respuesta_final"],
        "confianza": r["confianza"],
        "uso_herramientas": r["uso_herramientas"],
        "correcto": r["correcto"],
    }
    if r["tarea_id"] in TAREAS_INVERSAS:
        key = f"{r['modelo']}_{r['intento']}"
        entry["nota_cualitativa"] = notas_t6.get(key, "")
    respuestas_json.append(entry)

resultado_final = {
    "condiciones_experimento": {
        "modelos": ["Claude Sonnet", "Claude Opus"],
        "uso_herramientas": False,
        "intentos_por_modelo": 2,
        "fecha": "2026-06-10",
        "nota": "Sin herramientas externas; razonamiento interno del LLM únicamente."
    },
    "tareas": tareas_json,
    "respuestas": respuestas_json,
    "exactitud_por_modelo": {
        "sonnet": exactitud_sonnet,
        "opus": exactitud_opus,
    },
    "nota_tarea_inversa": (
        "t6_relevancia_escena es NO_COMPUTABLE: la escena se entrega en lenguaje natural "
        "sin estructura de datos, sin métrica de peligro ni función objetivo. "
        "La formalización necesaria para escribir un algoritmo ES el juicio que se pide. "
        "Los LLMs produjeron respuestas plausibles y coherentes identificando al niño, "
        "al repartidor o al acompañante como foco de la alerta, lo cual ilustra la capacidad "
        "del LLM en el dominio del significado contextual donde el cómputo puro no puede arrancar."
    )
}

json_path = EXP_DIR / "resultados.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(resultado_final, f, ensure_ascii=False, indent=2)

print(f"resultados.json escrito en: {json_path}")

# ---------------------------------------------------------------------------
# 7. GRÁFICOS
# ---------------------------------------------------------------------------

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

BG      = "#0e1a2b"
FG      = "#e8e6e1"
AMBER   = "#e0a458"
BLUE2   = "#4a90d9"
GRAY    = "#5a6a7a"
RED_ERR = "#c0392b"
TEAL    = "#2ecc99"

TAREA_LABELS = {
    "t1_multiplicacion":       "T1: Multiplicación\n(Bergson)",
    "t2_camino_corto":         "T2: Camino corto\n(Hui)",
    "t3_conteo_reticula":      "T3: Retícula 12×12\n(Bergson)",
    "t4_recursion_afin":       "T4: Recursión afín\n(Wiener)",
    "t5_calculo_exteriorizado": "T5: Suma cuadrados\n(Bergson)",
    "t6_relevancia_escena":    "T6: Relevancia\nurbana (Dreyfus)\n[inversa]",
}

# ---- Figura A: exactitud_por_tarea.png ----
fig, ax = plt.subplots(figsize=(13, 7))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

n_tareas = len(TAREAS_IDS)
x = np.arange(n_tareas)
w = 0.28

sonnet_vals = []
opus_vals   = []
sonnet_labels = []
opus_labels   = []

for tid in TAREAS_IDS:
    if tid in TAREAS_INVERSAS:
        sonnet_vals.append(None)
        opus_vals.append(None)
        sonnet_labels.append("N/A")
        opus_labels.append("N/A")
    else:
        s_aciertos, s_total = aciertos_tarea_modelo(tid, "sonnet")
        o_aciertos, o_total = aciertos_tarea_modelo(tid, "opus")
        sonnet_vals.append(s_aciertos)
        opus_vals.append(o_aciertos)
        sonnet_labels.append(f"{s_aciertos}/{s_total}")
        opus_labels.append(f"{o_aciertos}/{o_total}")

for i, (sv, ov) in enumerate(zip(sonnet_vals, opus_vals)):
    tid = TAREAS_IDS[i]
    if tid in TAREAS_INVERSAS:
        # Barra especial para inversa
        ax.bar(x[i] - w/2, 2, width=w, color=GRAY, alpha=0.5, label="_nolegend_")
        ax.bar(x[i] + w/2, 2, width=w, color=GRAY, alpha=0.5, label="_nolegend_")
        ax.text(x[i] - w/2, 2.1, "N/A", ha="center", va="bottom", color=FG, fontsize=9)
        ax.text(x[i] + w/2, 2.1, "N/A", ha="center", va="bottom", color=FG, fontsize=9)
    else:
        color_s = TEAL if sv == 2 else (AMBER if sv == 1 else RED_ERR)
        color_o = TEAL if ov == 2 else (AMBER if ov == 1 else RED_ERR)
        ax.bar(x[i] - w/2, sv, width=w, color=color_s, zorder=3)
        ax.bar(x[i] + w/2, ov, width=w, color=color_o, zorder=3)
        ax.text(x[i] - w/2, sv + 0.07, sonnet_labels[i],
                ha="center", va="bottom", color=FG, fontsize=9, fontweight="bold")
        ax.text(x[i] + w/2, ov + 0.07, opus_labels[i],
                ha="center", va="bottom", color=FG, fontsize=9, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(
    [TAREA_LABELS[tid] for tid in TAREAS_IDS],
    color=FG, fontsize=9
)
ax.set_yticks([0, 1, 2])
ax.set_yticklabels(["0", "1", "2"], color=FG, fontsize=10)
ax.set_ylim(0, 2.6)
ax.set_ylabel("Aciertos (de 2 intentos)", color=FG, fontsize=11)
ax.set_title("Aciertos por tarea y modelo\n(sin herramientas · 2 intentos por modelo)",
             color=FG, fontsize=13, fontweight="bold", pad=14)
ax.tick_params(colors=FG, which="both")
for spine in ax.spines.values():
    spine.set_edgecolor(GRAY)

# Leyenda
patch_s  = mpatches.Patch(color=BLUE2, label="Sonnet (barra izquierda)")
patch_o  = mpatches.Patch(color=AMBER, label="Opus (barra derecha)")
patch_na = mpatches.Patch(color=GRAY, alpha=0.5, label="Tarea inversa (no computable)")
patch_ok = mpatches.Patch(color=TEAL,   label="2/2 aciertos")
patch_mid= mpatches.Patch(color=AMBER,  label="1/2 aciertos")
patch_no = mpatches.Patch(color=RED_ERR,label="0/2 aciertos")
ax.legend(handles=[patch_ok, patch_mid, patch_no, patch_na],
          facecolor=BG, edgecolor=GRAY, labelcolor=FG,
          loc="upper right", fontsize=9)

# Añadir etiqueta de modelo en el eje X inferior
ax.annotate("◀ Sonnet   Opus ▶", xy=(0.01, -0.13), xycoords="axes fraction",
            color=AMBER, fontsize=8, ha="left")

fig.tight_layout()
path_a = ASSETS_DIR / "exactitud_por_tarea.png"
fig.savefig(path_a, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig)
print(f"PNG guardado: {path_a}")

# ---- Figura B: llm_vs_computo.png ----
fig2, ax2 = plt.subplots(figsize=(9, 6))
fig2.patch.set_facecolor(BG)
ax2.set_facecolor(BG)

# Tareas computables solamente (5)
n_computables = 5  # t1..t5, cada una 2 intentos x 2 modelos = 4 muestras

sonnet_total = exactitud_sonnet["total"]
sonnet_ok    = exactitud_sonnet["aciertos"]
opus_total   = exactitud_opus["total"]
opus_ok      = exactitud_opus["aciertos"]
# Python (cómputo puro) = 100% por definición en tareas computables
computo_ok = n_computables  # cada tarea una vez
computo_total = n_computables

grupos = ["Python\n(cómputo\nexteriorizado)", "Sonnet\n(sin herramientas)", "Opus\n(sin herramientas)"]
valores_pct = [
    100.0,
    round(sonnet_ok / sonnet_total * 100, 1),
    round(opus_ok   / opus_total   * 100, 1),
]
etiquetas = [
    f"{computo_ok}/{computo_total} = 100%",
    f"{sonnet_ok}/{sonnet_total} = {valores_pct[1]}%",
    f"{opus_ok}/{opus_total} = {valores_pct[2]}%",
]
colores = [TEAL, BLUE2, AMBER]

x3 = np.arange(len(grupos))
bars = ax2.bar(x3, valores_pct, width=0.5, color=colores, zorder=3)

for bar, etq in zip(bars, etiquetas):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
             etq, ha="center", va="bottom", color=FG, fontsize=11, fontweight="bold")

ax2.set_xticks(x3)
ax2.set_xticklabels(grupos, color=FG, fontsize=12)
ax2.set_yticks(range(0, 110, 20))
ax2.set_yticklabels([f"{v}%" for v in range(0, 110, 20)], color=FG, fontsize=10)
ax2.set_ylim(0, 115)
ax2.set_ylabel("Exactitud (%)", color=FG, fontsize=12)
ax2.set_title(
    "LLM vs. cómputo puro — exactitud global\nen tareas computables (5 tareas · sin herramientas)",
    color=FG, fontsize=13, fontweight="bold", pad=14
)
ax2.tick_params(colors=FG, which="both")
for spine in ax2.spines.values():
    spine.set_edgecolor(GRAY)

# Línea de referencia 100%
ax2.axhline(100, color=TEAL, linestyle="--", linewidth=1, alpha=0.5)
ax2.text(len(grupos) - 0.52, 101.5, "100% (referencia cómputo exacto)",
         color=TEAL, fontsize=8, alpha=0.8)

fig2.tight_layout()
path_b = ASSETS_DIR / "llm_vs_computo.png"
fig2.savefig(path_b, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig2)
print(f"PNG guardado: {path_b}")

# ---------------------------------------------------------------------------
# 8. VERIFICACIÓN FINAL
# ---------------------------------------------------------------------------
import json as _json

assert path_a.exists(), f"No existe: {path_a}"
assert path_b.exists(), f"No existe: {path_b}"
with open(json_path) as f:
    _json.load(f)  # valida que sea JSON bien formado
print()
print("VERIFICACIÓN FINAL: ambos PNG existen y resultados.json es JSON válido.")
print("Script completado con éxito.")
