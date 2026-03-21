#!/usr/bin/env python3
"""
Genera una lamina conceptual sobre la ciudad amurallada entendida como
membrana selectiva: abierta a flujos regulados y cerrada ante la amenaza.

Salida: ../Clase 1/apoyosGraficosCreados/ciudad_amurallada_membrana_selectiva.png
"""

import pathlib

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "Clase 1" / "apoyosGraficosCreados" / "ciudad_amurallada_membrana_selectiva.png"
DPI = 300

C_BG = "#f5f0e8"
C_DARK = "#1f2937"
C_MID = "#4b5563"
C_STONE = "#8a7e6f"
C_WHITE = "#fffdf8"
C_GOLD = "#c9a84c"
C_GOLD_SOFT = "#efe2bb"
C_GREEN = "#1a7a6d"
C_GREEN_L = "#dff1ec"
C_RED = "#a63c28"
C_RED_L = "#f7ddd5"
C_WALL = "#75675b"
C_WATER = "#b8d9e8"


def rounded_box(ax, x, y, w, h, facecolor, edgecolor, lw=2.0, alpha=0.96, radius=0.2):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.03,rounding_size={radius}",
        linewidth=lw,
        edgecolor=edgecolor,
        facecolor=facecolor,
        alpha=alpha,
        zorder=1,
    )
    ax.add_patch(patch)
    return patch


def add_panel_title(ax, x, y, title, color):
    ax.text(
        x,
        y,
        title,
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color=color,
        fontfamily="serif",
        zorder=4,
    )


def add_label(ax, x, y, text, size=9.2, color=C_MID, weight="normal", ha="center"):
    ax.text(
        x,
        y,
        text,
        ha=ha,
        va="center",
        fontsize=size,
        color=color,
        fontfamily="serif",
        fontweight=weight,
        zorder=5,
    )


def arrow(ax, start, end, color, lw=2.2, style="-|>", rad=0.0, ls="-"):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle=style,
        mutation_scale=12,
        linewidth=lw,
        color=color,
        connectionstyle=f"arc3,rad={rad}",
        linestyle=ls,
        zorder=3,
    )
    ax.add_patch(patch)


def draw_gate(ax, center, orientation="horizontal", color=C_GOLD, closed=False):
    x, y = center
    if orientation == "horizontal":
        gate = Rectangle((x - 0.35, y - 0.08), 0.7, 0.16, facecolor=color, edgecolor=C_STONE, linewidth=1.2, zorder=6)
        ax.add_patch(gate)
        if closed:
            ax.plot([x - 0.24, x + 0.24], [y - 0.16, y + 0.16], color=C_RED, lw=2.2, zorder=7)
            ax.plot([x - 0.24, x + 0.24], [y + 0.16, y - 0.16], color=C_RED, lw=2.2, zorder=7)
    else:
        gate = Rectangle((x - 0.08, y - 0.35), 0.16, 0.7, facecolor=color, edgecolor=C_STONE, linewidth=1.2, zorder=6)
        ax.add_patch(gate)
        if closed:
            ax.plot([x - 0.16, x + 0.16], [y - 0.24, y + 0.24], color=C_RED, lw=2.2, zorder=7)
            ax.plot([x - 0.16, x + 0.16], [y + 0.24, y - 0.24], color=C_RED, lw=2.2, zorder=7)


def draw_city(ax, center, mode="open"):
    cx, cy = center
    outer_r = 1.95
    inner_r = 1.38

    # Exterior
    water = Circle((cx, cy), outer_r + 0.7, facecolor=C_WATER, edgecolor="none", alpha=0.10, zorder=0)
    ax.add_patch(water)

    # Ciudad interior
    city = Circle((cx, cy), inner_r, facecolor=C_GOLD_SOFT, edgecolor=C_GOLD, linewidth=2.0, zorder=2)
    ax.add_patch(city)

    # Muralla / membrana
    wall_edge = C_GREEN if mode == "open" else C_RED
    wall_fill = C_WHITE
    wall = Circle((cx, cy), outer_r, facecolor=wall_fill, edgecolor=wall_edge, linewidth=8.5, zorder=2.5)
    ax.add_patch(wall)

    # Puertas
    gate_closed = mode == "closed"
    draw_gate(ax, (cx, cy + outer_r), "horizontal", closed=gate_closed)
    draw_gate(ax, (cx + outer_r, cy), "vertical", closed=gate_closed)
    draw_gate(ax, (cx, cy - outer_r), "horizontal", closed=gate_closed)
    draw_gate(ax, (cx - outer_r, cy), "vertical", closed=gate_closed)

    # Capas internas
    add_label(ax, cx, cy + 0.55, "Interior protegido", size=12.4, color=C_DARK, weight="bold")
    add_label(ax, cx, cy + 0.15, "casas · talleres · reservas", size=8.8)
    add_label(ax, cx, cy - 0.15, "mercado · vida comun · bienes", size=8.8)
    add_label(ax, cx, cy - 0.55, "la muralla resguarda acumulacion y convivencia", size=8.0)

    if mode == "open":
        add_label(ax, cx, cy - 2.55, "Modo abierto: permeabilidad regulada", size=10.4, color=C_GREEN, weight="bold")
        # flujos permitidos
        arrow(ax, (cx, cy + 3.1), (cx, cy + 2.05), C_GREEN, rad=0.0)
        arrow(ax, (cx + 3.15, cy), (cx + 2.05, cy), C_GREEN, rad=0.0)
        arrow(ax, (cx - 3.15, cy), (cx - 2.05, cy), C_GREEN, rad=0.0)
        arrow(ax, (cx, cy - 3.15), (cx, cy - 2.05), C_GREEN, rad=0.0)

        add_label(ax, cx, cy + 3.35, "personas", size=8.7)
        add_label(ax, cx + 3.55, cy, "mercancias", size=8.7, ha="left")
        add_label(ax, cx - 3.55, cy, "informacion", size=8.7, ha="right")
        add_label(ax, cx, cy - 3.45, "agua y recursos", size=8.7)
    else:
        add_label(ax, cx, cy - 2.55, "Modo cerrado: defensa y control", size=10.4, color=C_RED, weight="bold")
        # amenazas bloqueadas
        arrow(ax, (cx, cy + 3.1), (cx, cy + 2.38), C_RED, rad=0.0)
        arrow(ax, (cx + 3.15, cy), (cx + 2.38, cy), C_RED, rad=0.0)
        arrow(ax, (cx - 3.15, cy), (cx - 2.38, cy), C_RED, rad=0.0)
        arrow(ax, (cx, cy - 3.15), (cx, cy - 2.38), C_RED, rad=0.0)

        # marcas de bloqueo
        ax.plot([cx - 0.18, cx + 0.18], [cy + 2.28, cy + 2.64], color=C_RED, lw=2.0, zorder=7)
        ax.plot([cx - 0.18, cx + 0.18], [cy + 2.64, cy + 2.28], color=C_RED, lw=2.0, zorder=7)

        ax.plot([cx + 2.28, cx + 2.64], [cy - 0.18, cy + 0.18], color=C_RED, lw=2.0, zorder=7)
        ax.plot([cx + 2.28, cx + 2.64], [cy + 0.18, cy - 0.18], color=C_RED, lw=2.0, zorder=7)

        ax.plot([cx - 2.28, cx - 2.64], [cy - 0.18, cy + 0.18], color=C_RED, lw=2.0, zorder=7)
        ax.plot([cx - 2.28, cx - 2.64], [cy + 0.18, cy - 0.18], color=C_RED, lw=2.0, zorder=7)

        ax.plot([cx - 0.18, cx + 0.18], [cy - 2.28, cy - 2.64], color=C_RED, lw=2.0, zorder=7)
        ax.plot([cx - 0.18, cx + 0.18], [cy - 2.64, cy - 2.28], color=C_RED, lw=2.0, zorder=7)

        add_label(ax, cx, cy + 3.35, "amenaza", size=8.7)
        add_label(ax, cx + 3.55, cy, "incursion", size=8.7, ha="left")
        add_label(ax, cx - 3.55, cy, "saqueo", size=8.7, ha="right")
        add_label(ax, cx, cy - 3.45, "riesgo externo", size=8.7)


def draw_scale_strip(ax):
    rounded_box(ax, -8.8, -4.45, 17.6, 1.18, C_WHITE, C_STONE, lw=1.6, alpha=0.96, radius=0.16)
    add_label(ax, -8.1, -3.86, "Escalas de proteccion:", size=10.8, color=C_DARK, weight="bold", ha="left")

    rounded_box(ax, -3.8, -4.22, 2.8, 0.62, C_GOLD_SOFT, C_GOLD, lw=1.4, radius=0.12)
    rounded_box(ax, -0.45, -4.22, 3.2, 0.62, C_GOLD_SOFT, C_GOLD, lw=1.4, radius=0.12)
    rounded_box(ax, 3.45, -4.22, 3.2, 0.62, C_GOLD_SOFT, C_GOLD, lw=1.4, radius=0.12)

    add_label(ax, -2.4, -3.91, "vivienda", size=9.0, color=C_DARK, weight="bold")
    add_label(ax, 1.15, -3.91, "barrio / proximidad", size=9.0, color=C_DARK, weight="bold")
    add_label(ax, 5.05, -3.91, "ciudad amurallada", size=9.0, color=C_DARK, weight="bold")

    arrow(ax, (-0.98, -3.91), (-0.52, -3.91), C_STONE, lw=1.8)
    arrow(ax, (2.83, -3.91), (3.38, -3.91), C_STONE, lw=1.8)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(19, 10.5), dpi=DPI)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    rounded_box(ax, -8.85, 4.35, 4.65, 0.62, C_GOLD, C_GOLD, lw=0.0, alpha=1.0, radius=0.12)
    add_label(ax, -6.52, 4.66, "CIUDAD AMURALLADA · CLASE 1", size=10.6, color=C_WHITE, weight="bold")

    ax.text(
        0.0,
        3.95,
        "La muralla como membrana selectiva",
        ha="center",
        va="center",
        fontsize=28,
        fontweight="bold",
        color=C_DARK,
        fontfamily="serif",
    )
    ax.text(
        0.0,
        3.48,
        "Cierre perimetral, puertas reguladas y seguridad en distintas escalas",
        ha="center",
        va="center",
        fontsize=12.2,
        color=C_MID,
        fontfamily="serif",
        fontstyle="italic",
    )

    rounded_box(ax, -8.9, -3.05, 8.45, 5.95, C_GREEN_L, C_GREEN, lw=2.4, alpha=0.22, radius=0.34)
    rounded_box(ax, 0.45, -3.05, 8.45, 5.95, C_RED_L, C_RED, lw=2.4, alpha=0.20, radius=0.34)

    add_panel_title(ax, -4.2, 2.52, "Permeabilidad", C_GREEN)
    add_panel_title(ax, 4.65, 2.52, "Cierre defensivo", C_RED)

    draw_city(ax, (-4.2, -0.05), mode="open")
    draw_city(ax, (4.65, -0.05), mode="closed")

    draw_scale_strip(ax)

    rounded_box(ax, -8.8, 2.92, 17.6, 0.42, C_WHITE, C_STONE, lw=1.1, alpha=0.92, radius=0.1)
    add_label(
        ax,
        0.0,
        3.12,
        "La ciudad protege bienes y vidas porque no deja circular todo del mismo modo: filtra.",
        size=9.6,
        color=C_MID,
    )

    ax.set_xlim(-9.2, 9.2)
    ax.set_ylim(-4.85, 5.2)
    ax.axis("off")

    plt.tight_layout(pad=0.45)
    fig.savefig(
        OUT,
        dpi=DPI,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    plt.close(fig)
    print(f"✓ Diagrama generado: {OUT}  ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
