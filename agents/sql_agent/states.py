from typing import List, Optional, Dict
import pandas as pd
from typing import TypedDict


class SQLAgentState(TypedDict):
    """
    Carries context through the text→SQL and plotting pipeline:
      - question: original NL input
      - sql_query: generated SQL
      - sql_result: raw query result DataFrame  
      - answer: final answer
      - error: any error messages
    """
    question: str
    db_info: dict
    sql_query: str
    sql_result: Optional[pd.DataFrame] = None
    answer: str = ""
    error: Optional[str] = None
    plot_path: Optional[str] = None
    response_md: str = ""
    step: Optional[str] = None


