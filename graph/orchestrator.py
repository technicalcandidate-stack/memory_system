"""LangGraph Orchestrator for multi-agent coordination."""

from typing import Dict, Any, Optional, List, Literal
from langgraph.graph import StateGraph, END

from .state import MultiAgentState
from .nodes.supervisor import supervisor_node
from .nodes.sql_agent import sql_agent_node
from .nodes.document_agent import document_agent_node
from .nodes.synthesizer import synthesizer_node


def route_after_supervisor(state: MultiAgentState) -> Literal["sql_agent", "document_agent", "hybrid_sql"]:
    route = state.get("route_decision", "sql_only")
    if route == "sql_only":
        return "sql_agent"
    elif route == "document_search":
        return "document_agent"
    elif route == "hybrid":
        return "hybrid_sql"
    return "sql_agent"


def build_multi_agent_graph() -> StateGraph:
    """Build the LangGraph for multi-agent orchestration."""
    workflow = StateGraph(MultiAgentState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("sql_agent", sql_agent_node)
    workflow.add_node("hybrid_sql", sql_agent_node)
    workflow.add_node("document_agent", document_agent_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges("supervisor", route_after_supervisor,
        {"sql_agent": "sql_agent", "document_agent": "document_agent", "hybrid_sql": "hybrid_sql"})
    workflow.add_edge("sql_agent", "synthesizer")
    workflow.add_edge("hybrid_sql", "document_agent")
    workflow.add_edge("document_agent", "synthesizer")
    workflow.add_edge("synthesizer", END)
    return workflow.compile()


class MultiAgentOrchestrator:
    """Main orchestrator class for multi-agent execution."""

    def __init__(self, company_id: int):
        self.company_id = company_id
        self.graph = build_multi_agent_graph()

    def process_query(self, user_question: str, session_id: str, conversation_history: Optional[List[dict]] = None) -> Dict[str, Any]:
        print("\n" + "="*70)
        print("MULTI-AGENT ORCHESTRATOR")
        print("="*70)
        print(f"Question: {user_question}")
        print(f"Company ID: {self.company_id}")
        print("="*70 + "\n")

        initial_state: MultiAgentState = {
            "user_question": user_question, "company_id": self.company_id, "session_id": session_id,
            "conversation_history": conversation_history or [], "route_decision": "sql_only",
            "routing_reasoning": "", "agent_responses": [], "sql_skill": None, "sql_query": None,
            "sql_results": None, "sql_reasoning": None, "sql_natural_response": None,
            "retrieved_documents": None, "document_summary": None, "final_response": None,
            "execution_path": [], "error": None
        }

        try:
            final_state = self.graph.invoke(initial_state)
        except Exception as e:
            print(f"Graph execution failed: {e}")
            return {"success": False, "sql": "", "reasoning": "", "explanation": "", "results": [],
                    "error": str(e), "attempts": 1, "skill": "general",
                    "natural_response": f"I encountered an error processing your question: {str(e)}",
                    "data_sources": [], "metadata_summary": "", "trajectory": {"question": user_question,
                    "detected_skill": "ERROR", "reasoning": str(e), "execution_path": []},
                    "route_decision": "error", "documents": []}

        return self._convert_to_legacy_format(final_state, user_question)

    def _convert_to_legacy_format(self, state: MultiAgentState, user_question: str) -> Dict[str, Any]:
        data_sources = []
        sql_query = state.get("sql_query", "")
        if sql_query:
            from core.executor import extract_data_sources
            data_sources = extract_data_sources(sql_query)
        if state.get("retrieved_documents"):
            data_sources.append("Company Documents")

        trajectory = {"question": user_question, "detected_skill": state.get("sql_skill", "N/A").upper() if state.get("sql_skill") else "N/A",
                      "reasoning": state.get("sql_reasoning", "") or state.get("routing_reasoning", ""),
                      "execution_path": state.get("execution_path", []), "route_decision": state.get("route_decision", "unknown")}

        return {"success": state.get("error") is None, "sql": state.get("sql_query", ""),
                "reasoning": state.get("sql_reasoning", ""), "explanation": "",
                "results": state.get("sql_results", []) or [], "error": state.get("error"), "attempts": 1,
                "skill": state.get("sql_skill", "general") or "general",
                "natural_response": state.get("final_response", ""), "data_sources": data_sources,
                "metadata_summary": "", "trajectory": trajectory, "route_decision": state.get("route_decision"),
                "documents": state.get("retrieved_documents", [])}
