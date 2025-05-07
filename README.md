# cntkn

A minimal CLI to count tokens as used by OpenAI models (via `tiktoken`).

## Install

```bash
pip install -e .
````

## Usage

Count from a string:

```bash
cntkn count "hello world"
# or, with default command:
cntkn "hello world"
```

Count from a file:

```bash
cntkn count --file example.txt
```

Count from stdin (implicit):

```bash
echo "this is piped" | cntkn
# or explicitly:
echo "stdin" | cntkn count -
```

JSON output:

```bash
cntkn count "foo bar" --json
# → {"tokens":2}
```

Quiet mode (no output, just exit code):

```bash
cntkn count "foo bar" --quiet
```

Force color or no color:

```bash
cntkn count "test" --color
cntkn count "test" --no-color
```

Show help:

```bash
cntkn -h
cntkn --help
cntkn count -h
```

