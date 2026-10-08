#!/usr/bin/env python3
"""Convert scraped Ed Lessons content into RISE-ready Jupyter notebooks.

One notebook per lecture. Ed slide types map as follows:

    document  (orange doc icon)     -> lecture content: markdown + runnable code cells
    jupyter   (orange Jupyter icon) -> in-class example: description + real notebook cells
    code      ("<>" icon)           -> in-class exercise: titled placeholder for a URL
    quiz      (checkmarks icon)     -> in-class exercise: titled placeholder for a URL

Usage:
    python3 tools/ed_to_ipynb.py [--raw ed-lectures-raw-v2.json] [--out notebooks]
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

# --------------------------------------------------------------------------
# Theme
# --------------------------------------------------------------------------

NYU_VIOLET = "#57068c"
VIOLET_DEEP = "#3a0460"
VIOLET_TINT = "#f3ecfa"
EXERCISE = "#b26a00"
EXERCISE_TINT = "#fff6e6"
DEMO = "#0b6a70"
DEMO_TINT = "#e6f5f6"
INK = "#241c2c"
MUTED = "#6b6478"

# Where notebook images are served from (the repo's notebooks/ folder on GitHub).
IMAGE_BASE = "https://raw.githubusercontent.com/NYU-Testing-Center/dma-lecture-content/main/notebooks/"

# Global slide styling.
#
# JupyterLab's own `.jp-RenderedHTMLCommon h2` rules tie with a plain
# `.reveal h2` on specificity, so whichever loads last wins -- a coin flip we
# don't want to depend on. Every themed declaration is therefore scoped through
# `.jp-RenderedHTMLCommon` as well and marked !important.
THEME_RULES = f"""
/* ==== DMA lecture deck theme (NYU violet) ============================== */
.reveal {{
  --dma-violet: {NYU_VIOLET};
  --dma-violet-deep: {VIOLET_DEEP};
  --dma-ink: {INK};
  --dma-muted: {MUTED};
  font-size: 26px !important;
  color: var(--dma-ink);
}}
/* Slides are top-aligned (center: false), so without this the first heading
   sits flush against the top edge; the bottom pad clears the footer bar. */
.reveal .slides > section,
.reveal .slides > section > section {{
  padding: 22px 10px 46px 10px !important;
  box-sizing: border-box;
}}
.reveal .jp-RenderedHTMLCommon h1, .reveal .jp-RenderedHTMLCommon h2,
.reveal .jp-RenderedHTMLCommon h3, .reveal .jp-RenderedHTMLCommon h4,
.reveal h1, .reveal h2, .reveal h3, .reveal h4 {{
  color: {VIOLET_DEEP} !important;
  text-transform: none !important;
  letter-spacing: -0.01em;
  font-weight: 700 !important;
  text-align: left;
}}
.reveal .jp-RenderedHTMLCommon h1, .reveal h1 {{ font-size: 1.9em !important; }}
.reveal .jp-RenderedHTMLCommon h2, .reveal h2 {{
  font-size: 1.45em !important;
  border-bottom: 3px solid {VIOLET_TINT} !important;
  padding-bottom: 0.25em !important;
  margin-bottom: 0.7em !important;
}}
.reveal .jp-RenderedHTMLCommon h3, .reveal h3 {{
  font-size: 1.15em !important;
  color: {NYU_VIOLET} !important;
}}
.reveal .jp-RenderedHTMLCommon p, .reveal .jp-RenderedHTMLCommon li,
.reveal p, .reveal li {{ line-height: 1.45; text-align: left; }}
.reveal .jp-RenderedHTMLCommon ul, .reveal .jp-RenderedHTMLCommon ol,
.reveal ul, .reveal ol {{ display: block; margin-left: 1.1em; }}
.reveal .jp-RenderedHTMLCommon li, .reveal li {{ margin-bottom: 0.35em; }}
.reveal li::marker {{ color: {NYU_VIOLET}; font-weight: 700; }}
.reveal .jp-RenderedHTMLCommon strong, .reveal strong {{
  color: {VIOLET_DEEP} !important;
}}
.reveal .jp-RenderedHTMLCommon a, .reveal a {{
  color: {NYU_VIOLET} !important;
  text-decoration: underline;
}}
.reveal .jp-RenderedHTMLCommon blockquote, .reveal blockquote {{
  border-left: 4px solid {NYU_VIOLET} !important;
  background: {VIOLET_TINT} !important;
  padding: 0.6em 1em !important;
  box-shadow: none !important;
  font-style: normal !important;
  width: 100%;
}}
/* inline code (block code keeps the editor/pygments styling) */
.reveal .jp-RenderedHTMLCommon :not(pre) > code, .reveal :not(pre) > code {{
  background: {VIOLET_TINT} !important;
  color: {VIOLET_DEEP} !important;
  padding: 0.08em 0.34em !important;
  border-radius: 4px !important;
  font-size: 0.92em !important;
}}
.reveal .jp-InputArea-editor {{
  border-left: 4px solid {NYU_VIOLET} !important;
  border-radius: 0 6px 6px 0;
}}
/* Long source lines must wrap, not run off the side of the slide.
   `.cm-*` covers the live CodeMirror editors RISE presents; `.highlight pre`
   covers the static Pygments markup that `nbconvert --to slides` emits. */
.reveal .jp-InputArea-editor .cm-content,
.reveal .jp-InputArea-editor .cm-line,
.reveal .highlight pre,
.reveal pre code {{
  white-space: pre-wrap !important;
  overflow-wrap: anywhere;
  word-break: break-word;
}}
.reveal .jp-InputArea-editor .cm-content,
.reveal .highlight pre,
.reveal pre code {{
  font-size: 0.8em !important;
  line-height: 1.35 !important;
}}
.reveal .jp-OutputArea-output pre {{
  white-space: pre-wrap !important;
  font-size: 0.74em !important;
}}
/* Keep plots large but bounded, so a figure does not fill the whole slide. */
.reveal .jp-OutputArea img {{ max-height: 55vh; width: auto; max-width: 100%; }}
/* Let a slide scroll when its content is taller than the viewport -- running a
   demo cell adds output and routinely overflows.
   `.reveal` itself is `overflow: hidden`, so without this the overflow is just
   clipped and the rest of the slide is unreachable. RISE's own `scroll: true`
   config is supposed to do this but does not reliably apply, so own it here.
   Scoped to `.present` to leave off-screen slides out of the layout work, and
   deliberately NOT applied to `.jp-OutputArea`: a nested scroll box inside a
   scrolling slide means the wheel scrolls the wrong thing. One scroller. */
.reveal .slides > section.present,
.reveal .slides > section > section.present {{
  overflow-y: auto !important;
  overflow-x: hidden;
  max-height: 100vh;
}}
.reveal .jp-Cell {{ padding: 2px 0 !important; }}
.reveal .jp-RenderedHTMLCommon table {{ font-size: 0.85em !important; }}
.reveal .jp-RenderedHTMLCommon img {{ margin: 0 auto; }}
/* footer bar supplied via notebook `rise` metadata */
.dma-footer {{
  position: fixed; bottom: 0; left: 0; right: 0;
  padding: 6px 22px;
  font-size: 15px;
  color: #ffffff;
  background: linear-gradient(90deg, {VIOLET_DEEP} 0%, {NYU_VIOLET} 100%);
  display: flex; justify-content: space-between; align-items: center;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  z-index: 30;
}}
.dma-footer .dma-course {{ opacity: 0.78; }}
.dma-footer .dma-lecture {{ font-weight: 600; }}
"""

# Delivered twice on purpose, because the two presentation paths read different
# things and neither alone is sufficient:
#   * title cell  -> the only route `nbconvert --to slides` honours (it ignores
#                    `rise` metadata entirely, and drops `skip` cells)
#   * rise.footer -> injected by RISE straight from metadata, so the theme
#                    survives even if markdown HTML is ever sanitised
THEME_CSS = f"<style>{THEME_RULES}</style>"


def footer_html(course_short: str, number: int, title: str) -> str:
    """RISE renders this HTML string verbatim as a persistent footer bar."""
    return (
        '<div class="dma-footer">'
        f'<span class="dma-course">{esc_html(course_short)}</span>'
        f'<span class="dma-lecture">Lecture {number} &nbsp;&middot;&nbsp; {esc_html(title)}</span>'
        "</div>"
        f"<style>{THEME_RULES}</style>"
    )


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------


def esc_html(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return re.sub(r"^-+|-+$", "", text)


def clean_title(text: str) -> str:
    """Ed titles sometimes carry a leading number and stray whitespace."""
    return re.sub(r"\s+", " ", (text or "").strip())


def strip_lecture_number(title: str) -> tuple[int | None, str]:
    m = re.match(r"^\s*(\d+)\s*[.:]\s*(.+)$", title)
    if m:
        return int(m.group(1)), clean_title(m.group(2))
    return None, clean_title(title)


# --------------------------------------------------------------------------
# Ed document XML -> markdown / code parts
# --------------------------------------------------------------------------

# A "part" is either ("md", text) or ("code", source, language).
Part = tuple


class EdRenderer:
    """Renders Ed's `<document version="2.0">` XML into notebook-ready parts."""

    def __init__(self, image_map: dict[str, str]):
        self.image_map = image_map
        self.missing_images: set[str] = set()

    # ---- inline ----------------------------------------------------------

    def inline(self, node: ET.Element) -> str:
        out: list[str] = []
        if node.text:
            out.append(self._text(node.text))
        for child in node:
            out.append(self._inline_child(child))
            if child.tail:
                out.append(self._text(child.tail))
        return "".join(out)

    @staticmethod
    def _text(raw: str) -> str:
        # Escape markdown control characters that appear mid-prose and would
        # otherwise be interpreted as emphasis or headings.
        return raw.replace("*", r"\*").replace("_", r"\_")

    def _inline_child(self, el: ET.Element) -> str:
        tag = el.tag
        inner = self.inline(el)
        if tag == "bold":
            return f"**{inner.strip()}**" if inner.strip() else ""
        if tag == "italic":
            return f"*{inner.strip()}*" if inner.strip() else ""
        if tag == "underline":
            return f"<u>{inner}</u>"
        if tag == "code":
            # Raw text, unescaped -- markdown does not interpolate inside backticks.
            raw = "".join(el.itertext())
            ticks = "``" if "`" in raw else "`"
            return f"{ticks}{raw}{ticks}"
        if tag == "link":
            href = el.get("href", "")
            label = inner.strip() or href
            return f"[{label}]({href})"
        if tag in ("sub", "sup"):
            return f"<{tag}>{inner}</{tag}>"
        if tag == "break":
            return "  \n"
        if tag == "math":
            raw = "".join(el.itertext()).strip()
            return f"${raw}$"
        if tag == "image":
            return self._image(el)
        # Unknown inline tag: keep its text.
        return inner

    def _image(self, el: ET.Element) -> str:
        src = el.get("src", "")
        local = self.image_map.get(src)
        if not local:
            self.missing_images.add(src)
            local = src
        else:
            # Absolute link to the repo's copy, so the image also shows in Colab,
            # which can't resolve a path relative to the notebook.
            local = IMAGE_BASE + local
        width = el.get("width")
        if width:
            try:
                # Cap width so figures never overflow the slide.
                px = min(int(float(width)), 900)
                return f'<img src="{local}" alt="" style="max-width:100%;width:{px}px;height:auto;">'
            except ValueError:
                pass
        return f'<img src="{local}" alt="" style="max-width:100%;height:auto;">'

    # ---- blocks ----------------------------------------------------------

    def render(self, xml: str) -> list[Part]:
        """Split a slide's XML into an ordered list of markdown / code parts."""
        root = ET.fromstring(xml)
        parts: list[Part] = []
        buf: list[str] = []

        def flush() -> None:
            text = "\n\n".join(b for b in buf if b.strip()).strip()
            if text:
                parts.append(("md", text))
            buf.clear()

        for el in root:
            if el.tag == "snippet":
                lang = (el.get("language") or "").lower()
                source = "".join(
                    "".join(f.itertext()) for f in el.findall("snippet-file")
                ).strip("\n")
                if not source.strip():
                    continue
                if lang in ("py", "python", "python3"):
                    # Real code cell -- runnable live during the lecture.
                    flush()
                    parts.append(("code", source, "python"))
                else:
                    fence_lang = {"sqlite": "sql"}.get(lang, lang)
                    buf.append(f"```{fence_lang}\n{source}\n```")
                continue
            block = self._block(el)
            if block:
                buf.append(block)
        flush()
        return parts

    def _block(self, el: ET.Element) -> str:
        tag = el.tag
        if tag == "paragraph":
            return self.inline(el).strip()
        if tag == "heading":
            try:
                level = max(1, min(6, int(el.get("level", "2"))))
            except ValueError:
                level = 2
            # Demote by one: the slide title already occupies h2.
            level = min(6, level + 2)
            text = self.inline(el).strip()
            return f"{'#' * level} {text}" if text else ""
        if tag == "list":
            return self._list(el, depth=0)
        if tag == "pre":
            raw = "".join(el.itertext()).strip("\n")
            return f"```text\n{raw}\n```" if raw.strip() else ""
        if tag == "math":
            raw = "".join(el.itertext()).strip()
            return f"$$\n{raw}\n$$" if raw else ""
        if tag == "figure":
            imgs = [self._image(img) for img in el.findall(".//image")]
            caption = (el.findtext("caption") or "").strip()
            body = "\n".join(imgs)
            if not body:
                return ""
            block = f'<div style="text-align:center;margin:0.4em 0;">{body}</div>'
            if caption:
                block += (
                    f'\n<div style="text-align:center;font-size:0.8em;color:{MUTED};">'
                    f"{esc_html(caption)}</div>"
                )
            return block
        if tag == "callout":
            inner = "\n\n".join(filter(None, (self._block(c) for c in el)))
            return "\n".join(f"> {line}" for line in inner.splitlines()) if inner else ""
        # Unknown block: fall back to its inline rendering.
        return self.inline(el).strip()

    def _list(self, el: ET.Element, depth: int) -> str:
        ordered = (el.get("style") or "").lower() in ("number", "ordered", "numbered")
        lines: list[str] = []
        indent = "  " * depth
        for i, item in enumerate(el.findall("list-item"), start=1):
            marker = f"{i}." if ordered else "-"
            chunks: list[str] = []
            nested: list[str] = []
            for child in item:
                if child.tag == "list":
                    nested.append(self._list(child, depth + 1))
                else:
                    text = self._block(child)
                    if text:
                        chunks.append(text)
            body = " ".join(c.replace("\n", " ") for c in chunks).strip()
            lines.append(f"{indent}{marker} {body}" if body else f"{indent}{marker}")
            lines.extend(n for n in nested if n)
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Live-demo code fixups
# --------------------------------------------------------------------------

_PLOT_CALL = re.compile(
    r"\b(?:plt|sns|ax)\s*\.\s*\w*"
    r"(?:plot|scatter|hist|bar|heatmap|boxplot|imshow|pie|figure|subplots"
    r"|regplot|lmplot|pairplot|displot|countplot)\w*\s*\(",
    re.IGNORECASE,
)


def ensure_figure_renders(source: str) -> str:
    """Append an explicit ``plt.show()`` to a plotting cell that lacks one.

    Ed's notebooks rely on the inline backend implicitly flushing figures at the
    end of a cell. That breaks as soon as anything in the session runs
    ``%matplotlib inline``: from then on figures are only emitted by an explicit
    ``show()``, so a plotting cell renders its object repr
    (``[<matplotlib.lines.Line2D ...>]``) and no image. Verified on
    matplotlib 3.10 / matplotlib_inline 0.1.6 / IPython 8.30 -- and it poisons
    every later cell in the same kernel, not just the one with the magic.

    ``plt.show()`` is correct under any backend, so adding it makes the demos
    render regardless of the magic or the matplotlib version. Cells that never
    reference ``plt`` are left alone -- there we would have to invent an import.
    """
    if not _PLOT_CALL.search(source):
        return source
    if ".show()" in source:
        return source
    if not re.search(r"\bplt\b", source):
        return source
    return source.rstrip("\n") + "\nplt.show()"


# --------------------------------------------------------------------------
# Notebook assembly
# --------------------------------------------------------------------------


def cell(kind: str, source: str, slide_type: str = "", cid: str = "") -> dict:
    meta = {"slideshow": {"slide_type": slide_type}}
    src = source.rstrip("\n")
    base = {
        "cell_type": kind,
        "id": cid,
        "metadata": meta,
        "source": src.splitlines(keepends=True),
    }
    if kind == "code":
        base.update(execution_count=None, outputs=[])
    return base


def assign_ids(cells: list[dict], number: int) -> None:
    """nbformat 4.5 requires a unique cell id; derive them deterministically so
    regenerating a lecture produces a byte-identical file."""
    for i, c in enumerate(cells):
        c["id"] = f"l{number:02d}c{i:04d}"


def title_card(number: int, title: str, course_name: str, counts: dict) -> str:
    bits = []
    if counts["content"]:
        bits.append(f"{counts['content']} content slides")
    if counts["demo"]:
        bits.append(f"{counts['demo']} live demos")
    if counts["exercise"]:
        bits.append(f"{counts['exercise']} in-class exercises")
    summary = " &nbsp;&middot;&nbsp; ".join(bits)
    return f"""<div style="
    background:linear-gradient(135deg,{VIOLET_DEEP} 0%,{NYU_VIOLET} 55%,#7b1fa2 100%);
    color:#fff;border-radius:14px;padding:2.2em 2em 1.8em 2em;
    box-shadow:0 10px 30px rgba(87,6,140,0.28);">
  <div style="font-size:0.62em;letter-spacing:0.18em;text-transform:uppercase;opacity:0.82;">
    {esc_html(course_name)}
  </div>
  <div style="display:flex;align-items:baseline;gap:0.55em;margin-top:0.5em;">
    <span style="
        font-size:1.05em;font-weight:800;background:rgba(255,255,255,0.16);
        border:2px solid rgba(255,255,255,0.5);border-radius:10px;
        padding:0.08em 0.5em;line-height:1.25;">{number}</span>
    <span style="font-size:1.35em;font-weight:800;line-height:1.15;">{esc_html(title)}</span>
  </div>
  <div style="height:3px;width:110px;background:rgba(255,255,255,0.65);
              border-radius:2px;margin:0.9em 0 0.7em 0;"></div>
  <div style="font-size:0.62em;opacity:0.85;">{summary}</div>
</div>"""


def exercise_card(title: str) -> str:
    return f"""<div style="
    border:2px solid {EXERCISE};border-left:10px solid {EXERCISE};
    background:{EXERCISE_TINT};border-radius:12px;padding:1.3em 1.5em;">
  <div style="font-size:0.6em;font-weight:800;letter-spacing:0.16em;
              text-transform:uppercase;color:{EXERCISE};">
    &#129514; In-Class Exercise
  </div>
  <div style="font-size:1.15em;font-weight:800;color:{INK};margin:0.45em 0 0.9em 0;">
    {esc_html(title)}
  </div>
  <div style="background:#fff;border:2px dashed {EXERCISE};border-radius:8px;
              padding:0.7em 0.9em;font-size:0.72em;color:{MUTED};">
    <b style="color:{EXERCISE};">Exercise link:</b>
    <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;">
      &lt;paste URL here&gt;
    </span>
  </div>
</div>"""


def demo_banner(title: str) -> str:
    return f"""<div style="
    border-left:10px solid {DEMO};background:{DEMO_TINT};
    border-radius:0 10px 10px 0;padding:0.75em 1.1em;margin-bottom:0.6em;">
  <span style="font-size:0.58em;font-weight:800;letter-spacing:0.16em;
               text-transform:uppercase;color:{DEMO};">
    &#128200; Live Example
  </span>
  <div style="font-size:1.08em;font-weight:800;color:{INK};margin-top:0.2em;">
    {esc_html(title)}
  </div>
</div>"""


def end_card(number: int, title: str) -> str:
    return f"""<div style="
    background:{VIOLET_TINT};border:2px solid {NYU_VIOLET};border-radius:14px;
    padding:1.8em 2em;text-align:center;">
  <div style="font-size:0.62em;letter-spacing:0.18em;text-transform:uppercase;
              color:{NYU_VIOLET};font-weight:800;">End of Lecture {number}</div>
  <div style="font-size:1.15em;font-weight:800;color:{VIOLET_DEEP};margin-top:0.4em;">
    {esc_html(title)}
  </div>
</div>"""


COLAB_REPO = "NYU-Testing-Center/dma-lecture-content"

# Runs only in Colab: clone the repo and cd into notebooks/, so the lecture's
# relative paths to its data files (CSV, JSON, XML, .db, ...) resolve exactly as
# they do in a codespace. Elsewhere it does nothing.
COLAB_SETUP = f"""# Colab setup: download the course data files this lecture uses.
# Outside Colab (Codespaces, your own machine) this cell does nothing.
import os, sys
if "google.colab" in sys.modules:
    if not os.path.exists("/content/dma-lecture-content"):
        !git clone --depth 1 -q https://github.com/{COLAB_REPO}.git /content/dma-lecture-content
    %cd /content/dma-lecture-content/notebooks"""


def colab_cells(fname: str, nb: dict, data_files: list[str]) -> list[dict]:
    """An Open in Colab button for every lecture, plus the setup cell for lectures
    whose code reads a data file from notebooks/. Both are skipped in the slideshow."""
    url = f"https://colab.research.google.com/github/{COLAB_REPO}/blob/main/notebooks/{fname}"
    cells = [cell("markdown",
                  f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url})",
                  "skip")]
    code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    if any(name in code for name in data_files):
        cells.append(cell("code", COLAB_SETUP, "skip"))
    return cells


def build_notebook(lesson: dict, notebooks: dict, renderer: EdRenderer, course: dict) -> tuple[dict, dict]:
    number = lesson["index"]
    _, title = strip_lecture_number(lesson["title"])
    course_name = course["display"]

    slides = sorted(lesson["slides"], key=lambda s: s.get("index") or 0)
    counts = {"content": 0, "demo": 0, "exercise": 0}
    for s in slides:
        if s["type"] == "document":
            counts["content"] += 1
        elif s["type"] == "jupyter":
            counts["demo"] += 1
        else:
            counts["exercise"] += 1

    cells = [
        cell(
            "markdown",
            THEME_CSS + "\n\n" + title_card(number, title, course_name, counts),
            "slide",
        )
    ]

    for s in slides:
        stype = s["type"]
        s_title = clean_title(s["title"])
        content = s.get("content") or ""

        if stype in ("code", "quiz"):
            cells.append(cell("markdown", exercise_card(s_title), "slide"))
            continue

        if stype == "jupyter":
            head = demo_banner(s_title)
            parts = renderer.render(content) if content.strip() else []
            md = "\n\n".join(t for kind, t, *_ in parts if kind == "md")
            cells.append(cell("markdown", head + ("\n\n" + md if md else ""), "slide"))
            nb = notebooks.get(str(s["id"]))
            if nb:
                for c in nb["cells"]:
                    src = (c.get("source") or "").rstrip("\n")
                    if not src.strip():
                        continue
                    kind = "code" if c.get("type") == "code" else "markdown"
                    if kind == "code":
                        src = ensure_figure_renders(src)
                    # In these notebooks every markdown cell narrates the code
                    # that follows it, so each one starts a new subslide and
                    # carries its code along. Without a break like this the
                    # 106-cell Mongo notebook collapses into one unusable slide.
                    cells.append(cell(kind, src, "subslide" if kind == "markdown" else ""))
            continue

        # document -> lecture content
        heading = f"## {s_title}" if s_title else ""
        parts = renderer.render(content) if content.strip() else []
        first = True
        if not parts:
            cells.append(cell("markdown", heading or "##", "slide"))
            continue
        for part in parts:
            if part[0] == "md":
                text = part[1]
                if first:
                    text = f"{heading}\n\n{text}" if heading else text
                cells.append(cell("markdown", text, "slide" if first else ""))
                first = False
            else:
                if first and heading:
                    cells.append(cell("markdown", heading, "slide"))
                    first = False
                cells.append(cell("code", part[1], "" if not first else "slide"))
                first = False

    cells.append(cell("markdown", end_card(number, title), "slide"))
    assign_ids(cells, number)

    nb = {
        "cells": cells,
        "metadata": {
            "celltoolbar": "Slideshow",
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
            },
            "rise": {
                "autolaunch": False,
                "enable_chalkboard": True,
                "footer": footer_html(course["short"], number, title),
                "header": "",
                "scroll": True,
                "slideNumber": "c/t",
                "theme": "simple",
                "transition": "fade",
                "center": False,
                "controls": True,
                "progress": True,
                "start_slideshow_at": "beginning",
                "width": "100%",
                "height": "100%",
            },
            "dma": {
                "source": "Ed Lessons",
                "ed_course_id": lesson.get("course_id", course["id"]),
                "ed_lesson_id": lesson["id"],
                "lecture_number": number,
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return nb, counts


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="ed-lectures-raw-v2.json")
    ap.add_argument("--out", default="notebooks")
    ap.add_argument("--images", default="tools/image_map.json")
    args = ap.parse_args()

    raw = json.loads(Path(args.raw).read_text())
    image_map = json.loads(Path(args.images).read_text())
    renderer = EdRenderer(image_map)

    course = {
        "id": raw["course"]["primary"]["id"],
        # Literal characters, not HTML entities -- these pass through esc_html().
        "display": "CS 0479 · Data Management and Analysis",
        "short": "CS 0479 · Data Management and Analysis",
    }

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # data files the lectures read, which Colab gets via the setup cell
    data_files = [p.name for p in out_dir.iterdir()
                  if p.is_file() and p.suffix != ".ipynb" and p.name != "manifest.json"]

    manifest = []
    totals = {"content": 0, "demo": 0, "exercise": 0, "cells": 0}
    for lesson in sorted(raw["lessons"], key=lambda L: L["index"]):
        nb, counts = build_notebook(lesson, raw["notebooks"], renderer, course)
        _, title = strip_lecture_number(lesson["title"])
        fname = f"lecture-{lesson['index']:02d}-{slugify(title)[:60]}.ipynb"
        # right after the title card
        nb["cells"][1:1] = colab_cells(fname, nb, data_files)
        assign_ids(nb["cells"], lesson["index"])
        (out_dir / fname).write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
        for k in ("content", "demo", "exercise"):
            totals[k] += counts[k]
        totals["cells"] += len(nb["cells"])
        manifest.append(
            {
                "number": lesson["index"],
                "title": title,
                "file": fname,
                "cells": len(nb["cells"]),
                **counts,
            }
        )
        print(f"  {fname:<72} {len(nb['cells']):>4} cells")

    Path(args.out, "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(
        f"\n{len(manifest)} notebooks | {totals['cells']} cells | "
        f"{totals['content']} content, {totals['demo']} demos, {totals['exercise']} exercises"
    )
    if renderer.missing_images:
        print(f"WARNING: {len(renderer.missing_images)} images had no local copy")
        for u in sorted(renderer.missing_images):
            print("   ", u)


if __name__ == "__main__":
    main()
