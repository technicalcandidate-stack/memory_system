"""Supervisor node for LangGraph multi-agent orchestration."""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..state import MultiAgentState


class RoutingDecision(BaseModel):
    """Output schema for routing decision."""
    route: str = Field(description="Which agent(s) to invoke: 'conversational', 'sql_only', 'document_search', or 'hybrid'")
    reasoning: str = Field(description="Brief explanation of why this routing was chosen")
    search_terms: List[str] = Field(default=[], description="Key terms to search for in document content")
    conversational_response: str = Field(default="", description="If route is 'conversational', provide a brief, friendly response here")


ROUTING_PROMPT = """You are a query router for Harper Insurance's data system.

Analyze the user's question and determine which agent(s) should handle it.

## CRITICAL - CHECK FOR CONVERSATIONAL MESSAGES FIRST:
BEFORE routing to any data agent, check if this is just a greeting or chitchat.
Use 'conversational' route for ANY of these (including typos/variations):
- Greetings: "hello", "hi", "hey", "good morning", "how are you", "how are yo", "hows it going"
- Thanks: "thanks", "thank you", "thx", "appreciate it"
- Farewells: "bye", "goodbye", "see you", "later"
- Small talk: "how are you doing today?", "what's up", "how's your day"
- Capability questions: "what can you do?", "help", "what do you know"

For conversational messages, provide a brief friendly response in conversational_response.
Example: "how are you today?" → route=conversational, conversational_response="I'm doing well, thank you! How can I help you with insurance information today?"

DO NOT query the database for greetings or chitchat - this wastes resources!

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

1. **conversational**: Use for greetings, thanks, chitchat, or questions about your capabilities - NO data needed
2. **sql_only**: Use for communications, company info, listing documents (metadata)
3. **document_search**: Use when asking about content INSIDE documents
4. **hybrid**: Use when needing BOTH SQL data AND document content search

Return your routing decision."""


def _format_conversation_context(history: List[dict]) -> str:
    """Format conversation history for context (used for supervisor's own memory)."""
    if not history:
        return "No previous context."
    context_parts = []
    for i, exchange in enumerate(history[-3:], 1):
        q = exchange.get('question', '')[:100]
        a = exchange.get('answer', '')[:100]
        context_parts.append(f"[{i}] Q: {q}... A: {a}...")
    return "\n".join(context_parts)


def _format_supervisor_memory(memory: List[dict]) -> str:
    """Format supervisor's own memory showing past routing decisions."""
    if not memory:
        return "No previous routing decisions."
    context_parts = []
    for i, exchange in enumerate(memory[-3:], 1):
        q = exchange.get('question', '')[:80]
        route = exchange.get('answer', '')[:80]
        context_parts.append(f"[{i}] Question: {q}... -> Route: {route}")
    return "\n".join(context_parts)


def supervisor_node(state: MultiAgentState) -> Dict[str, Any]:
    """Supervisor node that decides which agent(s) to invoke."""
    print("\n" + "="*60)
    print("SUPERVISOR NODE - Routing Decision")
    print("="*60)
    print(f"Question: {state['user_question']}")

    # Use supervisor's own memory instead of shared conversation_history
    supervisor_memory = state.get("supervisor_memory", [])
    print(f"Supervisor memory entries: {len(supervisor_memory)}")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", ROUTING_PROMPT),
        ("human", "Question: {question}\n\nPrevious routing decisions: {context}\n\nAnalyze this question and decide the routing.")
    ])
    chain = prompt | llm.with_structured_output(RoutingDecision)
    context = _format_supervisor_memory(supervisor_memory)

    try:
        result = chain.invoke({"question": state["user_question"], "context": context})
        print(f"Route: {result.route}")
        print(f"Reasoning: {result.reasoning}")
        if result.conversational_response:
            print(f"Conversational response: {result.conversational_response}")
        print("="*60 + "\n")

        # Create memory entry for this routing decision
        memory_entry = {
            "question": state["user_question"],
            "answer": f"route={result.route}; reasoning={result.reasoning}"
        }

        response_dict = {
            "route_decision": result.route,
            "routing_reasoning": result.reasoning,
            "execution_path": ["supervisor"],
            "supervisor_memory": supervisor_memory + [memory_entry]
        }

        # If conversational, include the response directly
        if result.route == "conversational" and result.conversational_response:
            response_dict["conversational_response"] = result.conversational_response

        return response_dict
    except Exception as e:
        print(f"Supervisor routing failed: {e}, defaulting to sql_only")
        print("="*60 + "\n")

        # Still record the decision in memory even on error
        memory_entry = {
            "question": state["user_question"],
            "answer": f"route=sql_only; error={str(e)}"
        }

        return {
            "route_decision": "sql_only",
            "routing_reasoning": f"Defaulted to SQL due to routing error: {str(e)}",
            "execution_path": ["supervisor"],
            "supervisor_memory": supervisor_memory + [memory_entry]
        }
