"""SQL Agent node for LangGraph multi-agent orchestration."""

from typing import Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..state import MultiAgentState, AgentResponse
from core.executor import execute_with_retry


def sql_agent_node(state: MultiAgentState) -> Dict[str, Any]:
    """SQL Agent node - wraps existing execute_with_retry()."""
    print("\n" + "="*60)
    print("SQL AGENT NODE - Executing Query")
    print("="*60)

    result = execute_with_retry(
        user_question=state["user_question"],
        company_id=state["company_id"],
        conversation_history=state.get("conversation_history", [])
    )

    agent_response = AgentResponse(
        agent_name="sql_agent",
        content=result.get("natural_response", ""),
        data=result.get("results", []),
        sql=result.get("sql", ""),
        documents=None,
        confidence=1.0 if result.get("success") else 0.0,
        error=result.get("error")
    )

    print(f"SQL Agent completed: {len(result.get('results', []))} rows returned")
    print("="*60 + "\n")

    return {
        "agent_responses": [agent_response],
        "sql_skill": result.get("skill", "general"),
        "sql_query": result.get("sql", ""),
        "sql_results": result.get("results", []),
        "sql_reasoning": result.get("reasoning", ""),
        "sql_natural_response": result.get("natural_response", ""),
        "execution_path": ["sql_agent"]
    }
