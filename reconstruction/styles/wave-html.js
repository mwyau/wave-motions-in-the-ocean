(() => {
  const root = document.documentElement;
  const themeKey = "wave-theme";
  const themeModes = ["auto", "light", "dark"];
  const themeNames = { auto: "Auto", light: "Light", dark: "Dark" };
  let themeMode = "auto";

  try {
    const saved = localStorage.getItem(themeKey);
    if (themeModes.includes(saved)) themeMode = saved;
  } catch (_) {}

  const applyTheme = () => {
    if (themeMode === "auto") delete root.dataset.theme;
    else root.dataset.theme = themeMode;
    const nextMode = themeModes[(themeModes.indexOf(themeMode) + 1) % themeModes.length];
    document.querySelectorAll("[data-theme-cycle]").forEach((button) => {
      const label = button.querySelector("[data-theme-label]");
      if (label) label.textContent = themeNames[themeMode];
      button.setAttribute(
        "aria-label",
        `Appearance: ${themeNames[themeMode]}; switch to ${themeNames[nextMode]}`,
      );
      button.title = `Appearance: ${themeNames[themeMode]}`;
    });
  };

  document.querySelectorAll("[data-theme-cycle]").forEach((button) => {
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

  const installPermalinks = () => {
    document.querySelectorAll("main > h1[id], main h2[id]").forEach((heading) => {
      if (heading.querySelector(":scope > .heading-permalink")) return;
      const link = document.createElement("a");
      link.className = "heading-permalink";
      link.href = `#${encodeURIComponent(heading.id)}`;
      link.textContent = "#";
      link.setAttribute("aria-label", `Permalink to ${heading.textContent.trim()}`);
      link.title = "Permalink";
      heading.append(link);
    });
  };
  installPermalinks();

  const tocPanel = document.querySelector("#book-contents");
  const tocToggle = document.querySelector("[data-toc-toggle]");
  const tocRail = document.querySelector("[data-book-toc-rail]");
  const readerHeader = document.querySelector(".reader-header");
  const mainContent = document.querySelector("#main-content");
  const supportsPopover = "showPopover" in HTMLElement.prototype;

  const updateContentsMode = () => {
    if (!tocRail || !tocToggle || !mainContent) return;

    // The stylesheet decides when a persistent rail is a candidate. JavaScript
    // only shows it when it fits entirely in the unused gutter beside this page.
    tocRail.hidden = false;
    tocRail.style.visibility = "hidden";
    tocRail.style.pointerEvents = "none";
    tocRail.style.removeProperty("left");

    const eligible = getComputedStyle(tocRail).display !== "none";
    let showRail = false;
    if (eligible) {
      const contentRects = Array.from(mainContent.children)
        .map((element) => element.getBoundingClientRect())
        .filter((rect) => rect.width > 0 && rect.height > 0);
      const contentLeft = contentRects.length
        ? Math.min(...contentRects.map((rect) => rect.left))
        : mainContent.getBoundingClientRect().left;
      const railWidth = tocRail.getBoundingClientRect().width;
      const rem = Number.parseFloat(getComputedStyle(root).fontSize) || 16;
      const gutter = Math.max(16, rem);
      const gap = 1.5 * rem;
      const left = contentLeft - gap - railWidth;
      showRail = left >= gutter;
      if (showRail) tocRail.style.left = `${left}px`;
    }

    tocRail.hidden = !showRail;
    tocRail.style.removeProperty("visibility");
    tocRail.style.removeProperty("pointer-events");
    if (showRail) tocToggle.style.removeProperty("display");
    else tocToggle.style.setProperty("display", "inline-flex");
  };

  if (tocPanel && tocToggle) {
    if (supportsPopover) {
      tocPanel.hidden = false;
      const compactContents = matchMedia("(max-width: 36rem)");
      const positionContents = () => {
        if (compactContents.matches) return;
        const gutter = 16;
        const headerBottom = readerHeader?.getBoundingClientRect().bottom ?? 0;
        const toggleRect = tocToggle.getBoundingClientRect();
        const panelWidth = parseFloat(getComputedStyle(tocPanel).width) || 320;
        const maxLeft = Math.max(gutter, innerWidth - panelWidth - gutter);
        const left = Math.min(Math.max(toggleRect.left, gutter), maxLeft);
        tocPanel.style.setProperty("--book-contents-left", `${left}px`);
        tocPanel.style.setProperty(
          "--book-contents-top",
          `${Math.max(gutter, headerBottom + 8)}px`,
        );
      };

      tocPanel.addEventListener("beforetoggle", (event) => {
        if (event.newState === "open") positionContents();
      });
      tocPanel.addEventListener("click", (event) => {
        if (event.target.closest("a[href]") && tocPanel.matches(":popover-open")) {
          tocPanel.hidePopover();
        }
      });
      addEventListener(
        "resize",
        () => {
          updateContentsMode();
          if (tocPanel.matches(":popover-open")) positionContents();
        },
        { passive: true },
      );
    } else {
      tocToggle.addEventListener("click", () => {
        location.href = "index.html";
      });
    }
  }
  updateContentsMode();

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
