"""Comprehensive Evaluation Framework for Multi-Agent Insurance Assistant.

This file contains all evaluation questions organized into 4 categories:
1. Individual Agent Evaluation - Tests each agent's capabilities in isolation
2. Conversation Memory Evaluation - Tests follow-up questions requiring memory context
3. Multi-Agent/Multi-Table Queries - Tests complex queries requiring multiple agents or UNION queries
4. Edge Cases - Tests vague questions, chitchat, and off-topic questions

Test Company: Guardian Families Homecare, LLC (ID: 29447)
- Industry: Healthcare - Home Care Services
- Location: Indianapolis, Indiana
- Data: 12 emails, 16 calls, 24 SMS, 13 documents
"""

from typing import List, Dict, Any, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_COMPANY_ID = 29447
COMPANY_INFO = {
    "id": 29447,
    "name": "Guardian Families Homecare, LLC",
    "industry": "Healthcare",
    "sub_industry": "Home Care Services",
    "location": "Indianapolis, Indiana",
    "address": "356 Jefferson Avenue, Indianapolis, Indiana 46201",
    "email": "guardianfamiliesfirst@gmail.com",
    "phone": "+1 (317) 365-7605",
    "annual_revenue": 150000,
    "full_time_employees": 2,
    "part_time_employees": 2,
    "total_employees": 4,
    # Communication stats
    "total_emails": 12,
    "inbound_emails": 7,
    "outbound_emails": 4,
    "total_calls": 16,
    "incoming_calls": 7,
    "outgoing_calls": 9,
    "answered_calls": 12,
    "voicemails": 1,
    "total_sms": 24,
    "incoming_sms": 3,
    "outgoing_sms": 21,
    "total_documents": 13,
    "pdf_documents": 12,
    "png_documents": 1,
}

# =============================================================================
# CATEGORY 1: INDIVIDUAL AGENT EVALUATION
# =============================================================================

INDIVIDUAL_AGENT_QUESTIONS = [
    # -------------------------------------------------------------------------
    # Companies Data Skill (6 questions)
    # -------------------------------------------------------------------------
    {
        "id": "company_001",
        "category": "individual_agent",
        "subcategory": "companies_data",
        "question": "What is the company name?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "companies_data",
        "expected_tables": ["public.companies"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": "Guardian Families Homecare, LLC",
            "acceptable_variations": ["Guardian Families Homecare"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests basic company name retrieval"
    },
    {
        "id": "company_002",
        "category": "individual_agent",
        "subcategory": "companies_data",
        "question": "What industry is this company in?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "companies_data",
        "expected_tables": ["public.companies"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": "Healthcare",
            "acceptable_variations": ["Healthcare - Home Care Services", "Home Care Services"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests industry field retrieval"
    },
    {
        "id": "company_003",
        "category": "individual_agent",
        "subcategory": "companies_data",
        "question": "Where is Guardian Families Homecare located?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "companies_data",
        "expected_tables": ["public.companies"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": "Indianapolis",
            "acceptable_variations": ["Indianapolis, Indiana", "Indiana", "356 Jefferson Avenue"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests address/location retrieval"
    },
    {
        "id": "company_004",
        "category": "individual_agent",
        "subcategory": "companies_data",
        "question": "What is the annual revenue of this company?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "companies_data",
        "expected_tables": ["public.companies"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "numeric_range",
            "value": 150000,
            "acceptable_variations": ["$150,000", "150000", "$150K", "150K"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests revenue field retrieval"
    },
    {
        "id": "company_005",
        "category": "individual_agent",
        "subcategory": "companies_data",
        "question": "How many employees does this business have?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "companies_data",
        "expected_tables": ["public.companies"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 4,
            "acceptable_variations": ["4", "four", "4 employees", "2 full-time, 2 part-time"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests employee count calculation (full-time + part-time)"
    },
    {
        "id": "company_006",
        "category": "individual_agent",
        "subcategory": "companies_data",
        "question": "What are the contact details for this business?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "companies_data",
        "expected_tables": ["public.companies"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": ["guardianfamiliesfirst@gmail.com", "317"],
            "acceptable_variations": ["+1 (317) 365-7605", "3173657605"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests contact info (email + phone) retrieval"
    },

    # -------------------------------------------------------------------------
    # Email Communications Skill (8 questions)
    # -------------------------------------------------------------------------
    {
        "id": "email_001",
        "category": "individual_agent",
        "subcategory": "email_communications",
        "question": "How many emails have been exchanged with this company?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 12,
            "acceptable_variations": ["12", "twelve", "12 emails"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests total email count"
    },
    {
        "id": "email_002",
        "category": "individual_agent",
        "subcategory": "email_communications",
        "question": "How many inbound emails have we received from this client?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 7,
            "acceptable_variations": ["7", "seven", "7 inbound", "7 emails"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests inbound email filtering"
    },
    {
        "id": "email_003",
        "category": "individual_agent",
        "subcategory": "email_communications",
        "question": "What is the best quote received for this account?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": ["1,433.88", "1433"],
            "acceptable_variations": ["$1,433.88", "$1,434", "1434"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests quote extraction from email body_text with QUOTE category"
    },
    {
        "id": "email_004",
        "category": "individual_agent",
        "subcategory": "email_communications",
        "question": "Show me all emails sent to this company in the last 30 days",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "list",
            "value": "Recent emails with dates and subjects",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests date-based email filtering"
    },
    {
        "id": "email_005",
        "category": "individual_agent",
        "subcategory": "email_communications",
        "question": "Are there any unanswered emails or pending follow-ups?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should identify emails with FOLLOW_UP or CUSTOMER_FOLLOW_UP category",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests follow-up detection via classification_raw"
    },
    {
        "id": "email_006",
        "category": "individual_agent",
        "subcategory": "email_communications",
        "question": "When was the most recent email communication?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": "January 12, 2026",
            "acceptable_variations": ["2026-01-12", "Jan 12, 2026", "12 January 2026"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests most recent email date retrieval"
    },
    {
        "id": "email_007",
        "category": "individual_agent",
        "subcategory": "email_communications",
        "question": "What was the subject of the most recent email?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": "Mailing address",
            "acceptable_variations": ["Re: Mailing address clarification", "address clarification"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests subject extraction from most recent email"
    },
    {
        "id": "email_008",
        "category": "individual_agent",
        "subcategory": "email_communications",
        "question": "Was the policy cancelled?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should find POLICY_CANCELLATION category emails and explain status",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests policy cancellation email detection"
    },

    # -------------------------------------------------------------------------
    # Phone Calls Skill (7 questions)
    # -------------------------------------------------------------------------
    {
        "id": "calls_001",
        "category": "individual_agent",
        "subcategory": "phone_calls",
        "question": "What phone calls have been made with this company?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_calls",
        "expected_tables": ["communications.phone_call_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "list",
            "value": "Should list calls with dates, directions, and summaries",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests basic call history retrieval"
    },
    {
        "id": "calls_002",
        "category": "individual_agent",
        "subcategory": "phone_calls",
        "question": "How many phone calls have been made with this company?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_calls",
        "expected_tables": ["communications.phone_call_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 16,
            "acceptable_variations": ["16", "sixteen", "16 calls"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests total call count"
    },
    {
        "id": "calls_003",
        "category": "individual_agent",
        "subcategory": "phone_calls",
        "question": "Were there any voicemails left for this account?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_calls",
        "expected_tables": ["communications.phone_call_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should find 1 voicemail with type='unanswered_with_voicemail'",
            "acceptable_variations": ["1 voicemail", "Yes"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests voicemail filtering by call type"
    },
    {
        "id": "calls_004",
        "category": "individual_agent",
        "subcategory": "phone_calls",
        "question": "How many incoming calls have we received?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_calls",
        "expected_tables": ["communications.phone_call_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 7,
            "acceptable_variations": ["7", "seven", "7 incoming"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests incoming call direction filtering"
    },
    {
        "id": "calls_005",
        "category": "individual_agent",
        "subcategory": "phone_calls",
        "question": "How many calls were answered?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_calls",
        "expected_tables": ["communications.phone_call_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 12,
            "acceptable_variations": ["12", "twelve", "12 answered"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests answered call type filtering"
    },
    {
        "id": "calls_006",
        "category": "individual_agent",
        "subcategory": "phone_calls",
        "question": "What was the latest phone call conversation about?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_calls",
        "expected_tables": ["communications.phone_call_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should return recording_summary from most recent answered call",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests recording summary extraction"
    },
    {
        "id": "calls_007",
        "category": "individual_agent",
        "subcategory": "phone_calls",
        "question": "When was the most recent phone call?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_calls",
        "expected_tables": ["communications.phone_call_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": "January 9, 2026",
            "acceptable_variations": ["2026-01-09", "Jan 9, 2026"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests most recent call date retrieval"
    },

    # -------------------------------------------------------------------------
    # Phone Messages (SMS) Skill (5 questions)
    # -------------------------------------------------------------------------
    {
        "id": "sms_001",
        "category": "individual_agent",
        "subcategory": "phone_messages",
        "question": "Show me all text messages sent to this company",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_messages",
        "expected_tables": ["communications.phone_message_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "list",
            "value": "Should list SMS messages with dates and content",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests SMS message retrieval"
    },
    {
        "id": "sms_002",
        "category": "individual_agent",
        "subcategory": "phone_messages",
        "question": "What SMS communications have we had with the client?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_messages",
        "expected_tables": ["communications.phone_message_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "list",
            "value": "Should list SMS messages bidirectionally with direction",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests SMS keyword detection"
    },
    {
        "id": "sms_003",
        "category": "individual_agent",
        "subcategory": "phone_messages",
        "question": "How many text messages have been exchanged?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_messages",
        "expected_tables": ["communications.phone_message_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 24,
            "acceptable_variations": ["24", "twenty-four", "24 messages"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests total SMS count"
    },
    {
        "id": "sms_004",
        "category": "individual_agent",
        "subcategory": "phone_messages",
        "question": "How many incoming text messages did we receive?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_messages",
        "expected_tables": ["communications.phone_message_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 3,
            "acceptable_variations": ["3", "three", "3 incoming"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests incoming SMS direction filtering"
    },
    {
        "id": "sms_005",
        "category": "individual_agent",
        "subcategory": "phone_messages",
        "question": "When was the most recent text message?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_messages",
        "expected_tables": ["communications.phone_message_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": "January",
            "acceptable_variations": ["2026-01", "Jan 2026"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests most recent SMS date"
    },

    # -------------------------------------------------------------------------
    # Documents Skill - SQL Metadata (4 questions)
    # -------------------------------------------------------------------------
    {
        "id": "doc_001",
        "category": "individual_agent",
        "subcategory": "documents",
        "question": "How many documents does this company have?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "documents",
        "expected_tables": ["public.documents_01_14", "public.companies_documents_join"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 13,
            "acceptable_variations": ["13", "thirteen", "13 documents"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests document count via join table"
    },
    {
        "id": "doc_002",
        "category": "individual_agent",
        "subcategory": "documents",
        "question": "What types of documents does this company have?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "documents",
        "expected_tables": ["public.documents_01_14", "public.companies_documents_join"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": ["PDF", "PNG"],
            "acceptable_variations": ["application/pdf", "image/png", "12 PDF", "1 PNG"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests document type aggregation from metadata JSONB"
    },
    {
        "id": "doc_003",
        "category": "individual_agent",
        "subcategory": "documents",
        "question": "List all PDF documents for this company",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "documents",
        "expected_tables": ["public.documents_01_14", "public.companies_documents_join"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "list",
            "value": "Should list 12 PDF documents with filenames",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests PDF document filtering"
    },
    {
        "id": "doc_004",
        "category": "individual_agent",
        "subcategory": "documents",
        "question": "What are the filenames of all documents?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "documents",
        "expected_tables": ["public.documents_01_14", "public.companies_documents_join"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "list",
            "value": "Should list all 13 document filenames from metadata->>'filename'",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests filename extraction from JSONB metadata"
    },

    # -------------------------------------------------------------------------
    # Document Search - ChromaDB (4 questions)
    # -------------------------------------------------------------------------
    {
        "id": "docsearch_001",
        "category": "individual_agent",
        "subcategory": "document_search",
        "question": "What does the insurance policy document say about coverage?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "document_search",
        "expected_skill": "documents",
        "expected_tables": [],
        "expected_agents": ["supervisor", "document_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should search ChromaDB and return relevant document summaries about coverage",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests document content search via ChromaDB"
    },
    {
        "id": "docsearch_002",
        "category": "individual_agent",
        "subcategory": "document_search",
        "question": "Search for information about liability in the documents",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "document_search",
        "expected_skill": None,
        "expected_tables": [],
        "expected_agents": ["supervisor", "document_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should find general liability policy documents",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests liability-related document search"
    },
    {
        "id": "docsearch_003",
        "category": "individual_agent",
        "subcategory": "document_search",
        "question": "What is the premium amount mentioned in the policy documents?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "document_search",
        "expected_skill": "documents",
        "expected_tables": [],
        "expected_agents": ["supervisor", "document_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": ["1,036", "1036"],
            "acceptable_variations": ["$1,036", "$1,036.00"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests premium extraction from document content"
    },
    {
        "id": "docsearch_004",
        "category": "individual_agent",
        "subcategory": "document_search",
        "question": "What are the policy limits according to the documents?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "document_search",
        "expected_skill": None,
        "expected_tables": [],
        "expected_agents": ["supervisor", "document_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should find coverage limits from policy documents",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests policy limit extraction from documents"
    },
]

# =============================================================================
# CATEGORY 2: CONVERSATION MEMORY EVALUATION
# =============================================================================

MEMORY_QUESTIONS = [
    # -------------------------------------------------------------------------
    # Memory Test Pair 1: Email context follow-up
    # -------------------------------------------------------------------------
    {
        "id": "mem_001a",
        "category": "memory",
        "subcategory": "follow_up",
        "question": "How many emails did we receive from this client?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 7,
            "acceptable_variations": ["7 inbound emails", "7 emails", "7"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Setup question for email follow-up test"
    },
    {
        "id": "mem_001b",
        "category": "memory",
        "subcategory": "follow_up",
        "question": "What about outbound?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 4,
            "acceptable_variations": ["4 outbound emails", "4 emails", "4"]
        },
        "requires_memory": True,
        "memory_context": [
            {"question": "How many emails did we receive from this client?", "answer": "7 inbound emails"}
        ],
        "complexity": "moderate",
        "description": "Tests understanding 'outbound' refers to emails from memory context"
    },

    # -------------------------------------------------------------------------
    # Memory Test Pair 2: Phone call context follow-up
    # -------------------------------------------------------------------------
    {
        "id": "mem_002a",
        "category": "memory",
        "subcategory": "follow_up",
        "question": "When was the most recent phone call?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_calls",
        "expected_tables": ["communications.phone_call_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": "January 9, 2026",
            "acceptable_variations": ["2026-01-09", "Jan 9"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Setup question for call follow-up test"
    },
    {
        "id": "mem_002b",
        "category": "memory",
        "subcategory": "follow_up",
        "question": "What was discussed?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_calls",
        "expected_tables": ["communications.phone_call_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should return recording_summary from the most recent call",
            "acceptable_variations": []
        },
        "requires_memory": True,
        "memory_context": [
            {"question": "When was the most recent phone call?", "answer": "January 9, 2026"}
        ],
        "complexity": "moderate",
        "description": "Tests understanding 'discussed' refers to phone call from memory"
    },

    # -------------------------------------------------------------------------
    # Memory Test Pair 3: Company info context follow-up
    # -------------------------------------------------------------------------
    {
        "id": "mem_003a",
        "category": "memory",
        "subcategory": "follow_up",
        "question": "Tell me about the business",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "general",
        "expected_tables": ["public.companies"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": ["Guardian Families Homecare", "Healthcare"],
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Setup question for company follow-up test"
    },
    {
        "id": "mem_003b",
        "category": "memory",
        "subcategory": "follow_up",
        "question": "How many employees?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "companies_data",
        "expected_tables": ["public.companies"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": ["4"],
            "acceptable_variations": ["2 full-time", "2 part-time", "4 employees"]
        },
        "requires_memory": True,
        "memory_context": [
            {"question": "Tell me about the business", "answer": "Guardian Families Homecare, LLC is a Healthcare company"}
        ],
        "complexity": "moderate",
        "description": "Tests understanding 'employees' refers to same company from memory"
    },

    # -------------------------------------------------------------------------
    # Memory Test Pair 4: Pronoun resolution
    # -------------------------------------------------------------------------
    {
        "id": "mem_004a",
        "category": "memory",
        "subcategory": "pronoun_resolution",
        "question": "Show me the recent emails",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "list",
            "value": "Recent email list with dates and subjects",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Setup question for pronoun resolution test"
    },
    {
        "id": "mem_004b",
        "category": "memory",
        "subcategory": "pronoun_resolution",
        "question": "Which of those were about cancellation?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should filter previous email results by POLICY_CANCELLATION category",
            "acceptable_variations": []
        },
        "requires_memory": True,
        "memory_context": [
            {"question": "Show me the recent emails", "answer": "[list of emails]"}
        ],
        "complexity": "complex",
        "description": "Tests 'those' refers to previously shown emails"
    },

    # -------------------------------------------------------------------------
    # Memory Test Pair 5: Context switch
    # -------------------------------------------------------------------------
    {
        "id": "mem_005a",
        "category": "memory",
        "subcategory": "context_switch",
        "question": "What documents do they have?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "documents",
        "expected_tables": ["public.documents_01_14", "public.companies_documents_join"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 13,
            "acceptable_variations": ["13 documents", "13"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Setup question for context switch test"
    },
    {
        "id": "mem_005b",
        "category": "memory",
        "subcategory": "context_switch",
        "question": "What about their calls?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_calls",
        "expected_tables": ["communications.phone_call_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 16,
            "acceptable_variations": ["16 phone calls", "16 calls", "16"]
        },
        "requires_memory": True,
        "memory_context": [
            {"question": "What documents do they have?", "answer": "13 documents"}
        ],
        "complexity": "moderate",
        "description": "Tests context switch from documents to calls while maintaining company"
    },
]

# =============================================================================
# CATEGORY 3: MULTI-AGENT/MULTI-TABLE QUERIES
# =============================================================================

MULTI_AGENT_QUESTIONS = [
    # -------------------------------------------------------------------------
    # Union Queries (4 questions)
    # -------------------------------------------------------------------------
    {
        "id": "multi_001",
        "category": "multi_agent",
        "subcategory": "union_query",
        "question": "Give me a complete overview of all communications with this company",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "general",
        "expected_tables": [
            "communications.emails_silver",
            "communications.phone_call_silver",
            "communications.phone_message_silver"
        ],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": ["12", "16", "24"],
            "acceptable_variations": ["52 total", "12 emails", "16 calls", "24 SMS"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "complex",
        "description": "Tests UNION ALL across 3 communication tables"
    },
    {
        "id": "multi_002",
        "category": "multi_agent",
        "subcategory": "union_query",
        "question": "What is the total number of communications (emails + calls + messages)?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "general",
        "expected_tables": [
            "communications.emails_silver",
            "communications.phone_call_silver",
            "communications.phone_message_silver"
        ],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "exact",
            "value": 52,
            "acceptable_variations": ["52 total", "52 communications", "52"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "complex",
        "description": "Tests aggregated count across all communication tables"
    },
    {
        "id": "multi_003",
        "category": "multi_agent",
        "subcategory": "union_query",
        "question": "What's going on with this account?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "general",
        "expected_tables": [
            "communications.emails_silver",
            "communications.phone_call_silver",
            "communications.phone_message_silver"
        ],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should provide timeline combining all communication types ordered by date",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "complex",
        "description": "Tests account overview keyword triggering UNION query"
    },
    {
        "id": "multi_004",
        "category": "multi_agent",
        "subcategory": "union_query",
        "question": "Show me all activity for this company in the last 30 days",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "general",
        "expected_tables": [
            "communications.emails_silver",
            "communications.phone_call_silver",
            "communications.phone_message_silver"
        ],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "list",
            "value": "Recent activity across all communication channels with date filter",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "complex",
        "description": "Tests date-filtered UNION query"
    },

    # -------------------------------------------------------------------------
    # Hybrid Queries (1 question)
    # -------------------------------------------------------------------------
    {
        "id": "multi_005",
        "category": "multi_agent",
        "subcategory": "hybrid_query",
        "question": "What documents does this company have and what do they contain?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "hybrid",
        "expected_skill": "documents",
        "expected_tables": ["public.documents_01_14", "public.companies_documents_join"],
        "expected_agents": ["supervisor", "sql_agent", "document_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should list 13 documents with their summaries from ChromaDB",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "complex",
        "description": "Tests hybrid query requiring both SQL (metadata) and ChromaDB (content)"
    },

    # -------------------------------------------------------------------------
    # Aggregation Queries (2 questions)
    # -------------------------------------------------------------------------
    {
        "id": "multi_006",
        "category": "multi_agent",
        "subcategory": "aggregation",
        "question": "What percentage of calls were answered?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "phone_calls",
        "expected_tables": ["communications.phone_call_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "numeric_range",
            "value": 75,
            "acceptable_variations": ["75%", "12 out of 16", "12/16"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests percentage calculation (answered/total calls)"
    },
    {
        "id": "multi_007",
        "category": "multi_agent",
        "subcategory": "aggregation",
        "question": "What is the ratio of inbound to outbound emails?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "email_communications",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "contains",
            "value": ["7", "4"],
            "acceptable_variations": ["7:4", "7 inbound to 4 outbound", "1.75:1"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests ratio calculation for email directions"
    },
]

# =============================================================================
# CATEGORY 4: EDGE CASES
# =============================================================================

EDGE_CASE_QUESTIONS = [
    # -------------------------------------------------------------------------
    # Vague Questions (4 questions)
    # -------------------------------------------------------------------------
    {
        "id": "edge_vague_001",
        "category": "edge_cases",
        "subcategory": "vague_question",
        "question": "Show me stuff",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "general",
        "expected_tables": [],
        "expected_agents": ["supervisor", "sql_agent"],
        "expected_answer": {
            "type": "clarification",
            "value": "Should ask for clarification about what specific information is needed",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests needs_clarification detection for vague queries"
    },
    {
        "id": "edge_vague_002",
        "category": "edge_cases",
        "subcategory": "vague_question",
        "question": "Give me data",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": None,
        "expected_tables": [],
        "expected_agents": ["supervisor", "sql_agent"],
        "expected_answer": {
            "type": "clarification",
            "value": "Should ask for clarification",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests vague query handling"
    },
    {
        "id": "edge_vague_003",
        "category": "edge_cases",
        "subcategory": "vague_question",
        "question": "What about them?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "general",
        "expected_tables": [],
        "expected_agents": ["supervisor", "sql_agent"],
        "expected_answer": {
            "type": "clarification",
            "value": "Should ask what specific information about the company is needed",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests vague pronoun handling without memory context"
    },
    {
        "id": "edge_vague_004",
        "category": "edge_cases",
        "subcategory": "vague_question",
        "question": "Tell me more",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": None,
        "expected_tables": [],
        "expected_agents": ["supervisor", "sql_agent"],
        "expected_answer": {
            "type": "clarification",
            "value": "Should ask what specific aspect needs more detail",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests vague continuation query handling"
    },

    # -------------------------------------------------------------------------
    # Chitchat/Conversational (5 questions)
    # -------------------------------------------------------------------------
    {
        "id": "edge_chat_001",
        "category": "edge_cases",
        "subcategory": "chitchat",
        "question": "Hello",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "conversational",
        "expected_skill": "general",
        "expected_tables": [],
        "expected_agents": ["supervisor"],
        "expected_answer": {
            "type": "contains",
            "value": ["hello", "hi", "help"],
            "acceptable_variations": ["Hello!", "Hi there!", "How can I help?"]
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests greeting detection and conversational routing"
    },
    {
        "id": "edge_chat_002",
        "category": "edge_cases",
        "subcategory": "chitchat",
        "question": "How are you today?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "conversational",
        "expected_skill": None,
        "expected_tables": [],
        "expected_agents": ["supervisor"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Friendly response without querying database",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests chitchat detection"
    },
    {
        "id": "edge_chat_003",
        "category": "edge_cases",
        "subcategory": "chitchat",
        "question": "Thanks!",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "conversational",
        "expected_skill": None,
        "expected_tables": [],
        "expected_agents": ["supervisor"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Acknowledgment response like 'You're welcome'",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests gratitude detection"
    },
    {
        "id": "edge_chat_004",
        "category": "edge_cases",
        "subcategory": "chitchat",
        "question": "What can you do?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "conversational",
        "expected_skill": "general",
        "expected_tables": [],
        "expected_agents": ["supervisor"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Description of capabilities (emails, calls, documents, company info)",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests capability inquiry handling"
    },
    {
        "id": "edge_chat_005",
        "category": "edge_cases",
        "subcategory": "chitchat",
        "question": "Good morning!",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "conversational",
        "expected_skill": None,
        "expected_tables": [],
        "expected_agents": ["supervisor"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Friendly greeting response",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests time-based greeting detection"
    },

    # -------------------------------------------------------------------------
    # Off-Topic Questions (3 questions)
    # -------------------------------------------------------------------------
    {
        "id": "edge_offtopic_001",
        "category": "edge_cases",
        "subcategory": "off_topic",
        "question": "What's the weather like?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "conversational",
        "expected_skill": "general",
        "expected_tables": [],
        "expected_agents": ["supervisor"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should redirect to insurance-related queries or politely decline",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests off-topic query handling"
    },
    {
        "id": "edge_offtopic_002",
        "category": "edge_cases",
        "subcategory": "off_topic",
        "question": "Write me a poem about insurance",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "conversational",
        "expected_skill": None,
        "expected_tables": [],
        "expected_agents": ["supervisor"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should redirect to data queries or handle creatively within scope",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests creative request handling"
    },
    {
        "id": "edge_offtopic_003",
        "category": "edge_cases",
        "subcategory": "off_topic",
        "question": "Can you book me a flight?",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "conversational",
        "expected_skill": "general",
        "expected_tables": [],
        "expected_agents": ["supervisor"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should politely explain focus on insurance data",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests out-of-scope request handling"
    },

    # -------------------------------------------------------------------------
    # Typo/Ambiguous Questions (3 questions)
    # -------------------------------------------------------------------------
    {
        "id": "edge_typo_001",
        "category": "edge_cases",
        "subcategory": "typo",
        "question": "How are yo",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "conversational",
        "expected_skill": None,
        "expected_tables": [],
        "expected_agents": ["supervisor"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should recognize as greeting/chitchat despite truncation",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "simple",
        "description": "Tests truncated query handling"
    },
    {
        "id": "edge_typo_002",
        "category": "edge_cases",
        "subcategory": "typo",
        "question": "Shwo me emials",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "general",
        "expected_tables": ["communications.emails_silver"],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "list",
            "value": "Should interpret as 'show me emails' and return email list",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests typo resilience for actionable queries"
    },
    {
        "id": "edge_ambiguous_001",
        "category": "edge_cases",
        "subcategory": "ambiguous",
        "question": "Recent activity",
        "company_id": DEFAULT_COMPANY_ID,
        "expected_route": "sql_only",
        "expected_skill": "general",
        "expected_tables": [
            "communications.emails_silver",
            "communications.phone_call_silver",
            "communications.phone_message_silver"
        ],
        "expected_agents": ["supervisor", "sql_agent", "synthesizer"],
        "expected_answer": {
            "type": "open_ended",
            "value": "Should interpret as account timeline and use UNION ALL",
            "acceptable_variations": []
        },
        "requires_memory": False,
        "memory_context": [],
        "complexity": "moderate",
        "description": "Tests terse but actionable query interpretation"
    },
]

# =============================================================================
# COMBINED QUESTIONS LIST
# =============================================================================

ALL_EVALUATION_QUESTIONS = (
    INDIVIDUAL_AGENT_QUESTIONS +
    MEMORY_QUESTIONS +
    MULTI_AGENT_QUESTIONS +
    EDGE_CASE_QUESTIONS
)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_questions() -> List[Dict[str, Any]]:
    """Get all evaluation questions."""
    return ALL_EVALUATION_QUESTIONS


def get_questions_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Get all questions for a specific category.

    Args:
        category: One of 'individual_agent', 'memory', 'multi_agent', 'edge_cases'

    Returns:
        List of questions in that category
    """
    return [q for q in ALL_EVALUATION_QUESTIONS if q["category"] == category]


def get_questions_by_subcategory(subcategory: str) -> List[Dict[str, Any]]:
    """
    Get all questions for a specific subcategory.

    Args:
        subcategory: e.g., 'email_communications', 'phone_calls', 'chitchat', etc.

    Returns:
        List of questions in that subcategory
    """
    return [q for q in ALL_EVALUATION_QUESTIONS if q["subcategory"] == subcategory]


def get_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific question by its ID.

    Args:
        question_id: Unique question identifier (e.g., 'email_001')

    Returns:
        Question dict or None if not found
    """
    for q in ALL_EVALUATION_QUESTIONS:
        if q["id"] == question_id:
            return q
    return None


def get_memory_test_sequences() -> List[List[Dict[str, Any]]]:
    """
    Get memory test question pairs as sequences.

    Returns:
        List of [setup_question, follow_up_question] pairs
    """
    memory_questions = get_questions_by_category("memory")
    sequences = []

    # Group by sequence (mem_001a + mem_001b, etc.)
    sequence_ids = set()
    for q in memory_questions:
        # Extract base ID (mem_001 from mem_001a)
        base_id = q["id"][:-1] if q["id"][-1] in ['a', 'b'] else q["id"]
        sequence_ids.add(base_id)

    for base_id in sorted(sequence_ids):
        setup = get_question_by_id(f"{base_id}a")
        followup = get_question_by_id(f"{base_id}b")
        if setup and followup:
            sequences.append([setup, followup])

    return sequences


def get_questions_requiring_memory() -> List[Dict[str, Any]]:
    """Get all questions that require conversation memory context."""
    return [q for q in ALL_EVALUATION_QUESTIONS if q.get("requires_memory", False)]


def get_questions_by_complexity(complexity: str) -> List[Dict[str, Any]]:
    """
    Get questions by complexity level.

    Args:
        complexity: One of 'simple', 'moderate', 'complex'

    Returns:
        List of questions with that complexity
    """
    return [q for q in ALL_EVALUATION_QUESTIONS if q["complexity"] == complexity]


def get_questions_by_expected_route(route: str) -> List[Dict[str, Any]]:
    """
    Get questions by expected routing decision.

    Args:
        route: One of 'conversational', 'sql_only', 'document_search', 'hybrid'

    Returns:
        List of questions expected to route that way
    """
    return [q for q in ALL_EVALUATION_QUESTIONS if q["expected_route"] == route]


def get_questions_by_skill(skill: str) -> List[Dict[str, Any]]:
    """
    Get questions by expected skill.

    Args:
        skill: Skill name (e.g., 'email_communications', 'phone_calls')

    Returns:
        List of questions expected to use that skill
    """
    return [q for q in ALL_EVALUATION_QUESTIONS if q["expected_skill"] == skill]


def get_evaluation_summary() -> Dict[str, Any]:
    """Get summary statistics about the evaluation questions."""
    all_questions = ALL_EVALUATION_QUESTIONS

    # Count by category
    categories = {}
    for q in all_questions:
        cat = q["category"]
        categories[cat] = categories.get(cat, 0) + 1

    # Count by subcategory
    subcategories = {}
    for q in all_questions:
        subcat = q["subcategory"]
        subcategories[subcat] = subcategories.get(subcat, 0) + 1

    # Count by complexity
    complexities = {}
    for q in all_questions:
        comp = q["complexity"]
        complexities[comp] = complexities.get(comp, 0) + 1

    # Count by route
    routes = {}
    for q in all_questions:
        route = q["expected_route"]
        routes[route] = routes.get(route, 0) + 1

    # Count memory questions
    memory_required = len(get_questions_requiring_memory())

    return {
        "total_questions": len(all_questions),
        "by_category": categories,
        "by_subcategory": subcategories,
        "by_complexity": complexities,
        "by_expected_route": routes,
        "memory_questions": memory_required,
        "test_company": COMPANY_INFO
    }


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    summary = get_evaluation_summary()

    print("=" * 60)
    print("COMPREHENSIVE EVALUATION FRAMEWORK")
    print("=" * 60)
    print(f"\nTotal Questions: {summary['total_questions']}")

    print(f"\nTest Company: {summary['test_company']['name']}")
    print(f"  ID: {summary['test_company']['id']}")
    print(f"  Industry: {summary['test_company']['industry']}")

    print("\nBy Category:")
    for cat, count in summary["by_category"].items():
        print(f"  {cat}: {count}")

    print("\nBy Subcategory:")
    for subcat, count in sorted(summary["by_subcategory"].items()):
        print(f"  {subcat}: {count}")

    print("\nBy Complexity:")
    for comp, count in summary["by_complexity"].items():
        print(f"  {comp}: {count}")

    print("\nBy Expected Route:")
    for route, count in summary["by_route"].items():
        print(f"  {route}: {count}")

    print(f"\nQuestions Requiring Memory: {summary['memory_questions']}")

    print("\nMemory Test Sequences:")
    for seq in get_memory_test_sequences():
        print(f"  {seq[0]['id']} -> {seq[1]['id']}")
