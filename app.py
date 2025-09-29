# app.py - Streamlit UI for SQL Practice Playground (clean + single editor)
import streamlit as st
from pathlib import Path
import json
import time
import pandas as pd

from db import init_db, get_conn, save_practice

# -------------------- Initialize --------------------
init_db()

st.set_page_config(
    page_title="SQL Practice",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Global CSS: center content, nicer buttons ---
st.markdown("""
<style>
.main .block-container {
  max-width: 1100px;
  padding-top: 1rem;
  padding-bottom: 4rem;
  margin: 0 auto;
}
.stButton > button {
  border-radius: 10px;
  padding: .5rem 1rem;
}
label { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("💡 SQL Practice")
st.caption("Select a question, write a query, run it, and save your practiced queries.")

# -------------------- load topics/questions into session --------------------
TOPICS_PATH = Path(__file__).parent / "topics" / "questions.json"
if "TOPICS" not in st.session_state:
    st.session_state["TOPICS"] = json.loads(TOPICS_PATH.read_text(encoding="utf-8"))

def save_topics_to_disk():
    TOPICS_PATH.write_text(json.dumps(st.session_state["TOPICS"], indent=2), encoding="utf-8")

# -------------------- session-state defaults --------------------
defaults = {
    "sql_query_editor": "",
    "last_run_success": False,
    "last_df_csv": None,
    "last_rows_returned": 0,
    "last_exec_time_ms": 0,
    "show_save_note": False,
    "save_note_text": "",
    "show_add_q_modal": False,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# -------------------- pending-load (apply BEFORE widgets) --------------------
if "pending_load" in st.session_state:
    st.session_state["sql_query_editor"] = st.session_state.pop("pending_load")
if "pending_topic" in st.session_state:
    st.session_state["topic_select"] = st.session_state.pop("pending_topic")
if "pending_question" in st.session_state:
    st.session_state["question_select"] = st.session_state.pop("pending_question")
# Clear editor if flagged from previous run
if "pending_clear_editor" in st.session_state and st.session_state["pending_clear_editor"]:
    st.session_state["sql_query_editor"] = ""
    st.session_state["pending_clear_editor"] = False


# -------------------- Helpers --------------------
def is_select_query(q: str) -> bool:
    return bool(q and q.strip().lower().startswith("select"))

# =====================================================================
# 1) Selectors + Add Question (single container)
# =====================================================================
with st.container(border=True):
    left_sel, right_sel = st.columns(2)
    with left_sel:
        topic = st.selectbox(
            "Select Topic",
            options=list(st.session_state["TOPICS"].keys()),
            key="topic_select"
        )

    question_titles = [q["title"] for q in st.session_state["TOPICS"][topic]]
    with right_sel:
        question = st.selectbox(
            "Select Question",
            options=question_titles,
            key="question_select"
        )

    st.markdown("")

    # Add new question trigger
    if st.button("➕ Add a new question"):
        st.session_state["show_add_q_modal"] = True

    # Modal-style add (inside the same container)
    if st.session_state.get("show_add_q_modal"):
        st.divider()
        st.subheader("Add a new question")

        mode = st.radio("Add to:", ["Existing topic", "New topic"], horizontal=True, key="addq_mode")

        if mode == "Existing topic":
            add_topic = st.selectbox(
                "Choose an existing topic",
                options=list(st.session_state["TOPICS"].keys()),
                index=list(st.session_state["TOPICS"].keys()).index(topic),
                key="addq_topic_existing"
            )
        else:
            add_topic = st.text_input("New topic name", key="addq_topic_new").strip()

        new_q_text = st.text_area(
            "Question text",
            key="addq_text",
            placeholder="e.g. Show employees who joined after 2021"
        )

        new_tables = st.multiselect(
            "Target table(s)",
            ["employees", "departments", "orders"],
            key="addq_tables"
        )

        persist = st.checkbox(
            "Also save to questions.json for future sessions",
            value=False,
            key="addq_persist"
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button(" Save Question", key="addq_save"):
                if not new_q_text.strip():
                    st.warning("Please enter a question.")
                elif mode == "New topic" and not add_topic:
                    st.warning("Please provide a new topic name.")
                else:
                    if add_topic not in st.session_state["TOPICS"]:
                        st.session_state["TOPICS"][add_topic] = []
                    st.session_state["TOPICS"][add_topic].append({
                        "title": new_q_text.strip(),
                        "target_tables": new_tables
                    })
                    # queue for next run (avoids widget mutation error)
                    st.session_state["pending_topic"] = add_topic
                    st.session_state["pending_question"] = new_q_text.strip()
                    st.session_state["show_add_q_modal"] = False
                    if persist:
                        save_topics_to_disk()
                    st.success("Question added successfully 🎉")
                    st.rerun()
        with c2:
            if st.button("Cancel", key="addq_cancel"):
                st.session_state["show_add_q_modal"] = False
                st.rerun()

# =====================================================================
# 2) Question info
# =====================================================================
with st.container(border=True):
    q_meta = next((q for q in st.session_state["TOPICS"][topic] if q["title"] == question), None)
    target_tables = q_meta.get("target_tables", []) if q_meta else []
    st.markdown("**Question:**")
    st.write(question)
    st.markdown(f"**Target table(s):** {', '.join(target_tables) if target_tables else 'None specified'}")

# =====================================================================
# 3) Schema, Editor, Actions, Results  (SINGLE editor section)
# =====================================================================
with st.container(border=True):
    with st.expander(" Show schema & sample data (helpful reference)"):
        conn = get_conn()
        try:
            st.markdown("**Tables:**")
            st.write("- departments (id, dept_name, location)")
            st.write("- employees (id, name, dept_id, salary, hire_date, email)")
            st.write("- orders (order_id, customer_name, order_date, amount, employee_id, status)")
            st.markdown("**Sample rows (first 5)**")
            for t in ["departments", "employees", "orders"]:
                st.markdown(f"**{t}:**")
                st.dataframe(
                    pd.read_sql_query(f"SELECT * FROM {t} LIMIT 5", conn),
                    use_container_width=True, hide_index=True
                )
        finally:
            conn.close()

    st.divider()

    # --- Editor (single) ---
    query_text = st.text_area(
        "Write your SQL query here:",
        height=220,
        key="sql_query_editor"
    )

    run_col, save_col = st.columns([1, 1])

    # --- Run query ---
    with run_col:
        if st.button("Run Query"):
            q = st.session_state["sql_query_editor"]
            if not is_select_query(q):
                st.error("Only SELECT queries are allowed in this practice app.")
            else:
                conn = get_conn()
                try:
                    start = time.time()
                    df = pd.read_sql_query(q, conn)
                    end = time.time()
                    exec_ms = int((end - start) * 1000)

                    st.session_state["last_run_success"] = True
                    st.session_state["last_df_csv"] = df.to_csv(index=False)
                    st.session_state["last_rows_returned"] = len(df)
                    st.session_state["last_exec_time_ms"] = exec_ms

                    st.success(f" Query ran successfully — {len(df)} rows ({exec_ms} ms)")
                    st.dataframe(df, use_container_width=True, hide_index=True, height=420)
                   
                except Exception as e:
                    st.session_state["last_run_success"] = False
                    st.error(f"Error running query: {e}")
                finally:
                    conn.close()

    # --- Save query ---
    with save_col:
        if st.button("Save as Practiced"):
            if not st.session_state.get("last_run_success", False):
                st.warning("Run a successful query first.")
            else:
                st.session_state["show_save_note"] = True

    # --- Notes + confirm save ---
    if st.session_state.get("show_save_note", False):
        st.markdown("**Notes (optional)**")
        st.session_state["save_note_text"] = st.text_area(
            "Add a note (optional)",
            value=st.session_state.get("save_note_text", ""),
            key="save_note_text_area"
        )

        save_choice = st.radio(
            "Save mode:",
            ["Save as new entry (append)", "Overwrite last saved for this question"],
            index=0
        )

        import time

        if st.button("Confirm & Save"):
            overwrite_flag = (save_choice == "Overwrite last saved for this question")

            q = st.session_state.get("sql_query_editor", "")
            note = st.session_state.get("save_note_text", "")
            rows = st.session_state.get("last_rows_returned", 0)
            ms   = st.session_state.get("last_exec_time_ms", 0)

            # save to DB + auto-export to Excel
            save_practice(topic, question, q, note, rows, ms, overwrite=overwrite_flag)

            # success toast that stays visible briefly
            st.success("Saved to Practice Log — nice work!")

            # clear inputs for next run
            st.session_state["pending_clear_editor"] = True
            st.session_state["save_note_text"] = ""
            st.session_state["show_save_note"] = False
            st.session_state["last_run_success"] = False

            # let user see the success for a moment, then rerun
            time.sleep(1.5)
            st.rerun()


    # --- Last run summary ---
    if st.session_state.get("last_run_success", False):
        st.divider()
        st.write(f"**Last run:** {st.session_state['last_rows_returned']} rows — {st.session_state['last_exec_time_ms']} ms")
        if st.session_state["last_df_csv"]:
            st.download_button("Download result CSV", st.session_state["last_df_csv"], file_name="query_result.csv")

# -------------------- Footer --------------------
st.markdown("---")
st.write("💡 Tip: Save only after verifying your query. Use 'Run in Editor' from the Practice Log to re-run saved queries.")
