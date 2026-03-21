#!/usr/bin/env python3
"""
Genera un mapa mental comparativo centrado en la dimension fisica y la
escalabilidad de la polis griega y la ciudad romana.

Se deja fuera la capa metafisica o teleologica para concentrarse en:
- forma urbana;
- infraestructura;
- logica de crecimiento;
- capacidad de replicacion territorial.

Salida: ../Clase 1/apoyosGraficosCreados/mapa_mental_fisico_escalabilidad.png
"""

import pathlib

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "Clase 1" / "apoyosGraficosCreados" / "mapa_mental_fisico_escalabilidad.png"
DPI = 300

# Paleta base alineada con el grafo comparativo existente.
C_BG = "#f5f0e8"
C_WHITE = "#fffdf8"
C_DARK = "#1f2937"
C_MID = "#4b5563"
C_STONE = "#8a7e6f"
C_GOLD = "#c9a84c"
C_GOLD_SOFT = "#efe2bb"
C_GREEN = "#1a7a6d"
C_GREEN_L = "#d9f0eb"
C_RED = "#a63c28"
C_RED_L = "#f7ddd5"


def rounded_box(ax, x, y, w, h, facecolor, edgecolor, lw=2.0, alpha=0.96, radius=0.22):
    """Dibuja un rectangulo redondeado."""
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        linewidth=lw,
        edgecolor=edgecolor,
        facecolor=facecolor,
        alpha=alpha,
        zorder=1,
    )
    ax.add_patch(patch)
    return patch


def add_card(
    ax,
    center,
    size,
    title,
    body,
    facecolor,
    edgecolor,
    title_color=C_DARK,
    body_color=C_MID,
    title_size=13.5,
    body_size=10.0,
    radius=0.22,
):
    """Dibuja una tarjeta con titulo y cuerpo."""
    cx, cy = center
    w, h = size
    x = cx - w / 2
    y = cy - h / 2
    rounded_box(ax, x, y, w, h, facecolor, edgecolor, radius=radius)

    if body:
        ax.text(
            cx,
            y + h - 0.34,
            title,
            ha="center",
            va="top",
            fontsize=title_size,
            fontweight="bold",
            color=title_color,
            fontfamily="serif",
            zorder=3,
        )
        ax.text(
            cx,
            y + h / 2 - 0.15,
            body,
            ha="center",
            va="center",
            fontsize=body_size,
            color=body_color,
            fontfamily="serif",
            linespacing=1.35,
            zorder=3,
        )
    else:
        ax.text(
            cx,
            cy,
            title,
            ha="center",
            va="center",
            fontsize=title_size,
            fontweight="bold",
            color=title_color,
            fontfamily="serif",
            zorder=3,
        )


def connect(ax, start, end, color, rad=0.0, lw=2.2):
    """Traza una conexion curva entre dos nodos."""
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(
            arrowstyle="-|>",
            lw=lw,
            color=color,
            shrinkA=18,
            shrinkB=18,
            connectionstyle=f"arc3,rad={rad}",
        ),
        zorder=2,
    )


def draw_panel(ax, x, y, w, h, facecolor, edgecolor):
    """Dibuja un fondo suave para cada familia de nodos."""
    rounded_box(ax, x, y, w, h, facecolor, edgecolor, lw=2.4, alpha=0.28, radius=0.38)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(19, 10.8), dpi=DPI)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    # Fondos de paneles.
    draw_panel(ax, -10.2, -3.6, 8.4, 6.6, C_GREEN_L, C_GREEN)
    draw_panel(ax, 1.8, -3.6, 8.4, 6.6, C_RED_L, C_RED)

    # Encabezado.
    rounded_box(ax, -10.1, 3.62, 4.55, 0.5, C_GOLD, C_GOLD, lw=0, alpha=1.0, radius=0.12)
    ax.text(
        -7.82,
        3.87,
        "MAPA MENTAL · CLASE 1",
        ha="center",
        va="center",
        fontsize=10.5,
        fontweight="bold",
        color=C_WHITE,
        fontfamily="sans-serif",
        zorder=4,
    )
    ax.text(
        0,
        3.25,
        "Ciudad griega vs ciudad romana",
        ha="center",
        va="center",
        fontsize=28,
        fontweight="bold",
        color=C_DARK,
        fontfamily="serif",
    )
    ax.text(
        0,
        2.72,
        "Mapa mental comparativo de dimensión física y escalabilidad",
        ha="center",
        va="center",
        fontsize=12.5,
        color=C_MID,
        fontfamily="serif",
        fontstyle="italic",
    )

    # Nodo central.
    add_card(
        ax,
        center=(0.0, 0.95),
        size=(4.2, 1.45),
        title="Ciudad antigua\nComparación material",
        body="Forma urbana\nInfraestructura\nEscala y replicación",
        facecolor=C_GOLD_SOFT,
        edgecolor=C_GOLD,
        title_size=15.5,
        body_size=9.4,
        radius=0.28,
    )

    # Ramas principales.
    add_card(
        ax,
        center=(-4.55, 1.92),
        size=(3.25, 0.92),
        title="Polis griega",
        body="",
        facecolor=C_GREEN_L,
        edgecolor=C_GREEN,
        title_size=16,
        radius=0.24,
    )
    add_card(
        ax,
        center=(4.55, 1.92),
        size=(3.45, 0.92),
        title="Urbs romana",
        body="",
        facecolor=C_RED_L,
        edgecolor=C_RED,
        title_size=16,
        radius=0.24,
    )

    # Subramas griegas.
    add_card(
        ax,
        center=(-6.15, 0.35),
        size=(4.9, 2.15),
        title="Parte física",
        body=(
            "• trazado orgánico adaptado al relieve\n"
            "• muralla, puerto y pendientes como forma\n"
            "• separación visible entre acrópolis y ágora\n"
            "• tejido compacto y escala caminable"
        ),
        facecolor=C_WHITE,
        edgecolor=C_GREEN,
    )
    add_card(
        ax,
        center=(-6.15, -2.0),
        size=(4.9, 2.15),
        title="Escalabilidad",
        body=(
            "• crecimiento acotado por topografía y borde\n"
            "• comunidad de dimensión reconocible\n"
            "• baja replicabilidad entre poleis\n"
            "• expansión local, no modelo imperial repetible"
        ),
        facecolor=C_WHITE,
        edgecolor=C_GREEN,
    )

    # Subramas romanas.
    add_card(
        ax,
        center=(6.15, 0.35),
        size=(5.1, 2.15),
        title="Parte física",
        body=(
            "• retícula ortogonal y parcelación regular\n"
            "• cardo y decumanus como ejes jerárquicos\n"
            "• foro, termas y basílica como núcleos fijos\n"
            "• acueductos y calzadas como soporte material"
        ),
        facecolor=C_WHITE,
        edgecolor=C_RED,
    )
    add_card(
        ax,
        center=(6.15, -2.0),
        size=(5.1, 2.15),
        title="Escalabilidad",
        body=(
            "• trazado repetible en colonias y campamentos\n"
            "• expansión sin perder la forma básica\n"
            "• red imperial conectada por infraestructuras\n"
            "• alta capacidad de administración y logística"
        ),
        facecolor=C_WHITE,
        edgecolor=C_RED,
    )

    # Conexiones centrales.
    connect(ax, (-2.08, 1.1), (-2.98, 1.68), C_GREEN, rad=0.08)
    connect(ax, (2.08, 1.1), (2.98, 1.68), C_RED, rad=-0.08)

    # Conexiones griegas.
    connect(ax, (-4.98, 1.46), (-5.85, 1.42), C_GREEN, rad=0.04)
    connect(ax, (-6.15, -0.72), (-6.15, -0.92), C_GREEN, rad=0.0)

    # Conexiones romanas.
    connect(ax, (4.98, 1.46), (5.9, 1.42), C_RED, rad=-0.04)
    connect(ax, (6.15, -0.72), (6.15, -0.92), C_RED, rad=0.0)

    # Banda de lectura comparativa.
    rounded_box(ax, -10.1, -4.42, 20.2, 0.9, C_WHITE, C_STONE, lw=1.6, alpha=0.95, radius=0.16)
    ax.text(
        -9.6,
        -3.97,
        "Lectura rápida:",
        ha="left",
        va="center",
        fontsize=11.5,
        fontweight="bold",
        color=C_DARK,
        fontfamily="serif",
    )
    ax.text(
        -5.9,
        -3.97,
        "Grecia adapta la forma al sitio",
        ha="center",
        va="center",
        fontsize=9.2,
        color=C_MID,
        fontfamily="serif",
    )
    ax.text(
        0.0,
        -3.97,
        "Roma estandariza la forma para repetirla",
        ha="center",
        va="center",
        fontsize=9.2,
        color=C_MID,
        fontfamily="serif",
    )
    ax.text(
        6.6,
        -3.97,
        "La diferencia clave está en la capacidad de escalar",
        ha="center",
        va="center",
        fontsize=9.2,
        color=C_MID,
        fontfamily="serif",
    )

    ax.set_xlim(-10.6, 10.6)
    ax.set_ylim(-4.65, 4.3)
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
    print(f"✓ Mapa mental generado: {OUT}  ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
