(() => {
  const root = document.documentElement;
  const themeKey = "wave-theme";
  const themeModes = ["auto", "light", "dark"];
  let themeMode = "auto";

  try {
    const saved = localStorage.getItem(themeKey);
    if (themeModes.includes(saved)) themeMode = saved;
  } catch (_) {}

  const applyTheme = () => {
    if (themeMode === "auto") delete root.dataset.theme;
    else root.dataset.theme = themeMode;
    document.querySelectorAll("[data-theme-select]").forEach((select) => {
      select.value = themeMode;
    });
  };

  document.querySelectorAll("[data-theme-select]").forEach((select) => {
    select.addEventListener("change", () => {
      if (!themeModes.includes(select.value)) return;
      themeMode = select.value;
      try {
        if (themeMode === "auto") localStorage.removeItem(themeKey);
        else localStorage.setItem(themeKey, themeMode);
      } catch (_) {}
      applyTheme();
    });
  });
  applyTheme();

  const context = document.querySelector("[data-reader-context]");
  const currentSection = document.querySelector("[data-current-section]");
  const headings = Array.from(document.querySelectorAll("main h2[id]"));

  if (!context || context.hidden || !currentSection || currentSection.hidden || !headings.length) {
    return;
  }

  const chapterTitle = currentSection.textContent.trim();
  const readerHeader = document.querySelector(".reader-header");
  const tocPanel = document.querySelector("#chapter-contents");
  const tocNav = document.querySelector("[data-chapter-toc]");
  const tocToggle = document.querySelector("[data-toc-toggle]");
  const globalContents = document.querySelector("[data-global-contents]");
  const links = new Map();

  tocNav?.querySelectorAll("a[data-section-link]").forEach((link) => {
    links.set(link.dataset.sectionLink, link);
  });

  const setActive = (heading) => {
    const activeId = heading?.id || "";
    currentSection.textContent = heading ? heading.textContent.trim() : chapterTitle;
    links.forEach((link, id) => {
      const active = id === activeId;
      link.classList.toggle("is-active", active);
      if (active) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
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
    if (initial) setActive(initial);
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

  const supportsPopover = "showPopover" in HTMLElement.prototype;
  if (!supportsPopover || !tocPanel || !tocNav || !tocToggle || !globalContents || !links.size) {
    return;
  }

  tocPanel.hidden = false;
  globalContents.hidden = true;
  tocToggle.hidden = false;

  const compactContents = matchMedia("(max-width: 36rem)");
  const positionContents = () => {
    if (compactContents.matches) return;
    const gutter = 16;
    const headerBottom = readerHeader?.getBoundingClientRect().bottom ?? 0;
    const toggleRect = tocToggle.getBoundingClientRect();
    const panelWidth = parseFloat(getComputedStyle(tocPanel).width) || 304;
    const maxLeft = Math.max(gutter, innerWidth - panelWidth - gutter);
    const left = Math.min(Math.max(toggleRect.left, gutter), maxLeft);
    tocPanel.style.setProperty("--chapter-contents-left", `${left}px`);
    tocPanel.style.setProperty(
      "--chapter-contents-top",
      `${Math.max(gutter, headerBottom + 8)}px`,
    );
  };

  tocPanel.addEventListener("beforetoggle", (event) => {
    if (event.newState === "open") positionContents();
  });

  tocPanel.addEventListener("toggle", (event) => {
    if (event.newState !== "open") return;
    requestAnimationFrame(() => {
      tocNav.querySelector("a.is-active")?.scrollIntoView({ block: "nearest" });
    });
  });

  tocNav.addEventListener("click", (event) => {
    if (event.target.closest("a[href^='#']") && tocPanel.matches(":popover-open")) {
      tocPanel.hidePopover();
    }
  });

  addEventListener(
    "resize",
    () => {
      if (tocPanel.matches(":popover-open")) positionContents();
    },
    { passive: true },
  );
})();
