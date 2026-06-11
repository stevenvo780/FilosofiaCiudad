"""
Extiende resultados.json con los sujetos locales de kratos y regenera los 3 PNG.
Fecha: 2026-06-10
"""

import json
import math
import heapq
from pathlib import Path

BASE      = Path("/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad")
EXP_DIR   = BASE / "03_Trabajos/Ponencia_Yuk_Hui/experimento"
ASSETS_DIR= BASE / "03_Trabajos/Ponencia_Yuk_Hui/presentacion/assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. VALORES EXACTOS (misma lógica que experimento.py)
# ---------------------------------------------------------------------------

def calcular_t1():
    return str(387465129847 * 902341765893)

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
    camino = []
    nodo = fin
    while nodo is not None:
        camino.append(nodo)
        nodo = prev[nodo]
    camino.reverse()
    return ", ".join(camino)

def calcular_t3():
    return str(math.comb(24, 12))

def calcular_t4():
    A, B, M = 137, 991, 100000
    x = 42
    for _ in range(40):
        x = (A * x + B) % M
    return str(x)

def calcular_t5():
    lecturas = [
        4821, 3990, 5172, 4408, 3765, 6011, 2987, 5540, 4123, 3876,
        5298, 4710, 3654, 6102, 2890, 5471, 4019, 3788, 5630, 4255,
        3912, 6044, 2976, 5388, 4187, 3801, 5519, 4630, 3745, 6088
    ]
    return str(sum(x * x for x in lecturas))

VALOR_EXACTO = {
    "t1_multiplicacion":        calcular_t1(),
    "t2_camino_corto":          calcular_t2(),
    "t3_conteo_reticula":       calcular_t3(),
    "t4_recursion_afin":        calcular_t4(),
    "t5_calculo_exteriorizado": calcular_t5(),
    "t6_relevancia_escena":     "NO_COMPUTABLE",
}

TAREAS_INVERSAS = {"t6_relevancia_escena"}
TAREAS_IDS = [
    "t1_multiplicacion", "t2_camino_corto", "t3_conteo_reticula",
    "t4_recursion_afin", "t5_calculo_exteriorizado", "t6_relevancia_escena"
]

# Verify
assert VALOR_EXACTO["t1_multiplicacion"] == "349625969488102520908371"
assert VALOR_EXACTO["t2_camino_corto"] == "Altavista, Bellavista, Cumbres, Esmeralda, Horizonte, Jacaranda, Lagos, Tejar, Yarumal, Zafiro"
assert VALOR_EXACTO["t3_conteo_reticula"] == "2704156"
assert VALOR_EXACTO["t4_recursion_afin"] == "23842"
assert VALOR_EXACTO["t5_calculo_exteriorizado"] == "651396404"
print("Valores exactos verificados.")

# ---------------------------------------------------------------------------
# 2. NORMALIZACIÓN (misma que experimento.py)
# ---------------------------------------------------------------------------

def normalizar(s: str) -> str:
    """Strip, colapsa espacios internos, elimina separadores de miles (coma o punto
    cuando aparecen como separadores de grupos de 3 dígitos), colapsa mayúsculas
    para comparación de strings puramente numéricos. Para listas de nodos se
    compara tal cual (strip)."""
    return s.strip()

def calificar_respuesta(tarea_id: str, respuesta_final: str):
    """Retorna True/False para tareas computables, 'NO_APLICA' para la inversa."""
    if tarea_id in TAREAS_INVERSAS:
        return "NO_APLICA"
    if respuesta_final in ("SIN_RESPUESTA", "ERROR", ""):
        return False
    valor_ref = VALOR_EXACTO[tarea_id]
    return normalizar(respuesta_final) == normalizar(valor_ref)

# ---------------------------------------------------------------------------
# 3. CARGAR respuestas_kratos.json y construir entradas
# ---------------------------------------------------------------------------

kratos_path = EXP_DIR / "respuestas_kratos.json"
with open(kratos_path, encoding="utf-8") as f:
    kratos_raw = json.load(f)

MODELOS_LOCALES = ["qwen2.5:3b", "qwen3:14b", "gpt-oss:20b", "qwen3:32b"]

# Notas cualitativas para t6 en sujetos locales
NOTAS_T6_LOCALES = {
    "qwen2.5:3b_1": "Respuesta vaga: alerta genérica al grupo en el cruce, sin identificar un destinatario específico ni jerarquizar el peligro.",
    "qwen2.5:3b_2": "Identificó al niño como destinatario de la alerta; respuesta esquemática con marcadores HTML no solicitados.",
    "qwen3:14b_1":  "Identificó a la mujer mayor como destinataria principal; la escena menciona un niño y un repartidor, no una mujer mayor — alucinación de entidad.",
    "qwen3:14b_2":  "Identificó al repartidor en moto como destinatario; coherente con la lectura de agente activo de peligro.",
    "gpt-oss:20b_1": "Identificó al niño que cruza como destinatario; respuesta muy concisa, sin razonamiento adicional.",
    "gpt-oss:20b_2": "Identificó al niño que cruza como destinatario; idéntica respuesta en los dos intentos (convergencia plana).",
    "qwen3:32b_1":  "OMITIDO: timed out (605 s) — tarea no completada.",
    "qwen3:32b_2":  "OMITIDO: datos ausentes en respuestas_kratos.json — tarea no recogida.",
}

# Construir lista de respuestas locales con veredicto
respuestas_locales = []

for modelo in MODELOS_LOCALES:
    for tarea_id in TAREAS_IDS:
        for intento in [1, 2]:
            key = f"{modelo}|{tarea_id}|{intento}"
            if key not in kratos_raw:
                # Datos ausentes -> registrar como omisión
                if tarea_id in TAREAS_INVERSAS:
                    correcto = "NO_APLICA"
                    nota_q = NOTAS_T6_LOCALES.get(f"{modelo}_{intento}", "OMITIDO: sin dato en respuestas_kratos.json.")
                    entry = {
                        "tarea_id": tarea_id,
                        "modelo": modelo,
                        "intento": intento,
                        "respuesta_final": "OMITIDO",
                        "confianza": None,
                        "uso_herramientas": False,
                        "correcto": correcto,
                        "nota_cualitativa": nota_q,
                        "omision": True,
                        "razon_omision": "Datos ausentes en respuestas_kratos.json",
                    }
                else:
                    entry = {
                        "tarea_id": tarea_id,
                        "modelo": modelo,
                        "intento": intento,
                        "respuesta_final": "OMITIDO",
                        "confianza": None,
                        "uso_herramientas": False,
                        "correcto": False,
                        "omision": True,
                        "razon_omision": "Datos ausentes en respuestas_kratos.json",
                    }
                respuestas_locales.append(entry)
                print(f"  OMITIDO  {tarea_id:30s}  {modelo:15s}  intento {intento}")
                continue

            datos = kratos_raw[key]
            rf = datos.get("respuesta_final", "SIN_RESPUESTA")
            nota_raw = datos.get("nota", "")
            elapsed = datos.get("elapsed_s", None)

            if tarea_id in TAREAS_INVERSAS:
                correcto = "NO_APLICA"
                nota_q = NOTAS_T6_LOCALES.get(f"{modelo}_{intento}", rf)
                # Detectar timeout
                if rf in ("ERROR", "SIN_RESPUESTA") and elapsed and elapsed > 300:
                    nota_q = NOTAS_T6_LOCALES.get(f"{modelo}_{intento}", "OMITIDO: timed out.")
                entry = {
                    "tarea_id": tarea_id,
                    "modelo": modelo,
                    "intento": intento,
                    "respuesta_final": rf,
                    "confianza": None,
                    "uso_herramientas": False,
                    "correcto": correcto,
                    "nota_cualitativa": nota_q,
                }
                if elapsed:
                    entry["elapsed_s"] = elapsed
            else:
                # Detectar timeout / error explícito
                if rf in ("ERROR", "SIN_RESPUESTA") and elapsed and elapsed > 300:
                    correcto = False
                    omision = True
                    razon = f"Timed out ({elapsed} s) — sin respuesta registrada."
                    entry = {
                        "tarea_id": tarea_id,
                        "modelo": modelo,
                        "intento": intento,
                        "respuesta_final": rf,
                        "confianza": None,
                        "uso_herramientas": False,
                        "correcto": correcto,
                        "omision": True,
                        "razon_omision": razon,
                        "elapsed_s": elapsed,
                    }
                else:
                    correcto = calificar_respuesta(tarea_id, rf)
                    entry = {
                        "tarea_id": tarea_id,
                        "modelo": modelo,
                        "intento": intento,
                        "respuesta_final": rf,
                        "confianza": None,
                        "uso_herramientas": False,
                        "correcto": correcto,
                    }
                    if elapsed:
                        entry["elapsed_s"] = elapsed

            respuestas_locales.append(entry)
            print(f"  {tarea_id:30s}  {modelo:15s}  intento {intento}  -> {correcto}")

# ---------------------------------------------------------------------------
# 4. EXACTITUD AGREGADA POR MODELO LOCAL
# ---------------------------------------------------------------------------

def exactitud_modelo_lista(modelo, respuestas):
    total = 0
    aciertos = 0
    for r in respuestas:
        if r["modelo"] == modelo and r.get("correcto") not in ("NO_APLICA",):
            total += 1
            if r["correcto"] is True:
                aciertos += 1
    pct = round(aciertos / total * 100, 2) if total > 0 else 0.0
    return {"aciertos": aciertos, "total": total, "porcentaje": pct}

exactitud_local = {}
for m in MODELOS_LOCALES:
    exactitud_local[m] = exactitud_modelo_lista(m, respuestas_locales)
    print(f"  {m}: {exactitud_local[m]['aciertos']}/{exactitud_local[m]['total']} ({exactitud_local[m]['porcentaje']}%)")

# ---------------------------------------------------------------------------
# 5. CARGAR resultados.json EXISTENTE Y EXTENDER
# ---------------------------------------------------------------------------

json_path = EXP_DIR / "resultados.json"
with open(json_path, encoding="utf-8") as f:
    datos = json.load(f)

# Añadir condiciones locales
datos["condiciones_experimento"]["modelos_locales"] = MODELOS_LOCALES
datos["condiciones_experimento"]["ejecucion_local"] = {
    "plataforma": "kratos",
    "ollama_version": "0.24",
    "hardware": "RTX 5070 Ti 16 GB",
    "temperature": 0.2,
    "herramientas": False,
    "intentos_por_modelo": 2,
    "nota": "Sin herramientas por construcción (ollama no expone llamadas a herramientas en este modo); razonamiento interno únicamente."
}

# Omisiones registradas
omisiones = [r for r in respuestas_locales if r.get("omision")]
if omisiones:
    datos["condiciones_experimento"]["omisiones"] = [
        {
            "modelo": r["modelo"],
            "tarea_id": r["tarea_id"],
            "intento": r["intento"],
            "razon": r.get("razon_omision", r.get("nota_cualitativa", "sin datos")),
        }
        for r in omisiones
    ]

# Añadir respuestas locales (sin omision key en el JSON final para limpieza)
respuestas_locales_limpias = []
for r in respuestas_locales:
    e = {k: v for k, v in r.items() if k not in ("omision", "razon_omision")}
    respuestas_locales_limpias.append(e)

datos["respuestas"].extend(respuestas_locales_limpias)

# Añadir exactitud
for m in MODELOS_LOCALES:
    clave = m.replace(":", "_").replace(".", "_")
    datos["exactitud_por_modelo"][clave] = exactitud_local[m]

# Guardar
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)
print(f"\nresultados.json extendido y guardado: {json_path}")

# Validar que sigue siendo JSON válido
with open(json_path, encoding="utf-8") as f:
    _check = json.load(f)
print("resultados.json: JSON válido.")

# ---------------------------------------------------------------------------
# 6. GRÁFICOS
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
PURPLE  = "#a78bfa"
ORANGE  = "#f97316"

TAREA_LABELS = {
    "t1_multiplicacion":        "T1: Multiplicación\n(Bergson)",
    "t2_camino_corto":          "T2: Camino corto\n(Hui)",
    "t3_conteo_reticula":       "T3: Retícula 12×12\n(Bergson)",
    "t4_recursion_afin":        "T4: Recursión afín\n(Wiener)",
    "t5_calculo_exteriorizado": "T5: Suma cuadrados\n(Bergson)",
    "t6_relevancia_escena":     "T6: Relevancia\nurbana (Dreyfus)\n[inversa]",
}

# Todos los modelos en orden canónico
TODOS_MODELOS = ["qwen2.5:3b", "qwen3:14b", "gpt-oss:20b", "qwen3:32b", "sonnet", "opus"]
LABELS_MODELOS = {
    "qwen2.5:3b":  "Qwen2.5\n3B",
    "qwen3:14b":   "Qwen3\n14B",
    "gpt-oss:20b": "GPT-OSS\n20B",
    "qwen3:32b":   "Qwen3\n32B",
    "sonnet":      "Claude\nSonnet",
    "opus":        "Claude\nOpus",
}
COLORES_MODELOS = {
    "qwen2.5:3b":  "#6ee7b7",
    "qwen3:14b":   "#34d399",
    "gpt-oss:20b": "#f97316",
    "qwen3:32b":   "#a78bfa",
    "sonnet":      "#4a90d9",
    "opus":        "#e0a458",
}

# Helper: aciertos para un (tarea, modelo) sobre todas las respuestas
todas_respuestas = datos["respuestas"]

def aciertos_tm(tarea_id, modelo):
    filas = [r for r in todas_respuestas if r["tarea_id"] == tarea_id and r["modelo"] == modelo]
    if not filas:
        return None, 0
    if tarea_id in TAREAS_INVERSAS:
        return "NO_APLICA", len(filas)
    total = len(filas)
    aciertos = sum(1 for r in filas if r.get("correcto") is True)
    return aciertos, total

# ----------------------------------------------------------------
# Figura A: exactitud_por_tarea.png  (todos los modelos)
# ----------------------------------------------------------------

n_tareas = len(TAREAS_IDS)
n_modelos = len(TODOS_MODELOS)
x_pos = np.arange(n_tareas)
total_width = 0.82
w = total_width / n_modelos

fig, ax = plt.subplots(figsize=(16, 7))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

for mi, modelo in enumerate(TODOS_MODELOS):
    offset = (mi - (n_modelos - 1) / 2) * w
    for ti, tarea_id in enumerate(TAREAS_IDS):
        aciertos, total = aciertos_tm(tarea_id, modelo)
        if aciertos == "NO_APLICA":
            ax.bar(x_pos[ti] + offset, 2, width=w * 0.9,
                   color=GRAY, alpha=0.35, zorder=2)
            ax.text(x_pos[ti] + offset, 2.08, "N/A",
                    ha="center", va="bottom", color=FG, fontsize=6.5)
        elif aciertos is None:
            # Omisión completa
            ax.bar(x_pos[ti] + offset, 0, width=w * 0.9,
                   color=GRAY, alpha=0.2, zorder=2, linestyle="--", edgecolor=GRAY)
        else:
            color = TEAL if aciertos == 2 else (AMBER if aciertos == 1 else RED_ERR)
            ax.bar(x_pos[ti] + offset, aciertos, width=w * 0.9,
                   color=color, zorder=3, label="_nolegend_")
            label_txt = f"{aciertos}/{total}" if total > 0 else "—"
            ax.text(x_pos[ti] + offset, aciertos + 0.06, label_txt,
                    ha="center", va="bottom", color=FG, fontsize=6.5, fontweight="bold")

ax.set_xticks(x_pos)
ax.set_xticklabels([TAREA_LABELS[t] for t in TAREAS_IDS], color=FG, fontsize=9)
ax.set_yticks([0, 1, 2])
ax.set_yticklabels(["0", "1", "2"], color=FG, fontsize=10)
ax.set_ylim(0, 2.75)
ax.set_ylabel("Aciertos (de 2 intentos)", color=FG, fontsize=11)
ax.set_title(
    "Aciertos por tarea y modelo — todos los sujetos\n(sin herramientas · 2 intentos · local kratos + API Anthropic)",
    color=FG, fontsize=13, fontweight="bold", pad=14
)
ax.tick_params(colors=FG, which="both")
for spine in ax.spines.values():
    spine.set_edgecolor(GRAY)

# Leyenda modelos
patches_m = [mpatches.Patch(color=COLORES_MODELOS[m], label=LABELS_MODELOS[m].replace("\n", " "))
             for m in TODOS_MODELOS]
patches_score = [
    mpatches.Patch(color=TEAL,    label="2/2 aciertos"),
    mpatches.Patch(color=AMBER,   label="1/2 aciertos"),
    mpatches.Patch(color=RED_ERR, label="0/2 aciertos"),
    mpatches.Patch(color=GRAY, alpha=0.4, label="Tarea inversa / omitida"),
]
leg1 = ax.legend(handles=patches_m, facecolor=BG, edgecolor=GRAY, labelcolor=FG,
                 loc="upper left", fontsize=8, title="Modelos", title_fontsize=8)
leg1.get_title().set_color(AMBER)
ax.add_artist(leg1)
ax.legend(handles=patches_score, facecolor=BG, edgecolor=GRAY, labelcolor=FG,
          loc="upper right", fontsize=8)

# Anotación orden barras
order_txt = "  ".join([f"{'▐' if i==0 else '|'}{LABELS_MODELOS[m].replace(chr(10),' ')}"
                       for i, m in enumerate(TODOS_MODELOS)])
ax.annotate(f"Orden de barras (izq→der): {' | '.join(LABELS_MODELOS[m].replace(chr(10),' ') for m in TODOS_MODELOS)}",
            xy=(0.0, -0.14), xycoords="axes fraction",
            color=AMBER, fontsize=7.5, ha="left")

fig.tight_layout()
path_a = ASSETS_DIR / "exactitud_por_tarea.png"
fig.savefig(path_a, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig)
print(f"PNG guardado: {path_a}")

# ----------------------------------------------------------------
# Figura B: llm_vs_computo.png  (exactitud global por modelo)
# ----------------------------------------------------------------

fig2, ax2 = plt.subplots(figsize=(12, 6))
fig2.patch.set_facecolor(BG)
ax2.set_facecolor(BG)

# Exactitud de Python/cómputo puro = 100% en las 5 tareas computables
grupos_b = ["Python\n(cómputo\nexteriorizado)"] + [LABELS_MODELOS[m] for m in TODOS_MODELOS]
colores_b = [TEAL] + [COLORES_MODELOS[m] for m in TODOS_MODELOS]

# Exactitud API
exactitud_api = {
    "sonnet": datos["exactitud_por_modelo"]["sonnet"],
    "opus":   datos["exactitud_por_modelo"]["opus"],
}

def pct_modelo(modelo):
    clave = modelo.replace(":", "_").replace(".", "_")
    if clave in datos["exactitud_por_modelo"]:
        d = datos["exactitud_por_modelo"][clave]
    elif modelo in datos["exactitud_por_modelo"]:
        d = datos["exactitud_por_modelo"][modelo]
    else:
        return 0.0, 0, 0
    return d["porcentaje"], d["aciertos"], d["total"]

valores_pct_b = [100.0]
etiquetas_b   = ["5/5 = 100%"]
for m in TODOS_MODELOS:
    pct, ok, tot = pct_modelo(m)
    valores_pct_b.append(pct)
    etiquetas_b.append(f"{ok}/{tot} = {pct}%")

x3 = np.arange(len(grupos_b))
bars = ax2.bar(x3, valores_pct_b, width=0.55, color=colores_b, zorder=3)

for bar, etq in zip(bars, etiquetas_b):
    ax2.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + 1.5,
             etq, ha="center", va="bottom", color=FG, fontsize=9.5, fontweight="bold")

ax2.set_xticks(x3)
ax2.set_xticklabels(grupos_b, color=FG, fontsize=10)
ax2.set_yticks(range(0, 110, 20))
ax2.set_yticklabels([f"{v}%" for v in range(0, 110, 20)], color=FG, fontsize=10)
ax2.set_ylim(0, 120)
ax2.set_ylabel("Exactitud (%)", color=FG, fontsize=12)
ax2.set_title(
    "LLM vs. cómputo puro — exactitud global en tareas computables\n"
    "(5 tareas · 2 intentos · sin herramientas · todos los sujetos)",
    color=FG, fontsize=13, fontweight="bold", pad=14
)
ax2.tick_params(colors=FG, which="both")
for spine in ax2.spines.values():
    spine.set_edgecolor(GRAY)

# Línea referencia 100%
ax2.axhline(100, color=TEAL, linestyle="--", linewidth=1, alpha=0.6)
ax2.text(len(grupos_b) - 0.52, 101.5, "100% — referencia cómputo exacto",
         color=TEAL, fontsize=8, alpha=0.85)

fig2.tight_layout()
path_b = ASSETS_DIR / "llm_vs_computo.png"
fig2.savefig(path_b, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig2)
print(f"PNG guardado: {path_b}")

# ----------------------------------------------------------------
# Figura C: escala_vs_exactitud.png
# ----------------------------------------------------------------
# Orden eje x: qwen2.5:3b, qwen3:14b, gpt-oss:20b, qwen3:32b, Claude Sonnet, Claude Opus
# Eje y: exactitud en tareas computables (excluida t6)

fig3, ax3 = plt.subplots(figsize=(11, 6))
fig3.patch.set_facecolor(BG)
ax3.set_facecolor(BG)

eje_x_modelos = ["qwen2.5:3b", "qwen3:14b", "gpt-oss:20b", "qwen3:32b", "sonnet", "opus"]
eje_x_labels  = [
    "Qwen2.5\n3B\n(local)",
    "Qwen3\n14B\n(local)",
    "GPT-OSS\n20B\n(local)",
    "Qwen3\n32B\n(local)",
    "Claude\nSonnet\n(API)",
    "Claude\nOpus\n(API)",
]

vals_c = []
etqs_c = []
for m in eje_x_modelos:
    pct, ok, tot = pct_modelo(m)
    vals_c.append(pct)
    etqs_c.append(f"{ok}/{tot}\n= {pct}%")

x_c = np.arange(len(eje_x_modelos))
colores_c = [COLORES_MODELOS[m] for m in eje_x_modelos]

# Barras
bars_c = ax3.bar(x_c, vals_c, width=0.55, color=colores_c, zorder=3, alpha=0.92)
for bar, etq in zip(bars_c, etqs_c):
    ax3.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + 1.2,
             etq, ha="center", va="bottom", color=FG, fontsize=9, fontweight="bold")

# Línea de tendencia
ax3.plot(x_c, vals_c, color=AMBER, linewidth=2, marker="o",
         markersize=7, zorder=4, label="Exactitud observada")

# Línea referencia 100%
ax3.axhline(100, color=TEAL, linestyle="--", linewidth=1.5, alpha=0.7, label="Cómputo puro = 100%")
ax3.text(len(eje_x_modelos) - 0.55, 101.5,
         "Cómputo puro = 100%", color=TEAL, fontsize=8.5, alpha=0.9)

ax3.set_xticks(x_c)
ax3.set_xticklabels(eje_x_labels, color=FG, fontsize=10)
ax3.set_yticks(range(0, 110, 20))
ax3.set_yticklabels([f"{v}%" for v in range(0, 110, 20)], color=FG, fontsize=10)
ax3.set_ylim(0, 120)
ax3.set_xlabel("Modelo (escala creciente, local → API)", color=FG, fontsize=11)
ax3.set_ylabel("Exactitud en tareas computables (%)", color=FG, fontsize=11)
ax3.set_title(
    "Escala vs. exactitud en tareas computables\n"
    "(excluida tarea inversa t6 · sin herramientas · 2 intentos)",
    color=FG, fontsize=13, fontweight="bold", pad=14
)
ax3.tick_params(colors=FG, which="both")
for spine in ax3.spines.values():
    spine.set_edgecolor(GRAY)

ax3.legend(facecolor=BG, edgecolor=GRAY, labelcolor=FG, fontsize=9, loc="upper left")

fig3.tight_layout()
path_c = ASSETS_DIR / "escala_vs_exactitud.png"
fig3.savefig(path_c, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig3)
print(f"PNG guardado: {path_c}")

# ---------------------------------------------------------------------------
# 7. VERIFICACIÓN FINAL
# ---------------------------------------------------------------------------
assert path_a.exists(), f"No existe: {path_a}"
assert path_b.exists(), f"No existe: {path_b}"
assert path_c.exists(), f"No existe: {path_c}"
with open(json_path, encoding="utf-8") as f:
    json.load(f)  # JSON válido

print()
print("VERIFICACIÓN FINAL:")
print(f"  {path_a}  OK")
print(f"  {path_b}  OK")
print(f"  {path_c}  OK")
print("  resultados.json: JSON válido")
print("Script completado con éxito.")
