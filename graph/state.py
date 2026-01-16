"""State schema for LangGraph multi-agent orchestration."""

from typing import TypedDict, Annotated, List, Optional, Literal
from operator import add


class AgentResponse(TypedDict):
    """Response from an individual agent."""
    agent_name: str
    content: str
    data: Optional[List[dict]]
    sql: Optional[str]
    documents: Optional[List[dict]]
    confidence: float
    error: Optional[str]


class MultiAgentState(TypedDict):
    """Shared state schema for multi-agent orchestration."""
    user_question: str
    company_id: int
    session_id: str
    conversation_history: List[dict]  # Main conversation history (kept for compatibility)
    # Agent-specific memories - each agent has its own isolated memory
    supervisor_memory: List[dict]
    sql_agent_memory: List[dict]
    document_agent_memory: List[dict]
    synthesizer_memory: List[dict]
    route_decision: Literal["sql_only", "document_only", "hybrid", "conversational"]
    routing_reasoning: str
    conversational_response: Optional[str]
    agent_responses: Annotated[List[AgentResponse], add]
    sql_skill: Optional[str]
    sql_query: Optional[str]
    sql_results: Optional[List[dict]]
    sql_reasoning: Optional[str]
    sql_natural_response: Optional[str]
    retrieved_documents: Optional[List[dict]]
    document_summary: Optional[str]
    final_response: Optional[str]
    execution_path: Annotated[List[str], add]
    error: Optional[str]
