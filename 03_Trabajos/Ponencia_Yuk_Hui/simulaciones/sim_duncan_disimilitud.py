"""
Simulacion del Indice de Disimilitud de Duncan y Duncan (1955)

Autores: Otis Dudley Duncan y Beverly Duncan
Anio: 1955
Campo: Dinamica social / Segregacion urbana

Formulacion:
    D = 0.5 * sum_{i=1}^{n} |a_i/A - b_i/B|

    Donde:
        a_i = miembros del grupo A en el tract i
        b_i = miembros del grupo B en el tract i
        A   = total del grupo A
        B   = total del grupo B
        D en [0,1]: 0 = sin segregacion, 1 = segregacion completa

Experimento literal (determinista, sin semilla aleatoria):
    Ciudad con 4 tracts:
        Grupo A: [40, 30, 20, 10]  (A=100)
        Grupo B: [10, 20, 30, 40]  (B=100)
    Resultado esperado: D = 0.40
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json
import os
import sys

# Reusar la rejilla final del modulo Schelling canonico del proyecto
# (sim_schelling_segregacion.simular) para que Q3 sea reproducible desde
# "el experimento de Schelling" del proyecto (45% Rojo, 45% Azul, 10% vacio,
# T=0.30, seed=42, max_iter=200, vecindad de Moore).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim_schelling_segregacion as schelling

# ─────────────────────────────────────────────
# Paleta estetica
# ─────────────────────────────────────────────
BG_COLOR    = "#0e1a2b"
TEXT_COLOR  = "#e8e6e1"
AMBER       = "#e0a458"
BLUE_GRP    = "#4a90d9"   # Grupo A
RED_GRP     = "#c0392b"   # Grupo B
DIFF_COLOR  = "#7ecba1"   # Diferencia absoluta

ASSETS_DIR  = "/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui/presentacion/assets/sim"
DATOS_PATH  = "/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui/simulaciones/datos_duncan_disimilitud.json"
PREGS_PATH  = "/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui/simulaciones/preguntas_duncan_disimilitud.json"


# ─────────────────────────────────────────────
# 1. Funcion central: indice de disimilitud
# ─────────────────────────────────────────────
def indice_disimilitud(a: np.ndarray, b: np.ndarray) -> float:
    """
    Calcula D = 0.5 * sum |a_i/A - b_i/B|
    Invariante a multiplicar todos los a_i (o b_i) por una constante positiva.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    A = a.sum()
    B = b.sum()
    if A == 0 or B == 0:
        raise ValueError("El total de al menos un grupo es cero.")
    return 0.5 * np.sum(np.abs(a / A - b / B))


# ─────────────────────────────────────────────
# 2. Experimento literal del JSON
# ─────────────────────────────────────────────
a_exp = np.array([40, 30, 20, 10], dtype=float)
b_exp = np.array([10, 20, 30, 40], dtype=float)
A_exp = a_exp.sum()   # 100
B_exp = b_exp.sum()   # 100

prop_a = a_exp / A_exp
prop_b = b_exp / B_exp
diffs  = np.abs(prop_a - prop_b)
D_exp  = indice_disimilitud(a_exp, b_exp)

n_tracts = len(a_exp)
uniform  = 1.0 / n_tracts   # linea de referencia distribucion uniforme

print("=== Experimento Duncan & Duncan (1955) ===")
print(f"Grupo A por tract: {a_exp.tolist()}  (total={A_exp:.0f})")
print(f"Grupo B por tract: {b_exp.tolist()}  (total={B_exp:.0f})")
print(f"Proporciones A:    {prop_a.tolist()}")
print(f"Proporciones B:    {prop_b.tolist()}")
print(f"Diferencias |a/A - b/B|: {diffs.tolist()}")
print(f"Suma diferencias:  {diffs.sum():.4f}")
print(f"D (experimento):   {D_exp:.4f}  (esperado 0.40)")


# ─────────────────────────────────────────────
# 3. Pregunta 2: 3 tracts
# ─────────────────────────────────────────────
a_p2 = np.array([50, 30, 20], dtype=float)
b_p2 = np.array([20, 30, 50], dtype=float)
D_p2 = indice_disimilitud(a_p2, b_p2)
prop_a2 = a_p2 / a_p2.sum()
prop_b2 = b_p2 / b_p2.sum()
diffs2  = np.abs(prop_a2 - prop_b2)
print(f"\n=== Pregunta 2 (3 tracts) ===")
print(f"Diferencias: {diffs2.tolist()}  Suma: {diffs2.sum():.4f}")
print(f"D:           {D_p2:.4f}  (esperado 0.30)")


# ─────────────────────────────────────────────
# 4. Pregunta 3: rejilla final del experimento de Schelling canonico
#    del proyecto (sim_schelling_segregacion: 50x50, 45% Rojo, 45% Azul,
#    10% vacio, T=0.30, seed=42, max_iter=200, vecindad de Moore).
#    Divide en 25 bloques de 10x10 y calcula D de Duncan.
# ─────────────────────────────────────────────
print("\n=== Pregunta 3: rejilla del experimento de Schelling del proyecto ===")
print("  (sim_schelling_segregacion: 50x50, 45% Rojo, 45% Azul, T=0.30, seed=42)")
_res_sch = schelling.simular()   # parametros canonicos del modulo
grid_sch = _res_sch["grid_final"]  # estados: 0=vacia, 1=Rojo, 2=Azul

# Contar rojos y azules totales
total_red  = np.sum(grid_sch == 1)
total_blue = np.sum(grid_sch == 2)
print(f"  Rejilla {grid_sch.shape[0]}x{grid_sch.shape[1]}; "
      f"convergencia iter={_res_sch['iteracion_convergencia']}")
print(f"  Rojos totales: {total_red}, Azules totales: {total_blue}")

# Dividir en 25 bloques de 10x10
block_size = 10
blocks_per_side = 5   # 50 / 10 = 5
n_blocks = blocks_per_side ** 2

reds_per_block  = []
blues_per_block = []

for bi in range(blocks_per_side):
    for bj in range(blocks_per_side):
        r0, r1 = bi*block_size, (bi+1)*block_size
        c0, c1 = bj*block_size, (bj+1)*block_size
        block = grid_sch[r0:r1, c0:c1]
        reds_per_block.append(np.sum(block == 1))
        blues_per_block.append(np.sum(block == 2))

reds_per_block  = np.array(reds_per_block,  dtype=float)
blues_per_block = np.array(blues_per_block, dtype=float)

D_schelling = indice_disimilitud(reds_per_block, blues_per_block)
print(f"  D (Schelling->Duncan): {D_schelling:.4f}  "
      f"(segregacion baja-moderada a esta escala de agregacion; "
      f"baseline aleatorio D~0.09)")


# ─────────────────────────────────────────────
# 5. Validacion del criterio
# ─────────────────────────────────────────────
print("\n=== Validacion del criterio ===")
# a) D in [0,1]
assert 0 <= D_exp <= 1, f"D={D_exp} fuera de [0,1]"
# b) distribuciones identicas -> D=0
a_ident = np.array([25, 25, 25, 25], dtype=float)
b_ident = np.array([25, 25, 25, 25], dtype=float)
D_ident = indice_disimilitud(a_ident, b_ident)
assert abs(D_ident) < 1e-9, f"D distribucion identica = {D_ident}, esperado ~0"
# c) experimento D=0.40
assert abs(D_exp - 0.40) < 0.001, f"D experimento = {D_exp}, esperado 0.40"
# d) invarianza a escalar
a_scaled = a_exp * 7.3
D_scaled = indice_disimilitud(a_scaled, b_exp)
assert abs(D_scaled - D_exp) < 1e-9, f"Invarianza violada: {D_scaled} vs {D_exp}"
print(f"  D identico:            {D_ident:.10f}  (esperado 0)")
print(f"  D experimento:         {D_exp:.6f}  (esperado 0.40)")
print(f"  D escalado (a*7.3):    {D_scaled:.6f}  (debe = D experimento)")
print("  TODOS LOS CRITERIOS SUPERADOS")


# ─────────────────────────────────────────────
# 6. Guardar datos crudos JSON
# ─────────────────────────────────────────────
datos = {
    "teoria": "duncan_disimilitud",
    "autor": "Otis Dudley Duncan y Beverly Duncan",
    "anio": "1955",
    "experimento_principal": {
        "grupo_A": a_exp.tolist(),
        "grupo_B": b_exp.tolist(),
        "total_A": float(A_exp),
        "total_B": float(B_exp),
        "proporciones_A": prop_a.tolist(),
        "proporciones_B": prop_b.tolist(),
        "diferencias_absolutas": diffs.tolist(),
        "suma_diferencias": float(diffs.sum()),
        "D": float(D_exp),
        "D_esperado": 0.40,
        "n_tracts": n_tracts,
        "distribucion_uniforme_referencia": uniform
    },
    "pregunta_2": {
        "grupo_A": a_p2.tolist(),
        "grupo_B": b_p2.tolist(),
        "diferencias": diffs2.tolist(),
        "suma_diferencias": float(diffs2.sum()),
        "D": float(D_p2),
        "D_esperado": 0.30
    },
    "pregunta_3_schelling": {
        "fuente_rejilla": "sim_schelling_segregacion.simular()['grid_final']",
        "tamano_rejilla": 50,
        "composicion": "45% Rojo, 45% Azul, 10% vacio",
        "umbral_T": 0.30,
        "semilla": 42,
        "max_iter": int(schelling.MAX_ITER),
        "iteracion_convergencia": _res_sch["iteracion_convergencia"],
        "bloques": 25,
        "tamano_bloque": "10x10",
        "rojos_por_bloque": reds_per_block.tolist(),
        "azules_por_bloque": blues_per_block.tolist(),
        "total_rojos": int(total_red),
        "total_azules": int(total_blue),
        "contribuciones_D_por_tract": (0.5 * np.abs(
            reds_per_block / reds_per_block.sum()
            - blues_per_block / blues_per_block.sum())).tolist(),
        "D_schelling": float(D_schelling)
    },
    "validacion": {
        "D_identico": float(D_ident),
        "D_experimento": float(D_exp),
        "D_escalado_a_x7.3": float(D_scaled),
        "criterios_superados": True
    }
}

os.makedirs(os.path.dirname(DATOS_PATH), exist_ok=True)
with open(DATOS_PATH, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)
print(f"\nDatos guardados en: {DATOS_PATH}")


# ─────────────────────────────────────────────
# 7. Grafico 1: Barras proporcionales por tract
#    (experimento principal)
# ─────────────────────────────────────────────
os.makedirs(ASSETS_DIR, exist_ok=True)

fig1, ax1 = plt.subplots(figsize=(10, 6))
fig1.patch.set_facecolor(BG_COLOR)
ax1.set_facecolor(BG_COLOR)

tract_labels = [f"Tract {i+1}" for i in range(n_tracts)]
x = np.arange(n_tracts)
w = 0.32

bars_a = ax1.bar(x - w/2, prop_a, width=w, color=BLUE_GRP, alpha=0.88, label="Grupo A (proporción)", zorder=3)
bars_b = ax1.bar(x + w/2, prop_b, width=w, color=RED_GRP,  alpha=0.88, label="Grupo B (proporción)", zorder=3)

# Linea de referencia distribucion uniforme
ax1.axhline(y=uniform, color=AMBER, linestyle="--", linewidth=1.5,
            label=f"Distribución uniforme (1/{n_tracts} = {uniform:.2f})", zorder=2)

# Anotacion de diferencia absoluta sobre cada tract
for i in range(n_tracts):
    top = max(prop_a[i], prop_b[i]) + 0.015
    ax1.annotate(
        f"|Δ|={diffs[i]:.2f}",
        xy=(x[i], top),
        ha="center", va="bottom",
        fontsize=10, color=DIFF_COLOR, fontweight="bold"
    )

ax1.set_xticks(x)
ax1.set_xticklabels(tract_labels, color=TEXT_COLOR, fontsize=12)
ax1.set_yticks(np.linspace(0, 0.5, 6))
ax1.tick_params(colors=TEXT_COLOR)
ax1.set_ylabel("Proporción del grupo total", color=TEXT_COLOR, fontsize=12)
ax1.set_xlabel("Unidad espacial (tract)", color=TEXT_COLOR, fontsize=12)
ax1.set_ylim(0, 0.55)

for spine in ax1.spines.values():
    spine.set_edgecolor("#2a3a50")

ax1.yaxis.set_tick_params(color=TEXT_COLOR)
ax1.xaxis.set_tick_params(color=TEXT_COLOR)
for lbl in ax1.get_yticklabels():
    lbl.set_color(TEXT_COLOR)

ax1.set_title(
    f"Índice de Disimilitud de Duncan y Duncan (1955)\n"
    f"D = {D_exp:.2f}  — Ciudad de 4 tracts, grupos iguales (N=100 c/u)",
    color=TEXT_COLOR, fontsize=13, pad=14
)

legend = ax1.legend(
    facecolor="#1a2d42", edgecolor="#2a3a50",
    labelcolor=TEXT_COLOR, fontsize=10, loc="upper right"
)

# Texto explicativo dentro del grafico
ax1.text(0.01, 0.97,
    f"D = 0.5 × Σ|a_i/A − b_i/B| = 0.5 × {diffs.sum():.2f} = {D_exp:.2f}\n"
    f"Fracción del grupo que debería reubicarse para igualar distribuciones.",
    transform=ax1.transAxes,
    va="top", ha="left", fontsize=9,
    color=TEXT_COLOR, alpha=0.85,
    bbox=dict(facecolor="#0e1a2b", edgecolor="#2a3a50", alpha=0.7, boxstyle="round,pad=0.4")
)

plt.tight_layout()
png1 = os.path.join(ASSETS_DIR, "sim_duncan_disimilitud_1.png")
fig1.savefig(png1, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
plt.close(fig1)
print(f"Grafico 1 guardado: {png1}")


# ─────────────────────────────────────────────
# 8. Grafico 2: Rejilla Schelling + tracts coloreados por D
# ─────────────────────────────────────────────
fig2, axes = plt.subplots(1, 2, figsize=(14, 6))
fig2.patch.set_facecolor(BG_COLOR)

# Panel izquierdo: rejilla Schelling
ax_grid = axes[0]
ax_grid.set_facecolor(BG_COLOR)

# Mapa de color para la rejilla: 0=vacia, 1=Rojo, 2=Azul
color_map = np.zeros((*grid_sch.shape, 3))
color_map[grid_sch == 0] = [0.06, 0.12, 0.18]   # vacio ~ fondo
color_map[grid_sch == 1] = [0.75, 0.22, 0.17]   # Rojo
color_map[grid_sch == 2] = [0.29, 0.56, 0.85]   # Azul

ax_grid.imshow(color_map, interpolation="nearest")

# Dibujar bordes de bloques 10x10
for k in range(0, 51, 10):
    ax_grid.axhline(k - 0.5, color=AMBER, linewidth=0.7, alpha=0.6)
    ax_grid.axvline(k - 0.5, color=AMBER, linewidth=0.7, alpha=0.6)

ax_grid.set_title("Rejilla Schelling segregada del proyecto\n"
                  "(50×50, 45% Rojo / 45% Azul, T=0.30, seed=42)",
                  color=TEXT_COLOR, fontsize=11)
ax_grid.tick_params(colors=TEXT_COLOR, labelsize=8)
for spine in ax_grid.spines.values():
    spine.set_edgecolor("#2a3a50")
ax_grid.set_xlabel("Columna", color=TEXT_COLOR, fontsize=10)
ax_grid.set_ylabel("Fila", color=TEXT_COLOR, fontsize=10)

legend_handles = [
    mpatches.Patch(color="#bf381b", label="Grupo Rojo"),
    mpatches.Patch(color="#4a90d9", label="Grupo Azul"),
    mpatches.Patch(color="#0f1e2e", label="Vacío"),
]
ax_grid.legend(handles=legend_handles, facecolor="#1a2d42", edgecolor="#2a3a50",
               labelcolor=TEXT_COLOR, fontsize=9, loc="upper right")

# Panel derecho: contribucion real de cada tract al indice D (heatmap)
ax_heat = axes[1]
ax_heat.set_facecolor(BG_COLOR)

# Contribucion de cada tract al indice D de Duncan: 0.5*|r_i/R - a_i/A|.
# La SUMA de estas celdas es exactamente D (a diferencia de la desviacion
# local de proporcion, que no suma D).
R_total = reds_per_block.sum()
A_total = blues_per_block.sum()
block_d_matrix = np.zeros((blocks_per_side, blocks_per_side))
for bi in range(blocks_per_side):
    for bj in range(blocks_per_side):
        idx = bi * blocks_per_side + bj
        r_i = reds_per_block[idx]
        a_i = blues_per_block[idx]
        block_d_matrix[bi, bj] = 0.5 * abs(r_i / R_total - a_i / A_total)

# Verificacion: la suma de contribuciones es D
assert abs(block_d_matrix.sum() - D_schelling) < 1e-9, \
    f"Las contribuciones por tract ({block_d_matrix.sum()}) no suman D ({D_schelling})"

vmax_heat = float(block_d_matrix.max())
im = ax_heat.imshow(block_d_matrix, cmap="YlOrBr", vmin=0, vmax=vmax_heat,
                    interpolation="nearest")

# Anotaciones en cada bloque (contribucion x1000 para legibilidad)
thresh = vmax_heat * 0.6
for bi in range(blocks_per_side):
    for bj in range(blocks_per_side):
        val = block_d_matrix[bi, bj]
        ax_heat.text(bj, bi, f"{val:.3f}", ha="center", va="center",
                     fontsize=7, color="white" if val > thresh else "#0e1a2b",
                     fontweight="bold")

cbar = fig2.colorbar(im, ax=ax_heat, fraction=0.046, pad=0.04)
cbar.ax.tick_params(colors=TEXT_COLOR, labelsize=8)
cbar.set_label("Contribución del tract a D = 0.5·|r_i/R − a_i/A|",
               color=TEXT_COLOR, fontsize=9)

ax_heat.set_title(
    f"Contribución de cada tract al índice D (25 tracts)\n"
    f"Σ contribuciones = D (Duncan) = {D_schelling:.3f}",
    color=TEXT_COLOR, fontsize=11
)
ax_heat.set_xticks(range(blocks_per_side))
ax_heat.set_yticks(range(blocks_per_side))
ax_heat.set_xticklabels([f"B{j+1}" for j in range(blocks_per_side)],
                         color=TEXT_COLOR, fontsize=8)
ax_heat.set_yticklabels([f"F{i+1}" for i in range(blocks_per_side)],
                         color=TEXT_COLOR, fontsize=8)
for spine in ax_heat.spines.values():
    spine.set_edgecolor("#2a3a50")

fig2.suptitle(
    "Índice de Disimilitud de Duncan (1955) aplicado al Modelo de Schelling",
    color=TEXT_COLOR, fontsize=13, y=1.01
)

plt.tight_layout()
png2 = os.path.join(ASSETS_DIR, "sim_duncan_disimilitud_2.png")
fig2.savefig(png2, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
plt.close(fig2)
print(f"Grafico 2 guardado: {png2}")


# ─────────────────────────────────────────────
# 9. Guardar JSON de preguntas
# ─────────────────────────────────────────────
preguntas_json = {
    "teoria": "duncan_disimilitud",
    "nombre": "Indice de disimilitud de Duncan y Duncan",
    "autor": "Otis Dudley Duncan y Beverly Duncan",
    "anio": "1955",
    "preguntas": [
        {
            "q": "Una ciudad tiene 4 tracts con grupo A = [40,30,20,10] (total 100) y grupo B = [10,20,30,40] (total 100). Usando D = 0.5*sum|a_i/A - b_i/B|, calcula el indice de disimilitud. Formato: 'Respuesta final: <valor>'.",
            "valor_exacto": str(round(float(D_exp), 4)),
            "tipo": "forma_cerrada",
            "tolerancia": "±0.001 (0.40)",
            "como_computar": "|0.4-0.1|+|0.3-0.2|+|0.2-0.3|+|0.1-0.4|=0.3+0.1+0.1+0.3=0.8; D=0.5*0.8=0.40."
        },
        {
            "q": "En 3 tracts, grupo A = [50,30,20] (total 100) y grupo B = [20,30,50] (total 100). Calcula el indice de disimilitud de Duncan D = 0.5*sum|a_i/A - b_i/B|. Formato: 'Respuesta final: <valor>'.",
            "valor_exacto": str(round(float(D_p2), 4)),
            "tipo": "forma_cerrada",
            "tolerancia": "±0.001 (0.30)",
            "como_computar": "|0.5-0.2|+|0.3-0.3|+|0.2-0.5|=0.3+0+0.3=0.6; D=0.5*0.6=0.30."
        },
        {
            "q": "Toma la rejilla final del experimento de Schelling del proyecto (sim_schelling_segregacion: 50x50, 45% Rojo, 45% Azul, 10% vacio, umbral T=0.30, vecindad de Moore, numpy seed=42, max_iter=200), divide la rejilla en 25 bloques de 10x10 celdas como 'tracts', cuenta Rojos y Azules por bloque, y calcula el indice de disimilitud D de Duncan entre Rojo y Azul. Reporta D. Formato: 'Respuesta final: <valor>'.",
            "valor_exacto": str(round(float(D_schelling), 4)),
            "tipo": "emergente",
            "tolerancia": f"±0.05 en torno a {round(float(D_schelling), 3)} (a esta escala de agregacion 10x10 el Schelling T=0.30 da segregacion baja-moderada; baseline aleatorio D~0.09)",
            "como_computar": f"Rejilla final del modulo Schelling canonico (45/45/10, T=0.30, seed=42, max_iter=200) -> {int(total_red)} Rojos y {int(total_blue)} Azules; agregar en 25 bloques 10x10; rojos_por_bloque={reds_per_block.tolist()}; azules_por_bloque={blues_per_block.tolist()}; D=0.5*sum|r_i/R - a_i/A|={round(float(D_schelling), 4)}. Las contribuciones por tract 0.5*|r_i/R - a_i/A| suman exactamente D."
        }
    ]
}

with open(PREGS_PATH, "w", encoding="utf-8") as f:
    json.dump(preguntas_json, f, ensure_ascii=False, indent=2)
print(f"Preguntas guardadas en: {PREGS_PATH}")

print("\n=== RESUMEN FINAL ===")
print(f"D experimento (4 tracts):    {D_exp:.4f}   esperado 0.40")
print(f"D pregunta 2  (3 tracts):    {D_p2:.4f}   esperado 0.30")
print(f"D Schelling   (25 bloques):  {D_schelling:.4f}   "
      f"(rejilla canonica del proyecto; segregacion baja-moderada)")
print(f"PNG generados: sim_duncan_disimilitud_1.png, sim_duncan_disimilitud_2.png")
