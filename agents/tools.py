import sqlite3
import pandas as pd
from langchain.tools import BaseTool
import os
import matplotlib.pyplot as plt
from utils.consts import DB_PATH, PLOTS_DIR

# Fetch table list
_conn = sqlite3.connect(DB_PATH)
_TABLES = [row[0] for row in _conn.execute("SELECT name FROM sqlite_master WHERE type='table';")]
_conn.close()
_TABLES_LIST = ", ".join(_TABLES)

class SQLiteQueryTool(BaseTool):
    name: str = "sqlite_query"
    description: str = f"Executes a SQL query against the ecommerce SQLite database and returns results as CSV. Available tables: {_TABLES_LIST}."

    def _run(self, query: str) -> str:
        print(f"[SQLiteQueryTool] Executing query: {query}")
        conn = sqlite3.connect(DB_PATH)
        try:
            df = pd.read_sql_query(query, conn)
            return df.to_csv(index=False)
        except Exception as e:
            return f"SQL Error: {e}"
        finally:
            conn.close()

    async def _arun(self, query: str) -> str:
        raise NotImplementedError("Async not supported for SQLiteQueryTool")


class PlotSQLTool(BaseTool):
    name: str = "plot_sql"
    description: str = f"Executes a SQL query and generates a plot saved as a PNG; returns markdown image link. Available tables: {_TABLES_LIST}."

    def _run(self, query: str) -> str:
        print(f"[PlotSQLTool] Executing query: {query}")
        conn = sqlite3.connect(DB_PATH)
        try:
            df = pd.read_sql_query(query, conn)
            plt.figure()
            df.plot(kind='bar' if df.shape[1] > 1 else 'line', legend=False)
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = f"plot_{timestamp}.png"
            # Save plot to configured output directory
            output_dir = PLOTS_DIR
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            plt.tight_layout()
            plt.savefig(filepath)
            plt.close()
            return f"![Plot]({filepath})"
        except Exception as e:
            return f"Plot Error: {e}"
        finally:
            conn.close()

    async def _arun(self, query: str) -> str:
        raise NotImplementedError("Async not supported for PlotSQLTool")



