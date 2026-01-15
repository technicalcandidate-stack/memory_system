"""SQL generation chain using LangChain."""
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


class SQLGenerationOutput(BaseModel):
    """Output schema for SQL generation."""
    needs_clarification: bool = Field(default=False, description="Set to true when the question is too vague to determine what data to query. Examples REQUIRING clarification: 'show me the data', 'give me data', 'show me stuff', 'get info', 'what about them?'. Examples NOT needing clarification: 'what's going on?' (all communications), 'show me emails' (emails table), 'recent calls' (calls table), 'account status' (UNION ALL communications), 'recent activity' (recent communications with LIMIT 20).")
    clarification_question: str = Field(default="", description="If needs_clarification is true, provide a SPECIFIC, actionable question with options. Example: 'What information would you like to see? Recent communications (emails/calls/texts), company details, quotes, or something else?' Keep it conversational and provide clear choices.")
    reasoning: str = Field(description="Detailed reasoning explaining: 1) Why these specific tables were chosen (including why UNION ALL was used if combining tables), 2) Why these specific columns were selected, 3) Why each WHERE clause filter was included, 4) Why this specific JOIN strategy was used (if applicable), 5) Why certain rows/data are being excluded. For overview questions, explain why you're querying multiple tables. Be explicit about every decision made in the query.")
    sql: str = Field(default="", description="The generated SQL query. Leave empty if needs_clarification is true. For account overview/status questions, use UNION ALL to combine emails, calls, and SMS.")
    explanation: str = Field(description="What the query does in plain English. For multi-table queries, explain that you're combining data from multiple sources for a comprehensive view.")


class SQLGenerationChain:
    """LangChain-based SQL generation chain with skill-specific context."""

    def __init__(self, llm: ChatOpenAI, skill_context: str, company_id: int):
        """
        Initialize the SQL generation chain.

        Args:
            llm: LangChain ChatOpenAI instance
            skill_context: Skill-specific schema context template
            company_id: Company ID to inject into context
        """
        self.llm = llm
        self.company_id = company_id
        self.parser = JsonOutputParser(pydantic_object=SQLGenerationOutput)

        # Format skill context with company_id
        formatted_context = skill_context.format(company_id=company_id)

        # Create system message template
        system_template = SystemMessagePromptTemplate.from_template(formatted_context)

        # Create human message template
        human_template = HumanMessagePromptTemplate.from_template(
            """{conversation_context}{user_question_section}{error_section}
Generate a SQL query to answer this question.

{format_instructions}"""
        )

        # Combine into chat prompt
        self.prompt = ChatPromptTemplate.from_messages([
            system_template,
            human_template
        ])

        # Create the chain
        self.chain = self.prompt | self.llm | self.parser

    def generate(
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
            Dictionary with reasoning, sql, and explanation
        """
        # Format conversation context
        conversation_context = self._format_conversation(conversation_history)

        # Format user question section
        user_question_section = f"\nUser Question: {user_question}\n"

        # Format error feedback section
        if error_feedback:
            error_section = f"\nPREVIOUS ERROR: {error_feedback}\n\nPlease fix the SQL query based on the error above.\n"
        else:
            error_section = ""

        # Get format instructions from parser
        format_instructions = self.parser.get_format_instructions()

        try:
            # Run the chain
            result = self.chain.invoke({
                "conversation_context": conversation_context,
                "user_question_section": user_question_section,
                "error_section": error_section,
                "format_instructions": format_instructions
            })

            # Check if clarification is needed
            if result.get("needs_clarification", False):
                return {
                    "needs_clarification": True,
                    "clarification_question": result.get("clarification_question", "Could you please clarify your question?"),
                    "reasoning": result.get("reasoning", "Question requires clarification"),
                    "sql": "",
                    "explanation": "Clarification needed before generating SQL"
                }

            # Validate result has required fields
            if "sql" not in result or not result["sql"]:
                return {
                    "needs_clarification": False,
                    "clarification_question": "",
                    "reasoning": result.get("reasoning", "No reasoning provided"),
                    "sql": "",
                    "explanation": "Failed to generate SQL query"
                }

            # Ensure clarification fields are present in successful result
            result["needs_clarification"] = False
            result["clarification_question"] = ""
            return result

        except Exception as e:
            return {
                "needs_clarification": False,
                "clarification_question": "",
                "reasoning": "Chain execution failed",
                "sql": "",
                "explanation": f"Error generating SQL: {str(e)}"
            }

    def _format_conversation(self, conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """
        Format conversation history for the prompt.

        Args:
            conversation_history: List of {'question': ..., 'answer': ...} dicts

        Returns:
            Formatted conversation context string
        """
        if not conversation_history or len(conversation_history) == 0:
            return ""

        # Take only last 3 exchanges to keep context manageable
        recent_history = conversation_history[-3:]

        context = "\n\n## IMPORTANT: CONVERSATION HISTORY\n"
        context += "Use this history to understand follow-up questions. If the user refers to something from a previous answer (names, dates, amounts), USE that information.\n\n"

        for i, exchange in enumerate(recent_history, 1):
            context += f"### Exchange {i}:\n"
            context += f"**User asked:** {exchange.get('question', 'N/A')}\n"

            # Keep more context for the most recent answer (most relevant for follow-ups)
            answer = exchange.get('answer', 'N/A')
            if i == len(recent_history):
                # Keep up to 600 chars for the most recent answer
                if len(answer) > 600:
                    answer = answer[:600] + "..."
            else:
                # Truncate older answers more
                if len(answer) > 300:
                    answer = answer[:300] + "..."

            context += f"**Answer:** {answer}\n\n"

        context += "---\n"
        context += "**FOLLOW-UP DETECTION:** If the current question references 'they', 'them', 'that', 'who', 'what was', etc., look in the previous answers for the relevant information.\n"

        return context