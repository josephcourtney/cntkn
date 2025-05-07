import json as _json
import sys
from collections.abc import MutableMapping, Sequence
from pathlib import Path
from typing import Any, cast

import click
from click import Command

from .core import (
    SUPPORTED_MODELS,
    SUPPORTED_PREFIXES,
    count_tokens,
    get_supported_models,
    is_model_supported,
)


def _count_tokens(entry: int | list[int]) -> int:
    return entry if isinstance(entry, int) else len(entry)


def resolve_input_texts(
    text_or_dash: list[str],
    file_path: list[str],
) -> list[tuple[str, str]]:
    results = [(p, Path(p).read_text(encoding="utf-8")) for p in file_path]

    for t in text_or_dash:
        if t == "-":
            results.append(("stdin", sys.stdin.read()))
        else:
            results.append((t, t))

    if not results and not sys.stdin.isatty():
        stdin = sys.stdin.read()
        if stdin:
            results.append(("stdin", stdin))

    return results


class ModelName(click.ParamType):
    name: str = "model"

    def convert(self, value: str, param: click.Parameter | None, ctx: click.Context | None) -> str:  # noqa: ARG002, PLR6301
        if not is_model_supported(value):
            msg = (
                f"{value!r} is not a supported model. Use `cntkn models` to see available models.\n"
                f"Supported: {', '.join(SUPPORTED_MODELS[:5])}..."
            )
            raise click.ClickException(msg)
        return value


MODEL_TYPE = ModelName()


class DefaultGroup(click.Group):
    default_cmd: str | None

    def __init__(
        self,
        name: str | None = None,
        commands: MutableMapping[str, Command] | Sequence[Command] | None = None,
        *,
        default_cmd: str | None = None,
        **attrs: Any,
    ) -> None:
        self.default_cmd = default_cmd
        super().__init__(name=name, commands=commands, **attrs)

    def resolve_command(
        self,
        ctx: click.Context,
        args: list[str],
    ) -> tuple[str, click.Command, list[str]]:
        args_list = list(args)
        if (not args_list or args_list[0] not in self.commands) and self.default_cmd:
            args_list.insert(0, self.default_cmd)
        result = super().resolve_command(ctx, args_list)
        return cast("tuple[str, click.Command, list[str]]", result)


@click.group(
    cls=DefaultGroup,
    default_cmd="count",
    invoke_without_command=True,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.help_option("-h", "--help", is_eager=True)
@click.version_option(package_name="cntkn", prog_name="cntkn")
@click.pass_context
def main(ctx: click.Context) -> None:
    """cntkn: count tokens using OpenAI's tiktoken."""
    if ctx.invoked_subcommand is None and not any(f in ctx.args for f in ("-h", "--help")):
        ctx.invoke(
            count,
            text_or_dash=ctx.args,
            file_path=[],
            model="gpt-4o",
            as_json=False,
            quiet=False,
            verbose=False,
            show_tokens=False,
            color=None,
            total=False,
        )


@main.command("models")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output.")
def list_models(*, as_json: bool) -> None:
    """List known supported model names and prefixes."""
    if as_json:
        click.echo(_json.dumps(get_supported_models(), indent=2))
    else:
        click.echo("Exact models:")
        for model in SUPPORTED_MODELS:
            click.echo(f"  - {model}")
        click.echo("\nModel name prefixes (allowed):")
        for prefix in SUPPORTED_PREFIXES:
            click.echo(f"  - {prefix}*")


@main.command("count")
@click.help_option("-h", "--help", is_eager=True)
@click.argument("text_or_dash", nargs=-1)
@click.option(
    "-f",
    "--file",
    "file_path",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Read input text from file(s).",
)
@click.option(
    "-m", "--model", type=MODEL_TYPE, default="gpt-4o", show_default=True, help="Model name or prefix."
)
@click.option("-j", "--json", "as_json", is_flag=True, default=False, help="Emit JSON output.")
@click.option("-q", "--quiet", is_flag=True, default=False, help="Suppress output.")
@click.option("--verbose", is_flag=True, default=False, help="Show detailed output.")
@click.option("--tokens", "show_tokens", is_flag=True, default=False, help="Print raw tokens.")
@click.option("--total", is_flag=True, default=False, help="Sum token counts for all inputs.")
@click.option("--color/--no-color", "color", default=None, help="Force-enable or disable color output.")
def count(
    text_or_dash: list[str],
    file_path: list[str],
    model: str,
    *,
    as_json: bool,
    quiet: bool,
    verbose: bool,
    show_tokens: bool,
    total: bool,
    color: bool | None,
) -> None:
    """Count tokens in TEXT, file(s), or stdin."""
    color = sys.stdout.isatty() if color is None else color

    # 1) gather inputs exactly once
    texts = resolve_input_texts(text_or_dash, file_path)

    if not texts:
        msg = (
            "Error: no input provided.\n"
            "Provide a string, `-`, file via `--file`, or pipe via stdin.\n"
            "Example: echo 'hello world' | cntkn"
        )
        raise click.ClickException(msg)

    # 2) always store the raw return (int or list[int])
    results: list[tuple[str, int | list[int]]] = []
    for label, text in texts:
        enc = count_tokens(text, model, return_tokens=show_tokens)
        results.append((label, enc))

    if quiet:
        sys.exit(0)

    # 3) JSON output
    if as_json:
        if total:
            total_count = sum(_count_tokens(enc) for _, enc in results)
            click.echo(_json.dumps({"total_tokens": total_count}))
        else:
            out = dict(results)
            click.echo(_json.dumps(out, indent=2))
        return

    # 4) plain-text total
    if total:
        click.echo(str(sum(_count_tokens(enc) for _, enc in results)))
        return

    # 5) per-input printing
    for label, enc in results:
        count_val = _count_tokens(enc)
        if verbose:
            click.echo(f"{label} → {count_val} tokens")
        else:
            click.echo(str(count_val))
        if show_tokens:
            click.echo(f"  Tokens: {enc}")
