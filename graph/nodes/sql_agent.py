"""SQL Agent node for LangGraph multi-agent orchestration."""

from typing import Dict, Any, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..state import MultiAgentState, AgentResponse
from core.executor import execute_with_retry


def _format_sql_agent_memory(memory: List[dict]) -> List[dict]:
    """Format SQL agent's memory for context in execute_with_retry."""
    # The execute_with_retry expects conversation_history format
    # Convert our memory entries to that format
    formatted = []
    for entry in memory[-3:]:  # Last 3 entries
        formatted.append({
            "question": entry.get("question", ""),
            "answer": entry.get("answer", "")
        })
    return formatted


def sql_agent_node(state: MultiAgentState) -> Dict[str, Any]:
    """SQL Agent node - wraps existing execute_with_retry()."""
    print("\n" + "="*60)
    print("SQL AGENT NODE - Executing Query")
    print("="*60)

    # Use SQL agent's own memory instead of shared conversation_history
    sql_agent_memory = state.get("sql_agent_memory", [])
    print(f"SQL Agent memory entries: {len(sql_agent_memory)}")

    # Format memory for execute_with_retry (it expects conversation_history format)
    formatted_memory = _format_sql_agent_memory(sql_agent_memory)

    result = execute_with_retry(
        user_question=state["user_question"],
        company_id=state["company_id"],
        conversation_history=formatted_memory
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

    # Create memory entry for this SQL execution
    result_summary = f"SQL: {result.get('sql', '')[:100]}; Rows: {len(result.get('results', []))}"
    memory_entry = {
        "question": state["user_question"],
        "answer": result_summary
    }

    return {
        "agent_responses": [agent_response],
        "sql_skill": result.get("skill", "general"),
        "sql_query": result.get("sql", ""),
        "sql_results": result.get("results", []),
        "sql_reasoning": result.get("reasoning", ""),
        "sql_natural_response": result.get("natural_response", ""),
        "execution_path": ["sql_agent"],
        "sql_agent_memory": sql_agent_memory + [memory_entry]
    }
