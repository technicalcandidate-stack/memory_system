# AI Insurance Assistant

A natural language to SQL query system for commercial insurance communication data, powered by **LangChain** and **GPT-4o-mini**.

## Architecture

```
User Question
    ↓
Skill Router (keyword-based)
    ↓
LangChain SQL Generation Chain
    ├─ ChatPromptTemplate (skill-specific)
    ├─ ChatOpenAI (GPT-4o-mini, temp=0.1)
    └─ JsonOutputParser (Pydantic validation)
    ↓
SQL Validator (security checks)
    ↓
PostgreSQL Execution (with retry)
    ↓
LangChain Response Generation Chain
    ├─ ChatPromptTemplate (natural language)
    ├─ ChatOpenAI (temp=0.7)
    └─ StrOutputParser
    ↓
Results Display (Streamlit)
    ↓
LangChain Memory Manager (per-session history)
```

## Project Structure

```
ai_assistant/
├── config/
│   ├── database.py          # SQLAlchemy + PostgreSQL
│   └── settings.py           # Environment variables & LangChain config
├── chains/
│   ├── sql_generation_chain.py    # LangChain SQL generation
│   └── response_chain.py          # LangChain response generation
├── skills/
│   ├── base.py               # Base skill interface
│   ├── phone_calls.py        # Phone calls skill
│   ├── phone_messages.py     # SMS/text messages skill
│   ├── email_communications.py # Email & quotes skill
│   ├── companies_data.py     # Company information skill
│   └── general.py            # General fallback skill
├── agents/
│   ├── sql_agent.py          # Main LangChain agent orchestrator
│   └── skill_router.py       # Skill detection (keyword-based)
├── memory/
│   └── conversation_memory.py # LangChain memory manager
├── core/
│   ├── validator.py          # SQL validation & security
│   ├── executor.py           # SQL execution with retry
│   └── schema_loader.py      # Database schema context
└── ui/
    └── app.py                # Streamlit interface
```

## Features

- 🤖 **LangChain-Powered Agents** - Modern LLM orchestration with chains
- 🔄 **Automatic Retry Logic** - Up to 3 attempts with error feedback
- 💬 **Conversation Memory** - LangChain memory for multi-turn conversations
- 🎯 **Skill-Based Routing** - 5 specialized skills for different query types
- ✅ **SQL Validation** - Security checks before execution
- 📊 **Results Export** - Download query results as CSV
- 🌙 **Dark Theme UI** - Gemini-style Streamlit interface

## Key Components

### 🔗 LangChain Integration
- Uses LangChain chains and components for LLM orchestration
- `ChatPromptTemplate` for reusable, versioned prompt templates
- `JsonOutputParser` with Pydantic models for type-safe responses
- Built-in retry logic and error recovery

### 💾 Memory Management
- LangChain `ConversationBufferWindowMemory` for automatic conversation tracking
- Per-session memory isolation
- Configurable window size (default: 3 exchanges)

### 📝 Structured Outputs
- Pydantic models validate all LLM outputs
- Type-safe SQL generation and response formatting
- Clear error messages for debugging

### 📊 Observability
- Comprehensive logging throughout execution flow
- Optional LangSmith integration for tracing and debugging
- Memory state tracking for conversation context

## Setup Instructions

### 1. Install Dependencies

```bash
cd ai_assistant
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `ai_assistant/` directory:

```bash
# PostgreSQL (Supabase)
DATABASE_URL=postgresql://postgres.xxx:xxx@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# OpenAI
OPENAI_API_KEY=sk-...

# LangChain Configuration (Optional)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=ai-assistant

# LLM Configuration
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE_SQL=0.1
LLM_TEMPERATURE_RESPONSE=0.7
LLM_TIMEOUT=30
LLM_MAX_RETRIES=2

# Memory Configuration
MEMORY_WINDOW_SIZE=3

# SQL Agent Config
MAX_RETRIES=3
SQL_TIMEOUT_SECONDS=30
NLG_ENABLED=true
NLG_MAX_ROWS=10
```

### 3. Test Database Connection

```bash
python -c "from config.database import test_connection; print('Connected!' if test_connection() else 'Failed')"
```

### 4. Run the Streamlit App

```bash
streamlit run ui/app.py
```

The app will open in your browser at `http://localhost:8501`

## How LangChain Components Work

### 1. SQL Generation Chain

**Location**: `chains/sql_generation_chain.py`

```python
# Prompt Template
ChatPromptTemplate([
    SystemMessage(skill_context),  # Skill-specific schema
    HumanMessage(user_question + conversation_history)
])

# Chain Flow
prompt | ChatOpenAI(temp=0.1) | JsonOutputParser(SQLGenerationOutput)

# Output (Pydantic validated)
{
    "reasoning": "Why these tables...",
    "sql": "SELECT ...",
    "explanation": "What the query does"
}
```

### 2. Response Generation Chain

**Location**: `chains/response_chain.py`

```python
# Prompt Template
ChatPromptTemplate([
    SystemMessage(skill_guidelines),
    HumanMessage(question + results + history)
])

# Chain Flow
prompt | ChatOpenAI(temp=0.7) | StrOutputParser()

# Output
"The business has 2 email addresses and 1 phone number..."
```

### 3. Conversation Memory

**Location**: `memory/conversation_memory.py`

```python
# LangChain Memory (per session)
ConversationBufferWindowMemory(
    k=3,  # Remember last 3 exchanges
    return_messages=True,
    memory_key="chat_history"
)

# Automatic tracking
memory.save_context({"question": "..."}, {"answer": "..."})
history = memory.load_memory_variables({})
```

### 4. Main Agent Orchestrator

**Location**: `agents/sql_agent.py`

```python
class LangChainSQLAgent:
    def __init__(self, company_id):
        # Two LLM instances with different temperatures
        self.sql_llm = ChatOpenAI(temp=0.1)      # Deterministic SQL
        self.response_llm = ChatOpenAI(temp=0.7)  # Natural responses

        # Chain caching (one per skill)
        self.sql_chains = {}
        self.response_chain = ResponseGenerationChain(self.response_llm)

    def generate_sql(self, question, history, error_feedback):
        skill = self.skill_router.detect_skill(question)
        chain = self._get_sql_chain(skill)
        return chain.generate(question, history, error_feedback)

    def generate_response(self, question, sql, results, skill, history):
        return self.response_chain.generate(question, sql, results, skill, history)
```

## Skills System

### 5 Specialized Skills:

1. **Phone Calls** - Call records, voicemails, recording summaries (`phone_call_silver`)
2. **Phone Messages** - SMS/text messages (`phone_message_silver`)
3. **Email Communications** - Emails, quotes, pricing, account activity (`emails_silver`)
4. **Companies Data** - Company info, contacts, business details (`companies`)
5. **General** - Fallback for any other queries (all tables)

Each skill provides:
- Skill-specific schema context (as LangChain prompt templates)
- Custom response formatting (fallback if LLM fails)
- Example queries for few-shot learning

## Usage Examples

### Example 1: Phone Calls
```
User: "What was the last phone call?"

Flow:
1. Skill Router → phone_calls (keyword: "call")
2. SQL Chain → SELECT * FROM communications.phone_call_silver WHERE matched_company_id = 29447 ORDER BY call_timestamp DESC LIMIT 1
3. Execute → Results
4. Response Chain → "The most recent call was on January 9, 2026. The customer called about..."
5. Memory → Saves Q&A for context
```

### Example 2: Email/Quotes
```
User: "What quotes were sent?"

Flow:
1. Skill Router → email_communications (keyword: "quotes")
2. SQL Chain → SELECT * FROM communications.emails_silver WHERE matched_company_id = 29447 AND category = 'QUOTE'
3. Execute → Results
4. Response Chain → "On January 9, 2026, Harper sent a quote for $1,433.88..."
```

### Example 3: Follow-up Question
```
User: "What was the last call?"
Assistant: "The last call was from John on Jan 9..."

User: "What did they discuss?"

Flow:
1. Memory retrieves previous exchange
2. SQL Chain sees context: "previous question was about the last call"
3. Understands "they" = the caller from previous answer
4. Generates query using recording_summary field
```

## Configuration Options

### LLM Settings

- `LLM_MODEL`: Model name (default: `gpt-4o-mini`)
- `LLM_TEMPERATURE_SQL`: Temperature for SQL generation (default: `0.1`)
- `LLM_TEMPERATURE_RESPONSE`: Temperature for responses (default: `0.7`)
- `LLM_TIMEOUT`: Request timeout in seconds (default: `30`)
- `LLM_MAX_RETRIES`: LangChain retry attempts (default: `2`)

### Memory Settings

- `MEMORY_WINDOW_SIZE`: Number of conversation turns to remember (default: `3`)

### SQL Settings

- `MAX_RETRIES`: SQL generation retry attempts (default: `3`)
- `SQL_TIMEOUT_SECONDS`: SQL execution timeout (default: `30`)
- `NLG_ENABLED`: Use LLM for responses (default: `true`)

## Testing

### Test Individual Components

```bash
# Test SQL generation chain
python -c "from agents.sql_agent import LangChainSQLAgent; agent = LangChainSQLAgent(29447); print(agent.generate_sql('What are the contact details?'))"

# Test conversation memory
python -c "from memory.conversation_memory import ConversationMemoryManager; mgr = ConversationMemoryManager(); mgr.add_exchange('test', 'Q1', 'A1'); print(mgr.get_conversation_history('test'))"

# Test executor
python -c "from core.executor import execute_with_retry; result = execute_with_retry('What are the contact details?', 29447); print(f\"Success: {result['success']}\")"
```

## LangSmith Tracing (Optional)

Enable LangSmith for debugging and tracing:

```bash
# In .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls-...
LANGCHAIN_PROJECT=ai-assistant
```

Then run queries and view traces at https://smith.langchain.com

## Performance

- **Average Query Time**: 2-5 seconds
- **API Cost per Query**: ~$0.01-0.02 (GPT-4o-mini)
- **Success Rate**: >95% on first attempt, ~100% with retries
- **Memory Overhead**: Minimal (3-5 exchanges per session)

## Troubleshooting

### "No module named 'langchain'"
```bash
pip install -r requirements.txt
```

### "OPENAI_API_KEY environment variable is not set"
```bash
# Create .env file with:
OPENAI_API_KEY=sk-...
```

### "Memory not persisting across questions"
- Check that session_id is consistent
- Verify `ConversationMemoryManager` is in `st.session_state`

### "LangChain version conflicts"
```bash
pip install --upgrade langchain langchain-openai langchain-core
```

## Future Enhancements

- [ ] LLM-based skill routing (instead of keyword)
- [ ] Streaming responses with `astream()`
- [ ] Multi-provider support (Anthropic Claude, etc.)
- [ ] LangGraph for complex agent workflows
- [ ] Vector database for semantic search
- [ ] Query caching with LangChain cache
- [ ] Agent tools for complex operations
- [ ] Async execution for concurrent queries