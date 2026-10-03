#!/usr/bin/env python3
"""Watch's Brand v2 tokens stay one source, and that source stays Studio's (#68, #72).

KPubData Watch uses the KPubData Studio Brand v2 visual identity unchanged. The
values live in one file, `src/kpubdata_watch/web/static/brand-v2.css`, copied
verbatim from Studio's `src/globals.css`; the rules that use them live in
`docs/VISUAL_IDENTITY.md`. A rule without a gate is a wish, so this is the gate.
CI checks out Studio `main` (a sparse checkout of that one file) and always
passes it as `--studio`, so Watch never silently drifts from Studio's real
source — comparing checked-out CSS text is not a dependency: Watch still never
imports Studio or declares it as a package, which is all that
`scripts/check_independence.py` (PRD D-016) forbids.

Always checked, offline:

- the token file has the light, dark and OS-dark custom-property blocks, and the
  OS-dark block repeats the dark block exactly;
- no brand token (`--brand-*`, `--data-accent*`) resolves to any `--status-*`
  value in either theme, following `var()` references first: brand colour is
  never a status colour;
- the token table in `docs/VISUAL_IDENTITY.md` names the same tokens with the
  same light and dark values as the file;
- the Health table maps Healthy, Degraded, Critical and Unknown each to a
  `--status-*` token the file defines;
- each Health status colour (`--status-success`, `-warning`, `-failure`,
  `-unknown`) reaches the WCAG 2.1 text contrast of 4.5:1 on its own `-subtle`
  background, on `--card` and on `--background`, light and dark (24 pairs), and
  the contrast table in `docs/VISUAL_IDENTITY.md` is exactly what `--contrast`
  prints, so its numbers come from this computation;
- every pinned `kpubdata-studio/blob/<sha>` link under `docs/` names the commit
  the token file was copied from;
- no `.css`, `.html`, `.jinja` or `.j2` file under `ui-lab/` or
  `src/kpubdata_watch/web/` other than the token file declares a token the file
  declares — a prototype or template links the source, it does not fork it.

Checked against Studio (`--studio PATH`, required unless `--contrast`): every
custom property Studio's light, dark and OS-dark blocks define exists in
Watch's copy with the same value. Run this against Studio's `main` to see
whether Studio has moved on; nothing rewrites Watch's copy automatically — copy
the blocks again in a pull request instead.

Usage:
    python scripts/check_brand_tokens.py --studio PATH [--root PATH] [--watch PATH]
    python scripts/check_brand_tokens.py --contrast   # print the contrast table, no --studio needed
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TOKEN_FILE = Path("src") / "kpubdata_watch" / "web" / "static" / "brand-v2.css"
VISUAL_DOC = Path("docs") / "VISUAL_IDENTITY.md"
UI_DIRS = (Path("ui-lab"), Path("src") / "kpubdata_watch" / "web")
UI_SUFFIXES = (".css", ".html", ".jinja", ".j2")

HEALTH_STATES = ("Healthy", "Degraded", "Critical", "Unknown")
TOKEN_TABLE = ("<!-- brand-v2-tokens:start -->", "<!-- brand-v2-tokens:end -->")
HEALTH_TABLE = ("<!-- health-status-map:start -->", "<!-- health-status-map:end -->")
CONTRAST_TABLE = ("<!-- health-contrast:start -->", "<!-- health-contrast:end -->")

# WCAG 2.1 SC 1.4.3: normal-size text needs 4.5:1. Health labels are normal-size text.
TEXT_CONTRAST = 4.5
HEALTH_STATUS = {
    "Healthy": "success",
    "Degraded": "warning",
    "Critical": "failure",
    "Unknown": "unknown",
}
_HEX = re.compile(r"^#([0-9a-f]{6})$")

# The selector of each block, as Studio's globals.css writes it.
BLOCKS = {
    "light": re.compile(r':root\s*,\s*:root\[data-theme="light"\]\s*\{'),
    "dark": re.compile(r':root\[data-theme="dark"\]\s*\{'),
    "os-dark": re.compile(
        r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{\s*:root:not\(\[data-theme\]\)\s*\{"
    ),
}

# Watch's trailing type-scale block: a bare `:root {`, never the compound light selector
# or a bracketed one, so this never matches `light`, `dark` or `os-dark` above (issue 93).
TYPE_SCALE_SELECTOR = re.compile(r":root\s*\{")

# The tokens Studio keeps in its Tailwind `@theme` blocks (`src/globals.css`) that plain
# CSS cannot read, so Watch repeats them verbatim in its trailing `:root` block (issue 93).
# Watch's own type-scale, radius and density tokens there (`--radius`, `--text-section-title`,
# `--density-*`, ...) have no Studio counterpart and stay out of this comparison.
MIRRORED_THEME_TOKENS = (
    "--font-sans",
    "--font-mono",
    "--radius-lg",
    "--radius-xl",
    "--radius-2xl",
    "--text-page-title",
    "--text-page-title--line-height",
    "--text-page-title--font-weight",
    "--text-meta",
    "--text-meta--line-height",
)

_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_DECLARATION = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
_VAR = re.compile(r"^var\((--[\w-]+)\)$")
_SHA = re.compile(r"\b[0-9a-f]{40}\b")
_PINNED_LINK = re.compile(r"kpubdata-studio/blob/([0-9a-f]{7,40}|[\w.-]+)/")
_CELL_CODE = re.compile(r"`([^`]+)`")

Tokens = dict[str, str]


def parse_blocks(css: str) -> dict[str, Tokens]:
    """The custom properties of each block that is present, comments removed."""
    text = _COMMENT.sub("", css)
    blocks: dict[str, Tokens] = {}
    for name, selector in BLOCKS.items():
        match = selector.search(text)
        if match is None:
            continue
        body = text[match.end() : text.index("}", match.end())]
        blocks[name] = {
            key: " ".join(value.split()).lower() for key, value in _DECLARATION.findall(body)
        }
    return blocks


def type_scale_tokens(css: str) -> Tokens:
    """The custom properties of Watch's trailing, bare `:root {` block (issue 93)."""
    text = _COMMENT.sub("", css)
    match = TYPE_SCALE_SELECTOR.search(text)
    if match is None:
        return {}
    body = text[match.end() : text.index("}", match.end())]
    return {key: " ".join(value.split()).lower() for key, value in _DECLARATION.findall(body)}


def resolve(tokens: Tokens, name: str) -> str:
    """The value of a token with `var(--other)` followed within the same block."""
    seen: set[str] = set()
    value = tokens[name]
    while (ref := _VAR.match(value)) and ref.group(1) in tokens and ref.group(1) not in seen:
        seen.add(ref.group(1))
        value = tokens[ref.group(1)]
    return value


def _collisions(theme: str, tokens: Tokens) -> list[str]:
    """Brand tokens whose resolved value equals a status token's, in one block."""
    found: list[str] = []
    status = {resolve(tokens, n): n for n in tokens if n.startswith("--status-")}
    for name in tokens:
        if name.startswith(("--brand-", "--data-accent")):
            value = resolve(tokens, name)
            if value in status:
                found.append(f"{theme}: {name} = {status[value]} ({value})")
    return found


def _rows(doc: str, markers: tuple[str, str]) -> list[list[str]] | None:
    start, end = markers
    if start not in doc or end not in doc:
        return None
    section = doc[doc.index(start) + len(start) : doc.index(end)]
    rows: list[list[str]] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def _code(cell: str) -> str | None:
    match = _CELL_CODE.search(cell)
    return " ".join(match.group(1).split()).lower() if match else None


def table_problems(doc: str, light: Tokens, dark: Tokens) -> list[str]:
    """Differences between the documented token table and the token file."""
    rows = _rows(doc, TOKEN_TABLE)
    if rows is None:
        return [f"the token table markers {TOKEN_TABLE} are missing"]
    documented: dict[str, tuple[str | None, str | None]] = {}
    for cells in rows:
        name = _code(cells[0])
        if name is None or not name.startswith("--") or len(cells) < 3:
            continue
        documented[name] = (_code(cells[1]), _code(cells[2]))
    found: list[str] = []
    for name in sorted(set(light) - set(documented)):
        found.append(f"{name} is in the token file but not in the table")
    for name in sorted(set(documented) - set(light)):
        found.append(f"{name} is in the table but not in the token file")
    for name in sorted(set(documented) & set(light)):
        doc_light, doc_dark = documented[name]
        if doc_light != light[name]:
            found.append(f"{name} light: table {doc_light!r}, token file {light[name]!r}")
        if doc_dark != dark.get(name):
            found.append(f"{name} dark: table {doc_dark!r}, token file {dark.get(name)!r}")
    return found


def health_problems(doc: str, light: Tokens) -> list[str]:
    """Each Health state names one `--status-*` token the file defines."""
    rows = _rows(doc, HEALTH_TABLE)
    if rows is None:
        return [f"the Health table markers {HEALTH_TABLE} are missing"]
    mapped = {cells[0].strip("*` "): _code(cells[1]) for cells in rows if len(cells) >= 2}
    found: list[str] = []
    for state in HEALTH_STATES:
        token = mapped.get(state)
        if token is None:
            found.append(f"Health {state} has no token in the Health table")
        elif not token.startswith("--status-"):
            found.append(f"Health {state} maps to {token}, which is not a --status-* token")
        elif token not in light:
            found.append(f"Health {state} maps to {token}, which the token file does not define")
    return found


def _channel(value: int) -> float:
    c = value / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(colour: str) -> float:
    """WCAG 2.1 relative luminance of a `#rrggbb` colour."""
    match = _HEX.match(colour)
    if match is None:
        raise ValueError(f"not a #rrggbb colour: {colour!r}")
    digits = match.group(1)
    r, g, b = (int(digits[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(first: str, second: str) -> float:
    """WCAG 2.1 contrast ratio, (L1 + 0.05) / (L2 + 0.05) with L1 the lighter."""
    a, b = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def contrast_pairs(blocks: dict[str, Tokens]) -> list[tuple[str, str, str, str, str, str, float]]:
    """(theme, health, fg token, fg, bg token, bg, ratio) for every Health pair."""
    pairs = []
    for theme in ("light", "dark"):
        tokens = blocks.get(theme, {})
        for health, status in HEALTH_STATUS.items():
            fg_name = f"--status-{status}"
            for bg_name in (f"--status-{status}-subtle", "--card", "--background"):
                if fg_name not in tokens or bg_name not in tokens:
                    continue
                fg, bg = resolve(tokens, fg_name), resolve(tokens, bg_name)
                pairs.append((theme, health, fg_name, fg, bg_name, bg, contrast_ratio(fg, bg)))
    return pairs


def contrast_table(blocks: dict[str, Tokens]) -> str:
    """The Markdown table `--contrast` prints and docs/VISUAL_IDENTITY.md carries."""
    lines = [
        "| theme | Health | 글자 | 배경 | 대비 |",
        "|---|---|---|---|---|",
    ]
    for theme, health, fg_name, fg, bg_name, bg, ratio in contrast_pairs(blocks):
        lines.append(
            f"| {theme} | {health} | `{fg_name}` `{fg}` | `{bg_name}` `{bg}` | {ratio:.2f}:1 |"
        )
    return "\n".join(lines)


def contrast_problems(blocks: dict[str, Tokens], doc: str) -> list[str]:
    """Health pairs below 4.5:1, and a documented table that is not the computed one."""
    found: list[str] = []
    expected = 2 * len(HEALTH_STATUS) * 3
    pairs = contrast_pairs(blocks)
    if len(pairs) != expected:
        found.append(f"only {len(pairs)} of {expected} Health contrast pairs could be computed")
    for theme, health, fg_name, fg, bg_name, bg, ratio in pairs:
        if ratio < TEXT_CONTRAST:
            found.append(
                f"{theme} {health}: {fg_name} {fg} on {bg_name} {bg} is {ratio:.2f}:1, "
                f"below {TEXT_CONTRAST}:1"
            )
    start, end = CONTRAST_TABLE
    if start not in doc or end not in doc:
        found.append(f"{VISUAL_DOC}: the contrast table markers {CONTRAST_TABLE} are missing")
    else:
        documented = doc[doc.index(start) + len(start) : doc.index(end)].strip()
        if documented != contrast_table(blocks):
            found.append(
                f"{VISUAL_DOC}: the contrast table is not what `--contrast` prints; paste it again"
            )
    return found


def pin_problems(root: Path, css: str) -> list[str]:
    """Pinned Studio links under docs/ must all name the same commit."""
    match = _SHA.search(css.split("*/", 1)[0])
    if match is None:
        return [f"{TOKEN_FILE} names no 40-character Studio commit in its header"]
    sha = match.group(0)
    found: list[str] = []
    docs = root / "docs"
    for path in sorted(docs.rglob("*.md")) if docs.is_dir() else []:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for ref in _PINNED_LINK.findall(line):
                if _SHA.fullmatch(ref) and ref != sha:
                    where = f"{path.relative_to(root)}:{line_no}"
                    found.append(f"{where}: links Studio at {ref}, tokens are from {sha}")
    doc = root / VISUAL_DOC
    if doc.is_file() and sha not in doc.read_text(encoding="utf-8"):
        found.append(f"{VISUAL_DOC} does not link Studio at {sha}")
    return found


def fork_problems(root: Path, names: set[str]) -> list[str]:
    """UI files other than the token file that declare one of its tokens."""
    found: list[str] = []
    source = (root / TOKEN_FILE).resolve()
    for directory in UI_DIRS:
        base = root / directory
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix not in UI_SUFFIXES or path.resolve() == source:
                continue
            text = _COMMENT.sub("", path.read_text(encoding="utf-8"))
            for name, _ in _DECLARATION.findall(text):
                if name in names:
                    found.append(f"{path.relative_to(root)}: declares {name}")
    return found


def _token_value(text: str, name: str) -> str | None:
    """The first value `name` is declared with anywhere in `text`, comments removed."""
    match = re.search(rf"{re.escape(name)}\s*:\s*([^;]+);", _COMMENT.sub("", text))
    return " ".join(match.group(1).split()).lower() if match else None


def type_scale_drift_problems(ours: Tokens, studio_css: str) -> list[str]:
    """Drift between Watch's type-scale block and the Studio tokens it mirrors (issue 93).

    Studio keeps these in Tailwind `@theme` blocks rather than a `:root` selector, so this
    looks up each mirrored name by declaration rather than reusing `drift_problems`'s
    block-selector matching, which would otherwise find no Studio counterpart at all.
    """
    found: list[str] = []
    for name in MIRRORED_THEME_TOKENS:
        mine, theirs = ours.get(name), _token_value(studio_css, name)
        if mine != theirs:
            found.append(f"type-scale: {name} is {mine!r} here, {theirs!r} in Studio")
    return found


def drift_problems(ours: dict[str, Tokens], studio: dict[str, Tokens]) -> list[str]:
    """Every difference between the token file's blocks and Studio's."""
    found: list[str] = []
    for block in BLOCKS:
        mine, theirs = ours.get(block, {}), studio.get(block)
        if theirs is None:
            found.append(f"{block}: Studio's stylesheet has no such block")
            continue
        for name in sorted(set(mine) | set(theirs)):
            if mine.get(name) != theirs.get(name):
                found.append(
                    f"{block}: {name} is {mine.get(name)!r} here, {theirs.get(name)!r} in Studio"
                )
    return found


def main(argv: list[str] | None = None) -> int:
    """Run every check. Returns 0 when the tokens agree everywhere, 1 otherwise."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--watch", type=Path, default=None, help="Watch's token file (default: --root's copy)"
    )
    parser.add_argument(
        "--studio",
        type=Path,
        default=None,
        help="Studio's src/globals.css to compare against (required unless --contrast)",
    )
    parser.add_argument(
        "--contrast",
        action="store_true",
        help="print the Health contrast table for docs/VISUAL_IDENTITY.md and exit",
    )
    args = parser.parse_args(argv)
    root: Path = args.root.resolve()

    token_file = args.watch if args.watch is not None else root / TOKEN_FILE
    doc_file = root / VISUAL_DOC
    missing = [str(p) for p in (token_file, doc_file) if not p.is_file()]
    if missing:
        for path in missing:
            print(f"  {path} does not exist, so nothing was checked", file=sys.stderr)
        return 1

    css = token_file.read_text(encoding="utf-8")
    blocks = parse_blocks(css)
    if args.contrast:
        print(contrast_table(blocks))
        return 0

    if args.studio is None:
        parser.error("--studio is required (pass --contrast instead to only print the table)")

    doc = doc_file.read_text(encoding="utf-8")
    type_scale = type_scale_tokens(css)
    problems = [f"{TOKEN_FILE}: no {name} block" for name in BLOCKS if name not in blocks]
    if not type_scale:
        problems.append(f"{TOKEN_FILE}: no type-scale block")
    light, dark = blocks.get("light", {}), blocks.get("dark", {})
    if "os-dark" in blocks and blocks["os-dark"] != dark:
        problems.append(f"{TOKEN_FILE}: the OS-dark block differs from the dark block")
    for theme, tokens in blocks.items():
        problems.extend(f"brand colour used as status: {p}" for p in _collisions(theme, tokens))
    problems.extend(f"{VISUAL_DOC}: {p}" for p in table_problems(doc, light, dark))
    problems.extend(f"{VISUAL_DOC}: {p}" for p in health_problems(doc, light))
    problems.extend(contrast_problems(blocks, doc))
    problems.extend(pin_problems(root, css))
    problems.extend(fork_problems(root, set(light) | set(dark)))

    studio_css = args.studio
    if not studio_css.is_file():
        problems.append(f"{studio_css} does not exist, so Studio was not compared")
        compared = ""
    else:
        studio_text = studio_css.read_text(encoding="utf-8")
        studio_blocks = parse_blocks(studio_text)
        drift = drift_problems(blocks, studio_blocks)
        problems.extend(f"drift from Studio: {p}" for p in drift)
        problems.extend(
            f"drift from Studio: {p}" for p in type_scale_drift_problems(type_scale, studio_text)
        )
        compared = f", and they match {studio_css}"

    if problems:
        print("Watch's Brand v2 tokens disagree.\n", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        print(
            "\nStudio Brand v2 is canonical (#68). Copy its blocks again rather than editing"
            "\na value here, and keep docs/VISUAL_IDENTITY.md's tables in step.",
            file=sys.stderr,
        )
        return 1

    theme, health, fg_name, fg, bg_name, bg, ratio = min(
        contrast_pairs(blocks), key=lambda pair: pair[-1]
    )
    print(
        f"Brand v2 tokens agree: {len(light)} light and {len(dark)} dark tokens in "
        f"{TOKEN_FILE} match {VISUAL_DOC}{compared}\n"
        f"Health contrast: {len(contrast_pairs(blocks))} pairs at or above {TEXT_CONTRAST}:1, "
        f"lowest {theme} {health} {fg} on {bg_name} {bg} = {ratio:.2f}:1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
