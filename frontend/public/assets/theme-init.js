// Blocking head bootstrap: choose a theme before the document can paint.
(function () {
  var preference = 'system';
  try {
    var stored = localStorage.getItem('hf-theme');
    if (stored === 'light' || stored === 'dark' || stored === 'system') preference = stored;
  } catch (_) { /* A blocked storage area must not prevent startup. */ }
  var dark = preference === 'dark' || (preference === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
  var theme = dark ? 'dark' : 'light';
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  var meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', dark ? '#171914' : '#fffef7');
})();
