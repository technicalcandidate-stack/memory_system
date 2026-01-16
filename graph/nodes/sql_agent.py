"""SQL Agent node for LangGraph multi-agent orchestration."""

from typing import Dict, Any, List, Optional
import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..state import MultiAgentState, AgentResponse
from core.executor import execute_with_retry

# Simple in-memory cache for SQL agent results
# Key: hash of (question, company_id), Value: result dict
_sql_cache: Dict[str, dict] = {}
_CACHE_MAX_SIZE = 50  # Maximum number of cached entries


def _get_cache_key(question: str, company_id: int) -> str:
    """Generate a cache key from question and company_id."""
    cache_string = f"{company_id}:{question.lower().strip()}"
    return hashlib.md5(cache_string.encode()).hexdigest()


def _get_cached_result(question: str, company_id: int) -> Optional[dict]:
    """Check if we have a cached result for this query."""
    cache_key = _get_cache_key(question, company_id)
    if cache_key in _sql_cache:
        print(f"✅ CACHE HIT: Returning cached SQL result")
        return _sql_cache[cache_key]
    return None


def _cache_result(question: str, company_id: int, result: dict) -> None:
    """Cache the result for future use."""
    global _sql_cache

    # Evict oldest entries if cache is full
    if len(_sql_cache) >= _CACHE_MAX_SIZE:
        # Remove first 10 entries (simple eviction)
        keys_to_remove = list(_sql_cache.keys())[:10]
        for key in keys_to_remove:
            del _sql_cache[key]
        print(f"🗑️ CACHE EVICTION: Removed {len(keys_to_remove)} old entries")

    cache_key = _get_cache_key(question, company_id)
    _sql_cache[cache_key] = result
    print(f"💾 CACHE STORE: Saved result (cache size: {len(_sql_cache)})")


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
    """SQL Agent node - wraps existing execute_with_retry() with caching."""
    print("\n" + "="*60)
    print("SQL AGENT NODE - Executing Query")
    print("="*60)

    question = state["user_question"]
    company_id = state["company_id"]
    sql_agent_memory = state.get("sql_agent_memory", [])
    print(f"SQL Agent memory entries: {len(sql_agent_memory)}")

    # Check cache first
    cached_result = _get_cached_result(question, company_id)
    if cached_result:
        print(f"SQL Agent completed (FROM CACHE): {len(cached_result.get('results', []))} rows")
        print("="*60 + "\n")

        agent_response = AgentResponse(
            agent_name="sql_agent",
            content=cached_result.get("natural_response", ""),
            data=cached_result.get("results", []),
            sql=cached_result.get("sql", ""),
            documents=None,
            confidence=1.0 if cached_result.get("success") else 0.0,
            error=cached_result.get("error")
        )

        return {
            "agent_responses": [agent_response],
            "sql_skill": cached_result.get("skill", "general"),
            "sql_query": cached_result.get("sql", ""),
            "sql_results": cached_result.get("results", []),
            "sql_reasoning": cached_result.get("reasoning", ""),
            "sql_natural_response": cached_result.get("natural_response", ""),
            "execution_path": ["sql_agent (cached)"],
            "sql_agent_memory": sql_agent_memory  # No new memory entry for cached results
        }

    # Cache miss - execute the query
    print("🔍 CACHE MISS: Executing SQL query...")
    formatted_memory = _format_sql_agent_memory(sql_agent_memory)

    result = execute_with_retry(
        user_question=question,
        company_id=company_id,
        conversation_history=formatted_memory
    )

    # Cache the result for future use
    _cache_result(question, company_id, result)

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
        "question": question,
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
