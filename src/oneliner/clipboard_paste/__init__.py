from pathlib import Path

import streamlit.components.v1 as components

_component = components.declare_component(
    "clipboard_paste",
    path=str(Path(__file__).parent / "frontend"),
)


def clipboard_paste(key=None):
    """Renders a paste area. Returns the pasted text on Ctrl+V, None otherwise."""
    return _component(key=key, default=None)
