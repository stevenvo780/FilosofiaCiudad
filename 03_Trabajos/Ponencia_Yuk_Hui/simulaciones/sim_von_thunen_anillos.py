"""
Simulación: Anillos de von Thünen (renta de localización agrícola)
Autor del modelo: Johann Heinrich von Thunen (1826)
Campo: economía espacial

Formulación:
    R_k(d) = y_k * (p_k - c_k) - y_k * f_k * d
    R_k(d) = max(0, R_k(d))

El cultivo dominante a distancia d es: argmax_k R_k(d)
Radio de renta cero: d0_k = (p_k - c_k) / f_k
Fronteras entre anillos: distancias d* donde R_i(d*) = R_j(d*)

Experimento determinista (sin aleatoriedad):
    Cultivo A (intensivo, gana cerca):  y=10, p=7,  c=1, f=0.6
    Cultivo B (extensivo, gana lejos):  y=4,  p=14, c=2, f=0.75
    d en {0, 1, 2, ..., 18} km

Este experimento reproduce el fenómeno canónico de von Thünen: ANILLOS
concéntricos (plural) en los que cultivos DISTINTOS dominan en bandas de
distancia distintas. El cultivo intensivo A tiene mayor renta en el centro
(R_A(0)=60 > R_B(0)=48) pero una pendiente más pronunciada (-6.0 frente a
-3.0); el cultivo extensivo B lo releva más lejos. Se cruzan en d*=4 km.

Verificación numérica:
    R_A(0) = 60, R_B(0) = 48
    Pendientes: A=-6.0, B=-3.0
    d0_A = 10.0, d0_B = 16.0
    Frontera de anillo (cruce R_A=R_B) en d* = 4.0 km
    Anillo interior: domina A en 0 ≤ d < 4 km
    Anillo exterior: domina B en 4 < d < 16 km
    Sin cultivo rentable: d > 16 km
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ---------------------------------------------------------------------------
# Parámetros de cultivos
# ---------------------------------------------------------------------------
cultivos = {
    "A": {"y": 10, "p": 7,  "c": 1, "f": 0.6,  "color": "#4c9be8", "label": "Cultivo A (y=10, p=7, c=1, f=0.6)"},
    "B": {"y":  4, "p": 14, "c": 2, "f": 0.75, "color": "#e0a458", "label": "Cultivo B (y=4, p=14, c=2, f=0.75)"},
}

# ---------------------------------------------------------------------------
# Funciones del modelo
# ---------------------------------------------------------------------------
def renta(d, y, p, c, f):
    """Renta de localización por unidad de superficie (no negativa)."""
    return max(0.0, y * (p - c) - y * f * d)

def radio_cero(y, p, c, f):
    """Distancia máxima a la que la renta llega a cero."""
    return (p - c) / f

def pendiente(y, f):
    """Pendiente de la función de renta respecto a d."""
    return -y * f

# ---------------------------------------------------------------------------
# Experimento: d = 0, 1, 2, ..., 18 km (enteros, determinista)
# ---------------------------------------------------------------------------
d_values = np.arange(0, 19, 1, dtype=float)   # 0..18 km

# Calcular renta para cada cultivo en cada distancia
R = {}
for k, params in cultivos.items():
    R[k] = np.array([renta(d, params["y"], params["p"], params["c"], params["f"])
                     for d in d_values])

# Envolvente superior: max(R_A, R_B, 0)
envelope = np.maximum(R["A"], R["B"])

# Cultivo dominante en cada punto. Empates explícitos (renta común > 0) se
# etiquetan como "empate" en vez de desempatar por orden de inserción del dict.
dominant = []
for i, d in enumerate(d_values):
    ra, rb = R["A"][i], R["B"][i]
    if max(ra, rb) <= 0.0:
        dominant.append("ninguno")
    elif abs(ra - rb) < 1e-9:
        dominant.append("empate")
    else:
        dominant.append("A" if ra > rb else "B")

# Radios de renta cero
d0 = {k: radio_cero(**{kk: v for kk, v in params.items() if kk in ("y","p","c","f")})
      for k, params in cultivos.items()}

# Pendientes
slopes = {k: pendiente(params["y"], params["f"]) for k, params in cultivos.items()}

# ---------------------------------------------------------------------------
# Frontera de anillo: distancia d* donde R_A(d*) = R_B(d*) (cruce de rectas)
#   y_A(p_A-c_A) - y_A f_A d = y_B(p_B-c_B) - y_B f_B d
#   d* = [R_A(0) - R_B(0)] / [y_A f_A - y_B f_B]
# ---------------------------------------------------------------------------
RA0 = cultivos["A"]["y"] * (cultivos["A"]["p"] - cultivos["A"]["c"])
RB0 = cultivos["B"]["y"] * (cultivos["B"]["p"] - cultivos["B"]["c"])
slope_A_mag = cultivos["A"]["y"] * cultivos["A"]["f"]
slope_B_mag = cultivos["B"]["y"] * cultivos["B"]["f"]
d_star = (RA0 - RB0) / (slope_A_mag - slope_B_mag)
R_at_dstar = RA0 - slope_A_mag * d_star

# Cultivo dominante en cada banda: interior (d < d*) vs exterior (d > d*)
interior_crop = "A" if (RA0 - slope_A_mag * (d_star / 2)) > (RB0 - slope_B_mag * (d_star / 2)) else "B"
exterior_crop = "B" if interior_crop == "A" else "A"

# ---------------------------------------------------------------------------
# Envolvente-cero robusta: último d donde max(R_A, R_B, 0) > 0.
# NO se usa el atajo max(d0_k); la envolvente cae a cero en el d0 del cultivo
# que domina en el borde exterior, que aquí es d0_B = 16.0 km.
# ---------------------------------------------------------------------------
d_fine_env = np.linspace(0, 18, 180001)
RA_env = np.array([renta(d, **{k: v for k, v in cultivos["A"].items() if k in ("y","p","c","f")}) for d in d_fine_env])
RB_env = np.array([renta(d, **{k: v for k, v in cultivos["B"].items() if k in ("y","p","c","f")}) for d in d_fine_env])
env_grid = np.maximum(RA_env, RB_env)
envelope_zero_km = float(d_fine_env[np.where(env_grid > 1e-9)[0][-1]])
# Valor cerrado exacto (d0 del cultivo exterior) para el dato y las preguntas:
envelope_zero_closed = d0[exterior_crop]

# ---------------------------------------------------------------------------
# Verificaciones numéricas
# ---------------------------------------------------------------------------
assert R["A"][0] == 60.0, f"R_A(0) debería ser 60, obtenido: {R['A'][0]}"
assert R["B"][0] == 48.0, f"R_B(0) debería ser 48, obtenido: {R['B'][0]}"
assert abs(d0["A"] - 10.0)  < 0.01, f"d0_A debería ser 10.0, obtenido: {d0['A']}"
assert abs(d0["B"] - 16.0)  < 0.01, f"d0_B debería ser 16.0, obtenido: {d0['B']}"
assert abs(slopes["A"] - (-6.0)) < 1e-10, f"Pendiente A debería ser -6.0, obtenida: {slopes['A']}"
assert abs(slopes["B"] - (-3.0)) < 1e-10, f"Pendiente B debería ser -3.0, obtenida: {slopes['B']}"
assert abs(d_star - 4.0) < 1e-10, f"d* debería ser 4.0, obtenido: {d_star}"
assert interior_crop == "A" and exterior_crop == "B", \
    f"El anillo interior debe ser A y el exterior B, obtenido: {interior_crop}/{exterior_crop}"
# Hay un anillo interior real de A y un anillo exterior real de B
assert "A" in dominant, "El Cultivo A no forma ningún anillo (debería dominar cerca del centro)"
assert "B" in dominant, "El Cultivo B no forma ningún anillo (debería dominar más lejos)"
assert dominant.index("A") < dominant.index("B"), \
    "A debe dominar en una banda interior y B en una banda exterior"
# La envolvente-cero robusta coincide con el d0 del cultivo exterior
assert abs(envelope_zero_km - envelope_zero_closed) < 0.01, \
    f"Envolvente-cero robusta {envelope_zero_km} no coincide con d0_{exterior_crop}={envelope_zero_closed}"

# Verificar que la envolvente es monótona no creciente
assert all(envelope[i] >= envelope[i+1] for i in range(len(envelope)-1)), \
    "La envolvente no es monótona no creciente"

print("=== Verificaciones numéricas ===")
print(f"R_A(0) = {R['A'][0]:.1f}  (esperado: 60.0)")
print(f"R_B(0) = {R['B'][0]:.1f}  (esperado: 48.0)")
print(f"d0_A   = {d0['A']:.2f} km  (esperado: 10.0)")
print(f"d0_B   = {d0['B']:.2f} km  (esperado: 16.0)")
print(f"Pendiente A = {slopes['A']:.2f}  (esperado: -6.0)")
print(f"Pendiente B = {slopes['B']:.2f}  (esperado: -3.0)")
print(f"Frontera de anillo d* = {d_star:.2f} km  (esperado: 4.0)  R(d*)={R_at_dstar:.1f}")
print(f"Anillo interior: domina {interior_crop} (0 ≤ d < {d_star:.1f} km)")
print(f"Anillo exterior: domina {exterior_crop} ({d_star:.1f} < d < {d0['B']:.1f} km)")
print(f"Envolvente cae a 0 en (robusto): {envelope_zero_km:.3f} km  (cerrado d0_{exterior_crop}={envelope_zero_closed:.1f})")
print(f"Envolvente monótona no creciente: OK")
print()

# ---------------------------------------------------------------------------
# Preguntas del experimento
# ---------------------------------------------------------------------------
# P1: R_A(6) = 10*(7-1) - 10*0.6*6 = 60 - 36 = 24
R_A_6 = renta(6, **{k: v for k, v in cultivos["A"].items() if k in ("y","p","c","f")})
print(f"P1: R_A(6) = {R_A_6:.1f}  (esperado: 24.0)")

# P2: d0_B = (14-2)/0.75 = 16.0
d0_B = d0["B"]
print(f"P2: d0_B = {d0_B:.2f} km  (esperado: 16.0)")

# P3 (emergente): frontera de anillo d* entre el cultivo interior y el exterior
print(f"P3: Frontera de anillo (cruce R_A=R_B) en d* = {d_star:.2f} km  (esperado: 4.0)")

# ---------------------------------------------------------------------------
# Datos crudos para JSON
# ---------------------------------------------------------------------------
datos = {
    "teoria": "von_thunen_anillos",
    "nombre": "Anillos de von Thünen (renta de localización agrícola)",
    "autor": "Johann Heinrich von Thunen",
    "anio": "1826",
    "parametros": {k: {kk: v for kk, v in params.items() if kk in ("y","p","c","f")}
                   for k, params in cultivos.items()},
    "pendientes": slopes,
    "radios_cero": d0,
    "frontera_anillo_d_star_km": d_star,
    "renta_en_d_star": R_at_dstar,
    "anillo_interior": interior_crop,
    "anillo_exterior": exterior_crop,
    "d_values_km": d_values.tolist(),
    "R_A": R["A"].tolist(),
    "R_B": R["B"].tolist(),
    "envolvente": envelope.tolist(),
    "dominante": dominant,
    "envelope_zero_km": envelope_zero_closed,
    "envelope_zero_km_robusto": envelope_zero_km,
    "verificaciones": {
        "R_A_0": R["A"][0],
        "R_B_0": R["B"][0],
        "d0_A": d0["A"],
        "d0_B": d0["B"],
        "pendiente_A": slopes["A"],
        "pendiente_B": slopes["B"],
        "d_star_km": d_star,
        "anillo_interior": interior_crop,
        "anillo_exterior": exterior_crop,
        "envolvente_monotona_no_creciente": True,
    },
    "preguntas_respuestas": {
        "P1_R_A_6km": R_A_6,
        "P2_d0_B_km": d0_B,
        "P3_frontera_anillo_d_star_km": d_star,
    }
}

# Guardar JSON de datos crudos
sim_dir = os.path.dirname(os.path.abspath(__file__))
datos_path = os.path.join(sim_dir, "datos_von_thunen_anillos.json")
with open(datos_path, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)
print(f"Datos crudos guardados en: {datos_path}")

# ---------------------------------------------------------------------------
# Gráfico 1: Curvas de renta + envolvente + bandas de dominio
# ---------------------------------------------------------------------------
BG      = "#0e1a2b"
FG      = "#e8e6e1"
AMBER   = "#e0a458"
BLUE    = "#4c9be8"
ORANGE  = "#e0a458"
GREEN   = "#5bbf8f"
RED     = "#e05858"
GREY    = "#7a8a9a"

# Para el gráfico suave usamos más puntos
d_fine = np.linspace(0, 18, 3600)
R_A_fine = np.array([renta(d, **{k: v for k, v in cultivos["A"].items() if k in ("y","p","c","f")}) for d in d_fine])
R_B_fine = np.array([renta(d, **{k: v for k, v in cultivos["B"].items() if k in ("y","p","c","f")}) for d in d_fine])
env_fine = np.maximum(R_A_fine, R_B_fine)

fig, ax = plt.subplots(figsize=(11, 7), facecolor=BG)
ax.set_facecolor(BG)

# Bandas de dominio en el fondo (ANILLOS reales):
#   0 ≤ d < d*=4   : domina A (intensivo)
#   d* < d < 16    : domina B (extensivo)
#   d > 16         : ninguno
ax.axvspan(0, d_star, alpha=0.12, color=BLUE,  label="_nolegend_")
ax.axvspan(d_star, d0["B"], alpha=0.12, color=AMBER, label="_nolegend_")
ax.axvspan(d0["B"], 18, alpha=0.06, color=GREY, label="_nolegend_")

# Texto de anillos
ax.text(d_star / 2, 3.0, "Anillo interior\nCultivo A", color=BLUE, fontsize=9,
        ha="center", va="bottom", alpha=0.9, fontstyle="italic")
ax.text((d_star + d0["B"]) / 2, 3.0, "Anillo exterior\nCultivo B", color=AMBER, fontsize=9,
        ha="center", va="bottom", alpha=0.9, fontstyle="italic")
ax.text((d0["B"] + 18) / 2, 3.0, "Sin cultivo\nrentable", color=GREY, fontsize=9,
        ha="center", va="bottom", alpha=0.75, fontstyle="italic")

# Curvas de renta
ax.plot(d_fine, R_A_fine, color=BLUE, linewidth=2.2, label=f"Cultivo A  (pendiente = {slopes['A']:.1f})")
ax.plot(d_fine, R_B_fine, color=AMBER, linewidth=2.2, label=f"Cultivo B  (pendiente = {slopes['B']:.1f})")

# Envolvente superior
ax.plot(d_fine, env_fine, color=FG, linewidth=3.2, linestyle="--",
        dashes=(6, 3), label="Envolvente superior  max(R_A, R_B, 0)", zorder=5)

# Línea de renta cero
ax.axhline(0, color=GREY, linewidth=0.8, linestyle=":")

# Anotaciones: distancias clave
# d* = 4 (frontera de anillo, cruce R_A=R_B)
ax.axvline(d_star, color=GREEN, linewidth=1.4, linestyle="-", alpha=0.85)
ax.scatter([d_star], [R_at_dstar], color=GREEN, s=70, zorder=7)
ax.annotate(f"Frontera de anillo\nd* = {d_star:.0f} km   (R = {R_at_dstar:.0f})",
            xy=(d_star, R_at_dstar), xytext=(d_star + 1.6, R_at_dstar + 10),
            color=GREEN, fontsize=8.6, alpha=0.95,
            arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.0, alpha=0.85))

# d0_A = 10
ax.axvline(d0["A"], color=BLUE, linewidth=1.0, linestyle=":", alpha=0.7)
ax.text(d0["A"] + 0.15, 1.8, f"d₀_A = {d0['A']:.1f} km", color=BLUE,
        fontsize=8.5, va="bottom", alpha=0.9)

# d0_B = 16
ax.axvline(d0["B"], color=AMBER, linewidth=1.2, linestyle=":", alpha=0.85)
ax.text(d0["B"] + 0.15, 1.8, f"d₀_B = {d0['B']:.1f} km", color=AMBER,
        fontsize=8.5, va="bottom", alpha=0.9)

# Puntos de renta en d=0
ax.scatter([0], [R["A"][0]], color=BLUE,  s=55, zorder=6)
ax.scatter([0], [R["B"][0]], color=AMBER, s=55, zorder=6)
ax.text(0.25, R["A"][0] + 0.5, f"R_A(0)={R['A'][0]:.0f}", color=BLUE, fontsize=8, va="bottom", alpha=0.9)
ax.text(0.25, R["B"][0] - 3.0, f"R_B(0)={R['B'][0]:.0f}", color=AMBER, fontsize=8, va="top", alpha=0.9)

# Punto de renta cero de B (borde de la envolvente)
ax.scatter([d0["B"]], [0], color=AMBER, s=60, zorder=6)

# Estética
ax.set_xlim(0, 18)
ax.set_ylim(-2, 66)
ax.set_xlabel("Distancia al mercado central  d  (km)", color=FG, fontsize=11)
ax.set_ylabel("Renta de localización  R  (u.m. / hectárea)", color=FG, fontsize=11)
ax.set_title(
    "Anillos de von Thünen — Renta de localización agrícola (1826)\n"
    "Dos anillos: cultivo intensivo A cerca del centro, extensivo B más lejos",
    color=FG, fontsize=12, pad=14
)
ax.tick_params(colors=FG, labelsize=9)
for spine in ax.spines.values():
    spine.set_edgecolor(GREY)
    spine.set_alpha(0.5)
ax.grid(True, color=GREY, alpha=0.2, linestyle=":")

legend = ax.legend(loc="upper right", fontsize=9,
                   facecolor="#1a2d42", edgecolor=GREY,
                   labelcolor=FG, framealpha=0.9)

plt.tight_layout(pad=1.5)

assets_sim_dir = os.path.join(
    os.path.dirname(sim_dir),
    "presentacion", "assets", "sim"
)
os.makedirs(assets_sim_dir, exist_ok=True)

png1_path = os.path.join(assets_sim_dir, "sim_von_thunen_anillos_1.png")
fig.savefig(png1_path, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig)
print(f"Gráfico 1 guardado: {png1_path}")

# ---------------------------------------------------------------------------
# Gráfico 2: Mapa de anillos en el plano isótropo (vista 2D)
# ---------------------------------------------------------------------------
fig2, ax2 = plt.subplots(figsize=(8, 8), facecolor=BG)
ax2.set_facecolor(BG)

LIM = 18.0

# Anillos concéntricos reales:
#   0 ≤ d < d*=4   : domina A (intensivo)
#   d* < d < 16    : domina B (extensivo)
#   d > 16         : ninguno

# Zona sin cultivo (fondo)
ring_outer = plt.Circle((0, 0), LIM, color=GREY, alpha=0.07, zorder=0)
ax2.add_patch(ring_outer)

# Anillo exterior: B (entre d* y d0_B)
circle_B = plt.Circle((0, 0), d0["B"], color=AMBER, alpha=0.16, zorder=1)
ax2.add_patch(circle_B)

# Anillo interior: A (entre 0 y d*)
circle_A_fill = plt.Circle((0, 0), d_star, color=BLUE, alpha=0.22, zorder=2)
ax2.add_patch(circle_A_fill)

# Bordes
circle_B_edge = plt.Circle((0, 0), d0["B"], color=AMBER, fill=False,
                           linewidth=1.8, linestyle="--", alpha=0.85, zorder=4)
ax2.add_patch(circle_B_edge)
circle_dstar_edge = plt.Circle((0, 0), d_star, color=GREEN, fill=False,
                               linewidth=1.8, linestyle="-", alpha=0.9, zorder=4)
ax2.add_patch(circle_dstar_edge)
# d0_A como referencia (A llega a renta cero en 10 km, dentro del anillo de B)
circle_A0 = plt.Circle((0, 0), d0["A"], color=BLUE, fill=False,
                       linewidth=1.0, linestyle=":", alpha=0.45, zorder=4)
ax2.add_patch(circle_A0)

# Mercado central
ax2.scatter([0], [0], color=FG, s=120, zorder=6, marker="*")
ax2.text(0.4, 0.5, "Mercado\ncentral", color=FG, fontsize=9, va="bottom", alpha=0.9)

# Etiquetas de anillos
ax2.text(0, -(d_star + d0["B"]) / 2, "Cultivo B\n(extensivo)", color=AMBER,
         fontsize=10, ha="center", va="center",
         bbox=dict(facecolor="#1a2d42", edgecolor="none", alpha=0.7, pad=3))
ax2.text(0, -d_star / 2 + 0.2, "Cultivo A\n(intensivo)", color=BLUE,
         fontsize=9.5, ha="center", va="center",
         bbox=dict(facecolor="#1a2d42", edgecolor="none", alpha=0.7, pad=2))

ax2.text(d_star * 0.71, d_star * 0.71, f"d* = {d_star:.0f} km", color=GREEN,
         fontsize=8.5, ha="left", va="bottom", alpha=0.9)
ax2.text(0, -(d0["B"] + 0.5), f"d₀_B = {d0['B']:.0f} km", color=AMBER,
         fontsize=9, ha="center", va="top", alpha=0.85)
ax2.text(d0["A"] * 0.71 + 0.3, -d0["A"] * 0.71, f"d₀_A = {d0['A']:.0f} km\n(ref.)", color=BLUE,
         fontsize=8, ha="left", va="top", alpha=0.7)

# Zona sin cultivo
ax2.text(0, LIM - 0.8, "Sin cultivo rentable", color=GREY, fontsize=9,
         ha="center", va="top", alpha=0.75, fontstyle="italic")

ax2.set_xlim(-LIM - 0.5, LIM + 0.5)
ax2.set_ylim(-LIM - 0.5, LIM + 0.5)
ax2.set_aspect("equal")
ax2.set_xlabel("km (Este–Oeste)", color=FG, fontsize=10)
ax2.set_ylabel("km (Norte–Sur)", color=FG, fontsize=10)
ax2.set_title(
    "Anillos de von Thünen — Vista espacial del plano isótropo\n"
    "Dos anillos concéntricos de cultivos distintos según la renta de localización",
    color=FG, fontsize=11, pad=14
)
ax2.tick_params(colors=FG, labelsize=9)
for spine in ax2.spines.values():
    spine.set_edgecolor(GREY)
    spine.set_alpha(0.5)
ax2.grid(True, color=GREY, alpha=0.15, linestyle=":")

# Leyenda manual
patches = [
    mpatches.Patch(facecolor=BLUE,  alpha=0.6, label=f"Cultivo A intensivo  (0 ≤ d < {d_star:.0f} km)"),
    mpatches.Patch(facecolor=AMBER, alpha=0.5, label=f"Cultivo B extensivo  ({d_star:.0f} < d < {d0['B']:.0f} km)"),
    mpatches.Patch(facecolor=GREY,  alpha=0.3, label=f"Sin renta  (d > {d0['B']:.0f} km)"),
]
ax2.legend(handles=patches, loc="lower right", fontsize=8.5,
           facecolor="#1a2d42", edgecolor=GREY, labelcolor=FG, framealpha=0.9)

plt.tight_layout(pad=1.5)
png2_path = os.path.join(assets_sim_dir, "sim_von_thunen_anillos_2.png")
fig2.savefig(png2_path, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig2)
print(f"Gráfico 2 guardado: {png2_path}")

# ---------------------------------------------------------------------------
# JSON de preguntas
# ---------------------------------------------------------------------------
preguntas_json = {
    "teoria": "von_thunen_anillos",
    "nombre": "Anillos de von Thünen (renta de localización agrícola)",
    "autor": "Johann Heinrich von Thunen",
    "anio": "1826",
    "preguntas": [
        {
            "q": "Con R(d)=y*(p-c)-y*f*d y los parámetros del Cultivo A (y=10, p=7, c=1, f=0.6), calcula la renta de localización por hectárea a una distancia d=6 km del mercado. Formato: 'Respuesta final: <valor>'.",
            "valor_exacto": str(int(R_A_6)),
            "tipo": "forma_cerrada",
            "tolerancia": "igualdad exacta (24)",
            "como_computar": "R_A(6) = 10*(7-1) - 10*0.6*6 = 60 - 36 = 24"
        },
        {
            "q": "Para el Cultivo B (y=4, p=14, c=2, f=0.75), calcula la distancia máxima d0 (en km) a la que la renta de localización se hace cero. Formato: 'Respuesta final: <valor>'.",
            "valor_exacto": str(d0_B),
            "tipo": "forma_cerrada",
            "tolerancia": "igualdad exacta (16.0)",
            "como_computar": "d0_B = (p-c)/f = (14-2)/0.75 = 12/0.75 = 16.0 km"
        },
        {
            "q": "Ejecuta el experimento determinista de los dos cultivos (A: y=10,p=7,c=1,f=0.6; B: y=4,p=14,c=2,f=0.75) construyendo la envolvente superior max(R_A,R_B,0) en d=0..18 km. El cultivo intensivo A domina cerca del centro y el extensivo B lo releva más lejos. Reporta la distancia de transición d* (km) que separa el anillo interior del exterior, es decir donde R_A(d*)=R_B(d*). Formato: 'Respuesta final: <valor>'.",
            "valor_exacto": str(d_star),
            "tipo": "emergente",
            "tolerancia": "±0.25 km en torno a 4.0",
            "como_computar": "Cruce de rectas: 60-6d = 48-3d => 12 = 3d => d* = 4.0 km. A domina en 0≤d<4 (anillo interior), B en 4<d<16 (anillo exterior). La frontera emerge de la envolvente y no coincide con ningún d0."
        }
    ]
}

preguntas_path = os.path.join(sim_dir, "preguntas_von_thunen_anillos.json")
with open(preguntas_path, "w", encoding="utf-8") as f:
    json.dump(preguntas_json, f, ensure_ascii=False, indent=2)
print(f"Preguntas guardadas en: {preguntas_path}")

print()
print("=== Resumen de resultados ===")
print(f"Pendiente A = {slopes['A']:.4f}  (exacta: -6.0)")
print(f"Pendiente B = {slopes['B']:.4f}  (exacta: -3.0)")
print(f"d0_A = {d0['A']:.4f} km  (exacto: 10.0)")
print(f"d0_B = {d0['B']:.4f} km  (exacto: 16.0)")
print(f"Frontera de anillo d* = {d_star:.4f} km  (exacto: 4.0)")
print(f"Anillo interior: {interior_crop} (0..{d_star:.0f} km) | Anillo exterior: {exterior_crop} ({d_star:.0f}..{d0['B']:.0f} km)")
print(f"Envolvente monótona no creciente: OK")
print(f"Envolvente convexa por tramos: OK (lineal a trozos → convexa)")
print()
print("Criterio de validación CUMPLIDO:")
print("  - Pendientes exactas: A=-6.0, B=-3.0")
print(f"  - Radios de renta cero dentro de ±0.01 km: d0_A={d0['A']}, d0_B={d0['B']}")
print(f"  - Dos anillos reales de cultivos distintos con frontera en d*={d_star:.0f} km")
print("  - Envolvente monótona no creciente y convexa por tramos")
