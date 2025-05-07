<<<<<<< HEAD
from click.testing import CliRunner

from {{ project_name }}.cli import main

def test_import():
    assert main
=======
from importlib.metadata import version as pkg_version

import pytest
from click.testing import CliRunner

from cntkn.cli import main


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


def test_models_command(runner):
    result = runner.invoke(main, ["models"])
    assert result.exit_code == 0
    assert "Exact models:" in result.stdout


def test_models_command_json(runner):
    result = runner.invoke(main, ["models", "--json"])
    assert result.exit_code == 0
    assert result.stdout.strip().startswith("{")
    assert '"exact_models"' in result.stdout


@pytest.mark.parametrize(
    ("args", "stdin", "expected"),
    [
        (["count", "hello world"], None, "2"),
        (["count", "-"], "hello world", "2"),
        (["count"], "stdin input", lambda o: o.strip().isdigit()),
    ],
)
def test_various_input_modes(runner, args, stdin, expected):
    result = runner.invoke(main, args, input=stdin) if stdin is not None else runner.invoke(main, args)
    assert result.exit_code == 0
    out = result.stdout.strip()
    if callable(expected):
        assert expected(out)
    else:
        assert out == expected


def test_multiple_text_inputs(runner):
    result = runner.invoke(main, ["count", "hello", "world"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert all(line.isdigit() for line in lines)
    assert sum(map(int, lines)) >= 2


def test_multiple_files(tmp_path, runner):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("hello world")
    file2.write_text("foo")
    result = runner.invoke(main, ["count", "-f", str(file1), "-f", str(file2)])
    assert result.exit_code == 0
    counts = list(map(int, result.stdout.strip().splitlines()))
    assert counts == [2, 1]


def test_total_flag(runner):
    result = runner.invoke(main, ["count", "foo", "bar", "--total"])
    assert result.exit_code == 0
    assert result.stdout.strip().isdigit()
    assert int(result.stdout.strip()) >= 2


def test_json_total_flag(runner):
    result = runner.invoke(main, ["count", "foo", "bar", "--json", "--total"])
    assert result.exit_code == 0
    assert '"total_tokens"' in result.stdout


def test_verbose_flag(runner):
    result = runner.invoke(main, ["count", "foo bar", "--verbose"])
    assert result.exit_code == 0
    assert "→" in result.stdout


def test_tokens_flag(runner):
    result = runner.invoke(main, ["count", "foo", "--tokens"])
    assert result.exit_code == 0
    assert "Tokens:" in result.stdout


def test_combined_tokens_and_json(runner):
    result = runner.invoke(main, ["count", "foo", "--tokens", "--json"])
    assert result.exit_code == 0
    assert result.stdout.strip().startswith("{")
    assert "foo" in result.stdout


def test_help_messages(runner):
    assert runner.invoke(main, ["-h"]).exit_code == 0
    assert runner.invoke(main, ["--help"]).exit_code == 0
    result = runner.invoke(main, ["count", "-h"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_invalid_model_error(runner):
    result = runner.invoke(main, ["count", "foo", "--model", "invalid-model"])
    assert result.exit_code != 0
    assert "not a supported model" in result.stderr


def test_error_on_empty_input(runner):
    result = runner.invoke(main, ["count"])
    assert result.exit_code != 0
    assert "no input provided" in result.stderr.lower()


def test_version_flag(runner):
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    expected = pkg_version("cntkn")
    assert f"cntkn, version {expected}" in result.stdout


def test_quiet_flag(runner):
    result = runner.invoke(main, ["count", "foo", "--quiet"])
    assert result.exit_code == 0
    assert not result.stdout


@pytest.mark.parametrize("flag", ["--color", "--no-color"])
def test_color_flags(runner, flag):
    result = runner.invoke(main, ["count", "foo", flag])
    assert result.exit_code == 0
    assert result.stdout.strip().isdigit()


def test_auto_disable_color_when_piped(monkeypatch, runner):
    # Simulate sys.stdout.isatty() == False
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    result = runner.invoke(main, ["count", "foo"])
    # because there's no color output yet, this is a bit artificial,
    # but if you later add ANSI escapes, you'd assert none appear:
    assert "\x1b[" not in result.stdout


def test_errors_go_to_stderr(runner):
    # Missing input should go to stderr, not stdout
    result = runner.invoke(main, ["count"], catch_exceptions=False)
    assert result.exit_code != 0
    assert "Error: no input provided" in result.stderr
    assert not result.stdout


def test_invalid_model_name(runner):
    # This will hit ModelName.convert's failure branch
    result = runner.invoke(main, ["count", "foo", "--model", "not-a-model"])
    assert result.exit_code != 0
    assert "not a supported model" in result.stderr


def test_default_fallback_to_count(runner):
    # “cntkn hello” should act like “cntkn count hello”
    result = runner.invoke(main, ["hello"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "1"  # “hello” is one token


def test_no_input_argument_error(runner):
    # With no args and no stdin, should raise the “no input provided” ClickException
    result = runner.invoke(main, [])
    assert result.exit_code != 0
    assert "Error: no input provided" in result.stderr


def test_module_invocation(runner):
    # Simulate python -m cntkn hello
    # Note: CliRunner has a convenience for prog_name
    result = runner.invoke(main, ["foo"], prog_name="python -m cntkn")
    assert result.exit_code == 0
    assert result.stdout.strip().isdigit()
>>>>>>> 6c25a8e (initial commit)
