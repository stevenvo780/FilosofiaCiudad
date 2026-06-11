"""
Gravitación comercial: Ley de Reilly y modelo probabilístico de Huff
Autores: William J. Reilly (1931) / David L. Huff (1964)
Campo: economía espacial

Simulación determinista — dos ejecuciones producen resultados idénticos.
No requiere semilla aleatoria (no hay estocasticidad).
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import FancyArrowPatch
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
BASE = Path("/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad"
            "/03_Trabajos/Ponencia_Yuk_Hui")
SIM_DIR  = BASE / "simulaciones"
ASSET_DIR = BASE / "presentacion" / "assets" / "sim"
SIM_DIR.mkdir(parents=True, exist_ok=True)
ASSET_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Parámetros del experimento (literales del JSON de teoría)
# ---------------------------------------------------------------------------
# Reilly
P_A = 64_000        # población ciudad A
P_B = 16_000        # población ciudad B
D_AB = 30.0         # distancia A-B en km

# Huff (caso analítico con un consumidor)
A1, d1 = 1_000, 5.0    # Tienda 1: atractivo 1000 m², distancia 5 km
A2, d2 = 4_000, 10.0   # Tienda 2: atractivo 4000 m², distancia 10 km
BETA = 2.0

# Huff (rejilla 21×21)
GRID_N  = 21          # puntos por eje
GRID_LO, GRID_HI = 0.0, 20.0  # km
T1_POS = (5.0, 10.0)   # Tienda 1 en la rejilla
T2_POS = (15.0, 10.0)  # Tienda 2 en la rejilla
A1_GRID, A2_GRID = 1_000.0, 4_000.0

# ---------------------------------------------------------------------------
# 1. Ley de Reilly — punto de ruptura
# ---------------------------------------------------------------------------
BP_desde_B = D_AB / (1 + np.sqrt(P_A / P_B))
BP_desde_A = D_AB - BP_desde_B

print("=" * 55)
print("LEY DE REILLY — punto de ruptura")
print(f"  sqrt(P_A/P_B) = sqrt({P_A}/{P_B}) = {np.sqrt(P_A/P_B):.4f}")
print(f"  BP desde B    = {D_AB}/(1+{np.sqrt(P_A/P_B):.1f}) = {BP_desde_B:.4f} km")
print(f"  BP desde A    = {BP_desde_A:.4f} km")

# Verificación analítica
BP_teorico = 10.0
assert abs(BP_desde_B - BP_teorico) < 0.05, (
    f"FALLO validación Reilly: {BP_desde_B} ≠ {BP_teorico} (±0.05 km)")
print(f"  ✓ Verificación: |{BP_desde_B:.4f} - {BP_teorico}| < 0.05")

# ---------------------------------------------------------------------------
# 2. Modelo de Huff — caso analítico (un consumidor, dos tiendas)
# ---------------------------------------------------------------------------
U1 = A1 / (d1 ** BETA)
U2 = A2 / (d2 ** BETA)
total_U = U1 + U2
P1_analitico = U1 / total_U
P2_analitico = U2 / total_U

print("\nMODELO DE HUFF — caso analítico")
print(f"  U1 = {A1}/{d1}^{BETA:.0f} = {U1:.4f}")
print(f"  U2 = {A2}/{d2}^{BETA:.0f} = {U2:.4f}")
print(f"  P1 = {P1_analitico:.6f}")
print(f"  P2 = {P2_analitico:.6f}")
assert abs(P1_analitico + P2_analitico - 1.0) < 1e-9, "Las probabilidades no suman 1"
assert abs(P2_analitico - 0.5) < 0.001, f"FALLO: P2={P2_analitico} ≠ 0.5 (±0.001)"
print(f"  ✓ Verificación: P1+P2 = {P1_analitico+P2_analitico} (≈1)")
print(f"  ✓ Verificación: P2 = {P2_analitico:.4f} ≈ 0.5")

# ---------------------------------------------------------------------------
# 3. Modelo de Huff — rejilla 21×21
# ---------------------------------------------------------------------------
xs = np.linspace(GRID_LO, GRID_HI, GRID_N)
ys = np.linspace(GRID_LO, GRID_HI, GRID_N)
XX, YY = np.meshgrid(xs, ys)  # shape (GRID_N, GRID_N)

# Distancias euclídeas a cada tienda (evitar división por cero: eps pequeño)
EPS = 1e-9
D1_GRID = np.sqrt((XX - T1_POS[0])**2 + (YY - T1_POS[1])**2) + EPS
D2_GRID = np.sqrt((XX - T2_POS[0])**2 + (YY - T2_POS[1])**2) + EPS

UU1 = A1_GRID / (D1_GRID ** BETA)
UU2 = A2_GRID / (D2_GRID ** BETA)
TOT = UU1 + UU2

P_T2 = UU2 / TOT    # probabilidad de elegir Tienda 2 en cada celda

# Verificación: sumas de probabilidades == 1 en toda la rejilla
assert np.all(np.abs((UU1 / TOT + P_T2) - 1.0) < 1e-9), \
    "FALLO: las probabilidades de la rejilla no suman 1"

# Fracción de celdas con P(T2) >= 0.5
mask_t2 = P_T2 >= 0.5
fraccion_t2 = mask_t2.sum() / mask_t2.size

print("\nMODELO DE HUFF — rejilla 21×21")
print(f"  Celdas totales: {mask_t2.size}")
print(f"  Celdas con P(T2) >= 0.5: {mask_t2.sum()}")
print(f"  Fracción: {fraccion_t2:.4f}")

# Verificación: la fracción emergente debe caer en [0.73, 0.83] (±0.05 en torno a 0.78)
FRACCION_REF = 0.78
FRACCION_TOL = 0.05
assert abs(fraccion_t2 - FRACCION_REF) <= FRACCION_TOL, (
    f"FALLO validación rejilla: {fraccion_t2:.6f} fuera de "
    f"[{FRACCION_REF - FRACCION_TOL}, {FRACCION_REF + FRACCION_TOL}]"
)
print(f"  ✓ Verificación rejilla: |{fraccion_t2:.4f} - {FRACCION_REF}| = "
      f"{abs(fraccion_t2 - FRACCION_REF):.4f} ≤ {FRACCION_TOL}")

# ---------------------------------------------------------------------------
# 4. Guardar datos crudos en JSON
# ---------------------------------------------------------------------------
datos = {
    "teoria": "reilly_huff_gravitacion_comercial",
    "nombre": "Gravitación comercial: ley de Reilly y modelo probabilístico de Huff",
    "autor": "William J. Reilly / David L. Huff",
    "anio": "1931/1964",
    "reilly": {
        "P_A": P_A,
        "P_B": P_B,
        "D_AB_km": D_AB,
        "sqrt_PA_PB": float(np.sqrt(P_A / P_B)),
        "BP_desde_B_km": float(BP_desde_B),
        "BP_desde_A_km": float(BP_desde_A),
        "validacion_ok": bool(abs(BP_desde_B - 10.0) < 0.05),
    },
    "huff_analitico": {
        "A1": A1, "d1": d1,
        "A2": A2, "d2": d2,
        "beta": BETA,
        "U1": float(U1), "U2": float(U2),
        "P1": float(P1_analitico),
        "P2": float(P2_analitico),
        "suma_P": float(P1_analitico + P2_analitico),
        "validacion_ok": bool(abs(P2_analitico - 0.5) < 0.001),
    },
    "huff_rejilla": {
        "grid_n": GRID_N,
        "grid_rango_km": [GRID_LO, GRID_HI],
        "tienda1_pos": list(T1_POS),
        "tienda1_atractivo": A1_GRID,
        "tienda2_pos": list(T2_POS),
        "tienda2_atractivo": A2_GRID,
        "beta": BETA,
        "celdas_totales": int(mask_t2.size),
        "celdas_P_T2_ge_0p5": int(mask_t2.sum()),
        "fraccion_P_T2_ge_0p5": float(fraccion_t2),
        "validacion_sumas_1": True,
    },
}

json_path = SIM_DIR / "datos_reilly_huff_gravitacion_comercial.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)
print(f"\nDatos guardados en: {json_path}")

# ---------------------------------------------------------------------------
# 5. Figuras
# ---------------------------------------------------------------------------
FONDO      = "#0e1a2b"
TEXTO      = "#e8e6e1"
AMBAR      = "#e0a458"
ROJO_ZONA  = "#c0392b"
AZUL_ZONA  = "#2980b9"
VERDE      = "#27ae60"
GRIS_CLARO = "#7f8c8d"

# ---- Panel 1: Reilly -------------------------------------------------------
fig1, ax = plt.subplots(figsize=(10, 4), facecolor=FONDO)
ax.set_facecolor(FONDO)

# Línea A-B
ax.plot([0, D_AB], [0, 0], color=GRIS_CLARO, lw=2, zorder=1)

# Zonas de captura
ax.axvspan(0, BP_desde_A, alpha=0.25, color=AZUL_ZONA, label="Zona de captura de A")
ax.axvspan(BP_desde_A, D_AB, alpha=0.25, color=ROJO_ZONA, label="Zona de captura de B")

# Punto de ruptura
ax.axvline(BP_desde_A, color=AMBAR, lw=2, ls="--", label=f"Punto de ruptura ({BP_desde_A:.1f} km desde A)")
ax.plot(BP_desde_A, 0, "o", color=AMBAR, ms=10, zorder=5)

# Ciudades
ax.plot(0, 0, "s", color=AZUL_ZONA, ms=14, zorder=6, label=f"Ciudad A  (P={P_A:,})")
ax.plot(D_AB, 0, "s", color=ROJO_ZONA, ms=14, zorder=6, label=f"Ciudad B  (P={P_B:,})")

# Anotaciones
ax.annotate("A", (0, 0), (0, 0.15), color=AZUL_ZONA, fontsize=13, fontweight="bold",
            ha="center", xycoords="data", textcoords="data")
ax.annotate("B", (D_AB, 0), (D_AB, 0.15), color=ROJO_ZONA, fontsize=13, fontweight="bold",
            ha="center", xycoords="data", textcoords="data")
ax.annotate(f"BP = {BP_desde_A:.0f} km desde A\n({BP_desde_B:.0f} km desde B)",
            (BP_desde_A, 0), (BP_desde_A, -0.35),
            color=AMBAR, fontsize=10, ha="center",
            arrowprops=dict(arrowstyle="->", color=AMBAR, lw=1.2))

ax.set_xlim(-2, D_AB + 2)
ax.set_ylim(-0.6, 0.6)
ax.set_xlabel("Distancia (km)", color=TEXTO, fontsize=11)
ax.set_yticks([])
ax.tick_params(colors=TEXTO)
for sp in ax.spines.values():
    sp.set_edgecolor(GRIS_CLARO)

leg = ax.legend(loc="upper right", fontsize=8.5, framealpha=0.3,
                labelcolor=TEXTO, facecolor=FONDO, edgecolor=GRIS_CLARO)

ax.set_title("Ley de Reilly — Punto de ruptura gravitacional\n"
             "W. J. Reilly (1931)  ·  Economía espacial",
             color=TEXTO, fontsize=12, pad=12)

fig1.tight_layout()
out1 = ASSET_DIR / "sim_reilly_huff_gravitacion_comercial_1.png"
fig1.savefig(out1, dpi=150, bbox_inches="tight", facecolor=FONDO)
plt.close(fig1)
print(f"PNG 1 guardado: {out1}")

# ---- Panel 2: Huff mapa de calor ------------------------------------------
fig2, ax2 = plt.subplots(figsize=(8, 7), facecolor=FONDO)
ax2.set_facecolor(FONDO)

# Paleta sobria: azul oscuro → gris → ámbar
cmap_custom = mcolors.LinearSegmentedColormap.from_list(
    "huff_custom",
    [(0.0, "#1a3a5c"),   # baja prob T2 → azul oscuro (domina T1)
     (0.5, "#2d4a3e"),   # equiprobable → verde oscuro
     (1.0, "#7a4a1e")],  # alta prob T2 → marrón ámbar
)

im = ax2.imshow(
    P_T2,
    origin="lower",
    extent=[GRID_LO, GRID_HI, GRID_LO, GRID_HI],
    cmap=cmap_custom,
    vmin=0, vmax=1,
    aspect="equal",
    interpolation="bilinear",
)

# Isolíneas de probabilidad
contour_levels = [0.25, 0.5, 0.75]
contour_colors = [AZUL_ZONA, AMBAR, ROJO_ZONA]
cs = ax2.contour(XX, YY, P_T2, levels=contour_levels,
                 colors=contour_colors, linewidths=1.5)
ax2.clabel(cs, fmt={0.25: "P=0.25", 0.5: "P=0.50", 0.75: "P=0.75"},
           inline=True, fontsize=9, colors=contour_colors)

# Tiendas
ax2.plot(*T1_POS, "^", color=AZUL_ZONA, ms=14, zorder=10,
         label=f"Tienda 1  A={int(A1_GRID)} m²")
ax2.plot(*T2_POS, "s", color=ROJO_ZONA, ms=14, zorder=10,
         label=f"Tienda 2  A={int(A2_GRID)} m²")
ax2.annotate("T1", T1_POS, (T1_POS[0], T1_POS[1] + 1.0),
             color=AZUL_ZONA, fontsize=10, ha="center", fontweight="bold")
ax2.annotate("T2", T2_POS, (T2_POS[0], T2_POS[1] + 1.0),
             color=ROJO_ZONA, fontsize=10, ha="center", fontweight="bold")

cb = fig2.colorbar(im, ax=ax2, pad=0.02)
cb.set_label("Probabilidad de elegir la Tienda 2  P(T2)", color=TEXTO, fontsize=10)
cb.ax.yaxis.set_tick_params(color=TEXTO)
cb.outline.set_edgecolor(GRIS_CLARO)
plt.setp(cb.ax.yaxis.get_ticklabels(), color=TEXTO)

ax2.set_xlabel("Coordenada X (km)", color=TEXTO, fontsize=11)
ax2.set_ylabel("Coordenada Y (km)", color=TEXTO, fontsize=11)
ax2.tick_params(colors=TEXTO)
for sp in ax2.spines.values():
    sp.set_edgecolor(GRIS_CLARO)

leg2 = ax2.legend(loc="lower right", fontsize=9, framealpha=0.4,
                  labelcolor=TEXTO, facecolor=FONDO, edgecolor=GRIS_CLARO)

ax2.set_title(
    f"Modelo de Huff — Mapa de probabilidad de elección  (β={BETA:.0f})\n"
    f"D. L. Huff (1964)  ·  Fracción con P(T2)≥0.5: {fraccion_t2:.2f}",
    color=TEXTO, fontsize=12, pad=12,
)

fig2.tight_layout()
out2 = ASSET_DIR / "sim_reilly_huff_gravitacion_comercial_2.png"
fig2.savefig(out2, dpi=150, bbox_inches="tight", facecolor=FONDO)
plt.close(fig2)
print(f"PNG 2 guardado: {out2}")

# ---------------------------------------------------------------------------
# 6. Guardar preguntas con valores exactos
# ---------------------------------------------------------------------------
preguntas_json = {
    "teoria": "reilly_huff_gravitacion_comercial",
    "nombre": "Gravitación comercial: ley de Reilly y modelo probabilístico de Huff",
    "autor": "William J. Reilly / David L. Huff",
    "anio": "1931/1964",
    "preguntas": [
        {
            "q": (
                "Dos ciudades A (población 64000) y B (población 16000) están separadas "
                "por 30 km. Usando el punto de ruptura de Reilly BP=d/(1+sqrt(P_A/P_B)), "
                "calcula la distancia (km) del punto de ruptura medida desde B. "
                "Formato: 'Respuesta final: <valor>'."
            ),
            "valor_exacto": str(round(float(BP_desde_B), 6)),
            "tipo": "forma_cerrada",
            "tolerancia": "±0.05 (10.0)",
            "como_computar": (
                f"sqrt({P_A}/{P_B})=sqrt(4)=2; "
                f"BP={D_AB}/(1+2)={BP_desde_B:.4f} km desde B."
            ),
        },
        {
            "q": (
                "Con el modelo de Huff y beta=2, un consumidor enfrenta la Tienda 1 "
                "(atractivo 1000, distancia 5) y la Tienda 2 (atractivo 4000, distancia 10). "
                "Calcula la probabilidad de que elija la Tienda 2. "
                "Formato: 'Respuesta final: <valor>'."
            ),
            "valor_exacto": str(round(float(P2_analitico), 6)),
            "tipo": "forma_cerrada",
            "tolerancia": "±0.001 (0.5)",
            "como_computar": (
                f"U1={A1}/{d1}^{BETA:.0f}={U1:.2f}, "
                f"U2={A2}/{d2}^{BETA:.0f}={U2:.2f}; "
                f"P2={U2:.2f}/({U1:.2f}+{U2:.2f})={P2_analitico:.4f}."
            ),
        },
        {
            "q": (
                "Sobre una rejilla de 21x21 consumidores en [0,20]x[0,20] km, "
                "con Tienda 1 en (5,10) atractivo 1000 y Tienda 2 en (15,10) atractivo 4000, "
                "beta=2, calcula la fracción de celdas de la rejilla en las que la probabilidad "
                "de Huff de elegir la Tienda 2 es mayor o igual a 0.5. "
                "Formato: 'Respuesta final: <valor>'."
            ),
            "valor_exacto": str(round(float(fraccion_t2), 6)),
            "tipo": "emergente",
            "tolerancia": "±0.05 en torno a 0.78",
            "como_computar": (
                f"Rejilla {GRID_N}×{GRID_N}={mask_t2.size} celdas; "
                f"celdas con P(T2)>=0.5: {int(mask_t2.sum())}; "
                f"fracción={fraccion_t2:.6f}."
            ),
        },
    ],
}

preguntas_path = SIM_DIR / "preguntas_reilly_huff_gravitacion_comercial.json"
with open(preguntas_path, "w", encoding="utf-8") as f:
    json.dump(preguntas_json, f, ensure_ascii=False, indent=2)
print(f"Preguntas guardadas en: {preguntas_path}")

# ---------------------------------------------------------------------------
# Resumen final de validación
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print("RESUMEN DE VALIDACIÓN")
print(f"  Reilly  BP desde B     = {BP_desde_B:.4f} km   (esperado 10.0 ± 0.05)")
print(f"  Huff P2 analítico      = {P2_analitico:.6f}   (esperado 0.5 ± 0.001)")
print(f"  Huff suma de probs     = {float(P1_analitico + P2_analitico):.10f}  (esperado 1.0 ± 1e-9)")
print(f"  Huff rejilla P(T2)≥0.5 = {fraccion_t2:.4f}    (esperado ~0.78 ± 0.05, rango [0.73, 0.83])")
print("  Todos los criterios APROBADOS")
