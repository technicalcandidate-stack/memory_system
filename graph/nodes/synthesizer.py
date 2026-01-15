"""Response Synthesizer node for LangGraph multi-agent orchestration."""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..state import MultiAgentState


def synthesizer_node(state: MultiAgentState) -> Dict[str, Any]:
    """Response Synthesizer node - combines multi-agent outputs."""
    print("\n" + "="*60)
    print("SYNTHESIZER NODE - Combining Responses")
    print("="*60)

    agent_responses = state.get("agent_responses", [])
    route = state.get("route_decision", "sql_only")

    print(f"Route was: {route}")
    print(f"Agent responses to combine: {len(agent_responses)}")

    if len(agent_responses) == 1:
        final_response = agent_responses[0]["content"]
        print("Single agent response - passing through")
        print("="*60 + "\n")
        return {"final_response": final_response, "execution_path": ["synthesizer"]}

    if not agent_responses:
        print("No agent responses received!")
        print("="*60 + "\n")
        return {"final_response": "I apologize, but I couldn't retrieve any information to answer your question.",
                "execution_path": ["synthesizer"], "error": "No agent responses received"}

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
        response = chain.invoke({"sql_response": sql_response, "document_response": document_response, "question": state["user_question"]})
        final_response = response.content
        print("Synthesis complete")
    except Exception as e:
        print(f"Synthesis failed: {e}")
        final_response = f"**From Database:**\n{sql_response}\n\n**From Documents:**\n{document_response}"

    print("="*60 + "\n")
    return {"final_response": final_response, "execution_path": ["synthesizer"]}
