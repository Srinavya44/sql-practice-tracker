import streamlit as st
import pandas as pd
from pathlib import Path

# import shared DB helpers
from db import get_conn, fetch_log, update_excel_export

# --- page config ---
st.set_page_config(page_title="Practice Log", layout="wide")
st.title("Practice Log")

# helpful: TOPICS to sync question selector on load
import json
TOPICS_PATH = Path(__file__).parents[1] / "topics" / "questions.json"
TOPICS = json.loads(TOPICS_PATH.read_text(encoding="utf-8"))

# Filter
filter_topic = st.selectbox("Filter by Topic", options=["All"] + list(TOPICS.keys()), key="filter_topic_log")

# Load log
log_df = fetch_log(filter_topic)

if log_df.empty:
    st.info("No practiced queries yet. Save a successful run from the Practice page.")
    st.stop()

# Render each entry
for _, row in log_df.iterrows():
    header = f"{row['question_title']} — [Topic: {row['topic']}]"
    with st.expander(header):
        st.code(row['query_text'], language='sql')
        if row.get('user_note'):
            st.markdown("**Note:**")
            st.write(row['user_note'])

        c1, c2 = st.columns([1, 1])

        # Run in Editor → set pending and jump to Practice page
        if c1.button("Run in Editor", key=f"run_{row['id']}"):
            st.session_state["pending_load"] = row["query_text"]
            if row["topic"] in TOPICS:
                st.session_state["pending_topic"] = row["topic"]
                q_titles = [q['title'] for q in TOPICS[row['topic']]]
                if row["question_title"] in q_titles:
                    st.session_state["pending_question"] = row["question_title"]
            # switch to main Practice page
            try:
                st.switch_page("app.py")
            except Exception:
                st.success("Loaded into editor. Go to the Practice page.")
                st.stop()

        # Delete with inline confirm
        del_flag_key = f"confirm_delete_{row['id']}"
        if c2.button("Delete", key=f"del_{row['id']}"):
            st.session_state[del_flag_key] = True

        if st.session_state.get(del_flag_key, False):
            st.warning("Delete this saved query? This cannot be undone.")
            y, n = st.columns(2)
            if y.button("Yes — delete", key=f"yes_{row['id']}"):
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("DELETE FROM practice_log WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                update_excel_export()
                st.session_state.pop(del_flag_key, None)
                st.success("Deleted.")
                st.experimental_rerun()
            if n.button("Cancel", key=f"no_{row['id']}"):
                st.session_state.pop(del_flag_key, None)
                st.experimental_rerun()

# Optional: export whole log
csv = log_df.to_csv(index=False)
st.download_button(" Download Practice Log (CSV)", csv, file_name="practice_log.csv")
