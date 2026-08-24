(() => {
  const root = document.documentElement;
  const themeKey = "wave-theme";
  const themeModes = ["auto", "light", "dark"];
  const themeNames = { auto: "Auto", light: "Light", dark: "Dark" };
  const themeButtons = document.querySelectorAll("[data-theme-cycle]");
  let themeMode = "auto";

  try {
    const saved = localStorage.getItem(themeKey);
    if (themeModes.includes(saved)) themeMode = saved;
  } catch (_) {}

  const applyTheme = () => {
    if (themeMode === "auto") delete root.dataset.theme;
    else root.dataset.theme = themeMode;
    const nextMode = themeModes[(themeModes.indexOf(themeMode) + 1) % themeModes.length];
    themeButtons.forEach((button) => {
      const label = button.querySelector("[data-theme-label]");
      if (label) label.textContent = themeNames[themeMode];
      button.setAttribute(
        "aria-label",
        `Appearance: ${themeNames[themeMode]}; switch to ${themeNames[nextMode]}`,
      );
      button.title = `Appearance: ${themeNames[themeMode]}`;
    });
  };

  themeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      themeMode = themeModes[(themeModes.indexOf(themeMode) + 1) % themeModes.length];
      try {
        if (themeMode === "auto") localStorage.removeItem(themeKey);
        else localStorage.setItem(themeKey, themeMode);
      } catch (_) {}
      applyTheme();
    });
  });
  applyTheme();

  const params = new URLSearchParams(location.search);
  const mathKey = "wave-math-renderer";
  const mathModes = ["mathjax", "mathml"];
  const mathNames = { mathjax: "MathJax", mathml: "MathML" };
  let savedMathMode = "mathjax";
  try {
    const saved = localStorage.getItem(mathKey);
    if (mathModes.includes(saved)) savedMathMode = saved;
  } catch (_) {}
  const requestedMathMode = params.get("math");
  let mathMode = mathModes.includes(requestedMathMode) ? requestedMathMode : savedMathMode;
  const mathCycle = document.querySelector("[data-math-cycle]");
  const mathRenderers = document.querySelectorAll("[data-math-renderer]");
  const readerPagePattern = /^(?:index|chapter\d+|references)\.html$/;

  const updateReaderLinks = () => {
    document.querySelectorAll("a[href]").forEach((link) => {
      const raw = link.getAttribute("href");
      if (!raw || raw.startsWith("#")) return;
      let url;
      try {
        url = new URL(raw, location.href);
      } catch (_) {
        return;
      }
      if (url.origin !== location.origin) return;
      const filename = url.pathname.split("/").pop();
      if (!readerPagePattern.test(filename)) return;
      if (mathMode === "mathml") url.searchParams.set("math", "mathml");
      else url.searchParams.delete("math");
      const query = url.searchParams.toString();
      link.setAttribute("href", `${filename}${query ? `?${query}` : ""}${url.hash}`);
    });
  };

  const updateReaderUrl = () => {
    const url = new URL(location.href);
    if (mathMode === "mathml") url.searchParams.set("math", "mathml");
    else url.searchParams.delete("math");
    const query = url.searchParams.toString();
    history.replaceState(null, "", `${url.pathname}${query ? `?${query}` : ""}${url.hash}`);
  };

  const typesetMathJaxIfNeeded = () => {
    const pending = Array.from(
      document.querySelectorAll('[data-math-renderer="mathjax"]'),
    ).filter((node) => !node.querySelector('mjx-container[jax="CHTML"]'));
    if (!pending.length) return Promise.resolve();
    const mathJax = window.MathJax;
    if (!mathJax) return Promise.resolve();
    const typeset = () => {
      if (typeof mathJax.typesetPromise === "function") {
        return mathJax.typesetPromise(pending).catch(() => {});
      }
      return Promise.resolve();
    };
    if (mathJax.startup?.promise) return mathJax.startup.promise.then(typeset).catch(() => {});
    return typeset();
  };

  const visibleContentAnchor = () => {
    const headerBottom =
      document.querySelector(".reader-header")?.getBoundingClientRect().bottom ?? 0;
    const node = Array.from(document.querySelectorAll("#main-content > *")).find((element) => {
      const rect = element.getBoundingClientRect();
      return rect.bottom > headerBottom && rect.top < innerHeight;
    });
    return node ? { node, top: node.getBoundingClientRect().top } : null;
  };

  const restoreContentAnchor = (anchor) => {
    if (!anchor?.node.isConnected) return;
    scrollBy(0, anchor.node.getBoundingClientRect().top - anchor.top);
  };

  const applyMathMode = () => {
    mathRenderers.forEach((node) => {
      node.hidden = node.dataset.mathRenderer !== mathMode;
    });
    if (mathCycle) {
      const label = mathCycle.querySelector("[data-math-label]");
      const nextMode = mathModes[(mathModes.indexOf(mathMode) + 1) % mathModes.length];
      if (label) label.textContent = mathNames[mathMode];
      mathCycle.setAttribute(
        "aria-label",
        `Rendering: ${mathNames[mathMode]}; switch to ${mathNames[nextMode]}`,
      );
      mathCycle.title = `Rendering: ${mathNames[mathMode]}`;
    }
    const layoutReady =
      mathMode === "mathjax" ? typesetMathJaxIfNeeded() : Promise.resolve();
    try {
      if (mathMode === "mathjax") localStorage.removeItem(mathKey);
      else localStorage.setItem(mathKey, mathMode);
    } catch (_) {}
    updateReaderUrl();
    updateReaderLinks();
    return layoutReady;
  };

  if (mathCycle) {
    mathCycle.addEventListener("click", () => {
      const anchor = visibleContentAnchor();
      mathMode = mathModes[(mathModes.indexOf(mathMode) + 1) % mathModes.length];
      applyMathMode().then(() => {
        requestAnimationFrame(() => restoreContentAnchor(anchor));
      });
    });
  }
  applyMathMode();

  const installPermalinks = () => {
    document.querySelectorAll("main > h1[id], main h2[id]").forEach((heading) => {
      if (heading.querySelector(":scope > .heading-permalink")) return;
      heading.dataset.readerTitle = heading.textContent.trim();
      const link = document.createElement("a");
      link.className = "heading-permalink";
      link.href = `#${encodeURIComponent(heading.id)}`;
      link.textContent = "#";
      link.setAttribute("aria-label", `Permalink to ${heading.dataset.readerTitle}`);
      link.title = "Permalink";
      heading.append(link);
    });
  };
  installPermalinks();

  document.querySelectorAll("[data-toc-scope]").forEach((scope) => {
    const button = scope.querySelector("[data-toc-expand]");
    const groups = Array.from(scope.querySelectorAll("details.book-toc-group"));
    if (!button || !groups.length) return;

    const syncLabel = () => {
      const allOpen = groups.every((group) => group.open);
      button.textContent = allOpen ? "Collapse all" : "Expand all";
      button.setAttribute(
        "aria-label",
        allOpen ? "Collapse all contents groups" : "Expand all contents groups",
      );
    };

    button.addEventListener("click", () => {
      const open = !groups.every((group) => group.open);
      groups.forEach((group) => {
        group.open = open;
      });
      syncLabel();
    });
    groups.forEach((group) => group.addEventListener("toggle", syncLabel));
    syncLabel();
  });

  const tocPanel = document.querySelector("#book-contents");
  const tocToggle = document.querySelector("[data-toc-toggle]");
  const tocRail = document.querySelector("[data-book-toc-rail]");
  const readerHeader = document.querySelector(".reader-header");
  const mainContent = document.querySelector("#main-content");
  const supportsPopover = "showPopover" in HTMLElement.prototype;

  const updateContentsTop = () => {
    const gutter = 16;
    const headerBottom = readerHeader?.getBoundingClientRect().bottom ?? 0;
    const top = Math.max(gutter, headerBottom + 8);
    root.style.setProperty("--book-contents-top", `${top}px`);
  };

  const updateContentsMode = () => {
    if (!tocRail || !tocToggle || !mainContent) return;

    tocRail.hidden = false;
    tocRail.style.visibility = "hidden";
    tocRail.style.pointerEvents = "none";
    tocRail.style.removeProperty("left");

    const contentLeft = mainContent.getBoundingClientRect().left;
    const railWidth = tocRail.getBoundingClientRect().width;
    const rem = Number.parseFloat(getComputedStyle(root).fontSize) || 16;
    const gutter = Math.max(16, rem);
    const gap = 1.5 * rem;
    const left = contentLeft - gap - railWidth;
    const showRail = left >= gutter;

    if (showRail) tocRail.style.left = `${left}px`;
    tocRail.hidden = !showRail;
    tocRail.style.removeProperty("visibility");
    tocRail.style.removeProperty("pointer-events");
    tocToggle.hidden = showRail;

    if (showRail && tocPanel?.matches(":popover-open")) tocPanel.hidePopover();
  };

  const positionContents = () => {
    if (!tocPanel || !tocToggle) return;
    updateContentsTop();
    const gutter = 16;
    const toggleRect = tocToggle.getBoundingClientRect();
    const panelWidth = Number.parseFloat(getComputedStyle(tocPanel).width) || 320;
    const maxLeft = Math.max(gutter, innerWidth - panelWidth - gutter);
    const left = Math.min(Math.max(toggleRect.left, gutter), maxLeft);
    tocPanel.style.setProperty("--book-contents-left", `${left}px`);
  };

  if (tocPanel && tocToggle) {
    if (supportsPopover) {
      tocPanel.hidden = false;
      tocPanel.addEventListener("beforetoggle", (event) => {
        if (event.newState === "open") positionContents();
      });
      tocPanel.addEventListener("click", (event) => {
        if (event.target.closest("a[href]") && tocPanel.matches(":popover-open")) {
          tocPanel.hidePopover();
        }
      });
    } else {
      tocToggle.addEventListener("click", () => {
        location.href = "index.html";
      });
    }
  }

  const updateContentsLayout = () => {
    updateContentsTop();
    updateContentsMode();
    if (tocPanel?.matches(":popover-open")) positionContents();
  };
  updateContentsLayout();
  addEventListener("resize", updateContentsLayout, { passive: true });

  let contentsScrollFrame = 0;
  addEventListener(
    "scroll",
    () => {
      if (contentsScrollFrame) return;
      contentsScrollFrame = requestAnimationFrame(() => {
        contentsScrollFrame = 0;
        updateContentsTop();
      });
    },
    { passive: true },
  );

  const links = new Map();
  document.querySelectorAll("a[data-section-link]").forEach((link) => {
    const id = link.dataset.sectionLink;
    if (!links.has(id)) links.set(id, []);
    links.get(id).push(link);
  });
  if (!links.size) return;

  const headings = Array.from(document.querySelectorAll("main > h1[id], main h2[id]")).filter(
    (heading) => links.has(heading.id),
  );
  if (!headings.length) return;

  const readerContextTitle = document.querySelector(".reader-context-title");
  const defaultReaderTitle = readerContextTitle?.textContent ?? "";
  const setActive = (heading) => {
    const activeId = heading?.id || "";
    links.forEach((matchingLinks, id) => {
      const active = id === activeId;
      matchingLinks.forEach((link) => {
        link.classList.toggle("is-active", active);
        if (active) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
    });
    if (readerContextTitle) {
      readerContextTitle.textContent = heading?.dataset.readerTitle || defaultReaderTitle;
    }
  };

  const headingById = new Map(headings.map((heading) => [heading.id, heading]));
  const activeHeadingFromHash = () => {
    let hashId = "";
    try {
      hashId = decodeURIComponent(location.hash.slice(1));
    } catch (_) {}
    return headingById.get(hashId) || null;
  };
  const activeHeadingFromPosition = () => {
    const threshold = Number.parseFloat(getComputedStyle(headings[0]).scrollMarginTop) || 0;
    return (
      headings
        .filter((heading) => heading.getBoundingClientRect().top <= threshold)
        .at(-1) || null
    );
  };
  const syncActiveFromPosition = () => {
    setActive(activeHeadingFromPosition());
  };
  const syncActiveFromLocation = () => {
    setActive(activeHeadingFromHash() || activeHeadingFromPosition());
  };

  syncActiveFromLocation();
  addEventListener("hashchange", syncActiveFromLocation);

  let activeScrollFrame = 0;
  addEventListener(
    "scroll",
    () => {
      if (activeScrollFrame) return;
      activeScrollFrame = requestAnimationFrame(() => {
        activeScrollFrame = 0;
        syncActiveFromPosition();
      });
    },
    { passive: true },
  );
})();
