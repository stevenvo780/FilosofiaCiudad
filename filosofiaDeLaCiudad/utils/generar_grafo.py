#!/usr/bin/env python3
"""
Genera un grafo comparativo 2D de alta calidad entre ciudades griegas y romanas.
Usa matplotlib + networkx con layout manual, tipografía cuidada y paleta cromática
diferenciada para cada civilización.

Salida: ../Clase 1/apoyosGraficosCreados/comparacion_ciudades_griegas_romanas.png
"""

import pathlib
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Ellipse, Polygon
import networkx as nx
import numpy as np

# ─── Constantes ────────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "Clase 1" / "apoyosGraficosCreados" / "comparacion_ciudades_griegas_romanas.png"
DPI = 300

# Paleta
C_BG       = "#f5f0e8"
C_PANEL_G  = "#e8f4f1"
C_PANEL_R  = "#fce8e2"
C_GREEN    = "#1a7a6d"
C_GREEN_L  = "#74c9b9"
C_RED      = "#a63c28"
C_RED_L    = "#e8a090"
C_GOLD     = "#c9a84c"
C_STONE    = "#8a7e6f"
C_DARK     = "#1f2937"
C_MID      = "#4b5563"
C_LIGHT    = "#9ca3af"
C_WHITE    = "#ffffff"
C_WALL     = "#7b6d60"
C_ROAD     = "#75675b"
C_WATER    = "#b8d9e8"
C_HILL     = "#d9cfba"

# ─── Helpers ───────────────────────────────────────────────────────────────────

def _rounded_rect(ax, xy, w, h, color, ec, lw=1.8, alpha=0.92, zorder=2, radius=0.18):
    """Dibuja un rectángulo con esquinas redondeadas."""
    box = FancyBboxPatch(xy, w, h,
                         boxstyle=f"round,pad=0,rounding_size={radius}",
                         facecolor=color, edgecolor=ec, linewidth=lw,
                         alpha=alpha, zorder=zorder,
                         transform=ax.transData)
    ax.add_patch(box)
    return box


def _node_style(civ: str):
    """Devuelve estilo según civilización."""
    if civ == "greek":
        return dict(node_color=C_GREEN_L, edgecolors=C_GREEN, linewidths=2.5)
    elif civ == "roman":
        return dict(node_color=C_RED_L, edgecolors=C_RED, linewidths=2.5)
    else:
        return dict(node_color=C_GOLD, edgecolors=C_STONE, linewidths=2.0)


def draw_greek_territory(ax, offset_x):
    """Dibuja la implantación territorial de una polis griega."""
    coastline = np.array([
        [offset_x - 3.6, -0.4],
        [offset_x - 3.1,  0.8],
        [offset_x - 2.8,  2.0],
        [offset_x - 2.3,  3.2],
        [offset_x - 1.5,  4.2],
        [offset_x - 0.4,  4.8],
        [offset_x + 0.8,  4.5],
        [offset_x + 1.7,  3.6],
        [offset_x + 2.3,  2.1],
        [offset_x + 2.5,  0.5],
        [offset_x + 2.0, -1.4],
        [offset_x + 0.9, -1.7],
        [offset_x - 0.5, -1.7],
        [offset_x - 1.7, -1.5],
        [offset_x - 2.7, -1.1],
    ])
    ax.add_patch(Polygon(coastline, closed=True, facecolor=C_PANEL_G,
                         edgecolor=C_GREEN, linewidth=1.8, alpha=0.35, zorder=0.2))

    harbor = Ellipse((offset_x - 3.0, -0.7), 1.4, 0.8,
                     facecolor=C_WATER, edgecolor=C_GREEN, linewidth=1.3,
                     alpha=0.7, zorder=0.25)
    ax.add_patch(harbor)
    ax.text(offset_x - 3.0, -1.1, "Puerto / borde marítimo", fontsize=6.6,
            color=C_MID, ha="center", va="center", zorder=0.5, fontfamily="serif")

    hill = Polygon([
        (offset_x - 1.3, 3.6),
        (offset_x - 0.3, 4.9),
        (offset_x + 0.7, 4.0),
        (offset_x + 0.2, 3.1),
        (offset_x - 1.0, 3.1),
    ], closed=True, facecolor=C_HILL, edgecolor=C_STONE,
       linewidth=1.4, alpha=0.95, zorder=0.4)
    ax.add_patch(hill)
    ax.text(offset_x - 0.25, 4.25, "Colina sacra", fontsize=7.0,
            color=C_DARK, ha="center", va="center", zorder=0.6, fontfamily="serif")

    wall = np.array([
        [offset_x - 2.8, -1.0],
        [offset_x - 1.5,  0.2],
        [offset_x - 0.7,  1.2],
        [offset_x + 0.1,  2.2],
        [offset_x + 1.1,  3.1],
        [offset_x + 2.2,  3.7],
    ])
    ax.plot(wall[:, 0], wall[:, 1], color=C_WALL, lw=3.2,
            solid_capstyle="round", zorder=0.45)
    ax.text(offset_x + 1.6, 3.95, "Muralla adaptada al relieve", fontsize=6.3,
            color=C_MID, ha="center", va="bottom", zorder=0.6, fontfamily="serif")

    roads = [
        [(offset_x - 2.9, -0.1), (offset_x - 1.3, 0.7), (offset_x - 0.2, 1.8), (offset_x + 0.8, 3.2)],
        [(offset_x - 1.9, -1.2), (offset_x - 0.8, -0.1), (offset_x + 0.2, 1.0), (offset_x + 1.2, 2.2)],
        [(offset_x - 0.6, 3.0), (offset_x - 0.4, 3.6), (offset_x - 0.2, 4.2)],
    ]
    for road in roads:
        xs, ys = zip(*road)
        ax.plot(xs, ys, color=C_ROAD, lw=2.4, alpha=0.9,
                solid_capstyle="round", zorder=0.42)

    ax.text(offset_x - 0.8, -2.15,
            "Territorio: crecimiento irregular, adaptación topográfica\n"
            "y separación visible entre acrópolis y ágora.",
            fontsize=7.2, color=C_MID, ha="center", va="center",
            zorder=0.6, fontfamily="serif")


def draw_roman_territory(ax, offset_x):
    """Dibuja la implantación territorial de una ciudad romana."""
    ax.add_patch(Polygon([
        (offset_x - 2.8, -1.4),
        (offset_x + 2.8, -1.4),
        (offset_x + 2.8, 4.2),
        (offset_x - 2.8, 4.2),
    ], closed=True, facecolor=C_PANEL_R, edgecolor=C_RED,
       linewidth=1.8, alpha=0.33, zorder=0.2))

    for x in np.linspace(offset_x - 2.3, offset_x + 2.3, 5):
        ax.plot([x, x], [-1.1, 3.9], color=C_WALL, lw=2.6, alpha=0.8, zorder=0.32)
    for y in np.linspace(-0.7, 3.5, 5):
        ax.plot([offset_x - 2.3, offset_x + 2.3], [y, y], color=C_WALL, lw=2.6, alpha=0.8, zorder=0.32)

    ax.plot([offset_x, offset_x], [-1.25, 4.05], color=C_RED, lw=4.0, alpha=0.9, zorder=0.34)
    ax.plot([offset_x - 2.55, offset_x + 2.55], [1.4, 1.4], color=C_RED, lw=4.0, alpha=0.9, zorder=0.34)
    ax.text(offset_x, -1.55, "Cardo maximus", fontsize=6.8, color=C_MID,
            ha="center", va="center", zorder=0.6, fontfamily="serif")
    ax.text(offset_x + 2.9, 1.4, "Decumanus maximus", fontsize=6.8, color=C_MID,
            ha="left", va="center", zorder=0.6, fontfamily="serif")

    aqueduct_x = np.linspace(offset_x - 3.3, offset_x - 0.9, 100)
    aqueduct_y = 4.55 + 0.35 * np.sin(np.linspace(0, np.pi, 100))
    ax.plot(aqueduct_x, aqueduct_y, color=C_RED, lw=2.2, zorder=0.35)
    ax.text(offset_x - 2.1, 4.95, "Acueducto / abastecimiento", fontsize=6.6,
            color=C_MID, ha="center", va="center", zorder=0.6, fontfamily="serif")

    ax.text(offset_x, -2.15,
            "Territorio: retícula ortogonal, ejes jerárquicos\n"
            "y planificación repetible a escala imperial.",
            fontsize=7.2, color=C_MID, ha="center", va="center",
            zorder=0.6, fontfamily="serif")


# ─── Definición de grafos ─────────────────────────────────────────────────────

def build_greek_graph():
    """Grafo de la polis griega."""
    G = nx.DiGraph()

    nodes = {
        "Polis\n(ciudad-estado)":   {"pos": (0.0,  4.5), "size": 2800, "civ": "greek"},
        "Acrópolis\nAltura sagrada\ny defensiva":       {"pos": (-1.0, 3.0), "size": 2200, "civ": "greek"},
        "Ágora\nMercado, debate\ny vida cívica":        {"pos": (1.0,  3.0), "size": 2200, "civ": "greek"},
        "Teatro\nCultual, sobre\npendiente natural":    {"pos": (-2.2, 1.5), "size": 1500, "civ": "shared"},
        "Templos\nReligión cívica\npoliteísta":         {"pos": (-0.5, 1.3), "size": 1500, "civ": "shared"},
        "Stoa\nPórtico comercial\ny filosófico":        {"pos": (2.2,  1.5), "size": 1500, "civ": "shared"},
        "Trazado\nOrgánico\nadaptado al relieve":       {"pos": (-1.8, 0.0), "size": 1300, "civ": "greek"},
        "Democracia\ndirecta /\nAsamblea (Ekklesia)":  {"pos": (0.5,  0.0), "size": 1300, "civ": "greek"},
        "Gimnasio\nEducación del\ncuerpo y la mente":   {"pos": (2.2,  0.0), "size": 1300, "civ": "shared"},
        "Murallas\nDefensa colectiva\nde la polis":      {"pos": (-0.7,-1.2), "size": 1200, "civ": "shared"},
        "Autonomía\npolítica local":                     {"pos": (1.5, -1.2), "size": 1200, "civ": "greek"},
    }

    edges = [
        ("Polis\n(ciudad-estado)", "Acrópolis\nAltura sagrada\ny defensiva",     "contiene"),
        ("Polis\n(ciudad-estado)", "Ágora\nMercado, debate\ny vida cívica",      "contiene"),
        ("Acrópolis\nAltura sagrada\ny defensiva", "Templos\nReligión cívica\npoliteísta", "alberga"),
        ("Ágora\nMercado, debate\ny vida cívica", "Stoa\nPórtico comercial\ny filosófico", "rodea"),
        ("Ágora\nMercado, debate\ny vida cívica", "Democracia\ndirecta /\nAsamblea (Ekklesia)", "facilita"),
        ("Polis\n(ciudad-estado)", "Teatro\nCultual, sobre\npendiente natural",   "integra"),
        ("Polis\n(ciudad-estado)", "Trazado\nOrgánico\nadaptado al relieve",     "presenta"),
        ("Polis\n(ciudad-estado)", "Gimnasio\nEducación del\ncuerpo y la mente",  "incluye"),
        ("Trazado\nOrgánico\nadaptado al relieve", "Murallas\nDefensa colectiva\nde la polis", "delimita"),
        ("Democracia\ndirecta /\nAsamblea (Ekklesia)", "Autonomía\npolítica local", "produce"),
    ]

    for name, attr in nodes.items():
        G.add_node(name, **attr)
    for u, v, lab in edges:
        G.add_edge(u, v, label=lab)
    return G


def build_roman_graph():
    """Grafo de la ciudad romana."""
    G = nx.DiGraph()

    nodes = {
        "Urbs\n(ciudad imperial)":  {"pos": (0.0,  4.5), "size": 2800, "civ": "roman"},
        "Foro\nCentro político,\njudicial y comercial": {"pos": (-1.0, 3.0), "size": 2200, "civ": "roman"},
        "Basílica\nJusticia y\nadministración":          {"pos": (1.0,  3.0), "size": 2200, "civ": "roman"},
        "Anfiteatro\nEspectáculo\nmasivo (ludi)":        {"pos": (-2.2, 1.5), "size": 1500, "civ": "shared"},
        "Templos\nReligión oficial\ny culto imperial":    {"pos": (-0.5, 1.3), "size": 1500, "civ": "shared"},
        "Termas\nHigiene, ocio\ny socialización":         {"pos": (2.2,  1.5), "size": 1500, "civ": "shared"},
        "Retícula\nCardo / Decumanus\nplanificación":     {"pos": (-1.8, 0.0), "size": 1300, "civ": "roman"},
        "Derecho\nromano y\nadministración":              {"pos": (0.5,  0.0), "size": 1300, "civ": "roman"},
        "Acueducto\nIngeniería\nhidráulica":              {"pos": (2.2,  0.0), "size": 1300, "civ": "shared"},
        "Calzadas\nConexión\ninter-urbana":               {"pos": (-0.7,-1.2), "size": 1200, "civ": "shared"},
        "Poder\nimperial\ncentralizado":                  {"pos": (1.5, -1.2), "size": 1200, "civ": "roman"},
    }

    edges = [
        ("Urbs\n(ciudad imperial)", "Foro\nCentro político,\njudicial y comercial", "contiene"),
        ("Urbs\n(ciudad imperial)", "Basílica\nJusticia y\nadministración",          "contiene"),
        ("Foro\nCentro político,\njudicial y comercial", "Templos\nReligión oficial\ny culto imperial", "alberga"),
        ("Foro\nCentro político,\njudicial y comercial", "Derecho\nromano y\nadministración", "administra"),
        ("Basílica\nJusticia y\nadministración", "Derecho\nromano y\nadministración", "ejecuta"),
        ("Urbs\n(ciudad imperial)", "Anfiteatro\nEspectáculo\nmasivo (ludi)",        "integra"),
        ("Urbs\n(ciudad imperial)", "Retícula\nCardo / Decumanus\nplanificación",    "presenta"),
        ("Urbs\n(ciudad imperial)", "Termas\nHigiene, ocio\ny socialización",        "incluye"),
        ("Retícula\nCardo / Decumanus\nplanificación", "Calzadas\nConexión\ninter-urbana", "extiende"),
        ("Urbs\n(ciudad imperial)", "Acueducto\nIngeniería\nhidráulica",             "construye"),
        ("Derecho\nromano y\nadministración", "Poder\nimperial\ncentralizado",       "sostiene"),
    ]

    for name, attr in nodes.items():
        G.add_node(name, **attr)
    for u, v, lab in edges:
        G.add_edge(u, v, label=lab)
    return G


# ─── Dibujo ───────────────────────────────────────────────────────────────────

def draw_subgraph(ax, G, title, title_color, panel_color, offset_x, territory_drawer=None):
    """Dibuja un subgrafo en un eje dado."""
    pos   = {n: (d["pos"][0] + offset_x, d["pos"][1]) for n, d in G.nodes(data=True)}
    sizes = [d["size"] for _, d in G.nodes(data=True)]
    civs  = [d["civ"]  for _, d in G.nodes(data=True)]

    node_colors = []
    edge_colors_list = []
    for c in civs:
        s = _node_style(c)
        node_colors.append(s["node_color"])
        edge_colors_list.append(s["edgecolors"])

    # Fondo del panel
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    pad = 1.2
    _rounded_rect(ax,
                  (min(xs) - pad, min(ys) - pad),
                  max(xs) - min(xs) + 2 * pad,
                  max(ys) - min(ys) + 2 * pad,
                  panel_color, title_color, lw=2.5, alpha=0.30,
                  zorder=0, radius=0.5)

    if territory_drawer is not None:
        territory_drawer(ax, offset_x)

    # Título del panel
    ax.text(offset_x, max(ys) + 1.6, title,
            fontsize=18, fontweight="bold", color=title_color,
            ha="center", va="center", zorder=10,
            fontfamily="serif")

    # Aristas
    for u, v, data in G.edges(data=True):
        ax.annotate("",
                     xy=pos[v], xytext=pos[u],
                     arrowprops=dict(
                         arrowstyle="-|>",
                         color=C_STONE,
                         lw=1.6,
                         connectionstyle="arc3,rad=0.12",
                         shrinkA=22, shrinkB=22,
                     ),
                     zorder=1)
        # Etiqueta de arista
        mx = (pos[u][0] + pos[v][0]) / 2
        my = (pos[u][1] + pos[v][1]) / 2
        ax.text(mx, my, data["label"],
                fontsize=6.5, color=C_MID, ha="center", va="center",
                fontstyle="italic", zorder=5,
                bbox=dict(boxstyle="round,pad=0.15", fc=C_BG, ec="none", alpha=0.85))

    # Nodos
    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_size=sizes,
                           node_color=node_colors,
                           edgecolors=edge_colors_list,
                           linewidths=2.5,
                           alpha=0.92,
                           node_shape="o",
                           )

    # Etiquetas de nodo
    for node, (x, y) in pos.items():
        lines = node.split("\n")
        main_label = lines[0]
        sub_label = "\n".join(lines[1:]) if len(lines) > 1 else ""
        ax.text(x, y + 0.12, main_label,
                fontsize=8.5, fontweight="bold", color=C_DARK,
                ha="center", va="center", zorder=10,
                fontfamily="serif")
        if sub_label:
            ax.text(x, y - 0.22, sub_label,
                    fontsize=6.2, color=C_MID,
                    ha="center", va="center", zorder=10,
                    fontfamily="serif", linespacing=1.1)


def draw_center_comparison(ax):
    """Dibuja las flechas y etiquetas de comparación central."""
    comparisons = [
        (3.0,  "Ágora ↔ Foro",              "Centro cívico orgánico vs. planificado"),
        (1.5,  "Teatro ↔ Anfiteatro",        "Pendiente natural vs. estructura masiva"),
        (0.0,  "Trazado orgánico ↔ Retícula","Adaptar al terreno vs. imponer geometría"),
        (-1.2, "Autonomía ↔ Poder imperial", "Democracia local vs. administración central"),
    ]
    for y, title, desc in comparisons:
        ax.annotate("", xy=(0.8, y), xytext=(-0.8, y),
                     arrowprops=dict(arrowstyle="<->", color=C_GOLD, lw=2.2),
                     zorder=6)
        ax.text(0.0, y + 0.22, title,
                fontsize=7.5, fontweight="bold", color=C_DARK,
                ha="center", va="center", zorder=10,
                fontfamily="serif",
                bbox=dict(boxstyle="round,pad=0.2", fc=C_WHITE, ec=C_GOLD, lw=1.2, alpha=0.95))
        ax.text(0.0, y - 0.18, desc,
                fontsize=6, color=C_MID, ha="center", va="center",
                zorder=10, fontstyle="italic", fontfamily="serif")


def build_legend(ax):
    """Leyenda profesional en la parte inferior."""
    handles = [
        mpatches.Patch(facecolor=C_GREEN_L, edgecolor=C_GREEN, linewidth=2,
                       label="Elementos de la polis griega"),
        mpatches.Patch(facecolor=C_RED_L, edgecolor=C_RED, linewidth=2,
                       label="Elementos de la ciudad romana"),
        mpatches.Patch(facecolor=C_GOLD, edgecolor=C_STONE, linewidth=2,
                       label="Elementos compartidos / paralelos"),
        mpatches.FancyArrow(0, 0, 0.1, 0, width=0.02, color=C_STONE,
                            label="Relación estructural (contiene, facilita…)"),
        mpatches.FancyArrow(0, 0, 0.1, 0, width=0.02, color=C_GOLD,
                            label="Eje de comparación entre civilizaciones"),
        mpatches.Patch(facecolor=C_PANEL_G, edgecolor=C_WALL, linewidth=1.5,
                   label="Capa territorial / implantación urbana"),
    ]
    legend = ax.legend(handles=handles,
                       loc="lower center", ncol=3,
                       fontsize=6.6, frameon=True,
                       fancybox=True, shadow=False,
                       edgecolor=C_STONE,
                       facecolor=C_BG,
                       bbox_to_anchor=(0.5, 0.01))
    legend.get_frame().set_linewidth(1.5)


def draw_glossary(ax):
    """Añade un glosario breve y legible dentro de la lámina."""
    panel_x, panel_y = -7.7, -4.35
    panel_w, panel_h = 15.4, 1.45
    _rounded_rect(ax, (panel_x, panel_y), panel_w, panel_h,
                  C_WHITE, C_STONE, lw=1.6, alpha=0.96, zorder=0.8, radius=0.18)

    ax.text(panel_x + 0.35, panel_y + 1.08, "Glosario básico", fontsize=11,
            fontweight="bold", color=C_DARK, ha="left", va="center",
            zorder=1.2, fontfamily="serif")

    glossary_columns = [
        [
            ("Polis", "ciudad-estado griega con autonomía política."),
            ("Acrópolis", "zona elevada con función sagrada y defensiva."),
            ("Ágora", "plaza cívica y comercial de la ciudad griega."),
        ],
        [
            ("Stoa", "pórtico que rodea el ágora; comercio y filosofía."),
            ("Urbs", "ciudad romana entendida como centro urbano imperial."),
            ("Foro", "núcleo político, judicial y comercial romano."),
        ],
        [
            ("Cardo", "eje principal norte-sur en la retícula romana."),
            ("Decumanus", "eje principal este-oeste en la retícula romana."),
            ("Termas", "complejos públicos de baño, ocio e higiene."),
        ],
        [
            ("Anfiteatro", "edificio de espectáculos masivos romanos."),
            ("Teatro", "espacio escénico griego apoyado en la topografía."),
            ("Acueducto", "infraestructura de conducción de agua."),
        ],
    ]

    start_x = panel_x + 0.35
    col_gap = 3.8
    for index, column in enumerate(glossary_columns):
        col_x = start_x + index * col_gap
        base_y = panel_y + 0.78
        for row, (term, definition) in enumerate(column):
            y = base_y - row * 0.34
            ax.text(col_x, y, f"{term}:", fontsize=7.1, fontweight="bold",
                    color=C_DARK, ha="left", va="center", zorder=1.2,
                    fontfamily="serif")
            ax.text(col_x + 0.9, y, definition, fontsize=6.5,
                    color=C_MID, ha="left", va="center", zorder=1.2,
                    fontfamily="serif")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    G_greek = build_greek_graph()
    G_roman = build_roman_graph()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(25, 15), dpi=DPI)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    # Subgrafos
    draw_subgraph(ax, G_greek, "POLIS  GRIEGA", C_GREEN, C_PANEL_G, offset_x=-5.0,
                  territory_drawer=draw_greek_territory)
    draw_subgraph(ax, G_roman, "CIUDAD  ROMANA", C_RED, C_PANEL_R, offset_x=5.0,
                  territory_drawer=draw_roman_territory)

    # Comparación central
    draw_center_comparison(ax)

    # Título
    ax.text(0.0, 6.6,
            "Ciudades griegas vs. ciudades romanas",
            fontsize=24, fontweight="bold", color=C_DARK,
            ha="center", va="center", fontfamily="serif")
    ax.text(0.0, 6.1,
            "Grafo territorial y comparativo de organización urbana, política e infraestructura",
            fontsize=12, color=C_MID, ha="center", va="center",
            fontfamily="serif", fontstyle="italic")

    draw_glossary(ax)

    # Leyenda
    build_legend(ax)

    # Limpiar ejes
    ax.set_xlim(-8.5, 8.5)
    ax.set_ylim(-4.7, 7.2)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout(pad=0.5)
    fig.savefig(OUT, dpi=DPI, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"✓ Grafo generado: {OUT}  ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
