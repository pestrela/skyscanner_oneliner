import json

import streamlit as st
from streamlit_js_eval import streamlit_js_eval

from oneliner.clipboard_paste import clipboard_paste
from oneliner.skyscanner_parser import parse_text

st.title("Skyscanner Flight Summary")
st.write("Paste the Skyscanner flight page text below, then click **Parse**.")

if st.session_state.pop("pending_clear", False):
    st.session_state["input_key"] = st.session_state.get("input_key", 0) + 1
    st.session_state.pop("result", None)

if "input_key" not in st.session_state:
    st.session_state["input_key"] = 0

text = st.text_area("Flight page text", height=300, label_visibility="collapsed", key=f"input_text_{st.session_state['input_key']}")

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("Parse", type="primary"):
        if not text.strip():
            st.warning("Paste some text first.")
        else:
            try:
                lines = parse_text(text)
                result = "\n".join(lines)
                st.session_state["result"] = result
                st.session_state["copy_result"] = result
            except ValueError as e:
                st.error(str(e))

with col2:
    if st.button("Clear"):
        st.session_state["pending_clear"] = True

with col3:
    if st.button("Paste & Parse", type="secondary"):
        st.session_state["paste_requested"] = True

# Auto-copy when Parse button produced a result
if copy_result := st.session_state.pop("copy_result", None):
    streamlit_js_eval(
        js_expressions=f"navigator.clipboard.writeText({json.dumps(copy_result)})",
        key="clipboard_write_parse",
    )

if st.session_state.get("paste_requested"):
    st.caption("Paste area active — press Ctrl+V")
    pasted = clipboard_paste(key="paste_input")
    if pasted:
        st.session_state["paste_requested"] = False
        try:
            lines = parse_text(pasted)
            result = "\n".join(lines)
            st.session_state["result"] = result
            streamlit_js_eval(
                js_expressions=f"navigator.clipboard.writeText({json.dumps(result)})",
                key="clipboard_write",
            )
            st.success("Done — result copied to clipboard.")
        except ValueError as e:
            st.error(str(e))

if result := st.session_state.get("result"):
    st.code(result, language=None)
    escaped = result.replace("`", r"\`")
    st.components.v1.html(
        f"""
        <button
          onclick="navigator.clipboard.writeText(`{escaped}`).then(()=>this.textContent='Copied!').catch(()=>this.textContent='Failed')"
          style="padding:6px 14px;cursor:pointer;font-size:14px;border:1px solid #ccc;border-radius:4px;background:#fff"
        >Copy to clipboard</button>
        """,
        height=44,
    )
