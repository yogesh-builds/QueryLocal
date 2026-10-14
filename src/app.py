import time

import pandas as pd
import streamlit as st

from text_to_sql import DB_PATH, MODEL, OLLAMA_MODEL, answer, get_schema

st.set_page_config(page_title="QueryLocal", page_icon="🗄️", layout="wide")
st.title("QueryLocal")
st.caption("Ask your database in plain English.")


@st.cache_data
def load_schema():
    return get_schema(DB_PATH)


schema = load_schema()

with st.sidebar:
    st.header("Database")
    st.code(schema, language="sql")
    choice = st.radio("Model", ["Gemini (cloud)", "Ollama (local)"])
    backend = "gemini" if choice.startswith("Gemini") else "ollama"
    st.write(f"Using: `{MODEL if backend == 'gemini' else OLLAMA_MODEL}`")

# (question so far, clarifying question) while waiting for the user's answer
if "pending" not in st.session_state:
    st.session_state.pending = None
pending = st.session_state.pending

if pending:
    st.info(f"I need one detail: {pending[1]}")
    if st.button("Cancel and ask something else"):
        st.session_state.pending = None
        st.rerun()

with st.form("ask"):
    text = st.text_input(
        "Your answer" if pending else "Your question",
        placeholder="Who are the top 3 customers by total order amount?",
    )
    submitted = st.form_submit_button("Send" if pending else "Ask")

if submitted and text.strip():
    question = f"{pending[0]}\nUser clarification: {text.strip()}" if pending else text.strip()
    st.session_state.pending = None
    start = time.time()
    result, error = None, None
    try:
        with st.spinner("Thinking..."):
            result = answer(question, schema, backend)
    except Exception as e:
        error = e
    elapsed = time.time() - start

    if error:
        st.error(f"Could not answer: {error}")
    elif result["status"] == "clarify":
        st.session_state.pending = (question, result["question"])
        st.rerun()
    elif result["status"] == "impossible":
        st.warning(f"I can't answer that from this data: {result['reason']}")
    else:
        st.subheader("Generated SQL")
        st.code(result["sql"], language="sql")
        if result["assumption"]:
            st.info(f"Assumption: {result['assumption']}")
        st.subheader("Result")
        if result["rows"]:
            st.dataframe(
                pd.DataFrame(result["rows"], columns=result["columns"]),
                use_container_width=True,
            )
        else:
            st.info("The query ran fine but returned no rows.")
        st.caption(f"{len(result['rows'])} row(s) in {elapsed:.1f}s")