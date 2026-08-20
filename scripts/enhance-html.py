#!/usr/bin/env python3
"""Add responsive navigation and color-theme behavior to generated HTML."""
from __future__ import annotations

import html
import re
from pathlib import Path

from book_views import book_structure

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
ASSETS = OUT / "assets"
BOOK_TITLE = "Wave Motions in the Ocean"
REPOSITORY_URL = "https://github.com/mwyau/wave-motions-in-the-ocean"
REPOSITORY_LINK = f'<a class="source-link" href="{REPOSITORY_URL}">GitHub Source</a>'
MATHJAX_UNPINNED = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
MATHJAX_PINNED = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"

THEME_BUTTON = (
    '<button class="theme-toggle" type="button" data-theme-toggle '
    'aria-label="Color theme: Auto">Theme: Auto</button>'
)

EXTRA_CSS = r"""

/* Responsive reading layout and automatic/manual color themes. */
:root {
  color-scheme: light dark;
  --wave-bg: #fbfaf7;
  --wave-text: #202124;
  --wave-muted: #62666b;
  --wave-link: #145d8c;
  --wave-visited: #6b4c84;
  --wave-rule: #c9c5bc;
  --wave-control-bg: #f1efe9;
  --wave-control-border: #aaa69d;
  --wave-selection: #cfe7f5;
}
:root[data-theme="light"] {
  color-scheme: light;
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --wave-bg: #111416;
  --wave-text: #e8e4dc;
  --wave-muted: #b7b2aa;
  --wave-link: #8fc7ee;
  --wave-visited: #cbb3e6;
  --wave-rule: #4b5054;
  --wave-control-bg: #202427;
  --wave-control-border: #62686d;
  --wave-selection: #284b62;
}
html {
  background: var(--wave-bg);
  -webkit-text-size-adjust: 100%;
  text-size-adjust: 100%;
}
body {
  box-sizing: border-box;
  max-width: 60rem;
  background: var(--wave-bg);
  color: var(--wave-text);
  font-size: clamp(1rem, .97rem + .14vw, 1.08rem);
  line-height: 1.62;
}
::selection { background: var(--wave-selection); }
h1, h2, h3 { line-height: 1.2; overflow-wrap: anywhere; }
a { color: var(--wave-link); text-underline-offset: .13em; }
a:visited { color: var(--wave-visited); }
.book-nav {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: .65rem 1.15rem;
  border-color: var(--wave-rule);
}
.book-context {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: .12rem;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.2;
}
.book-title {
  width: fit-content;
  color: var(--wave-text);
  font-size: .78rem;
  font-weight: 700;
  letter-spacing: .045em;
  text-decoration: none;
  text-transform: uppercase;
}
.book-title:visited { color: var(--wave-text); }
.book-location { color: var(--wave-muted); font-size: .9rem; font-weight: 600; }
.book-controls { min-width: 0; display: flex; align-items: center; gap: .8rem; }
.book-nav-links { min-width: 0; display: flex; flex-wrap: wrap; gap: .2rem .55rem; align-items: center; }
.book-nav-links a { display: inline-flex; align-items: center; min-height: 2.25rem; white-space: nowrap; }
.theme-toggle {
  flex: 0 0 auto;
  min-height: 2.5rem;
  margin-left: 0;
  border: 1px solid var(--wave-control-border);
  border-radius: .55rem;
  padding: .4rem .7rem;
  background: var(--wave-control-bg);
  color: var(--wave-text);
  cursor: pointer;
  font: .88rem system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.theme-toggle:focus-visible { outline: 2px solid var(--wave-link); outline-offset: 2px; }
.book-toc { border-color: var(--wave-rule); }
figure { max-width: 100%; }
figcaption { color: var(--wave-muted); }
img, svg { max-width: 100%; height: auto; }
.math.display,
mjx-container[jax="CHTML"][display="true"] {
  display: block;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  padding: .25rem 0 .4rem;
  -webkit-overflow-scrolling: touch;
}
mjx-container[jax="CHTML"] { color: inherit; }
pre { max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
table { display: block; max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.license { color: var(--wave-muted); }
:root[data-theme="dark"] img[src^="assets/figures/"][src$=".svg"],
:root[data-theme="dark"] img[src^="assets/figures/source-"][src$=".png"],
:root[data-theme="dark"] img[src^="assets/figures/ch"][src$=".png"] {
  filter: invert(1) hue-rotate(180deg) brightness(.9) contrast(1.05);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    color-scheme: dark;
    --wave-bg: #111416;
    --wave-text: #e8e4dc;
    --wave-muted: #b7b2aa;
    --wave-link: #8fc7ee;
    --wave-visited: #cbb3e6;
    --wave-rule: #4b5054;
    --wave-control-bg: #202427;
    --wave-control-border: #62686d;
    --wave-selection: #284b62;
  }
  :root:not([data-theme]) img[src^="assets/figures/"][src$=".svg"],
  :root:not([data-theme]) img[src^="assets/figures/source-"][src$=".png"],
  :root:not([data-theme]) img[src^="assets/figures/ch"][src$=".png"] {
    filter: invert(1) hue-rotate(180deg) brightness(.9) contrast(1.05);
  }
}
@media (max-width: 700px) {
  body {
    padding: max(.9rem, env(safe-area-inset-top)) max(.9rem, env(safe-area-inset-right)) 3rem max(.9rem, env(safe-area-inset-left));
    line-height: 1.56;
  }
  h1 { font-size: clamp(1.65rem, 7vw, 2.2rem); }
  h2 { font-size: clamp(1.35rem, 5.7vw, 1.75rem); }
  .book-nav {
    grid-template-columns: minmax(0, 1fr);
    align-items: stretch;
    gap: .45rem;
    margin-bottom: 1.25rem;
    font-size: .9rem;
  }
  .book-context { gap: .08rem; }
  .book-title { font-size: .72rem; }
  .book-location { font-size: .86rem; line-height: 1.25; }
  .book-controls { width: 100%; gap: .55rem; }
  .book-nav-links {
    flex: 1 1 auto;
    flex-wrap: nowrap;
    gap: .65rem;
    overflow-x: auto;
    overscroll-behavior-inline: contain;
    padding-bottom: .12rem;
    scrollbar-width: thin;
    -webkit-overflow-scrolling: touch;
  }
  .book-nav-links a { min-height: 2.75rem; }
  .theme-toggle { min-height: 2.75rem; }
  figure { margin: 1rem 0; }
  img, svg { margin: .8rem auto; }
  .math.display, mjx-container[jax="CHTML"][display="true"] { padding-bottom: .55rem; }
}
@media print {
  :root,
  :root:not([data-theme]),
  :root[data-theme="light"],
  :root[data-theme="dark"] {
    color-scheme: light;
    --wave-bg: #fff;
    --wave-text: #000;
    --wave-muted: #444;
    --wave-link: #000;
    --wave-visited: #000;
    --wave-rule: #aaa;
    --wave-control-bg: #fff;
    --wave-control-border: #aaa;
    --wave-selection: #ddd;
  }
  body { background: var(--wave-bg); color: var(--wave-text); }
  .theme-toggle { display: none; }
  img[src^="assets/figures/"] { filter: none !important; }
}
"""

JS = r"""(() => {
  const root = document.documentElement;
  const key = "wave-theme";
  const modes = ["auto", "light", "dark"];
  let mode = "auto";
  try {
    const saved = localStorage.getItem(key);
    if (modes.includes(saved)) mode = saved;
  } catch (_) {}

  const apply = () => {
    if (mode === "auto") delete root.dataset.theme;
    else root.dataset.theme = mode;
    const label = mode[0].toUpperCase() + mode.slice(1);
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.textContent = `Theme: ${label}`;
      button.setAttribute("aria-label", `Color theme: ${label}. Activate to change.`);
    });
  };

  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      mode = modes[(modes.indexOf(mode) + 1) % modes.length];
      try {
        if (mode === "auto") localStorage.removeItem(key);
        else localStorage.setItem(key, mode);
      } catch (_) {}
      apply();
    });
  });
  apply();
})();
"""

NAV_RE = re.compile(r'(<nav class="book-nav"[^>]*>)(.*?)(</nav>)', re.S)


def page_context(path: Path) -> str:
    if path.name == "index.html":
        return "Front matter & contents"
    if path.name == "references.html":
        return "References"
    match = re.fullmatch(r"chapter([1-6])\.html", path.name)
    if match:
        number = int(match.group(1))
        chapter = next(chapter for chapter in book_structure() if chapter.number == number)
        return f"Chapter {chapter.number} · {chapter.title}"
    raise ValueError(f"unexpected publication page: {path.name}")


def enhance_page(path: Path) -> None:
    text = path.read_text(errors="replace")
    text = text.replace(MATHJAX_UNPINNED, MATHJAX_PINNED)
    context = page_context(path)
    escaped_context = html.escape(context)
    document_title = BOOK_TITLE if path.name == "index.html" else f"{context} — {BOOK_TITLE}"
    text = re.sub(
        r"<title>.*?</title>",
        f"<title>{html.escape(document_title)}</title>",
        text,
        count=1,
        flags=re.S,
    )
    if "assets/wave.js" not in text:
        text = text.replace("</head>", '<script defer src="assets/wave.js"></script>\n</head>')

    nav_context = (
        '<span class="book-context">'
        f'<a class="book-title" href="index.html">{BOOK_TITLE}</a>'
        f'<span class="book-location">{escaped_context}</span>'
        "</span>"
    )

    def nav_sub(match: re.Match[str]) -> str:
        inner = match.group(2).replace('href="index.html"', 'href="index.html#contents"')
        if REPOSITORY_URL not in inner:
            inner = inner.rstrip() + " · " + REPOSITORY_LINK
        if "data-theme-toggle" in inner or "book-context" in inner:
            return match.group(1) + inner + match.group(3)
        controls = (
            '<span class="book-controls"><span class="book-nav-links">'
            + inner
            + "</span>"
            + THEME_BUTTON
            + "</span>"
        )
        return match.group(1) + nav_context + controls + match.group(3)

    text = NAV_RE.sub(nav_sub, text)
    path.write_text(text)


def main() -> int:
    css = ASSETS / "wave.css"
    if not css.is_file():
        raise SystemExit(f"missing generated stylesheet: {css}")
    css_text = css.read_text(errors="replace")
    marker = "/* Responsive reading layout and automatic/manual color themes. */"
    if marker not in css_text:
        css.write_text(css_text + EXTRA_CSS)
    (ASSETS / "wave.js").write_text(JS)

    pages = sorted(OUT.glob("*.html"))
    if not pages:
        raise SystemExit("no generated HTML pages to enhance")
    for page in pages:
        enhance_page(page)

    index = OUT / "index.html"
    if 'id="contents"' not in index.read_text(errors="replace"):
        raise SystemExit("HTML contents anchor is missing from index.html")

    for page in pages:
        text = page.read_text(errors="replace")
        expected_context = html.escape(page_context(page))
        if "assets/wave.js" not in text or "data-theme-toggle" not in text or REPOSITORY_URL not in text:
            raise SystemExit(f"HTML enhancement missing from {page.name}")
        if 'class="book-context"' not in text or f'class="book-location">{expected_context}</span>' not in text:
            raise SystemExit(f"HTML reading context is missing from {page.name}")
        if 'href="index.html#contents"' not in text:
            raise SystemExit(f"HTML contents navigation is missing from {page.name}")
        if MATHJAX_UNPINNED in text:
            raise SystemExit(f"unversioned MathJax URL remains in {page.name}")
    print(f"HTML responsive/theme enhancement OK: {len(pages)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
