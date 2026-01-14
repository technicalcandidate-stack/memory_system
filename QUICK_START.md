# Quick Start Guide - AI Insurance Assistant

Get up and running with the LangChain-powered AI assistant in 5 minutes.

## Prerequisites

- Python 3.9+
- PostgreSQL database access (Supabase)
- OpenAI API key

## Installation

```bash
# Navigate to the ai_assistant folder
cd ai_assistant

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file:

```bash
# Required
DATABASE_URL=postgresql://your-connection-string
OPENAI_API_KEY=sk-your-key-here

# Optional (defaults shown)
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE_SQL=0.1
LLM_TEMPERATURE_RESPONSE=0.7
MEMORY_WINDOW_SIZE=3
MAX_RETRIES=3
```

## Run the App

```bash
streamlit run ui/app.py
```

Open http://localhost:8501 in your browser.

## Test Individual Components

### Test Database Connection
```bash
python -c "from config.database import test_connection; print('✅ Connected!' if test_connection() else '❌ Failed')"
```

### Test SQL Generation
```python
from agents.sql_agent import LangChainSQLAgent

agent = LangChainSQLAgent(company_id=29447)
result = agent.generate_sql("What are the contact details?")
print(f"SQL: {result['sql']}")
```

### Test Conversation Memory
```python
from memory.conversation_memory import ConversationMemoryManager

memory = ConversationMemoryManager()
memory.add_exchange("test_session", "What's the email?", "contact@example.com")
memory.add_exchange("test_session", "What about phone?", "+1234567890")

history = memory.get_conversation_history("test_session")
print(f"History: {history}")
```

### Test Full Execution
```python
from core.executor import execute_with_retry

result = execute_with_retry(
    user_question="What are the contact details?",
    company_id=29447
)

print(f"Success: {result['success']}")
print(f"SQL: {result['sql']}")
print(f"Response: {result['natural_response']}")
```

## Example Queries

Try these in the UI:

1. **Phone Calls**
   - "What was the last phone call?"
   - "Show me recent calls"
   - "Any voicemails?"

2. **Phone Messages (SMS)**
   - "Show me text messages"
   - "Any SMS from the client?"

3. **Email Communications**
   - "What quotes were sent?"
   - "What's going on with this account?"
   - "Show me recent emails"

4. **Company Data**
   - "What are the contact details?"
   - "What's the email address?"
   - "How many employees do they have?"

5. **General Queries**
   - "Show me all activity from last month"
   - "What happened recently?"

## Architecture Overview

```
┌─────────────────┐
│   Streamlit UI  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LangChain      │
│  SQL Agent      │
├─────────────────┤
│ • Skill Router  │
│ • SQL Chain     │
│ • Response Chain│
│ • Memory Mgr    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Executor      │
├─────────────────┤
│ • Validator     │
│ • PostgreSQL    │
│ • Retry Logic   │
└─────────────────┘
```

## Key Files

- `agents/sql_agent.py` - Main LangChain agent orchestrator
- `chains/sql_generation_chain.py` - SQL generation chain
- `chains/response_chain.py` - Response generation chain
- `memory/conversation_memory.py` - LangChain memory manager
- `core/executor.py` - SQL execution with retry
- `ui/app.py` - Streamlit interface

## Troubleshooting

### ImportError: No module named 'langchain'
```bash
pip install -r requirements.txt
```

### Database connection failed
- Check DATABASE_URL in .env
- Test with: `python -c "from config.database import test_connection; print(test_connection())"`

### LangChain memory not working
- Ensure memory_manager is in st.session_state
- Check session_id is consistent across requests

### SQL validation errors
- Review error message in UI debug info
- Check that query includes company_id filter
- Ensure only SELECT queries (no INSERT/UPDATE/DELETE)

## LangSmith Tracing (Optional)

Enable detailed tracing:

```bash
# In .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls-your-key
LANGCHAIN_PROJECT=ai-assistant
```

View traces at https://smith.langchain.com

## Next Steps

1. ✅ Get the app running
2. Try example queries
3. Review the architecture in README.md
4. Customize skills for your use case
5. Enable LangSmith for production monitoring
6. Explore advanced LangChain features

## Support

- README.md - Detailed documentation
- LangChain docs - https://python.langchain.com
- LangSmith tracing - https://smith.langchain.com
