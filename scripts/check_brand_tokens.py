#!/usr/bin/env python3
"""Watch's Brand v2 tokens stay one source, and that source stays Studio's (#68).

KPubData Watch uses the KPubData Studio Brand v2 visual identity unchanged. The
values live in one file, `src/kpubdata_watch/web/static/brand-v2.css`, copied
verbatim from Studio's `src/globals.css` at a pinned commit; the rules that use
them live in `docs/VISUAL_IDENTITY.md`. A rule without a gate is a wish, so this
is the gate.

Always checked, offline:

- the token file has the light, dark and OS-dark custom-property blocks, and the
  OS-dark block repeats the dark block exactly;
- the light theme's core roles hold the Brand v2 palette Studio's
  VISUAL_IDENTITY.md section 3.1 names (Brand Blue, Data Cyan, Fresh Mint, Ink,
  Canvas, Surface, Border), so a matching edit to the file and the table alone
  cannot repaint the brand;
- no brand token (`--brand-*`, `--data-accent*`) resolves to any `--status-*`
  value in either theme: brand colour is never a status colour;
- the token table in `docs/VISUAL_IDENTITY.md` names the same tokens with the
  same light and dark values as the file;
- the Health table maps Healthy, Degraded, Critical and Unknown each to a
  `--status-*` token the file defines;
- every pinned `kpubdata-studio/blob/<sha>` link under `docs/` names the commit
  the token file was copied from;
- no `.css`, `.html`, `.jinja` or `.j2` file under `ui-lab/` or
  `src/kpubdata_watch/web/` other than the token file declares a token the file
  declares — a prototype or template links the source, it does not fork it.

Checked when Studio's stylesheet is given (`--studio PATH`, or the
`STUDIO_GLOBALS_CSS` environment variable): its three blocks must equal the token
file's, value for value. Run this against Studio's `main` to see whether Studio
has moved on since the pinned commit.

Usage:
    python scripts/check_brand_tokens.py [--root PATH] [--studio PATH]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TOKEN_FILE = Path("src") / "kpubdata_watch" / "web" / "static" / "brand-v2.css"
VISUAL_DOC = Path("docs") / "VISUAL_IDENTITY.md"
UI_DIRS = (Path("ui-lab"), Path("src") / "kpubdata_watch" / "web")
UI_SUFFIXES = (".css", ".html", ".jinja", ".j2")
STUDIO_ENV = "STUDIO_GLOBALS_CSS"

HEALTH_STATES = ("Healthy", "Degraded", "Critical", "Unknown")
TOKEN_TABLE = ("<!-- brand-v2-tokens:start -->", "<!-- brand-v2-tokens:end -->")
HEALTH_TABLE = ("<!-- health-status-map:start -->", "<!-- health-status-map:end -->")

# Studio VISUAL_IDENTITY.md section 3.1: the Brand v2 palette, light theme.
BRAND_V2_PALETTE = {
    "--brand-primary": "#2563eb",  # Brand Blue
    "--data-accent": "#06b6d4",  # Data Cyan
    "--brand-secondary": "#14b8a6",  # Fresh Mint
    "--foreground": "#172033",  # Ink
    "--background": "#f7f8f3",  # Canvas
    "--card": "#ffffff",  # Surface
    "--border": "#e5e7e2",  # Border
}

# The selector of each block, as Studio's globals.css writes it.
BLOCKS = {
    "light": re.compile(r':root\s*,\s*:root\[data-theme="light"\]\s*\{'),
    "dark": re.compile(r':root\[data-theme="dark"\]\s*\{'),
    "os-dark": re.compile(
        r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{\s*:root:not\(\[data-theme\]\)\s*\{"
    ),
}

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


def resolve(tokens: Tokens, name: str) -> str:
    """The value of a token with `var(--other)` followed within the same block."""
    seen: set[str] = set()
    value = tokens[name]
    while (ref := _VAR.match(value)) and ref.group(1) in tokens and ref.group(1) not in seen:
        seen.add(ref.group(1))
        value = tokens[ref.group(1)]
    return value


def separation_problems(blocks: dict[str, Tokens]) -> list[str]:
    """Brand tokens whose resolved value equals a status token's, per theme."""
    found: list[str] = []
    for theme, tokens in blocks.items():
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


def pin_problems(root: Path, css: str) -> list[str]:
    """Pinned Studio links under docs/ must name the commit the tokens came from."""
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
        "--studio",
        type=Path,
        default=os.environ.get(STUDIO_ENV) or None,
        help=f"Studio's src/globals.css to compare against (default: ${STUDIO_ENV})",
    )
    args = parser.parse_args(argv)
    root: Path = args.root.resolve()

    token_file = root / TOKEN_FILE
    doc_file = root / VISUAL_DOC
    missing = [str(p) for p in (token_file, doc_file) if not p.is_file()]
    if missing:
        for path in missing:
            print(f"  {path} does not exist, so nothing was checked", file=sys.stderr)
        return 1

    css = token_file.read_text(encoding="utf-8")
    doc = doc_file.read_text(encoding="utf-8")
    blocks = parse_blocks(css)
    problems = [f"{TOKEN_FILE}: no {name} block" for name in BLOCKS if name not in blocks]
    light, dark = blocks.get("light", {}), blocks.get("dark", {})
    if "os-dark" in blocks and blocks["os-dark"] != dark:
        problems.append(f"{TOKEN_FILE}: the OS-dark block differs from the dark block")
    problems.extend(
        f"{TOKEN_FILE}: light {name} is {light.get(name)!r}, Brand v2 says {value!r}"
        for name, value in BRAND_V2_PALETTE.items()
        if light.get(name) != value
    )
    problems.extend(f"brand colour used as status: {p}" for p in separation_problems(blocks))
    problems.extend(f"{VISUAL_DOC}: {p}" for p in table_problems(doc, light, dark))
    problems.extend(f"{VISUAL_DOC}: {p}" for p in health_problems(doc, light))
    problems.extend(pin_problems(root, css))
    problems.extend(fork_problems(root, set(light) | set(dark)))

    compared = ""
    if args.studio is not None:
        studio_css = Path(args.studio)
        if not studio_css.is_file():
            problems.append(f"{studio_css} does not exist, so Studio was not compared")
        else:
            studio_blocks = parse_blocks(studio_css.read_text(encoding="utf-8"))
            drift = drift_problems(blocks, studio_blocks)
            problems.extend(f"drift from Studio: {p}" for p in drift)
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

    print(
        f"Brand v2 tokens agree: {len(light)} light and {len(dark)} dark tokens in "
        f"{TOKEN_FILE} match {VISUAL_DOC}{compared}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
