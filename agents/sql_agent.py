"""Main LangChain-based SQL agent orchestrator."""
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from config.settings import (
    LLM_MODEL,
    LLM_TEMPERATURE_SQL,
    LLM_TEMPERATURE_RESPONSE,
    LLM_TIMEOUT,
    LLM_MAX_RETRIES,
    MAX_RETRIES
)
from chains.sql_generation_chain import SQLGenerationChain
from chains.response_chain import ResponseGenerationChain
from agents.skill_router import SkillDetector
from skills import SKILL_HANDLERS


class LangChainSQLAgent:
    """
    Main agent orchestrator using LangChain for text-to-SQL conversion.

    This agent:
    - Routes questions to appropriate skills
    - Uses LangChain chains for SQL generation
    - Manages conversation context
    - Coordinates with validator and executor
    """

    def __init__(self, company_id: int, model: str = None):
        """
        Initialize the LangChain SQL agent.

        Args:
            company_id: Company ID to query for
            model: Optional LLM model override
        """
        self.company_id = company_id
        self.model = model or LLM_MODEL
        self.max_retries = MAX_RETRIES

        # Initialize LLM instances with different temperatures
        self.sql_llm = ChatOpenAI(
            model=self.model,
            temperature=LLM_TEMPERATURE_SQL,  # Low for deterministic SQL
            timeout=LLM_TIMEOUT,
            max_retries=LLM_MAX_RETRIES
        )

        self.response_llm = ChatOpenAI(
            model=self.model,
            temperature=LLM_TEMPERATURE_RESPONSE,  # Higher for natural responses
            timeout=LLM_TIMEOUT,
            max_retries=LLM_MAX_RETRIES
        )

        # Initialize skill router
        self.skill_router = SkillDetector()

        # Cache for SQL generation chains (one per skill)
        self.sql_chains: Dict[str, SQLGenerationChain] = {}

        # Response generation chain (shared)
        self.response_chain = ResponseGenerationChain(self.response_llm)

    def _get_sql_chain(self, skill: str) -> SQLGenerationChain:
        """
        Get or create SQL generation chain for a skill.

        Args:
            skill: Skill name

        Returns:
            SQL generation chain with skill-specific context
        """
        if skill not in self.sql_chains:
            # Get skill handler and context
            skill_handler = SKILL_HANDLERS.get(skill, SKILL_HANDLERS["general"])
            context_template = skill_handler.get_context_template()

            # Create chain with skill context
            self.sql_chains[skill] = SQLGenerationChain(
                llm=self.sql_llm,
                skill_context=context_template,
                company_id=self.company_id
            )

        return self.sql_chains[skill]

    def generate_sql(
        self,
        user_question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        error_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question.

        Args:
            user_question: User's natural language question
            conversation_history: Optional list of previous Q&A pairs
            error_feedback: Optional error feedback from previous attempt

        Returns:
            Dictionary with:
            - skill: Detected skill name
            - reasoning: Why these tables/columns were chosen
            - sql: Generated SQL query
            - explanation: What the query does
            - success: Whether generation succeeded
        """
        # Detect skill from question
        skill = self.skill_router.detect_skill(user_question)

        print("\n" + "="*80)
        print("🧠 SQL GENERATION TRAJECTORY")
        print("="*80)
        print(f"\n📝 User Question: {user_question}")
        print(f"\n🎯 Detected Skill: {skill.upper()}")

        if conversation_history:
            print(f"\n💬 Conversation Context: {len(conversation_history)} previous exchange(s)")

        if error_feedback:
            print(f"\n⚠️  Error Feedback from Previous Attempt:")
            print(f"   {error_feedback[:200]}...")

        # Get appropriate SQL generation chain
        sql_chain = self._get_sql_chain(skill)

        # Generate SQL
        print(f"\n🔄 Invoking LangChain SQL Generation Chain...")
        print(f"   Model: {self.model}")
        print(f"   Temperature: {LLM_TEMPERATURE_SQL}")

        result = sql_chain.generate(
            user_question=user_question,
            conversation_history=conversation_history,
            error_feedback=error_feedback
        )

        # Add skill
        result["skill"] = skill

        # Check if clarification is needed
        if result.get("needs_clarification", False):
            result["success"] = False
            print(f"\n❓ CLARIFICATION NEEDED:")
            print(f"   {result.get('clarification_question', 'Could you please clarify?')}")
            print(f"\n💭 Reasoning: {result.get('reasoning', 'N/A')}")
            print("="*80 + "\n")
            return result

        # Set success flag for SQL generation
        result["success"] = bool(result.get("sql"))

        # Print LLM's thinking trajectory
        print(f"\n💭 LLM Reasoning:")
        print(f"   {result.get('reasoning', 'N/A')}")

        print(f"\n📖 LLM Explanation:")
        print(f"   {result.get('explanation', 'N/A')}")

        print(f"\n🔍 Generated SQL Query:")
        sql = result.get('sql', 'N/A')
        if sql and sql != 'N/A':
            # Pretty print SQL with indentation
            for line in sql.split('\n'):
                print(f"   {line}")
        else:
            print(f"   {sql}")

        print(f"\n✅ Generation Status: {'SUCCESS' if result['success'] else 'FAILED'}")
        print("="*80 + "\n")

        return result

    def generate_response(
        self,
        user_question: str,
        sql_query: str,
        results: List[Dict[str, Any]],
        skill: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate natural language response from SQL results.

        Args:
            user_question: User's original question
            sql_query: Executed SQL query
            results: Query results
            skill: Skill that was used
            conversation_history: Optional conversation history

        Returns:
            Natural language response string
        """
        print("\n" + "="*80)
        print("💬 RESPONSE GENERATION TRAJECTORY")
        print("="*80)
        print(f"\n📊 Query Results: {len(results)} row(s) returned")
        print(f"\n🎯 Using Skill: {skill.upper()}")
        print(f"\n🔄 Invoking LangChain Response Generation Chain...")
        print(f"   Model: {self.model}")
        print(f"   Temperature: {LLM_TEMPERATURE_RESPONSE}")

        # Show a preview of results for quotes skill
        if skill == "quotes" and results and len(results) > 0:
            first_result = results[0]
            print(f"\n📧 Email Preview:")
            print(f"   Sender: {first_result.get('sender_name', 'N/A')} ({first_result.get('sender_email', 'N/A')})")
            print(f"   Subject: {first_result.get('subject', 'N/A')}")
            print(f"   Date: {first_result.get('received_date', 'N/A')}")
            if 'body_text' in first_result:
                body_preview = first_result['body_text'][:300] if first_result['body_text'] else 'N/A'
                print(f"   Body Preview: {body_preview}...")

        try:
            response = self.response_chain.generate(
                user_question=user_question,
                sql_query=sql_query,
                results=results,
                skill=skill,
                conversation_history=conversation_history
            )

            print(f"\n✅ Response Generated Successfully")
            print(f"\n📝 Final Response Preview:")
            preview = response[:200] if len(response) > 200 else response
            print(f"   {preview}{'...' if len(response) > 200 else ''}")
            print("="*80 + "\n")

            return response

        except Exception as e:
            print(f"\n⚠️  Response Generation Failed: {str(e)}")
            print(f"\n🔄 Falling back to skill-based template response")

            # Fallback to skill-based template response
            skill_handler = SKILL_HANDLERS.get(skill, SKILL_HANDLERS["general"])
            fallback_response = skill_handler.format_response(results, sql_query)

            print(f"\n📝 Fallback Response:")
            print(f"   {fallback_response}")
            print("="*80 + "\n")

            return fallback_response

    def process_query(
        self,
        user_question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a complete query (generate SQL only, execution happens in executor).

        Args:
            user_question: User's natural language question
            conversation_history: Optional conversation history

        Returns:
            Dictionary with SQL generation results
        """
        result = self.generate_sql(
            user_question=user_question,
            conversation_history=conversation_history
        )

        return result