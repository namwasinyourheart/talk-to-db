import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from agents.llms import LLM
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from utils.consts import DB_PATH
from agents.sql_agent.states import SQLAgentState

# Load environment vars
load_dotenv()

# def get_sql_agent():
#     """
#     Initializes a LangChain SQLDatabaseChain for SQLite.
#     """
#     # Load SQLite DB
#     db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
#     # Patch run to strip Markdown fences and log
#     orig_run = db.run
#     def clean_run(query: str, **kwargs) -> str:
#         lines = query.splitlines()
#         if lines and lines[0].strip().startswith("```"):
#             lines = lines[1:]
#         if lines and lines[-1].strip().startswith("```"):
#             lines = lines[:-1]
#         cleaned = "\n".join(lines).strip()
#         print(f"[SQLDatabaseChain] Running SQL: {cleaned}")

# def get_sql_agent():
#     """
#     Initializes a LangChain SQLDatabaseChain for SQLite.
#     """
#     # Load SQLite DB
#     db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
#     # Patch run to strip Markdown fences and log
#     orig_run = db.run
#     def clean_run(query: str, **kwargs) -> str:
#         lines = query.splitlines()
#         if lines and lines[0].strip().startswith("```"):
#             lines = lines[1:]
#         if lines and lines[-1].strip().startswith("```"):
#             lines = lines[:-1]
#         cleaned = "\n".join(lines).strip()
#         print(f"[SQLDatabaseChain] Running SQL: {cleaned}")
#         return orig_run(cleaned, **kwargs)
#     db.run = clean_run
#     # Initialize LLM
#     llm_wrapper = LLM()
#     # Create SQLDatabaseChain
#     chain = SQLDatabaseChain.from_llm(llm_wrapper.chat_model, db, verbose=True)
#     return chain

class SQLAgent:
    def __init__(self):
        self.db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
        self.llm = LLM()
        self.graph = self.build_graph()

    
    def build_graph(self):
        from agents.sql_agent.graph import build_graph
        return build_graph().compile()
    
    def run(self, state: SQLAgentState) -> SQLAgentState:
        """
        Run the SQL agent with the given query.
        """
        return self.graph.invoke(state)
    
if __name__ == "__main__":
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
        "error": None
    }
    while True:
        question = input("Enter your query (or 'exit' to quit): ")
        state['question'] = question
        if not question or question.lower() in ('exit', 'quit'):
            print("Goodbye!")
            break
        result = agent.run(state) 
        # print(result)

        # answer = result['answer']
        # print(answer)

        for step in agent.graph.stream(state, stream_mode="updates"):
            print(step)
    
