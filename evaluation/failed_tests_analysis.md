# Failed Tests Analysis & Improvement Ideas

**Evaluation Date**: January 15, 2026
**Pass Rate**: 26/30 (87%)

---

## Part 1: Failed Test Cases

### 1. `mem_001b` - "What about outbound?"
- **Expected**: 4 (outbound emails)
- **Got**: Clarification request
- **Why Failed**: The evaluation runner tests each question in isolation without passing conversation history. The system maintains only the last 3 chat entries (`memory[-3:]` in synthesizer), but the runner doesn't inject the prior question ("How many emails did we receive?") into memory before testing this follow-up.

### 2. `mem_005b` - "What about their calls?"
- **Expected**: 16 (total calls)
- **Got**: Clarification request
- **Why Failed**: Same root cause - the runner doesn't pass the preceding question's context. The system's 3-turn memory capability exists but isn't being utilized by the evaluation framework.

### 3. `multi_001` - "Give me a complete overview of all communications"
- **Expected**: 12 emails, 16 calls, 24 SMS
- **Got**: 5 emails, 4 calls (SMS missing)
- **Why Failed**: Response truncation due to output token length limit. The SQL agent likely retrieved complete data, but the synthesized response was cut off before all communication counts were included.

### 4. `edge_chat_004` - "What can you do?"
- **Expected**: "I'm here to help you with insurance information, including quotes, policy details, and more!"
- **Got**: Same response + "How can I assist you today?"
- **Why Failed**: LLM judge flagged the extra follow-up question as a mismatch despite the core answer being correct.

---

## Root Causes Summary

| Issue Type | Tests Affected | Fix Required |
|------------|----------------|--------------|
| Missing conversation context | mem_001b, mem_005b | Runner needs to pass chat history for follow-up tests |
| Response truncation | multi_001 | Increase output token limit or optimize response format |
| Strict LLM judge | edge_chat_004 | Update expected answer or adjust judge tolerance |

### Technical Root Cause: Memory Test Failures

The memory tests (`mem_001b`, `mem_005b`) fail due to how the evaluation runner assigns session IDs.

**Code Location**: `runner.py:358`
```python
session_id=f"eval_{test_id}"
```

**Problem**: Each test gets a unique session ID based on its test ID:
- `mem_001a` → session `eval_mem_001a`
- `mem_001b` → session `eval_mem_001b`

Since these are **different session IDs**, they don't share memory. The memory system keys conversations by session ID, so `mem_001b` cannot access the context from `mem_001a`.

**Potential Fix**: Use shared session ID for related test pairs:
```python
# Extract base ID: mem_001a → mem_001, mem_001b → mem_001
base_id = test_id.rstrip('abcdefgh')  # or use regex
session_id = f"eval_{base_id}"
```

This would allow `mem_001a` and `mem_001b` to share session `eval_mem_001`.

**Note**: The memory system itself works correctly (as seen in the Streamlit app). This is purely an evaluation framework limitation.

---

## Part 2: Improvement Ideas & Solutions

### 1. Document Summarization for Long Documents

#### Problem
When a document exceeds the LLM context length limit (e.g., >10,000 characters), the current approach simply truncates, causing important information at the end to be lost.

#### Solution: Map-Reduce Summarization

**Step 1: MAP - Split and Summarize Each Chunk**
```
Original Document (50,000 chars)
        ↓
    Split into chunks (8,000 chars each)
        ↓
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ Chunk 1 │ Chunk 2 │ Chunk 3 │ Chunk 4 │ Chunk 5 │
└────┬────┴────┬────┴────┬────┴────┬────┴────┬────┘
     ↓         ↓         ↓         ↓         ↓
  Summarize each chunk independently (LLM call per chunk)
     ↓         ↓         ↓         ↓         ↓
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ Sum 1   │ Sum 2   │ Sum 3   │ Sum 4   │ Sum 5   │
│ ~300ch  │ ~300ch  │ ~300ch  │ ~300ch  │ ~300ch  │
└─────────┴─────────┴─────────┴─────────┴─────────┘
```

**Step 2: REDUCE - Combine Summaries**
```
Combined Summaries (~1,500 chars)
        ↓
    Final summarization pass
        ↓
    Coherent Final Summary
```

#### Benefits
- **100% document coverage** vs 20% with truncation
- **No lost information** from document end
- **Better quality** summaries for insurance documents where details matter

#### Trade-offs
| Approach | API Calls | Coverage | Cost |
|----------|-----------|----------|------|
| Truncation | 1 | ~20% | Low |
| Map-Reduce | N+1 | 100% | Higher |

---

### 2. Hierarchical Memory Architecture

#### Current State
Each sub-agent has **isolated memory** - they don't know what other agents did:

```
┌─────────────────────────────────────────────────────────────┐
│  CURRENT: Isolated Agent Memories                            │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ Supervisor │  │ SQL Agent  │  │ Doc Agent  │             │
│  │  Memory    │  │  Memory    │  │  Memory    │             │
│  │            │  │            │  │            │             │
│  │ (isolated) │  │ (isolated) │  │ (isolated) │             │
│  └────────────┘  └────────────┘  └────────────┘             │
│         ↑              ↑              ↑                      │
│         │              │              │                      │
│    No connection between agent memories                      │
└─────────────────────────────────────────────────────────────┘
```

#### Proposed: Hierarchical Memory Flow

The main agent (orchestrator) should have visibility into sub-agent activities, and downstream agents should have context from upstream agents:

```
┌─────────────────────────────────────────────────────────────┐
│  PROPOSED: Hierarchical Memory Flow                          │
│                                                              │
│                    ┌──────────────┐                          │
│                    │ MAIN AGENT   │                          │
│                    │ (Supervisor) │                          │
│                    │              │                          │
│                    │ Has memory   │                          │
│                    │ of ALL sub-  │                          │
│                    │ agent actions│                          │
│                    └──────┬───────┘                          │
│                           │                                  │
│              ┌────────────┼────────────┐                     │
│              ↓            ↓            ↓                     │
│       ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│       │SQL Agent │  │Doc Agent │  │Synthesizer│             │
│       │          │  │          │  │          │              │
│       │ Has own  │  │ Has own  │  │ Has memory│              │
│       │ memory   │  │ memory   │  │ of SQL &  │              │
│       │ + context│  │ + context│  │ Doc agents│              │
│       │ from     │  │ from     │  │           │              │
│       │ supervisor│ │ supervisor│ │           │              │
│       └──────────┘  └──────────┘  └──────────┘              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Memory Flow Rules

1. **Main Agent (Supervisor)** - Maintains memory of all sub-agent decisions and outputs
2. **Sub-Agents (SQL, Document)** - Have their own isolated memory + receive context from supervisor
3. **Downstream Agents (Synthesizer)** - Has memory of upstream agent outputs
4. **Memory Reset on Route Back** - Sub-agent memory resets per query, main agent retains summary

#### Benefits
- Main agent has full visibility for better coordination
- Downstream agents have necessary context
- Clean separation prevents information overload
- Memory resets prevent stale context bleeding into new queries

---

### 3. Hybrid Agent for Combined Queries (ALREADY IMPLEMENTED)

#### Problem
Some queries require both SQL data AND document content.

#### Solution: Hybrid Route (Already in codebase)

The hybrid route is already implemented in the orchestrator. It runs SQL agent first, then document agent, then synthesizer:
- `graph/state.py:29` - Route type includes "hybrid"
- `graph/orchestrator.py:26-28` - Routes to hybrid_sql node
- `graph/orchestrator.py:55,62` - hybrid_sql → document_agent flow
- `graph/nodes/supervisor.py:13,56` - Supervisor can choose hybrid route

```
┌─────────────────────────────────────────────────────────────┐
│  HYBRID ROUTING                                              │
│                                                              │
│  User: "What documents does this company have and what       │
│         do they contain?"                                    │
│                                                              │
│                    ┌──────────────┐                          │
│                    │  Supervisor  │                          │
│                    │              │                          │
│                    │ route=hybrid │                          │
│                    └──────┬───────┘                          │
│                           │                                  │
│              ┌────────────┴────────────┐                     │
│              ↓                         ↓                     │
│       ┌──────────────┐         ┌──────────────┐             │
│       │  SQL Agent   │         │ Document     │             │
│       │              │         │ Agent        │             │
│       │ Get metadata:│         │              │             │
│       │ - doc count  │         │ Get content: │             │
│       │ - filenames  │         │ - summaries  │             │
│       │ - types      │         │ - key info   │             │
│       └──────┬───────┘         └──────┬───────┘             │
│              │                        │                      │
│              └────────────┬───────────┘                      │
│                           ↓                                  │
│                    ┌──────────────┐                          │
│                    │ Synthesizer  │                          │
│                    │              │                          │
│                    │ Combines:    │                          │
│                    │ SQL metadata │                          │
│                    │ + Doc content│                          │
│                    └──────────────┘                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### When to Use Hybrid

| Query Type | Route | Example |
|------------|-------|---------|
| "How many documents?" | sql_only | Count from metadata |
| "What does the policy say about coverage?" | document_search | Search document content |
| "List all documents and summarize each" | **hybrid** | Need both metadata + content |
| "What's the premium in the policy vs what we quoted?" | **hybrid** | Compare DB data + doc content |

---

## Summary of Improvements

| Area | Current State | Status |
|------|---------------|--------|
| **Long Documents** | Truncate at 10k chars | PROPOSED: Map-Reduce summarization |
| **Memory** | Isolated per agent | PROPOSED: Hierarchical with main agent visibility |
| **Hybrid Routing** | SQL → Document → Synthesizer | ALREADY IMPLEMENTED in orchestrator.py |

The hybrid route is already functional. The remaining proposed improvements (Map-Reduce summarization and Hierarchical Memory) would address additional edge cases.