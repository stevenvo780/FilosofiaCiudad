"""
Simulacion: Teoria de los lugares centrales de Walter Christaller (1933)
Principio de mercado k=3, jerarquia de 4 niveles.

Determinista: sin semilla aleatoria necesaria (construccion geometrica pura).
Dos corridas producen resultado identico.

Correccion v2:
- Centros de nivel 3 colocados a distancia r4-r3 del centro para que los
  hexagonos n3 queden completamente dentro del hexagono n4 (condicion visual
  de la especificacion).
- Criterio de validacion corregido: razon_lugares_OK evalua todas las razones
  segun la secuencia correcta 1,2,6,18 (factores 2,3,3,3 de arriba hacia abajo):
    18/6=3, 6/2=3, 2/1=2 -> las razones 1->2 y 2->3 deben ser 3; la razon 3->4
    debe ser 2 (factor correcto en el tope de la jerarquia k=3 con 4 niveles).
- JSON de validacion refleja el estado real sin enmascaramiento.

Salidas:
  - datos_christaller_lugares_centrales.json
  - sim_christaller_lugares_centrales_1.png  (teselacion hexagonal anidada)
  - sim_christaller_lugares_centrales_2.png  (panel de barras log)
"""

import numpy as np
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
import os

# ─────────────────────────────────────────────
# CONSTANTES Y RUTAS
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(
    BASE_DIR, "..", "presentacion", "assets", "sim"
)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Estetica
BG      = "#0e1a2b"
FG      = "#e8e6e1"
AMBER   = "#e0a458"
AZUL    = "#4a90c4"
VERDE   = "#5aab8a"
ROJO    = "#c45a5a"
GRIS    = "#607080"

# Parametros de la teoria
K       = 3          # principio de mercado
NIVELES = 4          # niveles jerarquicos (4 = maximo orden)
R_BASE  = 10.0       # km, alcance del hexagono de nivel 1

# ─────────────────────────────────────────────
# 1. CALCULOS ANALITICOS
# ─────────────────────────────────────────────

def area_hexagono(r):
    """Area del hexagono de radio r: A = (3*sqrt(3)/2)*r^2"""
    return (3.0 * np.sqrt(3) / 2.0) * r ** 2


# Areas por nivel (nivel 1 = base, nivel 4 = mayor)
# Factor de escala: K^(nivel-1) -> 1, 3, 9, 27
areas = {}
for nivel in range(1, NIVELES + 1):
    factor = K ** (nivel - 1)
    areas[nivel] = area_hexagono(R_BASE) * factor

# Numero de lugares por nivel.
# Secuencia correcta segun la teoria de Christaller k=3 para 4 niveles:
#   nivel 4 (metropoli): 1
#   nivel 3 (ciudad):    2   <- factor 2 entre nivel 4 y nivel 3 (tope de la jerarquia)
#   nivel 2 (villa):     6   <- factor 3 entre nivel 3 y nivel 2
#   nivel 1 (aldea):    18   <- factor 3 entre nivel 2 y nivel 1
# Secuencia descendente: 1, 2, 6, 18  con factores  2, 3, 3
num_lugares = {
    4: 1,
    3: 2,
    2: 6,
    1: 18,
}

# Radio por nivel: r_nivel = R_BASE * sqrt(K^(nivel-1))
radios = {}
for nivel in range(1, NIVELES + 1):
    radios[nivel] = R_BASE * np.sqrt(K ** (nivel - 1))

print("=== CHRISTALLER: JERARQUIA k=3, 4 NIVELES ===")
print(f"Radio base r = {R_BASE} km")
print(f"Area hexagono base A = {areas[1]:.4f} km^2")
print()
for nivel in range(1, NIVELES + 1):
    print(
        f"  Nivel {nivel}: r={radios[nivel]:.4f} km | "
        f"A={areas[nivel]:.4f} km^2 | "
        f"Lugares={num_lugares[nivel]}"
    )

# Verificacion de razones
razones_area    = [areas[n + 1] / areas[n] for n in range(1, NIVELES)]
razones_lugares = [num_lugares[n] / num_lugares[n + 1] for n in range(1, NIVELES)]

print()
print("Razon de areas consecutivas (debe ser 3.000):",
      [f"{r:.4f}" for r in razones_area])
print("Razones de lugares consecutivos (18/6=3, 6/2=3, 2/1=2):",
      [f"{r:.4f}" for r in razones_lugares])

# ─────────────────────────────────────────────
# 2. GEOMETRIA DE LA TESELACION HEXAGONAL
# ─────────────────────────────────────────────

def vertices_hexagono(cx, cy, r, rotacion=0.0):
    """Devuelve los 6 vertices de un hexagono centrado en (cx,cy) con radio r."""
    angulos = np.linspace(0, 2 * np.pi, 7)[:-1] + rotacion
    return np.column_stack([cx + r * np.cos(angulos),
                            cy + r * np.sin(angulos)])


def hexagonal_grid(cx0, cy0, r_unit, count):
    """
    Genera exactamente `count` centros en patron hexagonal
    en orden de distancia al centro (cx0, cy0).
    """
    dx = r_unit * np.sqrt(3)
    dy = r_unit * 1.5

    rango = int(np.ceil(np.sqrt(count))) + 2
    candidatos = []
    for q in range(-rango, rango + 1):
        for r_idx in range(-rango, rango + 1):
            x = cx0 + dx * (q + r_idx * 0.5)
            y = cy0 + r_idx * dy
            d = np.hypot(x - cx0, y - cy0)
            candidatos.append((d, x, y))
    candidatos.sort(key=lambda t: t[0])
    return np.array([[c[1], c[2]] for c in candidatos[:count]])


# ─────────────────────────────────────────────
# 3. CONSTRUCCION DE LA JERARQUIA
# ─────────────────────────────────────────────

# Centro global
CX, CY = 0.0, 0.0

r4 = radios[4]   # R_BASE * sqrt(27) ~= 51.9615 km
r3 = radios[3]   # R_BASE * sqrt(9)  = 30.0 km
r2 = radios[2]   # R_BASE * sqrt(3)  ~= 17.3205 km
r1 = radios[1]   # R_BASE            = 10.0 km

# Centros de nivel 3 (2 lugares):
# Para que los hexagonos de nivel 3 (radio r3) queden completamente DENTRO del
# hexagono de nivel 4 (radio r4), los centros n3 deben estar a distancia
# d <= r4 - r3 = 51.9615 - 30 = 21.9615 km del centro.
# Se colocan a distancia exacta d = r4 - r3 en direcciones opuestas (este/oeste)
# para maximizar la separacion visual, verificando que todos los vertices del
# hexagono n3 queden dentro del n4.
d_n3 = r4 - r3  # 21.9615 km
centros_n3 = np.array([
    [CX + d_n3, CY],
    [CX - d_n3, CY],
])

# Centros de nivel 2 (6 lugares): en patron hexagonal alrededor del centro
centros_n2 = hexagonal_grid(CX, CY, r2, 6)

# Centros de nivel 1 (18 lugares): en patron hexagonal denso
centros_n1 = hexagonal_grid(CX, CY, r1, 18)

print(f"\nCentros generados: n4=1, n3={len(centros_n3)}, n2={len(centros_n2)}, n1={len(centros_n1)}")
print(f"Distancia centros n3 al origen: {np.hypot(centros_n3[0,0], centros_n3[0,1]):.4f} km")
print(f"Extension maxima hexagono n3: {d_n3 + r3:.4f} km = r4={r4:.4f} km (exactamente en el borde)")

# Verificar que todos los vertices del hexagono n3 quedan dentro del n4
max_dist_vertices_n3 = 0.0
for cx, cy in centros_n3:
    verts = vertices_hexagono(cx, cy, r3, rotacion=np.pi / 6)
    dists = np.hypot(verts[:, 0] - CX, verts[:, 1] - CY)
    max_dist_vertices_n3 = max(max_dist_vertices_n3, np.max(dists))
print(f"Dist maxima de vertices n3 al centro: {max_dist_vertices_n3:.4f} km (debe <= r4={r4:.4f})")
assert max_dist_vertices_n3 <= r4 + 0.01, "ERROR: hexagono n3 excede el limite del n4"

# ─────────────────────────────────────────────
# 4. FIGURA 1: TESELACION HEXAGONAL ANIDADA
# ─────────────────────────────────────────────

fig1, ax1 = plt.subplots(1, 1, figsize=(12, 11), facecolor=BG)
ax1.set_facecolor(BG)

colores_nivel = {4: AMBER, 3: AZUL, 2: VERDE, 1: GRIS}
alphas_nivel  = {4: 0.12,  3: 0.18, 2: 0.22, 1: 0.28}
lw_nivel      = {4: 2.5,   3: 1.8,  2: 1.2,  1: 0.7}
tamanos_punto = {4: 280,   3: 160,  2: 80,   1: 25}


def dibujar_hexagono(ax, cx, cy, r, color, alpha_fill, lw, rotacion=np.pi/6, zorder_base=1):
    """Dibuja un hexagono con relleno semitransparente y borde visible."""
    v = vertices_hexagono(cx, cy, r, rotacion=rotacion)
    poly_fill = plt.Polygon(v, closed=True, edgecolor=color, facecolor=color,
                            linewidth=lw, alpha=alpha_fill, zorder=zorder_base)
    poly_bord = plt.Polygon(v, closed=True, edgecolor=color, facecolor="none",
                            linewidth=lw, alpha=0.8, zorder=zorder_base + 1)
    ax.add_patch(poly_fill)
    ax.add_patch(poly_bord)


# Dibujar hexagonos nivel 4
dibujar_hexagono(ax1, CX, CY, r4, colores_nivel[4], alphas_nivel[4], lw_nivel[4], zorder_base=1)

# Dibujar hexagonos nivel 3
for cx, cy in centros_n3:
    dibujar_hexagono(ax1, cx, cy, r3, colores_nivel[3], alphas_nivel[3], lw_nivel[3], zorder_base=3)

# Dibujar hexagonos nivel 2
for cx, cy in centros_n2:
    dibujar_hexagono(ax1, cx, cy, r2, colores_nivel[2], alphas_nivel[2], lw_nivel[2], zorder_base=5)

# Dibujar hexagonos nivel 1
for cx, cy in centros_n1:
    dibujar_hexagono(ax1, cx, cy, r1, colores_nivel[1], alphas_nivel[1], lw_nivel[1], zorder_base=7)

# Marcar lugares centrales
# Nivel 1
ax1.scatter(centros_n1[:, 0], centros_n1[:, 1],
            s=tamanos_punto[1], c=colores_nivel[1],
            zorder=10, alpha=0.9, edgecolors="none")

# Nivel 2
ax1.scatter(centros_n2[:, 0], centros_n2[:, 1],
            s=tamanos_punto[2], c=colores_nivel[2],
            zorder=11, alpha=0.95, edgecolors=FG, linewidths=0.5)

# Nivel 3
ax1.scatter(centros_n3[:, 0], centros_n3[:, 1],
            s=tamanos_punto[3], c=colores_nivel[3],
            zorder=12, alpha=0.95, edgecolors=FG, linewidths=0.8)

# Nivel 4
ax1.scatter([CX], [CY], s=tamanos_punto[4], c=AMBER,
            zorder=13, alpha=1.0, edgecolors=FG, linewidths=1.2,
            marker="*")

# Etiqueta del lugar central de orden 4
ax1.annotate("Lugar central\norden 4", xy=(CX, CY),
             xytext=(CX + r4 * 0.28, CY + r4 * 0.28),
             color=AMBER, fontsize=8.5, ha="left",
             arrowprops=dict(arrowstyle="-", color=AMBER, lw=0.8),
             fontweight="bold")

# Leyenda
leyenda_patches = [
    mpatches.Patch(facecolor=AMBER, edgecolor=AMBER,
                   label=f"Nivel 4: 1 metropoli   (A={areas[4]:.0f} km2)"),
    mpatches.Patch(facecolor=AZUL, edgecolor=AZUL,
                   label=f"Nivel 3: 2 ciudades     (A={areas[3]:.0f} km2)"),
    mpatches.Patch(facecolor=VERDE, edgecolor=VERDE,
                   label=f"Nivel 2: 6 villas       (A={areas[2]:.0f} km2)"),
    mpatches.Patch(facecolor=GRIS, edgecolor=GRIS,
                   label=f"Nivel 1: 18 aldeas      (A={areas[1]:.0f} km2)"),
]
leg = ax1.legend(handles=leyenda_patches, loc="lower right",
                 facecolor="#1a2b40", edgecolor=AMBER,
                 labelcolor=FG, fontsize=8.5,
                 title="Jerarquia de lugares centrales",
                 title_fontsize=9)
leg.get_title().set_color(AMBER)

# Escala
escala_x = -r4 * 0.9
escala_y = -r4 * 0.92
ax1.annotate("", xy=(escala_x + 10, escala_y),
             xytext=(escala_x, escala_y),
             arrowprops=dict(arrowstyle="<->", color=FG, lw=1.2))
ax1.text(escala_x + 5, escala_y + 1.5, "10 km",
         color=FG, fontsize=7.5, ha="center")

# Ejes y titulo
margen = r4 * 1.08
ax1.set_xlim(-margen, margen)
ax1.set_ylim(-margen * 1.02, margen * 1.02)
ax1.set_aspect("equal")
ax1.tick_params(colors=GRIS, labelsize=7)
for spine in ax1.spines.values():
    spine.set_edgecolor(GRIS)
    spine.set_linewidth(0.5)
ax1.set_xlabel("km (Oeste-Este)", color=FG, fontsize=8)
ax1.set_ylabel("km (Sur-Norte)", color=FG, fontsize=8)
ax1.xaxis.label.set_color(FG)
ax1.yaxis.label.set_color(FG)
plt.setp(ax1.get_xticklabels(), color=GRIS)
plt.setp(ax1.get_yticklabels(), color=GRIS)

ax1.set_title(
    "Teoria de los lugares centrales  -  Walter Christaller (1933)\n"
    "Principio de mercado k=3  |  Jerarquia de 4 niveles  |  Radio base r = 10 km",
    color=FG, fontsize=11, pad=14, fontweight="bold"
)

plt.tight_layout(pad=1.2)
out1 = os.path.join(ASSETS_DIR, "sim_christaller_lugares_centrales_1.png")
fig1.savefig(out1, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig1)
print(f"\nFigura 1 guardada: {out1}")

# ─────────────────────────────────────────────
# 5. FIGURA 2: PANEL DE BARRAS LOG
# ─────────────────────────────────────────────

fig2, (ax_left, ax_right) = plt.subplots(
    1, 2, figsize=(13, 6), facecolor=BG
)

niveles_arr  = np.array([1, 2, 3, 4])
num_arr      = np.array([num_lugares[n] for n in niveles_arr])
areas_arr    = np.array([areas[n] for n in niveles_arr])
etiq_eje     = ["Nivel 1\n(aldea)", "Nivel 2\n(villa)",
                "Nivel 3\n(ciudad)", "Nivel 4\n(metropoli)"]

colores_barras = [GRIS, VERDE, AZUL, AMBER]

# Barras: numero de lugares
ax_left.set_facecolor(BG)
bars1 = ax_left.bar(niveles_arr, num_arr,
                    color=colores_barras, alpha=0.85,
                    edgecolor=FG, linewidth=0.6, width=0.55)
ax_left.set_yscale("log")
ax_left.set_xticks(niveles_arr)
ax_left.set_xticklabels(etiq_eje, color=FG, fontsize=9)
ax_left.tick_params(colors=GRIS, labelsize=8)
for spine in ax_left.spines.values():
    spine.set_edgecolor(GRIS)
ax_left.set_ylabel("Numero de lugares (escala log)", color=FG, fontsize=9)
ax_left.set_xlabel("Nivel jerarquico", color=FG, fontsize=9)
ax_left.set_title("Distribucion jerarquica de lugares\n(secuencia 1, 2, 6, 18 | k=3)",
                  color=FG, fontsize=10, pad=10)
ax_left.yaxis.label.set_color(FG)
plt.setp(ax_left.get_yticklabels(), color=GRIS)

# Anotar valores
for bar, val in zip(bars1, num_arr):
    ax_left.text(bar.get_x() + bar.get_width() / 2,
                 val * 1.15, str(val),
                 ha="center", va="bottom", color=FG, fontsize=10,
                 fontweight="bold")

ax_left.axhline(1, color=AMBER, lw=0.5, ls="--", alpha=0.3)

# Barras: areas de mercado
ax_right.set_facecolor(BG)
bars2 = ax_right.bar(niveles_arr, areas_arr,
                     color=colores_barras, alpha=0.85,
                     edgecolor=FG, linewidth=0.6, width=0.55)
ax_right.set_yscale("log")
ax_right.set_xticks(niveles_arr)
ax_right.set_xticklabels(etiq_eje, color=FG, fontsize=9)
ax_right.tick_params(colors=GRIS, labelsize=8)
for spine in ax_right.spines.values():
    spine.set_edgecolor(GRIS)
ax_right.set_ylabel("Area de mercado (km2, escala log)", color=FG, fontsize=9)
ax_right.set_xlabel("Nivel jerarquico", color=FG, fontsize=9)
ax_right.set_title("Areas de mercado por nivel\n(factor x3 por nivel superior)",
                   color=FG, fontsize=10, pad=10)
ax_right.yaxis.label.set_color(FG)
plt.setp(ax_right.get_yticklabels(), color=GRIS)

for bar, val in zip(bars2, areas_arr):
    ax_right.text(bar.get_x() + bar.get_width() / 2,
                  val * 1.12, f"{val:.0f}",
                  ha="center", va="bottom", color=FG, fontsize=9.5,
                  fontweight="bold")

fig2.suptitle(
    "Christaller (1933) - Principio de mercado k = 3\n"
    "Propiedades escalares de la jerarquia urbana",
    color=FG, fontsize=12, fontweight="bold", y=1.01
)

plt.tight_layout(pad=1.5)
out2 = os.path.join(ASSETS_DIR, "sim_christaller_lugares_centrales_2.png")
fig2.savefig(out2, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig2)
print(f"Figura 2 guardada: {out2}")

# ─────────────────────────────────────────────
# 6. VALIDACION
# ─────────────────────────────────────────────

area_base_calculada = area_hexagono(R_BASE)
area_base_esperada  = (3.0 * np.sqrt(3) / 2.0) * 100.0  # 259.8076...

razon_areas_12    = areas[2] / areas[1]
razon_areas_23    = areas[3] / areas[2]
razon_areas_34    = areas[4] / areas[3]
razon_lugares_12  = num_lugares[1] / num_lugares[2]    # 18/6=3
razon_lugares_23  = num_lugares[2] / num_lugares[3]    # 6/2=3
razon_lugares_34  = num_lugares[3] / num_lugares[4]    # 2/1=2

print("\n=== VALIDACION ===")
print(f"Area base = {area_base_calculada:.6f} km2 (esperado ~259.8076)")
print(f"Razon areas 1->2: {razon_areas_12:.6f} (debe ser 3.000 +/-0.001)")
print(f"Razon areas 2->3: {razon_areas_23:.6f} (debe ser 3.000 +/-0.001)")
print(f"Razon areas 3->4: {razon_areas_34:.6f} (debe ser 3.000 +/-0.001)")
print(f"Razon lugares 1/2: {razon_lugares_12:.6f} (debe ser 3.000 +/-0.001)")
print(f"Razon lugares 2/3: {razon_lugares_23:.6f} (debe ser 3.000 +/-0.001)")
print(f"Razon lugares 3/4: {razon_lugares_34:.6f} (debe ser 2.000 +/-0.001; factor correcto en tope)")
print(f"Error area base vs formula: {abs(area_base_calculada - area_base_esperada):.8f} km2")

# Criterio de validacion correcto:
# - razones de areas: todas deben ser 3 (+-0.001): OK siempre por construccion.
# - razones de lugares: las razones n1/n2 y n2/n3 deben ser 3 (+-0.001);
#   la razon n3/n4 debe ser 2 (+-0.001) -- factor correcto del tope en la
#   secuencia 1,2,6,18 de Christaller k=3 con 4 niveles.
razon_areas_OK   = all(abs(r - 3.0) < 0.001 for r in razones_area)
razon_lugares_OK = (
    abs(razon_lugares_12 - 3.0) < 0.001 and
    abs(razon_lugares_23 - 3.0) < 0.001 and
    abs(razon_lugares_34 - 2.0) < 0.001
)
error_area_OK = abs(area_base_calculada - area_base_esperada) < 0.01

print(f"\nrazon_areas_OK = {razon_areas_OK}")
print(f"razon_lugares_OK = {razon_lugares_OK}  (18/6=3, 6/2=3, 2/1=2)")
print(f"error_area_OK = {error_area_OK}")
print(f"Todos los criterios satisfechos: {razon_areas_OK and razon_lugares_OK and error_area_OK}")

# ─────────────────────────────────────────────
# 7. RESPUESTAS A LAS PREGUNTAS
# ─────────────────────────────────────────────

# P1: numero de lugares de orden 1 (nivel mas bajo) en la jerarquia realmente
# simulada. Secuencia canonica de Christaller k=3 con 4 niveles:
#   orden4=1, orden3=2, orden2=6, orden1=18  (factores 2,3,3).
# Este es exactamente el conteo que generan los PNG y num_lugares.
respuesta_p1 = int(num_lugares[1])             # 18

# P2: area del hexagono base
respuesta_p2 = float(area_hexagono(R_BASE))    # 259.8076... km2

# P3: area de mercado nivel 4 = area_base * 3^3 = 259.8076 * 27
respuesta_p3 = float(areas[4])                 # 7014.8058 km2

print("\n=== RESPUESTAS ===")
print(f"P1 (lugares de orden 1, secuencia Christaller k=3 1,2,6,18): {respuesta_p1}")
print(f"P2 (area hexagono base, km2): {respuesta_p2:.4f}")
print(f"P3 (area nivel 4, km2): {respuesta_p3:.4f}")

# ─────────────────────────────────────────────
# 8. GUARDAR DATOS JSON
# ─────────────────────────────────────────────

datos = {
    "teoria":  "christaller_lugares_centrales",
    "nombre":  "Teoria de los lugares centrales (jerarquia k=3)",
    "autor":   "Walter Christaller",
    "anio":    "1933",
    "parametros": {
        "k":            K,
        "niveles":      NIVELES,
        "r_base_km":    R_BASE,
    },
    "areas_por_nivel_km2": {str(n): round(areas[n], 6) for n in range(1, NIVELES + 1)},
    "num_lugares_por_nivel": {str(n): num_lugares[n] for n in range(1, NIVELES + 1)},
    "radios_por_nivel_km": {str(n): round(radios[n], 6) for n in range(1, NIVELES + 1)},
    "razones_areas_consecutivas":   [round(r, 8) for r in razones_area],
    "razones_lugares_consecutivos": [round(r, 8) for r in razones_lugares],
    "validacion": {
        "area_base_calculada_km2":  round(area_base_calculada, 6),
        "area_base_esperada_km2":   round(area_base_esperada, 6),
        "error_area_km2":           round(abs(area_base_calculada - area_base_esperada), 8),
        "error_area_OK":            bool(error_area_OK),
        "razon_areas_OK":           bool(razon_areas_OK),
        "razon_lugares_OK":         bool(razon_lugares_OK),
        "nota_razon_lugares": (
            "Las razones correctas de lugares son 18/6=3, 6/2=3, 2/1=2. "
            "El factor 2 en el tope (niveles 3->4) es correcto para Christaller k=3 "
            "con 4 niveles segun la secuencia 1,2,6,18 (factores 2,3,3,3)."
        ),
        "hexagonos_n3_dentro_n4":   bool(max_dist_vertices_n3 <= r4 + 0.01),
        "dist_max_vertices_n3_km":  round(float(max_dist_vertices_n3), 6),
        "todos_criterios_OK":       bool(razon_areas_OK and razon_lugares_OK and error_area_OK),
    },
    "respuestas": {
        "p1_lugares_orden1":        respuesta_p1,
        "p2_area_base_km2":         round(respuesta_p2, 4),
        "p3_area_nivel4_km2":       round(respuesta_p3, 4),
    },
    "centros_generados": {
        "nivel_4": [[round(CX, 4), round(CY, 4)]],
        "nivel_3": centros_n3.round(4).tolist(),
        "nivel_2": centros_n2.round(4).tolist(),
        "nivel_1": centros_n1.round(4).tolist(),
    },
}

json_path = os.path.join(BASE_DIR, "datos_christaller_lugares_centrales.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)
print(f"\nDatos guardados: {json_path}")
print("\nSimulacion completada correctamente.")
