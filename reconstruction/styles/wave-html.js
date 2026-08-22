(() => {
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
