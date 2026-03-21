
run:
    uv run python main.py

tests:
    uv run python -B -m unittest discover -s tests -v

test n:
    uv run python main.py < tests/runs/test{{n}}.in


sl: streamlit



streamlit:
    uv run streamlit run app.py

claude_resume:
    claude --resume "skyscanner-flight-summarizer"

docs:
    uv run python scripts/serve_docs.py
