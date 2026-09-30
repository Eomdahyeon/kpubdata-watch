"""The package imports, reports a version and its CLI answers."""

from __future__ import annotations

import pytest

import kpubdata_watch
from kpubdata_watch.cli import main


def test_the_package_reports_its_version() -> None:
    assert kpubdata_watch.__version__


def test_the_cli_prints_help_without_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "kpubdata-watch" in capsys.readouterr().out


def test_the_cli_reports_its_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert kpubdata_watch.__version__ in capsys.readouterr().out
