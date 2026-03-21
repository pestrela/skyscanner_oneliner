# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This project uses [uv](https://docs.astral.sh/uv/) with Python 3.14. Run `uv sync` to create the virtualenv.

Run tests:
```bash
uv run python -B -m unittest discover -s tests -v
# or
just test
```

Run a specific test:
```bash
uv run python -B -m unittest test_list_utils.TestListReverse.test_basic -v
```

Use `-B` to suppress `.pyc` / `__pycache__` generation, or set `PYTHONDONTWRITEBYTECODE=1`.

## Structure

```
src/oneliner/        # package source
tests/               # unittest suite
main.py              # entrypoint
memory/              # Claude's persistent memory (MEMORY.md index + individual files)
```
