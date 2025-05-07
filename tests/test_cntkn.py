import runpy
import sys

import pytest


class DummyTTYIn:
    def isatty(self):
        return True

    def read(self, *args, **kwargs):
        return ""


def test___main___exits_on_no_input(monkeypatch, capsys):
    # Simulate a TTY stdin so we hit the final else branch in count()
    monkeypatch.setattr(sys, "stdin", DummyTTYIn())

    with pytest.raises(SystemExit) as exitinfo:
        runpy.run_module("cntkn", run_name="__main__")

    # Click will sys.exit(1) on that branch
    assert exitinfo.value.code == 1

    # And the error message should have been printed to stderr
    captured = capsys.readouterr()
    assert "Error: no input provided" in captured.err
