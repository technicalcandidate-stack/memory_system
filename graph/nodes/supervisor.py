"""Supervisor node for LangGraph multi-agent orchestration."""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..state import MultiAgentState


class RoutingDecision(BaseModel):
    """Output schema for routing decision."""
    route: str = Field(description="Which agent(s) to invoke: 'sql_only', 'document_search', or 'hybrid'")
    reasoning: str = Field(description="Brief explanation of why this routing was chosen")
    search_terms: List[str] = Field(default=[], description="Key terms to search for in document content")


ROUTING_PROMPT = """You are a query router for Harper Insurance's data system.

Analyze the user's question and determine which agent(s) should handle it.

## Available Agents:

**SQL Agent** handles queries about:
- Phone calls, call recordings, call summaries
- Text messages (SMS)
- Emails (quotes, communications, policy status)
- Company information (contacts, business details, address)
- Document METADATA (list documents, what files exist, document count)

**Document Search Agent** handles queries about:
- Searching WITHIN document content (what does the document say?)
- Finding specific information IN documents (policy terms, clauses, coverage details)
- "What's in the policy document?" type questions

## Routing Rules:

1. **sql_only**: Use for communications, company info, listing documents (metadata)
2. **document_search**: Use when asking about content INSIDE documents
3. **hybrid**: Use when needing BOTH SQL data AND document content search

Return your routing decision."""


def _format_conversation_context(history: List[dict]) -> str:
    if not history:
        return "No previous context."
    context_parts = []
    for i, exchange in enumerate(history[-3:], 1):
        q = exchange.get('question', '')[:100]
        a = exchange.get('answer', '')[:100]
        context_parts.append(f"[{i}] Q: {q}... A: {a}...")
    return "\n".join(context_parts)


def supervisor_node(state: MultiAgentState) -> Dict[str, Any]:
    """Supervisor node that decides which agent(s) to invoke."""
    print("\n" + "="*60)
    print("SUPERVISOR NODE - Routing Decision")
    print("="*60)
    print(f"Question: {state['user_question']}")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", ROUTING_PROMPT),
        ("human", "Question: {question}\n\nPrevious context: {context}\n\nAnalyze this question and decide the routing.")
    ])
    chain = prompt | llm.with_structured_output(RoutingDecision)
    context = _format_conversation_context(state.get("conversation_history", []))

    try:
        result = chain.invoke({"question": state["user_question"], "context": context})
        print(f"Route: {result.route}")
        print(f"Reasoning: {result.reasoning}")
        print("="*60 + "\n")
        return {
            "route_decision": result.route,
            "routing_reasoning": result.reasoning,
            "execution_path": ["supervisor"]
        }
    except Exception as e:
        print(f"Supervisor routing failed: {e}, defaulting to sql_only")
        print("="*60 + "\n")
        return {
            "route_decision": "sql_only",
            "routing_reasoning": f"Defaulted to SQL due to routing error: {str(e)}",
            "execution_path": ["supervisor"]
        }
