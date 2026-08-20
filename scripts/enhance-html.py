#!/usr/bin/env python3
"""Add responsive navigation and color-theme behavior to generated HTML."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "html"
ASSETS = OUT / "assets"

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
  --wave-rule: #c9c5bc;
  --wave-control-bg: #f1efe9;
  --wave-control-border: #aaa69d;
  --wave-selection: #cfe7f5;
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --wave-bg: #111416;
  --wave-text: #e8e4dc;
  --wave-muted: #b7b2aa;
  --wave-link: #8fc7ee;
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
  max-width: 72rem;
  background: var(--wave-bg);
  color: var(--wave-text);
  font-size: clamp(1rem, .97rem + .14vw, 1.08rem);
  line-height: 1.62;
}
::selection { background: var(--wave-selection); }
h1, h2, h3 { line-height: 1.2; overflow-wrap: anywhere; }
a { color: var(--wave-link); text-underline-offset: .13em; }
.book-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: .65rem 1rem;
  border-color: var(--wave-rule);
}
.book-nav-links { display: flex; flex-wrap: wrap; gap: .2rem .55rem; align-items: center; }
.book-nav-links a { white-space: nowrap; }
.theme-toggle {
  min-height: 2.5rem;
  margin-left: auto;
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
  .book-nav { margin-bottom: 1.25rem; font-size: .9rem; }
  .book-nav-links { gap: .35rem .6rem; }
  .theme-toggle { min-height: 2.75rem; }
  figure { margin: 1rem 0; }
  img, svg { margin: .8rem auto; }
  .math.display, mjx-container[jax="CHTML"][display="true"] { padding-bottom: .55rem; }
}
@media print {
  :root, :root[data-theme="dark"] { color-scheme: light; }
  body { background: white; color: black; }
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


def enhance_page(path: Path) -> None:
    text = path.read_text(errors="replace")
    if "assets/wave.js" not in text:
        text = text.replace("</head>", '<script defer src="assets/wave.js"></script>\n</head>')

    def nav_sub(match: re.Match[str]) -> str:
        inner = match.group(2)
        if "data-theme-toggle" in inner:
            return match.group(0)
        return match.group(1) + '<span class="book-nav-links">' + inner + "</span>" + THEME_BUTTON + match.group(3)

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

    for page in pages:
        text = page.read_text(errors="replace")
        if "assets/wave.js" not in text or "data-theme-toggle" not in text:
            raise SystemExit(f"HTML enhancement missing from {page.name}")
    print(f"HTML responsive/theme enhancement OK: {len(pages)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
