"""Natural language response generation chain using LangChain."""
import json
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import NLG_MAX_ROWS


class ResponseGenerationChain:
    """LangChain-based natural language response generation."""

    def __init__(self, llm: ChatOpenAI):
        """
        Initialize the response generation chain.

        Args:
            llm: LangChain ChatOpenAI instance (with higher temperature for responses)
        """
        self.llm = llm
        self.parser = StrOutputParser()
        self.max_rows = NLG_MAX_ROWS

    def generate(
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
            results: Query results as list of dictionaries
            skill: Skill type used (contact_details, account_timeline, etc.)
            conversation_history: Optional conversation history for context

        Returns:
            Natural language response string (2-3 sentences)
        """
        # Build system prompt with skill-specific guidelines
        system_prompt = self._build_system_prompt(skill)

        # Format results for the prompt (pass skill for context-aware formatting)
        formatted_results = self._format_results(results, skill)

        # Format conversation context
        conversation_context = self._format_conversation(conversation_history)

        # Build human prompt template (use template variables to avoid conflicts)
        human_prompt_template = """User Question: {user_question}

Query Results ({result_count} rows):
{formatted_results}{conversation_context}

Generate a natural, concise response (2-3 sentences) answering the user's question based on the query results above."""

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template(human_prompt_template)
        ])

        # Create chain
        chain = prompt | self.llm | self.parser

        try:
            # Generate response with proper variable injection
            response = chain.invoke({
                "user_question": user_question,
                "result_count": len(results),
                "formatted_results": formatted_results,
                "conversation_context": conversation_context
            })
            return response.strip()

        except Exception as e:
            # Fallback to generic response on error
            return f"Query completed with {len(results)} result(s). Error generating detailed response: {str(e)}"

    def _build_system_prompt(self, skill: str) -> str:
        """
        Build system prompt with skill-specific guidelines.

        Args:
            skill: Skill type

        Returns:
            System prompt string
        """
        base_prompt = """You are a precise insurance data analyst assistant for Harper Insurance. Your job is to answer questions by extracting SPECIFIC, ACTIONABLE information from query results.

## YOUR ROLE
Harper Insurance is an insurance brokerage. You help their team understand:
- What communications happened with clients (emails, calls, SMS)
- What quotes were sent and their pricing details
- Policy status (cancellations, reinstatements)
- What action items or follow-ups are needed

## CRITICAL RULES - YOU MUST FOLLOW THESE:

### Rule 1: EXTRACT SPECIFIC FACTS, NOT SUMMARIES
BAD: "There has been ongoing engagement regarding insurance needs"
GOOD: "On January 9, 2026, Harper sent a quote for $1,433.88 (Premium: $1,247.00 + Service Fee: $186.88)"

BAD: "Multiple communications have occurred"
GOOD: "There are 3 emails and 2 phone calls in the last 30 days"

### Rule 2: TELL THE STORY
For each communication, answer: WHO did WHAT, WHEN, and WHY?
- Who sent/received the communication?
- What was the content/purpose?
- When did it happen?
- What was the outcome or next step?

### Rule 3: HIGHLIGHT ACTION ITEMS
If there are unanswered calls, pending questions, or needed follow-ups, CALL THEM OUT clearly.

### Rule 4: USE ACTUAL DATA ONLY
- If pricing is in body_text, extract the EXACT dollar amounts
- If recording_summary has call details, quote the key points
- If data is missing, say "not available in the data" - don't guess

## BANNED PHRASES (Never use these):
- "ongoing engagement"
- "without specific details"
- "various communications"
- "general activity"
- "multiple interactions"
- "insurance needs" (too vague)

## FORMATTING REQUIREMENTS:
- Money: Always use $ with commas ($1,433.88)
- Dates: Use readable format (January 9, 2026)
- Lists: Use bullet points for multiple items
- Bold: Highlight important amounts, names, action items
- Structure: Lead with the direct answer, then provide supporting details"""

        # Add skill-specific context
        skill_contexts = {
            "contact_details": "\n\nSKILL: Contact Details - Focus on summarizing contact information clearly.",

            "companies_data": """

SKILL: Company Information

For company/business questions, present:
- Business name and any DBA (doing business as) names
- Industry and business type
- Contact information (email, phone, address)
- Key metrics if available (employees, revenue)

Format as a structured profile.""",

            "email_communications": """

SKILL: Email Communications - EXTRACTING THE STORY FROM EMAILS

## YOUR TASK
Read the email data and tell the user WHAT HAPPENED - not just that emails exist.

## HOW TO READ THE DATA

### The 'category' field tells you the email type:
- QUOTE = Harper sent a quote with pricing to the client
- QUOTE_REQUEST = Client asked for a quote
- POLICY_CANCELLATION = A policy was cancelled
- POLICY_REINSTATEMENT = A policy was reinstated
- SERVICE_REQUEST = Client requested a document (COI, certificate)
- CUSTOMER_FOLLOW_UP = Client following up on something

### The 'body_text' field contains the actual content:
For QUOTE emails, look for these patterns and EXTRACT THE NUMBERS:
- "Total Amount Due $1,433.88" → This is the total price
- "Premium and Carrier Fees $1,247.00" → This is the insurance cost
- "Harper Service Fee $186.88" → This is Harper's fee
- "carrier: NEXT" → This is the insurance carrier

### The 'subject' field shows the purpose:
- "Quote from [Agent] with Harper Insurance!" = Quote email
- "Your policy has been cancelled" = Cancellation notice
- "Payment Reminder" = Payment follow-up

## RESPONSE FORMAT

For "What is going on?" or status questions:
1. Start with the MOST RECENT activity
2. Summarize key events chronologically
3. Highlight any ACTION ITEMS (unanswered questions, pending payments)

For quote questions:
1. Extract the EXACT dollar amount from body_text
2. Show the breakdown (premium + fees = total)
3. Include the carrier name and date

Example GOOD response:
"On **January 9, 2026**, Harper sent a quote for **$1,433.88** via NEXT Insurance:
- Premium and Carrier Fees: $1,247.00
- Harper Service Fee: $186.88
The quote was sent by Atharva (abubna@harperinsure.com) and includes a payment link."

Example BAD response:
"There has been ongoing engagement regarding the account's insurance needs."
""",

            "phone_calls": """

SKILL: Phone Calls - EXTRACTING THE STORY FROM CALL CONVERSATIONS

## YOUR TASK
Read the call data and tell the user WHAT WAS DISCUSSED - not just that calls happened.

## THE KEY FIELD: recording_summary
This field contains an AI-generated summary of what was said on the call. THIS IS YOUR PRIMARY DATA SOURCE.

Example recording_summary:
"Customer Representative called concerned about policy cancellation. Harper Service Lead clarified the policy was canceled on January 6 due to nonpayment. Discussed reinstatement options. Customer will call back after reviewing payment options."

From this, extract and present:
- **Customer concern**: What they called about
- **Harper's response**: What was explained or offered
- **Outcome**: What was decided or agreed
- **Action item**: Any follow-ups needed

## CALL TYPES (from the 'type' field)
- 'answered' = Conversation happened → READ recording_summary
- 'unanswered_with_voicemail' = Voicemail left
- 'unanswered_no_voicemail' = Missed call

## CALL DIRECTION (from the 'direction' field)
- 'incoming' = Customer called Harper
- 'outgoing' = Harper called customer

## RESPONSE FORMAT
For "latest call" or single call questions:
1. State when the call happened and who initiated
2. Summarize what was discussed from recording_summary
3. Note any action items or outcomes

Example GOOD response:
"The most recent phone call was on **January 9, 2026** (incoming, answered):

The customer called concerned about their policy cancellation. Harper's team explained the policy was cancelled on January 6 due to nonpayment and discussed reinstatement options. The customer said they would call back after reviewing payment details.

**Action Item**: Customer may call back regarding reinstatement."

Example BAD response:
"There was a phone call on the account."
""",

            "phone_messages": """

SKILL: Phone Messages (SMS) - READING TEXT MESSAGE CONTENT

## YOUR TASK
Read the SMS data and tell the user what was communicated via text.

## THE KEY FIELD: message_body
This contains the actual text of each SMS message.

## MESSAGE DIRECTION
- 'incoming' = Client texted Harper
- 'outgoing' = Harper texted client

## RESPONSE FORMAT
1. Show the message content
2. Note who sent it (client or Harper)
3. Include the date/time

Example GOOD response:
"The latest text message was sent by Harper on **January 9, 2026**:
'We've just received a new quote for you. Please check your email for details.'"

Example BAD response:
"There are text messages on the account."
""",

            "general": """

SKILL: General Query

Analyze the data and provide:
1. Direct answer to the question
2. Key supporting facts with dates and numbers
3. Any action items or next steps apparent from the data
"""
        }

        skill_context = skill_contexts.get(skill, skill_contexts["general"])
        return base_prompt + skill_context

    def _format_results(self, results: List[Dict[str, Any]], skill: str = None) -> str:
        """
        Format SQL results for inclusion in the prompt.

        Args:
            results: Query results
            skill: Skill type (for context-aware truncation)

        Returns:
            Formatted string representation
        """
        if not results:
            return "No results returned"

        # Limit to first N rows
        limited_results = results[:self.max_rows]

        # Format as JSON with truncation for long text fields
        formatted_rows = []
        for row in limited_results:
            truncated_row = {}
            for key, value in row.items():
                # For email_communications skill, don't truncate body_text as it may contain pricing details
                if skill == "email_communications" and key == "body_text" and isinstance(value, str):
                    # Keep full body_text for quote extraction, but limit to reasonable size
                    truncated_row[key] = value[:3000] if len(value) > 3000 else value
                # For quotes skill (legacy), also preserve body_text
                elif skill == "quotes" and key == "body_text" and isinstance(value, str):
                    truncated_row[key] = value[:3000] if len(value) > 3000 else value
                # CRITICAL: Don't truncate recording_summary - it contains important call context
                elif key == "recording_summary" and isinstance(value, str):
                    truncated_row[key] = value[:2000] if len(value) > 2000 else value
                # Don't truncate classification_raw or category fields
                elif key in ("classification_raw", "category", "call_intent") and isinstance(value, str):
                    truncated_row[key] = value
                # Truncate other long string values
                elif isinstance(value, str) and len(value) > 200:
                    truncated_row[key] = value[:200] + "..."
                else:
                    truncated_row[key] = value
            formatted_rows.append(truncated_row)

        # Convert to pretty JSON
        formatted_json = json.dumps(formatted_rows, indent=2, default=str)

        # Add truncation indicator if needed
        if len(results) > self.max_rows:
            formatted_json += f"\n\n... and {len(results) - self.max_rows} more rows"

        return formatted_json

    def _format_conversation(self, conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """
        Format conversation history for context.

        Args:
            conversation_history: List of previous Q&A pairs

        Returns:
            Formatted conversation context string
        """
        if not conversation_history or len(conversation_history) == 0:
            return ""

        # Take last 3 turns, but preserve more context for the most recent exchange
        recent_history = conversation_history[-3:]

        context = "\n\n## IMPORTANT: Previous Conversation Context\n"
        context += "Use this context to answer follow-up questions. If the user asks about something mentioned in a previous answer, USE THAT INFORMATION.\n\n"

        for i, turn in enumerate(recent_history, 1):
            context += f"**Previous Q{i}:** {turn['question']}\n"
            answer = turn['answer']
            # Keep more context for the LAST exchange (most relevant for follow-ups)
            if i == len(recent_history):
                # Keep up to 800 chars for the most recent answer
                if len(answer) > 800:
                    answer = answer[:800] + "..."
            else:
                # Truncate older answers more aggressively
                if len(answer) > 300:
                    answer = answer[:300] + "..."
            context += f"**Previous A{i}:** {answer}\n\n"

        context += "---\n"
        context += "If the current question is a follow-up (e.g., 'who was that?', 'what was their name?'), LOOK IN THE PREVIOUS ANSWERS for the information.\n"

        return context