#!/usr/bin/env python3
"""
Genera 2 PNG de costos para la ponencia Yuk Hui.
Estética: fondo #0e1a2b, texto #e8e6e1, ámbar #e0a458
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path

# ── Paleta ──────────────────────────────────────────────────
BG    = "#0e1a2b"
FG    = "#e8e6e1"
AMBER = "#e0a458"
BLUE  = "#5b9bd5"
GREEN = "#6abf69"
RED   = "#e57373"
GRAY  = "#8899aa"

ASSETS = Path("/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui/presentacion/assets")
ASSETS.mkdir(parents=True, exist_ok=True)

# Fuente única de verdad: costos.json regenerado por experimento/medir_costos.py
# (precios API oficiales Anthropic jun-2026: Opus 4.8 $5/$25; Sonnet 4.6 $3/$15).
COSTOS_JSON = Path("/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui/experimento/costos.json")
with open(COSTOS_JSON, encoding="utf-8") as _f:
    _COSTOS = json.load(_f)["vias"]

def aplicar_estilo_base(fig, ax):
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.spines["bottom"].set_color(GRAY)
    ax.spines["left"].set_color(GRAY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=FG, labelsize=10)
    ax.xaxis.label.set_color(FG)
    ax.yaxis.label.set_color(FG)
    ax.title.set_color(FG)
    ax.yaxis.set_tick_params(which="minor", length=0)


# ─────────────────────────────────────────────────────────────
# GRÁFICO 1: costo_por_respuesta_correcta.png (escala log)
# ─────────────────────────────────────────────────────────────
def grafico_costo_por_correcta():
    # Datos (centro geométrico para rangos, error bars en log)
    vias = [
        "Python\nlocal",
        "qwen2.5\n:3b",
        "qwen3\n:14b",
        "gpt-oss\n:20b",
        "qwen3\n:32b",
        "Claude\nSonnet",
        "Claude\nOpus",
    ]

    # Valores medidos / estimados — leídos de costos.json (fuente única de verdad)
    def _cpr(via):
        return _COSTOS[via]["costo_por_resp_correcta_usd"]["valor"]
    def _cpr_rango(via):
        d = _COSTOS[via]["costo_por_resp_correcta_usd"]
        return d["rango_min"], d["rango_max"]

    # Python: valor único estimado
    py_cpr   = _COSTOS["python_local"]["costo_por_resp_correcta_usd"]["valor"]

    # Locales: valor único (medido tiempo, potencia medida, tarifa estimada)
    q3b_cpr  = _cpr("qwen2.5:3b")
    q14_cpr  = _cpr("qwen3:14b")
    gpt_cpr  = _cpr("gpt-oss:20b")
    q32_cpr  = _cpr("qwen3:32b")

    # API: rangos [min, max]
    son_min, son_max = _cpr_rango("claude-sonnet")
    opus_min, opus_max = _cpr_rango("claude-opus")

    # Para barras: usar valor central (geométrico para escala log) y error bars
    def geom_center(lo, hi):
        return np.sqrt(lo * hi)

    son_ctr  = geom_center(son_min, son_max)
    opus_ctr = geom_center(opus_min, opus_max)

    centros = np.array([py_cpr, q3b_cpr, q14_cpr, gpt_cpr, q32_cpr, son_ctr, opus_ctr])

    # Error bars en espacio log (asimétricas en lineal)
    err_lo = np.array([0, 0, 0, 0, 0, son_ctr - son_min, opus_ctr - opus_min])
    err_hi = np.array([0, 0, 0, 0, 0, son_max - son_ctr, opus_max - opus_ctr])

    # Colores por tipo
    colores = [GREEN, BLUE, BLUE, BLUE, BLUE, AMBER, RED]

    fig, ax = plt.subplots(figsize=(12, 6))
    aplicar_estilo_base(fig, ax)

    x = np.arange(len(vias))
    bars = ax.bar(x, centros, color=colores, alpha=0.85, width=0.6, zorder=3)

    # Error bars solo para APIs
    for i in range(len(vias)):
        if err_lo[i] > 0 or err_hi[i] > 0:
            ax.errorbar(
                x[i], centros[i],
                yerr=[[err_lo[i]], [err_hi[i]]],
                fmt="none", color=FG, capsize=6, linewidth=1.5, capthick=1.5, zorder=4
            )

    ax.set_yscale("log")
    ax.set_ylim(1e-7, 1.5)
    ax.yaxis.set_major_formatter(ticker.LogFormatterMathtext())
    ax.grid(axis="y", color=GRAY, alpha=0.25, linestyle="--", zorder=1)
    ax.set_xticks(x)
    ax.set_xticklabels(vias, fontsize=10.5, color=FG)

    # Etiquetas encima de cada barra — derivadas de los valores leídos
    etiquetas_centros = [
        f"${py_cpr*1e6:.1f}×10⁻⁶",
        f"${q3b_cpr:.6f}",
        f"${q14_cpr:.6f}",
        f"${gpt_cpr:.6f}",
        f"${q32_cpr:.5f}",
        f"${son_min:.3f}–${son_max:.3f}",
        f"${opus_min:.3f}–${opus_max:.3f}",
    ]
    for i, (bar, lbl) in enumerate(zip(bars, etiquetas_centros)):
        y_pos = centros[i] * (1 + err_hi[i] / centros[i] if err_hi[i] > 0 else 1) * 1.6
        ax.text(
            x[i], y_pos, lbl,
            ha="center", va="bottom", fontsize=8.5, color=FG,
            rotation=0
        )

    # Leyenda informal
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=GREEN,  label="Python determinista"),
        Patch(facecolor=BLUE,   label="Modelos locales (kratos)"),
        Patch(facecolor=AMBER,  label="API Claude Sonnet"),
        Patch(facecolor=RED,    label="API Claude Opus"),
    ]
    leg = ax.legend(
        handles=legend_elements, loc="upper left",
        framealpha=0.15, edgecolor=GRAY,
        labelcolor=FG, fontsize=9, facecolor=BG
    )

    ax.set_xlabel("Vía de conocimiento", fontsize=12, labelpad=8)
    ax.set_ylabel("Costo por respuesta correcta (USD)", fontsize=11)
    ax.set_title(
        "Costo por respuesta correcta — escala logarítmica\n"
        "(barras API: rango [mín, máx] con error bars; locales: valor único)",
        fontsize=12, pad=12
    )

    # Nota metodológica
    fig.text(
        0.01, 0.01,
        "Supuestos: tarifa 0.20 USD/kWh; potencia portátil 25 W estimado; GPU RTX 5070 Ti 281.5 W medido; tokens=chars/3.5",
        fontsize=7, color=GRAY, ha="left"
    )

    out = ASSETS / "costo_por_respuesta_correcta.png"
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(out, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close()
    print(f"Guardado: {out}")
    return out


# ─────────────────────────────────────────────────────────────
# GRÁFICO 2: tiempo_por_via.png
# ─────────────────────────────────────────────────────────────
def grafico_tiempo_por_via():
    vias = [
        "Python\nlocal",
        "qwen2.5\n:3b",
        "qwen3\n:14b",
        "gpt-oss\n:20b",
        "qwen3\n:32b",
        "Claude\nSonnet",
        "Claude\nOpus",
    ]

    # Tiempos en segundos (medidos excepto API)
    tiempos = np.array([
        70.786,    # python local  — medido
        159.8,     # qwen2.5:3b   — medido
        483.9,     # qwen3:14b    — medido
        1111.1,    # gpt-oss:20b  — medido
        3682.6,    # qwen3:32b    — medido
        np.nan,    # claude-sonnet — no medido
        np.nan,    # claude-opus  — no medido
    ])

    colores = [GREEN, BLUE, BLUE, BLUE, BLUE, AMBER, RED]

    fig, ax = plt.subplots(figsize=(12, 5.5))
    aplicar_estilo_base(fig, ax)

    x = np.arange(len(vias))

    # Barras medidas
    mask_val = ~np.isnan(tiempos)
    for i in range(len(vias)):
        if mask_val[i]:
            ax.bar(x[i], tiempos[i], color=colores[i], alpha=0.85, width=0.6, zorder=3)
        else:
            # Barra fantasma con texto "no medido"
            ax.bar(x[i], 100, color=GRAY, alpha=0.3, width=0.6, zorder=3, hatch="///")
            ax.text(x[i], 200, "no\nmedido", ha="center", va="bottom",
                    fontsize=9, color=GRAY, style="italic")

    ax.set_yscale("log")
    ax.set_ylim(10, 20000)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f}s"))
    ax.grid(axis="y", color=GRAY, alpha=0.25, linestyle="--", zorder=1)
    ax.set_xticks(x)
    ax.set_xticklabels(vias, fontsize=10.5, color=FG)

    # Etiquetas sobre barras medidas
    etiquetas = ["70.8s", "159.8s", "483.9s", "1 111s", "3 683s", "", ""]
    for i, (t, lbl) in enumerate(zip(tiempos, etiquetas)):
        if not np.isnan(t) and lbl:
            ax.text(x[i], t * 1.3, lbl, ha="center", va="bottom",
                    fontsize=9.5, color=FG)

    # Líneas de referencia con tiempo en minutos
    for secs, label in [(60, "1 min"), (600, "10 min"), (3600, "1 hora")]:
        ax.axhline(secs, color=GRAY, alpha=0.4, linestyle=":", linewidth=1)
        ax.text(len(vias) - 0.45, secs * 1.1, label, color=GRAY, fontsize=8, ha="right")

    ax.set_xlabel("Vía de conocimiento", fontsize=12, labelpad=8)
    ax.set_ylabel("Tiempo total banco completo (s, log)", fontsize=11)
    ax.set_title(
        "Tiempo total por vía para responder el banco completo (49 preguntas)\n"
        "(escala logarítmica; API: tiempo de servidor no disponible)",
        fontsize=12, pad=12
    )

    fig.text(
        0.01, 0.01,
        "Tiempos medidos desde elapsed_s (JSON de respuestas). API: tiempo de servidor no accesible externamente.",
        fontsize=7.5, color=GRAY, ha="left"
    )

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=GREEN,  label="Python determinista (medido)"),
        Patch(facecolor=BLUE,   label="Modelos locales kratos (medido)"),
        Patch(facecolor=AMBER,  label="Claude Sonnet (no medido)"),
        Patch(facecolor=RED,    label="Claude Opus (no medido)"),
    ]
    leg = ax.legend(
        handles=legend_elements, loc="upper left",
        framealpha=0.15, edgecolor=GRAY,
        labelcolor=FG, fontsize=9, facecolor=BG
    )

    out = ASSETS / "tiempo_por_via.png"
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close()
    print(f"Guardado: {out}")
    return out


if __name__ == "__main__":
    p1 = grafico_costo_por_correcta()
    p2 = grafico_tiempo_por_via()
    print("\nVerificando archivos:")
    for p in [p1, p2]:
        size = Path(p).stat().st_size
        print(f"  {p.name}: {size:,} bytes {'OK' if size > 1000 else 'ERROR-vacío'}")
