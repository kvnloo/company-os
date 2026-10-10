/* Local visual preference only. No network, clock, synthetic activity or data. */
(() => {
  const root = document.documentElement;
  const buttons = [...document.querySelectorAll('.hud-theme-switch [data-theme]')];
  const key = 'company-os.style-preview.theme';
  const apply = (value) => {
    const theme = value === 'light' ? 'light' : 'dark';
    root.dataset.hudTheme = theme;
    for (const button of buttons) {
      button.setAttribute('aria-pressed', String(button.dataset.theme === theme));
    }
  };
  let preference = 'dark';
  try { preference = localStorage.getItem(key); } catch { /* Storage can be disabled. */ }
  apply(preference);
  for (const button of buttons) {
    button.addEventListener('click', () => {
      apply(button.dataset.theme);
      try { localStorage.setItem(key, root.dataset.hudTheme); } catch { /* In-memory choice still works. */ }
    });
  }
})();
