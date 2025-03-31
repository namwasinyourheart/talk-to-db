import sqlite3
import pandas as pd
import re
from agents.llms import LLM
from agents.tools import PlotSQLTool
from .states import SQLAgentState
from utils.consts import DB_PATH


# def ingest(state: SQLAgentState) -> SQLAgentState:
#     """Populate state.tables with list of tables in the DB."""
#     db_info = state['db_info']
#     conn = sqlite3.connect(DB_PATH)
#     try:
#         db_info['tables'] = [row[0] for row in conn.execute(
#             "SELECT name FROM sqlite_master WHERE type='table';"
#         )]
#         # Populate columns for each table
#         columns = {}
#         for table in db_info['tables']:
#             col_rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
#             columns[table] = [r[1] for r in col_rows]
#         db_info['columns'] = columns
#         state.db_info = db_info
#     finally:
#         conn.close()
#     return state


from agents.safe_guardrails import OffTopicValidator
from guardrails import Guard

def detect_off_topic(state: SQLAgentState) -> SQLAgentState:
    """Check if the input question is off-topic."""
    question = state['question']
    validator = Guard().use(
        OffTopicValidator,
        on_fail="fix"
    )
    metadata = {
        "topic": "Database Queries",
        "additional_context": "The database is about ecommerce products with tables: products, laptops, phones, tablets, promotions, category"
    }

    validation_result = validator.validate(question, metadata=metadata)
    if validation_result.validated_output == "OFF_TOPIC":
        state['error'] = True
    else:
        state['error'] = False
    state['step'] = 'detect_off_topic'
    state['answer'] = validation_result.validated_output

    print(state)
    return state


def get_db_info(state: SQLAgentState) -> SQLAgentState:
    """Get database information."""
    db_info = state['db_info']
    conn = sqlite3.connect(DB_PATH)
    try:
        db_info['tables'] = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )]
        # Populate columns for each table
        columns = {}
        for table in db_info['tables']:
            col_rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            columns[table] = [r[1] for r in col_rows]
        db_info['columns'] = columns
        schema = "; ".join(f"{t}({', '.join(db_info['columns'][t])})" for t in db_info['tables'])
        db_info['schema'] = schema
    finally:
        conn.close()
    state['step'] = 'get_db_info'
    return state


def generate_sql(state: SQLAgentState) -> SQLAgentState:
    """Use LLM to translate user_query into SQL."""
    llm = LLM()
    # Include detailed schema with columns
    schema = state['db_info']['schema']
    prompt = (
        f"Given this database schema: {schema}, "
        f"write an SQL query to: {state['question']}. "
        "Respond with only the SQL enclosed in triple backticks."
    )
    raw = llm.generate(prompt)
    # print('raw', raw)
    lines = raw.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    state['sql_query'] = "\n".join(lines).strip()
    # print('sql_query', state['sql_query'])
    state['step'] = 'generate_sql'
    return state


def execute_sql(state: SQLAgentState) -> SQLAgentState:
    """Run the SQL in state.sql and store result DataFrame."""
    sql_query = state['sql_query']
    conn = sqlite3.connect(DB_PATH)
    try:
        state['sql_result'] = pd.read_sql_query(sql_query, conn)
    except Exception as e:
        state['error'] = str(e)
    finally:
        conn.close()
    state['step'] = 'execute_sql'
    return state

def generate_answer(state: SQLAgentState) -> SQLAgentState:
    """Generate answer using LLM based on SQL result."""
    llm = LLM()
    if state['sql_result'] is not None and not state['sql_result'].empty:
        result_str = state['sql_result'].to_string(index=False)
        prompt = (
            f"Given the question: {state['question']},\n"
            f"SQL Query: {state['sql_query']},\n"
            f"and the following SQL query result: {result_str},\n"
            "provide a concise answer:"
        )
        state['answer'] = llm.generate(prompt)
    else:
        state['error'] = state['error'] or "No results found."
        if state["answer"] == "OFF_TOPIC":
            state['error'] = "The question is off-topic." 
            state["answer"] = " Sorry, I can't assist you with that request."  
    state['step'] = 'generate_answer'
    return state


def optional_plot(state: SQLAgentState) -> SQLAgentState:
    """If user_query requests plotting, generate plot and set state.plot_path."""
    if any(k in state['question'].lower() for k in ['plot', 'vẽ', 'biểu đồ']):
        tool = PlotSQLTool()
        md = tool._run(state['sql_query'])
        m = re.search(r'!\[.*\]\((.*?)\)', md)
        if m:
            state['plot_path'] = m.group(1)
        else:
            state['error'] = state['error'] or 'Plot generation failed'
    return state


def format_response(state: SQLAgentState) -> SQLAgentState:
    """Build markdown response including SQL, table preview, and plot."""
    parts = []
    if state['sql_query']:
        parts.append(f"```sql\n{state['sql_query']}\n```")
    if state['sql_result'] is not None:
        parts.append(state['sql_result'].to_markdown(index=False))
    if state['plot_path']:
        parts.append(f"![Plot]({state['plot_path']})")
    if state['error']:
        parts.append(f"**Error**: {state['error']}")
    state['response_md'] = "\n\n".join(parts)
    return state
