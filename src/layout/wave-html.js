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
  const devMode = params.get("dev") === "1";
  const mathModes = ["mathjax", "mathml"];
  let mathMode = devMode && params.get("math") === "mathml" ? "mathml" : "mathjax";
  const devMathControls = document.querySelector("[data-dev-math-controls]");
  const mathModeButtons = document.querySelectorAll("[data-math-mode]");
  const mathRenderers = document.querySelectorAll("[data-math-renderer]");
  const readerPagePattern = /^(?:index|chapter\d+|references)\.html$/;

  const updateDevLinks = () => {
    if (!devMode) return;
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
      url.searchParams.set("dev", "1");
      url.searchParams.set("math", mathMode);
      link.setAttribute("href", `${filename}?${url.searchParams.toString()}${url.hash}`);
    });
  };

  const updateDevUrl = () => {
    if (!devMode) return;
    const url = new URL(location.href);
    url.searchParams.set("dev", "1");
    url.searchParams.set("math", mathMode);
    history.replaceState(null, "", `${url.pathname}?${url.searchParams.toString()}${url.hash}`);
  };

  const typesetMathJaxIfNeeded = () => {
    const pending = Array.from(
      document.querySelectorAll('[data-math-renderer="mathjax"]'),
    ).filter((node) => !node.querySelector('mjx-container[jax="CHTML"]'));
    if (!pending.length) return;
    const mathJax = window.MathJax;
    if (!mathJax) return;
    const typeset = () => {
      if (typeof mathJax.typesetPromise === "function") {
        mathJax.typesetPromise(pending).catch(() => {});
      }
    };
    if (mathJax.startup?.promise) mathJax.startup.promise.then(typeset).catch(() => {});
    else typeset();
  };

  const applyMathMode = () => {
    root.dataset.mathRenderer = mathMode;
    mathRenderers.forEach((node) => {
      node.hidden = node.dataset.mathRenderer !== mathMode;
    });
    mathModeButtons.forEach((button) => {
      const active = button.dataset.mathMode === mathMode;
      button.setAttribute("aria-pressed", String(active));
      button.style.fontWeight = active ? "700" : "";
      button.style.textDecoration = active ? "none" : "";
    });
    if (mathMode === "mathjax") typesetMathJaxIfNeeded();
    updateDevUrl();
    updateDevLinks();
  };

  if (devMode && mathRenderers.length) {
    if (devMathControls) devMathControls.hidden = false;
    mathModeButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const mode = button.dataset.mathMode;
        if (!mathModes.includes(mode) || mode === mathMode) return;
        mathMode = mode;
        applyMathMode();
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

  let hashId = "";
  try {
    hashId = decodeURIComponent(location.hash.slice(1));
  } catch (_) {}
  const hashHeading = headings.find((heading) => heading.id === hashId);
  if (hashHeading) {
    setActive(hashHeading);
  } else {
    const initial = headings
      .filter((heading) => heading.getBoundingClientRect().top <= innerHeight * 0.25)
      .at(-1);
    setActive(initial || null);
  }

  const titleBlock = document.querySelector("#title-block-header");
  const observer = new IntersectionObserver(
    (entries) => {
      const entering = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (!entering.length) return;
      const target = entering[0].target;
      setActive(target === titleBlock ? null : target);
    },
    { rootMargin: "-10% 0px -75% 0px", threshold: 0 },
  );
  if (titleBlock) observer.observe(titleBlock);
  headings.forEach((heading) => observer.observe(heading));
})();
