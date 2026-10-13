import time

import pandas as pd
import streamlit as st

from text_to_sql import DB_PATH, MODEL, answer, get_schema

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
    st.write(f"Model: `{MODEL}`")

with st.form("ask"):
    question = st.text_input(
        "Your question",
        placeholder="Who are the top 3 customers by total order amount?",
    )
    submitted = st.form_submit_button("Ask")

if submitted and question.strip():
    start = time.time()
    try:
        with st.spinner("Thinking..."):
            sql, columns, rows = answer(question.strip(), schema)
        elapsed = time.time() - start

        st.subheader("Generated SQL")
        st.code(sql, language="sql")

        st.subheader("Result")
        if rows:
            st.dataframe(pd.DataFrame(rows, columns=columns), use_container_width=True)
        else:
            st.info("The query ran fine but returned no rows.")
        st.caption(f"{len(rows)} row(s) in {elapsed:.1f}s")
    except Exception as e:
        st.error(f"Could not answer: {e}")