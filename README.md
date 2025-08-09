# cntkn - Count Tokens for OpenAI Models

A minimal, fast CLI for counting tokens the way [OpenAI](https://openai.com/) models do - powered by [`tiktoken`](https://github.com/openai/tiktoken).

## Features

- **Count tokens** from strings, files, or stdin.
- **JSON output** for easy scripting.
- **Color mode control** (`on`, `off`, `auto`).
- **Configurable defaults** via `pyproject.toml` or `cntkn.toml`.
- Small and dependency-light (just `click` + `tiktoken`).

## Installation

```bash
pip install cntkn
````

For development:

```bash
git clone https://github.com/<yourname>/cntkn.git
cd cntkn
pip install -e .[dev]
```

## Usage

### Count from a string

```bash
cntkn count "hello world"
# or, with default subcommand:
cntkn "hello world"
```

### Count from a file

```bash
cntkn count --file example.txt
```

### Count from stdin

```bash
echo "this is piped" | cntkn
# or explicitly:
echo "stdin" | cntkn count -
```

### JSON output

```bash
cntkn count "foo bar" --json
# -> {"tokens": 2}
```

### Quiet mode (no output, exit code only)

```bash
cntkn count "foo bar" --quiet
```

### Force color or disable color

```bash
cntkn count "test" --color
cntkn count "test" --no-color
```

## Configuration

`cntkn` reads defaults in the following order (later overrides earlier):

1. **Packaged defaults** (`src/cntkn/resources/default.toml`)
2. **`pyproject.toml`** `[tool.cntkn]` table
3. **`cntkn.toml`** file (top-level keys)

### Example: `pyproject.toml`

```toml
[tool.cntkn]
default_model = "gpt-4o"
color = "on"
```

### Example: `cntkn.toml`

```toml
default_model = "gpt-4o-mini"
color = "off"
```

When both exist, `cntkn.toml` takes precedence.

### Supported keys

| Key             | Type   | Values                     | Default  |
| --------------- | ------ | -------------------------- | -------- |
| `default_model` | string | any supported model/prefix | `gpt-4o` |
| `color`         | string | `"auto"`, `"on"`, `"off"`  | `auto`   |

## CLI Options (count command)

| Option                 | Description                          |
| ---------------------- | ------------------------------------ |
| `TEXT` / `-`           | Input text or `-` to read from stdin |
| `-f`, `--file PATH`    | Read from file(s)                    |
| `-m`, `--model NAME`   | Model name or prefix                 |
| `-j`, `--json`         | Emit JSON output                     |
| `-q`, `--quiet`        | Suppress output                      |
| `--verbose`            | Show detailed output                 |
| `-t`, `--tokens`       | Show token IDs instead of counts     |
| `--total`              | Sum token counts across inputs       |
| `--color / --no-color` | Force-enable or disable color output |
| `-h`, `--help`         | Show help                            |

## Listing Models

```bash
cntkn models
```

With JSON:

```bash
cntkn models --json
```

## Development & Testing

Clone the repo and install dev dependencies:

```bash
pip install -e .[dev]
```

Run lint, type checks, and tests:

```bash
ruff check .
ty check
pytest
```

## License

Licensed under the [GPL-3.0-only](./LICENSE).

## Example Workflows

Count tokens for multiple files and get a total:

```bash
cntkn count -f chapter1.txt -f chapter2.txt --total
```

Integrate into a script with JSON parsing:

```bash
TOKENS=$(cntkn count "some text" --json | jq .tokens)
echo "Tokens: $TOKENS"
```

```
