// Dataset catalog (#85). The table is fully rendered without JavaScript, and each
// dataset name is an ordinary link. This script adds two things: a click anywhere in
// a row opens that dataset (links inside the row keep their own target), and the
// filter form, which hides rows that do not match their data attributes: search,
// provider, health, checks and active. The filter state is kept in the query string
// so a filtered view can be shared.
(() => {
  const form = document.querySelector(".catalog-filters");
  if (!form) return;
  const rows = Array.from(document.querySelectorAll(".catalog-row"));
  const count = document.querySelector("[data-count]");
  const empty = document.querySelector("[data-empty]");

  const params = new URLSearchParams(window.location.search);
  for (const field of form.elements) {
    if (!field.name || !params.has(field.name)) continue;
    if (field.type === "checkbox") field.checked = params.get(field.name) === "1";
    else field.value = params.get(field.name);
  }

  // Hangul can reach this field in more than one Unicode normalization form:
  // NFC (precomposed) from ordinary typing, or NFD (decomposed combining jamo)
  // from some IME commit paths, HFS+-originated filenames, or a clipboard
  // round-trip. The two forms render identically but compare unequal
  // byte-for-byte, so both the query and the row's search text are folded
  // through this same function before either side is compared (issue 105).
  // `data-search` is already NFC and lowercase (`build_demo.py`,
  // `presentation.normalize_search_text`); normalizing again here is
  // defensive, not redundant -- it keeps this script correct even if a
  // row's text ever reaches the page unnormalized.
  function fold(text) {
    return text.normalize("NFC").trim().replace(/\s+/g, " ").toLowerCase();
  }

  function matches(row, filters) {
    const data = row.dataset;
    if (filters.q && !fold(data.search).includes(filters.q)) return false;
    if (filters.provider && data.provider !== filters.provider) return false;
    if (filters.health && data.health !== filters.health) return false;
    if (filters.check && !data.checks.split(" ").includes(filters.check)) return false;
    if (filters.active && data.active !== "true") return false;
    return true;
  }

  function apply() {
    const filters = {
      q: fold(form.elements.q.value),
      provider: form.elements.provider.value,
      health: form.elements.health.value,
      check: form.elements.check.value,
      active: form.elements.active.checked,
    };
    let shown = 0;
    for (const row of rows) {
      const visible = matches(row, filters);
      row.hidden = !visible;
      if (visible) shown += 1;
    }
    count.textContent = String(shown);
    empty.hidden = shown !== 0;

    const next = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value === true) next.set(key, "1");
      else if (value) next.set(key, value);
    }
    const query = next.toString();
    window.history.replaceState(null, "", query ? `?${query}` : window.location.pathname);
  }

  for (const row of rows) {
    row.addEventListener("click", (event) => {
      if (event.target.closest("a, button, input, select, label")) return;
      const link = row.querySelector(".row-link");
      if (link) window.location.href = link.href;
    });
  }

  form.addEventListener("input", apply);
  form.addEventListener("submit", (event) => event.preventDefault());
  form.hidden = false;
  apply();
})();
