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
  const chapterContext = document.querySelector("[data-chapter-context]");
  const currentSection = document.querySelector("[data-current-section]");
  const globalContents = document.querySelector("[data-global-contents]");
  const tocToggle = document.querySelector("[data-toc-toggle]");
  const tocPanel = document.querySelector("#chapter-contents");
  const tocNav = document.querySelector("[data-chapter-toc]");
  const tocChapter = document.querySelector("[data-toc-chapter]");
  const tocTitle = document.querySelector("[data-toc-title]");
  const titleMatch = document.title.match(/^(Chapter\s+\d+)\s+·\s+(.*?)\s+—\s+/);
  const headings = Array.from(document.querySelectorAll("main h2[id]"));
  const supportsPopover = "showPopover" in HTMLElement.prototype;

  if (!titleMatch || !context || !chapterContext || !currentSection) return;

  const chapterLabel = titleMatch[1];
  const chapterTitle = titleMatch[2];
  chapterContext.textContent = chapterLabel;
  currentSection.textContent = chapterTitle;
  context.hidden = false;

  if (!supportsPopover || !headings.length || !tocPanel || !tocNav || !tocToggle || !globalContents) {
    return;
  }

  tocPanel.hidden = false;
  globalContents.hidden = true;
  tocToggle.hidden = false;
  if (tocChapter) tocChapter.textContent = chapterLabel;
  if (tocTitle) tocTitle.textContent = chapterTitle;

  const list = document.createElement("ol");
  const links = new Map();
  headings.forEach((heading) => {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = `#${heading.id}`;
    link.textContent = heading.textContent.trim();
    link.dataset.sectionLink = heading.id;
    item.append(link);
    list.append(item);
    links.set(heading.id, link);
  });
  tocNav.replaceChildren(list);

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

  const hashId = decodeURIComponent(location.hash.slice(1));
  const hashHeading = headings.find((heading) => heading.id === hashId);
  if (hashHeading) {
    setActive(hashHeading);
  } else {
    const initial = headings.filter((heading) => heading.getBoundingClientRect().top <= innerHeight * 0.25).at(-1);
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

  tocNav.addEventListener("click", (event) => {
    if (event.target.closest("a[href^='#']") && tocPanel.matches(":popover-open")) {
      tocPanel.hidePopover();
    }
  });

  const wideScreen = matchMedia("(min-width: 1100px)");
  const tocPreferenceKey = "wave-chapter-contents";
  tocPanel.addEventListener("toggle", (event) => {
    if (!wideScreen.matches) return;
    try {
      localStorage.setItem(tocPreferenceKey, event.newState === "open" ? "open" : "closed");
    } catch (_) {}
  });

  try {
    if (wideScreen.matches && localStorage.getItem(tocPreferenceKey) === "open") {
      tocPanel.showPopover();
    }
  } catch (_) {}
})();
