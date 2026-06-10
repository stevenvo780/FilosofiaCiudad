#!/usr/bin/env python3
"""
Genera una comparativa visual de ciudad griega y ciudad romana siguiendo
un lenguaje mas cercano al de las diapositivas del curso: dos paneles,
ciudades amuralladas y etiquetas urbanas principales.

La lamina incorpora la idea de la muralla como borde regulador sin volver
la composicion demasiado abstracta.

Salida:
../Clase 1/apoyosGraficosCreados/ciudades_amuralladas_comparativa_membrana.png
"""

from __future__ import annotations

import math
import pathlib

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "Clase 1" / "apoyosGraficosCreados" / "ciudades_amuralladas_comparativa_membrana.png"
DPI = 300

C_BG = "#f5f0e8"
C_WHITE = "#fffdf8"
C_DARK = "#1f2937"
C_MID = "#4b5563"
C_STONE = "#8a7e6f"
C_WALL = "#75675b"
C_GOLD = "#c99a3f"
C_GOLD_SOFT = "#e7d2a6"
C_RED = "#9c3e36"
C_RED_SOFT = "#e7c6bf"
C_GREEN = "#356a57"
C_GREEN_SOFT = "#dbe8db"
C_WATER = "#c7e3ea"
C_EARTH = "#d8c9ae"
C_ROOF = "#bf6a44"
C_GRASS = "#c9d7ae"
C_ROAD = "#b89e78"
C_LABEL = "#f4efe4"


def rounded_box(ax, x, y, w, h, facecolor, edgecolor, lw=1.8, radius=0.16, alpha=1.0, zorder=1):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.03,rounding_size={radius}",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=lw,
        alpha=alpha,
        zorder=zorder,
    )
    ax.add_patch(box)
    return box


def add_text(ax, x, y, text, size=10, color=C_DARK, weight="normal", ha="center", va="center", style="normal", z=8):
    ax.text(
        x,
        y,
        text,
        fontsize=size,
        color=color,
        fontweight=weight,
        ha=ha,
        va=va,
        fontfamily="serif",
        fontstyle=style,
        zorder=z,
    )


def add_bar(ax, x, y, w, h, color, text):
    rounded_box(ax, x, y, w, h, color, color, lw=0, radius=0.05, zorder=3)
    add_text(ax, x + w / 2, y + h / 2, text, size=17, color=C_WHITE, weight="bold")


def add_marker(ax, x, y, label, facecolor):
    ax.add_patch(Circle((x, y), 0.13, facecolor=facecolor, edgecolor=C_WHITE, linewidth=1.2, zorder=8))
    add_text(ax, x, y - 0.005, str(label), size=9.2, color=C_WHITE, weight="bold", z=9)


def add_legend_row(ax, x, y, items, facecolor, edgecolor):
    rounded_box(ax, x, y, 5.8, 0.42, C_LABEL, edgecolor, lw=1.0, radius=0.06, zorder=2)
    cursor = x + 0.18
    for num, text in items:
        ax.add_patch(Circle((cursor, y + 0.21), 0.09, facecolor=facecolor, edgecolor=C_WHITE, linewidth=0.8, zorder=4))
        add_text(ax, cursor, y + 0.205, str(num), size=6.7, color=C_WHITE, weight="bold", z=5)
        add_text(ax, cursor + 0.16, y + 0.21, text, size=7.4, color=C_DARK, ha="left", z=5)
        cursor += 0.16 + 0.055 * len(text) + 0.24


def draw_house(ax, x, y, w=0.28, h=0.18, roof=C_ROOF, body="#f3eadb", z=5):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=body, edgecolor=C_STONE, linewidth=0.5, zorder=z))
    roof_poly = Polygon(
        [(x - 0.02, y + h), (x + w / 2, y + h + 0.09), (x + w + 0.02, y + h)],
        closed=True,
        facecolor=roof,
        edgecolor=C_STONE,
        linewidth=0.5,
        zorder=z + 0.1,
    )
    ax.add_patch(roof_poly)


def draw_tower(ax, x, y, r=0.12):
    ax.add_patch(Circle((x, y), r, facecolor=C_EARTH, edgecolor=C_WALL, linewidth=1.1, zorder=6))


def draw_gate(ax, x, y, orientation="h"):
    if orientation == "h":
        ax.add_patch(Rectangle((x - 0.24, y - 0.04), 0.48, 0.08, facecolor=C_GOLD, edgecolor=C_WALL, linewidth=0.8, zorder=7))
    else:
        ax.add_patch(Rectangle((x - 0.04, y - 0.24), 0.08, 0.48, facecolor=C_GOLD, edgecolor=C_WALL, linewidth=0.8, zorder=7))


def draw_flow(ax, start, end, color=C_GREEN):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="<|-|>",
            mutation_scale=10,
            linewidth=1.4,
            color=color,
            zorder=7,
        )
    )


def draw_greek_panel(ax, x0, y0, w, h):
    rounded_box(ax, x0, y0, w, h, "#f8f5ee", "#d9c9b1", lw=1.6, radius=0.06, zorder=1)
    add_bar(ax, x0, y0 + h + 0.08, w, 0.58, C_GOLD, "CIUDAD GRIEGA")

    # terreno
    terrain = Polygon(
        [
            (x0 + 0.55, y0 + 2.95),
            (x0 + 2.25, y0 + 3.55),
            (x0 + 4.35, y0 + 3.42),
            (x0 + 5.85, y0 + 2.85),
            (x0 + 5.45, y0 + 1.2),
            (x0 + 4.65, y0 + 0.58),
            (x0 + 2.2, y0 + 0.65),
            (x0 + 0.88, y0 + 1.08),
        ],
        closed=True,
        facecolor=C_GRASS,
        edgecolor="#bac596",
        linewidth=1.0,
        zorder=2,
    )
    ax.add_patch(terrain)

    water = Polygon(
        [(x0 + 1.95, y0 + 0.0), (x0 + 3.55, y0 + 0.0), (x0 + 4.1, y0 + 0.55), (x0 + 1.55, y0 + 0.55)],
        closed=True,
        facecolor=C_WATER,
        edgecolor="#8fb8c0",
        linewidth=1.0,
        zorder=1.5,
    )
    ax.add_patch(water)

    # muralla irregular
    wall_pts = [
        (x0 + 1.05, y0 + 1.35),
        (x0 + 1.0, y0 + 2.75),
        (x0 + 2.1, y0 + 3.2),
        (x0 + 3.95, y0 + 3.12),
        (x0 + 5.15, y0 + 2.55),
        (x0 + 4.95, y0 + 1.4),
        (x0 + 3.85, y0 + 0.9),
        (x0 + 2.2, y0 + 0.95),
    ]
    ax.add_patch(Polygon(wall_pts, closed=True, fill=False, edgecolor=C_WALL, linewidth=2.2, zorder=5))
    for tx, ty in wall_pts:
        draw_tower(ax, tx, ty)

    gate = (x0 + 2.75, y0 + 0.95)
    draw_gate(ax, gate[0], gate[1], "h")

    # camino y puerto
    ax.plot([gate[0], x0 + 2.7], [gate[1], y0 + 0.6], color=C_ROAD, lw=2.0, zorder=4)
    ax.plot([x0 + 2.7, x0 + 2.72], [y0 + 0.6, y0 + 0.28], color=C_ROAD, lw=2.0, zorder=4)
    ax.add_patch(Rectangle((x0 + 2.48, y0 + 0.34), 0.46, 0.22, facecolor="#ccb489", edgecolor=C_STONE, linewidth=0.6, zorder=4))
    ax.add_patch(Rectangle((x0 + 2.98, y0 + 0.3), 0.34, 0.18, facecolor="#ccb489", edgecolor=C_STONE, linewidth=0.6, zorder=4))

    # puerto/barcos
    for bx in [x0 + 2.2, x0 + 2.7, x0 + 3.2]:
        ax.add_patch(Ellipse((bx, y0 + 0.17), 0.2, 0.07, facecolor="#8a6c43", edgecolor=C_STONE, linewidth=0.5, zorder=4))
        ax.plot([bx, bx], [y0 + 0.17, y0 + 0.33], color=C_STONE, lw=0.5, zorder=4)

    # acropolis/templo
    hill = Ellipse((x0 + 3.35, y0 + 2.7), 1.15, 0.62, facecolor=C_EARTH, edgecolor="#b8a17d", linewidth=0.8, zorder=3)
    ax.add_patch(hill)
    ax.add_patch(Rectangle((x0 + 3.0, y0 + 2.78), 0.6, 0.18, facecolor="#f2ead9", edgecolor=C_STONE, linewidth=0.7, zorder=5))
    ax.add_patch(Polygon([(x0 + 2.94, y0 + 2.96), (x0 + 3.3, y0 + 3.1), (x0 + 3.66, y0 + 2.96)], closed=True, facecolor=C_ROOF, edgecolor=C_STONE, linewidth=0.6, zorder=5))

    # agora
    agora = Ellipse((x0 + 2.78, y0 + 1.95), 1.35, 0.78, facecolor="#efe4cf", edgecolor="#bda47e", linewidth=0.9, zorder=3)
    ax.add_patch(agora)

    # teatro
    for radius in [0.55, 0.42, 0.29]:
        ax.add_patch(Arc((x0 + 4.4, y0 + 2.1), radius, radius * 0.82, angle=25, theta1=205, theta2=350, color=C_STONE, lw=0.9, zorder=4))

    # viviendas
    houses = [
        (1.45, 1.5), (1.8, 1.85), (2.12, 2.3), (2.34, 2.62), (2.68, 2.45),
        (3.92, 2.24), (4.22, 1.86), (4.4, 1.48), (3.96, 1.28), (2.02, 1.22),
        (3.4, 1.55), (1.58, 2.35), (4.62, 2.42), (3.18, 1.2),
    ]
    for hx, hy in houses:
        draw_house(ax, x0 + hx, y0 + hy, w=0.24, h=0.15)

    # olivos afuera
    for ox in [x0 + 4.35, x0 + 4.7, x0 + 5.02]:
        for oy in [y0 + 0.95, y0 + 1.22]:
            ax.add_patch(Circle((ox, oy), 0.08, facecolor=C_GREEN, edgecolor="#355843", linewidth=0.3, zorder=2.5))
            ax.plot([ox, ox], [oy - 0.08, oy - 0.16], color=C_STONE, lw=0.4, zorder=2.4)

    # marcadores
    marker_color = C_GREEN
    add_marker(ax, x0 + 3.3, y0 + 3.05, 1, marker_color)
    add_marker(ax, x0 + 2.78, y0 + 1.95, 2, marker_color)
    add_marker(ax, x0 + 4.55, y0 + 2.18, 3, marker_color)
    add_marker(ax, x0 + 1.1, y0 + 1.35, 4, marker_color)
    add_marker(ax, x0 + 4.86, y0 + 1.08, 5, marker_color)
    add_marker(ax, x0 + 2.75, y0 + 0.46, 6, marker_color)

    # flujo y leyenda
    draw_flow(ax, (gate[0] - 0.3, gate[1] - 0.22), (gate[0] + 0.3, gate[1] - 0.22), color=C_GREEN)
    add_legend_row(
        ax,
        x0 + 1.2,
        y0 - 0.64,
        [(1, "templo"), (2, "ágora"), (3, "teatro"), (4, "muralla"), (5, "olivares"), (6, "puerto")],
        marker_color,
        "#ccb489",
    )
    rounded_box(ax, x0 + 1.32, y0 - 1.18, 5.25, 0.52, C_LABEL, "#ccb489", lw=1.0, radius=0.06, zorder=2)
    add_text(ax, x0 + 3.95, y0 - 0.92, "Polis: muralla adaptada al relieve y apertura concentrada en la puerta del puerto.", size=8.7, color=C_MID)


def draw_roman_panel(ax, x0, y0, w, h):
    rounded_box(ax, x0, y0, w, h, "#f8f5ee", "#d9c9b1", lw=1.6, radius=0.06, zorder=1)
    add_bar(ax, x0, y0 + h + 0.08, w, 0.58, C_RED, "CIUDAD ROMANA")

    terrain = Polygon(
        [
            (x0 + 0.55, y0 + 0.95),
            (x0 + 1.35, y0 + 3.2),
            (x0 + 5.78, y0 + 3.25),
            (x0 + 6.15, y0 + 1.2),
            (x0 + 4.8, y0 + 0.55),
            (x0 + 1.4, y0 + 0.55),
        ],
        closed=True,
        facecolor=C_GRASS,
        edgecolor="#bac596",
        linewidth=1.0,
        zorder=2,
    )
    ax.add_patch(terrain)

    wall_pts = [
        (x0 + 1.08, y0 + 1.08),
        (x0 + 1.58, y0 + 2.86),
        (x0 + 5.48, y0 + 2.88),
        (x0 + 5.82, y0 + 1.26),
        (x0 + 4.62, y0 + 0.88),
        (x0 + 1.55, y0 + 0.84),
    ]
    ax.add_patch(Polygon(wall_pts, closed=True, fill=False, edgecolor=C_WALL, linewidth=2.3, zorder=5))
    for tx, ty in wall_pts:
        draw_tower(ax, tx, ty)

    gate = (x0 + 3.6, y0 + 0.84)
    draw_gate(ax, gate[0], gate[1], "h")

    # grid
    for gx in [1.8, 2.4, 3.0, 3.6, 4.2, 4.8]:
        ax.plot([x0 + gx, x0 + gx], [y0 + 1.0, y0 + 2.78], color="#d4c2a8", lw=0.7, zorder=2.8)
    for gy in [1.25, 1.6, 1.95, 2.3, 2.65]:
        ax.plot([x0 + 1.45, x0 + 5.45], [y0 + gy, y0 + gy], color="#d4c2a8", lw=0.7, zorder=2.8)

    # insulae
    blocks = [
        (1.72, 1.1), (2.32, 1.1), (4.1, 1.1), (4.72, 1.1),
        (1.72, 1.45), (2.32, 1.45), (4.1, 1.45), (4.72, 1.45),
        (1.72, 2.15), (2.32, 2.15), (4.1, 2.15), (4.72, 2.15),
        (1.72, 2.5), (2.32, 2.5), (4.1, 2.5), (4.72, 2.5),
    ]
    for bx, by in blocks:
        ax.add_patch(Rectangle((x0 + bx, y0 + by), 0.46, 0.22, facecolor="#f2ead9", edgecolor=C_STONE, linewidth=0.45, zorder=3))
        ax.add_patch(Rectangle((x0 + bx, y0 + by + 0.22), 0.46, 0.05, facecolor=C_ROOF, edgecolor=C_STONE, linewidth=0.3, zorder=3.2))

    # forum
    forum = Rectangle((x0 + 2.85, y0 + 1.72), 1.15, 0.85, facecolor="#efe4cf", edgecolor="#bda47e", linewidth=0.9, zorder=3.8)
    ax.add_patch(forum)
    ax.add_patch(Rectangle((x0 + 3.05, y0 + 2.45), 0.75, 0.12, facecolor=C_ROOF, edgecolor=C_STONE, linewidth=0.4, zorder=4.2))
    # temple
    ax.add_patch(Rectangle((x0 + 4.3, y0 + 2.42), 0.62, 0.2, facecolor="#f2ead9", edgecolor=C_STONE, linewidth=0.6, zorder=4))
    ax.add_patch(Polygon([(x0 + 4.24, y0 + 2.62), (x0 + 4.61, y0 + 2.78), (x0 + 4.98, y0 + 2.62)], closed=True, facecolor=C_ROOF, edgecolor=C_STONE, linewidth=0.4, zorder=4.1))
    # baths
    ax.add_patch(Rectangle((x0 + 4.1, y0 + 1.72), 0.7, 0.48, facecolor="#ead7c0", edgecolor=C_STONE, linewidth=0.5, zorder=4))
    ax.add_patch(Ellipse((x0 + 4.45, y0 + 1.95), 0.22, 0.14, facecolor=C_WATER, edgecolor="#8fb8c0", linewidth=0.4, zorder=4.2))
    # amphitheatre
    ax.add_patch(Ellipse((x0 + 1.55, y0 + 0.45), 0.9, 0.42, facecolor="#ead7c0", edgecolor=C_STONE, linewidth=0.7, zorder=3))
    ax.add_patch(Ellipse((x0 + 1.55, y0 + 0.45), 0.52, 0.2, facecolor=C_BG, edgecolor=C_STONE, linewidth=0.5, zorder=3.2))
    # aqueduct
    for i in range(6):
        arc_x = x0 + 0.7 + i * 0.18
        ax.add_patch(Arc((arc_x, y0 + 2.95), 0.22, 0.26, theta1=0, theta2=180, color=C_RED, lw=1.0, zorder=4))
        ax.plot([arc_x - 0.11, arc_x - 0.11], [y0 + 2.95, y0 + 2.82], color=C_RED, lw=1.0, zorder=4)
        ax.plot([arc_x + 0.11, arc_x + 0.11], [y0 + 2.95, y0 + 2.82], color=C_RED, lw=1.0, zorder=4)

    # main axes
    ax.plot([x0 + 3.6, x0 + 3.6], [y0 + 1.0, y0 + 2.78], color=C_RED, lw=1.4, zorder=4)
    ax.plot([x0 + 1.45, x0 + 5.45], [y0 + 1.95, y0 + 1.95], color=C_RED, lw=1.4, zorder=4)

    marker_color = C_RED
    add_marker(ax, x0 + 1.12, y0 + 2.95, 1, marker_color)
    add_marker(ax, x0 + 3.45, y0 + 2.05, 2, marker_color)
    add_marker(ax, x0 + 4.45, y0 + 1.95, 3, marker_color)
    add_marker(ax, x0 + 1.55, y0 + 0.45, 4, marker_color)
    add_marker(ax, x0 + 4.62, y0 + 2.74, 5, marker_color)
    add_marker(ax, x0 + 5.35, y0 + 2.1, 6, marker_color)

    draw_flow(ax, (gate[0] - 0.28, gate[1] - 0.22), (gate[0] + 0.28, gate[1] - 0.22), color=C_GREEN)
    add_legend_row(
        ax,
        x0 + 1.05,
        y0 - 0.64,
        [(1, "acueducto"), (2, "foro"), (3, "termas"), (4, "anfiteatro"), (5, "templo"), (6, "muralla")],
        marker_color,
        "#c9a79e",
    )
    rounded_box(ax, x0 + 1.18, y0 - 1.18, 5.3, 0.52, C_LABEL, "#c9a79e", lw=1.0, radius=0.06, zorder=2)
    add_text(ax, x0 + 3.83, y0 - 0.92, "Urbs: muralla regular, ejes ortogonales y acceso controlado dentro de una forma repetible.", size=8.7, color=C_MID)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(20, 11), dpi=DPI)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    add_text(ax, 0.0, 5.23, "Ciudades amuralladas: Grecia y Roma", size=24, weight="bold")

    draw_greek_panel(ax, -9.2, 0.7, 8.3, 3.9)
    draw_roman_panel(ax, 0.9, 0.7, 8.3, 3.9)

    rounded_box(ax, -9.2, -0.68, 18.4, 0.62, C_WHITE, C_STONE, lw=1.1, radius=0.08, zorder=1)
    add_text(
        ax,
        0.0,
        -0.37,
        "Idea comun: la muralla no es un cierre absoluto; concentra seguridad y administra por donde entran y salen personas, bienes y recursos.",
        size=9.7,
        color=C_MID,
    )

    ax.set_xlim(-10.1, 10.1)
    ax.set_ylim(-1.05, 5.6)
    ax.axis("off")

    plt.tight_layout(pad=0.5)
    fig.savefig(OUT, dpi=DPI, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"✓ Comparativa generada: {OUT}  ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
