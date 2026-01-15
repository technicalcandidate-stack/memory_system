# AI Insurance Assistant

A multi-agent natural language interface for commercial insurance data, powered by **LangGraph**, **LangChain**, and **GPT-4o-mini**. Intelligently routes queries between structured database operations and semantic document search.

## Architecture

### Multi-Agent Orchestration Flow

```
User Question (Streamlit UI)
         ↓
┌────────────────────────────────────────┐
│   MultiAgentOrchestrator (LangGraph)   │
│   Primary Entry Point                  │
└──────────────┬─────────────────────────┘
               ↓
        ┌──────────────┐
        │  Supervisor  │ ← GPT-4o-mini routing decision
        │    Node      │
        └──────┬───────┘
               │
    ┌──────────┴──────────────┐
    │  Conditional Routing    │
    └─┬────────┬──────────┬───┘
      │        │          │
   sql_only  document  hybrid
      │        search     │
      ↓        ↓          ↓
   ┌─────┐  ┌─────┐  ┌─────────┐
   │ SQL │  │ Doc │  │SQL→Doc  │
   │Agent│  │Agent│  │Parallel │
   └──┬──┘  └──┬──┘  └────┬────┘
      │        │           │
      └────────┴───────────┘
               ↓
        ┌──────────────┐
        │ Synthesizer  │ ← Combines multi-agent responses
        │    Node      │
        └──────┬───────┘
               ↓
         Final Response
```

### SQL Agent Sub-Pipeline

```
User Question + Conversation History
         ↓
  Skill Router (keyword-based)
         ↓
  SQLGenerationChain
  ├─ Prompt: Skill-specific schema context
  ├─ LLM: GPT-4o-mini (temp=0.1)
  └─ Parser: Pydantic validation
         ↓
  SQL Validator (security checks)
         ↓
  PostgreSQL Execution (with retry)
         ↓
  ResponseGenerationChain
  ├─ Prompt: Skill-specific response guidelines
  ├─ LLM: GPT-4o-mini (temp=0.7)
  └─ Parser: String output
         ↓
  Natural Language Response
```

## Project Structure

```
ai_assistant/
├── graph/                          # Multi-agent orchestration (LangGraph)
│   ├── orchestrator.py            # Main workflow builder & executor
│   ├── state.py                   # TypedDict state schema
│   └── nodes/
│       ├── supervisor.py          # Routing decision node (GPT)
│       ├── sql_agent.py           # SQL execution node
│       ├── document_agent.py      # Vector search node
│       └── synthesizer.py         # Response synthesis node
├── config/
│   ├── database.py                # SQLAlchemy + PostgreSQL
│   └── settings.py                # Environment variables & LLM config
├── chains/                         # LangChain chain definitions
│   ├── sql_generation_chain.py   # SQL generation (temp=0.1)
│   └── response_chain.py          # Response generation (temp=0.7)
├── skills/                         # Skill-based query routing
│   ├── base.py                    # BaseSkill interface
│   ├── phone_calls.py            # Phone calls skill
│   ├── phone_messages.py         # SMS/text messages skill
│   ├── email_communications.py   # Email & quotes skill
│   ├── companies_data.py         # Company information skill
│   ├── documents.py              # Document metadata queries skill
│   └── general.py                # General fallback skill
├── agents/
│   ├── sql_agent.py              # LangChain agent orchestrator
│   └── skill_router.py           # Keyword-based skill detection
├── memory/
│   └── conversation_memory.py    # LangChain memory manager
├── core/
│   ├── validator.py              # SQL validation & security
│   ├── executor.py               # SQL execution with retry
│   └── schema_loader.py          # Database schema context
├── database/
│   └── chromadb/                 # Vector database for documents
│       ├── client.py             # ChromaDB wrapper
│       ├── indexer.py            # Document chunking & embedding
│       └── searcher.py           # Semantic search
├── evaluation/                    # Testing & evaluation
│   ├── runner.py                 # Test execution runner
│   └── test_questions.py         # Test question definitions
└── ui/
    └── app.py                    # Streamlit interface
```

## Features

- 🎯 **Multi-Agent Orchestration** - LangGraph workflow with intelligent routing
- 🤖 **LangChain-Powered Agents** - Modern LLM orchestration with chains
- 📄 **Document Search** - ChromaDB vector database for policy documents
- 🔀 **Hybrid Queries** - Combine structured data + document content
- 🧠 **Smart Routing** - Supervisor node analyzes questions and routes optimally
- 🔄 **Automatic Retry Logic** - Up to 3 attempts with error feedback
- 💬 **Conversation Memory** - LangChain memory for multi-turn conversations
- 🎯 **Skill-Based Routing** - 5 specialized skills for different query types
- ✅ **SQL Validation** - Security checks before execution
- 📊 **Results Export** - Download query results as CSV
- 🌙 **Dark Theme UI** - Gemini-style Streamlit interface

## Key Components

### Multi-Agent Orchestration (LangGraph)

**MultiAgentOrchestrator** ([graph/orchestrator.py](graph/orchestrator.py))
- Primary entry point for all queries
- Builds and executes LangGraph state machine
- Manages state flow through nodes
- Converts graph output to legacy API format

**Supervisor Node** ([graph/nodes/supervisor.py](graph/nodes/supervisor.py))
- Analyzes user questions using GPT-4o-mini
- Routes to: `sql_only`, `document_search`, or `hybrid`
- Uses structured output for routing decisions

**SQL Agent Node** ([graph/nodes/sql_agent.py](graph/nodes/sql_agent.py))
- Executes structured data queries
- Delegates to LangChainSQLAgent
- Handles retry logic with error feedback

**Document Agent Node** ([graph/nodes/document_agent.py](graph/nodes/document_agent.py))
- Performs semantic search in ChromaDB
- Returns relevant document chunks
- Configurable top-k and similarity threshold

**Synthesizer Node** ([graph/nodes/synthesizer.py](graph/nodes/synthesizer.py))
- Combines responses from multiple agents
- Uses LLM for intelligent synthesis
- Single-agent: pass-through, Multi-agent: synthesis

**State Management** ([graph/state.py](graph/state.py))
- TypedDict schema with 17 fields
- Tracks routing, SQL results, documents, errors
- Accumulates execution path for debugging

### Vector Database (ChromaDB)

**Document Indexer** ([database/chromadb/indexer.py](database/chromadb/indexer.py))
- Chunks documents (4000 tokens, 200 overlap)
- Creates embeddings (text-embedding-3-small, 1536 dims)
- Stores in ChromaDB collection

**Document Searcher** ([database/chromadb/searcher.py](database/chromadb/searcher.py))
- Semantic search with cosine similarity
- Configurable similarity threshold (0.7)
- Returns top-k relevant chunks

### LangChain Integration

**SQL Generation Chain** ([chains/sql_generation_chain.py](chains/sql_generation_chain.py))
- Uses LangChain chains and components for LLM orchestration
- `ChatPromptTemplate` for reusable, versioned prompt templates
- `JsonOutputParser` with Pydantic models for type-safe responses
- Output: `reasoning`, `sql`, `explanation`, `needs_clarification`

**Response Generation Chain** ([chains/response_chain.py](chains/response_chain.py))
- Natural language response generation (temp=0.7)
- Skill-specific response guidelines
- Fallback to template responses on LLM failure

### Memory Management

**ConversationMemoryManager** ([memory/conversation_memory.py](memory/conversation_memory.py))
- LangChain `ConversationBufferWindowMemory` for automatic conversation tracking
- Per-session memory isolation
- Configurable window size (default: 3 exchanges)
- Methods: `add_exchange()`, `get_conversation_history()`, `clear_session()`

### Skills System

**6 Specialized Skills:**

1. **Phone Calls** - Call records, voicemails, recording summaries (`phone_call_silver`)
2. **Phone Messages** - SMS/text messages (`phone_message_silver`)
3. **Email Communications** - Emails, quotes, pricing, account activity (`emails_silver`)
4. **Companies Data** - Company info, contacts, business details (`companies`)
5. **Documents** - Document metadata queries
6. **General** - Fallback for any other queries (all tables)

Each skill provides:
- Skill-specific schema context (as LangChain prompt templates)
- Custom response formatting (fallback if LLM fails)
- Example queries for few-shot learning

## Design Patterns

1. **Supervisor Pattern** - Centralized routing with conditional branching (LangGraph)
2. **State Machine** - TypedDict state management with accumulator fields
3. **Strategy Pattern** - Skills as pluggable strategies with consistent interface
4. **Chain of Responsibility** - SQL gen → validate → execute → respond with retry
5. **Multi-Modal Data** - Structured (SQL) + Unstructured (Documents) integration
6. **Response Synthesis** - LLM intelligently combines outputs from multiple agents
7. **Composition Over Inheritance** - Agents composed of chains/validators/memory
8. **Facade Pattern** - MultiAgentOrchestrator hides graph complexity

## Query Workflows

### Workflow 1: SQL-Only Query

```
User: "What was the last phone call?"
  ↓
Supervisor: Analyzes question → Routes to sql_only
  ↓
SQL Agent:
  • SkillDetector: Detects "phone_calls" skill (keyword: "call")
  • SQLGenerationChain: Generates SQL with phone_call_silver schema
  • Validator: Checks security (SELECT-only, company_id filter)
  • Executor: Runs query on PostgreSQL
  • ResponseChain: Generates natural language response
  ↓
Synthesizer: Pass-through (single agent)
  ↓
Output: "The most recent call was on January 9, 2026 from John Smith
         regarding policy renewal. Duration: 8 minutes."
```

### Workflow 2: Document Search Query

```
User: "What's covered in the liability policy?"
  ↓
Supervisor: Analyzes question → Routes to document_search
  ↓
Document Agent:
  • Converts question to search embedding
  • Queries ChromaDB with semantic search
  • Returns top-5 relevant document chunks (similarity > 0.7)
  ↓
Synthesizer: Formats document excerpts
  ↓
Output: "The liability policy covers:
         • General Liability: Up to $2M per occurrence
         • Professional Liability: $1M aggregate
         • Product Liability: Included in coverage
         [Source: Policy_2026_Liability.pdf, Page 3]"
```

### Workflow 3: Hybrid Query

```
User: "Show me quotes and what the policy covers"
  ↓
Supervisor: Analyzes question → Routes to hybrid
  ↓
SQL Agent (parallel):
  • Detects "email_communications" skill
  • Queries emails_silver for quotes
  • Returns: 2 quotes found ($1,433.88, $1,250.00)
  ↓
Document Agent (parallel):
  • Searches for "policy coverage" in ChromaDB
  • Returns: Policy document excerpts
  ↓
Synthesizer: LLM combines both sources
  ↓
Output: "You received 2 quotes:
         • Harper Insurance: $1,433.88 (Jan 9, 2026)
         • Competitor Quote: $1,250.00 (Jan 8, 2026)

         The Harper policy covers:
         • General Liability: $2M
         • Workers Comp: $500K
         • Commercial Auto: $1M combined
         [Sources: Database + Policy_2026.pdf]"
```

### Workflow 4: Multi-Turn Conversation

```
User: "What was the last phone call?"
Assistant: "The last call was from John Smith on Jan 9..."

User: "What did they discuss?"
  ↓
Memory: Retrieves previous exchange
  ↓
SQL Agent:
  • SQLGenerationChain receives conversation history
  • Understands "they" = John Smith from previous answer
  • Generates query using recording_summary field
  ↓
Output: "They discussed renewing the business liability policy.
         John mentioned expanding operations and needing higher
         coverage limits."
```

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

# Vector Search Configuration
VECTOR_SEARCH_TOP_K=5
VECTOR_SIMILARITY_THRESHOLD=0.7
EMBEDDINGS_MODEL=text-embedding-3-small
EMBEDDINGS_DIMENSION=1536

# Document Chunking
CHUNK_SIZE=4000
CHUNK_OVERLAP=200
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

## Configuration Options

### LLM Settings

- `LLM_MODEL`: Model name (default: `gpt-4o-mini`)
- `LLM_TEMPERATURE_SQL`: Temperature for SQL generation (default: `0.1` - deterministic)
- `LLM_TEMPERATURE_RESPONSE`: Temperature for responses (default: `0.7` - creative)
- `LLM_TIMEOUT`: Request timeout in seconds (default: `30`)
- `LLM_MAX_RETRIES`: LangChain retry attempts (default: `2`)

### Memory Settings

- `MEMORY_WINDOW_SIZE`: Number of conversation turns to remember (default: `3`)

### SQL Settings

- `MAX_RETRIES`: SQL generation retry attempts (default: `3`)
- `SQL_TIMEOUT_SECONDS`: SQL execution timeout (default: `30`)
- `NLG_ENABLED`: Use LLM for responses (default: `true`)

### Vector Search Settings

- `VECTOR_SEARCH_TOP_K`: Number of document chunks to return (default: `5`)
- `VECTOR_SIMILARITY_THRESHOLD`: Minimum similarity score (default: `0.7`)
- `EMBEDDINGS_MODEL`: OpenAI embedding model (default: `text-embedding-3-small`)
- `CHUNK_SIZE`: Document chunk size in tokens (default: `4000`)
- `CHUNK_OVERLAP`: Overlap between chunks in tokens (default: `200`)

## Usage Examples

### Example 1: Phone Calls (SQL-Only)
```
User: "What was the last phone call?"

Flow:
1. Supervisor → Routes to sql_only
2. SQL Agent → phone_calls skill
3. SQL: SELECT * FROM communications.phone_call_silver
        WHERE matched_company_id = 29447
        ORDER BY call_timestamp DESC LIMIT 1
4. Response: "The most recent call was on January 9, 2026..."
```

### Example 2: Email/Quotes (SQL-Only)
```
User: "What quotes were sent?"

Flow:
1. Supervisor → Routes to sql_only
2. SQL Agent → email_communications skill
3. SQL: SELECT * FROM communications.emails_silver
        WHERE matched_company_id = 29447 AND category = 'QUOTE'
4. Response: "On January 9, 2026, Harper sent a quote for $1,433.88..."
```

### Example 3: Policy Documents (Document Search)
```
User: "What does the policy say about liability coverage?"

Flow:
1. Supervisor → Routes to document_search
2. Document Agent → Semantic search in ChromaDB
3. Returns: Top-5 relevant chunks from policy PDFs
4. Response: "The liability policy covers up to $2M per occurrence..."
```

### Example 4: Hybrid Query
```
User: "Show me the quotes and what they cover"

Flow:
1. Supervisor → Routes to hybrid
2. SQL Agent → Queries emails_silver for quotes (parallel)
3. Document Agent → Searches policy documents (parallel)
4. Synthesizer → LLM combines both sources
5. Response: "You received 2 quotes... The policy covers..."
```

### Example 5: Follow-up Question
```
User: "What was the last call?"
Assistant: "The last call was from John on Jan 9..."

User: "What did they discuss?"

Flow:
1. Memory retrieves previous exchange
2. SQL Agent sees context: "previous question was about the last call"
3. Understands "they" = the caller from previous answer
4. Generates query using recording_summary field
```

## Testing

### Test Individual Components

```bash
# Test multi-agent orchestrator
python -c "from graph.orchestrator import MultiAgentOrchestrator; orch = MultiAgentOrchestrator(29447); result = orch.process_query('What was the last call?', 'test_session'); print(f'Success: {result[\"success\"]}')"

# Test SQL agent
python -c "from agents.sql_agent import LangChainSQLAgent; agent = LangChainSQLAgent(29447); print(agent.generate_sql('What are the contact details?'))"

# Test conversation memory
python -c "from memory.conversation_memory import ConversationMemoryManager; mgr = ConversationMemoryManager(); mgr.add_exchange('test', 'Q1', 'A1'); print(mgr.get_conversation_history('test'))"

# Test document search
python -c "from database.chromadb.searcher import search_documents; results = search_documents('liability coverage', top_k=3); print(f'Found {len(results)} documents')"

# Test executor (full pipeline)
python -c "from core.executor import execute_with_retry; result = execute_with_retry('What are the contact details?', 29447); print(f'Success: {result[\"success\"]}')"
```

### Run Evaluation Suite

```bash
cd ai_assistant/evaluation
python runner.py
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

- **Average Query Time**:
  - SQL-Only: 2-4 seconds
  - Document Search: 1-3 seconds
  - Hybrid: 4-6 seconds
- **API Cost per Query**: ~$0.01-0.03 (GPT-4o-mini)
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

### "ChromaDB collection not found"
```bash
# Index documents first
cd database/chromadb
python indexer.py
```

## Technology Stack

- **Orchestration**: LangGraph (state-based multi-agent workflows)
- **LLM Framework**: LangChain (chains, prompts, parsers, memory)
- **LLM Provider**: OpenAI GPT-4o-mini
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector DB**: ChromaDB for document embeddings
- **UI**: Streamlit
- **Validation**: sqlparse
- **Type Safety**: Pydantic v2

## Future Enhancements

- [ ] LLM-based skill routing (instead of keyword matching)
- [ ] Streaming responses with `astream()`
- [ ] Multi-provider support (Anthropic Claude, etc.)
- [ ] Query caching with LangChain cache
- [ ] Agent tools for complex operations
- [ ] Async execution for concurrent queries
- [ ] Persistent conversation history across sessions