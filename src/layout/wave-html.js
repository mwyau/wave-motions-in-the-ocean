(() => {
  const root = document.documentElement;
  root.dataset.mathSetup = "";
  const themeKey = "wave-theme";
  const themeModes = ["auto", "light", "dark"];
  const themeNames = { auto: "Device", light: "Light", dark: "Dark" };
  const themeToggle = document.querySelector("[data-theme-cycle]");
  const themeButtons = document.querySelectorAll("[data-theme-option]");
  let themeMode = "auto";

  try {
    const saved = localStorage.getItem(themeKey);
    if (themeModes.includes(saved)) themeMode = saved;
  } catch (_) {}

  const applyTheme = () => {
    if (themeMode === "auto") delete root.dataset.theme;
    else root.dataset.theme = themeMode;
    themeButtons.forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.themeOption === themeMode),
      );
    });
    if (themeToggle) {
      themeToggle.setAttribute(
        "aria-label",
        `Theme; current ${themeNames[themeMode]}`,
      );
      themeToggle.title = `Theme: ${themeNames[themeMode]}`;
    }
  };

  themeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const nextMode = button.dataset.themeOption;
      if (!themeModes.includes(nextMode)) return;
      themeMode = nextMode;
      try {
        if (themeMode === "auto") localStorage.removeItem(themeKey);
        else localStorage.setItem(themeKey, themeMode);
      } catch (_) {}
      applyTheme();
    });
  });

  const textSizeKey = "wave-text-size";
  const textSizeActions = ["decrease", "reset", "increase"];
  const textSizeMin = 50;
  const textSizeMax = 200;
  const textSizeStep = 10;
  const textSizeDefault = 100;
  const legacyTextSizes = { small: 90, default: 100, large: 110 };
  const textSizeButtons = document.querySelectorAll("[data-text-size-action]");
  const textSizeToggle = document.querySelector("[data-text-size-toggle]");
  const textSizeValue = document.querySelector("[data-text-size-value]");

  const normalizeTextSize = (value) => {
    const candidate = legacyTextSizes[value] ?? Number(value);
    if (
      Number.isInteger(candidate) &&
      candidate >= textSizeMin &&
      candidate <= textSizeMax &&
      candidate % textSizeStep === 0
    ) {
      return candidate;
    }
    return textSizeDefault;
  };

  let textSizePercent = textSizeDefault;
  try {
    textSizePercent = normalizeTextSize(localStorage.getItem(textSizeKey));
  } catch (_) {}

  const applyTextSize = () => {
    if (textSizePercent === textSizeDefault) {
      root.style.removeProperty("--wave-text-scale");
    } else {
      root.style.setProperty("--wave-text-scale", String(textSizePercent / 100));
    }
    root.style.setProperty("--wave-toolbar-text-size", `"${textSizePercent}%"`);
    textSizeButtons.forEach((button) => {
      const action = button.dataset.textSizeAction;
      if (action === "decrease") button.disabled = textSizePercent <= textSizeMin;
      if (action === "increase") button.disabled = textSizePercent >= textSizeMax;
    });
    if (textSizeValue) textSizeValue.textContent = `${textSizePercent}%`;
    if (textSizeToggle) {
      textSizeToggle.setAttribute(
        "aria-label",
        `Text size; current ${textSizePercent} percent`,
      );
      textSizeToggle.title = `Text size: ${textSizePercent}%`;
    }
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

  textSizeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.textSizeAction;
      if (!textSizeActions.includes(action)) return;
      const anchor = visibleContentAnchor();
      if (action === "decrease") {
        textSizePercent = Math.max(textSizeMin, textSizePercent - textSizeStep);
      } else if (action === "increase") {
        textSizePercent = Math.min(textSizeMax, textSizePercent + textSizeStep);
      } else {
        textSizePercent = textSizeDefault;
      }
      try {
        if (textSizePercent === textSizeDefault) localStorage.removeItem(textSizeKey);
        else localStorage.setItem(textSizeKey, String(textSizePercent));
      } catch (_) {}
      applyTextSize();
      requestAnimationFrame(() => restoreContentAnchor(anchor));
    });
  });

  applyTheme();
  applyTextSize();

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
  let mathUrlOverride = mathModes.includes(requestedMathMode) ? requestedMathMode : null;
  const bootstrapMathMode = mathModes.includes(root.dataset.initialMath)
    ? root.dataset.initialMath
    : savedMathMode;
  const initialMathMode = mathUrlOverride || bootstrapMathMode;
  let mathMode = initialMathMode;
  const mathCycle = document.querySelector("[data-math-cycle]");
  const mathLabels = document.querySelectorAll("[data-math-label]");
  const mathRenderers = document.querySelectorAll("[data-math-renderer]");
  const readerPagePattern = /^(?:index|chapter\d+|references)\.html$/;

  const showMathMode = (mode) => {
    mathRenderers.forEach((node) => {
      node.hidden = node.dataset.mathRenderer !== mode;
    });
  };

  const syncMathControl = () => {
    if (!mathCycle) return;
    const nextMode = mathModes[(mathModes.indexOf(mathMode) + 1) % mathModes.length];
    mathLabels.forEach((label) => {
      label.textContent = mathNames[mathMode];
    });
    mathCycle.setAttribute(
      "aria-label",
      `Rendering: ${mathNames[mathMode]}; switch to ${mathNames[nextMode]}`,
    );
    mathCycle.title = `Rendering: ${mathNames[mathMode]}`;
  };

  const markMathReady = (mode) => {
    root.dataset.mathRenderer = mode;
    root.removeAttribute("data-math-pending");
    root.dataset.mathReady = "";
    root.dispatchEvent(new Event("wave-math-ready"));
  };

  const updateReaderLinks = () => {
    const linkMathMode =
      mathUrlOverride || (savedMathMode === "mathml" ? "mathml" : null);
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
      if (linkMathMode) url.searchParams.set("math", linkMathMode);
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
    if (!pending.length) return Promise.resolve(true);
    const mathJax = window.MathJax;
    if (!mathJax || typeof mathJax.typesetPromise !== "function") {
      return Promise.resolve(false);
    }
    const typeset = () => {
      try {
        return Promise.resolve(mathJax.typesetPromise(pending)).then(
          () => pending.every((node) => node.querySelector('mjx-container[jax="CHTML"]')),
          () => false,
        );
      } catch (_) {
        return Promise.resolve(false);
      }
    };
    if (mathJax.startup?.promise) {
      return Promise.resolve(mathJax.startup.promise).then(typeset, () => false);
    }
    return typeset();
  };

  const persistMathMode = (mode) => {
    try {
      if (mode === "mathml") localStorage.setItem(mathKey, mode);
      else localStorage.removeItem(mathKey);
      savedMathMode = mode;
    } catch (_) {}
  };

  const applyMathMode = (
    target,
    { persist = false, updateUrl = false, initial = false } = {},
  ) => {
    if (target === "mathml") {
      mathMode = target;
      showMathMode(mathMode);
      syncMathControl();
      markMathReady(mathMode);
      if (persist) persistMathMode(mathMode);
      if (updateUrl) updateReaderUrl();
      updateReaderLinks();
      return Promise.resolve(true);
    }
    if (initial && root.hasAttribute("data-math-fallback")) {
      mathMode = "mathml";
      showMathMode(mathMode);
      syncMathControl();
      markMathReady(mathMode);
      updateReaderLinks();
      return Promise.resolve(false);
    }
    return typesetMathJaxIfNeeded().then((ready) => {
      mathMode = ready ? "mathjax" : "mathml";
      showMathMode(mathMode);
      syncMathControl();
      markMathReady(mathMode);
      if (ready && persist) persistMathMode(mathMode);
      if (updateUrl) updateReaderUrl();
      updateReaderLinks();
      return ready;
    });
  };

  syncMathControl();
  if (initialMathMode === "mathml") showMathMode("mathml");
  if (mathCycle) {
    mathCycle.addEventListener("click", () => {
      const anchor = visibleContentAnchor();
      const nextMode = mathModes[(mathModes.indexOf(mathMode) + 1) % mathModes.length];
      mathUrlOverride = null;
      applyMathMode(nextMode, { persist: true, updateUrl: true }).then(() => {
        requestAnimationFrame(() => restoreContentAnchor(anchor));
      });
    });
  }
  const initialMathReady = applyMathMode(initialMathMode, { initial: true });

  const copyText = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (_) {
      const field = document.createElement("textarea");
      field.value = text;
      field.setAttribute("readonly", "");
      field.style.position = "fixed";
      field.style.opacity = "0";
      document.body.append(field);
      field.select();
      let copied = false;
      try {
        copied = document.execCommand("copy");
      } catch (_) {}
      field.remove();
      return copied;
    }
  };

  const installPermalinks = () => {
    document.querySelectorAll("main h1[id], main h2[id]").forEach((heading) => {
      if (heading.querySelector(":scope > .heading-permalink")) return;
      heading.dataset.readerTitle = heading.textContent.trim();
      const link = document.createElement("a");
      link.className = "heading-permalink";
      link.href = `#${encodeURIComponent(heading.id)}`;
      link.textContent = "#";
      link.setAttribute("aria-label", `Permalink to ${heading.dataset.readerTitle}`);
      link.title = "Permalink";

      const copy = document.createElement("button");
      copy.type = "button";
      copy.className = "heading-copy-link";
      copy.textContent = "Copy link";
      copy.setAttribute("aria-label", `Copy link to ${heading.dataset.readerTitle}`);
      copy.addEventListener("click", async () => {
        const url = new URL(location.href);
        url.hash = heading.id;
        if (!(await copyText(url.href))) return;
        copy.textContent = "Copied";
        window.setTimeout(() => {
          copy.textContent = "Copy link";
        }, 1200);
      });

      heading.append(link, copy);
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
  const appearancePanel = document.querySelector("#appearance-settings");
  const textSizePanel = document.querySelector("#text-size-settings");

  const settingsIsOpen = (panel) => {
    if (!panel) return false;
    return supportsPopover ? panel.matches(":popover-open") : !panel.hidden;
  };

  const syncSettingsExpanded = (panel, toggle) => {
    if (toggle) toggle.setAttribute("aria-expanded", String(settingsIsOpen(panel)));
  };

  const positionSettings = (panel, toggle) => {
    if (!panel || !toggle) return;
    const gutter = 16;
    const toggleRect = toggle.getBoundingClientRect();
    const panelWidth = Number.parseFloat(getComputedStyle(panel).width) || 288;
    const maxLeft = Math.max(gutter, innerWidth - panelWidth - gutter);
    const left = Math.min(
      Math.max(toggleRect.right - panelWidth, gutter),
      maxLeft,
    );
    const top = Math.max(gutter, toggleRect.bottom + 8);
    panel.style.setProperty("--appearance-left", `${left}px`);
    panel.style.setProperty("--appearance-top", `${top}px`);
  };

  const installSettingsPopover = (panel, toggle) => {
    if (!panel || !toggle) return;
    if (supportsPopover) {
      panel.hidden = false;
      panel.addEventListener("beforetoggle", (event) => {
        if (event.newState === "open") positionSettings(panel, toggle);
        requestAnimationFrame(() => syncSettingsExpanded(panel, toggle));
      });
      panel.addEventListener("toggle", () => syncSettingsExpanded(panel, toggle));
    } else {
      toggle.addEventListener("click", () => {
        const open = panel.hidden;
        panel.hidden = !open;
        if (open) positionSettings(panel, toggle);
        syncSettingsExpanded(panel, toggle);
      });
    }
    syncSettingsExpanded(panel, toggle);
  };

  installSettingsPopover(appearancePanel, themeToggle);
  installSettingsPopover(textSizePanel, textSizeToggle);

  const updateAnchorOffset = () => {
    if (!readerHeader) return;
    const headerHeight = readerHeader.getBoundingClientRect().height;
    if (!Number.isFinite(headerHeight) || headerHeight <= 0) return;
    const rootFontSize = Number.parseFloat(getComputedStyle(root).fontSize) || 16;
    const gutter = Math.max(12, Math.min(24, Math.round(rootFontSize * 0.75)));
    root.style.setProperty(
      "--wave-anchor-offset",
      `${Math.ceil(headerHeight + gutter)}px`,
    );
  };

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
    root.dataset.tocReady = "";

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
      tocPanel.hidden = true;
      tocToggle.addEventListener("click", () => {
        location.href = "index.html";
      });
    }
  }

  const updateContentsLayout = () => {
    updateAnchorOffset();
    updateContentsTop();
    if (settingsIsOpen(appearancePanel)) positionSettings(appearancePanel, themeToggle);
    if (settingsIsOpen(textSizePanel)) positionSettings(textSizePanel, textSizeToggle);
    updateContentsMode();
    if (tocPanel?.matches(":popover-open")) positionContents();
  };
  updateContentsLayout();
  addEventListener("resize", updateContentsLayout, { passive: true });
  if (readerHeader && "ResizeObserver" in window) {
    new ResizeObserver(() => updateContentsLayout()).observe(readerHeader);
  }

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

  const fragmentTarget = () => {
    let id = "";
    try {
      id = decodeURIComponent(location.hash.slice(1));
    } catch (_) {}
    return id ? document.getElementById(id) : null;
  };

  const alignFragmentTarget = () => {
    const target = fragmentTarget();
    if (!target || !/^H[1-3]$/.test(target.tagName)) return;
    const offset = Number.parseFloat(getComputedStyle(target).scrollMarginTop);
    if (!Number.isFinite(offset)) return;
    const delta = target.getBoundingClientRect().top - offset;
    if (Math.abs(delta) > 1) scrollBy(0, delta);
  };

  const alignFragmentAfterLayout = () => {
    requestAnimationFrame(() => {
      updateContentsLayout();
      requestAnimationFrame(alignFragmentTarget);
    });
  };

  initialMathReady.then(alignFragmentAfterLayout);

  const links = new Map();
  document.querySelectorAll("a[data-section-link]").forEach((link) => {
    const id = link.dataset.sectionLink;
    if (!links.has(id)) links.set(id, []);
    links.get(id).push(link);
  });
  if (!links.size) return;

  const headings = Array.from(document.querySelectorAll("main h1[id], main h2[id]")).filter(
    (heading) => links.has(heading.id),
  );
  if (!headings.length) return;

  const readerContextTitle = document.querySelector(".reader-context-title");
  const readerContextSeparator = document.querySelector(".reader-context-separator");
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
      const title = heading?.dataset.readerTitle || defaultReaderTitle;
      readerContextTitle.textContent = title;
      readerContextTitle.hidden = !title;
      if (readerContextSeparator) readerContextSeparator.hidden = !title;
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
    const threshold =
      (Number.parseFloat(getComputedStyle(headings[0]).scrollMarginTop) || 0) + 2;
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
  addEventListener("hashchange", () => {
    syncActiveFromLocation();
    alignFragmentAfterLayout();
  });

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
