import streamlit as st
from pipeline import run, ask

st.set_page_config(page_title="Documents to Decisions", layout="wide")
st.title("Messy documents → decisions")
st.caption("Reads contracts and invoices, flags risks, and writes the owner's weekly brief.")

folder = st.text_input("Folder of contracts/invoices (.txt)", "data")
if st.button("Analyze", type="primary"):
    with st.spinner("Reading documents..."):
        st.session_state.result = run(folder)

r = st.session_state.get("result")
if r:
    brief, flags, data, chat = st.tabs(["Weekly brief", "Flags", "Extracted data", "Ask"])
    brief.markdown(r["brief"])
    flags.dataframe(r["flags"], use_container_width=True)
    data.dataframe(r["records"], use_container_width=True)
    q = chat.text_input("Ask a question, e.g. 'What renews in the next 60 days?'")
    if q:
        chat.write(ask(q, r["records"]))
