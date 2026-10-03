#!/usr/bin/env python3
"""Watch's Brand v2 colour tokens must not drift from KPubData Studio (#72).

`src/kpubdata_watch/web/static/brand-v2.css` carries a copy of the light, dark
and OS-dark custom-property blocks of Studio's `src/globals.css`. Copies drift
silently, so this gate compares the copy with Studio's real source, which CI
checks out from kpubdata-studio `main` (a sparse checkout of that one file).

Comparing CSS text read from a checkout is not a dependency: Watch still never
imports Studio or declares it as a package, which is all that
`scripts/check_independence.py` (PRD D-016) forbids.

Checked, for each of the three theme blocks:

- every custom property Studio defines exists in Watch's copy (missing token);
- every such property has the same value as in Studio (mismatched value);
- Healthy (`--status-success`) never takes Fresh Mint (`--brand-secondary` or
  `--brand-secondary-strong`), and no `--status-*` token takes Brand Blue
  (`--brand-primary`): brand colours and status colours never share a value.

Studio's Tailwind `@theme` blocks and Watch's own type-scale block are outside
the comparison. When Studio changes a token this gate fails; nothing rewrites
Watch's copy automatically. Copy the blocks again in a pull request instead.

Usage:
    python scripts/check_brand_tokens.py --studio PATH [--watch PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WATCH_TOKENS = REPO_ROOT / "src" / "kpubdata_watch" / "web" / "static" / "brand-v2.css"

THEME_BLOCKS = (
    ':root, :root[data-theme="light"]',
    ':root[data-theme="dark"]',
    ":root:not([data-theme])",
)

_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_BLOCK = re.compile(r"([^{}]+)\{([^{}]*)\}")
_PROPERTY = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")


def parse_blocks(css: str) -> dict[str, dict[str, str]]:
    """Map each innermost selector to its custom properties, whitespace-normalised.

    A block nested in `@media` is keyed by its own selector, which is how both
    files write the OS-dark block.
    """
    blocks: dict[str, dict[str, str]] = {}
    for match in _BLOCK.finditer(_COMMENT.sub("", css)):
        selector = " ".join(match.group(1).split())
        found = _PROPERTY.findall(match.group(2))
        properties = {name: " ".join(value.split()).lower() for name, value in found}
        if properties:
            blocks.setdefault(selector, {}).update(properties)
    return blocks


def compare(studio_css: str, watch_css: str) -> list[str]:
    """Return one message per problem; an empty list means Watch matches Studio."""
    studio = parse_blocks(studio_css)
    watch = parse_blocks(watch_css)
    problems: list[str] = []
    for selector in THEME_BLOCKS:
        if selector not in studio:
            problems.append(f"Studio has no `{selector}` block; the comparison cannot run")
            continue
        theirs = studio[selector]
        ours = watch.get(selector, {})
        for name, value in theirs.items():
            if name not in ours:
                problems.append(f"`{selector}`: missing {name} (Studio: {value})")
            elif ours[name] != value:
                problems.append(f"`{selector}`: {name} is {ours[name]}, Studio has {value}")
        problems.extend(_collisions(selector, ours))
    return problems


def _collisions(selector: str, tokens: dict[str, str]) -> list[str]:
    problems = []
    success = tokens.get("--status-success")
    for mint in ("--brand-secondary", "--brand-secondary-strong"):
        if success is not None and tokens.get(mint) == success:
            problems.append(f"`{selector}`: --status-success uses Fresh Mint ({mint} = {success})")
    blue = tokens.get("--brand-primary")
    for name, value in tokens.items():
        if name.startswith("--status-") and blue is not None and value == blue:
            problems.append(f"`{selector}`: {name} uses Brand Blue (--brand-primary = {blue})")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--studio", type=Path, required=True, help="Studio's src/globals.css")
    parser.add_argument("--watch", type=Path, default=WATCH_TOKENS, help="Watch's token file")
    args = parser.parse_args(argv)

    problems = compare(
        args.studio.read_text(encoding="utf-8"), args.watch.read_text(encoding="utf-8")
    )
    if problems:
        print(f"Brand v2 token drift: {len(problems)} problem(s)", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        print(
            "Copy Studio's light, dark and OS-dark blocks into brand-v2.css again and "
            "update the commit recorded at the top of that file.",
            file=sys.stderr,
        )
        return 1
    print(f"Brand v2 tokens match Studio ({', '.join(THEME_BLOCKS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
