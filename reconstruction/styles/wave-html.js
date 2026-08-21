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
    document.querySelectorAll("[data-theme-select]").forEach((select) => {
      select.value = mode;
    });
  };

  document.querySelectorAll("[data-theme-select]").forEach((select) => {
    select.addEventListener("change", () => {
      if (!modes.includes(select.value)) return;
      mode = select.value;
      try {
        if (mode === "auto") localStorage.removeItem(key);
        else localStorage.setItem(key, mode);
      } catch (_) {}
      apply();
    });
  });
  apply();
})();
