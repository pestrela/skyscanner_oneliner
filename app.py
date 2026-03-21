import json

import streamlit as st

st.set_page_config(page_title="✈️ OneLiner")

from oneliner.skyscanner_parser import parse_text

def help():
    #demo_url="https://www.skyscanner.pt/transporte/voos/fao/cur/260630/260708/config/11469-2606302010--31915,-32540-2-10807-2607011020%7C10807-2607081815--32540,-31915-2-11469-2607091655"
    demo_url="https://www.skyscanner.pt/transport/flights/fao/ams/270308/270310/config/11469-2703080605--31781-1-9451-2703081250%7C9451-2703101750--31781-1-11469-2703102350?"

    ret = f"""
This tool summarizes a Skyscanner flight to simple one-liners

For example, [this flight]({demo_url}) gets summarized neatly as:
```
170 €
 8 marco: FAO  6:05 ->  6:55 LIS | LIS  8:40 -> 12:50 AMS
10 marco: AMS 17:50 -> 20:15 LIS | LIS 23:00 -> 23:50 FAO
```

To use this tool:
1. Copy the **whole text** of a flight to the clipboard (Ctrl+A, Ctrl+C)
2. Paste in the box
3. Click **Summary**
4. The result is copied back to the clipboard
"""
    return ret


#st.markdown("<style>textarea { font-family: monospace !important; font-size: 12px !important; }</style>", unsafe_allow_html=True)
st.markdown("<style>textarea { font-family: monospace !important;  }</style>", unsafe_allow_html=True)
st.title("SkyScanner Flight Summary")
st.write("Paste the Skyscanner flight page text below, then click **Summary**.")



if "pending_text" in st.session_state:
    st.session_state["text"] = st.session_state.pop("pending_text")

if st.session_state.pop("pending_clear", False):
    st.session_state["text"] = ""

text = st.text_area("Flight page text", height=150, label_visibility="collapsed", key="text")

col1, col2, _, col3 = st.columns([1, 1, 3, 1])
with col1:
    parse_clicked = st.button("Summary", type="primary")
with col2:
    if st.button("Clear"):
        st.session_state["pending_clear"] = True
        st.rerun()
with col3:
    st.markdown("<style>div[data-testid='stColumn']:last-child { align-items: flex-end !important; }</style>", unsafe_allow_html=True)
    with st.popover("Help"):
        st.markdown(help())

if parse_clicked:
    if not text.strip():
        st.warning("Paste some text first.")
    else:
        try:
            result = "\n".join(parse_text(text))
            st.session_state["pending_text"] = result
            st.session_state["do_copy"] = result
            st.rerun()
        except ValueError as e:
            st.session_state["pending_clear"] = True
            st.session_state["error"] = str(e)
            st.rerun()

if error := st.session_state.pop("error", None):
    st.error(f"error: {error}")

if do_copy := st.session_state.pop("do_copy", None):
    st.components.v1.html(
        f"<script>window.parent.navigator.clipboard.writeText({json.dumps(do_copy)})</script>",
        height=0,
    )
    st.success("Clipboard updated.")


