"""`scripts/build_demo.py` builds a navigable multi-page product demo (#88).

The output has the Overview, the dataset catalog and a page per dataset, the
incident and change lists and a page per incident and change, plus the static
assets. Every link is relative, so the site works under GitHub Pages'
`/kpubdata-watch/` path, and the build fails rather than publish a page that
links to nothing.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

import pytest

from kpubdata_watch.web.presentation import NAV_ITEMS

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "build_demo.py"
FIXTURES = REPO_ROOT / "demo" / "fixtures"
LINK_ATTR = re.compile(r'(?:href|src)="([^"]+)"')


@pytest.fixture(scope="module")
def build_demo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_demo", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def site(build_demo: ModuleType, tmp_path_factory: pytest.TempPathFactory) -> Path:
    out: Path = build_demo.build(output_dir=tmp_path_factory.mktemp("site") / "_site")
    return out


def _ids(name: str) -> set[str]:
    return {row["id"] for row in json.loads((FIXTURES / f"{name}.json").read_text())}


def test_the_site_has_every_product_page(site: Path) -> None:
    pages = {str(p.relative_to(site)) for p in site.rglob("index.html")}
    expected = {"index.html", "datasets/index.html", "incidents/index.html", "changes/index.html"}
    expected |= {f"datasets/{i}/index.html" for i in _ids("datasets")}
    expected |= {f"incidents/{i}/index.html" for i in _ids("incidents")}
    expected |= {f"changes/{i}/index.html" for i in _ids("changes")}
    assert pages == expected
    for asset in ("brand-v2.css", "components.css", "demo.css", "catalog.js", "favicon.svg"):
        assert (site / "static" / asset).is_file()


def test_every_navigation_item_is_a_link_on_every_page(site: Path) -> None:
    for page in site.rglob("index.html"):
        html = page.read_text(encoding="utf-8")
        assert "is-pending" not in html, page
        nav = html[html.index('<nav class="primary-nav"') : html.index("</nav>")]
        assert nav.count('class="nav-item"') == len(NAV_ITEMS), page


@pytest.mark.parametrize(
    ("path", "label"),
    [
        ("index.html", "Overview"),
        ("datasets/index.html", "Datasets"),
        ("incidents/index.html", "Incidents"),
        ("changes/index.html", "Changes"),
        ("datasets/datago.apt_rent/index.html", "Datasets"),
        ("incidents/inc-contract-apt-rent-001/index.html", "Incidents"),
        ("changes/chg-contract-pps-001/index.html", "Changes"),
    ],
)
def test_the_current_section_is_marked(site: Path, path: str, label: str) -> None:
    html = (site / path).read_text(encoding="utf-8")
    assert re.search(rf'aria-current="page">{label}</a>', html), path


def test_the_incident_list_shows_ongoing_before_resolved(site: Path) -> None:
    html = (site / "incidents" / "index.html").read_text(encoding="utf-8")
    statuses = re.findall(r'<li class="incident-row status-(\w+)"', html)
    assert len(statuses) == len(_ids("incidents"))
    assert statuses.index("resolved") > max(i for i, s in enumerate(statuses) if s == "ongoing")
    for incident in _ids("incidents"):
        assert f'href="../incidents/{incident}/"' in html


def test_the_change_list_links_every_change_newest_first(site: Path) -> None:
    html = (site / "changes" / "index.html").read_text(encoding="utf-8")
    times = re.findall(r'<time class="timestamp" datetime="([^"]+)"', html)
    assert times == sorted(times, reverse=True) and len(times) == len(_ids("changes"))
    for change in _ids("changes"):
        assert f'href="../changes/{change}/"' in html


def test_every_link_is_relative_so_a_base_path_works(site: Path) -> None:
    for page in site.rglob("index.html"):
        for target in LINK_ATTR.findall(page.read_text(encoding="utf-8")):
            assert not target.startswith("/"), f"{page}: {target} is absolute"


def test_the_build_finds_a_broken_internal_link(build_demo: ModuleType, tmp_path: Path) -> None:
    (tmp_path / "ok").mkdir()
    (tmp_path / "ok" / "index.html").write_text('<a href="../">up</a>', encoding="utf-8")
    (tmp_path / "index.html").write_text(
        '<a href="ok/">fine</a><a href="missing/">broken</a><a href="https://x.test/">ext</a>'
        '<a href="#main">anchor</a><a href="docs/">docs</a>',
        encoding="utf-8",
    )
    assert build_demo.broken_links(tmp_path) == ["index.html: missing/"]


def test_the_build_fails_on_a_broken_link(
    build_demo: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(build_demo, "broken_links", lambda _out: ["index.html: missing/"])
    with pytest.raises(SystemExit, match="missing/"):
        build_demo.build(output_dir=tmp_path / "_site")
