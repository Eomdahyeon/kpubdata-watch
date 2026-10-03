"""Product-surface quality gate over every built page (#89).

These checks run on the whole demo site, not on one template, so a new page
cannot slip past them: one h1 and no skipped heading level, a skip link to
`#main`, exactly one current page in the navigation, every status shown as an
icon plus text, history marks with an accessible label, no stored relative
time, and the stylesheet that carries the reduced-motion rule on every page.
Colour comes only from the token file: no raw hex anywhere else under `web/`.

What needs a real browser (no page-level horizontal scroll at 390px, reduced
motion honoured) is checked by `scripts/check_product_surface.py` in CI.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "build_demo.py"
WEB = REPO_ROOT / "src" / "kpubdata_watch" / "web"
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RELATIVE_TIME = re.compile(r"\b\d+\s*(?:s|m|h|d|min|mins|hours?|days?)\s+ago\b|분 전|시간 전|일 전")


class Outline(HTMLParser):
    """Collect heading levels, the skip link target, `main` ids and current-page marks."""

    def __init__(self) -> None:
        super().__init__()
        self.headings: list[int] = []
        self.skip_targets: list[str] = []
        self.main_ids: list[str] = []
        self.current_in_nav = 0
        self._nav_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "a" and attributes.get("class") == "skip-link":
            self.skip_targets.append(attributes.get("href") or "")
        if tag == "main":
            self.main_ids.append(attributes.get("id") or "")
        if tag == "nav" and attributes.get("class") == "primary-nav":
            self._nav_depth = 1
        elif tag == "nav" and self._nav_depth:
            self._nav_depth += 1
        if self._nav_depth and attributes.get("aria-current") == "page":
            self.current_in_nav += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "nav" and self._nav_depth:
            self._nav_depth -= 1


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    spec = importlib.util.spec_from_file_location("build_demo", SCRIPT)
    assert spec is not None and spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out: Path = module.build(output_dir=tmp_path_factory.mktemp("site") / "_site")
    return out


@pytest.fixture(scope="module")
def pages(site: Path) -> dict[str, str]:
    return {
        str(path.relative_to(site)): path.read_text(encoding="utf-8")
        for path in sorted(site.rglob("index.html"))
    }


def outline(html: str) -> Outline:
    parser = Outline()
    parser.feed(html)
    return parser


STATUS_OPEN = re.compile(r'<span class="(?:status-badge|check-status) ')
STATUS_FULL = re.compile(
    r'<span class="(?:status-badge|check-status) [\w-]+">'
    r'<span class="status-icon" aria-hidden="true">([^<]+)</span>'
    r'<span class="status-text">([^<]+)</span></span>'
)


def heading_problems(html: str) -> list[str]:
    levels = outline(html).headings
    problems = []
    if levels.count(1) != 1 or (levels and levels[0] != 1):
        problems.append(f"expected one h1 first, got {levels}")
    problems += [f"h{a} then h{b}" for a, b in zip(levels, levels[1:], strict=False) if b > a + 1]
    return problems


def landmark_problems(html: str) -> list[str]:
    page = outline(html)
    problems = []
    if page.skip_targets != ["#main"]:
        problems.append(f"skip link targets {page.skip_targets}")
    if page.main_ids != ["main"]:
        problems.append(f"main ids {page.main_ids}")
    if page.current_in_nav != 1:
        problems.append(f"{page.current_in_nav} current items in the navigation")
    return problems


def status_problems(html: str) -> list[str]:
    complete = STATUS_FULL.findall(html)
    problems = []
    if len(STATUS_OPEN.findall(html)) != len(complete):
        problems.append("a status without both icon and text")
    problems += [
        f"empty icon or text in {pair}" for pair in complete if not all(map(str.strip, pair))
    ]
    problems += [
        f"history mark without a label: {mark}"
        for mark in re.findall(r'<li class="history-day [^"]+"[^>]*>', html)
        if 'aria-label="' not in mark
    ]
    return problems


def time_problems(html: str) -> list[str]:
    return [f"relative time {match.group(0)!r}" for match in RELATIVE_TIME.finditer(html)]


def test_the_gate_sees_every_page(pages: dict[str, str]) -> None:
    assert len(pages) == 1 + 1 + 15 + 1 + 7 + 1 + 2


@pytest.mark.parametrize(
    "check", [heading_problems, landmark_problems, status_problems, time_problems]
)
def test_every_page_passes(pages: dict[str, str], check: object) -> None:
    assert callable(check)
    failures = {name: check(html) for name, html in pages.items()}
    assert {name: found for name, found in failures.items() if found} == {}


NAV_OK = '<nav class="primary-nav"><a aria-current="page">x</a></nav>'
GOOD = f'<a class="skip-link" href="#main">s</a>{NAV_OK}<main id="main"><h1>t</h1><h2>u</h2></main>'


@pytest.mark.parametrize(
    ("check", "html"),
    [
        (heading_problems, "<h1>a</h1><h3>b</h3>"),
        (heading_problems, "<h2>a</h2><h1>b</h1>"),
        (heading_problems, "<h1>a</h1><h1>b</h1>"),
        (landmark_problems, GOOD.replace('href="#main"', 'href="#top"')),
        (landmark_problems, GOOD.replace('id="main"', 'id="content"')),
        (landmark_problems, GOOD.replace(NAV_OK, '<nav class="primary-nav"><a>x</a></nav>')),
        (
            status_problems,
            '<span class="status-badge status-critical"><span class="status-icon" aria-hidden="true">✕</span></span>',
        ),
        (status_problems, '<li class="history-day status-critical" tabindex="0">x</li>'),
        (time_problems, "<p>Checked 3m ago</p>"),
        (time_problems, "<p>5분 전 확인</p>"),
    ],
)
def test_each_check_catches_a_violation(check: object, html: str) -> None:
    assert callable(check)
    assert check(html), "the check did not report a deliberate violation"


def test_a_compliant_page_passes_every_check() -> None:
    for check in (heading_problems, landmark_problems, status_problems, time_problems):
        assert check(GOOD) == [], check


def test_every_page_links_the_stylesheet_with_the_reduced_motion_rule(
    pages: dict[str, str],
) -> None:
    css = (WEB / "static" / "components.css").read_text(encoding="utf-8")
    assert "@media (prefers-reduced-motion: reduce)" in css
    for name, html in pages.items():
        assert "static/components.css" in html, name


def test_no_raw_hex_colour_outside_the_token_file() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", str(WEB.relative_to(REPO_ROOT))],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert tracked, "git ls-files found nothing under web/"
    checked = 0
    for name in tracked:
        path = REPO_ROOT / name
        if path.name == "brand-v2.css" or path.suffix in {".svg", ".py", ".png", ".ico"}:
            continue
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        assert not HEX_COLOR.search(text), f"{name} has a raw hex colour; use var(--...)"
        checked += 1
    assert checked >= 10
