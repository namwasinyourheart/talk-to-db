import streamlit as st
import pandas as pd
from utils.consts import DB_PATH
import sqlite3
import re
import os
from agents.sql_agent.agent import SQLAgent
import time
from agents.tools import PlotSQLTool


st.set_page_config(page_title="🔍 TalkToDB", layout="wide")
st.markdown("<h3 style='text-align: center;'>🔍 TalkToDB: Ask Any Question About Your Database</h1>", unsafe_allow_html=True)
# Sidebar for settings
with st.sidebar:
    st.header("🛠 Settings", anchor=None)
    st.write("Configure TalkToDB")

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Initialize SQL agent
# agent = get_sql_agent()

agent = SQLAgent()
state = {
    "question": None,
    "db_info": {
        "tables": [],
        "columns": {},
        "schema": None
    },
    "sql_query": None,
    "sql_result": None,
    "error": None,
    "step": None,
    "answer": None
}
_, left_col, _, right_col, _ = st.columns([0.5, 2, 0.5, 2, 0.5])

with right_col:
    st.subheader("Chatbot")
    container = st.container(height=900, border=True)

    # Display chat messages
    for turn in st.session_state.chat_history:
        print('turn', turn)
        role = turn.get('role', '')
        content = turn.get('content', '')
        if role == 'user':
            container.chat_message("user").write(content)
        else:
            with container.chat_message("assistant"):
                # st.markdown(content)
                if 'intermediate_steps' in content:
                    for step_name, step_value in content['intermediate_steps'].items():
                        if step_name == 'sql_query':
                            st.markdown(f"```sql\n{step_value}\n```")
                        elif step_name == 'sql_result':
                            st.table(step_value)
                        elif step_name == 'answer':
                            st.markdown(f"{step_value}")
                        elif step_name == 'error':
                            st.error(step_value)
                        else:
                            st.text(f"{step_name}: {step_value}")

                if 'answer' in content:
                    st.markdown(f"{content['answer']}")
                if 'error' in content:
                    st.error(content['error'])


    # Chat input
    user_input = st.chat_input("Ask a question about the database...")
    if user_input:
        # # Save user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with container.chat_message("user"):
            st.write(user_input)
        
        state['question'] = user_input
        st.session_state.chat_history.append({"role": "assistant", "content": {"intermediate_steps": {}, "answer": ""}})
        with container:
            if user_input.strip().lower().startswith('/sql'):
                sql = user_input[len('/sql'):].strip()
                try:
                    df = pd.read_sql_query(sql, sqlite3.connect(DB_PATH))
                    st.session_state.chat_history.append({"role": "assistant", "content": f"```sql\n{sql}\n```", "table_data": df})
                    with container.chat_message("assistant"):
                        st.write(f"```sql\n{sql}\n```")
                        st.table(df)
                except Exception as e:
                    err = f"SQL Error: {e}"
                    st.session_state.chat_history.append({"role": "assistant", "content": err})
                    with container.chat_message("assistant"):
                        st.error(err)
            elif user_input.strip().lower().startswith('/plot'):
                sql = user_input[len('/plot'):].strip()
                try:
                    tool = PlotSQLTool()
                    md = tool._run(sql)
                    print("md", md)
                    st.session_state.chat_history.append({"role": "assistant", "content": md})
                    with container.chat_message("assistant"):
                        st.markdown(md)
                        # display the generated plot image
                        m = re.search(r'!\[.*\]\((.*?)\)', md)
                        if m:
                            st.image(m.group(1))
                except Exception as e:
                    err = f"Plot Error: {e}"
                    st.session_state.chat_history.append({"role": "assistant", "content": err})
                    with container.chat_message("assistant"):
                        st.error(err)
            else:
                with container.chat_message("assistant"):
                    
                    for step in agent.graph.stream(state, stream_mode="updates"):
                        step_name, step_details = next(iter(step.items()))
                        spinner_message = "Generating SQL" if step_name == 'generate_sql' else "Executing SQL" if step_name == 'execute_sql' else "Generating Answer" if step_name == 'generate_answer' else "Plotting SQL" if step_name == 'plot_sql' else "Processing"
                        if spinner_message and step_name != 'detect_off_topic':
                            with st.spinner(spinner_message):
                                time.sleep(1)
                            if step_name == 'generate_sql':
                                st.markdown(f"```sql\n{step_details.get('sql_query', '')}\n```")
                                st.session_state.chat_history[-1]['content']['intermediate_steps']['sql_query'] = step_details.get('sql_query', '')
                            elif step_name == 'execute_sql':
                                st.table(step_details.get('sql_result', pd.DataFrame()))
                                st.session_state.chat_history[-1]['content']['intermediate_steps']['sql_result'] = step_details.get('sql_result', pd.DataFrame())

                            elif step_name == 'generate_answer':
                                st.write(step_details.get('answer', ''))
                                st.session_state.chat_history[-1]['content']['answer'] = step_details.get('answer', '')

                # st.session_state.chat_history.append(
                #     {
                #         "role": "assistant", 
                #         "content": 
                #         {
                #             "intermediate_steps": {
                #                 "sql_query": step_details.get('sql_query', ''), 
                #                 "sql_result": step_details.get('sql_result', pd.DataFrame())}, 
                #             "answer": step_details.get('answer', '')
                #         }
                #     }
                # )




with left_col:
    st.subheader("Database Explorer")
    if st.checkbox("Show DB Schema"):
        # Display SQLite schema in collapsible view
        conn = sqlite3.connect(DB_PATH)
        tables = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table';").fetchall()
        for name, ddl in tables:
            st.subheader(name)
            st.code(ddl, language='sql')
        conn.close()
#     if st.checkbox("Show ER Diagram"):
#         conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'ecommerce.db'))
#         tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';")]
#         dot = "digraph schema {\nrankdir=LR;\nnode [shape=plaintext];\n"
#         for table in tables:
#             cols = [col[1] for col in conn.execute(f"PRAGMA table_info({table});")]
#             label = (table + "\n" + "\n".join(cols)).replace('"', '\\"')
#             dot += f'"{table}" [label="{label}"];
# '

#         for table in tables:
#             for fk in conn.execute(f"PRAGMA foreign_key_list({table});"):
#                 dot += f'"{table}" -> "{fk[2]}" [label="{fk[3]}-> {fk[4]}"];
# '

#         dot += "}"
#         st.graphviz_chart(dot)
#         # Option to export ER diagram as PNG
#         if st.button("Save ER Diagram as PNG"):
#             import graphviz
#             s = graphviz.Source(dot)
#             png_bytes = s.pipe(format='png')
#             file_path = os.path.join(os.path.dirname(__file__), 'diagram.png')
#             with open(file_path, 'wb') as f:
#                 f.write(png_bytes)
#             st.success(f"Diagram saved as {file_path}")
#             st.image(png_bytes, caption="ER Diagram PNG")
#             st.download_button(
#                 "Download ER Diagram",
#                 data=png_bytes,
#                 file_name="diagram.png",
#                 mime="image/png"
#             )
#         conn.close()
    st.write("Upload CSV to explore or view tables.")
    uploaded_files = st.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=True)
    if uploaded_files:
        tabs = st.tabs([f.name for f in uploaded_files])
        for tab, f in zip(tabs, uploaded_files):
            with tab:
                df = pd.read_csv(f)
                st.table(df)
                # Button to import CSV into SQLite DB
                table_name = os.path.splitext(f.name)[0]
                if st.button(f"Import {f.name} to DB"):
                    conn = sqlite3.connect(DB_PATH)
                    try:
                        df.to_sql(table_name, conn, if_exists='replace', index=False)
                        st.success(f"{f.name} imported to DB as table {table_name}.")
                    except Exception as e:
                        st.error(f"Error importing: {e}")
                    finally:
                        conn.close()
