# Proposed Solutions & Improvement Ideas

This document outlines architectural improvements and solutions for edge cases identified during development and evaluation.

---

## 1. Document Summarization for Long Documents

### Problem
When a document exceeds the LLM context length limit (e.g., >10,000 characters), the current approach simply truncates:

```python
if len(content) > 10000:
    content = content[:10000] + "..."  # Information at the end is LOST
```

This causes important information (coverage details, exclusions, premiums) at the end of long documents to be missed.

### Solution: Map-Reduce Summarization

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



### Benefits
- **100% document coverage** vs 20% with truncation
- **No lost information** from document end
- **Better quality** summaries for insurance documents where details matter

### Trade-offs
| Approach | API Calls | Coverage | Cost |
|----------|-----------|----------|------|
| Truncation | 1 | ~20% | Low |
| Map-Reduce | N+1 | 100% | Higher |

---

## 2. Hierarchical Memory Architecture

### Current State
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

### Proposed: Hierarchical Memory Flow

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
│              ┌────────────┴────────────┐                     │
│              ↓                         ↓                     │
│       ┌──────────────┐         ┌──────────────┐             │
│       │  SQL Agent   │         │  Doc Agent   │             │
│       │              │         │              │             │
│       │ Has own      │         │ Has own      │             │
│       │ memory       │         │ memory       │             │
│       │ + context    │         │ + context    │             │
│       │ from         │         │ from         │             │
│       │ supervisor   │         │ supervisor   │             │
│       └──────────────┘         └──────────────┘             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Memory Flow Rules

1. **Main Agent (Supervisor)**
   - Maintains memory of **its own actions** (routing decisions, orchestration logic)
   - **Also** maintains memory of all sub-agent decisions and outputs
   - Can see: its own routing decisions + SQL results + document findings + synthesized responses
   - Sub-agents do NOT have access to main agent's full memory

2. **Sub-Agents (SQL, Document)**
   - Have their own isolated memory for their specific tasks
   - Receive context from supervisor (what was asked, why routed here)
   - Do NOT see other sub-agent's internal memory

3. **Downstream Agents (Synthesizer)** *(Conceptual)*
   - The synthesizer is shown conceptually here - it's not a separate sub-agent but represents the final response generation step
   - Has memory of upstream agent outputs (SQL results, Doc results)
   - Uses this to combine and generate final response
   - Agents that come AFTER other agents can see those agents' outputs

4. **Memory Reset on Route Back**
   - When control returns to main agent, sub-agent memory for that query is "closed"
   - New query starts with fresh sub-agent context
   - Main agent retains high-level summary of what happened


### Key Insight: Direction Matters

```
Main Agent → Sub-Agent: Sub-agent does NOT see main agent's full history
Sub-Agent → Main Agent: Main agent DOES see sub-agent's actions
Sub-Agent → Downstream Agent: Downstream agent sees upstream outputs
```

### Benefits
- Main agent has full visibility for better coordination
- Downstream agents have necessary context from upstream agents
- Clean separation prevents information overload
- Memory resets prevent stale context bleeding into new queries
- Sub-agents stay focused without being distracted by irrelevant info

---

## 3. Hybrid Agent for Combined Queries

### Problem
Some queries require both SQL data AND document content:
- "What documents does this company have and what do they contain?"
- "Show me the policy details from both the database and documents"
- "What's the premium in the policy vs what we quoted?"

Previously, the supervisor had to choose ONE route: `sql_only` OR `document_search`

### Solution: Hybrid Route

Added a new routing option that runs BOTH agents:

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



### When to Use Each Route

| Query Type | Route | Example |
|------------|-------|---------|
| "How many documents?" | sql_only | Count from metadata |
| "What does the policy say about coverage?" | document_search | Search document content |
| "List all documents and summarize each" | **hybrid** | Need both metadata + content |
| "What's the premium in the policy vs what we quoted?" | **hybrid** | Compare DB data + doc content |
| "Hello, how are you?" | conversational | No data needed |

### Benefits
- Better answers for complex queries requiring multiple data sources
- No need for user to ask two separate questions
- Synthesizer can correlate and compare data from both sources
- More natural conversation flow

---

## Summary of Improvements

| Area | Current State | Proposed Improvement |
|------|---------------|---------------------|
| **Long Documents** | Truncate at 10k chars (lose ~80% of content) | Map-Reduce summarization (100% coverage) |
| **Memory Architecture** | Isolated per agent (no visibility) | Hierarchical with main agent visibility |
| **Memory Direction** | Flat structure | Upstream→Downstream flow, reset on return |
| **Query Routing** | Single route (sql OR doc) | Hybrid route for combined queries |

These improvements address the main limitations identified during evaluation testing and will significantly improve the system's ability to handle complex, real-world queries.