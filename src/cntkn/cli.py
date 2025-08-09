from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import click
from click import Command

from .config import Config, load_config
from .core import (
    SUPPORTED_MODELS,
    SUPPORTED_PREFIXES,
    TiktokenCounter,
    TokenCounter,
    count_tokens,
    get_supported_models,
    is_model_supported,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping  # pragma: no cover


def _count_tokens(entry: int | list[int]) -> int:
    return entry if isinstance(entry, int) else len(entry)


# ------------------------------- input handling -------------------------------
def find_input_sources(
    text_or_dash: list[str],
    file_path: list[str],
) -> list[tuple[str, str | Path]]:
    """Return a list of (label, source) where source is either text or a Path."""
    # Files are explicit paths (label is the path string)
    sources: list[tuple[str, str | Path]] = [(p, Path(p)) for p in file_path]

    # CLI text_or_dash: either '-' (stdin) or inline text
    for t in text_or_dash:
        if t == "-":
            sources.append(("stdin", "STDIN"))  # sentinel to read from stdin later
        else:
            sources.append((t, t))  # inline text

    # Implicit stdin if nothing was provided and stdin is piped
    if not sources and not sys.stdin.isatty():
        data = sys.stdin.read()
        if data:
            sources.append(("stdin", data))

    return sources


def read_sources(sources: list[tuple[str, str | Path]]) -> list[tuple[str, str]]:
    """Materialize sources into (label, text)."""
    results: list[tuple[str, str]] = []
    for label, src in sources:
        if isinstance(src, Path):
            results.append((label, src.read_text(encoding="utf-8")))
        elif src == "STDIN":
            results.append((label, sys.stdin.read()))
        else:
            # already a text literal
            results.append((label, cast("str", src)))
    return results


def resolve_input_texts(
    text_or_dash: list[str],
    file_path: list[str],
) -> list[tuple[str, str]]:
    """Back-compat wrapper retaining the original function name used by the CLI."""
    # NOTE: call split steps to keep responsibilities separate.
    sources = find_input_sources(text_or_dash, file_path)
    return read_sources(sources)


class ModelName(click.ParamType):
    name: str = "model"

    @staticmethod
    def convert(value: str, param: click.Parameter | None, ctx: click.Context | None) -> str:  # noqa: ARG004
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
        commands: Mapping[str, Command] | Iterable[Command] | None = None,
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


def _color_from_config(cfg: Config) -> bool | None:
    """Translate Config.color_mode into tri-state for Click handling.

    - 'on'  -> True
    - 'off' -> False
    - 'auto' (default) -> None (defer to TTY check)".
    """
    if cfg.color_mode == "on":
        return True
    if cfg.color_mode == "off":
        return False
    return None


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
    # "Load project/user configuration once per invocation."
    cfg = load_config()
    ctx.obj = {"config": cfg, "counter": TiktokenCounter()}

    if ctx.invoked_subcommand is None and not any(f in ctx.args for f in ("-h", "--help")):
        # Use configured default model unless overridden by args in explicit call below.
        ctx.invoke(
            count,
            text_or_dash=ctx.args,
            file_path=[],
            model=cfg.default_model,
            as_json=False,
            quiet=False,
            verbose=False,
            show_tokens=False,
            color=_color_from_config(cfg),
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


# ------------------------------- output strategy ------------------------------
# "Use small output helpers to keep branching contained (Strategy pattern-lite)."
def _output_json(
    results: list[tuple[str, int | list[int]]],
    *,
    total: bool,
) -> None:
    if total:
        total_count = sum(_count_tokens(enc) for _, enc in results)
        click.echo(_json.dumps({"total_tokens": total_count}))
        return
    out = dict(results)
    click.echo(_json.dumps(out, indent=2))


def _output_plain(
    results: list[tuple[str, int | list[int]]],
    *,
    verbose: bool,
    show_tokens: bool,
    total: bool,
) -> None:
    if total:
        click.echo(str(sum(_count_tokens(enc) for _, enc in results)))
        return

    for label, enc in results:
        count_val = _count_tokens(enc)
        if verbose:
            click.echo(f"{label} → {count_val} tokens")
        else:
            click.echo(str(count_val))
        if show_tokens:
            click.echo(f"  Tokens: {enc}")


def _emit_results(
    results: list[tuple[str, int | list[int]]],
    *,
    as_json: bool,
    quiet: bool,
    verbose: bool,
    show_tokens: bool,
    total: bool,
) -> None:
    """Single-responsibility output function for all modes."""
    if quiet:
        # NOTE: Exiting early keeps behavior identical to previous implementation.
        sys.exit(0)

    if as_json:
        _output_json(results, total=total)
        return

    _output_plain(results, verbose=verbose, show_tokens=show_tokens, total=total)


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
    "-m",
    "--model",
    type=MODEL_TYPE,
    default=None,
    show_default=False,
    help="Model name or prefix (defaults to config).",
)
@click.option("-j", "--json", "as_json", is_flag=True, default=False, help="Emit JSON output.")
@click.option("-q", "--quiet", is_flag=True, default=False, help="Suppress output.")
@click.option("--verbose", is_flag=True, default=False, help="Show detailed output.")
@click.option("--tokens", "show_tokens", is_flag=True, default=False, help="Print raw tokens.")
@click.option("--total", is_flag=True, default=False, help="Sum token counts for all inputs.")
@click.option("--color/--no-color", "color", default=None, help="Force-enable or disable color output.")
@click.pass_context
def count(
    ctx: click.Context,
    text_or_dash: list[str],
    file_path: list[str],
    model: str | None,
    *,
    as_json: bool,
    quiet: bool,
    verbose: bool,
    show_tokens: bool,
    total: bool,
    color: bool | None,
) -> None:
    # "Main command for counting tokens. Handles CLI args, resolves inputs, and delegates to core logic."
    cfg: Config = ctx.obj["config"]
    counter: TokenCounter = ctx.obj["counter"]

    # Resolve model from config if not explicitly passed.
    resolved_model = model or cfg.default_model

    # ----------------- removed dead code (no color output implemented yet) -----------------
    # NOTE: Previously computed resolved_color; it wasn't used anywhere.
    # Keeping the option for future ANSI output, but removing the unused computation.
    # resolved_color = (
    #     sys.stdout.isatty() if (color if color is not None else _color_from_config(cfg)) is None else color
    # )
    # _ = resolved_color  # currently unused; placeholder if you later add ANSI output
    # --------------------------------------------------------------------------------------
    _ = color  # intentionally unused until ANSI output is implemented

    texts = resolve_input_texts(text_or_dash, file_path)

    if not texts:
        msg = (
            "Error: no input provided.\n"
            "Provide a string, `-`, file via `--file`, or pipe via stdin.\n"
            "Example: echo 'hello world' | cntkn"
        )
        raise click.ClickException(msg)

    results: list[tuple[str, int | list[int]]] = []
    for label, text in texts:
        enc = count_tokens(text, resolved_model, return_tokens=show_tokens, counter=counter)
        results.append((label, enc))

    _emit_results(
        results,
        as_json=as_json,
        quiet=quiet,
        verbose=verbose,
        show_tokens=show_tokens,
        total=total,
    )
