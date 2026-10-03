"""The dataset catalog at `datasets/` finds any dataset among many (#85).

Every dataset is rendered as a table row with its provider, health, active
issue, latest change and last check, and the whole row leads to its detail
page. Search, provider, health, check and "active issues only" filters run in
the browser (`static/catalog.js`) on data attributes; without JavaScript the
filter form stays hidden and the full list is still there. An empty result
says so. The page stays usable with 150 datasets.
"""

from __future__ import annotations

import importlib.util
import json
import re
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from kpubdata_watch.web.presentation import STATIC_DIR, normalize_search_text

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "build_demo.py"
FIXTURES = REPO_ROOT / "demo" / "fixtures"
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")


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


@pytest.fixture(scope="module")
def catalog(site: Path) -> str:
    return (site / "datasets" / "index.html").read_text(encoding="utf-8")


def rows(html: str) -> list[str]:
    return re.findall(r'<tr class="catalog-row"[^>]*>', html)


def test_the_catalog_lists_every_dataset(catalog: str) -> None:
    assert len(rows(catalog)) == 15
    for column in (
        "Dataset",
        "Provider",
        "Health",
        "Active issue",
        "Latest change",
        "Last checked",
    ):
        assert f'<th scope="col">{column}</th>' in catalog


def test_the_catalog_has_a_checks_column_reusing_the_matrix_cell(catalog: str) -> None:
    # The Checks column header (issue 110) and every row's check_matrix cell —
    # the same macro the Overview matrix uses, per row with its own 4 cells.
    assert (
        '<th scope="col" aria-label="Checks (Availability, Freshness, Contract, '
        'Quality)">Checks</th>' in catalog
    )
    assert catalog.count('class="check-matrix"') == 15
    blocks = catalog.split('<tr class="catalog-row"')[1:]
    rent = next(block for block in blocks if 'data-id="datago.apt_rent"' in block)
    assert 'class="check-cell check-cell-fail"' in rent


def test_the_last_checked_column_is_a_machine_readable_time(catalog: str) -> None:
    """issue 96: the catalog's "Last checked" cell already used `datetime=`, and
    stays that way; this guards the real built page, not just the macro."""
    datasets = json.loads((FIXTURES / "datasets.json").read_text(encoding="utf-8"))
    rent = next(d for d in datasets if d["id"] == "datago.apt_rent")
    blocks = catalog.split('<tr class="catalog-row"')[1:]
    row = next(block for block in blocks if 'data-id="datago.apt_rent"' in block)
    match = re.search(r'<time class="timestamp" datetime="([^"]+)"', row)
    assert match is not None, "Last checked cell has no <time datetime=...>"
    assert datetime.fromisoformat(match.group(1)) == datetime.fromisoformat(rent["last_checked_at"])


def test_each_row_carries_what_the_filters_need(catalog: str) -> None:
    rent = next(row for row in rows(catalog) if 'data-id="datago.apt_rent"' in row)
    assert 'data-provider="molit"' in rent
    assert 'data-health="critical"' in rent
    assert 'data-checks="contract"' in rent
    assert 'data-active="true"' in rent
    assert 'data-search="아파트 전월세 실거래가 국토교통부 datago.apt_rent"' in rent
    healthy = next(row for row in rows(catalog) if 'data-id="visitkorea-tourism"' in row)
    assert 'data-active="false"' in healthy and 'data-checks=""' in healthy


def test_every_rows_search_attribute_is_nfc_normalized(catalog: str) -> None:
    """issue 105: a `data-search` value must already be in one canonical Unicode
    form, or the browser-side filter cannot compare it against a query reliably."""
    values = re.findall(r'data-search="([^"]*)"', catalog)
    assert len(values) == 15
    for value in values:
        assert value == unicodedata.normalize("NFC", value), value


def test_the_search_text_normalizes_a_name_recorded_as_nfd(
    build_demo: ModuleType, tmp_path: Path
) -> None:
    """issue 105: a provider's own record can hold Hangul as decomposed combining
    jamo (NFD) rather than precomposed syllables (NFC); the catalog's own render
    step must still produce one normalized, comparable `data-search` value."""
    name_nfc = "아파트"
    name_nfd = unicodedata.normalize("NFD", name_nfc)
    assert name_nfd != name_nfc, "the fixture must actually exercise two byte forms"

    now = "2026-10-02T21:15:00+09:00"
    checks = {
        kind: {"status": "pass"} for kind in ("availability", "freshness", "contract", "quality")
    }
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    dataset = {
        "id": "nfd.sample",
        "name": name_nfd,
        "provider": {"id": "nfd-provider", "name": name_nfd},
        "category": "sample",
        "health": "healthy",
        "checks": checks,
        "last_checked_at": now,
    }
    days = [
        {"date": (date(2026, 10, 2) - timedelta(days=n)).isoformat(), "health": "healthy"}
        for n in range(29, -1, -1)
    ]
    files = {
        "snapshot": {"generated_at": now},
        "datasets": [dataset],
        "incidents": [],
        "changes": [],
        "histories": [{"dataset_id": "nfd.sample", "days": days}],
    }
    for filename, content in files.items():
        (fixtures / f"{filename}.json").write_text(json.dumps(content), encoding="utf-8")

    out = build_demo.build(output_dir=tmp_path / "_site", fixtures_dir=fixtures)
    html = (out / "datasets" / "index.html").read_text(encoding="utf-8")
    match = re.search(r'data-search="([^"]*)"', html)
    assert match is not None
    rendered = match.group(1)
    assert rendered == unicodedata.normalize("NFC", rendered)
    assert name_nfd not in rendered, "the raw NFD bytes must not survive into the page"
    assert name_nfc.lower() in rendered


def test_normalize_search_text_folds_nfc_nfd_case_and_whitespace() -> None:
    """issue 105: the one function both `build_demo.py` and the browser lean on."""
    nfc = "아파트"
    nfd = unicodedata.normalize("NFD", nfc)
    assert nfd != nfc
    assert normalize_search_text(nfc) == normalize_search_text(nfd)
    assert normalize_search_text("  Datago   Apt   Rent  ") == "datago apt rent"


def test_each_row_leads_to_its_detail_page(site: Path, catalog: str) -> None:
    links = re.findall(r'<a class="row-link" href="([^"]+)"', catalog)
    assert len(links) == 15
    for target in links:
        assert (site / "datasets" / target / "index.html").resolve().exists(), target
    script = (STATIC_DIR / "catalog.js").read_text(encoding="utf-8")
    assert 'row.addEventListener("click"' in script and ".row-link" in script


def test_the_filters_cover_search_provider_health_check_and_active(catalog: str) -> None:
    form = catalog[catalog.index('<form class="catalog-filters"') : catalog.index("</form>")]
    assert " hidden" in form.split(">", 1)[0], "without JavaScript the filters stay hidden"
    assert 'type="search" name="q"' in form
    providers = re.findall(
        r'<option value="([\w-]+)">', form.split('name="provider"')[1].split("</select>")[0]
    )
    assert len(providers) == len(set(providers)) == 10
    for health in ("healthy", "degraded", "critical", "unknown"):
        assert f'<option value="{health}">' in form
    for check in ("availability", "freshness", "contract", "quality"):
        assert f'<option value="{check}">' in form
    assert 'type="checkbox" name="active"' in form


def test_an_empty_result_has_a_message(catalog: str) -> None:
    assert '<p class="empty-state" data-empty hidden>' in catalog
    assert 'aria-live="polite"' in catalog


def test_the_catalog_script_is_linked_and_uses_no_colour(site: Path, catalog: str) -> None:
    assert '<script src="../static/catalog.js" defer></script>' in catalog
    script = (site / "static" / "catalog.js").read_text(encoding="utf-8")
    assert not HEX_COLOR.search(script)
    for attribute in ("data-search", "data-provider", "data-health", "data-checks", "data-active"):
        assert attribute.removeprefix("data-") in script


def test_the_catalog_is_the_current_page_in_the_navigation(catalog: str) -> None:
    assert '<a class="nav-item" href="../datasets/" aria-current="page">Datasets</a>' in catalog


def test_the_overview_now_previews_and_links_to_the_catalog(site: Path) -> None:
    overview = (site / "index.html").read_text(encoding="utf-8")
    assert '<a class="view-all" href="datasets/">View all datasets</a>' in overview


def _many_datasets(directory: Path, count: int) -> None:
    now = "2026-10-02T21:15:00+09:00"
    checks = {
        name: {"status": "pass"} for name in ("availability", "freshness", "contract", "quality")
    }
    datasets: list[dict[str, Any]] = [
        {
            "id": f"bulk.dataset_{n:03d}",
            "name": f"Dataset {n:03d}",
            "provider": {"id": f"p{n % 12}", "name": f"Provider {n % 12}"},
            "category": "bulk",
            "health": "healthy",
            "checks": checks,
            "last_checked_at": now,
        }
        for n in range(count)
    ]
    days = [
        {"date": (date(2026, 10, 2) - timedelta(days=n)).isoformat(), "health": "healthy"}
        for n in range(29, -1, -1)
    ]
    files = {
        "snapshot": {"generated_at": now},
        "datasets": datasets,
        "incidents": [],
        "changes": [],
        "histories": [{"dataset_id": d["id"], "days": days} for d in datasets],
    }
    directory.mkdir()
    for name, content in files.items():
        (directory / f"{name}.json").write_text(json.dumps(content), encoding="utf-8")


def test_the_catalog_handles_150_datasets(build_demo: ModuleType, tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    _many_datasets(fixtures, 150)
    out = build_demo.build(output_dir=tmp_path / "_site", fixtures_dir=fixtures)
    html = (out / "datasets" / "index.html").read_text(encoding="utf-8")
    assert len(rows(html)) == 150
    assert len(html.encode("utf-8")) < 400_000
