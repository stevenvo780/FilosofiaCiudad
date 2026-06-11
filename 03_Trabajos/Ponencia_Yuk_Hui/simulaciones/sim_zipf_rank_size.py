"""
Simulacion: Ley rango-tamano de Zipf para ciudades
Autor original: George Kingsley Zipf (1949)
Implementacion: determinista (formula cerrada + perturbacion con semilla fija).

Formulacion:
    P(r) = P_1 / r^q
    donde P_1 = 1,000,000, r = 1..100.
    q = 1 es la version ESTRICTA/idealizada (regla rango-tamano clasica).
    Los sistemas urbanos reales muestran exponentes cercanos pero no exactamente
    1 (q tipicamente 0.8-1.2 segun pais y recorte; Gabaix 1999): q=1 es una
    regularidad empirica, no un invariante fisico exacto.

Se generan DOS sistemas para ilustrar el contraste:
  1) Sistema IDEAL  : q=1 exacto (P(r)=1,000,000/r). Sus puntos caen sobre la
     recta de referencia de pendiente -1, y la regresion recupera -1.000000.
  2) Sistema EMPIRICO: q=0.85 con perturbacion log-normal determinista (semilla
     fija). Su regresion se aparta visiblemente de la referencia estricta,
     mostrando que la ley es una idealizacion y que los sistemas reales se
     desvian de la pendiente -1.

Dos corridas siempre producen el mismo resultado (la perturbacion usa semilla fija).
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
import os

# ─────────────────────────────────────────────────────────────────────────────
# 1. PARAMETROS DEL EXPERIMENTO
# ─────────────────────────────────────────────────────────────────────────────
P1 = 1_000_000   # poblacion de la ciudad de mayor rango
Q  = 1.0         # exponente de Zipf (version estricta / idealizada)
N  = 100         # numero de ciudades

# Sistema empirico (ilustra desviaciones reales: Gabaix 1999, q tipico 0.8-1.2)
Q_EMP   = 0.85   # exponente empirico tipico (menor que la ley estricta)
SIGMA   = 0.12   # dispersion log-normal de la perturbacion
SEMILLA = 42     # semilla fija => resultado reproducible (determinista)

RANGOS = np.arange(1, N + 1, dtype=float)   # r = 1, 2, ..., 100

# ─────────────────────────────────────────────────────────────────────────────
# 2. GENERACION DE POBLACIONES
#    Ideal:    P(r) = P1 / r^Q              (Q = 1 exacto)
#    Empirico: P(r) = P1 / r^Q_EMP * ruido  (ruido log-normal determinista)
# ─────────────────────────────────────────────────────────────────────────────
POBLACIONES = P1 / (RANGOS ** Q)            # sistema ideal (canonico)

_rng = np.random.default_rng(SEMILLA)
RUIDO = _rng.lognormal(mean=0.0, sigma=SIGMA, size=N)
POBLACIONES_EMP = P1 / (RANGOS ** Q_EMP) * RUIDO

# Verificacion de valores clave del sistema ideal
assert POBLACIONES[0] == 1_000_000,  "P(1) debe ser 1,000,000"
assert POBLACIONES[1] == 500_000,    "P(2) debe ser 500,000"
assert POBLACIONES[3] == 250_000,    "P(4) debe ser 250,000"
assert POBLACIONES[9] == 100_000,    "P(10) debe ser 100,000"

# ─────────────────────────────────────────────────────────────────────────────
# 3. AJUSTE POR MINIMOS CUADRADOS  log10(P) = a + b * log10(r)
# ─────────────────────────────────────────────────────────────────────────────
log_r = np.log10(RANGOS)
log_p = np.log10(POBLACIONES)
log_p_emp = np.log10(POBLACIONES_EMP)

pendiente, intercepto, r_valor, p_valor, error_est = stats.linregress(log_r, log_p)
r_cuadrado = r_valor ** 2

pend_emp, inter_emp, rval_emp, pval_emp, err_emp = stats.linregress(log_r, log_p_emp)
r2_emp = rval_emp ** 2

print("=" * 55)
print("  Ley de Zipf  —  Sistema sintetico (100 ciudades)")
print("=" * 55)
print(f"  P_1 (ciudad mayor)     : {P1:>12,.0f}")
print(f"  q (exponente estricto) : {Q:>12.3f}")
print(f"  Pendiente recuperada   : {pendiente:>12.6f}")
print(f"  Intercepto             : {intercepto:>12.6f}")
print(f"  R^2                    : {r_cuadrado:>12.6f}")
print(f"  P(1)  = {POBLACIONES[0]:>10,.0f}  (esperado 1,000,000)")
print(f"  P(2)  = {POBLACIONES[1]:>10,.0f}  (esperado   500,000)")
print(f"  P(4)  = {POBLACIONES[3]:>10,.0f}  (esperado   250,000)")
print(f"  P(10) = {POBLACIONES[9]:>10,.0f}  (esperado   100,000)")
print("-" * 55)
print(f"  Sistema empirico (q={Q_EMP}, perturbado, semilla {SEMILLA}):")
print(f"  Pendiente recuperada   : {pend_emp:>12.6f}  (se aparta de -1)")
print(f"  R^2                    : {r2_emp:>12.6f}")
print("=" * 55)

# ─────────────────────────────────────────────────────────────────────────────
# 4. GUARDAR DATOS CRUDOS
# ─────────────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_DATOS = os.path.join(BASE, "datos_zipf_rank_size.json")

datos = {
    "teoria": "zipf_rank_size",
    "autor": "George Kingsley Zipf",
    "anio": "1949",
    "nota_canon": (
        "q=1 es la version estricta/idealizada de la regla rango-tamano (Zipf "
        "1949). Es una regularidad empirica, no un invariante fisico exacto: los "
        "sistemas urbanos reales muestran exponentes cercanos pero no exactamente "
        "1 (q tipicamente 0.8-1.2 segun pais/recorte; Gabaix 1999)."
    ),
    "parametros": {
        "P1": P1,
        "q": Q,
        "n_ciudades": N,
        "q_empirico": Q_EMP,
        "sigma_perturbacion": SIGMA,
        "semilla": SEMILLA
    },
    "ajuste_log_log": {
        "pendiente": float(pendiente),
        "intercepto": float(intercepto),
        "r_cuadrado": float(r_cuadrado),
        "p_valor": float(p_valor)
    },
    "ajuste_log_log_empirico": {
        "pendiente": float(pend_emp),
        "intercepto": float(inter_emp),
        "r_cuadrado": float(r2_emp),
        "p_valor": float(pval_emp)
    },
    "verificacion": {
        "P_rango_1":  float(POBLACIONES[0]),
        "P_rango_2":  float(POBLACIONES[1]),
        "P_rango_4":  float(POBLACIONES[3]),
        "P_rango_10": float(POBLACIONES[9])
    },
    "ciudades": [
        {"rango": int(r), "poblacion": float(p)}
        for r, p in zip(RANGOS.astype(int), POBLACIONES)
    ],
    "ciudades_empiricas": [
        {"rango": int(r), "poblacion": float(p)}
        for r, p in zip(RANGOS.astype(int), POBLACIONES_EMP)
    ]
}

with open(RUTA_DATOS, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)

print(f"\n  Datos guardados en: {RUTA_DATOS}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. GRAFICO PNG  (estetica: fondo oscuro, acento ambar, español)
# ─────────────────────────────────────────────────────────────────────────────
COLOR_FONDO   = "#0e1a2b"
COLOR_TEXTO   = "#e8e6e1"
COLOR_ACENTO  = "#e0a458"   # ambar: sistema ideal (q=1 exacto)
COLOR_LINEA   = "#5b8db8"   # azul acero: regresion del sistema empirico
COLOR_REF     = "#7ecba1"   # verde menta: referencia Zipf estricta (-1)
COLOR_EMP     = "#d98c8c"   # rosa: puntos del sistema empirico (q!=1)

ASSETS = os.path.join(
    BASE, "..", "presentacion", "assets", "sim"
)
os.makedirs(ASSETS, exist_ok=True)

r_continuo = np.logspace(0, 2, 500)
# Referencia Zipf estricta (q=1): pendiente -1 exacta
p_ref = P1 / r_continuo
# Regresion del sistema empirico (pendiente != -1, visiblemente distinta)
p_reg_emp = 10 ** (inter_emp + pend_emp * np.log10(r_continuo))

# ── GRAFICO 1: log-log con ideal sobre la referencia y empirico que se aparta ──
fig, ax = plt.subplots(figsize=(10, 7))
fig.patch.set_facecolor(COLOR_FONDO)
ax.set_facecolor(COLOR_FONDO)

# Referencia Zipf estricta: linea verde ANCHA, por DEBAJO de todo (zorder bajo).
# Asi queda visible aunque los puntos ideales caigan exactamente sobre ella.
ax.plot(
    r_continuo, p_ref,
    color=COLOR_REF, linewidth=4.0, linestyle="--", zorder=2, alpha=0.95,
    label="Zipf estricta idealizada (pendiente = −1)"
)

# Puntos del sistema ideal (q=1 exacto): caen sobre la referencia
ax.scatter(
    RANGOS, POBLACIONES,
    color=COLOR_ACENTO, s=42, zorder=6, alpha=0.9,
    edgecolors=COLOR_FONDO, linewidths=0.4,
    label="Sistema ideal: 100 ciudades (q = 1 exacto)"
)

# Puntos del sistema empirico (q=0.85 + ruido): se dispersan/aplanan
ax.scatter(
    RANGOS, POBLACIONES_EMP,
    color=COLOR_EMP, s=30, zorder=5, alpha=0.7, marker="^",
    label=f"Sistema empirico: q≈{-pend_emp:.2f} (perturbado)"
)

# Regresion del sistema empirico: pendiente visiblemente distinta de -1
ax.plot(
    r_continuo, p_reg_emp,
    color=COLOR_LINEA, linewidth=2.2, zorder=4,
    label=f"Regresion empirica: pendiente = {pend_emp:.3f}"
)

# Escala logaritmica en ambos ejes
ax.set_xscale("log")
ax.set_yscale("log")

# Etiquetas y titulo
ax.set_xlabel("Rango de la ciudad (log)", color=COLOR_TEXTO, fontsize=13)
ax.set_ylabel("Población (log)", color=COLOR_TEXTO, fontsize=13)
ax.set_title(
    "Ley Rango-Tamaño de Zipf para Ciudades\n"
    "George Kingsley Zipf (1949)  •  Ideal (q=1) vs. empírico (q≈0.86)",
    color=COLOR_TEXTO, fontsize=13, pad=14
)

# Anotacion del contraste de pendientes
ax.annotate(
    f"Ideal (q=1):  pendiente = {pendiente:.4f},  $R^2$ = {r_cuadrado:.4f}\n"
    f"Empírico:     pendiente = {pend_emp:.4f},  $R^2$ = {r2_emp:.4f}",
    xy=(0.40, 0.085), xycoords="axes fraction",
    color=COLOR_TEXTO, fontsize=10.5,
    bbox=dict(boxstyle="round,pad=0.4", facecolor=COLOR_FONDO,
              edgecolor=COLOR_ACENTO, alpha=0.85)
)

# Leyenda y ejes
leyenda = ax.legend(
    fontsize=9.5, facecolor=COLOR_FONDO,
    labelcolor=COLOR_TEXTO, edgecolor=COLOR_ACENTO,
    loc="upper right"
)

ax.tick_params(colors=COLOR_TEXTO, which="both")
for spine in ax.spines.values():
    spine.set_edgecolor(COLOR_TEXTO)
    spine.set_alpha(0.4)

ax.xaxis.label.set_color(COLOR_TEXTO)
ax.yaxis.label.set_color(COLOR_TEXTO)

plt.tight_layout()
ruta_g1 = os.path.join(ASSETS, "sim_zipf_rank_size_1.png")
fig.savefig(ruta_g1, dpi=150, facecolor=COLOR_FONDO, bbox_inches="tight")
plt.close(fig)
print(f"  Gráfico 1 guardado en: {ruta_g1}")

# ── GRAFICO 2: mismos datos en escala lineal (para contraste) ─────────────────
fig2, axes = plt.subplots(1, 2, figsize=(13, 6))
fig2.patch.set_facecolor(COLOR_FONDO)
fig2.suptitle(
    "Distribución de Ciudades: Escala Lineal vs. Log-Log\n"
    "Ley de Zipf — George Kingsley Zipf (1949) — ideal vs. empírico",
    color=COLOR_TEXTO, fontsize=13, y=1.01
)

# Panel izquierdo: escala lineal
ax_lin = axes[0]
ax_lin.set_facecolor(COLOR_FONDO)
ax_lin.scatter(RANGOS, POBLACIONES / 1e6,
               color=COLOR_ACENTO, s=30, alpha=0.85, zorder=5,
               label="Ideal (q=1)")
ax_lin.scatter(RANGOS, POBLACIONES_EMP / 1e6,
               color=COLOR_EMP, s=22, alpha=0.65, zorder=4, marker="^",
               label="Empírico")
ax_lin.set_xlabel("Rango", color=COLOR_TEXTO, fontsize=12)
ax_lin.set_ylabel("Población (millones)", color=COLOR_TEXTO, fontsize=12)
ax_lin.set_title("Escala lineal", color=COLOR_TEXTO, fontsize=12)
ax_lin.tick_params(colors=COLOR_TEXTO)
for sp in ax_lin.spines.values():
    sp.set_edgecolor(COLOR_TEXTO)
    sp.set_alpha(0.4)
ax_lin.legend(fontsize=9, facecolor=COLOR_FONDO,
              labelcolor=COLOR_TEXTO, edgecolor=COLOR_ACENTO)

# Panel derecho: log-log
ax_log = axes[1]
ax_log.set_facecolor(COLOR_FONDO)
# Referencia estricta ancha por debajo
ax_log.plot(r_continuo, p_ref,
            color=COLOR_REF, linewidth=4.0, linestyle="--", zorder=2, alpha=0.95,
            label="Zipf estricta (−1)")
ax_log.scatter(RANGOS, POBLACIONES,
               color=COLOR_ACENTO, s=30, alpha=0.9, zorder=6,
               edgecolors=COLOR_FONDO, linewidths=0.4,
               label="Ideal (q=1)")
ax_log.scatter(RANGOS, POBLACIONES_EMP,
               color=COLOR_EMP, s=24, alpha=0.7, zorder=5, marker="^",
               label="Empírico (q≈0.86)")
ax_log.plot(r_continuo, p_reg_emp,
            color=COLOR_LINEA, linewidth=2, zorder=4,
            label=f"Regresion empirica (b={pend_emp:.3f})")
ax_log.set_xscale("log")
ax_log.set_yscale("log")
ax_log.set_xlabel("Rango (log)", color=COLOR_TEXTO, fontsize=12)
ax_log.set_ylabel("Población (log)", color=COLOR_TEXTO, fontsize=12)
ax_log.set_title("Escala log-log", color=COLOR_TEXTO, fontsize=12)
ax_log.tick_params(colors=COLOR_TEXTO, which="both")
for sp in ax_log.spines.values():
    sp.set_edgecolor(COLOR_TEXTO)
    sp.set_alpha(0.4)
leyenda2 = ax_log.legend(
    fontsize=9, facecolor=COLOR_FONDO,
    labelcolor=COLOR_TEXTO, edgecolor=COLOR_ACENTO
)

plt.tight_layout()
ruta_g2 = os.path.join(ASSETS, "sim_zipf_rank_size_2.png")
fig2.savefig(ruta_g2, dpi=150, facecolor=COLOR_FONDO, bbox_inches="tight")
plt.close(fig2)
print(f"  Gráfico 2 guardado en: {ruta_g2}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. CRITERIO DE VALIDACION
# ─────────────────────────────────────────────────────────────────────────────
print("\n  ── VALIDACION ──")
ok_pendiente = abs(pendiente - (-1.0)) <= 0.001
ok_r2        = r_cuadrado > 0.95
print(f"  Pendiente = {pendiente:.6f}  (objetivo -1.000 ± 0.001): {'OK' if ok_pendiente else 'FALLO'}")
print(f"  R^2       = {r_cuadrado:.6f}  (objetivo > 0.95):         {'OK' if ok_r2 else 'FALLO'}")
print(f"  Validacion global: {'PASADA' if (ok_pendiente and ok_r2) else 'FALLIDA'}")
