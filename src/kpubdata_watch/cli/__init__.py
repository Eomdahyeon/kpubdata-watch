"""Operator command line (API_CONTRACT.md, "Operator CLI").

Only ``--version`` exists yet; the dataset, probe and incident commands arrive with
their epics.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from kpubdata_watch import __version__


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``kpubdata-watch`` command."""
    parser = argparse.ArgumentParser(
        prog="kpubdata-watch",
        description="Observe Korean public data APIs and explain their reliability.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.parse_args(argv)
    parser.print_help()
    return 0
