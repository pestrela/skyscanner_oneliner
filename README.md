# Skyscanner Flight Summary

Summarizes a Skyscanner flight page into simple one-liners.

For example, a flight gets summarized as:
```
170 €
 8 marco: FAO  6:05 ->  6:55 LIS | LIS  8:40 -> 12:50 AMS
10 marco: AMS 17:50 -> 20:15 LIS | LIS 23:00 -> 23:50 FAO
```

## Usage

### Web site

https://skyscanner-oneliner.streamlit.app/

1. Copy the **whole text** of a Skyscanner flight page (Ctrl+A, Ctrl+C)
1. Paste in the box
1. Click **Summary**
1. The result is copied to the clipboard

### Local Web app

```bash
uv run streamlit run app.py
```

### CLI

```bash
uv run python main.py
```

Paste the flight page text, then press Ctrl+D.

## Setup

```bash
uv sync
```
