"""SQL executor with retry logic and LangChain integration."""
from typing import Dict, List, Any, Optional
import re
from sqlalchemy import text
from config.database import get_db_session
from config.settings import NLG_ENABLED
from agents.sql_agent import LangChainSQLAgent
from core.validator import validate_sql, sanitize_sql
from skills import SKILL_HANDLERS


def extract_data_sources(sql: str) -> List[str]:
    """
    Extract table names from SQL query.

    Args:
        sql: SQL query string

    Returns:
        List of friendly table names
    """
    # Pattern to match FROM and JOIN clauses
    pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)'
    matches = re.findall(pattern, sql, re.IGNORECASE)

    # Remove duplicates and sort
    sources = sorted(list(set(matches)))

    # Map table names to friendly names
    friendly_names = {
        "public.companies": "Companies Master Data",
        "communications.emails_silver": "Email Communications",
        "communications.phone_call_silver": "Phone Calls",
        "communications.phone_message_silver": "SMS Messages"
    }

    return [friendly_names.get(src, src) for src in sources]


def get_metadata_summary(results: list, sql: str, data_sources: List[str]) -> str:
    """
    Generate metadata summary about the query results.

    Args:
        results: Query results
        sql: SQL query
        data_sources: List of friendly table names

    Returns:
        Formatted metadata string
    """
    if not results:
        return ""

    # Get columns returned
    columns = list(results[0].keys())
    column_count = len(columns)

    # Build summary
    summary = f"**Query Metadata:**\n"
    summary += f"• Tables: {', '.join(data_sources)}\n"
    summary += f"• Columns returned: {column_count} ({', '.join(columns[:5])}"
    if column_count > 5:
        summary += f" + {column_count - 5} more"
    summary += ")\n"
    summary += f"• Rows: {len(results)}"

    return summary


def execute_with_retry(
    user_question: str,
    company_id: int,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Execute SQL query with retry on failure using LangChain agent.

    Args:
        user_question: The user's question in natural language
        company_id: The company ID to query for
        conversation_history: Optional list of previous Q&A pairs for context

    Returns:
        {
            "success": bool,
            "sql": str,
            "reasoning": str,
            "explanation": str,
            "results": list[dict],
            "error": str or None,
            "attempts": int,
            "skill": str,
            "natural_response": str,
            "data_sources": list[str],
            "metadata_summary": str
        }
    """
    print("\n" + "="*60)
    print("🤖 LANGCHAIN SQL AGENT - EXECUTION FLOW")
    print("="*60)
    print(f"📝 Question: {user_question}")
    print(f"🏢 Company ID: {company_id}")
    print(f"💬 Conversation History: {len(conversation_history) if conversation_history else 0} exchanges")

    # Show conversation context if available
    if conversation_history:
        print("\n   📜 Context from Previous Exchanges:")
        for idx, exchange in enumerate(conversation_history, 1):
            print(f"      [{idx}] Q: {exchange.get('question', '')[:60]}...")
            print(f"          A: {exchange.get('answer', '')[:60]}...")

    # Create LangChain agent
    print("\n🔧 Initializing LangChain SQL Agent...")
    agent = LangChainSQLAgent(company_id)
    print(f"   ✅ Agent created with model: {agent.model}")
    error_feedback = None

    for attempt in range(1, agent.max_retries + 1):
        print(f"\n🔄 Attempt {attempt}/{agent.max_retries}")

        # Generate SQL using LangChain agent
        print("   📊 Step 1: Generating SQL with LangChain...")
        result = agent.generate_sql(
            user_question=user_question,
            conversation_history=conversation_history,
            error_feedback=error_feedback
        )

        # Check if clarification is needed
        if result.get("needs_clarification", False):
            clarification_question = result.get("clarification_question", "Could you please clarify your question?")
            print(f"   ❓ Clarification needed: {clarification_question}")

            return {
                "success": True,  # Not an error, just needs clarification
                "sql": "",
                "reasoning": result.get("reasoning", ""),
                "explanation": result.get("explanation", ""),
                "results": [],
                "error": None,
                "attempts": attempt,
                "skill": result.get("skill", "general"),
                "natural_response": f"I need a bit more information to answer your question.\n\n**{clarification_question}**",
                "data_sources": [],
                "metadata_summary": "",
                "trajectory": {
                    "question": user_question,
                    "detected_skill": result.get("skill", "general").upper(),
                    "reasoning": result.get("reasoning", ""),
                    "explanation": "Clarification needed",
                    "sql_generated": "",
                    "attempts": attempt,
                    "rows_returned": 0,
                    "clarification_requested": True
                },
                "needs_clarification": True
            }

        sql = result.get("sql", "")
        reasoning = result.get("reasoning", "")
        explanation = result.get("explanation", "")
        skill = result.get("skill", "general")

        print(f"   🎯 Skill Detected: {skill}")
        print(f"   💭 Reasoning: {reasoning[:100]}...")
        print(f"   📝 SQL Preview: {sql[:80] if sql else 'Empty'}...")

        # Check if agent returned empty SQL
        if not sql or not sql.strip():
            print(f"   ❌ Empty SQL returned")
            error_feedback = f"Agent returned empty SQL. Explanation: {explanation}"
            continue

        # Validate SQL syntax and safety
        print("   🔍 Step 2: Validating SQL...")
        is_valid, validation_error = validate_sql(sql)
        if not is_valid:
            print(f"   ❌ Validation failed: {validation_error}")
            error_feedback = f"Validation failed: {validation_error}"
            continue
        print("   ✅ SQL validation passed")

        # Execute the query
        print("   🗄️  Step 3: Executing SQL on PostgreSQL...")
        session = None
        try:
            session = get_db_session()

            # Use text() for raw SQL execution
            cursor = session.execute(text(sql))

            # Fetch all rows
            rows = cursor.fetchall()

            # Get column names
            if cursor.returns_rows:
                columns = cursor.keys()
            else:
                columns = []

            # Convert to list of dictionaries
            results = [dict(zip(columns, row)) for row in rows]

            session.close()
            print(f"   ✅ Query executed: {len(results)} rows returned")

            # Generate natural language response using LangChain
            print("   💬 Step 4: Generating natural language response...")
            if NLG_ENABLED:
                try:
                    print(f"      Using LangChain ResponseGenerationChain (temp={agent.response_llm.temperature})")
                    natural_response = agent.generate_response(
                        user_question=user_question,
                        sql_query=sql,
                        results=results,
                        skill=skill,
                        conversation_history=conversation_history
                    )
                    print(f"   ✅ Response generated: {natural_response[:80]}...")
                except Exception as llm_error:
                    # Fallback to template-based response if LLM fails
                    print(f"   ⚠️  LangChain response generation failed, using template: {llm_error}")
                    skill_handler = SKILL_HANDLERS.get(skill, SKILL_HANDLERS["general"])
                    natural_response = skill_handler.format_response(results, sql)
            else:
                # Use template-based formatting when NLG disabled
                print("      Using template-based response (NLG disabled)")
                skill_handler = SKILL_HANDLERS.get(skill, SKILL_HANDLERS["general"])
                natural_response = skill_handler.format_response(results, sql)

            # Extract data sources from SQL
            data_sources = extract_data_sources(sql)

            # Generate metadata summary
            metadata_summary = get_metadata_summary(results, sql, data_sources)

            print("\n✅ SUCCESS! Query completed successfully")
            print("="*60)
            print("\n📄 FULL RESPONSE DETAILS:")
            print(f"   Natural Response: {natural_response}")
            print(f"   SQL Query: {sql}")
            print(f"   Rows Returned: {len(results)}")
            print(f"   Data Sources: {', '.join(data_sources)}")
            print("="*60 + "\n")

            # Build trajectory information for UI display
            trajectory_info = {
                "question": user_question,
                "detected_skill": skill.upper(),
                "reasoning": reasoning,
                "explanation": explanation,
                "sql_generated": sql,
                "attempts": attempt,
                "rows_returned": len(results)
            }

            # Success!
            return {
                "success": True,
                "sql": sanitize_sql(sql),
                "reasoning": reasoning,
                "explanation": explanation,
                "results": results,
                "error": None,
                "attempts": attempt,
                "skill": skill,
                "natural_response": natural_response,
                "data_sources": data_sources,
                "metadata_summary": metadata_summary,
                "trajectory": trajectory_info
            }

        except Exception as e:
            # Execution failed
            error_message = str(e)

            # Close session if open
            if session:
                session.close()

            # Provide detailed error feedback to agent
            error_feedback = f"Execution failed: {error_message}"

            # Continue to next attempt
            continue

    # All retries failed - format natural response for error case
    skill = result.get("skill", "general") if result else "general"
    natural_response = f"I attempted to answer your question but encountered an error: {error_feedback}"

    return {
        "success": False,
        "sql": sanitize_sql(sql) if sql else "",
        "reasoning": reasoning if 'reasoning' in locals() else "",
        "explanation": explanation if 'explanation' in locals() else "",
        "results": [],
        "error": error_feedback,
        "attempts": agent.max_retries,
        "skill": skill,
        "natural_response": natural_response
    }


def execute_sql_direct(sql: str, company_id: int) -> Dict[str, Any]:
    """
    Execute SQL query directly without retry (for testing).

    Args:
        sql: The SQL query to execute
        company_id: The company ID (for logging)

    Returns:
        {
            "success": bool,
            "results": list[dict],
            "error": str or None
        }
    """
    # Validate first
    is_valid, validation_error = validate_sql(sql)
    if not is_valid:
        return {
            "success": False,
            "results": [],
            "error": f"Validation failed: {validation_error}"
        }

    # Execute
    session = None
    try:
        session = get_db_session()
        cursor = session.execute(text(sql))
        rows = cursor.fetchall()

        if cursor.returns_rows:
            columns = cursor.keys()
        else:
            columns = []

        results = [dict(zip(columns, row)) for row in rows]
        session.close()

        return {
            "success": True,
            "results": results,
            "error": None
        }

    except Exception as e:
        if session:
            session.close()

        return {
            "success": False,
            "results": [],
            "error": str(e)
        }