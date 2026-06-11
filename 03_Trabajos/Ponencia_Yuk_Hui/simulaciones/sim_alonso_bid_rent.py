"""
Simulacion del modelo Bid-Rent urbano de William Alonso (1964)

Formulacion:
    Cada grupo tiene una funcion de puja lineal R_g(d) = R0_g - k_g * d
    El suelo se asigna al mejor postor: argmax_g R_g(d)
    Frontera i,j: d* = (R0_i - R0_j) / (k_i - k_j)

Experimento (deterministico, sin semilla aleatoria):
    Grupo POBRE: R(d) = 500 - 20*d
    Grupo RICO:  R(d) = 300 - 5*d
    d en [0, 30] km, paso 0.1 km

Verificacion:
    d* = (500 - 300) / (20 - 5) = 200 / 15 = 13.3333... km
    Renta en d*: R(13.33) = 500 - 20*13.33 = 233.33
    Pobres ocupan d < 13.33, ricos d > 13.33
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# 1. Parametros del modelo (deterministico — sin numpy.random)
# ---------------------------------------------------------------------------
D_MIN = 0.0
D_MAX = 30.0
D_STEP = 0.1

grupos = {
    "pobre": {"R0": 500.0, "k": 20.0, "label": "Grupo Pobre", "color": "#e07b54"},
    "rico":  {"R0": 300.0, "k":  5.0, "label": "Grupo Rico",  "color": "#5ba4cf"},
}

# ---------------------------------------------------------------------------
# 2. Evaluacion de funciones de puja
# ---------------------------------------------------------------------------
d = np.arange(D_MIN, D_MAX + D_STEP, D_STEP)  # shape (301,)

R = {}
for nombre, g in grupos.items():
    R[nombre] = g["R0"] - g["k"] * d

# Envolvente de pujas (mejor postor en cada d)
envoltura = np.maximum(R["pobre"], R["rico"])

# Asignacion: 0 = pobre gana, 1 = rico gana
# Empate (d = d*) se asigna a pobre por >= (primer argmax es consistente)
asignacion = np.where(R["pobre"] >= R["rico"], "pobre", "rico")

# ---------------------------------------------------------------------------
# 3. Calculo analitico del punto de cruce
# ---------------------------------------------------------------------------
R0_p, k_p = grupos["pobre"]["R0"], grupos["pobre"]["k"]
R0_r, k_r = grupos["rico"]["R0"],  grupos["rico"]["k"]

d_star = (R0_p - R0_r) / (k_p - k_r)          # 13.3333... km
renta_cruce = R0_p - k_p * d_star              # 233.3333...

# ---------------------------------------------------------------------------
# 4. Respuestas a las preguntas
# ---------------------------------------------------------------------------
# Pregunta 1: distancia de cruce analitica
resp_p1 = d_star                                # 13.333...

# Pregunta 2: puja del grupo rico a d = 20 km
resp_p2 = R0_r - k_r * 20.0                    # 200.0

# Pregunta 3: fraccion del intervalo [0, 30] ocupada por pobres (simulacion)
n_total = len(d)
n_pobre = int(np.sum(asignacion == "pobre"))
fraccion_pobre = n_pobre / n_total              # ~0.444

# ---------------------------------------------------------------------------
# 5. Guardar datos crudos en JSON
# ---------------------------------------------------------------------------
SIMULACIONES_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(SIMULACIONES_DIR, "datos_alonso_bid_rent.json")

datos = {
    "teoria": "alonso_bid_rent",
    "autor": "William Alonso",
    "anio": "1964",
    "parametros": {
        "d_min_km": D_MIN,
        "d_max_km": D_MAX,
        "d_step_km": D_STEP,
        "grupos": {
            "pobre": {"R0": R0_p, "k": k_p},
            "rico":  {"R0": R0_r, "k": k_r},
        },
    },
    "resultados_analiticos": {
        "d_star_km": round(d_star, 6),
        "renta_en_cruce": round(renta_cruce, 6),
    },
    "simulacion": {
        "n_puntos": n_total,
        "n_puntos_pobre": n_pobre,
        "n_puntos_rico": n_total - n_pobre,
        "fraccion_pobre": round(fraccion_pobre, 6),
        "fraccion_rico": round(1.0 - fraccion_pobre, 6),
    },
    "verificacion": {
        "R_pobre_en_d0": float(R["pobre"][0]),
        "R_rico_en_d0":  float(R["rico"][0]),
        "R_pobre_mayor_en_centro": bool(R["pobre"][0] > R["rico"][0]),
        "envoltura_monotona_decreciente": bool(
            np.all(np.diff(envoltura) <= 0.0 + 1e-9)
        ),
        "grupo_interior_es_pobre": bool(asignacion[0] == "pobre"),
    },
    "series": {
        "d_km":      d.tolist(),
        "R_pobre":   R["pobre"].tolist(),
        "R_rico":    R["rico"].tolist(),
        "envoltura": envoltura.tolist(),
        "asignacion": asignacion.tolist(),
    },
}

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)

print(f"Datos guardados en: {json_path}")

# ---------------------------------------------------------------------------
# 6. Grafica principal — PNG 1
# ---------------------------------------------------------------------------
ASSETS_DIR = os.path.join(
    SIMULACIONES_DIR,
    "..", "presentacion", "assets", "sim"
)
ASSETS_DIR = os.path.normpath(ASSETS_DIR)
os.makedirs(ASSETS_DIR, exist_ok=True)

BG      = "#0e1a2b"
TEXT    = "#e8e6e1"
AMBER   = "#e0a458"
POBRE_C = "#e07b54"   # naranja-rojo
RICO_C  = "#5ba4cf"   # azul-gris
ENV_C   = AMBER       # envolvente en ambar

fig, ax = plt.subplots(figsize=(11, 7))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# --- Areas sombreadas por grupo ---
ax.fill_between(
    d, envoltura, alpha=0.15, color=POBRE_C,
    where=(asignacion == "pobre"),
    label="_nolegend_"
)
ax.fill_between(
    d, envoltura, alpha=0.15, color=RICO_C,
    where=(asignacion == "rico"),
    label="_nolegend_"
)

# --- Curvas individuales ---
ax.plot(d, R["pobre"], color=POBRE_C, lw=2.0,
        linestyle="--", label="Grupo Pobre: $R(d)=500-20d$", alpha=0.85)
ax.plot(d, R["rico"],  color=RICO_C,  lw=2.0,
        linestyle="--", label="Grupo Rico: $R(d)=300-5d$",   alpha=0.85)

# --- Envolvente (mejor postor) ---
ax.plot(d, envoltura, color=ENV_C, lw=3.0,
        label="Envolvente (mejor postor)", zorder=5)

# --- Punto de cruce d* ---
ax.axvline(x=d_star, color=TEXT, lw=1.2, linestyle=":", alpha=0.7)
ax.scatter([d_star], [renta_cruce], color=AMBER, s=90, zorder=10)
ax.annotate(
    f"$d^*$ = {d_star:.2f} km\nRenta = {renta_cruce:.2f}",
    xy=(d_star, renta_cruce),
    xytext=(d_star + 1.5, renta_cruce + 40),
    color=TEXT, fontsize=9,
    arrowprops=dict(arrowstyle="->", color=TEXT, lw=1.0),
)

# --- Etiquetas de zona ---
ax.text(d_star / 2, 50, "Pobres\n(centro)", ha="center", va="bottom",
        color=POBRE_C, fontsize=10, fontweight="bold")
ax.text((d_star + D_MAX) / 2, 50, "Ricos\n(periferia)", ha="center", va="bottom",
        color=RICO_C, fontsize=10, fontweight="bold")

# --- Nota contraintuitiva ---
ax.text(
    0.02, 0.97,
    "Inversion contraintuitiva: los pobres pujan mas por el centro\n"
    "por su mayor dependencia del acceso al CBD (gradiente pronunciado).",
    transform=ax.transAxes, color=AMBER, fontsize=8.5,
    va="top", ha="left",
    bbox=dict(facecolor=BG, edgecolor=AMBER, alpha=0.7, boxstyle="round,pad=0.3"),
)

# --- Ejes y formato ---
ax.set_xlim(0, 30)
ax.set_ylim(-50, 550)
ax.set_xlabel("Distancia al CBD (km)", color=TEXT, fontsize=12)
ax.set_ylabel("Puja de renta (unidades monetarias / km²)", color=TEXT, fontsize=12)
ax.tick_params(colors=TEXT)
for spine in ax.spines.values():
    spine.set_edgecolor(TEXT)
    spine.set_alpha(0.4)
ax.grid(True, color=TEXT, alpha=0.12, linestyle="--")

ax.set_title(
    "Modelo Bid-Rent Urbano — William Alonso (1964)\n"
    "Competencia por suelo urbano entre grupos de ingresos",
    color=TEXT, fontsize=13, fontweight="bold", pad=14,
)

legend = ax.legend(
    facecolor="#1a2d45", edgecolor=TEXT, labelcolor=TEXT,
    fontsize=9, loc="upper right",
)

plt.tight_layout()
png1_path = os.path.join(ASSETS_DIR, "sim_alonso_bid_rent_1.png")
fig.savefig(png1_path, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig)
print(f"Grafica 1 guardada en: {png1_path}")

# ---------------------------------------------------------------------------
# 7. Grafica secundaria — PNG 2: mapa de asignacion y gradientes
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
fig.patch.set_facecolor(BG)

# --- Panel izquierdo: asignacion por franja ---
ax1 = axes[0]
ax1.set_facecolor(BG)

colores_asig = [POBRE_C if a == "pobre" else RICO_C for a in asignacion]
ax1.bar(d, envoltura, width=D_STEP, color=colores_asig, alpha=0.75, align="edge")

ax1.axvline(x=d_star, color=AMBER, lw=2.0, linestyle="--")
ax1.text(d_star + 0.3, 480, f"d* = {d_star:.2f} km",
         color=AMBER, fontsize=9)

ax1.set_xlim(0, 30)
ax1.set_ylim(0, 560)
ax1.set_xlabel("Distancia al CBD (km)", color=TEXT, fontsize=11)
ax1.set_ylabel("Renta de equilibrio (mejor postor)", color=TEXT, fontsize=11)
ax1.set_title("Asignacion del suelo por mejor postor", color=TEXT, fontsize=11)
ax1.tick_params(colors=TEXT)
for spine in ax1.spines.values():
    spine.set_edgecolor(TEXT); spine.set_alpha(0.4)
ax1.grid(True, color=TEXT, alpha=0.1, linestyle="--")

patch_p = mpatches.Patch(color=POBRE_C, alpha=0.75, label=f"Grupo Pobre (d < {d_star:.2f} km)")
patch_r = mpatches.Patch(color=RICO_C,  alpha=0.75, label=f"Grupo Rico  (d > {d_star:.2f} km)")
ax1.legend(handles=[patch_p, patch_r], facecolor="#1a2d45",
           edgecolor=TEXT, labelcolor=TEXT, fontsize=9)

# --- Panel derecho: comparacion de gradientes ---
ax2 = axes[1]
ax2.set_facecolor(BG)

for nombre, g in grupos.items():
    col = POBRE_C if nombre == "pobre" else RICO_C
    label_g = (
        f"{g['label']} (gradiente $k={g['k']}$)"
    )
    ax2.plot(d, R[nombre], color=col, lw=2.2, label=label_g)
    # Extrapolar a renta negativa para mostrar pendiente
    ax2.axhline(y=0, color=TEXT, lw=0.7, alpha=0.4, linestyle=":")

ax2.scatter([d_star], [renta_cruce], color=AMBER, s=90, zorder=10,
            label=f"Cruce en d*={d_star:.2f} km")

# Gradiente visual como flechas
for nombre, g in grupos.items():
    col = POBRE_C if nombre == "pobre" else RICO_C
    d_arr = 5.0
    ax2.annotate("",
        xy=(d_arr + 2, g["R0"] - g["k"] * (d_arr + 2)),
        xytext=(d_arr, g["R0"] - g["k"] * d_arr),
        arrowprops=dict(arrowstyle="-|>", color=col, lw=1.5),
    )

ax2.set_xlim(0, 30)
ax2.set_ylim(-50, 550)
ax2.set_xlabel("Distancia al CBD (km)", color=TEXT, fontsize=11)
ax2.set_ylabel("Puja de renta", color=TEXT, fontsize=11)
ax2.set_title("Gradientes de puja por grupo", color=TEXT, fontsize=11)
ax2.tick_params(colors=TEXT)
for spine in ax2.spines.values():
    spine.set_edgecolor(TEXT); spine.set_alpha(0.4)
ax2.grid(True, color=TEXT, alpha=0.1, linestyle="--")
ax2.legend(facecolor="#1a2d45", edgecolor=TEXT, labelcolor=TEXT, fontsize=9)

fig.suptitle(
    "Bid-Rent de Alonso (1964) — Segregacion espacial por estructura de mercado",
    color=TEXT, fontsize=12, fontweight="bold", y=1.01,
)

plt.tight_layout()
png2_path = os.path.join(ASSETS_DIR, "sim_alonso_bid_rent_2.png")
fig.savefig(png2_path, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig)
print(f"Grafica 2 guardada en: {png2_path}")

# ---------------------------------------------------------------------------
# 8. Guardar respuestas a preguntas en JSON
# ---------------------------------------------------------------------------
preguntas_path = os.path.join(SIMULACIONES_DIR, "preguntas_alonso_bid_rent.json")

preguntas_out = {
    "teoria": "alonso_bid_rent",
    "nombre": "Bid-rent urbano de Alonso (funciones de puja residencial)",
    "autor": "William Alonso",
    "anio": "1964",
    "preguntas": [
        {
            "q": (
                "Dadas las funciones de puja lineales R_pobre(d)=500-20d y "
                "R_rico(d)=300-5d (con d en km), calcula la distancia d* (km) "
                "al CBD donde ambos grupos pujan exactamente lo mismo. "
                "Formato: 'Respuesta final: <valor>'."
            ),
            "valor_exacto": f"{resp_p1:.4f}",
            "tipo": "forma_cerrada",
            "tolerancia": "±0.01 (13.33)",
            "como_computar": "500-20d=300-5d => 200=15d => d*=200/15=13.3333 km",
        },
        {
            "q": (
                "Con R_rico(d)=300-5d, calcula la puja de renta del grupo rico "
                "a d=20 km del CBD. "
                "Formato: 'Respuesta final: <valor>'."
            ),
            "valor_exacto": f"{resp_p2:.4f}",
            "tipo": "forma_cerrada",
            "tolerancia": "igualdad exacta (200)",
            "como_computar": "R_rico(20)=300-5*20=300-100=200",
        },
        {
            "q": (
                "Ejecuta la asignacion por mejor postor con R_pobre(d)=500-20d y "
                "R_rico(d)=300-5d en d=0..30 km (paso 0.1). Reporta la fraccion "
                "del intervalo [0,30] km que termina ocupada por el grupo pobre "
                "(mejor postor). "
                "Formato: 'Respuesta final: <valor>'."
            ),
            "valor_exacto": f"{fraccion_pobre:.4f}",
            "tipo": "emergente",
            "tolerancia": "±0.02 en torno a 0.44",
            "como_computar": (
                f"Los pobres ganan en d < {d_star:.4f} km; "
                f"n_pobre={n_pobre} de {n_total} puntos; "
                f"fraccion={n_pobre}/{n_total}={fraccion_pobre:.4f}"
            ),
        },
    ],
}

with open(preguntas_path, "w", encoding="utf-8") as f:
    json.dump(preguntas_out, f, ensure_ascii=False, indent=2)

print(f"Preguntas guardadas en: {preguntas_path}")

# ---------------------------------------------------------------------------
# 9. Reporte de validacion en consola
# ---------------------------------------------------------------------------
print("\n=== VALIDACION DEL MODELO ===")
print(f"  d* analitico           : {d_star:.6f} km  (esperado: 13.333...)")
print(f"  Renta en d*            : {renta_cruce:.6f}  (esperado: 233.333...)")
print(f"  R0_pobre > R0_rico     : {R0_p} > {R0_r}  => {R0_p > R0_r}")
print(f"  Grupo interior         : {asignacion[0]}  (esperado: pobre)")
print(f"  Envoltura decreciente  : {datos['verificacion']['envoltura_monotona_decreciente']}")
print(f"  Fraccion pobre         : {fraccion_pobre:.4f}  (esperado: ~0.444)")
print(f"  R_rico(20)             : {resp_p2:.2f}  (esperado: 200.00)")
