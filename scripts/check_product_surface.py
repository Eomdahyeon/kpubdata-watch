#!/usr/bin/env python3
"""Check the built demo in a real browser (#89).

HTML parsing (tests/unit/web/test_product_surface_gate.py) cannot tell whether a
page scrolls sideways on a phone or whether motion stops when the reader asks
for reduced motion, so this script opens every built page in Chromium through
Playwright and checks:

- at 390px and 1280px wide, the page itself never scrolls sideways (a wide table
  may scroll inside its own container);
- with `prefers-reduced-motion: reduce`, no element keeps a transition or an
  animation;
- the dataset catalog's search matches a query in any Unicode normalization
  form -- NFC and NFD Hangul look identical but compare unequal byte-for-byte
  (issue 105).

`--self-test` builds pages that break every rule above and fails unless all of
them are caught, so CI shows the checks can fail before trusting them to pass.

Playwright is not a project dependency; CI runs this with `uv run --with playwright`.

Usage:
    python scripts/check_product_surface.py SITE_DIR
    python scripts/check_product_surface.py --self-test
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

WIDTHS = (390, 1280)

_SCROLL = "[document.documentElement.scrollWidth, document.documentElement.clientWidth]"
_MOVING = """[...document.querySelectorAll('*')].filter((element) => {
  const style = getComputedStyle(element);
  const transition = parseFloat(style.transitionDuration) > 0;
  const animation = style.animationName !== 'none' && parseFloat(style.animationDuration) > 0;
  return transition || animation;
}).length"""

SELF_TEST_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      .fade { transition: opacity 0.3s ease; }
    </style>
  </head>
  <body>
    <div style="width: 1000px">This block is wider than a phone.</div>
    <p class="fade">This paragraph keeps its transition under reduced motion.</p>
  </body>
</html>
"""

# A catalog page that reproduces the pre-fix behaviour (issue 105): the filter
# compares `data-search` against the query with no Unicode normalization, so an
# NFD query misses a row whose `data-search` was written in NFC. Proves
# `catalog_search_problems` can fail before CI trusts it to pass.
BROKEN_CATALOG_PAGE = """<!doctype html>
<html lang="en">
  <head><meta charset="utf-8" /></head>
  <body>
    <form class="catalog-filters">
      <input type="search" name="q" />
    </form>
    <table>
      <tbody>
        <tr class="catalog-row" data-search="아파트 국토교통부"></tr>
        <tr class="catalog-row" data-search="지하안전정보 국토교통부"></tr>
      </tbody>
    </table>
    <script>
      const form = document.querySelector(".catalog-filters");
      const rows = Array.from(document.querySelectorAll(".catalog-row"));
      function apply() {
        // Deliberately the pre-fix bug: no `.normalize("NFC")` on either side.
        const q = form.elements.q.value.toLowerCase();
        for (const row of rows) {
          row.hidden = q !== "" && !row.dataset.search.toLowerCase().includes(q);
        }
      }
      form.addEventListener("input", apply);
    </script>
  </body>
</html>
"""


def page_problems(page: Any, url: str) -> list[str]:
    """Problems with one page, opened in an existing Playwright page."""
    problems = []
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900})
        page.goto(url)
        scroll_width, client_width = page.evaluate(_SCROLL)
        if scroll_width > client_width:
            problems.append(
                f"{url} at {width}px: the page scrolls sideways ({scroll_width} > {client_width})"
            )
    page.emulate_media(reduced_motion="reduce")
    page.goto(url)
    moving = page.evaluate(_MOVING)
    if moving:
        problems.append(f"{url}: {moving} element(s) still move under reduced motion")
    page.emulate_media(reduced_motion="no-preference")
    return problems


def catalog_search_problems(page: Any, site: Path) -> list[str]:
    """The dataset catalog's search must match a query in any Unicode
    normalization form (issue 105): NFC (precomposed) and NFD (decomposed
    combining jamo) render identically but compare unequal byte-for-byte, so a
    query pasted or typed as NFD has to find the same rows as its NFC form.
    """
    import unicodedata

    catalog = site / "datasets" / "index.html"
    if not catalog.exists():
        return []
    page.goto(catalog.resolve().as_uri())
    query_field = page.query_selector('input[name="q"]')
    if query_field is None:
        return [f"{catalog}: no search input to drive this check"]

    query_nfc = unicodedata.normalize("NFC", "아파트")
    query_nfd = unicodedata.normalize("NFD", "아파트")
    if query_nfc == query_nfd:
        return [f"{catalog}: the fixture word has only one normalization form"]

    def shown_count(value: str) -> int:
        page.fill('input[name="q"]', "")
        page.fill('input[name="q"]', value)
        return page.eval_on_selector_all(
            ".catalog-row", "rows => rows.filter((row) => !row.hidden).length"
        )

    nfc_shown = shown_count(query_nfc)
    nfd_shown = shown_count(query_nfd)
    if nfc_shown == 0:
        return [f"{catalog}: the NFC query matched no rows -- the fixture may have changed"]
    if nfd_shown != nfc_shown:
        return [
            f"{catalog}: NFD query matched {nfd_shown} row(s), NFC matched {nfc_shown} "
            "-- search is not Unicode-normalization-insensitive"
        ]
    return []


def check_site(site: Path) -> list[str]:
    """Open every `index.html` under `site` and collect its problems."""
    from playwright.sync_api import sync_playwright

    pages = sorted(site.rglob("index.html"))
    if not pages:
        return [f"{site}: no pages to check"]
    problems: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        for html in pages:
            problems += page_problems(page, html.resolve().as_uri())
        problems += catalog_search_problems(page, site)
        browser.close()
    return problems


def self_test() -> list[str]:
    """What the checks failed to catch on pages built to break every rule."""
    with tempfile.TemporaryDirectory() as directory:
        site = Path(directory)
        (site / "index.html").write_text(SELF_TEST_PAGE, encoding="utf-8")
        (site / "datasets").mkdir()
        (site / "datasets" / "index.html").write_text(BROKEN_CATALOG_PAGE, encoding="utf-8")
        found = check_site(site)
    missed = []
    if not any("scrolls sideways" in problem for problem in found):
        missed.append("a page that scrolls sideways at 390px was not caught")
    if not any("reduced motion" in problem for problem in found):
        missed.append("a transition under reduced motion was not caught")
    if not any("Unicode-normalization" in problem for problem in found):
        missed.append("a catalog search that ignores Unicode normalization was not caught")
    return missed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("site", nargs="?", type=Path, help="the built demo, e.g. _site")
    parser.add_argument("--self-test", action="store_true", help="prove the checks can fail")
    args = parser.parse_args(argv)

    if args.self_test:
        missed = self_test()
        for problem in missed:
            print(f"self-test: {problem}", file=sys.stderr)
        if missed:
            return 1
        print("self-test: every deliberate violation was caught")
        return 0

    if args.site is None:
        parser.error("give the built site directory, or --self-test")
    problems = check_site(args.site)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"{len(problems)} product-surface problem(s)", file=sys.stderr)
        return 1
    print(f"every page under {args.site} passes at {', '.join(f'{w}px' for w in WIDTHS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
