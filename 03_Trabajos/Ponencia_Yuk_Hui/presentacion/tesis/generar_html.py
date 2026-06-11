#!/usr/bin/env python3
"""
Genera index.html a partir de los .md de la tesis (00-11).
Produce una pagina unica con indice lateral fijo y tipografia de lectura.
"""

import os
import re
import glob
import markdown

TESIS_DIR = "/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui/tesis"
OUT_FILE = "/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui/presentacion/tesis/index.html"

# Etiquetas cortas para el indice lateral
CHAPTER_LABELS = {
    "00": "Portada e Indice",
    "01": "01. Introduccion",
    "02": "02. Epistemologia",
    "03": "03. Catalogo razonado",
    "04": "04. Metodologia",
    "05": "05. Resultados",
    "06": "06. Critica tecnica",
    "07": "07. Critica ontologica",
    "08": "08. Critica politico-economica",
    "09": "09. Banco Epistemico Urbano",
    "10": "10. Nota reflexiva",
    "11": "11. Conclusiones",
}


def slug(num: str) -> str:
    return f"cap-{num}"


def first_h1(text: str) -> str:
    """Extrae el primer titulo H1 del markdown."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def render_chapters():
    pattern = os.path.join(TESIS_DIR, "*.md")
    files = sorted(glob.glob(pattern))

    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])

    chapters = []
    for path in files:
        fname = os.path.basename(path)
        num = fname[:2]
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
        title = first_h1(raw)
        md.reset()
        body = md.convert(raw)
        # Prefijar los id de encabezados con el numero de capitulo para
        # garantizar unicidad en el documento unico (evita id="referencias"
        # repetido 12 veces). No afecta a la navegacion lateral, que usa
        # los anclajes #cap-NN de la <section>.
        body = re.sub(
            r'id="([^"]+)"',
            lambda m: f'id="cap-{num}-{m.group(1)}"',
            body,
        )
        chapters.append({"num": num, "title": title, "body": body})

    return chapters


def build_sidebar(chapters):
    items = []
    for ch in chapters:
        label = CHAPTER_LABELS.get(ch["num"], ch["num"])
        items.append(
            f'<li><a href="#{slug(ch["num"])}">{label}</a></li>'
        )
    return "\n        ".join(items)


def build_content(chapters):
    sections = []
    for ch in chapters:
        sections.append(
            f'<section id="{slug(ch["num"])}" class="chapter">\n{ch["body"]}\n</section>'
        )
    return "\n\n".join(sections)


def main():
    chapters = render_chapters()

    sidebar_items = build_sidebar(chapters)
    content_html = build_content(chapters)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>La herramienta sobredimensionada y la aplicacion faltante</title>
  <style>
    /* ── Variables ─────────────────────────────────── */
    :root {{
      --bg:        #fdf8f2;
      --surface:   #faf4ec;
      --border:    #e4d9c8;
      --text:      #2e2a24;
      --muted:     #6b5f50;
      --accent:    #b07d2b;
      --accent-dk: #8a5f1e;
      --link:      #7a5518;
      --link-hov:  #b07d2b;
      --sidebar-w: 260px;
      --body-max:  75ch;
    }}

    /* ── Reset ──────────────────────────────────────── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    /* ── Layout ─────────────────────────────────────── */
    body {{
      display: flex;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: "Georgia", "Times New Roman", serif;
      font-size: 1.05rem;
      line-height: 1.75;
    }}

    /* ── Sidebar ─────────────────────────────────────── */
    #sidebar {{
      position: fixed;
      top: 0; left: 0;
      width: var(--sidebar-w);
      height: 100vh;
      overflow-y: auto;
      background: var(--surface);
      border-right: 1px solid var(--border);
      padding: 1.5rem 1rem 2rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
      z-index: 100;
    }}

    #sidebar .back-btn {{
      display: block;
      text-align: center;
      padding: .45rem .8rem;
      border: 1.5px solid var(--accent);
      border-radius: 6px;
      color: var(--accent-dk);
      text-decoration: none;
      font-family: system-ui, sans-serif;
      font-size: .82rem;
      font-weight: 600;
      letter-spacing: .02em;
      transition: background .18s, color .18s;
    }}
    #sidebar .back-btn:hover {{
      background: var(--accent);
      color: #fff;
    }}

    #sidebar h2 {{
      font-family: system-ui, sans-serif;
      font-size: .72rem;
      font-weight: 700;
      letter-spacing: .12em;
      text-transform: uppercase;
      color: var(--muted);
    }}

    #sidebar nav ul {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: .15rem;
    }}

    #sidebar nav a {{
      display: block;
      padding: .35rem .5rem;
      border-radius: 5px;
      text-decoration: none;
      color: var(--link);
      font-family: system-ui, sans-serif;
      font-size: .8rem;
      line-height: 1.35;
      transition: background .14s, color .14s;
    }}
    #sidebar nav a:hover {{
      background: var(--border);
      color: var(--accent-dk);
    }}

    /* ── Main content ────────────────────────────────── */
    #main {{
      margin-left: var(--sidebar-w);
      padding: 3rem 2.5rem 5rem;
      flex: 1;
    }}

    .chapter {{
      max-width: var(--body-max);
      margin: 0 auto 4rem;
      padding-bottom: 2.5rem;
      border-bottom: 1px solid var(--border);
    }}
    .chapter:last-child {{
      border-bottom: none;
    }}

    /* ── Typography ──────────────────────────────────── */
    h1 {{
      font-size: 1.65rem;
      line-height: 1.25;
      color: var(--accent-dk);
      margin-bottom: 1rem;
      scroll-margin-top: 1.5rem;
    }}
    h2 {{
      font-size: 1.2rem;
      color: var(--accent-dk);
      margin-top: 2rem;
      margin-bottom: .6rem;
      border-left: 3px solid var(--accent);
      padding-left: .6rem;
    }}
    h3 {{
      font-size: 1.05rem;
      color: var(--muted);
      margin-top: 1.5rem;
      margin-bottom: .4rem;
    }}
    h4, h5 {{
      font-size: 1rem;
      color: var(--muted);
      margin-top: 1.2rem;
      margin-bottom: .35rem;
    }}

    p {{ margin-bottom: .85rem; }}

    a {{
      color: var(--link);
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    a:hover {{ color: var(--link-hov); }}

    /* ── Tables ──────────────────────────────────────── */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1.25rem 0;
      font-family: system-ui, sans-serif;
      font-size: .88rem;
    }}
    th {{
      background: var(--border);
      padding: .45rem .7rem;
      text-align: left;
      font-weight: 700;
      border-bottom: 2px solid var(--accent);
    }}
    td {{
      padding: .4rem .7rem;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    tr:nth-child(even) td {{ background: #f5ede0; }}

    /* ── Code ────────────────────────────────────────── */
    code {{
      font-family: "Fira Code", "Consolas", monospace;
      font-size: .85em;
      background: var(--border);
      padding: .1em .35em;
      border-radius: 3px;
    }}
    pre code {{
      display: block;
      padding: 1rem;
      overflow-x: auto;
      background: #f0e6d3;
      border-radius: 6px;
      line-height: 1.5;
    }}

    /* ── Blockquote ──────────────────────────────────── */
    blockquote {{
      border-left: 4px solid var(--accent);
      margin: 1.25rem 0;
      padding: .5rem 1rem;
      color: var(--muted);
      font-style: italic;
    }}

    /* ── Lists ───────────────────────────────────────── */
    ul, ol {{
      padding-left: 1.6rem;
      margin-bottom: .85rem;
    }}
    li {{ margin-bottom: .25rem; }}

    /* ── hr ──────────────────────────────────────────── */
    hr {{
      border: none;
      border-top: 1px solid var(--border);
      margin: 2rem 0;
    }}

    /* ── Scroll margin for anchor links ──────────────── */
    .chapter {{ scroll-margin-top: 1rem; }}

    /* ── Responsive ──────────────────────────────────── */
    @media (max-width: 768px) {{
      :root {{ --sidebar-w: 0px; }}
      #sidebar {{
        position: static;
        width: 100%;
        height: auto;
        border-right: none;
        border-bottom: 1px solid var(--border);
      }}
      #main {{ margin-left: 0; padding: 1.5rem 1rem 3rem; }}
    }}
  </style>
</head>
<body>

<aside id="sidebar">
  <a class="back-btn" href="../index.html">&#8592; Volver a la presentacion</a>
  <h2>Indice</h2>
  <nav>
    <ul>
        {sidebar_items}
    </ul>
  </nav>
</aside>

<main id="main">
  {content_html}
</main>

</body>
</html>
"""

    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        fh.write(html)

    size = os.path.getsize(OUT_FILE)
    print(f"Archivo generado: {OUT_FILE}")
    print(f"Tamano: {size:,} bytes ({size / 1024:.1f} KB)")
    print(f"Capitulos incluidos: {len(chapters)}")
    for ch in chapters:
        print(f"  [{ch['num']}] {ch['title'][:80]}")


if __name__ == "__main__":
    main()
