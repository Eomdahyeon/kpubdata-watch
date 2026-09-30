"""KPubData Watch: observe Korean public data APIs and explain their reliability.

See docs/PRD.md for the product and docs/ARCHITECTURE.md for the pipeline.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("kpubdata-watch")
except PackageNotFoundError:  # pragma: no cover - only when run from a bare checkout
    __version__ = "0+unknown"

__all__ = ["__version__"]
