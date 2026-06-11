"""
Simulacion: Agregacion Limitada por Difusion (DLA) y Dimension Fractal Urbana
Autores: Michael Batty y Paul Longley (1994)
Campo: Morfologia y crecimiento urbano

Descripcion:
    DLA: una semilla en el centro; particulas lanzadas desde lejos hacen
    caminata aleatoria hasta tocar el agregado, donde se pegan, formando
    un cluster ramificado de dimension fractal D ~ 1.7 en 2D.

    Dimension fractal por mass-radius:
        N(R) ~ R^D  =>  D = log(N2/N1) / log(R2/R1)

    Implementacion:
        - Rejilla 201x201, semilla central, 1500 particulas
        - numpy.random.seed(3) para reproducibilidad exacta
        - Regresion log-log sobre region de escalamiento (excluyendo saturacion)
        - Dos corridas identicas producen resultado identico (determinista)

Notas sobre el rango de regresion:
    El cluster DLA con 1500 particulas se extiende hasta radio ~65-70 unidades.
    La ley de potencias N(R) ~ R^D es valida mientras el cluster no este saturado
    (N(R) << N_total). Se excluyen puntos con N(R) > 60% del total para ajustar
    solo sobre la region de escalamiento genuina y evitar el aplanamiento en la
    region de frontera dispersa (que sesga D hacia abajo). El rango efectivo es
    aproximadamente R = 5..35, donde R^2 > 0.99 y D ~ 1.69, alineado con el
    valor canonico ~1.71 de un DLA 2D.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os
from pathlib import Path

# ============================================================
# CONFIGURACION
# ============================================================
GRID_SIZE   = 201          # Rejilla 201x201
N_PARTICLES = 1500         # Numero de particulas (teoria: 1500)
SEED        = 3            # numpy.random.seed(3)
CENTER      = GRID_SIZE // 2  # 100

# Radio de lanzamiento: launch_r = cluster_radius + LAUNCH_MARGIN
LAUNCH_MARGIN = 5
# Radio de muerte: kill_r = launch_r + KILL_MARGIN (> launch_r para DLA real)
KILL_MARGIN = 40

# Directorios de salida
BASE = Path("/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad"
            "/03_Trabajos/Ponencia_Yuk_Hui")
SIM_DIR    = BASE / "simulaciones"
ASSETS_DIR = BASE / "presentacion/assets/sim"
SIM_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# COLORES  (fondo #0e1a2b, texto #e8e6e1, acento #e0a458)
# ============================================================
BG_COLOR   = "#0e1a2b"
TEXT_COLOR = "#e8e6e1"
ACCENT     = "#e0a458"
GRID_COLOR = "#1e2e42"
LINE_COLOR = "#5b8fc9"
DOT_COLOR  = "#7ec8e3"


# ============================================================
# SIMULACION DLA
# ============================================================

def simulate_dla():
    """
    Simulacion DLA con numpy.random.seed(SEED).
    Determinista: dos corridas con el mismo seed dan resultado identico.

    Retorna:
        grid : ndarray int32 (GRID_SIZE x GRID_SIZE)
               0 = vacio, k = orden de pegado de la k-esima particula
        cluster_radius : radio maximo alcanzado por el cluster
    """
    np.random.seed(SEED)

    grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int32)
    grid[CENTER, CENTER] = 1
    cluster_radius = 1

    for particle_idx in range(2, N_PARTICLES + 2):
        launch_r = cluster_radius + LAUNCH_MARGIN
        kill_r   = launch_r + KILL_MARGIN

        # Lanzar particula desde circulo de radio launch_r
        angle = np.random.uniform(0.0, 2.0 * np.pi)
        x = int(CENTER + launch_r * np.cos(angle))
        y = int(CENTER + launch_r * np.sin(angle))
        x = np.clip(x, 1, GRID_SIZE - 2)
        y = np.clip(y, 1, GRID_SIZE - 2)

        while True:
            # Caminata aleatoria (4-conectividad)
            d = np.random.randint(0, 4)
            if   d == 0: x -= 1
            elif d == 1: x += 1
            elif d == 2: y -= 1
            else:        y += 1

            x = np.clip(x, 1, GRID_SIZE - 2)
            y = np.clip(y, 1, GRID_SIZE - 2)

            dist2 = (x - CENTER) ** 2 + (y - CENTER) ** 2

            # Matar y relanzar si supera el radio de muerte
            if dist2 > kill_r * kill_r:
                angle = np.random.uniform(0.0, 2.0 * np.pi)
                x = int(CENTER + launch_r * np.cos(angle))
                y = int(CENTER + launch_r * np.sin(angle))
                x = np.clip(x, 1, GRID_SIZE - 2)
                y = np.clip(y, 1, GRID_SIZE - 2)
                continue

            # Pegar si toca el cluster (4-vecindad)
            if (grid[x, y] == 0 and
                    (grid[x-1, y] > 0 or grid[x+1, y] > 0 or
                     grid[x, y-1] > 0 or grid[x, y+1] > 0)):
                grid[x, y] = particle_idx
                r = int(np.sqrt(dist2))
                if r > cluster_radius:
                    cluster_radius = r
                break

    return grid, cluster_radius


# ============================================================
# DIMENSION FRACTAL POR MASS-RADIUS
# ============================================================

def measure_fractal_dimension(grid, r_min=5, r_max=None, n_points=30,
                               sat_threshold=0.60):
    """
    Mide la dimension fractal D por la ley mass-radius:
        N(R) ~ R^D  =>  log N = D log R + b

    Parametros:
        r_min         : radio minimo para la regresion
        r_max         : radio maximo (por defecto: 75% del radio del cluster)
        n_points      : numero de radios en [r_min, r_max]
        sat_threshold : excluir puntos con N(R) > sat_threshold * N_total
                        (0.60: solo region de escalamiento genuina, antes de
                         la frontera dispersa que aplana la curva log-log)

    Retorna:
        radii_all, counts_all : arrays completos (para graficar)
        radii_fit, counts_fit : arrays usados en la regresion
        D, b, r2              : parametros del ajuste
    """
    xs, ys = np.where(grid > 0)
    N_total = len(xs)
    dists   = np.sqrt((xs - CENTER) ** 2 + (ys - CENTER) ** 2)
    max_r   = float(np.max(dists))

    if r_max is None:
        r_max = min(int(max_r * 0.75), 60)

    radii_all  = np.linspace(r_min, r_max, n_points)
    counts_all = np.array([int(np.sum(dists <= R)) for R in radii_all])

    # Excluir saturacion
    mask = (counts_all > 5) & (counts_all < sat_threshold * N_total)
    radii_fit  = radii_all[mask]
    counts_fit = counts_all[mask]

    log_r = np.log(radii_fit)
    log_n = np.log(counts_fit.astype(float))

    coeffs  = np.polyfit(log_r, log_n, 1)
    D, b    = float(coeffs[0]), float(coeffs[1])

    log_n_pred = np.polyval(coeffs, log_r)
    ss_res = float(np.sum((log_n - log_n_pred) ** 2))
    ss_tot = float(np.sum((log_n - np.mean(log_n)) ** 2))
    r2     = (1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    return radii_all, counts_all, radii_fit, counts_fit, D, b, r2, max_r


# ============================================================
# CALCULOS ANALITICOS (preguntas)
# ============================================================

def compute_two_point_dimension(N1=158, R1=10, N2=380, R2=20):
    """D = log(N2/N1) / log(R2/R1)  — ejemplo literal del enunciado."""
    return np.log(N2 / N1) / np.log(R2 / R1)


def compute_scaling_prediction(D=1.7, N_ref=200, R_ref=10, R_new=20):
    """N(R_new) = N_ref * (R_new/R_ref)^D"""
    return N_ref * (R_new / R_ref) ** D


# ============================================================
# GRAFICAS
# ============================================================

def _style_axes(ax):
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.6)


def save_figure_1(grid, radii_all, counts_all, radii_fit, counts_fit,
                  D, b, r2, max_r_cluster, path):
    """
    Figura 1 — dos paneles:
        Izquierdo : cluster DLA coloreado por orden de adhesion
        Derecho   : grafica log-log N(R) vs R con recta ajustada
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5))
    fig.patch.set_facecolor(BG_COLOR)
    for ax in axes:
        _style_axes(ax)

    # ---- Panel izquierdo: cluster DLA ----
    ax = axes[0]
    occupied = grid > 0
    display  = np.where(occupied, grid.astype(float), np.nan)

    img = ax.imshow(
        display.T,
        origin='lower',
        cmap='plasma',
        interpolation='nearest',
        vmin=1,
        vmax=N_PARTICLES + 1
    )
    cbar = plt.colorbar(img, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Orden de adhesion", color=TEXT_COLOR, fontsize=8)
    cbar.ax.yaxis.set_tick_params(color=TEXT_COLOR)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TEXT_COLOR, fontsize=7)
    cbar.outline.set_edgecolor(GRID_COLOR)

    ax.plot(CENTER, CENTER, 'o', color=ACCENT, markersize=7, zorder=5,
            label="Semilla central")
    ax.legend(fontsize=8, facecolor=BG_COLOR, edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, loc='upper right')

    n_cells = int(np.sum(occupied))
    ax.text(0.02, 0.97,
            f"Particulas: {N_PARTICLES}\n"
            f"Celdas ocupadas: {n_cells}\n"
            f"Radio del cluster: {int(max_r_cluster)} celdas\n"
            f"Rejilla: {GRID_SIZE}×{GRID_SIZE}",
            transform=ax.transAxes, color=TEXT_COLOR, fontsize=8, va='top',
            bbox=dict(facecolor=BG_COLOR, edgecolor=GRID_COLOR, alpha=0.85,
                      boxstyle='round,pad=0.4'))
    ax.set_title("Cluster DLA: crecimiento ramificado\n"
                 "(mapa de calor temporal — orden de adhesion)",
                 color=TEXT_COLOR, fontsize=10, pad=8)
    ax.set_xlabel("x (unidades de rejilla)", fontsize=9)
    ax.set_ylabel("y (unidades de rejilla)", fontsize=9)

    # ---- Panel derecho: log-log N(R) vs R ----
    ax = axes[1]

    # Todos los puntos
    mask_pos = counts_all > 0
    ax.scatter(radii_all[mask_pos], counts_all[mask_pos],
               color=DOT_COLOR, s=20, zorder=3, alpha=0.75,
               label="N(R) simulado")

    # Puntos usados en la regresion
    ax.scatter(radii_fit, counts_fit,
               color=ACCENT, s=30, zorder=4, alpha=0.9,
               label="Puntos de ajuste")

    # Recta ajustada
    r_line = np.linspace(radii_fit.min(), radii_fit.max(), 200)
    n_line = np.exp(b) * r_line ** D
    ax.plot(r_line, n_line, color=ACCENT, linewidth=2.0, zorder=5,
            label=f"Ajuste: $D = {D:.3f}$,  $R^2 = {r2:.4f}$")

    # Puntos literales (ejemplo dos puntos)
    D_lit = compute_two_point_dimension()
    ax.scatter([10, 20], [158, 380],
               color='#e87070', s=55, zorder=6, marker='D',
               label=f"Ejemplo literal: $D_{{2pt}}={D_lit:.3f}$")

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel("Radio $R$ (unidades de rejilla)", fontsize=9)
    ax.set_ylabel("Celdas ocupadas $N(R)$", fontsize=9)
    ax.set_title("Dimension fractal por mass-radius\n"
                 "$N(R) \\sim R^{\\,D}$  (ley de potencias)",
                 color=TEXT_COLOR, fontsize=10, pad=8)

    ax.text(0.05, 0.95,
            f"$D = {D:.3f}$\n$R^2 = {r2:.4f}$",
            transform=ax.transAxes, color=ACCENT, fontsize=11, va='top',
            bbox=dict(facecolor=BG_COLOR, edgecolor=GRID_COLOR, alpha=0.85,
                      boxstyle='round,pad=0.5'))
    ax.legend(fontsize=8, facecolor=BG_COLOR, edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, loc='lower right')

    fig.suptitle(
        "Agregacion Limitada por Difusion (DLA) — Dimension Fractal Urbana\n"
        "Batty y Longley (1994) — Morfologia y Crecimiento Urbano",
        color=TEXT_COLOR, fontsize=12, fontweight='bold', y=1.01
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    print(f"  Figura 1 guardada: {path}")


def save_figure_2(grid, max_r_cluster, path):
    """
    Figura 2 — vista detallada del cluster con circulos de referencia.
    """
    occupied = grid > 0
    display  = np.where(occupied, grid.astype(float), np.nan)

    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor(BG_COLOR)
    _style_axes(ax)

    ax.imshow(
        display.T,
        origin='lower',
        cmap='inferno',
        interpolation='nearest',
        vmin=1,
        vmax=grid.max()
    )
    cbar = plt.colorbar(ax.images[0], ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Orden de adhesion (particula #)", color=TEXT_COLOR, fontsize=9)
    cbar.ax.yaxis.set_tick_params(color=TEXT_COLOR)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TEXT_COLOR, fontsize=8)
    cbar.outline.set_edgecolor(GRID_COLOR)

    # Circulos de referencia
    theta = np.linspace(0, 2 * np.pi, 400)
    ref_radii = [(10, "R=10"), (20, "R=20"), (40, "R=40")]
    for r_ref, lbl in ref_radii:
        ax.plot(CENTER + r_ref * np.cos(theta),
                CENTER + r_ref * np.sin(theta),
                '--', color=ACCENT, linewidth=0.9, alpha=0.55)
        ax.text(CENTER + r_ref * 0.71, CENTER + r_ref * 0.71,
                lbl, color=ACCENT, fontsize=7.5, alpha=0.85)

    ax.plot(CENTER, CENTER, 'o', color='#80ff80', markersize=8,
            zorder=5, label="Semilla central")
    ax.legend(fontsize=9, facecolor=BG_COLOR, edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR)
    ax.set_xlabel("x (unidades de rejilla)", color=TEXT_COLOR, fontsize=9)
    ax.set_ylabel("y (unidades de rejilla)", color=TEXT_COLOR, fontsize=9)
    ax.set_title(
        "Cluster DLA — vista detallada con circulos de radio de referencia\n"
        "Batty y Longley (1994) — Morfologia Fractal Urbana",
        color=TEXT_COLOR, fontsize=10
    )

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    print(f"  Figura 2 guardada: {path}")


# ============================================================
# GUARDAR JSON DE DATOS CRUDOS
# ============================================================

def save_raw_data(grid, radii_all, counts_all, radii_fit, counts_fit,
                  D_sim, b_sim, r2_sim, max_r_cluster,
                  D_lit, N_pred_q2, path):
    data = {
        "teoria": "dla_batty_longley_fractal",
        "nombre": ("Agregacion limitada por difusion (DLA) y "
                   "dimension fractal urbana de Batty-Longley"),
        "autor": "Michael Batty y Paul Longley",
        "anio": "1994",
        "parametros_simulacion": {
            "grid_size": GRID_SIZE,
            "n_particles": N_PARTICLES,
            "seed": SEED,
            "launch_margin": LAUNCH_MARGIN,
            "kill_margin": KILL_MARGIN,
            "centro": [int(CENTER), int(CENTER)]
        },
        "dimension_fractal_simulacion": {
            "D": round(float(D_sim), 5),
            "R2": round(float(r2_sim), 5),
            "intercepto_log": round(float(b_sim), 5),
            "r_min_fit": float(radii_fit.min()),
            "r_max_fit": float(radii_fit.max()),
            "n_puntos_fit": int(len(radii_fit)),
            "n_puntos_total": int(len(radii_all)),
            "cluster_radius": int(max_r_cluster)
        },
        "dimension_fractal_ejemplo_literal": {
            "N1": 158, "R1": 10, "N2": 380, "R2": 20,
            "D": round(float(D_lit), 5),
            "formula": "D = log(N2/N1) / log(R2/R1)"
        },
        "prediccion_q2": {
            "D": 1.7, "N_ref": 200, "R_ref": 10, "R_nuevo": 20,
            "N_predicho": round(float(N_pred_q2), 2),
            "formula": "N(20) = 200 * (20/10)^1.7"
        },
        "mass_radius_data": {
            "radii": [round(float(r), 3) for r in radii_all.tolist()],
            "counts": [int(c) for c in counts_all.tolist()],
            "radii_fit": [round(float(r), 3) for r in radii_fit.tolist()],
            "counts_fit": [int(c) for c in counts_fit.tolist()]
        },
        "cluster_celdas_totales": int(np.sum(grid > 0))
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Datos crudos guardados: {path}")
    return data


# ============================================================
# GUARDAR JSON DE PREGUNTAS
# ============================================================

def save_preguntas(D_sim, D_lit, N_pred_q2, path):
    data = {
        "teoria": "dla_batty_longley_fractal",
        "nombre": ("Agregacion limitada por difusion (DLA) y "
                   "dimension fractal urbana de Batty-Longley"),
        "autor": "Michael Batty y Paul Longley",
        "anio": "1994",
        "preguntas": [
            {
                "q": ("Usando la relacion mass-radius N(R) ~ R^D, un cluster sintetico "
                      "contiene N_1=158 celdas dentro de radio R_1=10 y N_2=380 celdas "
                      "dentro de radio R_2=20. Calcula la dimension fractal "
                      "D = log(N_2/N_1)/log(R_2/R_1) (forma mas ramificada que la "
                      "urbana tipica ~1.7). "
                      "Formato: 'Respuesta final: <valor>'."),
                "valor_exacto": f"{D_lit:.3f}",
                "tipo": "forma_cerrada",
                "tolerancia": "±0.01 (1.266)",
                "como_computar": (
                    "D = log(380/158) / log(20/10) = "
                    "log(2.4051) / log(2) = "
                    f"{np.log(380/158):.5f} / {np.log(20/10):.5f} = {D_lit:.5f}"
                )
            },
            {
                "q": ("Una forma urbana cumple N(R) ~ R^D con dimension fractal D=1.7. "
                      "Si dentro de radio R=10 hay 200 celdas ocupadas, cuantas celdas "
                      "ocupadas se esperan dentro de radio R=20? "
                      "Formato: 'Respuesta final: <valor>'."),
                "valor_exacto": f"{N_pred_q2:.1f}",
                "tipo": "forma_cerrada",
                "tolerancia": "±1% (649.8)",
                "como_computar": (
                    "N(20) = 200 * (20/10)^1.7 = 200 * 2^1.7 = "
                    f"200 * {2**1.7:.5f} = {N_pred_q2:.4f}"
                )
            },
            {
                "q": ("Simula DLA en rejilla 201x201 con semilla central, 1500 "
                      "particulas en caminata aleatoria, numpy.random.seed(3); "
                      "luego mide la dimension fractal por mass-radius "
                      "(regresion log N(R) vs log R sobre la region de "
                      "escalamiento, radios ~5..35, excluyendo saturacion "
                      "N>60% del total). Reporta la dimension fractal D estimada. "
                      "Formato: 'Respuesta final: <valor>'."),
                "valor_exacto": f"{D_sim:.3f}",
                "tipo": "emergente",
                "tolerancia": "±0.12 en torno a 1.71",
                "como_computar": (
                    f"Simulacion DLA 201x201, {N_PARTICLES} particulas, seed={SEED}, "
                    f"regresion log-log excluyendo saturacion (N>60% total). "
                    f"D obtenido = {D_sim:.5f}"
                )
            }
        ]
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Preguntas guardadas: {path}")
    return data


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 62)
    print("DLA y Dimension Fractal Urbana — Batty y Longley (1994)")
    print("=" * 62)

    # 1. Simulacion DLA
    print(f"\n[1] Simulando DLA ({GRID_SIZE}x{GRID_SIZE}, "
          f"{N_PARTICLES} particulas, seed={SEED})...")
    grid, cluster_radius = simulate_dla()
    n_cells = int(np.sum(grid > 0))
    print(f"    Celdas ocupadas : {n_cells}")
    print(f"    Radio del cluster: {cluster_radius}")

    # 2. Dimension fractal
    print("\n[2] Midiendo dimension fractal por mass-radius...")
    (radii_all, counts_all,
     radii_fit, counts_fit,
     D_sim, b_sim, r2_sim, max_r) = measure_fractal_dimension(grid)
    print(f"    D (simulacion)  = {D_sim:.5f}")
    print(f"    R^2             = {r2_sim:.5f}")
    print(f"    Rango de ajuste = [{radii_fit.min():.1f}, {radii_fit.max():.1f}]")

    # 3. Ejemplo literal dos puntos
    D_lit = compute_two_point_dimension()
    print(f"\n[3] Ejemplo literal (N1=158, R1=10, N2=380, R2=20):")
    print(f"    D = log(380/158)/log(20/10) = {D_lit:.5f}")

    # 4. Prediccion Q2
    N_pred_q2 = compute_scaling_prediction()
    print(f"\n[4] Prediccion Q2 (D=1.7, N_ref=200, R_ref=10, R_new=20):")
    print(f"    N(20) = 200 * 2^1.7 = {N_pred_q2:.4f}")

    # 5. Validacion
    ok_D  = (1.60 <= D_sim <= 1.80)
    ok_r2 = (r2_sim > 0.97)
    print(f"\n[5] Criterio de validacion:")
    print(f"    D = {D_sim:.3f}  | rango valido 1.70 +/- 0.10  -> {'OK' if ok_D else 'FALLO'}")
    print(f"    R^2 = {r2_sim:.4f} > 0.97                    -> {'OK' if ok_r2 else 'FALLO'}")

    # 6. Graficas
    print("\n[6] Generando graficas PNG...")
    fig1 = ASSETS_DIR / "sim_dla_batty_longley_fractal_1.png"
    fig2 = ASSETS_DIR / "sim_dla_batty_longley_fractal_2.png"
    save_figure_1(grid, radii_all, counts_all, radii_fit, counts_fit,
                  D_sim, b_sim, r2_sim, max_r, fig1)
    save_figure_2(grid, max_r, fig2)

    # 7. Datos crudos
    print("\n[7] Guardando datos crudos JSON...")
    raw_path = SIM_DIR / "datos_dla_batty_longley_fractal.json"
    save_raw_data(grid, radii_all, counts_all, radii_fit, counts_fit,
                  D_sim, b_sim, r2_sim, max_r, D_lit, N_pred_q2, raw_path)

    # 8. Preguntas
    print("\n[8] Guardando respuestas a preguntas JSON...")
    preg_path = SIM_DIR / "preguntas_dla_batty_longley_fractal.json"
    save_preguntas(D_sim, D_lit, N_pred_q2, preg_path)

    print("\n" + "=" * 62)
    print("RESUMEN FINAL")
    print("=" * 62)
    print(f"  D simulacion (mass-radius): {D_sim:.5f}")
    print(f"  R^2 simulacion:             {r2_sim:.5f}")
    print(f"  D ejemplo literal (2 pts):  {D_lit:.5f}")
    print(f"  N predicho Q2 (D=1.7):      {N_pred_q2:.4f}")
    print(f"  Validacion D (1.70+/-0.10): {'OK' if ok_D else 'FALLO'} ({D_sim:.3f})")
    print(f"  Validacion R^2 (>0.97):     {'OK' if ok_r2 else 'FALLO'} ({r2_sim:.4f})")
    print("=" * 62)

    return {
        "D_sim":      D_sim,
        "r2_sim":     r2_sim,
        "D_lit":      D_lit,
        "N_pred_q2":  N_pred_q2,
        "ok_D":       ok_D,
        "ok_r2":      ok_r2
    }


if __name__ == "__main__":
    results = main()
