"""
Simulacion: Escalamiento urbano superlineal de Bettencourt-West (2007)
======================================================================
Implementacion de la ley de potencias urbanas:
    Y = Y_0 * N^beta

Referencia: Bettencourt, L.M.A., Lobo, J., Helbing, D., Kuhnert, C. & West, G.B. (2007).
"Growth, innovation, scaling, and the pace of life in cities."
PNAS, 104(17), 7301-7306.

Ejecutar con:
    /home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/.venv/bin/python \
        simulaciones/sim_bettencourt_west_escalamiento.py
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy import stats
import os

# ---------------------------------------------------------------------------
# Parametros del experimento (deterministico, sin semilla aleatoria)
# ---------------------------------------------------------------------------
BETA_SOCIOECON  = 1.15   # superlineal: creacion socioeconomica
BETA_INFRAESTR  = 0.85   # sublineal:   infraestructura
BETA_LINEAL     = 1.00   # lineal:      necesidades individuales
Y_0             = 1.0    # coeficiente de normalizacion

# Ciudades del experimento literal
N_LITERALES = [100_000, 200_000, 1_000_000]

# Nube de 50 ciudades espaciadas logaritmicamente para regresion
N_MIN  = 10_000
N_MAX  = 5_000_000
N_NUBE = 50

# ---------------------------------------------------------------------------
# Colores / estetica (fondo oscuro)
# ---------------------------------------------------------------------------
BG_COLOR    = "#0e1a2b"
TEXT_COLOR  = "#e8e6e1"
AMBER       = "#e0a458"
CYAN_SOFT   = "#6ec6ca"
GREEN_SOFT  = "#7ec98e"
RED_SOFT    = "#e07070"

# ---------------------------------------------------------------------------
# Calculo de la ley de potencias
# ---------------------------------------------------------------------------
def escalamiento(N, beta=BETA_SOCIOECON, Y_0=Y_0):
    """Ley de escalamiento urbano Y = Y_0 * N^beta."""
    return Y_0 * np.asarray(N, dtype=float) ** beta


# ---------------------------------------------------------------------------
# 1. Ciudades literales del enunciado
# ---------------------------------------------------------------------------
N_lit = np.array(N_LITERALES, dtype=float)
Y_lit = escalamiento(N_lit, BETA_SOCIOECON)

verificacion_lit = {
    "Y(100000)":   float(Y_lit[0]),
    "Y(200000)":   float(Y_lit[1]),
    "Y(1000000)":  float(Y_lit[2]),
    "factor_duplicacion_2^1.15": float(2 ** BETA_SOCIOECON),
}

print("=== Verificacion ciudades literales ===")
for k, v in verificacion_lit.items():
    print(f"  {k:35s} = {v:,.3f}")

# ---------------------------------------------------------------------------
# 2. Nube de 50 ciudades (log-espaciadas, sin ruido)
# ---------------------------------------------------------------------------
N_nube = np.logspace(np.log10(N_MIN), np.log10(N_MAX), N_NUBE)
Y_nube = escalamiento(N_nube, BETA_SOCIOECON)

# Para referencia visual: escalamiento lineal (beta=1) y sublineal (beta=0.85)
Y_lineal   = escalamiento(N_nube, BETA_LINEAL)
Y_infraestr = escalamiento(N_nube, BETA_INFRAESTR)

# ---------------------------------------------------------------------------
# 3. Regresion log-log (minimos cuadrados)
# ---------------------------------------------------------------------------
log_N = np.log10(N_nube)
log_Y = np.log10(Y_nube)

slope, intercept, r_value, p_value, std_err = stats.linregress(log_N, log_Y)
beta_recuperado = slope
Y0_recuperado   = 10 ** intercept

print(f"\n=== Regresion log-log socioeconomica (50 ciudades, sin ruido) ===")
print(f"  beta recuperado : {beta_recuperado:.6f}  (esperado {BETA_SOCIOECON})")
print(f"  Y_0 recuperado  : {Y0_recuperado:.6f}  (esperado {Y_0})")
print(f"  R^2             : {r_value**2:.10f}")

# Regresion log-log analoga sobre la nube de infraestructura (beta=0.85 sublineal)
log_Y_infra = np.log10(Y_infraestr)
(slope_infra, intercept_infra, r_value_infra,
 p_value_infra, std_err_infra) = stats.linregress(log_N, log_Y_infra)
beta_recuperado_infra = slope_infra
Y0_recuperado_infra   = 10 ** intercept_infra

print(f"\n=== Regresion log-log infraestructura (50 ciudades, sin ruido) ===")
print(f"  beta recuperado : {beta_recuperado_infra:.6f}  (esperado {BETA_INFRAESTR})")
print(f"  Y_0 recuperado  : {Y0_recuperado_infra:.6f}  (esperado {Y_0})")
print(f"  R^2             : {r_value_infra**2:.10f}")

# ---------------------------------------------------------------------------
# 4. Productividad per capita
# ---------------------------------------------------------------------------
Y_percapita_nube = Y_nube / N_nube   # = N^(beta-1) = N^0.15

# ---------------------------------------------------------------------------
# 5. Exportar datos crudos a JSON
# ---------------------------------------------------------------------------
datos_json = {
    "teoria": "bettencourt_west_escalamiento",
    "parametros": {
        "beta_socioecon": BETA_SOCIOECON,
        "beta_infraestr": BETA_INFRAESTR,
        "beta_lineal":    BETA_LINEAL,
        "Y_0":            Y_0,
        "N_nube":         N_NUBE,
        "N_min":          N_MIN,
        "N_max":          N_MAX,
    },
    "ciudades_literales": [
        {
            "N": int(N_lit[i]),
            "Y": round(float(Y_lit[i]), 3),
            "Y_per_capita": round(float(Y_lit[i] / N_lit[i]), 6),
        }
        for i in range(len(N_lit))
    ],
    "verificacion": {
        "Y_100000":           round(float(Y_lit[0]), 0),
        "Y_200000":           round(float(Y_lit[1]), 0),
        "Y_1000000":          round(float(Y_lit[2]), 0),
        "factor_duplicacion": round(float(2 ** BETA_SOCIOECON), 4),
        "factor_esperado":    round(2 ** 1.15, 4),
    },
    "regresion": {
        "beta_recuperado": round(float(beta_recuperado), 6),
        "Y0_recuperado":   round(float(Y0_recuperado), 8),
        "R_cuadrado":      round(float(r_value ** 2), 10),
        "std_err":         round(float(std_err), 10),
    },
    "regresion_infraestructura": {
        "beta_recuperado_infra": round(float(beta_recuperado_infra), 6),
        "Y0_recuperado_infra":   round(float(Y0_recuperado_infra), 8),
        "R_cuadrado_infra":      round(float(r_value_infra ** 2), 10),
        "std_err_infra":         round(float(std_err_infra), 10),
    },
    "nube_ciudades": [
        {
            "N":          round(float(N_nube[i]), 2),
            "Y":          round(float(Y_nube[i]), 4),
            "Y_per_capita": round(float(Y_percapita_nube[i]), 8),
        }
        for i in range(N_NUBE)
    ],
    "criterio_validacion": {
        "beta_en_rango_1.10_1.20": bool(1.10 <= beta_recuperado <= 1.20),
        "beta_infra_en_rango_0.80_0.90": bool(0.80 <= beta_recuperado_infra <= 0.90),
        "factor_duplicacion_error_pct": round(
            abs((2 ** beta_recuperado - 2 ** BETA_SOCIOECON) / (2 ** BETA_SOCIOECON)) * 100, 6
        ),
    },
}

RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_JSON = os.path.join(RUTA_BASE, "datos_bettencourt_west_escalamiento.json")

with open(RUTA_JSON, "w", encoding="utf-8") as f:
    json.dump(datos_json, f, ensure_ascii=False, indent=2)

print(f"\nDatos crudos guardados en: {RUTA_JSON}")

# ---------------------------------------------------------------------------
# 6. Graficas
# ---------------------------------------------------------------------------
RUTA_ASSETS = os.path.normpath(
    os.path.join(RUTA_BASE, "../presentacion/assets/sim")
)
os.makedirs(RUTA_ASSETS, exist_ok=True)

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.facecolor":   BG_COLOR,
    "figure.facecolor": BG_COLOR,
    "text.color":       TEXT_COLOR,
    "axes.labelcolor":  TEXT_COLOR,
    "xtick.color":      TEXT_COLOR,
    "ytick.color":      TEXT_COLOR,
    "axes.edgecolor":   "#2e4060",
    "grid.color":       "#1e2e42",
    "grid.alpha":       0.7,
    "axes.spines.top":  False,
    "axes.spines.right": False,
})

# --- Grafica 1: log-log Y vs N con nube de ciudades ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor(BG_COLOR)

ax1 = axes[0]
ax1.set_facecolor(BG_COLOR)

# Lineas de referencia
ax1.plot(N_nube, Y_lineal,   color="#4a7fc1", lw=1.8, ls="--",
         label=r"Escala lineal $\beta=1.00$")
ax1.plot(N_nube, Y_infraestr, color=GREEN_SOFT, lw=1.8, ls="-.",
         label=r"Infraestructura $\beta=0.85$")

# Linea ajustada de la regresion
N_fit = np.logspace(np.log10(N_MIN), np.log10(N_MAX), 200)
Y_fit = 10 ** intercept * N_fit ** slope
ax1.plot(N_fit, Y_fit, color=AMBER, lw=2.5, ls="-",
         label=fr"Ajuste regresion $\hat\beta={beta_recuperado:.3f}$",
         zorder=4)

# Nube de ciudades
ax1.scatter(N_nube, Y_nube, color=CYAN_SOFT, s=45, zorder=5, alpha=0.85,
            edgecolors="none", label="Ciudades simuladas")

# Ciudades literales destacadas
ax1.scatter(N_lit, Y_lit, color=AMBER, s=120, zorder=6,
            marker="*", edgecolors=TEXT_COLOR, linewidth=0.6,
            label="Ciudades del enunciado")

# Anotaciones ciudades literales
etiquetas_lit = ["100 k", "200 k", "1 M"]
for n, y, lab in zip(N_lit, Y_lit, etiquetas_lit):
    ax1.annotate(
        f"N={lab}\nY={y:,.0f}",
        xy=(n, y), xytext=(n * 1.25, y * 0.6),
        color=TEXT_COLOR, fontsize=8.5,
        arrowprops=dict(arrowstyle="->", color=AMBER, lw=0.8),
    )

ax1.set_xscale("log")
ax1.set_yscale("log")
ax1.set_xlabel("Poblacion N (habitantes)", fontsize=12)
ax1.set_ylabel("Magnitud socioeconómica Y", fontsize=12)
ax1.set_title(
    "Escalamiento urbano superlineal\nBettencourt & West (2007)  —  escala log-log",
    fontsize=13, color=TEXT_COLOR, pad=10,
)
ax1.legend(fontsize=9, facecolor="#0a1520", edgecolor="#2e4060",
           labelcolor=TEXT_COLOR)
ax1.grid(True, which="both", alpha=0.35)
ax1.set_xlim(N_MIN * 0.8, N_MAX * 1.5)

# Texto prima urbana
ax1.text(
    0.03, 0.97,
    r"$Y = Y_0 \cdot N^{\beta}$,  $\beta = 1.15$" + "\nlas ciudades grandes son\ndesproporcionadamente productivas",
    transform=ax1.transAxes, fontsize=9,
    color=AMBER, verticalalignment="top",
    bbox=dict(facecolor="#0a1520", edgecolor=AMBER, alpha=0.7, boxstyle="round,pad=0.4"),
)

# --- Panel 2: productividad per capita Y/N vs N ---
ax2 = axes[1]
ax2.set_facecolor(BG_COLOR)

ax2.plot(N_nube, Y_percapita_nube, color=AMBER, lw=2.5, label=r"$Y/N = N^{0.15}$")
ax2.scatter(N_nube, Y_percapita_nube, color=CYAN_SOFT, s=40, zorder=4,
            alpha=0.85, edgecolors="none")

# Ciudades literales per capita
Ypc_lit = Y_lit / N_lit
ax2.scatter(N_lit, Ypc_lit, color=AMBER, s=120, zorder=6,
            marker="*", edgecolors=TEXT_COLOR, linewidth=0.6,
            label="Ciudades del enunciado")
for n, ypc, lab in zip(N_lit, Ypc_lit, etiquetas_lit):
    ax2.annotate(
        f"N={lab}",
        xy=(n, ypc), xytext=(n * 1.2, ypc * 1.1),
        color=TEXT_COLOR, fontsize=8.5,
        arrowprops=dict(arrowstyle="->", color=AMBER, lw=0.8),
    )

ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlabel("Poblacion N (habitantes)", fontsize=12)
ax2.set_ylabel("Productividad per cápita  Y/N", fontsize=12)
ax2.set_title(
    "Prima urbana: productividad per cápita\ncreciente con el tamaño de la ciudad",
    fontsize=13, color=TEXT_COLOR, pad=10,
)
ax2.legend(fontsize=9, facecolor="#0a1520", edgecolor="#2e4060",
           labelcolor=TEXT_COLOR)
ax2.grid(True, which="both", alpha=0.35)
ax2.set_xlim(N_MIN * 0.8, N_MAX * 1.5)

ax2.text(
    0.03, 0.97,
    r"$Y/N = N^{\beta-1} = N^{0.15}$" + "\nla ventaja per cápita\ncrece con la ciudad",
    transform=ax2.transAxes, fontsize=9,
    color=AMBER, verticalalignment="top",
    bbox=dict(facecolor="#0a1520", edgecolor=AMBER, alpha=0.7, boxstyle="round,pad=0.4"),
)

plt.tight_layout(pad=2.0)
PNG1 = os.path.join(RUTA_ASSETS, "sim_bettencourt_west_escalamiento_1.png")
plt.savefig(PNG1, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
plt.close(fig)
print(f"PNG 1 guardado: {PNG1}")

# --- Grafica 2: comparacion tres regimenes de escalamiento ---
fig2, ax3 = plt.subplots(figsize=(10, 6))
fig2.patch.set_facecolor(BG_COLOR)
ax3.set_facecolor(BG_COLOR)

Y_socioecon_nube = escalamiento(N_nube, BETA_SOCIOECON)
Y_infraestr_nube = escalamiento(N_nube, BETA_INFRAESTR)
Y_lineal_nube    = escalamiento(N_nube, BETA_LINEAL)

ax3.plot(N_nube, Y_socioecon_nube, color=AMBER,      lw=2.5,
         label=fr"Socioeconómico  $\beta={BETA_SOCIOECON}$ (superlineal)")
ax3.plot(N_nube, Y_lineal_nube,    color="#4a7fc1",  lw=2.0, ls="--",
         label=fr"Lineal          $\beta={BETA_LINEAL:.2f}$ (referencia)")
ax3.plot(N_nube, Y_infraestr_nube, color=GREEN_SOFT, lw=2.0, ls="-.",
         label=fr"Infraestructura $\beta={BETA_INFRAESTR}$ (sublineal)")

# Banda "prima urbana": area entre socioecon y lineal
ax3.fill_between(N_nube, Y_lineal_nube, Y_socioecon_nube,
                 alpha=0.15, color=AMBER, label="Prima urbana")

ax3.set_xscale("log")
ax3.set_yscale("log")
ax3.set_xlabel("Poblacion N (habitantes)", fontsize=13)
ax3.set_ylabel("Magnitud Y (unidades normalizadas  $Y_0=1$)", fontsize=13)
ax3.set_title(
    "Tres regímenes de escalamiento urbano\nBettencourt & West (2007)",
    fontsize=14, color=TEXT_COLOR, pad=12,
)
ax3.legend(fontsize=10, facecolor="#0a1520", edgecolor="#2e4060",
           labelcolor=TEXT_COLOR, loc="upper left")
ax3.grid(True, which="both", alpha=0.35)
ax3.set_xlim(N_MIN * 0.8, N_MAX * 1.5)

# Flechas anotando factor de duplicacion
x_dup   = 500_000
y_dup   = escalamiento(x_dup, BETA_SOCIOECON)
y_dup2  = escalamiento(x_dup * 2, BETA_SOCIOECON)
ax3.annotate(
    "",
    xy=(x_dup * 2, y_dup2), xytext=(x_dup, y_dup),
    arrowprops=dict(arrowstyle="<->", color=AMBER, lw=1.5),
)
ax3.text(
    x_dup * 1.05, (y_dup * y_dup2) ** 0.5,
    f"×{2**BETA_SOCIOECON:.3f}\nal duplicar N",
    color=AMBER, fontsize=9,
    bbox=dict(facecolor="#0a1520", edgecolor=AMBER, alpha=0.7,
              boxstyle="round,pad=0.3"),
)

plt.tight_layout(pad=2.0)
PNG2 = os.path.join(RUTA_ASSETS, "sim_bettencourt_west_escalamiento_2.png")
fig2.savefig(PNG2, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
plt.close(fig2)
print(f"PNG 2 guardado: {PNG2}")

# ---------------------------------------------------------------------------
# 7. Preguntas y respuestas
# ---------------------------------------------------------------------------
preguntas_json = {
    "teoria":  "bettencourt_west_escalamiento",
    "nombre":  "Escalamiento urbano superlineal de Bettencourt-West",
    "autor":   "Bettencourt, Lobo, Helbing, Kuhnert y West",
    "anio":    "2007",
    "preguntas": [
        {
            "q": (
                "Con escalamiento Y=Y_0*N^beta, Y_0=1 y beta=1.15, "
                "calcula la magnitud Y para una ciudad de N=1,000,000 habitantes. "
                "Da el resultado redondeado al entero. "
                "Formato: 'Respuesta final: <valor>'."
            ),
            "valor_exacto": str(round(float(escalamiento(1_000_000)))),
            "tipo":         "forma_cerrada",
            "tolerancia":   "±1% (7943282)",
            "como_computar": (
                "Y = 1,000,000^1.15 = 10^(6*1.15) = 10^6.9 = "
                f"{escalamiento(1_000_000):.3f} -> redondeado: "
                f"{round(float(escalamiento(1_000_000)))}"
            ),
        },
        {
            "q": (
                "Bajo escalamiento superlineal con beta=1.15, "
                "por que factor se multiplica la magnitud socioeconomica Y "
                "cuando la poblacion de una ciudad se DUPLICA? "
                "Formato: 'Respuesta final: <valor>'."
            ),
            "valor_exacto": f"{2 ** BETA_SOCIOECON:.4f}",
            "tipo":         "forma_cerrada",
            "tolerancia":   "±0.01 (2.219)",
            "como_computar": (
                f"Factor = 2^1.15 = {2**BETA_SOCIOECON:.6f}"
            ),
        },
        {
            "q": (
                "Genera 50 ciudades con poblaciones N espaciadas logaritmicamente "
                "entre 10,000 y 5,000,000 y magnitud Y=N^1.15 (sin ruido), "
                "ajusta por minimos cuadrados log10(Y)=a+b*log10(N) y reporta "
                "el exponente b recuperado. "
                "Formato: 'Respuesta final: <valor>'."
            ),
            "valor_exacto": f"{beta_recuperado:.4f}",
            "tipo":         "emergente",
            "tolerancia":   "±0.02 en torno a 1.150",
            "como_computar": (
                "Datos sin ruido generados con beta=1.15 exacto -> "
                f"el ajuste por minimos cuadrados recupera b={beta_recuperado:.6f}; "
                f"R^2={r_value**2:.10f}"
            ),
        },
    ],
}

RUTA_PREGUNTAS = os.path.join(RUTA_BASE, "preguntas_bettencourt_west_escalamiento.json")
with open(RUTA_PREGUNTAS, "w", encoding="utf-8") as f:
    json.dump(preguntas_json, f, ensure_ascii=False, indent=2)

print(f"\nPreguntas guardadas en: {RUTA_PREGUNTAS}")

# ---------------------------------------------------------------------------
# 8. Resumen criterio de validacion
# ---------------------------------------------------------------------------
print("\n=== Criterio de validacion ===")
print(f"  beta socioecon recuperado      : {beta_recuperado:.6f}")
print(f"  Rango esperado [1.10,1.20]     : {1.10 <= beta_recuperado <= 1.20}")
print(f"  beta infraestr recuperado      : {beta_recuperado_infra:.6f}")
print(f"  Rango esperado [0.80,0.90]     : {0.80 <= beta_recuperado_infra <= 0.90}")
print(f"  Factor duplicacion 2^beta      : {2**beta_recuperado:.4f}")
print(f"  Error % respecto 2^1.15        : {abs((2**beta_recuperado - 2**BETA_SOCIOECON)/(2**BETA_SOCIOECON))*100:.6f}%")
print("\nSimulacion completada.")
