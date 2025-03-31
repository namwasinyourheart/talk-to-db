import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from agents.sql_agent.states import SQLAgentState
from langgraph.graph import StateGraph, START, END
from agents.sql_agent.nodes import get_db_info, generate_sql, execute_sql, generate_answer, detect_off_topic

def build_graph() -> StateGraph:
    graph = StateGraph(SQLAgentState)

    # Add nodes
    graph.add_node("detect_off_topic", detect_off_topic)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("get_db_info", get_db_info)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("generate_answer", generate_answer)

    # Add edges
    graph.add_edge(START, "detect_off_topic")

    graph.add_conditional_edges(
        "detect_off_topic",
        lambda state: state['error'], 
        path_map={
            True: "generate_answer",  
            False: "get_db_info"
        }
    )

    graph.add_edge("get_db_info", "generate_sql")
    graph.add_edge("generate_sql", "execute_sql")
    graph.add_edge("execute_sql", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph

def visualize_graph(graph) -> None:
    graph.visualize()

if __name__ == "__main__":
    state = {
        "question": "How many products are there?",
        "db_info": {
            "tables": [],
            "columns": {},
            "schema": ""
        },
        "sql_query": "",
        "sql_result": None,
        "error": None
    }

    graph = build_graph().compile()
    # visualize_graph(graph)

    result = graph.invoke(state)
    # print(result)

    answer = result['answer']
    print(answer)

    # for step in graph.stream(
    #     state, stream_mode="updates"
    # ):
    #     print(step)