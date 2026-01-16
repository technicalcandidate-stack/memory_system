"""Response Synthesizer node for LangGraph multi-agent orchestration."""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..state import MultiAgentState


def _format_synthesizer_memory(memory: List[dict]) -> str:
    """Format synthesizer's memory for context."""
    if not memory:
        return "No previous synthesis history."
    context_parts = []
    for i, entry in enumerate(memory[-3:], 1):
        q = entry.get('question', '')[:60]
        result = entry.get('answer', '')[:80]
        context_parts.append(f"[{i}] Q: {q}... -> {result}")
    return "\n".join(context_parts)


def synthesizer_node(state: MultiAgentState) -> Dict[str, Any]:
    """Response Synthesizer node - combines multi-agent outputs."""
    print("\n" + "="*60)
    print("SYNTHESIZER NODE - Combining Responses")
    print("="*60)

    agent_responses = state.get("agent_responses", [])
    route = state.get("route_decision", "sql_only")

    # Use synthesizer's own memory
    synthesizer_memory = state.get("synthesizer_memory", [])
    print(f"Synthesizer memory entries: {len(synthesizer_memory)}")

    print(f"Route was: {route}")
    print(f"Agent responses to combine: {len(agent_responses)}")

    question = state["user_question"]

    if len(agent_responses) == 1:
        final_response = agent_responses[0]["content"]
        print("Single agent response - passing through")
        print("="*60 + "\n")

        # Create memory entry
        memory_entry = {
            "question": question,
            "answer": f"Single agent pass-through: {final_response[:80]}..."
        }

        return {"final_response": final_response, "execution_path": ["synthesizer"],
                "synthesizer_memory": synthesizer_memory + [memory_entry]}

    if not agent_responses:
        print("No agent responses received!")
        print("="*60 + "\n")

        # Create memory entry for error case
        memory_entry = {
            "question": question,
            "answer": "Error: No agent responses received"
        }

        return {"final_response": "I apologize, but I couldn't retrieve any information to answer your question.",
                "execution_path": ["synthesizer"], "error": "No agent responses received",
                "synthesizer_memory": synthesizer_memory + [memory_entry]}

    print("Synthesizing multiple agent responses...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are synthesizing responses from multiple data sources for Harper Insurance.

**SQL Database Results:**
{sql_response}

**Document Search Results:**
{document_response}

Create a unified, coherent response that answers the user's question completely."""),
        ("human", "Original question: {question}\n\nSynthesize the responses above into a single coherent answer.")
    ])

    sql_response = next((r["content"] for r in agent_responses if r["agent_name"] == "sql_agent"), "No SQL results available.")
    document_response = next((r["content"] for r in agent_responses if r["agent_name"] == "document_agent"), "No document results available.")

    try:
        chain = prompt | llm
        response = chain.invoke({"sql_response": sql_response, "document_response": document_response, "question": question})
        final_response = response.content
        print("Synthesis complete")
    except Exception as e:
        print(f"Synthesis failed: {e}")
        final_response = f"**From Database:**\n{sql_response}\n\n**From Documents:**\n{document_response}"

    print("="*60 + "\n")

    # Create memory entry for synthesis
    memory_entry = {
        "question": question,
        "answer": f"Synthesized from {len(agent_responses)} agents: {final_response[:80]}..."
    }

    return {"final_response": final_response, "execution_path": ["synthesizer"],
            "synthesizer_memory": synthesizer_memory + [memory_entry]}
