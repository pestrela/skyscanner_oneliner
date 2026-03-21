# Usage

## Installation

Clone the repository and install dependencies:

```bash
uv sync
```

## Running

### Web app (Streamlit)

```bash
just streamlit
# or
uv run streamlit run app.py
```

### CLI

```bash
just run
# or
uv run python main.py
```

Paste flight page text into stdin, then press Ctrl+D to parse.

### Run a specific test input

```bash
just test 1   # runs tests/runs/test1.in through the parser
```

## Testing

```bash
just tests
# or
uv run python -B -m unittest discover -s tests -v
```

## Documentation

Preview docs locally:

```bash
just docs
```

Build static docs:

```bash
uv run mkdocs build
```
