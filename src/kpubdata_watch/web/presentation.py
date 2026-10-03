"""Presentation vocabulary shared by every Watch page (#73).

The health labels and icons, the Change glyph and the Jinja environment live
here so that the fixture demo (`scripts/build_demo.py`) and the server-rendered
service use the same primitives from `templates/components/primitives.html`.
A health state always shows its icon and text label together with its colour,
never colour alone (docs/UI.md, PRD §53).
"""

from __future__ import annotations

import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, pass_context, select_autoescape
from jinja2.runtime import Context

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

HEALTH_ORDER = ("healthy", "degraded", "critical", "unknown")
HEALTH_META: dict[str, dict[str, str]] = {
    "healthy": {"label": "Healthy", "icon": "●"},
    "degraded": {"label": "Degraded", "icon": "▲"},
    "critical": {"label": "Critical", "icon": "✕"},
    "unknown": {"label": "Unknown", "icon": "?"},
}
# A check result (pass, warn, fail, unknown, not_applicable) borrows the health
# colour it implies and always carries its own icon and label (#86).
CHECK_META: dict[str, dict[str, str]] = {
    "pass": {"label": "Pass", "icon": "●", "tone": "healthy"},
    "warn": {"label": "Warn", "icon": "▲", "tone": "degraded"},
    "fail": {"label": "Fail", "icon": "✕", "tone": "critical"},
    "unknown": {"label": "Unknown", "icon": "?", "tone": "unknown"},
    "not_applicable": {"label": "Not applicable", "icon": "–", "tone": "neutral"},
}
CHECK_LABELS = {
    "availability": "Availability",
    "freshness": "Freshness",
    "contract": "Contract",
    "quality": "Quality",
}
# The check order the matrix and the catalog's Checks column always use (#110);
# matches `kpubdata_watch.api.read_models.public.CHECK_NAMES`.
CHECK_NAMES: tuple[str, ...] = ("availability", "freshness", "contract", "quality")
# A one-letter abbreviation for the matrix (#110): a full name always comes with it
# (the cell's aria-label/title, or the column header), so the letter is never the
# only way to tell the checks apart.
CHECK_ABBR: dict[str, str] = {
    "availability": "A",
    "freshness": "F",
    "contract": "C",
    "quality": "Q",
}
# Incident severity -> the health tone its badge uses; `info` stays neutral (#87).
SEVERITY_TONE: dict[str, str | None] = {"critical": "critical", "warning": "degraded", "info": None}
SEVERITY_LABELS = {"critical": "Critical", "warning": "Warning", "info": "Info"}
INCIDENT_STATUS_LABELS = {
    "open": "Open",
    "ongoing": "Ongoing",
    "resolved": "Resolved",
    "false_positive": "False positive",
}
# A Change is informational: the neutral "info" glyph, never a health colour
# (PRD §46, §53).
CHANGE_ICON = "ⓘ"

# The product navigation (#83, #109): (key, label, path below the site root).
# Overview answers "can this be used right now"; History answers "how reliable
# has this been" over the last 30 days (ADR 0013). History sits right after
# Overview because both answer a question about every dataset at once, before
# the per-entity lists.
NAV_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("overview", "Overview", ""),
    ("history", "History", "history/"),
    ("datasets", "Datasets", "datasets/"),
    ("changes", "Changes", "changes/"),
    ("incidents", "Incidents", "incidents/"),
)
# Pages that take an identifier live one directory deeper.
_ENTITY_PATHS = {"dataset": "datasets/{}/", "incident": "incidents/{}/", "change": "changes/{}/"}
_PAGE_PATHS = {key: path for key, _, path in NAV_ITEMS}

KST = ZoneInfo("Asia/Seoul")


def normalize_search_text(text: str) -> str:
    """Fold text into the one form the catalog's search filter compares (issue 105).

    Hangul reaches this field in more than one Unicode normalization form: NFC
    (precomposed syllables) from ordinary typing, or NFD (decomposed combining
    jamo) from some IME commit paths, HFS+-originated filenames, and certain
    clipboard round-trips. The two forms render identically but compare unequal
    byte-for-byte, so both the row text built here and the query typed into
    `static/catalog.js` must pass through this same fold (NFC, collapsed
    whitespace, lowercase) before either side is compared.
    """
    collapsed = " ".join(text.split())
    return unicodedata.normalize("NFC", collapsed).lower()


def kst_time(moment: datetime) -> str:
    """`21:12 KST`: a clock time, which stays true however late a static page is read."""
    return moment.astimezone(KST).strftime("%H:%M KST")


def kst_datetime(moment: datetime) -> str:
    """`2026-10-02 21:12:43 KST`: the exact time, for a title or tooltip."""
    return moment.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S KST")


def kst_minute(moment: datetime) -> str:
    """`2026-10-02 21:15 KST`: a date and clock time to the minute."""
    return moment.astimezone(KST).strftime("%Y-%m-%d %H:%M KST")


def _format_minutes(total_minutes: int) -> str:
    """`29m`, `1h 15m`, `1d 1h`: a minute count, at a glance."""
    days, minutes = divmod(max(0, total_minutes), 24 * 60)
    hours, minutes = divmod(minutes, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def duration(start: datetime, end: datetime) -> str:
    """`29m`, `1h 15m`, `1d 1h`: how long something has lasted, at a glance."""
    return _format_minutes(int((end - start).total_seconds() // 60))


def evidence_value(value: Any) -> str:
    """One evidence value as a reader sees it: timestamps in KST, lists joined.

    Evidence (PRD §22) is free-form per detector, so this only makes the common
    shapes readable; the raw JSON stays available on the page.
    """
    if isinstance(value, str):
        try:
            moment = datetime.fromisoformat(value)
        except ValueError:
            return value
        return kst_datetime(moment) if moment.tzinfo is not None else value
    if isinstance(value, list):
        return ", ".join(evidence_value(item) for item in value)
    if isinstance(value, dict):
        return ", ".join(f"{key}: {evidence_value(item)}" for key, item in value.items())
    return str(value)


# evidence_view's mini charts share one 0-300 SVG canvas: every coordinate below
# is computed here, in Python, so `evidence_chart` in primitives.html only draws
# the numbers it is given (issue 111, mirroring the read-model/template split
# section 2 of the owner spec asks for).
_CANVAS_LEFT = 10.0
_CANVAS_RIGHT = 290.0
_CANVAS_WIDTH = _CANVAS_RIGHT - _CANVAS_LEFT
# A pathological `consecutive_failures` still renders, but capped so the bars
# stay legible instead of becoming hairlines; the real count is always in the
# accessible summary and in the existing Observed table below the chart.
_MAX_FAILURE_BARS = 60


def _canvas_x(percent: float) -> float:
    """Map a 0-100 percent position onto the shared evidence-chart canvas."""
    return round(_CANVAS_LEFT + max(0.0, min(100.0, percent)) / 100.0 * _CANVAS_WIDTH, 1)


def _axis_percent(value: float, low: float, high: float) -> float:
    """Where `value` sits between `low` and `high`, as a 0-100 percent, clamped."""
    span = high - low
    if span <= 0:
        return 50.0
    return max(0.0, min(100.0, (value - low) / span * 100.0))


def _seconds_percent(moment: datetime, start: datetime, end: datetime) -> float:
    span = (end - start).total_seconds()
    if span <= 0:
        return 50.0
    return max(0.0, min(100.0, (moment - start).total_seconds() / span * 100.0))


def _as_number(value: Any) -> float | None:
    """`value` as a plain number, rejecting bools (`isinstance(True, int)` is true)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _as_aware_datetime(value: Any) -> datetime | None:
    """An evidence string as a timezone-aware moment, or `None` when it is not one."""
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    return moment if moment.tzinfo is not None else None


def _format_count(value: float) -> str:
    """`10,124` for a whole number, `10,124.50` otherwise -- a reader-facing count."""
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}"


def _signed_percent(value: int) -> str:
    """`+12%`, `−40%`, `0%` -- U+2212 MINUS SIGN, never a hyphen, for the negative case."""
    if value > 0:
        return f"+{value}%"
    if value < 0:
        return f"−{abs(value)}%"
    return "0%"


def _quality_volume_view(
    expected: dict[str, Any], observed: dict[str, Any], tone: str
) -> dict[str, Any] | None:
    """quality/volume: the expected count band, the observed dot, a signed percent.

    The percent is relative to the nearest bound when the observed count falls
    outside `[record_count_min, record_count_max]` (e.g. 40% under the minimum),
    or to the band's midpoint when it falls inside the band (e.g. 2% over the
    middle of an otherwise passing range). Either way it is one number: how far
    the observed count sits from what the band calls normal.
    """
    low = _as_number(expected.get("record_count_min"))
    high = _as_number(expected.get("record_count_max"))
    value = _as_number(observed.get("record_count"))
    if low is None or high is None or value is None or low > high:
        return None
    if value < low:
        base = low
    elif value > high:
        base = high
    else:
        base = (low + high) / 2
    if base == 0:
        return None
    percent = round((value - base) / base * 100)
    percent_label = _signed_percent(percent)

    axis_low = min(low, value)
    axis_high = max(high, value)
    pad = (axis_high - axis_low) * 0.15 or max(abs(axis_high), 1.0) * 0.15
    axis_low -= pad
    axis_high += pad

    band_start = _canvas_x(_axis_percent(low, axis_low, axis_high))
    band_end = _canvas_x(_axis_percent(high, axis_low, axis_high))
    in_band = low <= value <= high
    return {
        "kind": "quality_volume",
        "band_x": band_start,
        "band_width": round(band_end - band_start, 1),
        "dot_x": _canvas_x(_axis_percent(value, axis_low, axis_high)),
        "dot_tone": "healthy" if in_band else tone,
        "percent_label": percent_label,
        "summary": (
            f"Expected {_format_count(low)}–{_format_count(high)} records, observed "
            f"{_format_count(value)} ({percent_label})."
        ),
    }


def _freshness_window_view(
    expected: dict[str, Any], observed: dict[str, Any], generated_at: datetime, tone: str
) -> dict[str, Any] | None:
    """freshness (A): the expected update window, latest data, snapshot time, delay.

    The expected window is `update_at` plus and minus `tolerance_minutes` (the
    incident summaries read it the same way: "20:00 +/- 30 min"). The delay
    segment spans the window's end to the snapshot time -- how long the
    deadline has been missed, measured against `generated_at`, never wall
    clock -- and is omitted when the snapshot arrived before the window closed.
    """
    update_at = _as_aware_datetime(expected.get("update_at"))
    tolerance = _as_number(expected.get("tolerance_minutes"))
    latest = _as_aware_datetime(observed.get("latest_data_at"))
    if update_at is None or tolerance is None or tolerance < 0 or latest is None:
        return None
    window_start = update_at - timedelta(minutes=tolerance)
    window_end = update_at + timedelta(minutes=tolerance)

    axis_start = min(window_start, latest, generated_at)
    axis_end = max(window_end, latest, generated_at)
    span = (axis_end - axis_start).total_seconds()
    if span <= 0:
        return None
    pad = timedelta(seconds=span * 0.08)
    axis_start -= pad
    axis_end += pad

    def pct(moment: datetime) -> float:
        return _canvas_x(_seconds_percent(moment, axis_start, axis_end))

    has_delay = generated_at > window_end
    window_x = pct(window_start)
    window_end_x = pct(window_end)
    return {
        "kind": "freshness_window",
        "window_x": window_x,
        "window_width": round(window_end_x - window_x, 1),
        "delay_x": window_end_x if has_delay else 0.0,
        "delay_width": round(pct(generated_at) - window_end_x, 1) if has_delay else 0.0,
        "latest_x": pct(latest),
        "snapshot_x": pct(generated_at),
        "tone": tone,
        "summary": (
            f"Expected update by {kst_minute(window_end)} (window "
            f"{kst_minute(window_start)}–{kst_minute(window_end)}), latest data at "
            f"{kst_minute(latest)}, snapshot at {kst_minute(generated_at)}."
        ),
        "caption": (
            f"Expected {kst_minute(update_at)} ± {int(tolerance)} min "
            f"· Latest data {kst_minute(latest)} · Snapshot {kst_minute(generated_at)}"
        ),
    }


def _freshness_age_view(
    expected: dict[str, Any], observed: dict[str, Any], generated_at: datetime, tone: str
) -> dict[str, Any] | None:
    """freshness (B): the allowed age against the current age, both against `generated_at`.

    "Current age" is the snapshot time minus `latest_data_at`, never wall clock --
    a static page read long after it was built must show the same bar it showed
    on the day it was built.
    """
    allowed = _as_number(expected.get("max_age_minutes"))
    latest = _as_aware_datetime(observed.get("latest_data_at"))
    if allowed is None or allowed <= 0 or latest is None:
        return None
    current_minutes = max(0, int((generated_at - latest).total_seconds() // 60))
    scale = max(allowed, current_minutes) or 1.0
    over = current_minutes > allowed
    allowed_width = round(allowed / scale * _CANVAS_WIDTH, 1)
    return {
        "kind": "freshness_age",
        "allowed_width": allowed_width,
        "current_width": round(current_minutes / scale * _CANVAS_WIDTH, 1),
        "boundary_x": round(_CANVAS_LEFT + allowed_width, 1),
        "over": over,
        "tone": tone,
        "summary": (
            f"Allowed age {_format_minutes(int(allowed))}, current age "
            f"{_format_minutes(current_minutes)}."
        ),
        "caption": (
            f"Allowed {_format_minutes(int(allowed))} · Current "
            f"{_format_minutes(current_minutes)} (as of {kst_minute(generated_at)})"
        ),
    }


def _availability_view(
    expected: dict[str, Any],
    observed: dict[str, Any],
    timeline: list[Any],
    started_at: Any,
    tone: str,
) -> dict[str, Any] | None:
    """availability: one failure bar per consecutive failure; no healthy probes drawn.

    The last success time is not an evidence key (`expected`/`observed` only
    carry the failing probe); it comes from the incident's own observation
    timeline -- the latest recorded event before `started_at` -- and is shown
    as text only, next to the bars, never as a probe mark (there is no
    timestamp per healthy probe in the data, so none is drawn).
    """
    expected_status = expected.get("http_status")
    observed_status = observed.get("http_status")
    failures = observed.get("consecutive_failures")
    if (
        not isinstance(expected_status, int)
        or isinstance(expected_status, bool)
        or not isinstance(observed_status, int)
        or isinstance(observed_status, bool)
        or not isinstance(failures, int)
        or isinstance(failures, bool)
        or failures < 1
    ):
        return None

    last_success_at: datetime | None = None
    if isinstance(timeline, list) and isinstance(started_at, datetime):
        candidates = [
            event.at
            for event in timeline
            if isinstance(getattr(event, "at", None), datetime) and event.at < started_at
        ]
        if candidates:
            last_success_at = max(candidates)

    count = min(failures, _MAX_FAILURE_BARS)
    step = _CANVAS_WIDTH / count
    bar_width = round(min(18.0, step * 0.7), 1)
    bars = [round(_CANVAS_LEFT + i * step + (step - bar_width) / 2, 1) for i in range(count)]
    summary = (
        f"Expected HTTP {expected_status}, observed HTTP {observed_status} across "
        f"{failures} consecutive failed probe(s)."
    )
    if last_success_at is not None:
        summary += f" Last success at {kst_minute(last_success_at)}."
    return {
        "kind": "availability",
        "bars": bars,
        "bar_width": bar_width,
        "tone": tone,
        "last_success_label": kst_minute(last_success_at) if last_success_at else None,
        "summary": summary,
    }


def _contract_view(expected: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any] | None:
    """contract: added/removed fields, reusing `contract_diff`'s own chips."""
    expected_fields = expected.get("fields")
    observed_fields = observed.get("fields")
    if not isinstance(expected_fields, list) or not isinstance(observed_fields, list):
        return None
    if not all(isinstance(field, str) for field in (*expected_fields, *observed_fields)):
        return None
    expected_set = set(expected_fields)
    observed_set = set(observed_fields)
    added = [field for field in observed_fields if field not in expected_set]
    removed = [field for field in expected_fields if field not in observed_set]
    return {
        "kind": "contract",
        "added": added,
        "removed": removed,
        "summary": f"{len(added)} field(s) added, {len(removed)} field(s) removed.",
    }


def evidence_view(incident: Any, generated_at: datetime) -> dict[str, Any] | None:
    """A template-ready dict for `evidence_chart`, or `None` to fall back to the table.

    Branches on `incident.check` and the evidence keys actually present
    (docs/UI.md "Evidence-based"; ADR 0013 (b)):

    - quality + `record_count_min`/`record_count_max`/`record_count` -> the
      expected band, the observed dot and a signed percent (`_quality_volume_view`).
    - freshness + `update_at`/`tolerance_minutes` -> the expected window, latest
      data, snapshot time and the delay segment (`_freshness_window_view`).
    - freshness + `max_age_minutes` (no `update_at`) -> allowed age vs current
      age (`_freshness_age_view`).
    - availability + `http_status`/`consecutive_failures` -> one failure bar per
      consecutive failure, last success as text (`_availability_view`).
    - contract + `fields` -> added/removed chips (`_contract_view`).
    - anything else, or a required key missing or the wrong type for its shape
      (a reversed band, a non-numeric status, a naive timestamp, ...) -> `None`,
      so the caller keeps the existing Expected/Observed/Difference/Rule table.

    This never guesses a value evidence does not have: a view is built only from
    `incident.evidence.expected`/`observed` (plus `generated_at` for an age or a
    delay, and the timeline for availability's last-success text).
    """
    expected = incident.evidence.expected
    observed = incident.evidence.observed
    if not isinstance(expected, dict) or not isinstance(observed, dict):
        return None
    tone = SEVERITY_TONE.get(incident.severity) or "unknown"
    try:
        if incident.check == "quality":
            return _quality_volume_view(expected, observed, tone)
        if incident.check == "freshness":
            if "update_at" in expected and "tolerance_minutes" in expected:
                return _freshness_window_view(expected, observed, generated_at, tone)
            if "max_age_minutes" in expected:
                return _freshness_age_view(expected, observed, generated_at, tone)
            return None
        if incident.check == "availability":
            return _availability_view(
                expected, observed, incident.timeline, incident.started_at, tone
            )
        if incident.check == "contract":
            return _contract_view(expected, observed)
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        return None
    return None


@pass_context
def asset_url(context: Context, name: str) -> str:
    """A static asset's URL from the page being rendered.

    Every page passes `root`, the relative path back to the site root ("" for the
    overview, "../../" for a dataset detail), so the same templates work at any
    depth and under any base path, such as GitHub Pages' `/kpubdata-watch/`.
    """
    return f"{context.get('root', '')}static/{name}"


@pass_context
def page_url(context: Context, kind: str, identifier: str | None = None) -> str:
    """A product page's URL from the page being rendered, for example `datasets/<id>/`."""
    path = _ENTITY_PATHS[kind].format(identifier) if identifier else _PAGE_PATHS[kind]
    return f"{context.get('root', '')}{path}" or "./"


def environment(templates_dir: Path = TEMPLATES_DIR) -> Environment:
    """Return a Jinja environment with the presentation vocabulary as globals."""
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )
    env.globals.update(
        health_order=HEALTH_ORDER,
        health_meta=HEALTH_META,
        change_icon=CHANGE_ICON,
        check_meta=CHECK_META,
        severity_tone=SEVERITY_TONE,
        severity_labels=SEVERITY_LABELS,
        incident_status_labels=INCIDENT_STATUS_LABELS,
        check_labels=CHECK_LABELS,
        check_names=CHECK_NAMES,
        check_abbr=CHECK_ABBR,
        nav_items=NAV_ITEMS,
        asset_url=asset_url,
        page_url=page_url,
    )
    env.filters.update(
        kst_time=kst_time,
        kst_minute=kst_minute,
        kst_datetime=kst_datetime,
        evidence_value=evidence_value,
    )
    return env
